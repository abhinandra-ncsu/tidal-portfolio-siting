# ORPC TidGen 2.0 — OpEx Source Data

## Per-Device Annual OpEx

From the **LCOE Summary** sheet of workbook `D7.2.7_DE-EE0007820_Revised LCOE_EE0007820 DOE
metrics_CA revised 05-23-2018.xlsx` (May-23 revised version), cell **F7**:

| Parameter | Value |
|---|---|
| Single Device OPEX (Improved System, May-23 revised) | $160,422.48/year |

This is ORPC's bundled per-device annual OpEx for the 500 kW TidGen 2.0 Improved System.

ORPC submitted D7.2.7 twice (April-30 and May-23, 2018). CBS line items and per-device CapEx
are identical; OpEx is the only difference (April-30: $148,422/yr, May-23: $160,422/yr). We
use the May-23 revised value as the later authoritative revision.

## Per-Device OpEx Breakdown

The **`Cost Breakdown Structure_051718`** sheet publishes a full hierarchical breakdown of
the $160,422.48 for the Improved System (500 kW TidGen 2.0). Values below are column **I**
("Proposed Configuration (Continuation Application)"), the single-device standalone figures:

| CBS # | Category | $/device/year | Cell |
|---|---|---:|---|
| **2** | **Operational Expenditures (OPEX)** | **160,422.48** | I282 |
| 2.1 | Operations | 91,737.08 | I283 |
| 2.1.1 | Environmental, Health & Safety Monitoring | 40,000.00 | I284 |
| 2.1.1.1 | Health, Safety Monitoring | 10,000.00 | I285 |
| 2.1.1.2 | Environmental Monitoring | 30,000.00 | I286 |
| 2.1.2 | Annual Leases / Fees / Costs of Doing Business | 5,000.00 | I287 |
| 2.1.3 | Insurance | 20,000.00 | I292 |
| 2.1.4 | Operations, Management & General Administration | 26,737.08 | I293 |
| 2.2 | Maintenance | 68,685.40 | I304 |
| 2.2.2 | Scheduled Maintenance | 45,790.30 | I306 |
| 2.2.3 | Unscheduled Maintenance | 22,895.10 | I316 |

Subtotals reconcile to the total: Operations $91,737.08 + Maintenance $68,685.40 =
$160,422.48. We do **not** adopt this total as-is. To use one insurance methodology across
both devices, we remove the explicit insurance line (**CBS 2.1.3, $20,000/device/year**),
carry the remaining **$140,422.48/device/year** as a flat non-insurance bundle, and re-model
insurance as `1% × CapEx` — computed from the pipeline's own CapEx, the same rule as VP (see
`opex_cost_components.md` and `optimization_cost_structure.md`).

## References

- Marnagh, C. & McEntee, J. (2018). *D7.2.7 Revised LCOE Cost and Performance Template*. DOE MHKDR Submission 269, Award DE-EE0007820. Sheet `LCOE Summary`, cell F7.
