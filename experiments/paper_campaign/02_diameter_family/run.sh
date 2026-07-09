#!/usr/bin/env bash
# Campaign 02 — diameter family: modvp{2,3,4,6,7,8}, pooled, 6.6 kV step-up.
# Per variant: steps 1-4 fresh (each variant has its own depth filter, hence
# its own eligibility pool); step 5 once per MW target.
# The gen5 (D=5) row of the family comes from ../01_baseline — not re-run here.
# Usage: ./run.sh [variant]    (optional: run a single variant, e.g. ./run.sh modvp6)
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

VARIANTS=(modvp2 modvp3 modvp4 modvp6 modvp7 modvp8)
[[ -n "${1:-}" ]] && VARIANTS=("$1")
MW_GRID=(1 5 25 100)

export TIDAL_STEPUP_KV="6.6"
export TIDAL_STATE=""                      # pooled East Coast
unset TIDAL_GROUP 2>/dev/null || true
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
    echo "Campaign 02 — diameter family (pooled, 6.6 kV)"
    echo "Started:  $(date)"
    echo "Variants: ${VARIANTS[*]}"
    echo "MW:       ${MW_GRID[*]}"
    echo "LCOE:     $TIDAL_LCOE_TARGETS"
    echo ""
    printf "%-8s %-7s %-14s %9s\n" "variant" "cap" "step" "elapsed_s"
} >> "$SUMMARY"
log_row() { printf "%-8s %-7s %-14s %9d\n" "$1" "$2" "$3" "$4" >> "$SUMMARY"; }

for variant in "${VARIANTS[@]}"; do
    VDIR="$RESULTS/$variant"
    mkdir -p "$VDIR"
    echo ""
    echo "############################################################"
    echo "## variant=$variant"
    echo "############################################################"

    export TIDAL_VARIANT="$variant"
    export TIDAL_RESULTS_DIR="$VDIR"
    build_log="$VDIR/build.log"

    run_step() {  # run_step <label> <output.nc> <cmd...>
        local label="$1" out="$2"; shift 2
        if [[ -f "$VDIR/$out" ]]; then
            echo ">>> $variant $label: $out exists, skipping"
            return 0
        fi
        echo ">>> $variant $label"
        local t0=$(date +%s)
        if "$@" 2>&1 | tee -a "$build_log"; then
            log_row "$variant" "-" "$label" "$(( $(date +%s) - t0 ))"
        else
            log_row "$variant" "-" "${label}_FAILED" "$(( $(date +%s) - t0 ))"
        fi
        [[ -f "$VDIR/$out" ]]
    }

    if ! run_step "extract"    "harmonics.nc"  "$VENV_PY" 01_extract_harmonics.py; then continue; fi
    if ! run_step "histograms" "histograms.nc" "$MATLAB_BIN" -batch "build_histograms"; then continue; fi
    if ! run_step "screen"     "candidates.nc" "$VENV_PY" 03_screen_candidates.py; then continue; fi
    if ! run_step "covariance" "covariance.nc" "$MATLAB_BIN" -batch "compute_covariance"; then continue; fi

    export TIDAL_RESOURCE_DIR="$VDIR"
    export TIDAL_CURVE_DIR="$VDIR"
    for mw in "${MW_GRID[@]}"; do
        cell="$VDIR/${mw}mw"
        mkdir -p "$cell"
        if [[ -f "$cell/optimization_results.nc" ]]; then
            echo ">>> $variant optimize ${mw}MW: results exist, skipping"
            continue
        fi
        echo ">>> $variant optimize ${mw}MW"
        export TIDAL_RESULTS_DIR="$cell"
        export TIDAL_P_TARGET_MW="$mw"
        t0=$(date +%s)
        if "$VENV_PY" 05_optimize.py 2>&1 | tee "$cell/optimize.log"; then status="optimize"; else status="opt_FAILED"; fi
        log_row "$variant" "${mw}MW" "$status" "$(( $(date +%s) - t0 ))"
        "$VENV_PY" plot_results.py 2>&1 | tee -a "$cell/optimize.log" || echo "(plots failed — non-fatal)"
    done
done

echo "" >> "$SUMMARY"
echo "Finished: $(date)" >> "$SUMMARY"
echo ""
echo "===== 02_diameter_family summary ====="
cat "$SUMMARY"
