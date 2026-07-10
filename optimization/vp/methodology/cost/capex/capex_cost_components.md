# CapEx Cost Components — VP Gen5 KHPS Tidal LCOE Model

Six-component model. Percentages from Hassan (2024); applied across our N-range as a simplifying assumption (cross-scale invariance not validated). Electrical infrastructure is per-site (varies by shore distance). Cable installation is portfolio-dependent (total shore distance across selected sites). All other costs depend only on N.

---

## 1. Device Cost (C_device)

Manufacturing cost of the TriFrame hardware: turbines (rotor, drivetrain, nacelle), gravity-base foundation, and SCADA. Uses VP "Total Cost" field (manufacturing), not "Delivered Price Goal" (which includes margin/overhead), because we apply a learning rate to the manufacturing base.

| Component | Total Cost (mfg) |
|---|---|
| Rotors (x3) | $219,000 |
| IMA (x3) | $510,000 |
| Nacelle/Pylon/Cones (x3) | $424,500 |
| TriFrame 5m | $187,000 |
| SCADA | $62,000 |
| **Unit 1 cost** | **$1,402,500** |

Source: VP MHKDR 318 (2020). See `device/source_data.md` for verification against source Excel files.

**Learning rate: 12%** (Hassan 2024, EU Ocean Energy Status Report). Unit i costs C_device × i^b where b = ln(1-0.12)/ln(2). Total project device cost: `C_device_total = Σ C_device × i^b` for i = 1 to N.

## 2. Electrical Infrastructure (C_elec)

Each TriFrame steps its 480 V generation up to 6.6 kV at the seabed, then transmits to shore on its own radial submarine cable (no offshore collection points). Two parts:

- **Cable (per-site).** Cheapest ABB cable (70–500 mm² copper, 10 kV three-core) that keeps transmission loss ≤ 10%; cost scales with shore distance. Cost: Nakhai (2023) Eq. 3; specs ABB XLPE Rev 5, Table 41. This is the only per-site CapEx component.
- **Step-up transformer (per-TriFrame).** Wet/subsea unit sized to S = P_TF / PF = 0.0985 MVA; Collin (2017) LV:MV Wet → ≈ $156,000/TriFrame. Site-independent, so it enters constant CapEx, not the per-site term. Zero in the 480 V comparison arm.

Transmission loss reduces delivered AEP: `AEP_delivered = AEP_generated × (1 - loss)`.

Cable installation is portfolio-dependent (see `optimization_cost_structure.md` for the full categorization). See `electrical/methodology.md` and `electrical/source_data.md`.

## 3. Installation (C_inst)

Portfolio-dependent. Two phases, using **two different costing frameworks** per Mattia (2025) §2.1.18:

```
Phase 1 — Device (jack-up, day-rate × time, Mattia Eq. 68):
  C_inst_device = (2 + 1.5 × N + 2) × $33,647/day

Phase 2 — Cable (per-meter metric, Mattia Eq. 74):
  C_inst_cable  = 160.67 €/m × L_total × 1000 × 1.08
               ≈ $173,500 × L_total

where L_total = sum of shore distances for all sites in portfolio (km)

C_inst = C_inst_device + C_inst_cable
```

Device placement: 1.5 days per TriFrame (Meygen gravity-based data). Cable installation: Mattia Eqs. 72–74 — €/m metric bundles vessel charter, drilling rig (for the 1/3 buried portion), mobilization, crew, and consumables. Device-phase transit: 2 days each. See `installation/methodology.md` for full Phase 2 derivation.

## 4. Subsystem Integration (C_subsys)

Cost of assembling manufactured components into a working TriFrame, testing, and QA. Not captured in per-component manufacturing costs. Project-level cost.

`C_subsys = 0.10 × C_device_total`

10% of total project device cost. Hassan (2024) Eq. 3. Note: applied across our N-range as a simplifying assumption — Hassan's 10% is calibrated at the scale of his source paper; cross-scale invariance is not validated.

## 5. Contingency (C_contin)

Budget reserve for unforeseen costs and estimation uncertainty. Project-level cost.

`C_contin = 0.10 × (C_device_total + C_subsys + C_inst)`

10% of (device + subsystem integration + installation). Hassan (2024) Eq. 8. Note: applied across our N-range as a simplifying assumption; cross-scale invariance not validated.

## 6. Environmental Compliance & Permitting (C_EC)

NEPA, siting, scoping, environmental studies, permitting. Project-level cost — done once per project regardless of number of TriFrames.

`C_EC = 0.05 × (C_device_total + C_subsys + C_contin)`

5% of (device + subsystem integration + contingency). Hassan (2024) Eq. 9. Note: applied across our N-range as a simplifying assumption; cross-scale invariance not validated.

---

## Total CapEx

```
C_device_total = Σ C_device × i^b,  i = 1..N     (with learning rate)
C_inst_device  = (2 + 1.5 × N + 2) × $33,647/day
C_inst_cable   = 160.67 €/m × L_total × 1000 × 1.08  ≈ $173,500 × L_total
C_inst         = C_inst_device + C_inst_cable
C_subsys       = 0.10 × C_device_total
C_contin       = 0.10 × (C_device_total + C_subsys + C_inst)
C_EC           = 0.05 × (C_device_total + C_subsys + C_contin)
C_elec         = Σ cable_cost_i  for selected sites
C_xfmr         = N × $156,000                    (6.6 kV step-up; $0 in the 480 V arm; no contingency/EC cascade)

CapEx = C_device_total + C_elec + C_inst + C_subsys + C_contin + C_EC + C_xfmr
```

## References

- Collin, A.J. et al. (2017). Component-level cost models for offshore tidal-stream arrays. *Energies*, 10(12), 1973.
- Hassan, M. et al. (2024). Technoeconomic optimization of coaxial hydrokinetic turbines. *Renewable Energy*, 239, 122041.
- Mattia, P. (2025). Techno-Economic Modelling and Comparative Analysis of HATEC. Master's thesis, Politecnico di Torino.
- Neary, V.S. et al. (2014). Methodology for Design and Economic Analysis of MEC Technologies. SAND2014-9040.
