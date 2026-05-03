# Installation Costs — Source Data

## Vessel Charter Rate Cost Functions

From **Mattia (2025) Table 2.1-12** (DTOceanPlus project). All costs in EUR/day.

| Vessel type | Input parameter | Domain | Function (EUR/day) |
|---|---|---|---|
| Jack-up | Crane capacity (tonnes) | 50 ≤ x < 755 | 64.71x + 21448.41 |
| CLV | Total cable storage (tonnes) | 565 ≤ x ≤ 10000 | 2.46e-4 x² + 7.25x + 53090 |

## Device Installation Time

From **Mattia (2025) Section 2.1.18** (p. 33), citing Meygen AR1500 experience:

- Gravity-based substructure installation: **1 to 2 days** per device (24-hour working days)
- Turbine mounting after substructure placement: less than 60 minutes (Meygen AR1500)

## Cable Installation Costs

From **Mattia (2025) Eqs. 72–74** (p. 33):

```
Cost_cable_laid         = 100 €/m     (Eq. 72) — surface laying on seabed
Cost_cable_drilled_duct = 282 €/m     (Eq. 73) — burial in drilled duct
COST_cable_inst = 100 × (2/3) × L + 282 × (1/3) × L    (Eq. 74)
```

## Crane Capacity Rule

From **Mattia (2025) Section 2.1.18** (p. 31): "the dry weight of the component to lift should be less than 65% of the crane lifting capacity."

## Hassan 2024 Installation Vessel Specs (Cross-Reference)

From **Hassan (2024) Table 3**:

| Vessel | Deck area | Speed | Day rate |
|---|---|---|---|
| DP2 (device) | 3,533.75 m² | 10.3 m/s | $30,000/day |
| CLV (cable) | 10,700 ton turntable | 6.43 m/s (900 m/h) | $190,000/day |

Note: Hassan's vessels are for deep-water tethered TCDTs, not nearshore gravity-based devices. His CLV is significantly larger and more expensive than what our application requires.

## References

- Mattia, P. (2025). Techno-Economic Modelling and Comparative Analysis of HATEC. Master's thesis, Politecnico di Torino. Section 2.1.18, Table 2.1-12, Eqs. 72-74.
- Hassan, M. et al. (2024). Technoeconomic optimization of coaxial hydrokinetic turbines. *Renewable Energy*, 239, 122041. Table 3.
- DTOceanPlus project. Vessel charter rate cost functions. Referenced as [46] in Mattia (2025).
