#!/usr/bin/env bash
# Max-energy efficient-frontier sweep — gen5 at 6.6 kV across 4 scales.
#
# The max-energy frontier (max portfolio energy s.t. LCOE <= L) only bends
# inside a narrow band [L_min, L*_E], which the original $100 grid stepped over.
# This driver re-runs step 5 on a FINE grid sized to each scale's band, so the
# achieved-LCOE-vs-energy curve is actually traced instead of collapsing to one
# or two points. Band endpoints come from
# results/vp/max_energy/analysis/find_frontier_band.py:
#
#   scale   L_min    L*_E     band $
#    1 MW   645.5    651.4      5.8
#    5 MW   657.6    680.8     23.2
#   25 MW   783.5    857.3     73.8
#  100 MW  1028.2   1171.2    143.0
#
# Each scale's target list is the UNION of:
#   - the original coarse anchor grid ($600..$1500 step $100) — kept so the
#     transmission_stepup min-variance comparison cells still match, and
#   - a fine grid spanning [L_min - margin, L*_E + margin] at a per-scale step,
#     with a couple of points below L_min (infeasible cliff) and above L*_E
#     (plateau).
#
# Outputs OVERWRITE the existing per-MW dirs (the .nc gains the fine targets
# while keeping every coarse cell). Spatial maps are skipped (dozens of targets
# would mean dozens of slow shoreline redraws); the frontier figure is built
# separately by analysis/plot_frontier.py.
#
# Steps 1-4 are MW-independent and already seeded at the scope level, so the
# run_group.sh guards skip them (no MATLAB boot).

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

VARIANT="gen5"
SCOPE="new_england_new_york"
STEPUP_KV="6.6"
MW_TARGETS=(1 5 25 100)

NE_NY_STATES="Maine_coastline,New_Hampshire_coastline,Massachusetts_coastline,Rhode_Island_coastline,Connecticut_coastline,New_York_coastline"

COARSE="600 700 800 900 1000 1100 1200 1300 1400 1500"

# Per-scale fine grid (first step last) — see band table above.
fine_grid() {
    case "$1" in
        1)   seq 644 0.5 653  ;;   # band 645.5-651.4, step $0.50
        5)   seq 656 2   684  ;;   # band 657.6-680.8, step $2
        25)  seq 780 5   865  ;;   # band 783.5-857.3, step $5
        100) seq 1025 10 1175 ;;   # band 1028.2-1171.2, step $10
    esac
}

# Union of coarse + fine, numerically sorted, de-duplicated, comma-joined.
targets_for() {
    { echo "$COARSE" | tr ' ' '\n'; fine_grid "$1"; } \
        | sort -g -u | paste -sd, -
}

export TIDAL_VARIANT="$VARIANT"
export TIDAL_STEPUP_KV="$STEPUP_KV"
export TIDAL_OBJECTIVE="energy"
export TIDAL_SKIP_SPATIAL=1
export MATLAB_BIN="${MATLAB_BIN:-/c/Program Files/MATLAB/R2024b/bin/matlab.exe}"

BASELINE_BASE="$REPO_DIR/results/vp/turbine_modification/$VARIANT/groups/$SCOPE"
SCOPE_DIR="$REPO_DIR/results/vp/max_energy/$VARIANT/groups/$SCOPE"

mkdir -p "$SCOPE_DIR"
export TIDAL_RESOURCE_DIR="$(cygpath -m "$SCOPE_DIR")"
export TIDAL_CURVE_DIR="$TIDAL_RESOURCE_DIR"

# Seed the scope level once (steps 1-4 outputs); link to baseline if present.
for name in harmonics.nc histograms.nc candidates.nc covariance.nc; do
    src="$BASELINE_BASE/1mw/$name"
    if [[ -e "$src" && ! -e "$SCOPE_DIR/$name" ]]; then
        ln -sf "$src" "$SCOPE_DIR/$name"
    fi
done

SUMMARY="$REPO_DIR/results/vp/max_energy/run_summary_frontier.txt"
: > "$SUMMARY"
{
    echo "Max-energy efficient-frontier sweep"
    echo "Started:   $(date)"
    echo "Variant:   $VARIANT   Scope: $SCOPE   Step-up: $STEPUP_KV kV"
    echo ""
    printf "%-6s  %-20s  %8s  %s\n" "MW" "status" "elapsed_s" "n_targets"
} >> "$SUMMARY"

for mw in "${MW_TARGETS[@]}"; do
    TARGETS="$(targets_for "$mw")"
    n_targets=$(echo "$TARGETS" | tr ',' '\n' | wc -l | tr -d ' ')
    export TIDAL_LCOE_TARGETS="$TARGETS"
    export TIDAL_P_TARGET_MW="$mw"

    echo ""
    echo "############################################################"
    echo "## ${mw}MW  objective=energy  stepup=${STEPUP_KV}kV  ($n_targets targets)"
    echo "## $TARGETS"
    echo "############################################################"

    t_start=$(date +%s)
    if "$SCRIPT_DIR/run_group.sh" "$SCOPE" "$NE_NY_STATES"; then
        status="OK"
    else
        status="FAILED($?)"
    fi
    elapsed=$(( $(date +%s) - t_start ))

    printf "%-6s  %-20s  %8d  %d\n" "${mw}MW" "$status" "$elapsed" "$n_targets" >> "$SUMMARY"
done

echo "" >> "$SUMMARY"
echo "Finished: $(date)" >> "$SUMMARY"

echo ""
echo "===== max_energy frontier sweep summary ====="
cat "$SUMMARY"
