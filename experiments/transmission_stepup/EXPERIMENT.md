# Transmission step-up — experiment design brief

**Date:** 2026-05-27 (design); 2026-05-28 (outcome analysis)
**Status:** sweep complete; outcome analysis complete; mechanism layer + SYNTHESIS pending
**Baseline it modifies:** the VP Gen5 "direct cable to shore" electrical configuration
(`optimization/vp/methodology/cost/capex/electrical/methodology.md` §Configuration —
*"No offshore transformers, collection points, or voltage step-up"*).

---

## Question

The baseline transmits each 93.6 kW TriFrame to shore at **480 V on its own radial
cable**. At 480 V the per-TriFrame current is high, so I²R loss forces the cable
selector onto large cross-sections at short distances — which prices out the far
sites. ~75% of the 11,874 eligible sites (new_england_new_york, gen5) are uneconomic,
and rejection is **distance-driven, not resource-driven** (Spearman(r_i, distance) =
+0.90).

**Does stepping the voltage up at each device expand the feasible / low-variance
set, and by how much?**

## Rung ladder (one lever per rung)

| Rung | Lever | Effect on model | Status |
|---|---|---|---|
| 0 | 480 V radial (baseline) | — | done |
| **1** | **per-device step-up + radial cable** | isolates voltage; preserves per-site linearity (only step 5 re-runs; covariance/candidates reused) | **this brief** |
| 2 | shared offshore collector + single export cable | isolates aggregation; breaks per-site separability (co-selected sites couple) | future |

This brief is **rung 1**: a step-up transformer at each TriFrame, cable unchanged.

## What is swept vs held

- **Swept:** step-up voltage ∈ {6.6} kV — bounded above by the existing ABB 10 kV
  (Um = 12 kV) cable catalogue, which deploys cleanly up to the 11 kV class but not
  33 kV; within that bound, the CDF preview shows the loss-driven CSA benefit
  saturates by ~6.6 kV, so higher voltages would only add transformer premium with
  no cable savings.
- **Held:** TriFrame architecture (3 turbines, P_TF = 93.6 kW), power factor 0.95,
  the ABB 10 kV three-core cable catalogue, the 10% loss ceiling, and all step-0–4
  pipeline outputs (harmonics, histograms, covariance, candidate screen).



## Cable infrastructure — reused unchanged

Same **ABB three-core 10 kV (Um = 12 kV) catalogue** as the baseline. In the model,
cable resistance and cost are functions of **cross-section, not voltage class**, so the
catalogue is reused as-is; the 10 kV insulation comfortably covers 6.6 kV operation. The
*only* thing voltage changes is current → loss → which CSA the selector picks.

## Transformer — type, value, and cost basis

The transformer sits **at each TriFrame, on the seabed** (deployment depth ≥ 10 m). A
device-level step-up there is, by definition, a **wet / subsea-marinized** unit — Collin
et al. (2017). We therefore use the **LV:MV Wet** coefficients.

**Cost model** — Collin et al. (2017), Eq. 2 (`papers/Collin 2017.pdf`, Table A3):

    C_transformer = c1 · S^c2 + c3        (S = transformer rating in MVA)

| Type | c1 | c2 | c3 | Fitted range (MVA) |
|---|---|---|---|---|
| LV:MV **Wet** | 45.48×10⁴ | 0.6329 | 51.115×10³ | [0.1125, 3] |

**Sizing:** S = P_TF / PF = 93.6 kW / 0.95 = **0.0985 MVA**.

    C_wet = 454,800 × 0.0985^0.6329 + 51,115 ≈ $156,000 per device

## How the cost enters the model

The transformer is **site-independent** (one per TriFrame regardless of location), so it
adds to **C_const**, not to per-site `c_site`.

It is handled **like the cable / electrical items**: added to `capex_const` as **raw**
CapEx (so the central `FCR` annualization and the insurance fraction both apply), but it
does **NOT** attract the contingency / environmental-compliance cascade. Concretely
`compute_c_const` gains `c_transformer = N × $156,000` inside the `capex_const` sum.

## Acknowledged design choices / assumptions

1. **Wet (subsea) transformer.** A per-TriFrame seabed step-up is a marinized unit; the
   ~$156k wet figure is the physically defensible cost. The dry value (~$22k, ~7×
   cheaper) assumes step-up above the waterline (a surface-piercing point), which is
   rung 2's territory.
2. **Cascade treatment = "like the cable."** FCR + insurance apply; contingency / EC do
   not (matches how cable/electrical items are treated in `compute_c_const`).
3. **MVA below the fitted floor.** S = 0.0985 MVA is ~12% below Collin's [0.1125, 3] MVA
   calibration range. The power law (c2 = 0.6329 < 1) is concave and well-behaved down to
   the c3 intercept, and clamping S to the 0.1125 floor changes cost only ~6%
   (wet: $156k → ~$165k). Treated as a benign extrapolation; clamp-to-floor is available
   as a strict-domain option.

## Success criteria

The question is answered once step 5 has been re-run at 6.6 kV and 480 V across all four
scales and, for each, we can report:

- **Min-feasible LCOE** (6.6 kV vs 480 V) — does step-up lower the cost floor?
- **σ² at matched LCOE** — does step-up firm the portfolio at equal price?
- **E at matched LCOE** — does step-up unlock more energy at equal price?
- **|feasible candidate set| at L** — how much does the lever expand the pool the
  optimizer picks from? Computed in-script via the same `c_site − L·E < 0` screen
  `05_optimize.py` uses, so the .nc files (per-site `c_site` and `energy_mwh`)
  are self-sufficient — no log-file parsing.

A site-composition diagnostic (overlap between selected portfolios at matched L) is
reported alongside to distinguish *"same sites, cheaper portfolio"* from *"different
portfolio with marginal restructuring."*

**Why not CV.** The original brief listed CV at matched LCOE as the firming metric. It
was dropped during analysis. Steps 1–4 are reused via symlinks, so `P_rated` and Σ are
bit-identical between the two voltages — raw σ² in W² is already apples-to-apples, and
CV's normalization solves a problem this experiment doesn't have. More importantly, at
small N the data shows σ² flat and E +7–9%; CV would summarize this as a "CV drop" —
arithmetically true but readable as firming, which it isn't (numerator is flat;
denominator moved). Reporting σ² and E separately keeps the two regimes (small-N "more
energy at the same risk" vs large-N "cheaper floor + lower risk") legible.

Decision rule: step-up "helps" if it lowers the min-feasible LCOE, or lowers σ² at
matched LCOE, or raises E at matched LCOE. The CDF preview is necessary motivation, not
sufficient evidence — it shows feasibility, not the portfolio-outcome payoff.

## Headline findings

At the worst-common L per MW (the most binding LCOE constraint where both voltages are
optimal):

| MW  | Min-feasible LCOE (480 V → 6.6 kV) | Δσ² at matched L | ΔE at matched L | Candidate pool Δ |
|-----|------------------------------------|------------------|-----------------|------------------|
| 1   | $700 → $700                        | −3.3%            | +7.2%           | +65.1%           |
| 5   | $700 → $700                        | −5.1%            | +6.8%           | +65.1%           |
| 25  | $900 → $800 (−$100)                | −11.3%           | +6.8%           | +69.1%           |
| 100 | $1300 → $1100 (−$200)              | −23.8%           | +3.2%           | +70.4%           |

**Two regimes:**

- **Small N (1, 5 MW):** σ² is essentially flat (within ±5%), E rises ~7%, LCOE floor
  unchanged. Step-up unlocks more energy at the same constraint without changing risk.
- **Large N (25, 100 MW):** σ² drops materially (−11% at 25 MW, −24% at 100 MW), the
  LCOE floor extends $100–$200/MWh lower, and the E gain saturates. Step-up both firms
  and cheapens the portfolio. 25 MW shows the regime transition beginning; 100 MW is
  fully in the new regime.

**Site composition.** Portfolios overlap 82–91% at the worst-common L. Step-up does not
just buy the 480 V portfolio at lower cost — it swaps 9–18% of sites at the margin,
slightly favoring farther sites (+0.03 to +0.13 km mean-distance shift). At 100 MW
that is ~150 sites out of 1069 swapped, which carries part of the σ² and E gains there.

**Lever vs use of lever.** The CDF preview's premise — that step-up expands the
feasible candidate set — is confirmed at +65–70% across all four scales (the *lever's*
effect, computed from the `c_site − L·E < 0` screen). The portfolio metrics show the
optimizer actually *uses* some of that expansion to restructure, and the more it
restructures (large N), the more variance also drops.

## Implementation status

**Code in place (at `optimization/vp/`):**

- `config/config.py` reads the `TIDAL_STEPUP_KV` env var, computes the transformer
  cost live from the Collin Wet coefficients, and routes results to a
  `transmission_stepup` path segment when step-up is active.
- `05_optimize.py` reads voltage from `STEPUP_KV` (defaulting to 480 V) and adds
  `N × C_TRANSFORMER_PER_TF` into `capex_const`.
- `run_transmission_stepup.sh` orchestrates gen5 × NE+NY × {1, 5, 25, 100} MW at
  6.6 kV, symlinking the baseline's steps 1–4 `.nc` outputs into each step-up cell
  so only step 5 re-runs.

When `TIDAL_STEPUP_KV` is unset, all of the above is a no-op — baseline runs are
bit-identical to the pre-change pipeline.

**Sweep — complete (2026-05-27).** All four scales OK. Per-MW elapsed: 1 MW 1105 s,
5 MW 528 s, 25 MW 524 s, 100 MW 415 s (large-N is faster because the LCOE constraint
binds harder). Outputs at
`results/vp/transmission_stepup/gen5/groups/new_england_new_york/{1,5,25,100}mw/`.

**Outcome analysis — complete (2026-05-28).**
`experiments/transmission_stepup/analyze.py` walks both result trees (480 V from
`turbine_modification/gen5`, 6.6 kV from `transmission_stepup/gen5`) and writes to
`results/vp/transmission_stepup/analysis/`:

- `portfolio_metrics.csv` — one row per (voltage, mw, lcoe_target) with status,
  achieved LCOE, σ², portfolio E, n_selected, n_feasible candidates
- `site_overlap.csv` — one row per (mw, L) where both voltages were optimal:
  n_common, n_swap, overlap %, mean shore distance per voltage
- `summary.csv` — one row per MW with min-feasible LCOE per voltage + matched-L
  deltas (variance, energy, pool, overlap) at the worst-common L
- `figures/outcome_panels.png` — 2 × 4 grid, rows = {σ², E}, cols = {1, 5, 25, 100}
  MW, two lines per panel (480 V solid, 6.6 kV dashed)

**Pending:**

1. **Mechanism layer** — answers *why* step-up helps, complementing the "did it help"
   outcome layer. Three pieces:
   (a) per-site Δc_site and ΔE_i vs distance — shows cable-CapEx savings and loss
   savings, the two physical mechanisms, in their natural units;
   (b) algebraic decomposition of the 100 MW −$200/MWh floor drop into
   ⟨Δc_site⟩ + ⟨ΔE_i⟩·L − N·C_transformer terms over the selected-portfolio averages,
   to check the headline number sums and quantify the transformer-cost tax;
   (c) loss-cap rejection histogram vs distance — should confirm the +65–70% pool
   expansion is the 10% loss ceiling being relieved at 6.6 kV (per the run, zero
   sites exceed the cap at 6.6 kV).
2. **SYNTHESIS.md** mirroring the diameter experiment's writeup, then commit the
   whole experiment (code + brief + analysis + synthesis together).

## References

1. Collin, A.J. et al. (2017). *Component-level cost models for offshore tidal-stream
   arrays.* Energies 10(12), 1973. Eq. 2, Table A3 (transformer cost coefficients).
2. ABB. *XLPE Submarine Cable Systems*, Rev 5, Table 41 (10 kV three-core).
