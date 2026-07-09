#!/usr/bin/env bash
# Run all 18 cells of the scope×scale experiment serially.
# Each cell = one step-5 invocation across 7 LCOE caps.
set -euo pipefail

ROOT="/Users/abhinandra/codes/spring-2026/tidal-portfolio-siting"
EXP="$ROOT/experiments/scope_x_scale"
PY="$ROOT/.venv/bin/python"
LCOE_TARGETS="500,700,1000,1200,1500,2000,2500"

# (device, scope, mw) tuples
CELLS=(
  # smoke first (smallest scales)
  "vp pooled 5"
  "vp new_england_ny 5"
  "orpc pooled 25"
  "orpc new_england_ny 25"
  "vp pooled 25"
  "vp new_england_ny 25"
  # mid
  "vp pooled 50"
  "vp new_england_ny 50"
  "orpc pooled 50"
  "orpc new_england_ny 50"
  "vp pooled 100"
  "vp new_england_ny 100"
  "orpc pooled 100"
  "orpc new_england_ny 100"
  # large (slowest)
  "vp pooled 250"
  "vp new_england_ny 250"
  "orpc pooled 250"
  "orpc new_england_ny 250"
)

CELL_ARG="${1:-}"   # optional: run a single cell index (0-indexed) or 'all'

run_cell() {
  local device="$1" scope="$2" mw="$3"
  local cell_dir="$EXP/results/$device/${scope}_${mw}mw"
  local log_file="$EXP/logs/${device}_${scope}_${mw}mw.log"
  local script="$ROOT/optimization/$device/05_optimize.py"

  echo "----------------------------------------------------------------"
  echo "[$(date +%H:%M:%S)] cell: $device | $scope | ${mw} MW"
  echo "  TIDAL_RESULTS_DIR=$cell_dir"
  echo "  log: $log_file"
  local t0=$(date +%s)
  TIDAL_RESULTS_DIR="$cell_dir" \
  TIDAL_P_TARGET_MW="$mw" \
  TIDAL_LCOE_TARGETS="$LCOE_TARGETS" \
    "$PY" "$script" > "$log_file" 2>&1 || {
      echo "  FAILED. Last 20 lines of log:"
      tail -n 20 "$log_file"
      return 1
    }
  local dt=$(( $(date +%s) - t0 ))
  echo "  done in ${dt}s"
}

if [[ "$CELL_ARG" =~ ^[0-9]+$ ]]; then
  read -r d s m <<< "${CELLS[$CELL_ARG]}"
  run_cell "$d" "$s" "$m"
else
  for entry in "${CELLS[@]}"; do
    read -r d s m <<< "$entry"
    run_cell "$d" "$s" "$m"
  done
  echo "----------------------------------------------------------------"
  echo "All 18 cells complete."
fi
