# ORPC TidGen 2.0 — Electrical Infrastructure Methodology

## Electrical Design Basis

| Parameter | Value | Source |
|---|---|---|
| Rated power per device | 500 kW | `../../turbine_design_specification.md` |
| Generation voltage | 480 V AC, 3-phase | Modeled (this study); NREL/TP-5D00-66097 conversion model + the 277/480 VAC grid node in Tech Report Table 7 |
| Transmission voltage | 6.6 kV (per-device step-up) | Adopted to match VP — see Configuration |
| Power factor | 0.95 | DNV GL 2015; Nakhai 2023 Table 1 (as VP) |
| Transmission current | 46.0 A | I = P / (√3 · V · PF) = 500,000 / (1.732 · 6600 · 0.95) |

**Why not 1000 VDC.** Tech Report Table 7 lists "Subsea Power Transmission: 1000 VDC," but it
sits in a scenario-flavored "Power Output" block — its neighbor is "200 kW to grid, assuming
2 km transmission" — calibrated to ORPC's Admiralty-Inlet reference deployment. ORPC's own
power-conversion modeling (NREL/TP-5D00-66097; NREL/CP-5D00-66866) describes variable-frequency
AC with power-electronic conversion, not a portable fixed DC link. We therefore drop 1000 VDC as
a device constant and, mirroring the VP methodology, model a per-device 480 V → 6.6 kV step-up
with AC transmission.

## Configuration: Per-Device Step-Up to 6.6 kV

Each ORPC TidGen 2.0 steps its 480 V generation up to 6.6 kV at the seabed, then transmits to
shore on its own radial 3-core AC cable — no shared export cable, one step-up per device — exactly
as VP. This replaces the retired 1000 VDC / DC-monopolar architecture.

**Why step up.** At 480 V the per-device current is 633 A, and conductor loss is 3·I²·R·L, so the
10% loss cap forces large, expensive cross-sections and caps usable range near ~1 km. Stepping to
6.6 kV cuts the current to 46 A and the I²R loss ~189×; the cable then sits at the catalog-minimum
70 mm² across the device's entire ≤5 km envelope (≤1.6% loss at 5 km).

**Why the voltage level is fixed, not optimized.** For this device the choice of transmission
voltage is degenerate. The step-up transformer cost (Collin Eq. 2) depends only on rating, not
voltage; the cable cost depends only on cross-section; and at 500 kW over ≤5 km every standard MV
level (3.3–33 kV) drops the current far enough that the loss-limited cross-section falls below the
70 mm² catalog floor. Total electrical cost is therefore identical across all MV levels — the model
cannot distinguish them. Neither Nakhai's CSA-only cable cost nor Collin's rating-only transformer
cost carries a voltage-increasing term (the insulation/switchgear premiums that would, in reality,
create an interior optimum). Absent that term, any MV level yields the same LCOE; we adopt 6.6 kV
to match VP.

**Step-up transformer cost** (Collin et al. 2017 Eq. 2, LV:MV Wet — the same coefficients as VP):

```
C_transformer = 454,800 × S^0.6329 + 51,115     (S = rating in MVA)
S = P / PF = 0.500 / 0.95 = 0.526 MVA
C_transformer ≈ $354,000 per device
```

The transformer is site-independent — one per device regardless of location — so it enters
constant CapEx as raw CapEx (FCR annualization applies; the contingency and environmental-compliance
cascade does not), the same treatment VP gives it. See `../optimization_cost_structure.md`.

## Cable Selection

For each site, select the cheapest ABB 3-core 10 kV XLPE cable (70–500 mm² copper; the 10 kV,
Um = 12 kV rating comfortably covers 6.6 kV) where transmission loss ≤ 10%. Cable cost from
Nakhai (2023) Eq. 3. At 6.6 kV every site within the ≤5 km device envelope selects the 70 mm²
floor cable ($97/m); the loss cap never binds. Selection details in `source_data.md`.

## How Transmission Loss Affects AEP

```
AEP_delivered = AEP_generated × (1 − transmission_loss)
```

Per-site and distance-dependent, but ≤1.6% everywhere within 5 km at 6.6 kV.

## Comparison Arm (480 V, no step-up)

At 480 V the per-device current is 633 A — ampacity forces large cables even at zero distance, and
the 10% loss cap is exceeded past ~1 km even on the 500 mm² cross-section. We model this as a
comparison arm (transformer cost = $0). It does not scale past pilot deployments, the same
conclusion VP reaches for its 480 V arm — only sharper here, because ORPC's per-device power is
~5× VP's per-TriFrame power.

## Onshore

No separate onshore substation line. The DC→AC inverter station ($102,500/site in the retired DC
model) is removed — it existed only because transmission was DC. With AC transmission the device's
onboard inverter already delivers 60 Hz AC, so the onshore side reduces to step-down/interconnection,
matching VP's treatment (VP carries no explicit onshore substation cost).

## References

- Collin, A.J. et al. (2017). "Electrical Components for Marine Renewable Energy Arrays: A Techno-Economic Review." *Energies* 10(12): 1973. Eq. 2 (LV:MV Wet transformer).
- Nakhai, A.Y. (2023). *Electrical Infrastructure Cost Model for Marine Energy Systems*. NREL/TP-5700-87184. Eq. 3.
- ABB. *XLPE Submarine Cable Systems: Attachment to XLPE Land Cable Systems – User's Guide*. Rev 5. Table 41 (three-core, 10 kV).
- Muljadi, E., Wright, A., Gevorgian, V., Donegan, J., Marnagh, C., & McEntee, J. (2016). *Power Generation for River and Tidal Generators*. NREL/TP-5D00-66097. https://www.osti.gov/biblio/1259805
- Muljadi, E., Gevorgian, V., Wright, A., Donegan, J., Marnagh, C., & McEntee, J. (2016). *Electrical Power Conversion of a River and Tidal Power Generator*. NREL/CP-5D00-66866, IEEE NAPS 2016.
- Device parameter primary citations: see `../../turbine_design_specification.md`.
