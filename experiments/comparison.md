# Comparison: VP Gen5 vs ORPC TidGen 2.0 at 10 + 50 + 100 MW, NE+NY

**Date started:** 2026-04-26
**Status:** all six runs complete; comparison plots pending

## Question

On the New England + New York coastline, how do VP Gen5 (TriFrame, 105 kW per frame) and ORPC TidGen 2.0 (single device, 500 kW) compare across:
1. The lowest LCOE cap at which a portfolio is feasible (LCOE floor),
2. The variance-vs-LCOE-cap frontier,
3. The set and spatial distribution of selected sites,
and how do these comparisons shift across three deployment targets (10, 50, 100 MW)?

## Why this experiment exists

Prior runs are not on the same axes:
- VP NE+NY at 5.25 MW (50 TriFrames), LCOE caps {800, 1200, 2000}.
- ORPC NE+NY at 50 MW (100 devices), LCOE caps {700, 800, …, 1500}.

Without a matched run, every cross-device claim is confounded by target size and LCOE-grid spacing. After running matched 100 MW runs first, the 100 MW LCOE floors (VP $1100, ORPC $800) were higher than the priors at smaller targets, so target size enters as its own dimension to vary. 50 MW was added second; 10 MW added third, giving three target points across which to observe how each device's LCOE floor and variance frontier change.

## Setup

- **Scope:** New England + New York (ME, NH, MA, RI, CT, NY). Reason: prior synthesis (`results/synthesis/SYNTHESIS.md`) showed ~89% of viable east-coast resource sits in this region and NE+NY captures 94–98% of pooled-scope variance benefit at 5.25 MW.

- **Targets (three points):**
  - **10 MW.**
    - VP: 96 TriFrames = 10.08 MW (rounded up from 95.24).
    - ORPC: 20 devices = 10.0 MW exactly.
  - **50 MW.**
    - VP: 477 TriFrames = 50.085 MW (rounded up from 476.19).
    - ORPC: 100 devices = 50.0 MW exactly.
  - **100 MW** (stakeholder framing).
    - VP: 953 TriFrames = 100.065 MW (rounded up from 952.38).
    - ORPC: 200 devices = 100.0 MW exactly.

- **LCOE grid (same at both targets):** {500, 600, 700, 800, 900, 1000, 1100, 1200} $/MWh. Spacing matches the existing ORPC grid. Starting at $500 because we do not know either device's LCOE floor at either target; the experiment must probe it, not assume it.

- **CF threshold:** 0.05 (unchanged from canonical pipelines).

- **Depth windows:** VP ≥10 m, ORPC 18–40 m. Device properties — not normalized away.

## Method

Each run solves a binary quadratic program: pick N sites (N = target MW ÷ device nameplate) that **minimize portfolio variance** — the variance of total power output across the selected sites, computed from pairwise covariances of harmonic-reconstructed velocity time series — subject to **portfolio LCOE ≤ cap** (total annualized CapEx + OpEx ÷ total annual energy of the selected sites). A run is reported **infeasible** when no selection of N sites can satisfy the LCOE constraint — a true no-solution-exists outcome, not a solver failure. Solver: Gurobi, MIP gap 2%, 30 min limit per cap. Full derivations live in `optimization/methodology/` (VP) and `optimization/orpc/methodology/` (ORPC); this section summarizes, it does not re-derive.

## What this experiment measures

1. **Variance vs LCOE-cap frontier** per device per target.
2. **Feasibility floor** per device per target — the lowest LCOE cap with a feasible portfolio.
3. **Spatial site selection** at a chosen cap per (device, target): count of sites selected, longitude/latitude range, mean CF, mean depth.
4. **How floors and frontiers change across 10, 50, 100 MW** — three target points per device.

## Success criterion

One headline figure overlaying all four frontiers with feasibility floors annotated, plus side-by-side spatial maps for VP and ORPC at a chosen cap (likely the lowest cap where both devices are feasible at 100 MW). All numbers reproducible by re-running step 5 against the cached steps 1–4 outputs.

## Decisions made and reason

- **Three targets (10, 50, 100 MW), not one:** the 100 MW run produced LCOE floors higher than priors at smaller targets, so target size was added as a varied dimension. 50 MW added second; 10 MW added third, giving three points per device to observe the floor-vs-target relationship rather than relying on a single point. Each additional target costs one optimizer run per device (~1 min) with cached steps 1–4.

- **Parameterize, don't fork:** added env-var hooks for `P_TARGET_MW` and `LCOE_TARGETS` to both pipeline `config.py` files. Defaults preserved so canonical runs still reproduce.

- **Symlink cached steps 1–4 outputs:** harmonics, histograms, candidates, and covariance only depend on scope + CF threshold + depth window. None change in this experiment. Symlinking avoids redundant computation and guarantees the new runs use bit-identical inputs to the canonical ones.

- **Output layout:** `results/comparison/{vp,orpc}_{10,50,100}mw/`. All six runs in one experiment folder, suffixed by target. Plot scripts at `results/comparison/scripts/`, figures at `results/comparison/figures/` (mirroring the `results/synthesis/` layout — keeps the experiment self-contained).

## Out of scope (deferred)

- **Mixed-device portfolios** — joint optimizer picking VP-or-ORPC per site under one shared budget. Needs an MILP reformulation. Not this experiment.
- **Other geographic scopes.** This experiment is NE+NY only. Pooled-scope rerun deferred unless the NE+NY findings at 100 MW disagree with prior synthesis.
- **Other targets** beyond 10/50/100 MW.

## Findings (2026-04-26)

**Variance (W²) by device × target × LCOE cap.** Bold = LCOE floor for that combo.

| Cap | VP 10 MW | VP 50 MW | VP 100 MW | ORPC 10 MW | ORPC 50 MW | ORPC 100 MW |
|----:|---------:|---------:|----------:|-----------:|-----------:|------------:|
| $500  | infeas | infeas | infeas | **2.64e+12** | infeas | infeas |
| $600  | infeas | infeas | infeas | 1.30e+12 | infeas | infeas |
| $700  | **2.50e+11** | infeas | infeas | 7.97e+11 | **3.39e+13** | infeas |
| $800  | 1.23e+11 | infeas | infeas | 5.36e+11 | 1.97e+13 | 1.23e+14 |
| $900  | 8.37e+10 | **1.09e+13** | infeas | 3.93e+11 | 1.30e+13 | 8.31e+13 |
| $1000 | 6.23e+10 | 5.23e+12 | infeas | 3.00e+11 | 9.39e+12 | 5.97e+13 |
| $1100 | 4.84e+10 | 3.14e+12 | **3.46e+13** | 2.39e+11 | 7.33e+12 | 4.48e+13 |
| $1200 | 3.92e+10 | 2.06e+12 | 1.95e+13 | 1.91e+11 | 6.03e+12 | 3.51e+13 |

**LCOE floors (the headline trend).**

| Target | VP floor | ORPC floor | VP–ORPC gap |
|-------:|--------:|----------:|------------:|
| 10 MW | $700 | <$500 (no floor in $500 grid) | ≥$200 |
| 50 MW | $900 | $700 | $200 |
| 100 MW | $1100 | $800 | $300 |

- Across the target jumps in the grid, VP's floor moves ~$200/MWh per jump.
- ORPC's floor moves ~$100/MWh per jump.

**Variance comparison (where both devices feasible).** VP has lower variance at every overlapping (cap, target) point. The ratio at $1200 is ~5× at 10 MW, ~3× at 50 MW, ~1.8× at 100 MW — the ratio shrinks monotonically as target grows.

**Spatial range (selection longitude, $1200 cap).**

| Target | VP lon range | ORPC lon range |
|-------:|:-------------|:---------------|
| 10 MW | -70.82 to -66.92 | -72.22 to -66.92 |
| 50 MW | -74.00 to -66.92 | -72.22 to -66.92 |
| 100 MW | -74.00 to -66.92 | -72.22 to -66.92 |

ORPC's range is the same at all three targets. VP's range is wider at 50 MW and 100 MW than at 10 MW; the upper longitude bound (-66.92) is the same across all six runs.

**Energy yield at $1200, 100 MW comparison:** VP 192 GWh/yr (CF ≈ 0.22), ORPC 74.5 GWh/yr (CF ≈ 0.085) — VP ~2.6× higher at the same nameplate.

**Feasibility regimes.** Below VP's floor, only ORPC is feasible. Above VP's floor, both feasible. VP's floor by target: $700 at 10 MW, $900 at 50 MW, $1100 at 100 MW — these are the boundary caps between the two regimes.

## Known risks to flag if hit

- $500 (and possibly $600) caps may come back infeasible for both devices even at 50 MW. Informative — defines floors — not a failure.
- VP at 953 TriFrames is ~9% of the ~10.6k NE+NY candidate pool. If low-cap runs are forced to pick most of the pool, the variance objective has fewer choices and the result may approach the all-candidates baseline. Worth inspecting in the output, not pre-correcting.
