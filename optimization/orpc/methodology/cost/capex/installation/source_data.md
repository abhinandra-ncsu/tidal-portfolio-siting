# ORPC TidGen 2.0 — Installation Source Data

## Vessel Charter Rate Cost Functions

From **Mattia (2025) Table 2.1-12** (DTOceanPlus project, Mattia ref [46]). All rates EUR/day.

### Tug

| Domain (bollard pull, tonnes) | Function (EUR/day) |
|---|---|
| 13 ≤ x < 25 | 151.34x − 467.47 |
| 25 ≤ x < 70 | 2.18x + 3261.61 |
| 70 ≤ x ≤ 80 | 508.57x − 32186 |

### Multicat

| Domain (LOA, m) | Function (EUR/day) |
|---|---|
| 21 ≤ x < 28 | 63.23x + 1812.4 |
| 28 ≤ x < 35 | 916.74x − 22086 |
| 35 ≤ x ≤ 42 | 10000 (flat) |

### Cable Laying Vessel (CLV)

| Domain (cable storage, tonnes) | Function (EUR/day) |
|---|---|
| 565 ≤ x ≤ 10000 | 2.46e-4 x² + 7.25x + 53090 |

## Mooring Installation Time

From **Mattia (2025) Section 2.1.18** (p. 33), citing reference [58]:

| Step | Duration |
|---|---|
| Anchor pre-lay | 12 h per anchor |
| Mooring line installation | 22 h per line |
| Mooring connection | 10 h per line |

For ORPC TidGen 2.0's 4-line BTMS (see `../../turbine_design_specification.md`):

    per-device mooring time = 4 × (12 + 22 + 10) = 176 h = 7.33 days  (24-h working)

## Cable Installation Costs

From **Mattia (2025) Eqs. 72–74** (p. 33):

```
Cost_cable_laid         = 100 €/m     (Eq. 72) — surface laying on seabed
Cost_cable_drilled_duct = 282 €/m     (Eq. 73) — burial in drilled duct
COST_cable_inst = 100 × (2/3) × L + 282 × (1/3) × L    (Eq. 74)
```

Per-meter values bundle vessel charter, drilling rig, mobilization, crew, and consumables
(Mattia ref [61]).

## Mooring Materials

From **CBS-A30** (Cost Breakdown Structure_043018, single-device column, cell I244):

| CBS # | Item | Cost ($) |
|---|---|---:|
| 1.2.8 | Substructure & Foundation (single device) | 40,000 |

For ORPC TidGen 2.0 with BTMS, this represents the per-device cost of mooring chains and gravity anchors. ORPC's CBS does not provide a finer breakdown of 1.2.8.

## Currency Conversion

EUR → USD at **1.09** (Mattia 2025 vintage).

## References

- Mattia, P. (2025). *Techno-Economic Modelling and Comparative Analysis of HATEC*. Master's thesis, Politecnico di Torino. Section 2.1.18, Table 2.1-12, Eqs. 72–74.
- Marnagh, C. & McEntee, J. (2018). *D7.2.7 LCOE Cost and Performance Template*. DOE MHKDR Submission 269. CBS-A30 cell I244.
- DTOceanPlus project. Vessel charter rate cost functions. Mattia (2025) reference [46].
