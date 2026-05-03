#!/usr/bin/env bash
# Run the full ORPC TidGen 2.0 pipeline for a single state (or pooled).
#
# Usage:
#   ./run_state.sh Virginia_coastline
#   ./run_state.sh pooled          # pooled east-coast run
#
# Writes all outputs to results/orpc/states/<state>/ (or results/orpc/groups/pooled/).
# Captures stdout+stderr to <results_dir>/log.txt.

set -euo pipefail

STATE_ARG="${1:-}"
if [[ -z "$STATE_ARG" ]]; then
    echo "Usage: $0 <state_name|pooled>" >&2
    echo "  state_name must match a value in config/east_coast_state_boundaries.csv" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_PY="$REPO_DIR/.venv/bin/python"
MATLAB_BIN="${MATLAB_BIN:-/Applications/MATLAB_R2024b.app/bin/matlab}"

if [[ "$STATE_ARG" == "pooled" ]]; then
    export TIDAL_STATE=""
    RESULTS_DIR="$REPO_DIR/results/orpc/groups/pooled"
else
    export TIDAL_STATE="$STATE_ARG"
    RESULTS_DIR="$REPO_DIR/results/orpc/states/$STATE_ARG"
fi

mkdir -p "$RESULTS_DIR"
export TIDAL_RESULTS_DIR="$RESULTS_DIR"

LOG_FILE="$RESULTS_DIR/log.txt"

# Log everything; tee so it also shows on terminal
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================================"
echo "ORPC run: $STATE_ARG"
echo "Started: $(date)"
echo "Results dir: $RESULTS_DIR"
echo "========================================================"

cd "$SCRIPT_DIR"

echo ""
echo ">>> Step 1: extract harmonics"
"$VENV_PY" 01_extract_harmonics.py

echo ""
echo ">>> Step 2: build histograms (MATLAB)"
"$MATLAB_BIN" -batch "build_histograms"

echo ""
echo ">>> Step 3: screen candidates"
"$VENV_PY" 03_screen_candidates.py

echo ""
echo ">>> Step 4: compute covariance (MATLAB)"
"$MATLAB_BIN" -batch "compute_covariance"

echo ""
echo ">>> Step 5: optimize"
"$VENV_PY" 05_optimize.py

echo ""
echo ">>> Plots"
"$VENV_PY" plot_results.py

echo ""
echo "========================================================"
echo "Done: $(date)"
echo "========================================================"
