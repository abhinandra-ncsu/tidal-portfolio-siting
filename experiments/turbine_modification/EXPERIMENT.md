# Turbine modification — diameter ladder (device specification brief)

**Date:** 2026-06-08
**Status:** draft for review
**Supersedes:** the shrink-only D = 5 → 2 design (variants `gen5`, `modvp4`, `modvp3`, `modvp2`; brief at `results/vp/turbine_modification/turbine_modification.md`). This brief extends the family upward to D = 8 m and re-derives `v_rated` for the whole ladder under one uniform rule.

---

## Why re-run

The old family only shrank the rotor. It never asked the opposite question: does a *bigger* rotor help? Bigger rotor means more swept area and more energy per device — but the ≥2D depth rule confines it to deeper water, which carries fewer eligible sites and (per the shallow-band finding) slower upper-tail currents. The tradeoff could break either way on the CV/LCOE frontier. Nobody has looked.

Adding the larger variants forces a second change. The old `v_rated` rule sized each smaller device to its **incremental shallow band [2D, 10) m** — the sites it uniquely unlocks. A larger device unlocks nothing; it is a strict subset of Gen5's deep sites, so the rule has no upward analog. We therefore re-derive `v_rated` for **all seven variants** under one uniform rule (below). This rewrites the smaller variants' speeds, so the family is re-run from scratch for internal consistency rather than appended to.

## Family

Seven Verdant Gen5-class horizontal-axis tidal turbines: the Gen5 baseline at D = 5 m, three smaller variants (D = 4, 3, 2 m), and three larger variants (D = 6, 7, 8 m). Same architecture across the family — 3 generators per TriFrame, Cp = 0.37, generation voltage 480 V, depth filter ≥ 2D. They differ only in rotor diameter and the quantities that follow from it.

## Variant specification

Cost and geometry are fixed by D and are filled below. The three speed-derived quantities (`v_rated`, `v_cut_in`, `P_rated`) are produced by `derive_variants.py` (see *Derivation*) and are marked pending here — they must not be hand-set.

| Variant | D (m) | A (m²) | Depth ≥ | v_rated (m/s) | v_cut_in (m/s) | P_rated (kW) | **C_device** |
|---|---|---|---|---|---|---|---|
| modvp2 | 2 | 3.14 | 4 m | _pending_ | _pending_ | _pending_ | **$417.0K** |
| modvp3 | 3 | 7.07 | 6 m | _pending_ | _pending_ | _pending_ | **$640.5K** |
| modvp4 | 4 | 12.57 | 8 m | _pending_ | _pending_ | _pending_ | **$967.0K** |
| **gen5 (baseline)** | **5** | **19.63** | **10 m** | _pending_ | _pending_ | _pending_ | **$1,402.5K** |
| modvp6 | 6 | 28.27 | 12 m | _pending_ | _pending_ | _pending_ | **$1,952.9K** |
| modvp7 | 7 | 38.48 | 14 m | _pending_ | _pending_ | _pending_ | **$2,623.9K** |
| modvp8 | 8 | 50.27 | 16 m | _pending_ | _pending_ | _pending_ | **$3,420.5K** |

Naming follows the existing convention (`modvp<D>`); the three new variants are `modvp6`, `modvp7`, `modvp8`. Gen5 keeps its name and its role as the comparison reference.

A = π(D/2)². Depth filter = 2D (rotor diameter plus equal clearance above and below the hub).

## Derivation — `derive_variants.py`

A single checked-in script produces the speed column for all seven variants, so the ladder is reproducible instead of a set of literals. It writes the full `VARIANTS` dict that `config.py` consumes.

**The uniform v_rated rule.** For each variant:

1. Take the candidate population at depth ≥ 2D — the device's **full eligible set**.
2. For each site in that set, compute **U_max**, the per-site maximum tidal current speed, from the existing t_predic harmonic reconstruction at hourly resolution over 2013.
3. **v_rated = p99.5 of U_max** across that eligible set.

This is the same percentile and the same reconstruction the baseline already used; the only change is that *every* variant now uses its full eligible set [2D, ∞) rather than an incremental band. The rule applies identically up and down the ladder.

Expected shape of the result (to confirm on run, not assume): smaller D reaches shallow, fast-tail sites and lands a higher v_rated; larger D is confined to deep, calmer water and lands a lower one. Gen5's eligible set is exactly [10, ∞) m, so its v_rated is unchanged from the current 2.03 m/s — the baseline is held fixed by construction, and the other six move around it.

**Then, per variant, deterministically:**

- v_cut_in = 0.30 · v_rated   (Lewis et al. 2021 standardization)
- P_rated = ½ · ρ · A · Cp · v_rated³,   ρ = 1025 kg/m³, Cp = 0.37
- P_TriFrame = 3 · P_rated

**I/O.** Inputs: the candidate set with per-site depth, and the harmonic reconstruction over the candidate population (sources: the same `harmonics.nc` / `candidates.nc` the pipeline already produces; exact field names confirmed at implementation). Output: a `VARIANTS` table (printed + written to `experiments/turbine_modification/variants_derived.csv`) that is pasted into `config.py`. The script is the reviewable first implementation step — its table gets sign-off before any 40-cell sweep runs.

## Cost

C_device decomposes into five line items. The three turbine-package items scale with rotor diameter from the Gen5 anchors; the support structure and monitoring are held flat. Scaling exponents from Mattia (2025) Ch. 2.1:

| Line item | Gen5 anchor | Exponent | Formula |
|---|---|---|---|
| Rotors (×3) | $219,000 | D^2.7 | `$219K · (D/5)^2.7` |
| IMA (×3) | $510,000 | D^2.0 | `$510K · (D/5)^2.0` |
| Nacelle/Pylon/Cones (×3) | $424,500 | D^2.0 | `$424.5K · (D/5)^2.0` |
| TriFrame | $187,000 | — | held flat |
| SCADA | $62,000 | — | held flat |

The power-law items extrapolate upward without issue; the C_device column above is computed from these formulas.

**Caveat — TriFrame held flat going up.** Freezing the TriFrame at the Gen5 5 m value across the family is clean shrinking down (smaller rotor on the same-or-lighter support), but it understates structure cost for the larger rotors — an 8 m rotor would in reality need a heavier frame. We accept it by choice. The optimism is bounded: at D = 8 the frozen $187K TriFrame is ~5.5% of a $3.42M device, so it cannot move LCOE much. Flagged here; revisit only if the large-D variants land near a feasibility boundary where 5% matters.

**Caveat — IMA exponent is approximate** (carried over). Mattia's drivetrain cost is torque-driven (T ∝ D²·v_rated³), not pure-D. Collapsing to D^2.0 assumes constant v_rated across the family; our v_rated varies with D, so the D^2.0 IMA cost is approximate. Direction: larger variants have *lower* v_rated, so true torque grows slower than D² and the D^2.0 rule slightly *over*-states their IMA cost (conservative). Acceptable under simple scaling.

## Electrical and installation (reused, unchanged)

The cable-cost and installation methodology from the existing VP pipeline is reused across the family without re-derivation, valid under two held assumptions:

1. **Generation voltage V = 480 V is constant across all seven variants.** Per-TriFrame current I = P_TF / (√3·V·PF) shifts only because P_TF shifts; the ABB cable selector reruns against the same catalog (cheapest three-core 10 kV CSA meeting ≤10% transmission loss, plus Mattia per-meter installation).
2. **TriFrame-of-3 architecture is preserved**, so P_TF = 3·P_rated, keeping the per-TriFrame cable-sizing formula valid.

Installation (jack-up device placement + Mattia per-meter cable laying) flows through unchanged: N TriFrames and total cable length L_total are already explicit parameters. TriFrame assembled mass is a per-variant device-spec input feeding the crane-capacity rule; the larger variants need a mass figure (resolved with the speed derivation, or held at the Gen5-rule scaling — to confirm).

## Experiment grid

Each variant runs the existing 40-cell template, both scopes:

- **Scope:** new_england_new_york, pooled (2)
- **MW target:** 1, 5, 25, 100 (4)
- **LCOE target:** 600, 700, …, 1500 — a 10-point frontier emitted by one solve

= 4 MW × 10 LCOE = **40-point frontier per variant per scope**. Seven variants × two scopes = 56 pipeline runs. The driver is `run_turbine_modification.sh` with `VARIANTS=(gen5 modvp4 modvp3 modvp2 modvp6 modvp7 modvp8)`.

Per-cell metric is **CV** (coefficient of variation), with energy, pool size, and floor as support — consistent with the rest of the portfolio work. Gen5 is the reference each variant is read against.

## Covariance — no shortcut

The old `Σ^D = (A_D/A_5)²·Σ^5` area-scaling trick (see `optimization/vp/methodology/diameter_scaling_note.md`) is **only exact when v_rated is D-independent**. We vary v_rated with D, so the power-curve shape (rated and cut-in points) shifts per variant and the trick is invalid. Each variant gets a full `compute_covariance.m` build, as the existing per-cell `covariance.nc` files already do. No operational change; noted so nobody reaches for the shortcut.

## Results layout and archiving

Outputs follow the scope-level convention to `results/vp/turbine_modification/<variant>/groups/<scope>/<MW>mw/`. The existing `gen5`/`modvp2`/`modvp3`/`modvp4` trees there are from the superseded shrink-only design with the old v_rated numbers, so they are **stale and must not be mixed** with the new run. Before the sweep: archive the current `results/vp/turbine_modification/` (e.g. to `…/_archive_shrink_only/`), then run the full seven-variant ladder fresh. Decision to confirm before running.

## Acknowledged design choices

1. **Uniform full-eligible-set v_rated rule.** Chosen for method consistency across a family that now spans D = 2–8. It replaces the old incremental-shallow-band justification and flattens the small-variant spread the old design engineered. Accepted: a single reproducible rule across the whole ladder is worth more than the hand-tuned shallow-band signal.
2. **TriFrame/SCADA held flat** (see cost caveat) — optimism for large D, bounded to ~5% of device cost at D = 8.
3. **p99.5 percentile** for v_rated, carried over: for the D = 5 baseline it reproduces Verdant's published P_rated to within 4%, the unique percentile among {p50…p99.9} that does so.

## Open items before implementation

- [ ] Confirm `derive_variants.py` I/O against actual `harmonics.nc` / `candidates.nc` field names.
- [ ] Decide large-variant TriFrame **mass** input (for the crane/installation rule).
- [ ] Confirm archive-then-rerun of the stale `results/vp/turbine_modification/` tree.
