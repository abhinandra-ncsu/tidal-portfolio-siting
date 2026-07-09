#!/usr/bin/env bash
# Campaign 04 — voltage justification arm: gen5, pooled, 480 V (no step-up).
# Evidence for the Sec. 2 design statement that RITE's as-built 480 V direct
# transmission does not scale. Voltage enters at step 5 only, so this reuses
# 01_baseline's steps 1-4 verbatim and re-runs only the optimizer per MW.
# See EXPERIMENT.md and ../CAMPAIGN.md.

set -uo pipefail
export PYTHONIOENCODING=utf-8

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
VP_DIR="$REPO_DIR/optimization/vp"
if [[ -x "$REPO_DIR/.venv/Scripts/python.exe" ]]; then
    VENV_PY="$REPO_DIR/.venv/Scripts/python.exe"
else
    VENV_PY="$REPO_DIR/.venv/bin/python"
fi

MW_GRID=(1 5 25 100)

export TIDAL_VARIANT="gen5"
unset TIDAL_STEPUP_KV 2>/dev/null || true   # 480 V baseline transmission
export TIDAL_STATE=""                       # pooled East Coast
unset TIDAL_GROUP 2>/dev/null || true
export TIDAL_LCOE_TARGETS="600,700,800,900,1000,1100,1200,1300,1400,1500"

BASE="$SCRIPT_DIR/../01_baseline/results"
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

if [[ ! -f "$BASE/candidates.nc" || ! -f "$BASE/covariance.nc" ]]; then
    echo "FATAL: curve tier missing at $BASE — run ../01_baseline/run.sh first" >&2
    exit 1
fi

export TIDAL_RESOURCE_DIR="$BASE"
export TIDAL_CURVE_DIR="$BASE"

cd "$VP_DIR"

{
    echo "Campaign 04 — voltage justification (gen5, pooled, 480 V)"
    echo "Started:  $(date)"
    echo "MW:       ${MW_GRID[*]}"
    echo "LCOE:     $TIDAL_LCOE_TARGETS"
    echo ""
    printf "%-7s %-14s %9s\n" "cap" "step" "elapsed_s"
} >> "$SUMMARY"
log_row() { printf "%-7s %-14s %9d\n" "$1" "$2" "$3" >> "$SUMMARY"; }

for mw in "${MW_GRID[@]}"; do
    cell="$RESULTS/${mw}mw"
    mkdir -p "$cell"
    if [[ -f "$cell/optimization_results.nc" ]]; then
        echo ">>> optimize ${mw}MW: results exist, skipping"
        continue
    fi
    echo ">>> optimize ${mw}MW (480 V)"
    export TIDAL_RESULTS_DIR="$cell"
    export TIDAL_P_TARGET_MW="$mw"
    t0=$(date +%s)
    if "$VENV_PY" 05_optimize.py 2>&1 | tee "$cell/optimize.log"; then status="optimize"; else status="opt_FAILED"; fi
    log_row "${mw}MW" "$status" "$(( $(date +%s) - t0 ))"
done

echo "" >> "$SUMMARY"
echo "Finished: $(date)" >> "$SUMMARY"
echo ""
echo "===== 04_voltage_justification summary ====="
cat "$SUMMARY"
