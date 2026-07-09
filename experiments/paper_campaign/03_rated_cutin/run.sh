#!/usr/bin/env bash
# Campaign 03 — rated x cut-in design sweep: gen5 geometry, pooled, 6.6 kV.
# Adapted from experiments/rated_cutin_sweep/run_sweep.sh (NE+NY original);
# this campaign version runs at pooled scope and reads the resource tier from
# ../01_baseline/results (same variant, same scope -> identical steps 1-2).
#   steps 1-2 (harmonics, histograms)  -> copied once from 01_baseline
#   step  3   (screen)                 -> once per (v_rated, v_cut_in) curve
#   step  4   (covariance, expensive)  -> once per curve
#   step  5   (optimize)               -> once per (curve, capacity)
# Resumable: existing outputs are not recomputed (delete to force a rebuild).
# See EXPERIMENT.md and ../CAMPAIGN.md.

set -uo pipefail
export PYTHONIOENCODING=utf-8
export MATLAB_BIN="${MATLAB_BIN:-/c/Program Files/MATLAB/R2024b/bin/matlab.exe}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
VP_DIR="$REPO_DIR/optimization/vp"
if [[ -x "$REPO_DIR/.venv/Scripts/python.exe" ]]; then
    VENV_PY="$REPO_DIR/.venv/Scripts/python.exe"
else
    VENV_PY="$REPO_DIR/.venv/bin/python"
fi

# Reference cell (2.03/0.61) first so the first full slice is the known one.
V_RATED_GRID=(2.03 1.75 1.50 2.30 2.60)
V_CUT_IN_GRID=(0.61 0.40 0.80)
MW_GRID=(1 5 25 100)

export TIDAL_VARIANT="gen5"
export TIDAL_STEPUP_KV="6.6"
export TIDAL_STATE=""                      # pooled East Coast
unset TIDAL_GROUP 2>/dev/null || true
export TIDAL_LCOE_TARGETS="600,700,800,900,1000,1100,1200,1300,1400,1500"

SRC12="$SCRIPT_DIR/../01_baseline/results"
RESULTS="$SCRIPT_DIR/results"
SUMMARY="$RESULTS/run_summary.txt"
mkdir -p "$RESULTS"

LOCK="$RESULTS/.run.lock"
if ! mkdir "$LOCK" 2>/dev/null; then
    oldpid=$(cat "$LOCK/pid" 2>/dev/null || true)
    [[ -z "$oldpid" ]] && sleep 1 && oldpid=$(cat "$LOCK/pid" 2>/dev/null || true)
    if [[ -n "$oldpid" ]] && kill -0 "$oldpid" 2>/dev/null; then
        echo "run.sh: instance (pid $oldpid) already running; exiting." >&2
        exit 0
    fi
    echo "run.sh: reclaiming stale lock (pid='${oldpid:-none}' not alive)" >&2
    rm -f "$LOCK/pid" 2>/dev/null; rmdir "$LOCK" 2>/dev/null
    mkdir "$LOCK" 2>/dev/null || { echo "run.sh: lost lock race; exiting." >&2; exit 0; }
fi
echo "$$" > "$LOCK/pid"
trap 'rm -f "$LOCK/pid" 2>/dev/null; rmdir "$LOCK" 2>/dev/null' EXIT

if [[ ! -f "$SRC12/harmonics.nc" || ! -f "$SRC12/histograms.nc" ]]; then
    echo "FATAL: resource tier missing at $SRC12 — run ../01_baseline/run.sh first" >&2
    exit 1
fi

# Resource-only inputs live ONCE at the sweep root (identical for every curve).
cp -f "$SRC12/harmonics.nc"  "$RESULTS/harmonics.nc"
cp -f "$SRC12/histograms.nc" "$RESULTS/histograms.nc"
export TIDAL_RESOURCE_DIR="$RESULTS"

cd "$VP_DIR"

{
    echo "Campaign 03 — rated x cut-in sweep (gen5 geometry, pooled, 6.6 kV)"
    echo "Started:  $(date)"
    echo "v_rated:  ${V_RATED_GRID[*]}"
    echo "v_cut_in: ${V_CUT_IN_GRID[*]}"
    echo "MW:       ${MW_GRID[*]}"
    echo "LCOE:     $TIDAL_LCOE_TARGETS"
    echo ""
    printf "%-8s %-8s %-7s %-14s %9s\n" "v_rated" "v_cut_in" "cap" "step" "elapsed_s"
} >> "$SUMMARY"
log_row() { printf "%-8s %-8s %-7s %-14s %9d\n" "$1" "$2" "$3" "$4" "$5" >> "$SUMMARY"; }

for vr in "${V_RATED_GRID[@]}"; do
  for vci in "${V_CUT_IN_GRID[@]}"; do
    curve="$RESULTS/vr${vr}_vci${vci}"
    mkdir -p "$curve"
    echo ""
    echo "############################################################"
    echo "## curve  v_rated=$vr  v_cut_in=$vci"
    echo "############################################################"

    export TIDAL_V_RATED="$vr"
    export TIDAL_V_CUT_IN="$vci"
    export TIDAL_RESULTS_DIR="$curve"
    # CURVE_DIR must be set BEFORE step 3: screen writes candidates.nc and
    # covariance reads/writes via get_curve_dir(). Setting it after the steps
    # leaks the prior curve's dir into this one (screen sees the old
    # candidates.nc, skips; covariance never lands here -> cov_FAILED).
    export TIDAL_CURVE_DIR="$curve"
    build_log="$curve/build.log"

    if [[ -f "$curve/candidates.nc" ]]; then
        echo ">>> step 3 screen: candidates.nc exists, skipping"
    else
        echo ">>> step 3 screen"
        t0=$(date +%s)
        "$VENV_PY" 03_screen_candidates.py 2>&1 | tee "$build_log"
        log_row "$vr" "$vci" "-" "screen" "$(( $(date +%s) - t0 ))"
    fi

    if [[ -f "$curve/covariance.nc" ]]; then
        echo ">>> step 4 covariance: covariance.nc exists, skipping"
    else
        echo ">>> step 4 covariance (MATLAB)"
        t0=$(date +%s)
        "$MATLAB_BIN" -batch "compute_covariance" 2>&1 | tee -a "$build_log"
        log_row "$vr" "$vci" "-" "covariance" "$(( $(date +%s) - t0 ))"
    fi

    if [[ ! -f "$curve/covariance.nc" ]]; then
        echo "WARNING: covariance.nc not produced for $curve; skipping its capacities"
        log_row "$vr" "$vci" "-" "cov_FAILED" 0
        continue
    fi

    for mw in "${MW_GRID[@]}"; do
        cell="$curve/${mw}mw"
        mkdir -p "$cell"
        if [[ -f "$cell/optimization_results.nc" ]]; then
            echo ">>> step 5 optimize ${mw}MW: results exist, skipping"
            continue
        fi
        echo ">>> step 5 optimize  capacity=${mw}MW"
        export TIDAL_RESULTS_DIR="$cell"
        export TIDAL_P_TARGET_MW="$mw"
        t0=$(date +%s)
        if "$VENV_PY" 05_optimize.py 2>&1 | tee "$cell/optimize.log"; then status="optimize"; else status="opt_FAILED"; fi
        log_row "$vr" "$vci" "${mw}MW" "$status" "$(( $(date +%s) - t0 ))"
    done
    export TIDAL_RESULTS_DIR="$curve"
  done
done

unset TIDAL_V_RATED TIDAL_V_CUT_IN

echo "" >> "$SUMMARY"
echo "Finished: $(date)" >> "$SUMMARY"
echo ""
echo "===== 03_rated_cutin summary ====="
cat "$SUMMARY"
