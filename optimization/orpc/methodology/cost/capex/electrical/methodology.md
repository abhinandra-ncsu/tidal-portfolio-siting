# ORPC TidGen 2.0 — Electrical Infrastructure Methodology

## Electrical Design Basis

Device electrical parameters are taken from `../../turbine_design_specification.md`:

| Parameter | Value |
|---|---|
| Per-device rated power | 500 kW |
| Subsea transmission voltage | 1000 VDC |
| Number of conductors | 2 (DC monopolar: positive + negative) |
| Rated DC current | 500 A (= P / V) |

The transmission voltage is fixed by the device hardware: ORPC's onboard PCC rectifies the
variable-frequency AC from the permanent magnet generator to 1000 VDC. We treat voltage as a
device-spec input, not a free parameter to be optimized via Nakhai's voltage-selection logic.

## Configuration: Single Device Per Site, Direct Cable to Shore

Each ORPC TidGen 2.0 deployed at a candidate site has its own subsea cable directly to shore,
carrying 1000 VDC. An onshore inverter station at each site converts DC to grid AC.

## Cable Selection Logic

For each site, select the smallest CSA in Nakhai's dataset where transmission loss ≤ 10%.
If no CSA meets the threshold, use the largest (1000 mm²). Cable cost from Nakhai (2023) Eq. 3:

    $/m_total = 0.3476 × CSA × 2                  (DC, 2 conductors)
    C_cable_ORPC(L_shore) = $/m_total × L_shore × 1000     ($, L in km)

The selection table by shore distance is in `source_data.md`. Two constraints bind: ampacity
sets a floor of 150 mm² (ABB Table 35 wide-spacing rating: 520 A at 150 mm², covering ORPC's
500 A); loss takes over beyond 0.87 km, walking up the catalog as distance grows.

## How Transmission Loss Affects AEP

    AEP_delivered = AEP_generated × (1 − transmission_loss)

The transmission loss varies per site, set by the cable CSA chosen for that distance.

## Onshore Inverter Station

Each site requires a DC→AC inverter station to deliver power to the grid (ORPC's PCC outputs
1000 VDC; the grid is AC). Cost: **$102,500 per site**, taken from CBS-A30 1.2.3.4.5 (Onshore
Substations, single-device value). ORPC does not publish a methodology for this figure, and we
have not independently validated it for a 500 kW DC→AC inverter station.

## Total Electrical Infrastructure Cost

    C_elec_ORPC(site) = C_cable_ORPC(L_shore) + 102,500     ($)

with `C_cable_ORPC(L_shore)` from the cable selection table.

## References

- ABB. *XLPE Submarine Cable Systems: Attachment to XLPE Land Cable Systems – User's Guide*. Rev 5. Table 35.
- Nakhai, A.Y. (2023). *Electrical Infrastructure Cost Model for Marine Energy Systems*. NREL/TP-5700-87184.
- Collin, A.J. et al. (2017). "Electrical Components for Marine Renewable Energy Arrays: A Techno-Economic Review." *Energies* 10(12): 1973.
- Device parameter primary citations: see `../../turbine_design_specification.md`.
