# Max-energy objective — experiment design brief

**Date:** 2026-06-06 (design, implementation, and sweep same day)
**Status:** sweep complete; analysis layer + writeup pending
**Baseline it modifies:** the objective of the BQP in
`optimization/vp/methodology/optimization_formulation.md`, evaluated on the VP Gen5
TriFrame at the 6.6 kV per-device step-up electrical configuration
(`experiments/transmission_stepup/EXPERIMENT.md`).

---

## Question

This experiment makes one change and asks one question.

The change: swap the objective. The baseline minimizes portfolio variance (x^T Σ x);
energy appears only inside the LCOE constraint. The new run maximizes portfolio
energy (Σ E_i x_i). Everything else stays.

The question: **same budget, same N, same candidate sites — how far apart are the
two portfolios, in energy, in variance, and in the sites they pick?**

## Formulation

```
max   Σ_i E_i x_i                                       (portfolio energy, MWh/yr)
s.t.  Σ_i x_i = N                                        (deploy N TriFrames)
      C_const(N) + Σ_i x_i (c_site_i − L · E_i) ≤ 0      (LCOE ≤ target)
      x_i ∈ {0, 1}                                       (binary site selection)
```

Same decision variable. Same constraints. Only the objective moves.

- **E_i is delivered-to-shore energy — transmission losses are already in it.**
  `compute_energy()` applies each site's cable loss as a (1 − loss_i) factor.
  loss_i is the I²R loss of the cable the selector assigns to that site's shore
  distance, computed at the step-up voltage. Availability (0.95) is in there too.
  The objective therefore maximizes what reaches shore, not what the rotors
  produce. No extra loss term is needed. The same net E_i sits inside the LCOE
  constraint, so objective and constraint price energy identically. (The one loss
  the model carries nowhere is transformer efficiency — the step-up experiment
  models the transformer as a cost only. Held, not changed, here.)
- N = ceil(P_target / P_TF), P_TF = 93.6 kW (gen5, 3 × 31.2 kW).
- The LCOE constraint is the same linearized ratio as the baseline
  (`optimization_formulation.md` §Constraints).
- Σ drops out of the objective. The problem collapses from a binary quadratic
  program (BQP) to an integer linear program (ILP). Gurobi solves it in seconds.


## What is swept vs held

- **Swept:** the objective ∈ {min-variance, max-energy}. That is the experiment.
- **Held:** turbine (gen5, no design overrides), electrical configuration (6.6 kV
  per-device step-up — the adopted VP case), power factor 0.95, the LCOE ceiling and
  targets, N per scale, and all step-0–4 pipeline outputs (harmonics, histograms,
  candidate screen, covariance). The min-variance anchors already exist at
  `results/vp/transmission_stepup/gen5/groups/.../` — no baseline re-runs.

Scope and scale are deliberately deferred. The formulation is settled first; the
sweep grid is a later decision.

## What changes, and what doesn't

| Piece | Changes? | Why |
|---|---|---|
| `methodology/energy/` + `compute_energy()` | No | E_i is computed identically — same power curve, histograms, cable loss |
| `methodology/cost/` + `compute_c_const()`, `compute_c_site()` | No | Costs live only in the LCOE constraint, which is untouched |
| Steps 1–4 (harmonics → covariance) | No | Reused via symlinks / input-dir hooks |
| `methodology/optimization_formulation.md` | Yes | Gains the max-energy variant when implementation lands |
| `05_optimize.py` | Yes | Objective switch via a `TIDAL_OBJECTIVE` env var (`variance` default, `energy` opt-in), matching the `TIDAL_VARIANT` / `TIDAL_STEPUP_KV` pattern. Unset ⇒ baseline runs stay bit-identical |

## Two implementation traps, named now

**1. The margin screen is invalid under max-energy.** Before solving, `05_optimize.py`
computes each site's margin, m_i = c_site_i − L·E_i. Negative margin: the site earns
more than it costs at price L, so it pushes the budget constraint toward feasibility.
Positive margin: the opposite. The baseline deletes every positive-margin site before
building the model. The screen exists to shrink the dense covariance matrix — the
quadratic objective needs ~n²/2 terms in solver memory, and at ~18k sites memory only
survives if n drops first. Under min-variance the deletion is harmless: the objective
gains nothing from any particular site, so there is no reason to spend budget slack
on one that hurts the budget.

Max-energy breaks that logic. The objective now wants high-E sites, and a high-E
site can carry a positive margin (strong resource, long expensive cable). Numbers:
N = 2, C_const = $30/yr. Site A: E = 100, m = −$50. Site B: E = 90, m = +$10.
Site C: E = 10, m = −$50. Portfolio {A, B}: budget = 30 − 50 + 10 = −10 ≤ 0,
feasible, energy 190. Portfolio {A, C}: feasible, energy 110. The optimum is
{A, B} — A's surplus pays for B. The screen deletes B and forces the inferior
{A, C}.

Fix: skip the reduction when `TIDAL_OBJECTIVE=energy`. It is also unnecessary
there — a linear objective builds no dense Q, so all ~18k binaries fit comfortably.

**2. Covariance stays loaded — for reporting, not optimizing.** Σ leaves the
objective, but the result we care about is the σ² of whatever portfolio max-energy
picks. The optimizer computes `x^T Σ x` post-hoc on the solution and writes it to
the results .nc exactly as the min-variance run does, so the two anchors read from
the same field.

## Degeneracy check

Strip away the budget constraint for a moment. Maximizing Σ E_i x_i with Σ x_i = N
has a trivial solution: sort the sites by E_i and take the top N. No solver needed.
The only thing that can force a different answer is the LCOE ceiling: if the top-N
set busts the budget, the solver must swap expensive high-E sites for cheaper,
slightly-lower-E ones. So the constraint's slack at the optimum tells us what kind
of answer we got:

- **Slack > 0 (constraint loose):** the solution is the naive top-N-by-E sort.
  Economics never touched the siting — "degenerate," the optimizer added nothing.
- **Slack = 0 (constraint binding):** the budget actively reshaped the portfolio.
  A real optimization happened.

That is a finding, not a bug. It maps where economics starts to discipline an
energy-chaser. Expect degeneracy at loose L and small N (the top handful of sites
is easy to afford), and binding at tight L and large N (the step-up runs already
show the constraint binding harder at 100 MW). Report, per (scale, L): the slack at
the solution, and whether the selected set equals the naive top-N set. Where the
crossover sits is part of the result.

## Success criteria

Success is a quantified side-by-side comparison: the two objectives' portfolios at
matched (scale, L). The question is answered once the max-energy runs are done and,
for each (scale, L) where both objectives are optimal, we can report:

- **ΔE** = E_maxE − E_minVar — the energy the min-variance portfolio left on the table
- **Δσ²** = σ²_maxE − σ²_minVar — the variance the max-energy portfolio took on
- **Site overlap** between the two selections — distinguishes "same sites, reshuffled
  margins" from "genuinely different portfolio" (same diagnostic as the step-up brief)
- **LCOE-constraint slack** + top-N degeneracy flag (see above)

Decision rule: read the four numbers, then decide whether any follow-up experiment
is worth it. Nothing is pre-committed.

How the numbers relate — the deltas and the overlap answer different questions.
Identical portfolios force ΔE = Δσ² = 0, so large deltas do imply different sites.
The converse fails: different sites do not imply large deltas, because the two
objectives can pick different but energy-equivalent portfolios. That makes the
small-ΔE case ambiguous until overlap splits it:

- **Small ΔE, high overlap** — the two objectives agree on the sites. One portfolio
  serves both goals.
- **Small ΔE, low overlap** — many portfolios harvest near-equal energy, and
  min-variance picks the steady one. Steadiness is free. This is the strongest
  result on offer.
- **Large ΔE and Δσ²** — a genuine tradeoff. Energy and steadiness pull siting in
  different directions, and choosing between them costs real MWh or real σ².

## Implementation status

**Code in place (2026-06-06, at `optimization/vp/`):**

- `config/config.py` reads `TIDAL_OBJECTIVE` (`variance` default / `energy`),
  validates it, and routes energy-objective results to a `max_energy` path
  segment: `results/vp/max_energy/<variant>/groups/<scope>/<MW>mw/`.
- `05_optimize.py` branches the Gurobi objective (`max E @ x` vs
  `min x @ Σ @ x`), skips the margin screen under `energy` (trap 1; Σ stays
  unsliced — no 18k² copy), drops the screen-consistent `n_feasible < N`
  pre-check under `energy` (keeps the exact best-N-margins check, which is
  objective-independent), and stores `lcoe_slack` ($/yr, per target) plus an
  `objective` attr in the results .nc. Post-hoc σ² needed no new code.
- `run_max_energy.sh` orchestrates gen5 × NE+NY × {1, 5, 25, 100} MW at
  6.6 kV with L ∈ {600…1500} in $100 steps — the exact grid of the existing
  min-variance step-up anchors — symlinking the baseline steps 1–4 .nc
  outputs so only step 5 runs.

When `TIDAL_OBJECTIVE` is unset, all of the above is a no-op — variance runs
are bit-identical to the pre-change pipeline.

**Verified:** results-dir routing (baseline / step-up / energy / invalid value)
and `solve_bqp` on the trap-1 counterexample — energy mode selects the
positive-margin site B ({A,B}, 190 MWh), variance mode selects {A,C}.

**Layout rework (same day).** Steps 1–4 outputs (harmonics, histograms,
candidates, covariance) are MW-independent, so they now live once at the scope
level instead of being symlinked into every `<MW>mw/` dir. Changes: steps 1–4
write their outputs to the resource/curve dirs (`TIDAL_RESOURCE_DIR` /
`TIDAL_CURVE_DIR`, falling back to the results dir — old single-dir flows are
untouched); `plot_results.py` reads covariance from the curve dir;
`run_group.sh` skip-guards steps 1–4 in bash so a skipped step never boots
MATLAB (was minutes of dead time per cell); the driver seeds the scope level
from the baseline files and exports the two hooks. Per-MW dirs now hold only
`optimization_results.nc`, `figures/`, `log.txt`. Two Windows traps fixed on
the way: `readarray` keeps the `\r` from Windows-Python CRLF output (fixed
with `tr -d '\r'`), and the BQP's 2% MIPGap left the ILP's E_max non-monotone
in L and corrupted the top-N flag (energy objective now solves at MIPGap=0).

**Sweep — complete (2026-06-06).** 4/4 cells OK at 61–87 s each (the
min-variance BQP sweep needed 415–1105 s/cell). Outputs at
`results/vp/max_energy/gen5/groups/new_england_new_york/`.

**Pending:** the analysis layer (`analyze.py` + figures: ΔE/Δσ² vs L panels,
overlap, slack/degeneracy table), SYNTHESIS.md, and the commit.

## Headline findings (first pass, from the in-line comparison)

**Feasibility is identical to the min-variance anchors at every (scale, L)** —
floors at $700 (1, 5 MW), $800 (25 MW), $1100 (100 MW). Same constraints, same
feasible set, now confirmed empirically.

**The tradeoff is real and large — the "large ΔE and Δσ²" branch of the
decision rule.** At matched (scale, L):

| MW | floor L | ΔE at floor | Δσ² at floor | ΔE at L=1500 | Δσ² at L=1500 | overlap (floor→1500) |
|---|---|---|---|---|---|---|
| 1   | 700  | +10.1% | ×2.0 | +137% | ×16.1 | 64% → 18% |
| 5   | 700  | +10.9% | ×3.9 | +140% | ×37.7 | 52% → 22% |
| 25  | 800  | +9.3%  | ×1.9 | +126% | ×36.3 | 68% → 20% |
| 100 | 1100 | +22.6% | ×2.5 | +79%  | ×10.0 | 59% → 28% |

**Mechanism: ΔE grows with L because min-variance walks away from energy.**
The max-energy portfolio is one fixed set per scale (the top-N, once
affordable) — its E and σ² are flat in L. Min-variance spends every extra
dollar of slack on decorrelated, lower-yield sites, so its E falls and its σ²
falls as L rises. At loose L it harvests well under half the achievable energy
— the price of a 10–38× variance reduction.

**Degeneracy: the budget disciplines an energy-chaser only at large N, and
only at the feasibility floor.** At 1 and 5 MW the top-N-by-E set is already
affordable at the floor — the solve is a sort at every feasible L. At 25 and
100 MW exactly one cell each is a true constrained optimum: the floor
(slack $758/yr and $1,500/yr — binding), where the budget vetoes expensive
high-E sites. One $100 step above the floor, the sort regime takes over.
Caveat on reading slack: slack > 0 does not prove the solve was a sort — in an
integer program the budget can veto the greedy set while the chosen set keeps
slack (no complementary slackness); the set-equality flag is the real test.

## References

## References

- `optimization/vp/methodology/optimization_formulation.md` — baseline BQP.
- `experiments/transmission_stepup/EXPERIMENT.md` — electrical configuration held
  here; source of the min-variance anchor runs and the overlap/metric conventions.
