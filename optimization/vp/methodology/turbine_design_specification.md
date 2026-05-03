## Tidal Turbine Design Specification

Based on Verdant Power Gen5 KHPS (FERC P-12611), with a standardized power curve from Lewis et al. (2021).

### Turbine Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Turbine type | Horizontal-axis, axial-flow, 3-blade | VP Gen5 |
| Rotor diameter | 5.0 m | VP/DOE public documentation |
| Swept area | 19.63 m² | π × 2.5² |
| Rated power | 35 kW per turbine | VP MHKDR 318; Lewis et al. (2021) Table 1 |
| Power coefficient (Cp) | 0.37 | Lewis et al. (2021), mean of 14 operational devices (std 0.04) |
| Rated current speed | 2.11 m/s | Derived: Vr = (2Pr / ρACp)^(1/3) |
| Cut-in speed | 0.63 m/s | 0.3 × Vr, per Lewis et al. (2021) mean of 14 devices (std 7%) |
| Cut-out speed | 4.57 m/s | Max speed in dataset |
| Minimum depth | 10.0 m | 2.0D clearance rule — see `site_depth_constraint.md` |
| Deployment | TriFrame (3 turbines per gravity-base frame) | VP Gen5 |
| Rated power per TriFrame | 105 kW | 3 × 35 kW |

### Rated Speed Derivation

From the turbine power equation:

```
P = 0.5 × ρ × A × Cp × Vr³

35,000 = 0.5 × 1025 × 19.63 × 0.37 × Vr³
Vr³ = 35,000 / 3,722.6
Vr = 2.11 m/s
```

### Power Curve

Following Lewis et al. (2021) Eq. 5:

- Below cut-in (< 0.63 m/s): P = 0
- Cut-in to rated (0.63 – 2.11 m/s): P = 0.5 × ρ × A × Cp × v³
- Above rated (> 2.11 m/s): P = 35 kW (constant)

### Clearance Rule: 2.0D

0.5D surface + 1.0D rotor + 0.5D seabed = 2.0D total = 10.0 m minimum depth.

Consistent with VP's deployment of a 5m rotor in 10m depth at the RITE project (East River, NYC).

### References

- Lewis, M. et al. (2021). A standardised tidal-stream power curve, optimised for the global resource. Renewable Energy, 170, 1308–1323.
- Verdant Power Gen5 KHPS — FERC P-12611, DOE MHKDR Submission 318.
- DOE/Sandia SAND2014-9040 — Reference Model Project.
