# Turbine modification — device specification brief

**Date:** 2026-05-19
**Status:** design locked, advisor sign-off pending
**Supersedes:** earlier 48-node (D × P_rated) grid design (see git history); reframed after Stage 1 diagnosis at `experiments/turbine_modification/diagnosis/`

---

## Family

Four Verdant Gen5-class horizontal-axis tidal turbines: the Gen5 baseline at D = 5 m plus three smaller-rotor "Modified Verdant" variants at D = 2, 3, 4 m. Same architecture across the family (3 generators per Triframe). They differ only in rotor diameter and the operating quantities that follow from it.

## Variant specification

| Variant | D (m) | A (m²) | v_rated (m/s) | v_cut_in (m/s) | P_rated (kW) | Depth filter |
|---|---|---|---|---|---|---|
| Gen5 (baseline) | 5 | 19.63 | 2.03 | 0.61 | 31.2 | ≥ 10 m |
| ModVP-4 | 4 | 12.57 | 2.33 | 0.70 | 30.1 | ≥ 8 m |
| ModVP-3 | 3 | 7.07 | 2.32 | 0.70 | 16.8 | ≥ 6 m |
| ModVP-2 | 2 | 3.14 | 2.22 | 0.67 | 6.5 | ≥ 4 m |

## How these numbers are derived

Three Lewis et al. (2021) standardizations are taken as given for the entire family: **Cp = 0.37**, **v_cut_in = 0.30*v_rated**, and ρ = 1025 kg/m³ (seawater). The depth filter ≥ 2D is a deployment-clearance convention (rotor diameter D plus equal clearance above and below the rotor hub).

The remaining per-variant numbers are derived in this order:

1. **v_rated** is set to the 99.5th-percentile of per-site maximum tidal current speed (U_max, computed from the existing t_predic harmonic reconstruction at hourly resolution over 2013) on the device's uniquely-eligible site set:
   - For the **D = 5 baseline**, the eligible set is the full Gen5 candidate population at depth ≥ 10 m.
   - For the **modified variants**, the eligible set is the incremental shallow band [2D, 10) m — i.e., the sites the smaller device can reach that Gen5 cannot. This sizes v_rated to the population each modification is justified by.

2. **P_rated = ½ · ρ · A · Cp · v_rated³** (cube law at the rated point).

## Acknowledged design choices

Two judgement calls in this specification:

1. **The 99.5th-percentile choice for v_rated** was selected because, for the D = 5 baseline, applying the cube law (P_rated = ½·ρ·A·Cp·v_rated³) to Verdant's published P_rated = 35 kW gives v_rated = 2.11 m/s, and p99.5 of per-site U_max reproduces that value to within 4%. p99.5 is the unique percentile among {p50, p75, p90, p95, p99, p99.5, p99.9} that achieves this.

2. **Incremental band [2D, 10) m for the modified variants' v_rated** is justified by: each modified variant's v_rated should be sized to the sites it adds, not to the sites Gen5 already serves. The alternative (using the full eligible set [2D, ∞) m for every variant) gives ≤ 5% spread in v_rated across all four variants — i.e., effectively no per-D variation. The incremental-band choice produces ~15% variation between the baseline and the modified variants, which is a real resource-derived signal: the shallow sites newly unlocked by smaller D have systematically faster upper-tail velocities than the deep sites Gen5 serves.

## Electrical infrastructure

The cable-cost methodology from the existing VP pipeline (cheapest ABB three-core 10 kV CSA meeting ≤ 10% transmission loss, plus Mattia per-meter installation) is reused across the family without re-derivation. Cable from each TriFrame to shore is the only electrical infrastructure cost. Two assumptions make this reuse valid:

1. **Generation voltage V = 480 V is held constant across all four variants.** Per-TriFrame current I = P_TF / (√3 · V · PF) then shifts only because P_TF shifts, and the cable selector reruns against the same ABB catalog. 480 V 3-phase is appropriate across the kW range spanned by the family, but is held by choice, not derived per variant.

2. **TriFrame-of-3 architecture is preserved across all four variants**, so P_TF = 3 · P_rated. Already stated in the family description above; called out here because it is what keeps the per-TriFrame cable sizing formula valid across the family.

## Installation

The installation methodology from the existing VP pipeline (Phase 1: jack-up device placement; Phase 2: Mattia per-meter cable laying) is reused across the family without re-derivation. Number of TriFrames N and total cable length L_total are already explicit parameters in the formulas, so portfolio scale-up under smaller variants flows through the existing machinery. One assumption makes this reuse valid:

1. **TriFrame assembled mass is treated as a device-spec input per variant**, the same way as in the Gen5 baseline. It feeds the jack-up crane-capacity rule (65% × mass → crane tonnage → Mattia day-rate function). Gen5 uses 94,966 kg → 150-tonne crane → $33,647/day; modified variants resize through the same rule once per-variant mass is available.

## Device cost

C_device for the Gen5 baseline ($1,402,500 per TriFrame, from VP MHKDR 318) decomposes into five line items: Rotors (×3) $219K, IMA (×3) $510K, Nacelle/Pylon/Cones (×3) $424.5K, TriFrame 5m $187K, SCADA $62K. Modified variants keep the Gen5 dollar anchors and scale only the three turbine-package line items with rotor diameter. TriFrame and SCADA stay at Gen5 values across the family (same support structure, same per-array monitoring).

Scaling exponents are taken from Mattia (2025) Chapter 2.1:

| Line item | Gen5 anchor | Exponent | Formula | Mattia source |
|---|---|---|---|---|
| Rotors (×3) | $219,000 | D^2.7 | `C_rotors = $219K × (D/5)^2.7` | Eq. 3 (blade-dominant) |
| IMA (×3) | $510,000 | D^2.0 | `C_IMA = $510K × (D/5)^2.0` | Drivetrain bundle (Eqs. 19–30, 37) |
| Nacelle/Pylon/Cones (×3) | $424,500 | D^2.0 | `C_NPC = $424.5K × (D/5)^2.0` | Eqs. 31–36 (cover as pressure vessel) |

Per-variant C_device:

| Variant | D (m) | C_rotors | C_IMA | C_NPC | C_TriFrame | C_SCADA | **C_device** |
|---|---|---|---|---|---|---|---|
| Gen5 | 5 | $219.0K | $510.0K | $424.5K | $187K | $62K | **$1,402.5K** |
| ModVP-4 | 4 | $119.9K | $326.4K | $271.7K | $187K | $62K | **$967.0K** |
| ModVP-3 | 3 | $55.1K | $183.6K | $152.8K | $187K | $62K | **$640.5K** |
| ModVP-2 | 2 | $18.5K | $81.6K | $67.9K | $187K | $62K | **$417.0K** |

### Scaling assumptions for the diameter-scaled lines

D^2.7 (Rotors) is taken verbatim from Mattia Eq. 3; the two D^2.0 exponents (IMA, NPC) are our own reductions of Mattia's torque-driven and pressure-vessel mechanics. All three apply a single exponent to a multi-component line and hold fixed a quantity that varies across the family — but the resulting errors do not all point the same way.

**Rotors — verbatim blade exponent applied to the hub+blade line; plausibly under-charges the modified variants.** D^2.7 is Mattia's empirical *blade* cost metric (Eq. 3, `40·(D/2)^2.7`); the hub scales as D^2.0 (Eq. 7). Applying 2.7 to the combined "Hub + 3 blades" line assumes blade cost dominates the hub — unverified, since Verdant books the rotor as one $219K line with no blade/hub split. If the hub share is material the effective exponent falls toward 2.0, which for D < 5 raises rotor cost above the rule, i.e. under-charges the modified variants. Separately, Eq. 3 is purely geometric and carries no load term: the modified variants' higher v_rated (~32% in v², the thrust driver) would demand stronger blades, pushing the same direction. Mattia offers no v-dependent blade-cost function, so both effects are flagged by direction only, not quantified.

**IMA — assumes constant v_rated; under-charges the modified variants.** The drivetrain bundle is torque/power-sized, not geometry-sized: gearbox mass ∝ T_LSS^0.77, generator cost ≈ linear in T, power converter linear in P. Mapping to diameter via T ∝ P ∝ D²·v_rated³ collapses to D^2.0 **only if v_rated is constant across the family** — it is not (2.03→2.33 m/s; ~15%, ~52% in v³). A power-faithful sizing scales IMA by P_rated instead; against it the D^2.0 rule under-charges the modified variants' IMA by ≈30–50% (≈+17% on C_device for ModVP-4). The gearbox's sub-linear T^0.77 (≈v^2.3, not v³) puts the true bottom-up a little below the full-v³ figure — same direction, smaller. The whole IMA line (incl. brake) is scaled by this single drivetrain exponent.

**NPC — assumes constant depth and length; over-charges the modified variants.** The cover is sized as a hydrostatic pressure vessel (Eqs. 31–36): P = ρ·g·h, Mariotte t = P·D/(2σ) → t ∝ D, cylinder shell mass ∝ D²·L. Collapsing to D^2.0 rests on four held-constant assumptions: (a) cover diameter scales with rotor D; (b) deployment depth — hence pressure P — is constant; (c) cylinder length L is constant; (d) the cylinder dominates the hemispherical end-cap (itself a D³ term). Because the depth filter is 2D, a depth-faithful cover (sized to each variant's own shallower band) scales as (D/5)²·(h/10) = (D/5)³, and L ∝ D steepens it to D³ independently — either makes the modified variants ≈20–60% cheaper than the rule. A minimum wall gauge floors the thinning at small D, flattening the curve at the ModVP-2 end. Unlike IMA's v_rated, none of (a)–(d) is forced to vary by the spec, so holding them fixed is a legitimate design choice, not a dropped term.

Net direction across the three lines: Rotors and IMA both under-charge the modified variants (faster v_rated → stronger blades and more drivetrain torque), while NPC over-charges them (shallower deployment, steeper-than-D² geometry) — so the errors partially offset on C_device. All are acceptable under the simple-scaling approach; flagged here for transparency.

