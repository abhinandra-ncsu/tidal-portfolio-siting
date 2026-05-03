# Electrical Infrastructure — Methodology

## Electrical Design Basis

| Parameter | Value | Source |
|---|---|---|
| Rated power per TriFrame | 105 kW (3 × 35) | VP Gen5 turbine design spec; Lewis et al. (2021) |
| Generation voltage | 480 V AC, 3-phase | VP BOP (MHKDR 318): "480 V bundled Power Cable umbilical". 3-phase is inferred — 480V is standard US 3-phase industrial voltage, not explicitly stated in source. |
| Power factor | 0.95 | Standard assumption (DNV GL 2015; Nakhai 2023 Table 1) |
| Current per TriFrame | 133 A | I = P / (sqrt(3) × V × PF) = 105,000 / (1.732 × 480 × 0.95) = 132.9 A |

## Configuration: Direct Cable to Shore

Each TriFrame gets its own submarine cable directly to shore. No offshore transformers, collection points, or voltage step-up.

**Why:** Verdant Power's RITE project (FERC P-12611) used individual 480V cables from each TriFrame to shoreline switchgear for a planned 1 MW array in the East River, NYC. We follow the same approach.

## Cable Selection Logic

For each site, select the cheapest ABB cable (70–500 mm² copper, 10 kV 3-core XLPE) where transmission loss ≤ threshold (default: 10%). If no cable meets the threshold, use the largest (500 mm²).

**Why 10 kV cables:** The lowest-voltage three-core submarine cable in ABB's catalog. The insulation is overrated for 480V, but voltage rating only affects insulation thickness — resistance and current capacity are the same as higher-voltage cables of the same CSA. The mechanical design (steel wire armour, waterproof sheathing) is what matters for submarine deployment.

**Why 10% loss threshold:** A tunable parameter in the optimization. Balances cable cost against energy delivery — tighter thresholds force larger (more expensive) cables at shorter distances.

## How Transmission Loss Affects AEP

```
AEP_delivered = AEP_generated × (1 - transmission_loss)
```

This replaces the fixed efficiency factor (eta = 0.98) used in Sandia RM1 (SAND2014-9040) with a distance-dependent loss that varies per site.
