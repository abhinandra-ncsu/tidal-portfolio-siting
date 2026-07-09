# Runbook — executing the paper campaign (for the agent on energizelab)

You are running a pre-built experiment campaign. Everything is already
designed, scaffolded, and partially verified — your job is to validate one
thing, run a smoke test, inspect it, then execute five experiments in order
and report. **Do not redesign anything.** Read `CAMPAIGN.md` and each
experiment's `EXPERIMENT.md` for context before starting.

## Hard guardrails

1. **No git operations.** This working tree is uncommitted by deliberate
   choice and is the ONLY copy of the code that produced the existing paper
   results. Never run `git checkout`, `git stash`, `git clean`, or commit.
2. **Do not edit** `optimization/vp/config/config.py` or `config.m` (variant
   specs were extended 2026-06-10; backups: `config.{py,m}.bak_20260610`).
3. **Write nowhere outside** `experiments/paper_campaign/*/results/`.
4. Run drivers from **Git Bash** (`C:\Program Files\Git\bin\bash.exe`), not
   WSL — the pipeline assumes the Windows venv (`.venv/Scripts/python.exe`)
   and Git Bash `cp`/path semantics.
5. Run experiments **serially** — they share MATLAB/Gurobi/CPU. The drivers
   have per-experiment locks but nothing stops two experiments thrashing.
6. All drivers are **resumable**: existing `.nc` outputs are skipped. After
   any interruption, re-run the same command; never delete outputs to "start
   clean" unless a step is provably corrupt.

## Step 0 — validate config.m parses with the new variants (~1 min)

The Python side is already verified. MATLAB side (from Git Bash):

```bash
cd /c/Users/asingh66/tidal-portfolio-siting/optimization/vp
TIDAL_VARIANT=modvp8 "/c/Program Files/MATLAB/R2024b/bin/matlab.exe" -batch \
  "cd config; cfg=config(); fprintf('A=%.2f Vr=%.2f Vci=%.2f P=%.0f\n', cfg.AREA, cfg.V_RATED, cfg.V_CUT_IN, cfg.P_RATED)"
```

Expected: `A=50.27 Vr=1.89 Vci=0.57 P=64400`. If MATLAB errors, STOP and
report — do not attempt to fix config.m.

## Step 1 — smoke test (~35–40 min)

```bash
cd /c/Users/asingh66/tidal-portfolio-siting/experiments/paper_campaign
./01_baseline/run.sh smoke
```

## Step 2 — inspection gate (do NOT proceed on failure)

1. `01_baseline/results/run_summary.txt` — all five steps present, no
   `_FAILED` rows.
2. Candidate count (printed in `build.log` / `candidates.nc` site dimension):
   expect roughly 13,000–14,000 (pooled gen5 eligibility pool; it is
   voltage-independent). Order-of-magnitude deviation = stop and report.
3. `1mw/optimization_results.nc`: compare against the May 480 V cell at
   `../../results/vp/turbine_modification/gen5/groups/pooled/1mw/optimization_results.nc`.
   At matched LCOE caps the new (6.6 kV) variance should be **at or below**
   the 480 V variance, and the feasibility floor at or below $700. If 6.6 kV
   is *worse* than 480 V anywhere, stop and report — that inverts the known
   physics.

## Step 3 — full campaign (serial, ~25–40 h total)

```bash
./01_baseline/run.sh               # resumes past the smoke cells (~1.5-2 h)
./04_voltage_justification/run.sh  # step-5 only, reads 01 (~1-2 h)
./02_diameter_family/run.sh modvp6 # single-variant gate for the NEW variants (~1-1.5 h)
# inspect 02 summary for modvp6 sanity (steps complete, optimize rows OK), then:
./02_diameter_family/run.sh        # remaining variants (~6-8 h)
./05_scope_restriction/run.sh      # ~1.5 h
./03_rated_cutin/run.sh            # long pole (~15-25 h)
```

Launch each in the background and watch its `results/run_summary.txt`; a
driver has finished when the summary's `Finished:` line appears. Between
experiments, scan the summary for `_FAILED` rows.

## What "expected" looks like

- `infeasible` statuses at low LCOE caps / small MW are NORMAL (the $600 cap
  was infeasible at 480 V; some cells stay infeasible at 6.6 kV).
- modvp2 was infeasible at most scales in the May matrix — if it's infeasible
  here too, that is a result, not an error.
- Anomalies worth stopping for: `cov_FAILED` / `opt_FAILED` rows, a variant
  with zero candidates, MATLAB license errors, or every cap infeasible at
  every scale for gen5.

## Report back

Per experiment: wall time, any `_FAILED`/anomaly rows, and for 01 the LCOE
floor per MW target. Nothing else — analysis happens in a later session.
