#!/usr/bin/env bash
# Run the full tidal portfolio pipeline for a single state (or pooled).
#
# Usage:
#   ./run_state.sh Virginia_coastline
#   ./run_state.sh pooled          # pooled east-coast run
#
# Writes all outputs to results/<state>/ (or results/pooled/).
# Captures stdout+stderr to results/<state>/log.txt.

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

if [[ "$STATE_ARG" == "pooled" ]]; then
    export TIDAL_STATE=""
else
    export TIDAL_STATE="$STATE_ARG"
fi

# Defer path resolution to config.py so TIDAL_VARIANT et al. take effect.
RESULTS_DIR="$("$VENV_PY" -c "import sys; sys.path.insert(0, '$SCRIPT_DIR'); from config.config import get_results_dir; print(get_results_dir())")"
mkdir -p "$RESULTS_DIR"
export TIDAL_RESULTS_DIR="$RESULTS_DIR"

LOG_FILE="$RESULTS_DIR/log.txt"

# Log everything; tee so it also shows on terminal
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================================"
echo "Run: $STATE_ARG"
echo "Started: $(date)"
echo "Results dir: $RESULTS_DIR"
echo "========================================================"

cd "$SCRIPT_DIR"

echo ""
echo ">>> Step 1: extract harmonics"
"$VENV_PY" 01_extract_harmonics.py

echo ""
echo ">>> Step 2: build histograms"
"$VENV_PY" 02_build_histograms.py

echo ""
echo ">>> Step 3: screen candidates"
"$VENV_PY" 03_screen_candidates.py

echo ""
echo ">>> Step 4: compute covariance"
"$VENV_PY" 04_compute_covariance.py

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
