#!/usr/bin/env bash
# Run the full tidal pipeline for a named group of states.
#
# Usage:
#   ./run_group.sh <group_name> <state1,state2,...>
#
# Example:
#   ./run_group.sh new_england Maine_coastline,New_Hampshire_coastline,...
#
# Writes outputs to results/<group_name>/.

set -euo pipefail

GROUP="${1:-}"
STATES="${2:-}"
if [[ -z "$GROUP" || -z "$STATES" ]]; then
    echo "Usage: $0 <group_name> <state1,state2,...>" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_PY="$REPO_DIR/.venv/bin/python"
MATLAB_BIN="${MATLAB_BIN:-/Applications/MATLAB_R2024b.app/bin/matlab}"

export TIDAL_GROUP="$GROUP"
export TIDAL_STATE="$STATES"

RESULTS_DIR="$REPO_DIR/results/vp/groups/$GROUP"
mkdir -p "$RESULTS_DIR"
export TIDAL_RESULTS_DIR="$RESULTS_DIR"

LOG_FILE="$RESULTS_DIR/log.txt"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================================"
echo "Group run: $GROUP"
echo "States: $STATES"
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
