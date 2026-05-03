# OpEx Cost Components — VP Gen5 KHPS Tidal LCOE Model

Three-component model. Per-TriFrame replacement and repair costs are fixed; insurance varies by site.

---

## 1. Replacement Cost (c_replace)

Annual expected cost of spare parts and labor when components fail.

```
c_replace_parts = Σ (failure_rate_i × spare_part_fraction × component_cost_i)
c_replace_labor = Σ (failure_rate_j × repair_hours_j × n_workers_j × hourly_rate)
c_replace = c_replace_parts + c_replace_labor
```

- Spare part fraction: **15%** of component manufacturing cost per failure event (Mattia Sec 2.2). Tunable parameter — see `methodology.md`.
- Repair hours and workers: from Mattia Table 2.2-1 (GBS column)
- Labor: $54/hr (same as repair cost)

**$74,804/yr per TriFrame** ($52,391 parts + $22,413 labor).

## 2. Repair Cost (c_repair)

Annual cost of one coordinated maintenance trip plus per-component labor.

```
c_repair = c_vessel_trip + Σ c_labor_i

c_vessel_trip = (28/24) × $3,732/day = $4,355/yr   (single annual trip)
c_labor_i     = 28 hrs × n_workers_i × $54/hr      (per component)
```

- Maintenance hours: 28 hrs/yr per component, *labor-hours* per VP MHKDR 318 field definition
- Vessel: multicat at $3,732/day (Mattia Table 2.1-12, MV C-Odyssey 26m LOA), charged once per year
- Labor: $54/hr (Mattia Sec 2.2, €50 × 1.08 EUR/USD)

**$37,619/yr per TriFrame** ($4,355 vessel + $33,264 labor). See `methodology.md` for the single-trip assumption.

## 3. Insurance (c_insure)

```
c_insure = 1% × CapEx
```

1% of CapEx per year. Validated against MeyGen actual spend of 0.87% (Mattia 2025).

---

## Total OpEx (excl. insurance)

**$112,423/yr per TriFrame** ($74,804 replacement + $37,619 repair). Replacement and repair are fixed per TriFrame; only insurance varies by site.

See `source_data.md` for raw values from VP and Mattia. See `methodology.md` for mapping and derivations.

## References

- Hassan, M. et al. (2024). Technoeconomic optimization of coaxial hydrokinetic turbines. *Renewable Energy*, 239, 122041.
- Mattia, P. (2025). Techno-Economic Modelling and Comparative Analysis of HATEC. Master's thesis, Politecnico di Torino. Section 2.2, Table 2.1-12.
- Verdant Power (2020). VP Gen5 KHPS Content Models. DOE MHKDR Submission 318.
