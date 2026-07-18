#!/bin/bash
# Fine-band LCOE frontier sweep for pooled max-energy, per capacity.
# Re-solves ~9 in-band LCOE targets (distinct portfolios) to a *_frontier dir,
# then renders baseline-format spatial_map_L{L}.png via the repo's plot_results.py.
set -u
cd /mnt/c/Users/asingh66/tidal-portfolio-siting/optimization/vp || exit 1

REPO=C:/Users/asingh66/tidal-portfolio-siting
CURVE=$REPO/results/vp/turbine_modification/gen5/groups/pooled/1mw
PY=/mnt/c/Users/asingh66/tidal-portfolio-siting/.venv/Scripts/python.exe

export PYTHONIOENCODING=utf-8
export TIDAL_OBJECTIVE=energy TIDAL_VARIANT=gen5 TIDAL_STEPUP_KV=6.6
export TIDAL_CURVE_DIR="$CURVE"

run() {
  MW=$1; TARGETS=$2
  OUT=$REPO/results/vp/max_energy/gen5/groups/pooled/${MW}mw_frontier
  echo "======== ${MW} MW -> ${OUT} (targets ${TARGETS}) ========"
  TIDAL_P_TARGET_MW=$MW TIDAL_LCOE_TARGETS=$TARGETS TIDAL_RESULTS_DIR="$OUT" "$PY" 05_optimize.py || { echo "SOLVE FAILED $MW"; return 1; }
  TIDAL_P_TARGET_MW=$MW TIDAL_RESULTS_DIR="$OUT" "$PY" plot_results.py || { echo "PLOT FAILED $MW"; return 1; }
  echo "======== ${MW} MW DONE ========"
}

case "${1:-all}" in
  1)   run 1   "646,647,648,649,650,651,652" ;;
  5)   run 5   "658,661,664,667,670,673,676,679,681" ;;
  25)  run 25  "784,794,804,814,824,834,844,854,858" ;;
  100) run 100 "1029,1045,1061,1077,1093,1109,1125,1141,1157,1172" ;;
  all)
    run 1   "646,647,648,649,650,651,652"
    run 5   "658,661,664,667,670,673,676,679,681"
    run 25  "784,794,804,814,824,834,844,854,858"
    run 100 "1029,1045,1061,1077,1093,1109,1125,1141,1157,1172"
    ;;
esac
echo ALL_DONE
