# ORPC TidGen 2.0 — Electrical Infrastructure Source Data

## Device Electrical Specifications

See `../../turbine_design_specification.md` for primary citations. Values used in this
component:

| Parameter | Value |
|---|---|
| Subsea transmission voltage | 1000 VDC |
| Subsea cable architecture | DC monopolar, 2 conductors |
| Per-device rated power | 500 kW |
| Rated DC current | 500 A (= P / V) |
| Grid-side voltage | 3-Phase AC, 277/480 V, 60 Hz |

## Onshore Inverter Station

From CBS-A30, single-device column (cell I189):

| CBS # | Item | Cost ($) |
|---|---|---:|
| 1.2.3.4.5 | Onshore Substations (single device) | 102,500 |

For our single-device-per-site model, this is the per-site cost of the onshore DC→AC inverter station.

## Cable Specifications

From **ABB XLPE Submarine Cable Systems, Rev 5, Table 35**: Single-core copper cables, rated voltage 10–90 kV, 5 mm copper armour. DC monopolar deployment uses two single-core cables (positive + negative).

| CSA (mm²) | Ampacity, wide spacing (A) |
|---:|---:|
| 95 | 410 |
| 120 | 465 |
| 150 | 520 |
| 185 | 585 |
| 240 | 670 |
| 300 | 750 |
| 400 | 840 |
| 500 | 940 |
| 630 | 1050 |
| 800 | 1160 |
| 1000 | 1265 |

ABB Table 35 Note 4: cross sections larger than 1000 mm² can be offered on request. We restrict
the selection to standard catalog sizes (≤ 1000 mm²).

A cable can only be used if its rated ampacity ≥ ORPC's 500 A device current. The smallest
CSA that meets this is **150 mm²** (520 A wide-spacing rating); 95 and 120 mm² cables
(410 A and 465 A) fail the criterion and are excluded regardless of distance.

## Cable Cost Model

From **Nakhai (2023)** NREL/TP-5700-87184, Equation 3:

    $/m/conductor = 0.3476 × CSA       (CSA in mm²)

For DC the model assumes 2 conductors (positive + negative):

    $/m_total = 0.3476 × CSA × 2

| CSA (mm²) | Cost ($/m, 2-conductor DC) |
|---:|---:|
| 150 | 104 |
| 185 | 129 |
| 240 | 167 |
| 300 | 209 |
| 400 | 278 |
| 500 | 348 |
| 630 | 438 |
| 800 | 556 |
| 1000 | 695 |

## Resistance and Transmission Loss

Per-conductor resistance from copper resistivity ρ = 1.724 × 10⁻⁸ Ω·m:

    R = 17.24 / CSA       (Ω/km, CSA in mm²)

DC monopolar loss (current flows through both conductors in series from the load's perspective):

    % loss = 2 × I² × R × L / P  =  17.24 × L / CSA       (L in km, CSA in mm², I = 500 A, P = 500 kW)

| CSA (mm²) | R (Ω/km) | Max distance at 10% loss (km) |
|---:|---:|---:|
| 150 | 0.115 | 0.87 |
| 185 | 0.093 | 1.07 |
| 240 | 0.072 | 1.39 |
| 300 | 0.057 | 1.74 |
| 400 | 0.043 | 2.32 |
| 500 | 0.034 | 2.90 |
| 630 | 0.027 | 3.65 |
| 800 | 0.022 | 4.64 |
| 1000 | 0.017 | 5.80 |

## Cable Selection (at 10% loss threshold, with 150 mm² ampacity floor)

| Shore distance (km) | Selected CSA (mm²) | Cost ($/m) | Binding constraint |
|---:|---:|---:|---|
| 0 – 0.87 | 150 | 104 | ampacity |
| 0.87 – 1.07 | 185 | 129 | loss |
| 1.07 – 1.39 | 240 | 167 | loss |
| 1.39 – 1.74 | 300 | 209 | loss |
| 1.74 – 2.32 | 400 | 278 | loss |
| 2.32 – 2.90 | 500 | 348 | loss |
| 2.90 – 3.65 | 630 | 438 | loss |
| 3.65 – 4.64 | 800 | 556 | loss |
| 4.64 – 5.80 | 1000 | 695 | loss |

Beyond ~5.80 km, even the 1000 mm² cable exceeds 10% loss.

## References

- ABB. *XLPE Submarine Cable Systems: Attachment to XLPE Land Cable Systems – User's Guide*. Rev 5. Table 35 (single-core, 10–90 kV).
- Marnagh, C. & McEntee, J. (2018). *D7.2.7 Revised LCOE Cost and Performance Template*. DOE MHKDR Submission 269. CBS-A30 cell I189 (1.2.3.4.5 Onshore Substations).
- Nakhai, A.Y. (2023). *Electrical Infrastructure Cost Model for Marine Energy Systems*. NREL/TP-5700-87184. Eq. 3.
- Device parameter primary citations: see `../../turbine_design_specification.md`.
