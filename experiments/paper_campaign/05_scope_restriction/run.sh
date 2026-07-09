#!/usr/bin/env bash
# Campaign 05 — scope restriction: gen5, NE+NY only, 6.6 kV step-up.
# Quantifies what restricting the pool to NE+NY costs vs the pooled baseline
# (01_baseline) at each scale. Steps 1-4 fresh (own scope); step 5 per MW.
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

MW_GRID=(1 5 25 100)
NE_NY_STATES="Maine_coastline,New_Hampshire_coastline,Massachusetts_coastline,Rhode_Island_coastline,Connecticut_coastline,New_York_coastline"

export TIDAL_VARIANT="gen5"
export TIDAL_STEPUP_KV="6.6"
export TIDAL_GROUP="new_england_new_york"
export TIDAL_STATE="$NE_NY_STATES"
export TIDAL_LCOE_TARGETS="600,700,800,900,1000,1100,1200,1300,1400,1500"

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

cd "$VP_DIR"

{
    echo "Campaign 05 — scope restriction (gen5, NE+NY, 6.6 kV)"
    echo "Started:  $(date)"
    echo "MW:       ${MW_GRID[*]}"
    echo "LCOE:     $TIDAL_LCOE_TARGETS"
    echo ""
    printf "%-7s %-14s %9s\n" "cap" "step" "elapsed_s"
} >> "$SUMMARY"
log_row() { printf "%-7s %-14s %9d\n" "$1" "$2" "$3" >> "$SUMMARY"; }

export TIDAL_RESULTS_DIR="$RESULTS"
build_log="$RESULTS/build.log"

run_step() {  # run_step <label> <output.nc> <cmd...>
    local label="$1" out="$2"; shift 2
    if [[ -f "$RESULTS/$out" ]]; then
        echo ">>> $label: $out exists, skipping"
        return 0
    fi
    echo ">>> $label"
    local t0=$(date +%s)
    if "$@" 2>&1 | tee -a "$build_log"; then
        log_row "-" "$label" "$(( $(date +%s) - t0 ))"
    else
        log_row "-" "${label}_FAILED" "$(( $(date +%s) - t0 ))"
    fi
    [[ -f "$RESULTS/$out" ]]
}

run_step "extract"    "harmonics.nc"  "$VENV_PY" 01_extract_harmonics.py   || exit 1
run_step "histograms" "histograms.nc" "$MATLAB_BIN" -batch "build_histograms" || exit 1
run_step "screen"     "candidates.nc" "$VENV_PY" 03_screen_candidates.py   || exit 1
run_step "covariance" "covariance.nc" "$MATLAB_BIN" -batch "compute_covariance" || exit 1

export TIDAL_RESOURCE_DIR="$RESULTS"
export TIDAL_CURVE_DIR="$RESULTS"
for mw in "${MW_GRID[@]}"; do
    cell="$RESULTS/${mw}mw"
    mkdir -p "$cell"
    if [[ -f "$cell/optimization_results.nc" ]]; then
        echo ">>> optimize ${mw}MW: results exist, skipping"
        continue
    fi
    echo ">>> optimize ${mw}MW"
    export TIDAL_RESULTS_DIR="$cell"
    export TIDAL_P_TARGET_MW="$mw"
    t0=$(date +%s)
    if "$VENV_PY" 05_optimize.py 2>&1 | tee "$cell/optimize.log"; then status="optimize"; else status="opt_FAILED"; fi
    log_row "${mw}MW" "$status" "$(( $(date +%s) - t0 ))"
done
export TIDAL_RESULTS_DIR="$RESULTS"

echo "" >> "$SUMMARY"
echo "Finished: $(date)" >> "$SUMMARY"
echo ""
echo "===== 05_scope_restriction summary ====="
cat "$SUMMARY"
