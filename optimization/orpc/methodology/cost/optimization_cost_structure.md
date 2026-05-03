# Cost Structure for the Optimization

How CapEx and OpEx components feed into the LCOE constraint of the BQP. Costs split into two buckets based on whether they depend on which sites are chosen.

Implementation: `compute_c_const(N)` and `compute_c_site(...)` in `optimization/orpc/05_optimize.py`. See `capex/capex_cost_components.md` and `opex/opex_cost_components.md` for how each component is computed at the methodology level.

---

## Why ORPC's cost structure is simple

ORPC's per-device OpEx is a single bundled value ($160,422/yr/device, source: LCOE Summary May-23 revised, sheet F7) that does not vary with site selection or scale with CapEx. Two consequences flow from that:

1. **All OpEx is in C_const(N).** No portion of OpEx depends on which sites are chosen — only on how many.
2. **No insurance term in c_site_i.** `INSURE_FRAC = 0` because insurance is already inside ORPC's bundled OpEx number. There is no separate annual insurance line that would otherwise scale with per-site CapEx and feed back into site selection.

c_site_i ends up as a pure CapEx-driven, shore-distance-driven term: cable purchase + onshore inverter + cable laying + a small contingency/EC cascade on the laying portion. There is no coupling from OpEx into c_site_i, and no cross-site coupling — site i's cost does not depend on whether site j is also selected.

This separability is what keeps the LCOE constraint linear in x.

---

## Project-Level Constant — C_const(N)

Costs that depend on N alone, not on which sites are picked. Computed by `compute_c_const(N)` in `05_optimize.py`.

**CapEx components:**

| Component | Formula | Why N-only |
|-----------|---------|------------|
| Device manufacturing | $\sum_{i=1}^{N} C_{\text{device,1}} \cdot i^{b}$, with learning exponent $b = \log_2(1 - 0.10) \approx -0.152$ | Manufacturing cost is per-unit |
| Tow installation (tug) | $(2 \cdot T_{\text{transit}} + d_{\text{tug}} \cdot N) \cdot R_{\text{tug}}$ | Per-device tow time |
| Mooring installation (multicat) | $(2 \cdot T_{\text{transit}} + d_{\text{moor}} \cdot N) \cdot R_{\text{multicat}}$ | Per-device mooring time |
| Mooring materials | $40{,}000 \cdot N$ | Per-device chains + anchors |
| Subsystem integration | $0.10 \cdot C_{\text{device,total}}$ | Cascade from device |
| Contingency (constant part) | $0.10 \cdot (C_{\text{device}} + C_{\text{subsys}} + C_{\text{install,const}})$ | Cascade from N-only terms |
| Environmental compliance | $0.05 \cdot (C_{\text{device}} + C_{\text{subsys}} + C_{\text{contin,const}})$ | Cascade from N-only terms |

The cable-laying portion of installation is *not* in C_const — laying time is proportional to total selected shore distance, which is portfolio-dependent, so it sits in c_site_i below.

**OpEx component:**

| Component | Value |
|-----------|-------|
| Bundled OpEx | $160{,}422 \cdot N$ ($/yr, flat) |

**Annualization:**

$$C_{\text{const}}(N) \;=\; \text{FCR} \cdot \text{CapEx}_{\text{const}}(N) \;+\; \text{OpEx}(N)$$

with FCR = 0.113 and INSURE_FRAC = 0.

---

## Portfolio-Dependent — c_site_i

Costs that change with which sites are selected. Each site's c_site_i is independent of the other sites — there is no cross-site coupling in the cost model. Computed by `compute_c_site(cable_cost_total_i, laying_cost_i)`.

**CapEx components, all shore-distance-driven except the inverter:**

| Component | Formula | Source |
|-----------|---------|--------|
| Cable purchase | (cable cost $/m, from CSA selection at d_i) × d_i × 1000 | Nakhai (2023) Eq. 3, DC monopolar |
| Onshore inverter | $102{,}500 (flat per selected site) | CBS-A30 1.2.3.4.5 |
| Cable laying | $175{,}130 \cdot d_i$ ($/site, $d_i$ in km) | Mattia Eq. 74 (per-meter direct, all-in) |
| Contingency (laying portion) | $0.10 \cdot C_{\text{laying},i}$ | Hassan (2024) Eq. 8 |
| Environmental compliance (laying portion) | $0.05 \cdot C_{\text{contin},i}$ | Hassan (2024) Eq. 9 |

The inverter is a flat per-site cost that does not enter the contingency cascade in our implementation — only the laying cost cascades. (See note at end.)

**Cascade:**

```
laying_i (linear in d_i)
  ↓
contin_pd_i = 0.10 × laying_i
  ↓
ec_pd_i = 0.05 × contin_pd_i
  ↓
capex_pd_i = cable_i + 102,500 + laying_i + contin_pd_i + ec_pd_i
  ↓
c_site_i = FCR × capex_pd_i        (since INSURE_FRAC = 0)
```

Each c_site_i is precomputed once before the BQP solve. The `compute_c_site` function takes the per-site cable cost and laying cost and produces the annualized $/yr scalar.

**Note on cascade scope.** Contingency in the methodology is `0.10 × (device + subsystem + installation)`, where "installation" includes laying. We split that 10% across C_const (covering device + subsystem + the constant portions of install) and c_site_i (covering the laying portion only). The cable purchase and the onshore inverter sit *inside* capex_pd_i but *outside* the contingency cascade, matching the structure inherited from the base pipeline's cost model. Treating the cable+inverter as already-priced commodities (not subject to additional contingency markup) is the implementation choice; an alternative could fold them into the cascade, but that would require revising `compute_c_site` and re-deriving the per-site cost decomposition.

---

## How This Enters the BQP

LCOE constraint:

$$C_{\text{const}}(N) \;+\; \sum_i x_i \cdot ( c_{\text{site},i} - L \cdot E_i ) \;\leq\; 0$$

- C_const(N): scalar, computed once per N
- c_site_i: per-site scalar, computed once before the solve
- E_i: annual energy at site i (`energy/methodology.md`)
- L: LCOE target ($/MWh), swept over `LCOE_TARGETS`

The constraint is linear in x. The only quadratic term in the BQP is the variance objective.

---

## Numerical sanity check (N = 100)

Verified during pipeline development:

- C_const(100) ≈ $43.5M/yr (device manufacturing learning-curve avg ≈ $1.85M/device vs $3.18M unit-1)
- c_site_i at d = 0.3 km shore: ≈ $15k/yr (cable purchase modest at smallest CSA)
- c_site_i at d = 5.0 km shore: ≈ $407k/yr (cable purchase scales with distance × CSA step-up)

These produce achievable LCOEs of $700–$1500/MWh in the configured sweep.

---

## References

- Hassan, M. et al. (2025). Technoeconomic optimization of coaxial hydrokinetic turbines. *Renewable Energy* 239, 122041. Eqs. 3, 8, 9.
- Marnagh, C. & McEntee, J. (2018). DOE MHKDR Submission 269.
- Mattia, P. (2025). *Techno-Economic Modelling and Comparative Analysis of HATEC*. Master's thesis, Politecnico di Torino.
- Nakhai, A. Y. (2023). *Electrical Infrastructure Cost Model for Marine Energy Systems*. NREL/TP-5700-87184.
- See `capex/capex_cost_components.md` and `opex/opex_cost_components.md` for component-level sourcing.
