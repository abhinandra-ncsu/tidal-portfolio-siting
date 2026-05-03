# OpEx — Methodology

## Mapping VP Components to Mattia Failure Rates

VP Gen5 reports costs for 5 components per TriFrame. Mattia defines failure rates for 10 sub-components. The mapping aggregates Mattia's sub-component failure rates to VP's cost categories:

| VP Component | Mfg Cost | Mattia Sub-components | Combined Failure Rate |
|---|---|---|---|
| Rotor (Hub + 3 blades) | $219,000 | Blade (9%) | 9% |
| IMA (Gearbox/Generator/Brake) | $510,000 | Drivetrain (44%) + Gearbox (4%) + Generator (2%) | 50% |
| Nacelle, Pylon, Cones, Fairings | $424,500 | Nacelle (12%) | 12% |
| TriFrame structure | $187,000 | Foundation (6%) | 6% |
| SCADA + Equipment | $62,000 | Electric system (17%) + Power converter (2%) + Control system (1%) | 20% |

**Excluded:** Pitch system (Mattia: 4%) — VP Gen5 is fixed-pitch.

## 1. Replacement Cost Calculation

Two sub-costs: spare parts and labor to perform the replacement.

**Spare parts:**
```
c_replace_parts = Σ (failure_rate_i × 15% × component_cost_i)

Rotor:     9% × 15% × $219,000  =  $2,957
IMA:      50% × 15% × $510,000  = $38,250
Nacelle:  12% × 15% × $424,500  =  $7,641
TriFrame:  6% × 15% × $187,000  =  $1,683
SCADA:    20% × 15% × $62,000   =  $1,860
                                   --------
Total:                             $52,391/yr
```

**Note on 15% spare part fraction:** This value comes from Mattia Section 2.2, representing the average cost of the part actually replaced per failure event — not every failure requires full component replacement. Sandia RM1 uses 100% (full replacement), which is conservative. The 15% is a tunable parameter; at 100%, spare parts cost would be $349,275/yr.

**Replacement labor:**

When a failure occurs, workers must retrieve the component, perform the replacement, and reinstall. Repair times for GBS devices from Mattia Table 2.2-1. For components mapping to multiple Mattia sub-components, each sub-component's contribution is computed separately.

```
c_replace_labor = Σ (failure_rate_j × repair_hours_j × n_workers_j × $54/hr)

Rotor:      0.09 × 7 × 2 × $54                                           =     $68
IMA:        (0.44 × 60 × 4 + 0.04 × 45 × 4 + 0.02 × 140 × 4) × $54
            = (105.6 + 7.2 + 11.2) × $54 = 124.0 × $54                   =  $6,696
Nacelle:    0.12 × 60 × 6 × $54                                           =  $2,333
TriFrame:   0.06 × 500 × 8 × $54                                          = $12,960
SCADA:      (0.17 × 5 × 2 + 0.02 × 50 × 4 + 0.01 × 45 × 2) × $54
            = (1.7 + 4.0 + 0.9) × $54 = 6.6 × $54                        =    $356
                                                                            --------
Total:                                                                     $22,413/yr
```

**Total replacement cost: $52,391 + $22,413 = $74,804/yr per TriFrame.**

## 2. Repair Cost Calculation

VP MHKDR 318 reports 28 hrs/yr routine maintenance for all components. The field definition (Data sheet column N, "Annual Routine Maintenance Estimate") is *labor-hours per component per year* — the focused worker-time needed to keep that component operational. It is NOT vessel-hours per component.

**Vessel time is charged once per year, not per component.** Routine maintenance is performed during a single coordinated annual trip; multiple components are addressed in parallel by workers with different specialties. Charging vessel time per component would charge for 5 separate trips that don't operationally happen.

Worker counts come from Mattia Table 2.2-1, mapped to VP components using the dominant sub-component:

| VP Component | Workers | Reasoning |
|---|---|---|
| Rotor | 2 | Mattia: Blade = 2 workers |
| IMA | 4 | Mattia: Drivetrain, Gearbox, Generator all = 4 workers |
| Nacelle | 6 | Mattia: Nacelle = 6 workers |
| TriFrame | 8 | Mattia: Foundation = 8 workers |
| SCADA | 2 | Mattia: Electric system = 2 workers (dominant at 17% of 20%) |

```
c_repair = c_vessel_trip + Σ c_labor_i

c_vessel_trip = (28/24) × $3,732/day = $4,355/yr   (single annual trip, ~28 hrs on site)

c_labor_i = 28 hrs × n_workers_i × $54/hr   (per component)
  Rotor:    28 × 2 × $54  =  $3,024
  IMA:      28 × 4 × $54  =  $6,048
  Nacelle:  28 × 6 × $54  =  $9,072
  TriFrame: 28 × 8 × $54  = $12,096
  SCADA:    28 × 2 × $54  =  $3,024
  Σ labor:                  $33,264

c_repair = $4,355 + $33,264 = $37,619/yr per TriFrame
```

If multiple maintenance trips per year are warranted (e.g., quarterly inspections for sites with high biofouling), `c_vessel_trip` scales linearly with `n_trips`. Default is 1 trip/yr.

## 3. Vessel Choice for Maintenance

**Multicat** (25-28m LOA) — a small nearshore workboat with crane. Appropriate because:
- VP Gen5 turbines are small (~2 tonnes each)
- Sites are nearshore (median ~5 km from shore)
- Multicat is the standard O&M vessel for small tidal devices (Mattia Section 2.1.18)

## Insurance

1% of CapEx per year (flat rate). MeyGen actual spend was 0.87%, supporting this estimate.
