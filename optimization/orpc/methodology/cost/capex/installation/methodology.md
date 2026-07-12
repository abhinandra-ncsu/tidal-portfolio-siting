# ORPC TidGen 2.0 — Installation Methodology

## Three-Phase Installation Structure

Device parameters used in this component (see `../../turbine_design_specification.md` for
primary citations): floating device on Buoyant Tension Mooring System (BTMS), 4 mooring lines
per device, 140-tonne dry mass, gravity anchors. Installation has three independent phases
requiring three vessels:

| Phase | Vessel | What's installed |
|---|---|---|
| Tow | Tug | Floating device, towed from onshore assembly to site |
| Moor | Multicat | 4 gravity anchors + 4 mooring chains + connections |
| Cable | CLV | Subsea power cable from device to shore |

The vessel choices below follow Mattia (2025) Section 2.1.18 recommendations for floating
tidal turbines.

## Phase 1: Towing

**Vessel:** Tug — Mattia recommends tug for floating-platform towing (Section 2.1.18).
**Bollard pull:** 50 tonnes assumed — sufficient for hydrodynamic drag on a 140-tonne buoyant
platform at typical towing speeds (7.4–9.3 km/h per Mattia).
**Day rate:** From Mattia Table 2.1-12 tier 2 (25 ≤ x < 70):

    2.18 × 50 + 3261.61 = 3,371 EUR/day  =  $3,641/day  at 1.08 EUR/USD

**Time:** 1 day per device on-site (towing + positioning), plus 2 days transit each way.

    tug_days   = 2 + 1.0 × N + 2
    C_inst_tow = tug_days × $3,641/day

## Phase 2: Mooring Installation

**Vessel:** Multicat per Mattia Section 2.1.18 ("the mooring line installation phase involves the
use of a multicat vessel").
**LOA:** 26 m, matching Mattia's MV C-Odyssey case-study reference vessel.
**Day rate:** From Mattia Table 2.1-12 tier 1 (21 ≤ x < 28):

    63.23 × 26 + 1812.4 = 3,456 EUR/day  =  $3,732/day

**Time per device:** 4 lines × (12 h anchor + 22 h line + 10 h connection) = 176 h = 7.33 days,
plus 2 days transit each way.

    multicat_days = 2 + 7.33 × N + 2
    C_inst_moor   = multicat_days × $3,732/day

## Phase 3: Cable Installation

**Approach:** Mattia (2025) §2.1.18 explicitly switches frameworks for cables — abandoning
day-rate × time and adopting per-meter installation metrics from reference [61] for "better
simplicity." We follow Mattia's framework directly.

**Cost metrics (Mattia Eqs. 72–74):**
- Surface laying: 100 €/m
- Drilled duct (buried): 282 €/m
- Split: 2/3 surface, 1/3 buried

**What the €/m bundles:** vessel charter (CLV), drilling rig for the buried portion,
mobilization, crew, and consumables. Mattia treats the metric as all-in; we do the same. We do
not separately model CLV day-rate, transit time, or mobilization for cable installation —
these are inside the €/m.

**Formula:**

    L_total      = sum of shore distances over selected sites (km)
    c_blend      = (2/3) × 100 + (1/3) × 282 = 160.67 €/m   [Mattia Eq. 74]
    C_inst_cable = c_blend × L_total × 1000 × 1.08 USD/EUR
                 ≈ $173,500 × L_total

## Mooring Materials

Mooring chains and gravity anchors are a material cost separate from vessel time. We use ORPC's
published value:

    C_mooring_mat = $40,000 × N      (CBS-A30 1.2.8, single-device value)

## Total Installation Cost

    C_inst = C_inst_tow + C_inst_moor + C_inst_cable + C_mooring_mat

## References

- Mattia, P. (2025). *Techno-Economic Modelling and Comparative Analysis of HATEC*. Master's thesis, Politecnico di Torino. Section 2.1.18, Table 2.1-12, Eqs. 72–74.
- Marnagh, C. & McEntee, J. (2018). *D7.2.7 LCOE Cost and Performance Template*. DOE MHKDR Submission 269. CBS-A30 cell I244 (1.2.8 Substructure & Foundation).
- Device parameter primary citations: see `../../turbine_design_specification.md`.
