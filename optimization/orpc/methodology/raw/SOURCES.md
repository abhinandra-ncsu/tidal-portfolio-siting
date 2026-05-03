# ORPC TidGen 2.0 — Reference Materials

Raw reference workbooks and report for the ORPC TidGen 2.0 cross-flow tidal current turbine, obtained 2026-04-11 from DOE MHKDR submissions 269 (xlsx workbooks) and 273 (final design PDF).

## Provenance

- **DOE Award:** DE-EE0007820
- **Project title:** Advanced TidGen® Power System — LCOE Calculations and System Overview
- **Submitter:** Ocean Renewable Power Company (ORPC)
- **Authors:** Cian Marnagh and Jarlath McEntee (ORPC)
- **Publication date:** 2018-06-14
- **Award period:** 2017-11-01 to 2021-12-31
- **MHKDR submission 269:** https://mhkdr.openei.org/submissions/269 — four xlsx deliverables (D7.2.6, D7.2.7 ×2, D7.2.8)
- **MHKDR submission 273:** https://mhkdr.openei.org/submissions/273 — D7.2.9 final system design technical report PDF

## Files

| Filename | MHKDR | Contents |
|---|---|---|
| `D7.2.8_DE-EE0007820_System Content Model.xlsx` | 269 | System Content Model: device specs, measured power curve, resource probability distribution |
| `D7.2.7_DE-EE0007820_Revised LCOE_EE0007820 DOE metrics_CA revised 05-23-2018.xlsx` | 269 | Revised LCOE workbook (May-23): multi-level Cost Breakdown Structure with dollar figures, array scenarios, reference cost models. Reproduces ORPC's published $603.58/MWh array LCOE — used as primary reference downstream. |
| `D7.2.7_DE-EE0007820_LCOE_EE0007820 DOE metrics_CA 04-30-2018.xlsx` | 269 | Original LCOE workbook (April-30): same single-device CBS values as the revised version, but with explicit array column labels that disambiguate cost-model vs. no-cost-model totals. |
| `D7.2.6_DE-EE0007820_Updated TA1 Metrics.xlsx` | 269 | TA1 metrics summary |
| `D7.2.9_DE-EE0007820_Final System Design Technical Report.pdf` | 273 | Final system design technical report. |

## Device at a glance

- Cross-flow CEC (vertical-axis rotors mounted horizontally for cross-flow operation)
- `targetPeakPower = 500,000 W` per device
- Cp ≈ 0.39 (primary source, from SCM `CEC Resource and Power` sheet)
- Reference deployment: 60 m water depth, 300 m shore distance, Admiralty Inlet (Puget Sound)

## Usage

These workbooks are the primary source for the ORPC cost and energy methodology in `../cost/`, `../energy/`, and `../turbine_design_specification.md`. Specific cells are cited inline in those documents.
