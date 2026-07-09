#!/usr/bin/env bash
# Rated × cut-in design sweep — VP Gen5, 6.6 kV step-up, NE+NY.
# See experiments/rated_cutin_sweep/EXPERIMENT.md.
#
# Sweeps v_rated and v_cut_in as independent design parameters (the 0.3 ratio is
# broken). The rating tracks v_rated via the cubic law, so fleet size N follows
# from each installed-capacity target. Per-device cost is held.
#
# Results layout mirrors the dependency tiers exactly — each artifact lives at
# the level it actually depends on, and nothing is replicated:
#   results/vp/rated_cutin_sweep/
#     harmonics.nc, histograms.nc          resource-only -> ONE copy, all curves
#     vr<rated>_vci<cutin>/
#       candidates.nc, covariance.nc       per power curve, shared across capacity
#       <MW>mw/optimization_results.nc     per (curve, capacity)
#
# This is achieved with the engine's input-dir hooks (default to TIDAL_RESULTS_DIR
# when unset, so sibling experiments are unaffected):
#   TIDAL_RESOURCE_DIR -> where harmonics.nc / histograms.nc are read (steps 3,4)
#   TIDAL_CURVE_DIR    -> where candidates.nc / covariance.nc are read (step 5)
#   TIDAL_RESULTS_DIR  -> where the current step writes its output
#
# Reuse structure (the covariance depends only on the power curve, not capacity):
#   steps 1-2 (harmonics, histograms)  -> reuse once (symlink at sweep root)
#   step  3   (screen)                 -> once per (v_rated, v_cut_in) curve
#   step  4   (covariance, expensive)  -> once per curve
#   step  5   (optimize)               -> once per (curve, capacity)
#
# Resumable: existing candidates.nc / covariance.nc / optimization_results.nc
# are not recomputed (delete to force a rebuild).

set -uo pipefail
export PYTHONIOENCODING=utf-8
export MATLAB_BIN="${MATLAB_BIN:-/c/Program Files/MATLAB/R2024b/bin/matlab.exe}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
VP_DIR="$REPO_DIR/optimization/vp"
if [[ -x "$REPO_DIR/.venv/Scripts/python.exe" ]]; then
    VENV_PY="$REPO_DIR/.venv/Scripts/python.exe"
else
    VENV_PY="$REPO_DIR/.venv/bin/python"
fi

# --- experiment definition -------------------------------------------------
VARIANT="gen5"
SCOPE="new_england_new_york"
STEPUP_KV="6.6"
NE_NY_STATES="Maine_coastline,New_Hampshire_coastline,Massachusetts_coastline,Rhode_Island_coastline,Connecticut_coastline,New_York_coastline"

# Reference cell (2.03/0.61) first so the first full slice is the known one.
V_RATED_GRID=(2.03 1.75 1.50 2.30 2.60)
V_CUT_IN_GRID=(0.61 0.40 0.80)
MW_GRID=(1 5 25 100)

export TIDAL_VARIANT="$VARIANT"
export TIDAL_STEPUP_KV="$STEPUP_KV"
export TIDAL_GROUP="$SCOPE"
export TIDAL_STATE="$NE_NY_STATES"
export TIDAL_LCOE_TARGETS="600,700,800,900,1000,1100,1200,1300,1400,1500"

# Source for the design-independent steps 1-2 (resource only; reused verbatim).
SRC12="$REPO_DIR/results/vp/turbine_modification/$VARIANT/groups/$SCOPE/5mw"
# Results live under the shared results tree (gitignored), matching sibling
# experiments — not inside the experiment folder.
RESULTS="$REPO_DIR/results/vp/rated_cutin_sweep"
SUMMARY="$RESULTS/run_summary.txt"
mkdir -p "$RESULTS"

# --- single-instance lock --------------------------------------------------
# This box's Git-for-Windows launcher (bin/bash -> usr/bin/bash) can spawn the
# driver TWICE from one invocation, racing two drivers on the same cells. mkdir
# is atomic, so only the first wins. We also reclaim a stale lock left by a
# force-killed run (SIGKILL skips the EXIT trap), keyed on PID liveness.
LOCK="$RESULTS/.run_sweep.lock"
if ! mkdir "$LOCK" 2>/dev/null; then
    oldpid=$(cat "$LOCK/pid" 2>/dev/null || true)
    # A concurrent winner may not have written its PID yet — give it a moment.
    [[ -z "$oldpid" ]] && sleep 1 && oldpid=$(cat "$LOCK/pid" 2>/dev/null || true)
    if [[ -n "$oldpid" ]] && kill -0 "$oldpid" 2>/dev/null; then
        echo "run_sweep.sh: instance (pid $oldpid) already running; exiting." >&2
        exit 0
    fi
    echo "run_sweep.sh: reclaiming stale lock (pid='${oldpid:-none}' not alive)" >&2
    rm -f "$LOCK/pid" 2>/dev/null; rmdir "$LOCK" 2>/dev/null
    mkdir "$LOCK" 2>/dev/null || { echo "run_sweep.sh: lost lock race; exiting." >&2; exit 0; }
fi
echo "$$" > "$LOCK/pid"
trap 'rm -f "$LOCK/pid" 2>/dev/null; rmdir "$LOCK" 2>/dev/null' EXIT

if [[ ! -f "$SRC12/harmonics.nc" || ! -f "$SRC12/histograms.nc" ]]; then
    echo "FATAL: step 1-2 source missing at $SRC12" >&2
    exit 1
fi

# Resource-only inputs live ONCE at the sweep root (identical for every curve).
# Every screen/covariance step reads them from here via TIDAL_RESOURCE_DIR.
ln -sf "$SRC12/harmonics.nc"  "$RESULTS/harmonics.nc"
ln -sf "$SRC12/histograms.nc" "$RESULTS/histograms.nc"
export TIDAL_RESOURCE_DIR="$RESULTS"

# Pipeline scripts import config as a package and use script-relative paths.
cd "$VP_DIR"

{
    echo "Rated × cut-in design sweep"
    echo "Started:  $(date)"
    echo "Variant:  $VARIANT   Scope: $SCOPE   Transmission: ${STEPUP_KV} kV step-up"
    echo "v_rated:  ${V_RATED_GRID[*]}"
    echo "v_cut_in: ${V_CUT_IN_GRID[*]}"
    echo "capacity: ${MW_GRID[*]} MW"
    echo "LCOE:     $TIDAL_LCOE_TARGETS"
    echo ""
    printf "%-8s %-8s %-7s %-14s %9s\n" "v_rated" "v_cut_in" "cap" "step" "elapsed_s"
} > "$SUMMARY"

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

    # Steps 3-4 write the curve-level outputs; they read harmonics/histograms
    # from TIDAL_RESOURCE_DIR (the sweep root, set above).
    export TIDAL_RESULTS_DIR="$curve"

    # Per-curve build log — captures the design-dependent step output
    # (n_candidates, CF/distance ranges, P_rated, covariance shape) next to the
    # curve's artifacts, mirroring the original pipeline's per-dir log.txt.
    build_log="$curve/build.log"

    # Step 3 — screen (capacity-independent).
    if [[ -f "$curve/candidates.nc" ]]; then
        echo ">>> step 3 screen: candidates.nc exists, skipping"
    else
        echo ">>> step 3 screen"
        t0=$(date +%s)
        "$VENV_PY" 03_screen_candidates.py 2>&1 | tee "$build_log"
        log_row "$vr" "$vci" "-" "screen" "$(( $(date +%s) - t0 ))"
    fi

    # Step 4 — covariance (capacity-independent, expensive).
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

    # Step 5 — optimize, once per capacity. Reads this curve's candidates +
    # covariance from TIDAL_CURVE_DIR and writes its result into the MW cell.
    export TIDAL_CURVE_DIR="$curve"
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
        # Per-cell optimize log — captures per-LCOE feasibility, the selected
        # portfolio, variance, energy and achieved LCOE next to the cell result.
        # pipefail (set above) propagates the optimizer's exit status through tee.
        if "$VENV_PY" 05_optimize.py 2>&1 | tee "$cell/optimize.log"; then status="optimize"; else status="opt_FAILED"; fi
        log_row "$vr" "$vci" "${mw}MW" "$status" "$(( $(date +%s) - t0 ))"
    done
    # Restore curve-level results dir for the next iteration's steps 3-4.
    export TIDAL_RESULTS_DIR="$curve"
  done
done

echo "" >> "$SUMMARY"
echo "Finished: $(date)" >> "$SUMMARY"
echo ""
echo "===== rated_cutin_sweep summary ====="
cat "$SUMMARY"
