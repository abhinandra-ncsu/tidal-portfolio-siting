#!/usr/bin/env bash
# Transmission step-up experiment driver — gen5 at 6.6 kV across 4 scales.
#
# Reuses the baseline (480 V) steps 1-4 outputs by symlinking them into each
# step-up results dir before invoking the pipeline; only step 5 (the optimizer)
# re-runs at the new voltage with the transformer term added to C_const.
#
# Writes outputs to:
#   results/vp/transmission_stepup/gen5/groups/new_england_new_york/<MW>mw/
#
# Per-cell status logged to results/vp/transmission_stepup/run_summary.txt.
# See experiments/transmission_stepup/EXPERIMENT.md for the design.

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

BASELINE_BASE="$REPO_DIR/results/vp/turbine_modification/$VARIANT/groups/$SCOPE"
STEPUP_BASE="$REPO_DIR/results/vp/transmission_stepup/$VARIANT/groups/$SCOPE"

SUMMARY_DIR="$REPO_DIR/results/vp/transmission_stepup"
SUMMARY="$SUMMARY_DIR/run_summary.txt"
mkdir -p "$SUMMARY_DIR"
: > "$SUMMARY"
{
    echo "Transmission step-up sweep"
    echo "Started:  $(date)"
    echo "Variant:  $VARIANT"
    echo "Scope:    $SCOPE"
    echo "Step-up:  $STEPUP_KV kV"
    echo "MW:       ${MW_TARGETS[*]}"
    echo "LCOE:     $TIDAL_LCOE_TARGETS"
    echo ""
    printf "%-6s  %-20s  %8s\n" "MW" "status" "elapsed_s"
} >> "$SUMMARY"

for mw in "${MW_TARGETS[@]}"; do
    echo ""
    echo "############################################################"
    echo "## variant=$VARIANT  scope=$SCOPE  mw=${mw}MW  stepup=${STEPUP_KV}kV"
    echo "############################################################"

    export TIDAL_P_TARGET_MW="$mw"

    baseline_dir="$BASELINE_BASE/${mw}mw"
    stepup_dir="$STEPUP_BASE/${mw}mw"

    # Symlink baseline steps 1-4 outputs into the step-up dir so the pipeline's
    # auto-skip kicks in and only step 5 (the optimizer) re-runs at 6.6 kV.
    # Exclude optimization_results.nc — that is the step-5 output we want to regenerate.
    if [[ -d "$baseline_dir" ]]; then
        mkdir -p "$stepup_dir"
        for f in "$baseline_dir"/*.nc; do
            [[ -e "$f" ]] || continue
            name=$(basename "$f")
            if [[ "$name" != "optimization_results.nc" ]]; then
                ln -sf "$f" "$stepup_dir/$name"
            fi
        done
    else
        echo "WARNING: baseline dir not found at $baseline_dir; pipeline will re-run all steps"
    fi

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
echo "===== transmission_stepup sweep summary ====="
cat "$SUMMARY"
