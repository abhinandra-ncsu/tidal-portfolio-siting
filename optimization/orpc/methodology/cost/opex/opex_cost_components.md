# OpEx Cost Components — ORPC TidGen 2.0

Two-component model, harmonized with the VP pipeline so both devices treat insurance the
same way:

1. **Non-insurance bundle** — ORPC's published per-device OpEx with its insurance line
   removed. Flat per device.
2. **Insurance** — `1% × CapEx`, the same rule the VP model uses. A separate term that is
   partly site-varying.

Source: see `source_data.md`.

## 1. Non-Insurance Bundled OpEx (C_OpEx_year)

    C_OpEx_year = $140,422 × N      ($/year)

ORPC publishes a bundled per-device OpEx of $160,422.48 for the Improved System (500 kW
TidGen 2.0), which the `Cost Breakdown Structure_051718` sheet resolves into Operations
($91,737.08) and Maintenance ($68,685.40). We remove the explicit insurance line (CBS 2.1.3,
$20,000/device/year) and carry the remainder — **$140,422/device/year** — as a flat, all-in
bundle (monitoring, leases & fees, administration, scheduled/unscheduled maintenance). Linear
in N. Not site-varying.

## 2. Insurance (c_insure)

    c_insure = 1% × CapEx

Modeled identically to the VP pipeline: 1% of CapEx per year, validated against MeyGen's
actual spend of 0.87% (Mattia 2025). "CapEx" here is the **pipeline's own computed CapEx**
(device manufacturing on the learning curve + BOS + the site-dependent cable), *not* ORPC's
published $9.47M single-device figure. Because that CapEx includes the shore-distance-driven
cable, insurance is **partly site-varying**: it enters the constant term (on device + BOS
CapEx) and `c_site_i` (on cable CapEx). See `optimization_cost_structure.md` for the split.

## Why we strip ORPC's bundled insurance

The aim is one insurance methodology across both devices. ORPC instead books insurance as a
fixed **$20,000/device/year** inside its bundle — a flat figure that neither scales with
CapEx nor varies by site. We remove that line (stripping it first is what prevents
double-counting) and let the `1% × CapEx` rule stand in its place.

This is more a change of *structure* than of *level*: the flat $20k is already the same order
as 1% of the pipeline's per-device CapEx (a few $M), so replacing it mainly changes how
insurance **scales** — with CapEx, and partly with shore distance — rather than its magnitude.
The 1% rule yields roughly a few tens of $k per device, N- and site-dependent; the exact
per-device amount and the effect on ORPC LCOE will be quantified on re-run.

## References

- Marnagh, C. & McEntee, J. (2018). *D7.2.7 Revised LCOE Cost and Performance Template*. DOE MHKDR Submission 269, Award DE-EE0007820.
- Mattia, P. (2025). *Techno-Economic Modelling and Comparative Analysis of HATEC*. Master's thesis, Politecnico di Torino.
