# Cost Structure for the Optimization

How CapEx and OpEx components feed into the LCOE constraint of the BQP. Costs split into two buckets based on whether they depend on which sites are chosen.

Implementation: `compute_c_const(N)` and `compute_c_site(...)` in `optimization/orpc/05_optimize.py`. See `capex/capex_cost_components.md` and `opex/opex_cost_components.md` for how each component is computed at the methodology level.

> **Status (2026-07-12):** this doc reflects the electrical rework (480 V generation → 6.6 kV AC step-up; onshore inverter removed; step-up transformer added to C_const). The code (`config/config.py`, `05_optimize.py`) has been **reconciled to match** this spec. Results still need **re-running** — the local `candidates.nc`/`covariance.nc` were deleted, so regenerate via `01`/`03` (or run on the remote). The 480 V comparison arm runs with `TIDAL_STEPUP_KV=0`.

---

## OpEx structure and the insurance term

ORPC's per-device OpEx splits into two parts (see `opex/opex_cost_components.md`):

- a **flat non-insurance bundle** — $140,422/yr/device (ORPC's published $160,422 with its $20,000 insurance line removed), which does not vary with site selection or scale with CapEx, and
- **insurance = 1% × CapEx**, harmonized with the VP pipeline (`INSURE_FRAC = 0.01`), which scales with CapEx.

Two consequences:

1. **The non-insurance bundle is entirely in C_const(N).** It depends only on how many devices are built, not which sites.
2. **Insurance follows CapEx into both buckets.** On the constant device CapEx it adds to C_const(N); on the shore-distance-driven cable CapEx it adds to c_site_i. Insurance is therefore partly site-varying, exactly as in the VP model.

c_site_i is a CapEx-driven, shore-distance-driven term — cable purchase + cable laying + a small contingency/EC cascade on the laying portion — now also carrying its 1% insurance share. There is still no cross-site coupling: site i's cost does not depend on whether site j is also selected.

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
| Step-up transformer | $354{,}000 \cdot N$ | Per-device 480 V→6.6 kV seabed unit (Collin Eq. 2, S = 0.526 MVA); site-independent |
| Subsystem integration | $0.10 \cdot C_{\text{device,total}}$ | Cascade from device |
| Contingency (constant part) | $0.10 \cdot (C_{\text{device}} + C_{\text{subsys}} + C_{\text{install,const}})$ | Cascade from N-only terms |
| Environmental compliance | $0.05 \cdot (C_{\text{device}} + C_{\text{subsys}} + C_{\text{contin,const}})$ | Cascade from N-only terms |

The cable-laying portion of installation is *not* in C_const — laying time is proportional to total selected shore distance, which is portfolio-dependent, so it sits in c_site_i below.

**OpEx components:**

| Component | Value |
|-----------|-------|
| Non-insurance bundle | $140{,}422 \cdot N$ ($/yr, flat) |
| Insurance (constant part) | $\text{INSURE\_FRAC} \cdot \text{CapEx}_{\text{const}}(N)$, with INSURE_FRAC = 0.01 |

**Annualization:**

$$C_{\text{const}}(N) \;=\; \text{FCR} \cdot \text{CapEx}_{\text{const}}(N) \;+\; 140{,}422\,N \;+\; \text{INSURE\_FRAC} \cdot \text{CapEx}_{\text{const}}(N)$$

with FCR = 0.113 and INSURE_FRAC = 0.01.

---

## Portfolio-Dependent — c_site_i

Costs that change with which sites are selected. Each site's c_site_i is independent of the other sites — there is no cross-site coupling in the cost model. Computed by `compute_c_site(cable_cost_total_i, laying_cost_i)`.

**CapEx components, all shore-distance-driven:**

| Component | Formula | Source |
|-----------|---------|--------|
| Cable purchase | (cable cost $/m, from CSA selection at d_i) × d_i × 1000 | Nakhai (2023) Eq. 3, 3-core AC (70 mm² floor at 6.6 kV) |
| Cable laying | $175{,}130 \cdot d_i$ ($/site, $d_i$ in km) | Mattia Eq. 74 (per-meter direct, all-in) |
| Contingency (laying portion) | $0.10 \cdot C_{\text{laying},i}$ | Hassan (2024) Eq. 8 |
| Environmental compliance (laying portion) | $0.05 \cdot C_{\text{contin},i}$ | Hassan (2024) Eq. 9 |

Only the laying cost enters the contingency cascade; the cable purchase does not. (See note at end.)

**Cascade:**

```
laying_i (linear in d_i)
  ↓
contin_pd_i = 0.10 × laying_i
  ↓
ec_pd_i = 0.05 × contin_pd_i
  ↓
capex_pd_i = cable_i + laying_i + contin_pd_i + ec_pd_i
  ↓
c_site_i = (FCR + INSURE_FRAC) × capex_pd_i    (INSURE_FRAC = 0.01)
```

The `INSURE_FRAC × capex_pd_i` term is the site-varying insurance share — the same 1% × CapEx rule as the VP pipeline, applied to the portfolio-dependent (cable) CapEx.

Each c_site_i is precomputed once before the BQP solve. The `compute_c_site` function takes the per-site cable cost and laying cost and produces the annualized $/yr scalar.

**Note on cascade scope.** Contingency in the methodology is `0.10 × (device + subsystem + installation)`, where "installation" includes laying. We split that 10% across C_const (covering device + subsystem + the constant portions of install) and c_site_i (covering the laying portion only). The cable purchase sits *inside* capex_pd_i but *outside* the contingency cascade, matching the structure inherited from the base pipeline's cost model. Treating the cable as an already-priced commodity (not subject to additional contingency markup) is the implementation choice; an alternative could fold it into the cascade, but that would require revising `compute_c_site` and re-deriving the per-site cost decomposition.

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

> ⚠️ **Stale — reflects the retired DC / onshore-inverter model.** These figures predate the
> 2026-07-12 electrical rework (480 V generation → 6.6 kV AC step-up; onshore inverter removed;
> $354k × N step-up transformer added to C_const) and the insurance harmonization (c_site_i now
> carries a 1% insurance share, so uses FCR + INSURE_FRAC rather than FCR alone; OpEx bundle is
> $140,422, not $160,422). The DC-monopolar CSA figures (150/1000 mm²) no longer apply — at
> 6.6 kV the cable is the 70 mm² floor everywhere within 5 km. Re-verify after the code is
> updated to match this spec.

Verified 2026-05-03 against the post-2026-05-02 cable-laying fix (retired DC model):

- C_const(100) ≈ $43.5M/yr (device manufacturing learning-curve avg ≈ $1.85M/device vs $3.18M unit-1)
- c_site_i at d = 0.3 km shore: ≈ $22k/yr (cable purchase modest at 150 mm² CSA; laying $52.5k dominates)
- c_site_i at d = 5.0 km shore: ≈ $514k/yr (1000 mm² CSA cable + $876k laying cascade)

These produce achievable LCOEs of $700–$1500/MWh in the configured sweep.

---

## References

- Hassan, M. et al. (2025). Technoeconomic optimization of coaxial hydrokinetic turbines. *Renewable Energy* 239, 122041. Eqs. 3, 8, 9.
- Marnagh, C. & McEntee, J. (2018). DOE MHKDR Submission 269.
- Mattia, P. (2025). *Techno-Economic Modelling and Comparative Analysis of HATEC*. Master's thesis, Politecnico di Torino.
- Nakhai, A. Y. (2023). *Electrical Infrastructure Cost Model for Marine Energy Systems*. NREL/TP-5700-87184.
- See `capex/capex_cost_components.md` and `opex/opex_cost_components.md` for component-level sourcing.
