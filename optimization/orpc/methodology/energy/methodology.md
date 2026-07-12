# Annual Energy Production — ORPC TidGen 2.0

Adapted from Sandia SAND2014-9040 Section 2.3.1.1 (AEP Calculation for CEC Devices).
Drivetrain efficiency terms are omitted; see *Why no separate drivetrain efficiency* below.

## Formula

Annual energy delivered per device at site i (MWh/yr):

```
E_i = (8766 / 10^6) * η_avail * (1 - loss_i) * n_t * Σ_k P(u_k) * p_i(u_k)
```

| Term | Definition | Value / source |
|------|-----------|---------------|
| 8766 | Hours per Julian year (365.25 × 24) | constant |
| 10^6 | Convert W·hr to MWh | constant |
| η_avail | Operational availability | 0.92 — `LCOE Metrics` sheet C24, "Improved System" |
| (1 − loss_i) | Site-dependent transmission efficiency | from cable selection (`cost/capex/electrical/methodology.md`) |
| n_t | Devices per selected site | 1 (`DEVICES_PER_SITE` in config) |
| P(u_k) | Power at speed bin center u_k (W) | tabulated power curve, see below |
| p_i(u_k) | Probability that the speed at site i falls in bin u_k | from `histograms.nc` |

## Power Curve

P(u_k) is evaluated at the histogram bin centers (0.025, 0.075, …, 4.975 m/s) by the following piecewise rule:

| Speed regime | P(u) |
|---|---|
| u < 0.5 m/s (below cut-in) | 0 |
| 0.5 ≤ u ≤ 3.0 m/s | linear interpolation on the SCM-tabulated electrical curve (31 points, 0.1 m/s spacing) |
| 3.0 < u ≤ 3.5 m/s | rated plateau (500 kW) |
| u > 3.5 m/s (above max operational) | 0 |

The SCM column is **electrical power** (D7.2.8 SCM workbook, `CEC Resource and Power` sheet column F); the full table is reproduced in `turbine_design_specification.md`.

The plateau-then-cutout choice for u > 3.0 (rather than the SCM's literal zero past 3.0) follows the spec doc's interpretation: max operational speed = 3.5 m/s, with shutdown above. We zero out at 3.5 m/s because the device is no longer operating to produce power above its operational ceiling.

## Speed Histogram

p_i(u_k) is the fraction of the year that site i sees a current speed in bin u_k, obtained from a speed frequency histogram built by:

1. Reconstructing a year-long (2013, 1-hour resolution) tidal current speed timeseries at site i from harmonic ellipse parameters via T_TIDE.
2. Binning reconstructed speeds into 100 bins of width 0.05 m/s spanning 0–5 m/s and normalizing to a probability distribution.

## Why no separate drivetrain efficiency

The SCM `Electrical Power` column gives the device's electrical output at the device terminals — it already accounts for rotor-to-electrical conversion (drivetrain, generator, on-device power conversion).

Sandia's SAND2014-9040 AEP formula assumes P(u) is a *rotor* (mechanical) power curve and layers gearbox and generator efficiencies on top to get electrical output. Combining a Sandia-style efficiency stack with the SCM's already-electrical curve would double-count those losses, so we omit those efficiency terms.

## Transmission Loss (1 − loss_i)

Site-dependent. The smallest-CSA cable that keeps loss ≤ 10% is selected per site, with fallback to the largest catalog size (500 mm²) if none meet the threshold. With the per-device 480 V → 6.6 kV step-up (see `cost/capex/electrical/methodology.md`), the 3-phase loss `% loss = 3·I²·R·L/P = 1.272·R·L` (I = 46.0 A, P = 500 kW) stays ≤ 1.6% on the 70 mm² floor cable across the device's entire ≤5 km envelope. The resulting fractional loss enters the energy formula as `(1 − loss_i)`.

## References

- Marnagh, C. & McEntee, J. (2018). D7.2.8 System Content Model. DOE MHKDR Submission 269.
- Marnagh, C. & McEntee, J. (2018). D7.2.7 Revised LCOE Cost and Performance Template. DOE MHKDR Submission 269. Sheet `LCOE Metrics`, cell C24 (availability).
- Neary, V.S. et al. (2014). SAND2014-9040 — Methodology for Design & Economic Analysis of MEC Technologies. Sandia National Laboratories.
- Pawlowicz, R., Beardsley, B., Lentz, S. (2002). Classical tidal harmonic analysis with errors in MATLAB using T_TIDE. *Computers & Geosciences*, 28(8), 929–937.
