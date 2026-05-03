# Verdant Power Gen5 KHPS — Reference Materials

Raw reference workbooks for the Verdant Power Gen5 KHPS axial-flow tidal turbine and its TriFrame triplet support structure, obtained from DOE MHKDR submission 318.

## Provenance

- **Submitter:** Verdant Power
- **Publication date:** 2020-03-31 (filename suffix `03-31-20`)
- **Device program:** Gen5 KHPS, FERC Project P-12611 (Roosevelt Island Tidal Energy / RITE)
- **MHKDR submission 318:** https://mhkdr.openei.org/submissions/318 — three xlsx system content models

## Files

| Filename | Contents |
|---|---|
| `VP-Gen5-KHPS-Turbine-System-Content-Model_03-31-20.xlsx` | Turbine content model: rotor (hub + 3 blades), IMA (gearbox/generator/brake), nacelle/pylon/cones/fairings — masses, costs, maintenance hours |
| `VP-TriFrame-System-Content-Model-03-31-20.xlsx` | TriFrame triplet support structure: 5 m TriFrame mass/cost, deployment depth field, physical dimensions used for the depth constraint |
| `VP-BOP-System-Content-Model-03-31-20.xlsx` | Balance of plant: 480 V umbilical power cable and remaining BOP components |

## Device at a glance

- Axial-flow horizontal-axis tidal turbine, 3-blade rotor, 5 m diameter
- 35 kW rated electrical power per turbine; 3 turbines per TriFrame → 105 kW per TriFrame
- Cp = 0.37 (Lewis et al. 2021, Table 1; system Cp including drivetrain + generator losses)
- Reference deployment: East River, NYC (RITE, FERC P-12611), gravity-based structure on seabed

## Usage

These workbooks are the primary source for the VP cost and turbine-spec methodology in `../cost/`, `../turbine_design_specification.md`, and `../site_depth_constraint.md`. Specific cells and field definitions are cited inline in those documents.
