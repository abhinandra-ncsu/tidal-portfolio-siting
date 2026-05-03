# OpEx — Source Data

## VP Gen5 Component Costs and Maintenance Hours

From **VP MHKDR 318** (March 2020), three Excel content model files. All components report 28 hrs/yr routine maintenance. The VP MHKDR field definition for "Annual Routine Maintenance Estimate" (Data sheet column N) is *labor-hours per component per year* — the worker-time needed to keep that component operational, not vessel-on-site time.

| Component | Mfg Cost | Maint. Hours/yr |
|---|---|---|
| Rotors (×3) | $219,000 | 28 |
| IMA — Gearbox/Generator/Brake (×3) | $510,000 | 28 |
| Nacelle, Pylon, Cones, Fairings (×3) | $424,500 | 28 |
| TriFrame 5m foundation | $187,000 | 28 |
| SCADA system + Equipment | $62,000 | 28 |

Source: same Excel files as device cost — see `../capex/device/verdant_power_device_costs.md`.

## Mattia Failure Rates and Worker Counts

From **Mattia (2025) Table 2.2-1** (Section 2.2). Failure rates from reliability studies of fixed (GBS) tidal turbines. Worker counts per maintenance intervention.

**Interpretation (Mattia §2.2, p. 35):** Failure rates are *per-component annual probabilities of failure*, not a distribution across components. The sum (~101%) is coincidental — it reflects that the total annual failure probability across all components is ≈1, plausible for the 2 MW Sabella-scale turbine to which Mattia's source (Kamidelivand 2023) calibrated. Our cost math (`failure_rate × spare_part_cost`, etc.) is consistent with this interpretation.

| Mattia Sub-component | Failure Rate (%/yr) | Repair Time GBS (hrs) | Workers |
|---|---|---|---|
| Blade | 9% | 7 | 2 |
| Drivetrain | 44% | 60 | 4 |
| Gearbox | 4% | 45 | 4 |
| Generator | 2% | 140 | 4 |
| Nacelle | 12% | 60 | 6 |
| Foundation | 6% | 500 | 8 |
| Electric system | 17% | 5 | 2 |
| Power converter | 2% | 50 | 4 |
| Control system | 1% | 45 | 2 |
| Pitch system | 4% | 44 | — |

## Mattia Vessel and Labor Costs

From **Mattia (2025) Table 2.1-12 and Section 2.2**:

- **Multicat vessel** (26m LOA, MV C-Odyssey): `63.23 × 26 + 1812.4 = 3,456 EUR/day` (Table 2.1-12)
- **Worker hourly rate**: €50/hr (Section 2.2)
- **Spare part fraction**: 15% of component manufacturing cost per failure event (Section 2.2)
- **Currency conversion**: 1 EUR = 1.08 USD (2024 annual average ECB rate)
  - Vessel: €3,456 × 1.08 = **$3,732/day**
  - Labor: €50 × 1.08 = **$54/hr**

## Insurance Benchmarks

| Source | Rate |
|---|---|
| Mattia (2025) | 1% of CapEx, citing MeyGen actual of 0.87% |
| Hassan (2024) | 2% at 1-10 units, 1% at 50, 0.5% at 100 |
| Sandia RM1 | ~1.5% small scale, ~0.4% at 100 units |
| MeyGen (actual) | 0.87% of CapEx |

## References

- Mattia, P. (2025). Techno-Economic Modelling and Comparative Analysis of HATEC. Master's thesis, Politecnico di Torino. Section 2.2, Table 2.1-12, Table 2.2-1.
- Verdant Power (2020). VP Gen5 KHPS Content Models. DOE MHKDR Submission 318.
- Hassan, M. et al. (2024). Technoeconomic optimization of coaxial hydrokinetic turbines. *Renewable Energy*, 239, 122041.
