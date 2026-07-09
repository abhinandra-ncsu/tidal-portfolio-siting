#!/usr/bin/env bash
# Max-energy objective experiment driver — gen5 at 6.6 kV across 4 scales.
#
# Flips the optimizer objective to maximize delivered energy
# (TIDAL_OBJECTIVE=energy); constraints are unchanged.
#
# Layout: steps 1-4 outputs (harmonics, histograms, candidates, covariance)
# are MW-independent, so they live ONCE at the scope level — seeded as
# symlinks to the baseline's files. Each <MW>mw/ subdir holds only the
# per-MW step-5 outputs (optimization_results.nc, figures/, log.txt).
# TIDAL_RESOURCE_DIR / TIDAL_CURVE_DIR point the pipeline at the scope level.
#
# Min-variance anchors for the comparison are the existing 6.6 kV step-up
# runs at the same MW and LCOE grid (results/vp/transmission_stepup/).
#
# Writes outputs to:
#   results/vp/max_energy/gen5/groups/new_england_new_york/        (shared .nc)
#   results/vp/max_energy/gen5/groups/new_england_new_york/<MW>mw/ (per-MW)
#
# Per-cell status logged to results/vp/max_energy/run_summary.txt.
# See experiments/max_energy_objective/EXPERIMENT.md for the design.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

VARIANT="gen5"
SCOPE="new_england_new_york"
STEPUP_KV="6.6"
MW_TARGETS=(1 5 25 100)

# NE+NY group composition (matches the turbine_modification driver).
NE_NY_STATES="Maine_coastline,New_Hampshire_coastline,Massachusetts_coastline,Rhode_Island_coastline,Connecticut_coastline,New_York_coastline"

export TIDAL_LCOE_TARGETS="600,700,800,900,1000,1100,1200,1300,1400,1500"
export TIDAL_VARIANT="$VARIANT"
export TIDAL_STEPUP_KV="$STEPUP_KV"
export TIDAL_OBJECTIVE="energy"

BASELINE_BASE="$REPO_DIR/results/vp/turbine_modification/$VARIANT/groups/$SCOPE"
SCOPE_DIR="$REPO_DIR/results/vp/max_energy/$VARIANT/groups/$SCOPE"

# The hooks are read by Python and MATLAB, which need Windows-style paths;
# bash-side ops below keep the POSIX form.
mkdir -p "$SCOPE_DIR"
export TIDAL_RESOURCE_DIR="$(cygpath -m "$SCOPE_DIR")"
export TIDAL_CURVE_DIR="$TIDAL_RESOURCE_DIR"

# Seed the scope level once: the four shared files are identical to the
# baseline's, so link instead of recomputing. If the baseline is missing,
# the first cell computes them into the scope dir.
for name in harmonics.nc histograms.nc candidates.nc covariance.nc; do
    src="$BASELINE_BASE/1mw/$name"
    if [[ -e "$src" ]]; then
        ln -sf "$src" "$SCOPE_DIR/$name"
    else
        echo "WARNING: $src not found; pipeline will compute it into $SCOPE_DIR"
    fi
done

SUMMARY_DIR="$REPO_DIR/results/vp/max_energy"
SUMMARY="$SUMMARY_DIR/run_summary.txt"
mkdir -p "$SUMMARY_DIR"
: > "$SUMMARY"
{
    echo "Max-energy objective sweep"
    echo "Started:   $(date)"
    echo "Variant:   $VARIANT"
    echo "Scope:     $SCOPE"
    echo "Step-up:   $STEPUP_KV kV"
    echo "Objective: energy"
    echo "MW:        ${MW_TARGETS[*]}"
    echo "LCOE:      $TIDAL_LCOE_TARGETS"
    echo ""
    printf "%-6s  %-20s  %8s\n" "MW" "status" "elapsed_s"
} >> "$SUMMARY"

for mw in "${MW_TARGETS[@]}"; do
    echo ""
    echo "############################################################"
    echo "## variant=$VARIANT  scope=$SCOPE  mw=${mw}MW  objective=energy  stepup=${STEPUP_KV}kV"
    echo "############################################################"

    export TIDAL_P_TARGET_MW="$mw"

    t_start=$(date +%s)
    if "$SCRIPT_DIR/run_group.sh" "$SCOPE" "$NE_NY_STATES"; then
        status="OK"
    else
        status="FAILED($?)"
    fi
    t_end=$(date +%s)
    elapsed=$(( t_end - t_start ))

    printf "%-6s  %-20s  %8d\n" "${mw}MW" "$status" "$elapsed" >> "$SUMMARY"
done

echo "" >> "$SUMMARY"
echo "Finished: $(date)" >> "$SUMMARY"

echo ""
echo "===== max_energy sweep summary ====="
cat "$SUMMARY"
