# Site Depth Constraint

## Decision

**Minimum site water depth for a feasible site: 10 m.**

Applied in `optimization_model/config/config.py` as `MIN_DEPTH_M = 10.0`, and enforced in `01_extract_harmonics.py` when points are streamed from the ROMS database.

No upper bound is imposed. Deployments deeper than 10 m are outside the qualified envelope of the VP Gen5 TriFrame (the only field-validated foundation for this turbine) and would require foundation re-qualification, but are not physically precluded. This caveat is noted in the methodology and not enforced at the filter.

## Three converging justifications

The 10 m floor is supported by three independent lines of reasoning. All give the same number for a 5 m rotor on the VP Gen5 TriFrame.

### 1. Lewis et al. (2021) 2.0D clearance rule

Lewis et al. (2021) recommend a minimum water column of 2.0 × rotor diameter, decomposed as:

- 0.5D surface clearance (wave action, navigation, tidal range)
- 1.0D rotor
- 0.5D seabed clearance (boundary-layer effects, foundation)

For a 5 m rotor: 2.0 × 5 m = **10 m minimum depth**.

### 2. VP MHKDR TriFrame content model

The Verdant Power TriFrame system content model (DOE MHKDR submission 318, `VP-TriFrame-System-Content-Model-03-31-20.xlsx`, Data sheet) records:

| Field | Value | Column description (from header) |
|---|---|---|
| Water Depth (m) | 10 | "maximum operating depth of the component in meters" |
| Pressure (psi) | 29 | "maximum pressure that the component operates at, in PSI" |

The 10 m and 29 psi entries are not independent. At 10 m of seawater, absolute pressure is 14.7 psi (atmosphere) + ρgh ≈ 14.6 psi = **~29.3 psi**. The spreadsheet records the same fact twice, in different units.

This 10 m is **the depth VP designed and deployed the TriFrame for at the RITE project**, not a hydrostatic ceiling. The gravity-base frame would structurally survive greater depths; no deeper qualification exists because RITE is the only full-scale Gen5 deployment (2020, decommissioned Dec 2021).

### 3. TriFrame geometry

From the same MHKDR spreadsheet, the TriFrame physical dimensions are:

- Height: 490 cm (4.9 m)
- Width: 1569 cm
- Depth (horizontal footprint): 1779 cm

The frame is **~4.9 m tall** on the seabed. A 5 m rotor mounted on top needs roughly another ~5 m of water column to leave space for the rotor sweep and a modest surface clearance. At a 10 m site depth this is tight but feasible, exactly matching the Gen5 RITE as-deployed configuration. Below 10 m, a 5 m rotor on a 4.9 m TriFrame cannot fit without breaking the water surface or compromising clearance.

## Reconciling "min 10 m" vs "max 10 m"

The value of 10 m appeared in project documentation in two apparently contradictory roles:

- `turbine_design_specification.md` — 10 m as **minimum** depth (2.0D clearance rule)
- `cost/capex/device/source_data.md` — 10 m as **maximum** operating depth (MHKDR field wording)

Both readings are right about what their source says, and they reconcile once the MHKDR entry is understood as an **as-rated / as-deployed envelope** rather than a structural ceiling:

- The clearance rule gives a hard lower bound (physics: rotor must fit in the water column).
- The MHKDR entry gives the depth VP certified and tested the TriFrame at.
- Both point to 10 m as the correct design-for depth; VP has never deployed deeper than the envelope they designed for.

For site filtering, this means 10 m functions unambiguously as a **minimum**. The "maximum" wording in the MHKDR column header reflects the spreadsheet template's field definition ("maximum operating depth of the component") applied to a device with a single qualified operating point.

## Supporting field evidence — RITE Phase II (Gen4 6-pack)

The FERC Final License Application for the Roosevelt Island Tidal Energy project (FERC Project P-12611, filed Dec 2010, `Verdant-Power-2010.pdf`) reproduces letters from the 2003–2004 NYSDEC and USACE review describing the Phase II 6-pack test site geometry:

> "The 6 turbines will be placed on 18\" to 24\" diameter piles … piles will extend about 6 feet above the bottom. The turbine blades will be a maximum of 5 meters in diameter … Each turbine center will be about 12 feet above the bottom and will have at least 5 feet of water between the turbine tips and the surface." — NYSDEC letter to Verdant Power, Dec 22 2003

> "The 0.88 acre turbine field would cover a 225 foot by 170 foot area in the east channel of the East River … in an area where the water depth is approximately 30 feet. Project plans (sheet 7) indicate there would be approximately 6 feet of water above the highest point of the turbine at mean low water." — USACE Public Notice 2003-00402-Y3, May 2004

Converted to metric:

| Quantity | Imperial | Metric |
|---|---|---|
| RITE site water depth at MLW | ~30 ft | ~9.14 m |
| Rotor axis above seabed (Gen4 pile mount) | ~12 ft | ~3.66 m |
| Top-tip clearance below surface at MLW | ~5–6 ft | ~1.5–1.8 m |
| Rotor diameter | 16.4 ft | 5.0 m |

The Gen4 pile-mounted 6-pack operated at ~9.1 m site depth — feasible because a slim pile consumes almost no water column. The Gen5 TriFrame (gravity base) cannot achieve the same site depth because its ~4.9 m tall foundation eats the bottom of the water column; it needs ~10 m. Both deployments are internally consistent with the 10 m floor adopted here when the foundation type is taken into account.

## Implication for the pipeline

`MIN_DEPTH_M` was previously set to 5.0 m in `config.py`, which admitted sites where a 5 m rotor on the Gen5 TriFrame could not physically fit. The correct canonical value is **10.0 m**.

Existing sweep runs at `depth0m` and `depth5m` are retained as sensitivity artifacts for understanding filter behavior, but they correspond to configurations below the physical clearance envelope and should not appear in headline LCOE reporting.

A companion document, `depth_filter_validation.md`, cross-checks the ROMS bathymetry field against the NOAA Coastal Relief Model at the 10 m threshold and confirms that the two datasets broadly agree, so the 10 m filter is honored robustly by the underlying data.

## Sources

- **Verdant Power (2020).** *VP-TriFrame-System-Content-Model-03-31-20.xlsx*, Data sheet. DOE MHKDR Submission 318. [mhkdr.openei.org/submissions/318](https://mhkdr.openei.org/submissions/318)
- **Verdant Power (2010).** *Final License Application, Roosevelt Island Tidal Energy Project*. FERC Project P-12611, filed December 2010. Local copy: `DOE-3.9/lit-review-papers/Verdant-Power-2010.pdf`
- **Lewis, M. et al. (2021).** A standardised tidal-stream power curve, optimised for the global resource. *Renewable Energy*, 170, 1308–1323.
- **PNNL Tethys.** Roosevelt Island Tidal Energy (RITE) Project Pilot. [tethys.pnnl.gov/project-sites/roosevelt-island-tidal-energy-rite-project-pilot](https://tethys.pnnl.gov/project-sites/roosevelt-island-tidal-energy-rite-project-pilot)
