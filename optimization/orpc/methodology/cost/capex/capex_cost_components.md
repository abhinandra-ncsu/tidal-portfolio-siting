# CapEx Cost Components — ORPC TidGen 2.0

Turbine-specific inputs come from ORPC's Cost Breakdown Structure in DOE MHKDR submission 269.

## 1. Device Cost (C_device)

Manufacturing cost of the TidGen 2.0 Marine Energy Converter: structural
assembly, power conversion chain (drivetrain, on-device electrical),
coatings, and transportation. Per-device value taken directly from ORPC's
published CBS at the device level (1.1).

Source: see `device/source_data.md`.

    C_device_ORPC(unit i) = $3,182,500 × i^(-0.152)
    C_device_total        = Σ C_device_ORPC(i)  for i = 1..N

**Learning rate: 10%** (ORPC LCOE Whitepaper, REF Cost models cell C10;
documented in workbook as "conservative based on historical wind turbine
industry"). Wright's-Law exponent b = log10(1 − 0.10) / log10(2) = 0.152.

### Scope of the learning rate

ORPC's REF Cost models sheet applies the 10% rate to a "Single System
Variable cost" of $4,197,799.52 per first unit, which the workbook
explicitly defines as excluding "fixed costs such as project development
costs and fixed infrastructure" (REF cell J12). ORPC does not publish a
line-item split of variable vs. fixed.

We apply the rate only to CBS 1.1 MEC because:

1. MEC is unambiguously per-device manufacturing — clearly within the
   scope of unit-by-unit learning.
2. Other CBS components are documented separately and receive their own
   treatment; applying learning here would double-count.

This is a more conservative scope than ORPC's own application of the rate.

## 2. Electrical Infrastructure (C_elec)

Per-device 480 V → 6.6 kV seabed step-up transformer, plus a subsea 3-core AC cable from each
device to shore. Each ORPC TidGen 2.0 deployed at a candidate site has its own radial cable
directly to shore; at 6.6 kV the cross-section sits at the 70 mm² catalog floor across the
device's ≤5 km envelope (loss ≪ 10%). No onshore inverter station — retired with the DC
architecture (see `electrical/methodology.md`, "Why not 1000 VDC").

Source: see `electrical/source_data.md` and `electrical/methodology.md`.

    C_transformer      = 454,800 × S^0.6329 + 51,115,  S = P/PF = 0.526 MVA  ≈ $354,000/device
    C_cable_ORPC(site) = C_cable(L_shore)     (70 mm² @ $97/m within 5 km)

The transformer is site-independent (one per device) and enters constant CapEx (N-only); the
cable is the only shore-distance-driven electrical term. Cable cost from Nakhai (2023) Eq. 3
(`$/m = 4 × 0.3476 × CSA` for 3-phase AC); transformer from Collin et al. (2017) Eq. 2 (LV:MV
Wet). See `../optimization_cost_structure.md` for the C_const / c_site split.

## 3. Installation (C_inst)

Three-phase installation reflecting ORPC TidGen 2.0's floating BTMS architecture: tow (tug),
moor (multicat), cable (CLV). Plus a per-device flat cost for mooring system materials (chains
and anchors) from ORPC CBS.

Source: see `installation/source_data.md` and `installation/methodology.md`.

    tug_days        = 2 + 1.0  × N + 2
    multicat_days   = 2 + 7.33 × N + 2

    C_inst_tow      = tug_days      × $3,641/day
    C_inst_moor     = multicat_days × $3,732/day
    C_inst_cable    = 173,500 × L_total                 [Mattia Eq. 74, per-meter direct]
    C_mooring_mat   = $40,000 × N

    C_inst = C_inst_tow + C_inst_moor + C_inst_cable + C_mooring_mat

Tug and multicat cost functions from Mattia (2025) Table 2.1-12 (DTOceanPlus). Per-device
mooring time (7.33 days) from Mattia Section 2.1.18: 4 lines × (12 h anchor + 22 h line + 10 h
connection). Cable installation costs from Mattia (2025) Eqs. 72–74 (per-meter direct, all-in).
Mooring materials from ORPC CBS-A30 1.2.8 (single-device value).

## 4. Subsystem Integration (C_subsys)

Cost of assembling manufactured components into a working TidGen 2.0 device, testing, and QA.
Not captured in per-device manufacturing costs. Project-level cost.

    C_subsys = 0.10 × C_device_total

10% of total project device cost, from Hassan (2024) Eq. 3.

## 5. Contingency (C_contin)

Budget reserve for unforeseen costs and estimation uncertainty. Project-level cost.

    C_contin = 0.10 × (C_device_total + C_subsys + C_inst)

10% of (device + subsystem integration + installation), from Hassan (2024) Eq. 8.

## 6. Environmental Compliance & Permitting (C_EC)

NEPA, siting, scoping, environmental studies, permitting. Done once per project regardless of
N. Project-level cost.

    C_EC = 0.05 × (C_device_total + C_subsys + C_contin)

5% of (device + subsystem integration + contingency), from Hassan (2024) Eq. 9.

## Why percentages instead of ORPC's CBS values

For components 4–6, we use Hassan's percentages rather than ORPC's CBS line items because the
percentages **scale with project size N**. The optimization deploys variable numbers of
devices across selected sites, so contingency and overhead must grow with project scale.
ORPC's published CBS values are at fixed device counts and don't provide a scaling rule.

## Total CapEx

    C_device_total = Σ C_device_ORPC(i),  i = 1..N      (with learning rate, see Section 1)
    C_elec         = N · C_transformer + Σ C_cable(L_i)  (transformer N-only; cable per selected site)
    C_inst         = C_inst_tow + C_inst_moor + C_inst_cable + C_mooring_mat
    C_subsys       = 0.10 × C_device_total
    C_contin       = 0.10 × (C_device_total + C_subsys + C_inst)
    C_EC           = 0.05 × (C_device_total + C_subsys + C_contin)

    CapEx = C_device_total + C_elec + C_inst + C_subsys + C_contin + C_EC

## References

- Hassan, M. et al. (2025). Technoeconomic optimization of coaxial hydrokinetic turbines. *Renewable Energy*, 239, 122041. Eqs. 3, 8, 9.
- Marnagh, C. & McEntee, J. (2018). *D7.2.7 LCOE Cost and Performance Template*. DOE MHKDR Submission 269. CBS-A30.
- Component-level sources: see `device/source_data.md`, `electrical/source_data.md` and `electrical/methodology.md`, `installation/source_data.md` and `installation/methodology.md`.
