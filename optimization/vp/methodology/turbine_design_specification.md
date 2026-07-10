## Tidal Turbine Design Specification

Based on Verdant Power Gen5 KHPS (FERC P-12611), with a standardized power curve from Lewis et al. (2021).

### Turbine Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Turbine type | Horizontal-axis, axial-flow, 3-blade | VP Gen5 |
| Rotor diameter | 5.0 m | VP/DOE public documentation |
| Swept area | 19.63 m² | π × 2.5² |
| Power coefficient (Cp) | 0.37 | Lewis et al. (2021), mean of 14 operational devices (std 0.04) |
| Rated current speed (v_rated) | 2.03 m/s | p99.5 of per-site U_max over the depth ≥ 2D eligible set (see below) |
| Rated power | 31.2 kW per turbine | Derived: P = ½ρA·Cp·v_rated³ |
| Cut-in speed | 0.61 m/s | 0.30 × v_rated, per Lewis et al. (2021) |
| Cut-out speed | 4.57 m/s | Max speed in dataset |
| Minimum depth | 10.0 m | 2.0D clearance rule — see `site_depth_constraint.md` |
| Deployment | TriFrame (3 turbines per gravity-base frame) | VP Gen5 |
| Rated power per TriFrame | 93.6 kW | 3 × 31.2 kW |

### Rated Speed and Power

The rated speed is the p99.5 of per-site maximum current speed (U_max) across the device's eligible set (depth ≥ 2D = 10 m), reconstructed hourly over 2013. For Gen5 this is v_rated = 2.03 m/s. Rated power then follows from the turbine power equation:

```
P = 0.5 × ρ × A × Cp × v_rated³
  = 0.5 × 1025 × 19.63 × 0.37 × 2.03³
  ≈ 31,200 W = 31.2 kW per turbine
```

The p99.5 rule rates the whole diameter family (D = 2–8 m) under one uniform convention; see `experiments/turbine_modification/EXPERIMENT.md`. For Gen5 it lands within 4% of Verdant's published rated speed (2.11 m/s, implied by the 35 kW MHKDR 318 rating), so the baseline device stays anchored to the as-built machine.

### Power Curve

Following Lewis et al. (2021) Eq. 5:

- Below cut-in (< 0.61 m/s): P = 0
- Cut-in to rated (0.61 – 2.03 m/s): P = 0.5 × ρ × A × Cp × v³
- Above rated (> 2.03 m/s): P = 31.2 kW (constant)

### Clearance Rule: 2.0D

0.5D surface + 1.0D rotor + 0.5D seabed = 2.0D total = 10.0 m minimum depth.

Consistent with VP's deployment of a 5m rotor in 10m depth at the RITE project (East River, NYC).

### References

- Lewis, M. et al. (2021). A standardised tidal-stream power curve, optimised for the global resource. Renewable Energy, 170, 1308–1323.
- Verdant Power Gen5 KHPS — FERC P-12611, DOE MHKDR Submission 318.
- DOE/Sandia SAND2014-9040 — Reference Model Project.
