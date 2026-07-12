# ORPC TidGen 2.0 — Electrical Infrastructure Source Data

## Device Electrical Specifications

See `../../turbine_design_specification.md` for primary citations. Values used in this component:

| Parameter | Value |
|---|---|
| Generation voltage | 480 V AC, 3-phase |
| Transmission voltage | 6.6 kV (per-device step-up) |
| Per-device rated power | 500 kW |
| Power factor | 0.95 |
| Transmission current | 46.0 A = P / (√3 · V · PF) |

The retired DC architecture (1000 VDC subsea, DC-monopolar 2-conductor, 500 A) is superseded — see
`methodology.md`, "Why not 1000 VDC." There is no onshore inverter station in the current model.

## Cable Specifications

From **ABB XLPE Submarine Cable Systems, Rev 5, Table 41**: three-core cables, nominal voltage
10 kV (Um = 12 kV), copper wire screen. Same catalog as VP (6.6 kV operation is covered by the
10 kV insulation class).

| CSA (mm²) | R (Ω/km) |
|---:|---:|
| 70 | 0.254 |
| 95 | 0.187 |
| 120 | 0.148 |
| 150 | 0.119 |
| 185 | 0.096 |
| 240 | 0.074 |
| 300 | 0.059 |
| 400 | 0.045 |
| 500 | 0.036 |

## Cable Cost Model

From **Nakhai (2023)** Eq. 3: cost per length per conductor = 0.3476 × CSA ($/m/conductor). For
3-phase AC (4 conductors per Nakhai): $/m = 4 × 0.3476 × CSA. Same as VP.

| CSA (mm²) | Cost ($/m) |
|---:|---:|
| 70 | 97 |
| 95 | 132 |
| 120 | 167 |
| 150 | 209 |
| 185 | 257 |
| 240 | 334 |
| 300 | 417 |
| 400 | 556 |
| 500 | 695 |

## Transmission Loss at 6.6 kV

3-phase loss with I = 46.0 A, P = 500 kW:

```
% loss = 3 × I² × R × L / P = 1.272 × R × L     (R in Ω/km, L in km)
```

| Distance | 70 mm² loss |
|---:|---:|
| 1 km | 0.3% |
| 2 km | 0.6% |
| 5 km | 1.6% |

At 6.6 kV the 70 mm² floor cable clears the entire ≤5 km device envelope; larger cross-sections are
never required, and the 10% loss cap never binds.

## Cable Selection (6.6 kV, 10% loss threshold)

| Shore distance (km) | Selected CSA (mm²) | Cost ($/m) | Binding constraint |
|---:|---:|---:|---|
| 0 – 5 (device max) | 70 | 97 | catalog floor (loss ≪ 10%) |

## Comparison Arm (480 V, no step-up)

3-phase loss with I = 633 A, P = 500 kW: `% loss = 240.3 × R × L`.

| Distance | 240 mm² | 300 mm² | 400 mm² | 500 mm² |
|---:|---:|---:|---:|---:|
| 0.5 km | 8.9% | 7.1% | 5.4% | 4.3% |
| 1.0 km | 17.8% | 14.2% | 10.8% | 8.7% |

At 480 V the loss cap forces ≥240 mm² at 0.5 km and is exceeded past ~1.15 km even on 500 mm²;
the 633 A current additionally pushes ampacity toward the large cross-sections at any distance.
The arm is effectively infeasible past ~1 km.

## Step-Up Transformer

From **Collin et al. (2017)** Eq. 2, LV:MV Wet:

```
C_transformer = 454,800 × S^0.6329 + 51,115     (S = rating in MVA)
S = P / PF = 0.500 / 0.95 = 0.526 MVA
C_transformer ≈ $354,000 per device
```

Site-independent (one per device); enters constant CapEx (N-only). See `../optimization_cost_structure.md`.

## References

- ABB. *XLPE Submarine Cable Systems: Attachment to XLPE Land Cable Systems – User's Guide*. Rev 5. Table 41 (three-core, 10 kV).
- Nakhai, A.Y. (2023). *Electrical Infrastructure Cost Model for Marine Energy Systems*. NREL/TP-5700-87184. Eq. 3.
- Collin, A.J. et al. (2017). "Electrical Components for Marine Renewable Energy Arrays: A Techno-Economic Review." *Energies* 10(12): 1973. Eq. 2.
- Device parameter primary citations: see `../../turbine_design_specification.md`.
