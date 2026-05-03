# Annual Energy Production — Methodology

Adapted from Sandia SAND2014-9040 Section 2.3.1.1 (AEP Calculation for CEC Devices). Drivetrain efficiency terms are omitted; see *Note on drivetrain efficiencies* below.

## Formula

Annual energy production per TriFrame at site i:

```
E_i = (8766 / 1000) × η_avail × (1 - loss_i) × n_t × Σ_k P(u_k) × p_i(u_k)   [kWh]
```

| Term | Definition |
|------|-----------|
| 8766 | Hours per Julian year (365.25 days) |
| 1000 | W to kW conversion |
| η_avail | Operational availability |
| (1 - loss_i) | Transmission efficiency at site i (site-dependent) |
| n_t | Turbines per TriFrame |
| P(u_k) | Power output at speed bin center u_k (W), from turbine power curve |
| p_i(u_k) | Probability of speed u_k at site i, from speed histogram |

The summation Σ_k P(u_k) × p_i(u_k) gives the mean power output per turbine at site i. Each speed bin contributes energy proportional to the power produced at that speed and the fraction of time that speed occurs.

## Note on drivetrain efficiencies

Sandia SAND2014-9040 multiplies by η_gearbox × η_generator because its formula assumes P(u) is a *rotor* (mechanical) power curve — Sandia derives this from BEM/CFD models of the RM1/RM2/RM4 rotors, then layers manufacturer-supplied gearbox and generator efficiencies on top.

Our power curve uses Cp = 0.37 from Lewis et al. (2021), which is derived from manufacturer-published *rated electrical power* via Cp = 2 P_r / (ρ A V_r³) (Lewis Eq. 4) and validated against 0.5 Hz measurements from a grid-connected device (Lewis Fig. 2b). The 14 commercial devices in Lewis's Table 1 (MCT, Atlantis, Verdant Gen5, Schottel, etc.) all report rated power as nameplate electrical output, not rotor shaft power. Lewis's Cp is therefore a *system* Cp that already includes drivetrain and generator losses.

Combining a Lewis-derived Cp with Sandia's η_gearbox × η_generator would count those losses twice. We omit both terms.

## Power Curve

P(u_k) is defined by the turbine power curve (see `turbine_design_specification.md` for parameter values):

```
P(u) = 0                           if u < V_s  or  u > V_out
P(u) = 0.5 × ρ × A × Cp × u³     if V_s ≤ u ≤ V_r       (cubic region)
P(u) = P_r                         if V_r < u ≤ V_out      (rated region)
```

where V_s is cut-in speed, V_r is rated speed, V_out is cut-out speed, ρ is seawater density, A is rotor swept area, Cp is power coefficient, and P_r is rated power per turbine.

## Speed Histogram

p_i(u_k) is the probability of current speed u_k occurring at site i, obtained from a speed frequency histogram:

1. Reconstruct a year-long tidal current timeseries from harmonic constituents (1-hour resolution, 2013)
2. Bin current speeds into 100 bins spanning 0–5 m/s (bin width: 0.05 m/s)
3. Normalize by total count so that Σ_k p_i(u_k) = 1

u_k is the center of each bin (0.025, 0.075, ..., 4.975 m/s).

## Efficiency Parameters

| Parameter | Symbol | Value | Source |
|-----------|--------|-------|--------|
| Operational availability | η_avail | 0.95 | SAND2014-9040 Section 2.3.1.1 |

η_avail is based on land-based wind plant operational studies (Graves et al. 2008, Peters et al. 2012).

## Transmission Loss

Sandia uses a flat transmission efficiency η₃ = 0.98 for all sites. In our model, transmission loss is site-dependent because shore distance varies across candidate sites. The term (1 - loss_i) replaces Sandia's η₃.

See `cost/capex/electrical/methodology.md` for cable selection logic and loss computation.

## References

- Neary, V.S. et al. (2014). SAND2014-9040 — Methodology for Design & Economic Analysis of MEC Technologies. Sandia National Laboratories.
