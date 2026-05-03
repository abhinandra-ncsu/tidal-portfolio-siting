# OpEx Cost Components — ORPC TidGen 2.0

Single-component model. ORPC publishes a per-device annual OpEx directly; we adopt it as
bundled (all-in: replacement, repair, insurance, administration, etc.), flat per device.

Source: see `source_data.md`.

## 1. Per-Device Annual OpEx (C_OpEx_year)

    C_OpEx_year = $160,422 × N      ($/year)

ORPC's published per-device OpEx for the Improved System (500 kW TidGen 2.0), from the LCOE
Summary May-23 revised version. Linear in N. Not site-varying.

## Bundled Interpretation

ORPC does not publish a breakdown of the $160,422 into replacement, repair, insurance,
administration, or other categories. We adopt the value as **all-in**: it includes whatever
ORPC factored into their LCOE calculation. We do **not** add a separate insurance term (e.g.
1% × CapEx) on top, because doing so risks double-counting if insurance is already included in
ORPC's $160,422.

The cost is therefore **flat per device, not site-varying**.

## References

- Marnagh, C. & McEntee, J. (2018). *D7.2.7 Revised LCOE Cost and Performance Template*. DOE MHKDR Submission 269, Award DE-EE0007820.
