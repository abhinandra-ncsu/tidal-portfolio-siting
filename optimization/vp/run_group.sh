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
export PYTHONIOENCODING=utf-8

GROUP="${1:-}"
STATES="${2:-}"
if [[ -z "$GROUP" || -z "$STATES" ]]; then
    echo "Usage: $0 <group_name> <state1,state2,...>" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
if [[ -x "$REPO_DIR/.venv/Scripts/python.exe" ]]; then
    VENV_PY="$REPO_DIR/.venv/Scripts/python.exe"
else
    VENV_PY="$REPO_DIR/.venv/bin/python"
fi
MATLAB_BIN="${MATLAB_BIN:-/Applications/MATLAB_R2024b.app/bin/matlab}"

export TIDAL_GROUP="$GROUP"
export TIDAL_STATE="$STATES"

# Defer path resolution to config.py so TIDAL_VARIANT et al. take effect.
# Resource/curve dirs fall back to the results dir when their env hooks
# (TIDAL_RESOURCE_DIR / TIDAL_CURVE_DIR) are unset, so single-dir runs see
# three identical paths.
# tr: Windows Python emits CRLF; readarray -t strips only the LF.
readarray -t _DIRS < <(cd "$SCRIPT_DIR" && "$VENV_PY" -c "import sys; sys.path.insert(0, '.'); from config.config import get_results_dir, get_resource_dir, get_curve_dir; print(get_results_dir()); print(get_resource_dir()); print(get_curve_dir())" | tr -d '\r')
RESULTS_DIR="${_DIRS[0]}"
RESOURCE_DIR="${_DIRS[1]}"
CURVE_DIR="${_DIRS[2]}"
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

# Steps 1-4 skip in-script when their output exists; the guards below skip
# the interpreter/MATLAB launch itself (MATLAB boot is minutes of dead time).
echo ""
echo ">>> Step 1: extract harmonics"
if [[ -e "$RESOURCE_DIR/harmonics.nc" ]]; then
    echo "Already exists: $RESOURCE_DIR/harmonics.nc (skipping launch)"
else
    "$VENV_PY" 01_extract_harmonics.py
fi

echo ""
echo ">>> Step 2: build histograms (MATLAB)"
if [[ -e "$RESOURCE_DIR/histograms.nc" ]]; then
    echo "Already exists: $RESOURCE_DIR/histograms.nc (skipping launch)"
else
    "$MATLAB_BIN" -batch "build_histograms"
fi

echo ""
echo ">>> Step 3: screen candidates"
if [[ -e "$CURVE_DIR/candidates.nc" ]]; then
    echo "Already exists: $CURVE_DIR/candidates.nc (skipping launch)"
else
    "$VENV_PY" 03_screen_candidates.py
fi

echo ""
echo ">>> Step 4: compute covariance (MATLAB)"
if [[ -e "$CURVE_DIR/covariance.nc" ]]; then
    echo "Already exists: $CURVE_DIR/covariance.nc (skipping launch)"
else
    "$MATLAB_BIN" -batch "compute_covariance"
fi

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
