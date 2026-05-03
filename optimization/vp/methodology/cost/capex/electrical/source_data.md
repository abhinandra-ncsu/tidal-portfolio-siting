# Electrical Infrastructure — Source Data

## Cable Specifications

From **ABB XLPE Submarine Cable Systems, Rev 5, Table 41**: Three-core cables, nominal voltage 10 kV (Um = 12 kV), copper wire screen.

| CSA (mm²) | Weight (kg/m) |
|---|---|
| 70 | 15.0 |
| 95 | 16.2 |
| 120 | 17.2 |
| 150 | 18.5 |
| 185 | 19.9 |
| 240 | 22.2 |
| 300 | 24.5 |
| 400 | 28.2 |
| 500 | 32.1 |

## Cable Cost Model

Costs below are computed from Nakhai (2023) Eq. 3 — a parametric model fit to historical submarine cable pricing. Manufacturer per-CSA prices are not publicly available for this voltage class.

From **Nakhai (2023) Eq. 3**: Cost per length per conductor = 0.3476 × CSA ($/m/conductor).

For 3-phase AC (4 conductors per Nakhai): Cost ($/m) = 4 × 0.3476 × CSA.

| CSA (mm²) | Cost ($/m) |
|---|---|
| 70 | 97 |
| 95 | 132 |
| 120 | 167 |
| 150 | 209 |
| 185 | 257 |
| 240 | 334 |
| 300 | 417 |
| 400 | 556 |
| 500 | 695 |

## Resistance and Transmission Loss

Resistance from copper resistivity: R = 0.0178 × 1000 / CSA (ohm/km).

| CSA (mm²) | R (ohm/km) |
|---|---|
| 70 | 0.254 |
| 95 | 0.187 |
| 120 | 0.148 |
| 150 | 0.119 |
| 185 | 0.096 |
| 240 | 0.074 |
| 300 | 0.059 |
| 400 | 0.045 |
| 500 | 0.036 |

Loss formula: `% loss = 3 × I² × R × L / P = 3 × 133² × R × L / 105,000 = 0.505 × R × L`, where I = 133 A (from P = 105 kW, V = 480 V, PF = 0.95).

| Distance | 70 mm² | 95 mm² | 120 mm² | 150 mm² | 185 mm² | 240 mm² | 300 mm² | 400 mm² | 500 mm² |
|---|---|---|---|---|---|---|---|---|---|
| 1 km | 12.8% | 9.4% | 7.5% | 6.0% | 4.8% | 3.7% | 3.0% | 2.3% | 1.8% |
| 2 km | 25.7% | 18.9% | 15.0% | 12.0% | 9.7% | 7.5% | 6.0% | 4.5% | 3.6% |
| 5 km | 64.1% | 47.2% | 37.4% | 30.0% | 24.2% | 18.7% | 14.9% | 11.2% | 9.0% |
| 10 km | >100% | 94.4% | 74.7% | 60.1% | 48.5% | 37.4% | 29.8% | 22.5% | 18.0% |

## Cable Selection (at 10% loss threshold)

| Distance | Selected cable | Cost ($/m) |
|---|---|---|
| 0 – 0.8 km | 70 mm² | 97 |
| 0.8 – 1.1 km | 95 mm² | 132 |
| 1.1 – 1.3 km | 120 mm² | 167 |
| 1.3 – 1.7 km | 150 mm² | 209 |
| 1.7 – 2.1 km | 185 mm² | 257 |
| 2.1 – 2.7 km | 240 mm² | 334 |
| 2.7 – 3.4 km | 300 mm² | 417 |
| 3.4 – 4.4 km | 400 mm² | 556 |
| 4.4 – 5.6 km | 500 mm² | 695 |

Beyond ~5.6 km, even the 500 mm² cable exceeds 10% loss.

## References

- ABB. *XLPE Submarine Cable Systems: Attachment to XLPE Land Cable Systems - User's Guide*. Rev 5. Table 41.
- Nakhai, A.Y. (2023). *Electrical Infrastructure Cost Model for Marine Energy Systems*. NREL/TP-5700-87184. Eq. 3, Figure 4.
