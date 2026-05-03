## Tidal Turbine Design Specification — ORPC Advanced TidGen 2.0

Based on the ORPC Advanced TidGen Power System as documented in DOE MHKDR submissions 269 and 273 (Marnagh & McEntee, ORPC, 2018; DOE Award DE-EE0007820). The Advanced TidGen 2.0 is a DOE-funded design-phase deliverable; it is not listed in ORPC's current commercial product lineup (orpc.co, checked 2026-04-23). The MHKDR deliverables remain the most detailed publicly-available primary-source specification for an ORPC tidal device and are used here as the basis for academic LCOE modeling.

### Turbine Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Turbine type | Cross-flow CEC, 2 stacked TGUs, 8 rotors total | Tech Report D7.2.9 p. 12; SCM Characteristics sheet |
| Mounting | Suspended in water column on buoyant tension mooring system (BTMS) | Tech Report Table 7 |
| Anchor | Gravity (site-dependent) | Tech Report Table 7 |
| Mooring lines per device | 4 | Mattia (2025) Section 2.4.4 typical default for floating tidal; ORPC does not state explicitly |
| Generator | Permanent magnet, one per TGU | Tech Report D7.2.9 p. 12 |
| Subsea transmission | 1000 VDC | Tech Report Table 7 |
| Subsea cable architecture | DC monopolar (2-conductor: positive + negative) | Inferred from 1000 VDC subsea spec; convention per Nakhai (2023) Eq. 3 |
| Grid voltage | 277/480 VAC, 3-phase, 60 Hz | Tech Report Table 7 |
| Rated power (design phase) | 500 kW | SCM `targetPeakPower`; LCOE Metrics sheet cell C23 (Improved System) |
| Power coefficient (Cp) | 0.39 | SCM `CEC Resource and Power` sheet, constant over u = 0.5 – 2.4 m/s |
| Rated current speed | 3.0 m/s | SCM power curve — speed at which electrical power reaches 500 kW |
| Cut-in speed | 0.5 m/s | SCM power curve — first non-zero electrical power |
| Maximum operational speed | 3.5 m/s | Tech Report Table 7 |
| Survivable current speed | 4.0 m/s | Tech Report Table 7 |
| Minimum operating depth | 18 m (at MLLW) | Tech Report Table 7 |
| Maximum operating depth | 40 m (at MHHW) | Tech Report Table 7 |
| Maximum shore distance | 5 km | Tech Report Table 7 |
| Device dimensions (L × H × W) | 34.6 m × 9.0 m × 6.3 m | Tech Report Table 7 |
| Device dry mass | 140,000 kg | Tech Report D7.2.9 p. 12 |
| System design life | 20 years (in water) | Tech Report Table 7 |
| Availability | 0.92 | LCOE Metrics sheet cell C24 (Improved System) |

### Power Curve

Cut-in to rated (0.5 ≤ u ≤ 3.0 m/s): tabulated in SCM `CEC Resource and Power` rows 17–42 at 0.1 m/s increments. Cp = 0.39 constant from 0.5 to 2.4 m/s, then declining Cp regulation from 2.4 to 3.0 m/s where electrical power reaches 499 kW (≈ the 500 kW rated value).

Above rated speed: SCM does not tabulate electrical power past 3.0 m/s (rows 43–45 leave the electrical power column blank); we treat as zero in our model. The Tech Report Table 7 gives maximum operational speed 3.5 m/s and survivable current speed 4.0 m/s; the operating regime above 3.0 m/s is interpreted as rated-power regulation up to the operational max, with shutdown at survival speed. This regime is **not** directly tabulated in SCM and is inferred from the design envelope.

Below cut-in (u < 0.5 m/s): P = 0 (SCM rows 12–16, all zero).
Above survival (u > 4.0 m/s): P = 0 (interpreted; not in SCM).

### Notes on Parameter Choices

- **Rated power = 500 kW.** SCM `targetPeakPower` and LCOE Metrics C23 (Improved System) both state 500 kW. Tech Report Table 7 separately reports "200 kW to grid (assuming 2 km transmission)" — a scenario-specific after-transmission figure, not a device rating. External sources (CompositesWorld; NREL/SNL CRADA CRD-12-481) describe the Advanced TidGen as 150–175 kW per TGU (≈300–350 kW system-level), not commercially released. We adopt the 500 kW design-phase figure because it is the value used to compute ORPC's own published AEP (520.5 MWh/yr) and array LCOE ($603/MWh). ORPC's workbook places the 500 kW figure in DOE-template sections labeled "Optional - Improved System Performance" — a reporting-structure convention that distinguishes the design-phase upgrade from the deployed Baseline (150 kW Cobscook Bay) system. The 500 kW value is consistent across SCM, all four LCOE Metrics scenario sheets in the May-23 workbook, and ORPC's published AEP figure.
- **Rated current speed = 3.0 m/s.** Derived from the SCM power curve (speed at which electrical power reaches the 500 kW rated value). Tech Report Table 7 states 2.25 m/s, which pairs with the 200 kW grid-side figure; we use 3.0 m/s for consistency with the 500 kW rated power.
- **Minimum depth = 18 m.** Tech Report Table 7 (CDR-frozen April 30 2018). SCM workbook lists 16 m; the Tech Report is the engineering-authoritative source.
- **Device mass = 140,000 kg.** Tech Report D7.2.9 p. 12 supersedes SCM's 160,000 kg.
- **Availability = 0.92.** From LCOE Metrics C24 in the "CA revised, AI" sheet (Admiralty Inlet reference site) of the May-23 workbook. Table 7 separately lists "System Availability: 94%", and the WP / CI / sine-3-m/s scenario sheets in the same workbook also show 0.94. We use the 0.92 Admiralty Inlet value for consistency with the rest of the methodology, which uses Admiralty Inlet as the reference site.

### References

- Marnagh, C. & McEntee, J. (2018). D7.2.8 System Content Model; D7.2.7 LCOE Cost and Performance Template (April 30 original and May 23 revised versions); D7.2.6 Updated TA1 Metrics. DOE MHKDR Submission 269, Award DE-EE0007820. https://mhkdr.openei.org/submissions/269
- Marnagh, C. & McEntee, J. (2018). D7.2.9 Final System Design Technical Report. DOE MHKDR Submission 273, Award DE-EE0007820. https://mhkdr.openei.org/submissions/273
- ORPC website, current product lineup and commercial status: https://orpc.co (verified 2026-04-23)
