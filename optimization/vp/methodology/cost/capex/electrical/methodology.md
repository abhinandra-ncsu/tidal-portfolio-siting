# Electrical Infrastructure — Methodology

## Electrical Design Basis

| Parameter | Value | Source |
|---|---|---|
| Rated power per TriFrame | 93.6 kW (3 × 31.2) | VP Gen5 turbine design spec |
| Generation voltage | 480 V AC, 3-phase | VP BOP (MHKDR 318): "480 V bundled Power Cable umbilical". 3-phase inferred — 480 V is standard US 3-phase industrial voltage, not explicit in source. |
| Transmission voltage | 6.6 kV | Per-TriFrame step-up (see Configuration) |
| Power factor | 0.95 | Standard assumption (DNV GL 2015; Nakhai 2023 Table 1) |
| Transmission current per TriFrame | 8.6 A | I = P / (√3 × V × PF) = 93,600 / (1.732 × 6600 × 0.95) = 8.6 A |

## Configuration: Per-TriFrame Step-Up to 6.6 kV

Each TriFrame steps its 480 V generation up to 6.6 kV at the seabed, then transmits to shore on its own radial submarine cable. There are no offshore collection points and no shared export cable — the step-up is per device.

**Why step up.** At 480 V the per-TriFrame current is high, and conductor loss is 3·I²·R·L, so the 10% loss cap forces the cable selector onto large, expensive cross-sections even at short distances — pricing out distant sites. In the NE+NY set, ~75% of eligible sites are rejected, and rejection is distance-driven, not resource-driven. Stepping to 6.6 kV cuts the current 6600/480 ≈ 13.75× and the I²R loss ≈ 189×. The loss cap stops binding, the selector picks smaller conductors, and far sites become affordable.

**Step-up transformer cost.** A per-TriFrame seabed step-up is a wet, subsea-marinized unit, so the Collin et al. (2017) Eq. 2 LV:MV Wet coefficients apply:

```
C_transformer = 454,800 × S^0.6329 + 51,115     (S = rating in MVA)
S = P_TF / PF = 93.6 / 0.95 = 0.0985 MVA
C_transformer ≈ $156,000 per TriFrame
```

The transformer is site-independent — one per TriFrame regardless of location — so it enters constant CapEx as raw CapEx: the FCR annualization and the insurance fraction apply, but the contingency and environmental-compliance cascade does not, the same treatment as the cable and other electrical items.

**Comparison arm (480 V).** Verdant's as-built RITE project (FERC P-12611) used individual 480 V cables from each TriFrame to shoreline switchgear, with no step-up. We model that configuration as a comparison arm (transformer cost = $0). It does not scale past pilot deployments: at matched cost the 6.6 kV design delivers more energy at every scale, and lowers the LCOE floor and portfolio variance at 25 MW and above.

## Cable Selection Logic

For each site, select the cheapest ABB cable (70–500 mm² copper, 10 kV 3-core XLPE) where transmission loss ≤ threshold (default: 10%). If no cable meets the threshold, use the largest (500 mm²).

**Why 10 kV cables:** The lowest-voltage three-core submarine cable in ABB's catalog; its 10 kV (Um = 12 kV) insulation comfortably covers 6.6 kV operation. Voltage rating only affects insulation thickness — resistance and current capacity are the same as higher-voltage cables of the same CSA. The mechanical design (steel wire armour, waterproof sheathing) is what matters for submarine deployment.

**Why 10% loss threshold:** A tunable parameter in the optimization. Balances cable cost against energy delivery — tighter thresholds force larger (more expensive) cables at shorter distances.

## How Transmission Loss Affects AEP

```
AEP_delivered = AEP_generated × (1 - transmission_loss)
```

This replaces the fixed efficiency factor (eta = 0.98) used in Sandia RM1 (SAND2014-9040) with a distance-dependent loss that varies per site.
