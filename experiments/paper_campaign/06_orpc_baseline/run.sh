#!/usr/bin/env bash
# Campaign 06 — ORPC TidGen 2.0 baseline: pooled East Coast, two voltage arms.
# Mirrors 01_baseline but drives the optimization/orpc/ pipeline instead of vp/.
#
# Steps 1-4 (harmonics/histograms/candidates/covariance) are voltage- AND
# capacity-independent, so they run fresh ONCE into results/shared/. Step 5
# (05_optimize.py) runs once per voltage-arm x MW target into
# results/<arm>/<mw>mw/. The ORPC pipeline resolves every file off a single
# TIDAL_RESULTS_DIR (no RESOURCE/CURVE dir split like VP), so each cell gets a
# copy of the two voltage-independent step-5 inputs before optimizing.
#
# Usage: ./run.sh [smoke]    (smoke = 5 MW cell only, both arms)
# See EXPERIMENT.md and ../CAMPAIGN.md.

set -uo pipefail
export PYTHONIOENCODING=utf-8
export MATLAB_BIN="${MATLAB_BIN:-/c/Program Files/MATLAB/R2024b/bin/matlab.exe}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
ORPC_DIR="$REPO_DIR/optimization/orpc"
if [[ -x "$REPO_DIR/.venv/Scripts/python.exe" ]]; then
    VENV_PY="$REPO_DIR/.venv/Scripts/python.exe"
else
    VENV_PY="$REPO_DIR/.venv/bin/python"
fi

# T_TIDE toolbox: optimization/orpc/t_tide is a git symlink to ../vp/t_tide, but
# this Windows checkout (core.symlinks=false) materialized it as a plain text
# file, so build_histograms.m / compute_covariance.m addpath fails. Put the real
# toolbox on MATLABPATH so t_predic/t_getconsts resolve at MATLAB startup; the
# scripts' broken addpath is then skipped by their `if ~exist(...)` guard.
export MATLABPATH="$(cygpath -m "$REPO_DIR/optimization/vp/t_tide" 2>/dev/null || echo "$REPO_DIR/optimization/vp/t_tide")"

MW_GRID=(5 10 25 100)
[[ "${1:-}" == "smoke" ]] && MW_GRID=(5)

# Voltage arms: "<subdir label>:<TIDAL_STEPUP_KV value>".
# 6.6 kV step-up (baseline) and 480 V (no step-up) comparison arm.
ARMS=("6600v:6.6" "480v:0")

export TIDAL_STATE=""                       # pooled East Coast
unset TIDAL_GROUP 2>/dev/null || true       # TIDAL_RESULTS_DIR override wins regardless
export TIDAL_LCOE_TARGETS="600,700,800,900,1000,1100,1200,1300,1400,1500"

RESULTS="$SCRIPT_DIR/results"
SHARED="$RESULTS/shared"
SUMMARY="$RESULTS/run_summary.txt"
mkdir -p "$SHARED"

# --- single-instance lock (same rationale as 01_baseline/run.sh: the
# Git-for-Windows launcher can spawn the driver twice from one invocation).
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

cd "$ORPC_DIR"

{
    echo "Campaign 06 — ORPC TidGen 2.0 baseline (pooled, 6.6 kV + 480 V arms)"
    echo "Started:  $(date)"
    echo "MW:       ${MW_GRID[*]}"
    echo "Arms:     ${ARMS[*]}"
    echo "LCOE:     $TIDAL_LCOE_TARGETS"
    echo ""
    printf "%-12s %-14s %9s\n" "cell" "step" "elapsed_s"
} >> "$SUMMARY"
log_row() { printf "%-12s %-14s %9d\n" "$1" "$2" "$3" >> "$SUMMARY"; }

build_log="$SHARED/build.log"

# --- Steps 1-4: voltage-independent, once, into results/shared/.
export TIDAL_RESULTS_DIR="$SHARED"
run_step() {  # run_step <label> <output.nc> <cmd...>
    local label="$1" out="$2"; shift 2
    if [[ -f "$SHARED/$out" ]]; then
        echo ">>> $label: $out exists, skipping"
        return 0
    fi
    echo ">>> $label"
    local t0=$(date +%s)
    if "$@" 2>&1 | tee -a "$build_log"; then
        log_row "shared" "$label" "$(( $(date +%s) - t0 ))"
    else
        log_row "shared" "${label}_FAILED" "$(( $(date +%s) - t0 ))"
    fi
    [[ -f "$SHARED/$out" ]]
}

run_step "extract"    "harmonics.nc"  "$VENV_PY" 01_extract_harmonics.py    || exit 1
run_step "histograms" "histograms.nc" "$MATLAB_BIN" -batch "build_histograms" || exit 1
run_step "screen"     "candidates.nc" "$VENV_PY" 03_screen_candidates.py    || exit 1
run_step "covariance" "covariance.nc" "$MATLAB_BIN" -batch "compute_covariance" || exit 1

# --- Step 5: per voltage arm x MW target, into results/<arm>/<mw>mw/.
for arm in "${ARMS[@]}"; do
    label="${arm%%:*}"; kv="${arm##*:}"
    export TIDAL_STEPUP_KV="$kv"
    for mw in "${MW_GRID[@]}"; do
        cell="$RESULTS/$label/${mw}mw"
        mkdir -p "$cell"
        if [[ -f "$cell/optimization_results.nc" ]]; then
            echo ">>> optimize $label ${mw}MW: results exist, skipping"
            continue
        fi
        echo ">>> optimize $label ${mw}MW (stepup_kv=$kv)"
        # ORPC step 5 reads candidates.nc + covariance.nc from TIDAL_RESULTS_DIR;
        # stage the voltage-independent inputs into the cell.
        cp -f "$SHARED/candidates.nc" "$SHARED/covariance.nc" "$cell/"
        export TIDAL_RESULTS_DIR="$cell"
        export TIDAL_P_TARGET_MW="$mw"
        t0=$(date +%s)
        if "$VENV_PY" 05_optimize.py 2>&1 | tee "$cell/optimize.log"; then status="optimize"; else status="opt_FAILED"; fi
        log_row "$label/${mw}MW" "$status" "$(( $(date +%s) - t0 ))"
        "$VENV_PY" plot_results.py 2>&1 | tee -a "$cell/optimize.log" || echo "(plots failed — non-fatal)"
    done
done
export TIDAL_RESULTS_DIR="$SHARED"

echo "" >> "$SUMMARY"
echo "Finished: $(date)" >> "$SUMMARY"
echo ""
echo "===== 06_orpc_baseline summary ====="
cat "$SUMMARY"
