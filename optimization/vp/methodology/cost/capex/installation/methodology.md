# Installation Costs — Methodology

## Structure

Installation has two phases: device placement and cable laying. No mooring installation — VP Gen5 TriFrame is a gravity-based structure that sits on the seabed by its own weight. Assembled mass: 94,966 kg (TriFrame 76,950 + Rotors 2,007 + IMA 5,595 + Nacelle/Pylon/Cones 10,414; all from VP MHKDR 318).

## Phase 1: Device Installation

**Vessel choice:** Jack-up vessel. Meygen used a jack-up for their gravity-based AR1500 substructure installation because it provides a stable platform for precise seabed placement (Mattia Section 2.1.18).

**Crane capacity:** Assembled TriFrame mass is 94,966 kg (from VP MHKDR 318). Applying the 65% crane capacity rule (Mattia Section 2.1.18): 94,966 / 0.65 = 146,102 kg → 150 tonnes minimum.

**Day rate:** From Mattia Table 2.1-12 jack-up cost function at 150 tonnes crane capacity: 64.71 × 150 + 21,448.41 = 31,155 EUR/day. At 1.08 EUR/USD (2024 ECB annual average) ≈ $33,647/day.

**Placement time:** 1.5 days per TriFrame — midpoint of Mattia's 1-2 day range for gravity-based installations (24-hour working days), based on Meygen AR1500 experience.

**Mobilization + transit:** 2 days each side of the work (load at port + travel to site, then return + secure vessel). This is a flat project-overhead allowance, not pure transit time — Mattia's Eq. 68 uses distance-based transit (2 × d/V_vessel), and for our nearshore application (typical d < 10 km, jack-up tow speeds) pure transit is well under an hour each way. The 4 days represents mobilization, prep, weather standby, and securing.

**Formula:**
```
device_days = 2 + 1.5 × N + 2
C_inst_device = device_days × $33,647/day
```

## Phase 2: Cable Installation

**Approach:** Mattia (2025) §2.1.18 explicitly switches frameworks for cables — abandoning day-rate × time and adopting per-meter installation metrics from reference [61] for "better simplicity." We follow Mattia's framework directly.

**Cost metrics (Mattia Eqs. 72–74):**
- Surface laying: 100 €/m
- Drilled duct (buried): 282 €/m
- Split: 2/3 surface, 1/3 buried

**What the €/m bundles:** vessel charter (CLV), drilling rig for the buried portion, mobilization, crew, and consumables. Mattia treats the metric as all-in; we do the same. We do not separately model CLV day-rate, transit time, or mobilization for cable installation — these are inside the €/m. If a reviewer asks "where is the vessel cost?", the answer is: bundled into the €/m, sourced from Mattia's reference [61].

**Formula:**
```
L_total = sum of shore distances for all sites in portfolio (km)

c_blend      = (2/3) × 100 + (1/3) × 282 = 160.67 €/m   [Mattia Eq. 74]
C_inst_cable = c_blend × L_total × 1000 × 1.08 USD/EUR
             ≈ $173,500 × L_total
```

For a representative 10-TriFrame NE+NY portfolio with L_total ≈ 50 km: C_inst_cable ≈ **$8.7M**.

## Total Installation Cost

```
C_inst = C_inst_device + C_inst_cable
```
