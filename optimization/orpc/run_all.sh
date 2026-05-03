#!/usr/bin/env bash
# Run the full ORPC TidGen 2.0 pipeline for pooled + every state in the boundaries CSV.
# Continues past individual failures (so one bad state doesn't kill the loop).

set -u  # intentionally NOT -e: we want to continue past failures

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
CSV="$SCRIPT_DIR/config/east_coast_state_boundaries.csv"
SUMMARY="$REPO_DIR/results/orpc/run_all_summary.txt"

STATES=(pooled)
while IFS=, read -r state _ _ _ _; do
    [[ "$state" == "State" ]] && continue
    STATES+=("$state")
done < "$CSV"

echo "States to run (${#STATES[@]}): ${STATES[*]}"
echo "Summary log: $SUMMARY"

mkdir -p "$REPO_DIR/results/orpc"
: > "$SUMMARY"
echo "Run started: $(date)" >> "$SUMMARY"
echo "" >> "$SUMMARY"

for state in "${STATES[@]}"; do
    echo ""
    echo "####################################################"
    echo "#### $state"
    echo "####################################################"

    t_start=$(date +%s)
    if "$SCRIPT_DIR/run_state.sh" "$state"; then
        status="OK"
    else
        status="FAILED (exit $?)"
    fi
    t_end=$(date +%s)
    elapsed=$(( t_end - t_start ))

    printf "%-30s  %-20s  %5d s\n" "$state" "$status" "$elapsed" >> "$SUMMARY"
done

echo "" >> "$SUMMARY"
echo "Run finished: $(date)" >> "$SUMMARY"

echo ""
echo "===== run_all summary ====="
cat "$SUMMARY"
