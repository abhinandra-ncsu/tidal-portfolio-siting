#!/usr/bin/env bash
# Turbine modification experiment driver — sweep variant x scope x MW target.
#
# Matrix:
#   variants: gen5, modvp4, modvp3, modvp2     (4)
#   scopes:   new_england_new_york, pooled     (2)
#   MW:       1, 5, 25, 100                    (4)
# = 32 pipeline runs, each producing a 10-point LCOE frontier at
#   $100 intervals from $600 to $1500.
#
# Writes outputs to:
#   results/vp/turbine_modification/<variant>/groups/<scope>/<MW>mw/
#
# Per-cell status logged to results/vp/turbine_modification/run_summary.txt.
# Continues past individual cell failures (set -u, NOT -e) so one bad
# cell does not kill the rest of the matrix.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

VARIANTS=(gen5 modvp4 modvp3 modvp2)
SCOPES=(new_england_new_york pooled)
MW_TARGETS=(1 5 25 100)

# NE+NY group composition (matches existing ORPC new_england_ny states list).
NE_NY_STATES="Maine_coastline,New_Hampshire_coastline,Massachusetts_coastline,Rhode_Island_coastline,Connecticut_coastline,New_York_coastline"

export TIDAL_LCOE_TARGETS="600,700,800,900,1000,1100,1200,1300,1400,1500"

SUMMARY_DIR="$REPO_DIR/results/vp/turbine_modification"
SUMMARY="$SUMMARY_DIR/run_summary.txt"
mkdir -p "$SUMMARY_DIR"
: > "$SUMMARY"
{
    echo "Turbine modification sweep"
    echo "Started: $(date)"
    echo "Variants: ${VARIANTS[*]}"
    echo "Scopes:   ${SCOPES[*]}"
    echo "MW:       ${MW_TARGETS[*]}"
    echo "LCOE:     $TIDAL_LCOE_TARGETS"
    echo ""
    printf "%-8s  %-25s  %-6s  %-20s  %8s\n" "variant" "scope" "MW" "status" "elapsed_s"
} >> "$SUMMARY"

for variant in "${VARIANTS[@]}"; do
    for scope in "${SCOPES[@]}"; do
        for mw in "${MW_TARGETS[@]}"; do
            echo ""
            echo "############################################################"
            echo "## variant=$variant  scope=$scope  mw=${mw}MW"
            echo "############################################################"

            export TIDAL_VARIANT="$variant"
            export TIDAL_P_TARGET_MW="$mw"

            t_start=$(date +%s)
            if [[ "$scope" == "pooled" ]]; then
                unset TIDAL_GROUP TIDAL_STATE 2>/dev/null || true
                if "$SCRIPT_DIR/run_state.sh" pooled; then
                    status="OK"
                else
                    status="FAILED($?)"
                fi
            else
                if "$SCRIPT_DIR/run_group.sh" "$scope" "$NE_NY_STATES"; then
                    status="OK"
                else
                    status="FAILED($?)"
                fi
            fi
            t_end=$(date +%s)
            elapsed=$(( t_end - t_start ))

            printf "%-8s  %-25s  %-6s  %-20s  %8d\n" "$variant" "$scope" "${mw}MW" "$status" "$elapsed" >> "$SUMMARY"
        done
    done
done

echo "" >> "$SUMMARY"
echo "Finished: $(date)" >> "$SUMMARY"

echo ""
echo "===== turbine_modification sweep summary ====="
cat "$SUMMARY"
