# Paper campaign — full §3 rerun (2026-06-10)

One coherent configuration for every result in the paper: **VP Gen5 family,
pooled East Coast scope, 6.6 kV per-TriFrame step-up transmission**, LCOE grid
$600–$1,500/MWh in $100 steps, capacity targets {1, 5, 25, 100} MW.

All results live inside this folder (no writes to `results/`). Every
experiment re-runs its pipeline steps fresh — no reuse of pre-campaign
artifacts — so every number in the paper traces to this campaign.

## Design decisions (settled 2026-06-10)

1. **Scope = pooled East Coast.** NE+NY ≈ pooled holds only at pilot scale:
   variance ratio NE+NY/pooled from the gen5 turbine_modification cells is
   1.00–1.06 at 1–5 MW, 1.09–1.21 at 25 MW, 1.54–1.81 at 100 MW (with a $100
   LCOE-floor gap). Geographic concentration is therefore a *result*, not an
   assumption. `05_scope_restriction` quantifies the restriction cost.
2. **6.6 kV step-up is the design**, not an experiment. Justified in §2
   methods (RITE's as-built 480 V does not scale); `04_voltage_justification`
   produces the supplementary evidence. Voltage enters the pipeline at step 5
   only (cable re-selection + Collin transformer term in the optimizer), so
   the 480 V arm shares steps 1–4 with `01_baseline`.
3. **Engine = hybrid pipeline as-is**: Python (extract, screen, optimize) +
   MATLAB (t_tide histograms, covariance), Windows venv + Git Bash.
4. **Diameter family extended upward** to D = 6, 7, 8 (see
   `02_diameter_family/EXPERIMENT.md` for the derived specs and the v_rated
   rule for D > 5).

## Experiments and run order

| # | Experiment | Cells | Est. wall time |
|---|---|---|---|
| 01 | `01_baseline` — gen5, 6.6 kV | steps 1–4 + 4 MW | ~1.5–2 h |
| 02 | `02_diameter_family` — modvp{2,3,4,6,7,8}, 6.6 kV | 6 × (steps 1–4 + 4 MW) | ~7–9 h |
| 03 | `03_rated_cutin` — 5×3 speed grid, 6.6 kV | 15 × (steps 3–4 + 4 MW) | ~15–25 h |
| 04 | `04_voltage_justification` — gen5, 480 V | 4 × step 5 | ~1–2 h |
| 05 | `05_scope_restriction` — gen5, NE+NY, 6.6 kV | steps 1–4 + 4 MW | ~1.5 h |

Order: 01 first (03 and 04 read its outputs), then 04, 02, 05, 03.
Each driver is resumable (existing `.nc` outputs are skipped; delete to force
a rebuild) and appends per-step timings to its own `run_summary.txt`.

## Paper mapping

- §3.1 candidate pool ← 01 (candidates.nc)
- §3.2 frontiers × scale + §3.3 composition ← 01
- §3.4–3.5 turbine modification ← 02 (diameter), 03 (ratings)
- §2 / supplementary ← 04 (voltage), 05 (scope restriction)

## Status

Track via each experiment's `run_summary.txt`. Smoke test = `01_baseline/run.sh smoke`
(steps 1–4 + the 1 MW cell only).
