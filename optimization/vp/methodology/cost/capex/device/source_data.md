# Verdant Power Gen5 KHPS — Device Costs

Source: DOE MHKDR Submission 318 (March 2020), three Excel files.
We use the **Total Cost** column for the cost model; **Delivered Price Goal** is shown alongside for completeness — see `../../capex_cost_components.md` §1 Device Cost for the choice rationale.

## Cost per TriFrame

From **VP-Gen5-KHPS-Turbine-System-Content-Model_03-31-20.xlsx** (Data sheet):

| Component | Mass (kg) | Total Cost | Delivered Price Goal |
|---|---|---|---|
| Gen5 KHPS Turbine (3) Rotor (Hub + 3 blades) | 2,007 | 219,000 | 309,000 |
| Gen5 KHPS Turbine (3) IMA — Gear Box/Generator/Brake | 5,595 | 510,000 | 719,000 |
| Gen5 KHPS Turbine (3) Nacelle, Pylon, Cones, and Fairings | 10,414 | 424,500 | 599,000 |

From **VP-TriFrame-System-Content-Model-03-31-20.xlsx** (Data sheet):

| Component | Mass (kg) | Material Cost | Mfg Cost | Total Cost | Delivered Price Goal |
|---|---|---|---|---|---|
| Verdant Power 5m TriFrame | 76,950 | 110,000 | 77,000 | 187,000 | 391,000 |

From **VP-BOP-System-Content-Model-03-31-20.xlsx** (Data sheet):

| Component | Total Cost | Delivered Price Goal | Included in device cost? |
|---|---|---|---|
| SCADA system + Equipment | 62,000 | 112,000 | Yes |
| TriFrame Power Cable - UW | 15,800 | 32,000 | No — site-dependent, modeled separately |

The BOP xlsx also lists ADCPs (monitoring equipment, $91,500); not part of the cost model.

## Totals

| | Total Cost (mfg) | Delivered Price Goal |
|---|---|---|
| **Device cost per TriFrame** | **1,402,500** | **2,130,000** |

## Field Definitions (from MHKDR content model)

- **Total Cost**: manufacturing cost (material + fabrication)
- **Delivered Price Goal**: estimated price delivered to assembly area (adds overhead, margin, transport)
- **Annual Routine Maintenance Estimate**: all components report 28 hrs/yr
- **Target Availability**: 88% for turbine components, 99.7% for TriFrame structure
- **Water Depth**: TriFrame spreadsheet reports 10 m under the "maximum operating depth" field (paired with 29 psi, which is the absolute pressure at 10 m seawater — the same fact in different units). This is the RITE as-designed / as-deployed depth, not a structural ceiling. See `../../../site_depth_constraint.md` for the derivation of the 10 m site-depth floor used in site filtering.
