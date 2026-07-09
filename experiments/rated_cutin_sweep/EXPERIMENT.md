# Rated × Cut-in Design Sweep — VP Gen5

**Question:** Gen5's power curve fixes two speeds — rated `v_rated = 2.03 m/s` and
cut-in `v_cut_in = 0.61 m/s`. Did it pick them well for the US East-Coast tidal
resource? Or can a different `(v_rated, v_cut_in)` pair build a better portfolio?


---

## 1. The design family

The baseline is the **Verdant Gen5** power curve: `v_rated = 2.03 m/s`,
`v_cut_in = 0.61 m/s`, deployed as TriFrames of 3 turbines. We treat both speeds as
**independent design parameters** and sweep them around gen5. Raising `v_rated`
raises the rating, through the cube law. So each design is a different power curve,
with a different rated power per TriFrame.

**The power curve** 

```
        ⎧ 0              v < v_cut_in
P(v) =  ⎨ ½·ρ·A·Cp·v³    v_cut_in ≤ v ≤ v_rated
        ⎩ P_rated        v > v_rated   (no cut-out)
```

with `P_rated = ½·ρ·A·Cp·v_rated³`. A TriFrame is three turbines, so `P_TF(v) = 3·P(v)`.

| `v_rated` (m/s) | `v_cut_in` levels (m/s) | P_rated / turbine (kW) | P_rated / TriFrame (kW) |
|---|---|---:|---:|
| 1.50 | 0.40, 0.61, 0.80 | 12.6 | 37.7 |
| 1.75 | 0.40, 0.61, 0.80 | 19.9 | 59.8 |
| **2.03** (gen5) | 0.40, **0.61**, 0.80 | 31.1 | 93.4 |
| 2.30 | 0.40, 0.61, 0.80 | 45.3 | 135.9 |
| 2.60 | 0.40, 0.61, 0.80 | 65.4 | 196.3 |

Bold = current design. **5 rated × 3 cut-in = 15 power-curve designs.**

![15 VP power curves](../../results/vp/rated_cutin_sweep/power_curves.png)

*All 15 designs ride one cube-law envelope. `v_rated` sets where each caps — the five
plateaus. `v_cut_in` shifts only the near-zero liftoff (inset).*

**Held constant across the family:** rotor geometry (D = 5 m, A = 19.63 m²),
Cp = 0.37, ρ = 1025 kg/m³, the cube rating *law* (only the two speeds move), the per-device
cost formulas, the NE+NY scope, the 2013 hourly resource reconstruction, the
CF > 0.05 screen, and the cable / loss / OpEx / annualization model. 

Each TriFrame gets one step-up transformer, sized to its
apparent power `S = P_TF / 0.95` (MVA, PF = 0.95) and priced by Collin (2017):
`C_xfmr = 454,800 · S^0.6329 + 51,115` ($/TriFrame).

The Appendix explains how the gen5 anchor speeds are set.

## 2. Experimental design

We ran every combination below — **5 `v_rated` × 3 `v_cut_in` × 4 capacities = 60
solved optimization runs.**

- **Scope:** New England + New York (Maine, New Hampshire, Massachusetts, Rhode
  Island, Connecticut, New York).
- **Scales (installed-capacity target):** 1, 5, 25, 100 MW.
- **LCOE targets (cost ceiling):** \$600 → \$1,500 /MWh in \$100 steps (10 values).

**What is optimized.** For each design, the optimizer picks which sites to deploy. It
**minimizes the variance of aggregate power output**, subject to two constraints:
deploy exactly `N = ⌈P_target / P_TriFrame⌉` TriFrames, and keep portfolio LCOE at or
below the target. Gurobi solves it as a binary quadratic program. 

**Assumptions**: 

* no cut-out — power holds at rated for all speeds above `v_rated`.

* Deployment is always a whole number of TriFrames (`N = ⌈P_target / P_TriFrame⌉`, each site
in or out), so realized capacity runs slightly above target

A lower rating means less power per TriFrame. So low-rated designs need many more units
to hit the same MW target:

| `v_rated` | P_rated / TriFrame (kW) | 1 MW | 5 MW | 25 MW | 100 MW |
|---|---:|---:|---:|---:|---:|
| 1.50 | 37.7 | 27 | 133 | 664 | 2,654 |
| 1.75 | 59.8 | 17 | 84 | 418 | 1,671 |
| **2.03** | 93.4 | 11 | 54 | 268 | 1,071 |
| 2.30 | 135.9 | 8 | 37 | 185 | 737 |
| 2.60 | 196.3 | 6 | 26 | 128 | 510 |


## 3. Results

### Performance metric

We compare portfolios on the **coefficient of variation (CV) of aggregate power**. The
optimizer minimizes variance, so steadiness is the quantity each design is judged on:

```
σ  = sqrt(variance_w2)                          # std-dev of aggregate power   [W]
μ  = total_energy_mwh · 1e6 / 8760              # mean power                   [W]
CV = σ / μ                                      # steadiness (dimensionless)
```

Raw variance cannot rank these designs, because it scales with the output it
measures. CV = σ/μ normalizes that scale out, leaving a measure of steadiness that
is comparable at any output level.

**Lower CV means firmer, steadier output, at any installed capacity.** But steadiness
is half the story. Modifying the cut-in and rated speeds reshapes the power curve,
and the most direct effect is on the power each turbine produces — and therefore on
the energy each design delivers. CV, being a ratio, is blind to this difference: two
portfolios can share a CV while one delivers far more energy. So we report both
metrics.


![Energy vs LCOE, per capacity](../../results/vp/rated_cutin_sweep/energy_vs_lcoe.png)

*Figure 1 — Delivered energy versus LCOE. A line in green delivers more energy than gen5 at that cost.*

![CV vs LCOE, per capacity](../../results/vp/rated_cutin_sweep/cv_vs_lcoe.png)

*Figure 2 — Steadiness (CV, lower = steadier) versus LCOE.*

### Finding 1 — A lower rating always delivers more energy

In the energy plot, the low-rated designs (vr 1.50, 1.75) deliver more energy than
gen5 at every deployment scale, and the high-rated designs (2.30, 2.60) deliver
less. The ordering is strict: at every capacity and cost ceiling where two designs
are both feasible, the lower-rated design delivers more energy.

**Reason**: A lower rated speed caps the power curve at a lower current speed,
which raises the capacity factor. The same nameplate capacity therefore delivers
more energy. At 1 MW, vr 1.50 delivers up to ~5,750 MWh/yr against gen5's ~5,170.

Note, however, where each line begins. The low-rated designs are feasible only at
the upper end of the cost range; Finding 3 quantifies this entry cost.

### Finding 2 — A lower rating is steadier too, but only at small scale

At 1 and 5 MW, the low-rated designs fall below gen5's curve on the CV plot. At
1 MW, vr 1.50 reaches CV ≈ 0.050, while gen5 never falls below ≈ 0.066. At small
scale, therefore, a lower rating improves on gen5 in *both* metrics at once —
steadier and more energetic. By 100 MW, the low-rated designs are confined to the
most expensive targets or are infeasible altogether. The advantage in steadiness,
however, does not revert to gen5: vr 2.30 and 2.60 achieve a lower CV than gen5 at
every cost ceiling they share with it. 25 MW is the crossover scale — the high
ratings are steadiest at the cheaper ceilings (\$800–1,100), and gen5's rating is
steadiest from \$1,200 up.

### Finding 3 — The advantage is bought at high cost, and the bill rises with scale

A lower rating requires 2–5× the TriFrames (§2), and each TriFrame adds its own
transformer and cable, so unit count drives cost. The table reports each design's
**entry price** — the cheapest LCOE target at which it can be built at all. The
entry price rises in two directions. Reading left, toward lower ratings: at 1 MW it
doubles, from \$700 (gen5) to \$1,400 (vr 1.50). Reading down, toward larger
fleets: gen5's own entry rises from \$700 at 1 MW to \$1,100 at 100 MW.

| capacity | vr 1.50 | vr 1.75 | **gen5 (2.03)** | vr 2.30 | vr 2.60 |
|---|---:|---:|---:|---:|---:|
| 1 MW   | \$1,400 | \$1,000 | **\$700**   | \$600 | \$600 |
| 5 MW   | \$1,400 | \$1,000 | **\$700**   | \$600 | \$600 |
| 25 MW  | \$1,500 | \$1,100 | **\$800**   | \$700 | \$600 |
| 100 MW | **—**   | \$1,400 | **\$1,100** | \$900 | \$800 |

Cheapest feasible LCOE target per design (`v_cut_in` = 0.61). "—" means infeasible
anywhere in the \$600–1,500 sweep. At 100 MW, the vr 1.50 portfolio needs 2,654
TriFrames. It cannot clear \$1,500/MWh at all.

### Finding 4 — Cut-in barely matters

In both plots, the three `v_cut_in` lines for each rating collapse into a single
narrow band. The cut-in speed only switches the lowest, least energetic velocity
bins on or off, so it has little effect on either energy or CV. The rated speed is
the design parameter that matters. (The Appendix explains why.)

### Summary

No single design wins this sweep. Steadiness and energy favor different turbine
specifications, at different scales and different prices, so the recommendation
depends on the objective. Both tables below read the same way: for a given
capacity, the recommended design is optimal while the cost ceiling lies inside the
quoted band; below that band, the design in the last column is preferred.

**Objective 1 — steadiest output.** The recommended design minimizes CV over all
15 `(v_rated, v_cut_in)` cells at the given capacity and cost ceiling.

| target | build (vr / vci, m/s) | P_rated / TriFrame | steadiest when the ceiling is | on a tighter budget |
|---|---|---:|---|---|
| 1 MW | **1.75 / 0.40** | 59.8 kW | \$1,000–1,400 (1.50/0.40 takes over at \$1,500) | 2.03/0.40 at \$800–900; 2.30/0.40 below |
| 5 MW | **1.75 / 0.40** | 59.8 kW | \$1,100–1,400 (1.50/0.40 at \$1,500) | 2.03/0.40 at \$800–1,000; 2.30/0.40 below |
| 25 MW | **2.03 / 0.40** | 93.4 kW | \$1,200–1,500 | 2.30/0.40 at \$1,000–1,100; 2.60/0.40 below |
| 100 MW | **2.60 / 0.40** | 196.3 kW | every cost where it can be built | — already the cheapest entry |

One specification is universal: every recommended design carries the 0.40 cut-in,
though its margin over 0.61 is small (Finding 4).

**Objective 2 — most energy delivered.** The recommended design carries the lowest
rated speed that is feasible at the given ceiling. Each design also delivers its
maximum energy at its own entry price, where the cost constraint leaves the
optimizer no slack to trade energy for lower variance.

| target | build (vr / vci, m/s) | P_rated / TriFrame | most energetic when the ceiling is | on a tighter budget |
|---|---|---:|---|---|
| 1 MW | **1.50 / 0.40** | 37.7 kW | \$1,400–1,500 (peak 5,751 MWh/yr) | 1.75/0.80 at \$1,000–1,300; 2.03/0.61 at \$700–900 |
| 5 MW | **1.50 / 0.80** | 37.7 kW | \$1,400–1,500 (peak 25,339 MWh/yr) | 1.75/0.61 at \$1,000–1,300; 2.03/0.80 at \$700–900 |
| 25 MW | **1.50 / 0.61** | 37.7 kW | \$1,500 only (117 GWh/yr; 1.75/0.80 holds \$1,100–1,400) | 2.03/0.80 at \$800–1,000; 2.30/2.60 below |
| 100 MW | **1.75 / 0.80** | 59.8 kW | \$1,400–1,500 (peak 329 GWh/yr; 1.50 unbuildable) | 2.03/0.80 at \$1,100–1,300; 2.30/0.80 at \$900–1,000; 2.60/0.80 at \$800 |

The cut-ins in this table should be read loosely: at 1–5 MW the winning cut-in
varies across all three levels, within Finding 4's margins. Only at 25 and 100 MW
does the 0.80 cut-in win consistently — not by capturing more energy per site, but
by restricting the candidate pool to stronger sites.

The two objectives nearly agree at 1–25 MW: the steadiest design sits at or near
the lowest buildable rating, which also delivers the most energy. At 100 MW they
diverge: the steadiest feasible design (2.60) is the least energetic, and the most
energetic (1.75) is the most variable. At that scale, the objective must be chosen
before the turbine.

Where does this leave gen5? Its specification is optimal in the middle of the
tested range — at 25 MW under Objective 1, and at intermediate budgets under
Objective 2 — and it is never far from optimal elsewhere. Verdant's speeds, in
short, suit a mid-scale build; a small pilot favors a lower rating, and a 100 MW
build-out a higher one. One caveat applies to both tables: per-device cost is held
fixed across ratings (§1). If device cost rose with rated power, as it would in
practice, every recommendation would shift toward the lower ratings.



---

## Appendix — methodology & derivations

### Reading the two plots: gen5's win / lose region



Gen5 is the baseline, and its own curve serves as the reference. It divides each
panel into a better half and a worse half:

- **Energy plot** (higher = more): a competitor **above** gen5's curve delivers more —
  gen5 loses; **below** it, gen5 wins.
- **CV plot** (lower = steadier): a competitor **below** gen5's curve is steadier than
  gen5 at that cost — gen5 loses; **above** it, gen5 wins.

We tint the half where a design beats gen5 green, and the half where gen5 wins
pink; green always means "better than gen5." A design in green on *both* plots
dominates gen5 at that cost. A design in pink on both is dominated by it. A design
in green on one plot and pink on the other trades one objective against the other.





### What the two speeds do, and the candidate pool

The CF > 0.05 screen divides mean power by the rating. So the two speeds act on
opposite parts of the same ratio:

```
CF = mean_power / P_rated,     P_rated = ½ρACp·v_rated³
```

- **`v_rated` — the dominant driver (denominator).** Lowering `v_rated` lifts CF for
  nearly every marginal site. The pool grows steeply. Raising it shrinks the pool.
- **`v_cut_in` — a weak driver (numerator).** It only switches the low-speed bins
  `[v_cut_in, …]` on or off, where `½ρACp·v³` is tiny. That barely changes mean power.
  So it shifts CF only at low `v_rated`. There, the small rating in the denominator
  turns a tiny change in power into a visible move in the ratio.

The screen bears this out. Each design is the candidate-pool size — the number of sites
clearing CF > 0.05 — for that `(v_rated, v_cut_in)` pair:

| `v_rated` ↓ / `v_cut_in` → | 0.40 | 0.61 | 0.80 |
|---|---:|---:|---:|
| 1.50 | 28,686 | 24,392 | 18,198 |
| 1.75 | 19,372 | 17,462 | 13,859 |
| 2.03 | 12,589 | 11,895 | 10,425 |
| 2.30 | 8,980 | 8,707 | 7,890 |
| 2.60 | 6,234 | 6,103 | 5,741 |

Raising `v_rated` (down a column) shrinks the pool ~3–5× in every column. Raising
`v_cut_in` (across a row) shrinks it only ≈1.1–1.6×, and even that mostly at low
`v_rated`. This is the split predicted above. `v_rated` acts through the denominator
and dominates. `v_cut_in` acts through the numerator and barely moves the pool.

**Pool size is not the output.** A larger pool does not make a portfolio steadier or
more feasible. It only gives the optimizer more sites to choose from.

**Operating-regime breakdown — idle, ramping, plateau.**  A lower rating admits a larger
but slower pool — its CF > 0.05 screen passes more marginal sites, and mean site
speed falls from 1.0 m/s at vr 2.60 to 0.7 at vr 1.50. The slower pool offsets the
lower cap, so the regime shares differ less across designs than the power curves
alone would suggest.

| design (`v_rated` / `v_cut_in`) | mean speed (m/s) | idle (< cut-in) | ramping (cubic) | plateau (≥ rated) |
|---|---:|---:|---:|---:|
| 1.50 / 0.40 | 0.68 | 26.0% | 70.3% | 3.8% |
| 1.50 / 0.61 | 0.71 | 42.6% | 52.9% | 4.4% |
| 1.50 / 0.80 | 0.77 | 55.9% | 38.2% | 5.9% |
| 1.75 / 0.40 | 0.76 | 21.4% | 76.2% | 2.4% |
| 1.75 / 0.61 | 0.78 | 36.6% | 60.7% | 2.7% |
| 1.75 / 0.80 | 0.84 | 49.8% | 46.7% | 3.4% |
| 2.03 / 0.40 | 0.86 | 17.2% | 81.4% | 1.3% |
| **2.03 / 0.61** | **0.87** | **30.9%** | **67.7%** | **1.4%** |
| 2.03 / 0.80 | 0.90 | 44.3% | 54.1% | 1.6% |
| 2.30 / 0.40 | 0.93 | 14.9% | 84.4% | 0.8% |
| 2.30 / 0.61 | 0.94 | 27.3% | 71.9% | 0.8% |
| 2.30 / 0.80 | 0.96 | 39.9% | 59.2% | 0.9% |
| 2.60 / 0.40 | 1.01 | 12.6% | 87.0% | 0.4% |
| 2.60 / 0.61 | 1.01 | 24.1% | 75.5% | 0.4% |
| 2.60 / 0.80 | 1.02 | 36.0% | 63.6% | 0.4% |



**Plateau time still falls with the rating.** A vr 1.50 design operates at rated output 4–6% of the year, gen5 ~1.4%,
and a vr 2.60 design 0.4%. Every design reaches its plateau rarely — peak tidal
currents are brief — but a lower rating reaches its cap several times more often,
and this is the source of its firmness. **Idle time is governed by the cut-in, not
the rating.** Raising the cut-in from 0.40 to 0.80 more than doubles idle time,
from 17% to 44% at gen5's rating. This appears to contradict Finding 4, but does
not: the affected velocity bins carry almost no energy (`½ρACp·v³` is small at
those speeds), so the cut-in shifts operating *hours* without materially shifting
energy or CV.

### How the rated and cut-in speeds are set

We sweep both speeds independently. The **gen5 anchor values** come from:

- **Cut-in:** `v_cut_in = 0.30 × v_rated` (Lewis standardization).
- **Rated:** the 99.5th percentile of per-site *maximum* tidal current speed (U_max),
  from the 2013 t_predic harmonic reconstruction at hourly resolution. p99.5 is the
  *unique* percentile (among p50…p99.9) that reproduces Verdant's published 35 kW
  rating. Via the cube law, that gives `v_rated ≈ 2.11 m/s` — within 4%.



### References

1. Lewis et al. (2021) — *A standardised tidal-stream power curve, optimised for the
   global resource.*
   [PDF](https://tethys-engineering.pnnl.gov/sites/default/files/publications/Lewis-et-al-2021.pdf)
2. Collin (2017) — step-up transformer apparent-power cost scaling
   (`C_xfmr = 454,800 · S^0.6329 + 51,115`).
