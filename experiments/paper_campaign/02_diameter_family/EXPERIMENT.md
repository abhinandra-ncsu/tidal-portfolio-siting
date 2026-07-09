# Campaign 02 — turbine modification: diameter family

**Configuration:** Modified-Verdant variants at D = 2, 3, 4, 6, 7, 8 m, pooled
East Coast scope, 6.6 kV step-up, LCOE caps $600–$1,500 × {1, 5, 25, 100} MW.
The D = 5 (Gen5) row comes from `../01_baseline` — same configuration, not
re-run here.

## Question

§3 turbine-modification (diameter axis): does any rotor size beat the Gen5
baseline on the variance–LCOE frontier, in either direction — smaller rotors
(shallower, faster incremental sites) or larger rotors (more swept area on the
deep pool)?

## Variant specification

The D < 5 arm is the locked spec from
`experiments/turbine_modification/EXPERIMENT.md` (unchanged). The D > 5 arm
was added 2026-06-10 for this campaign:

| Variant | D (m) | A (m²) | v_rated | v_cut_in | P/turbine (kW) | C_device | Depth filter |
|---|---|---|---|---|---|---|---|
| modvp6 | 6 | 28.27 | 1.99 | 0.60 | 42.3 | $1,953,000 | ≥ 12 m |
| modvp7 | 7 | 38.48 | 1.94 | 0.58 | 53.3 | $2,623,800 | ≥ 14 m |
| modvp8 | 8 | 50.27 | 1.89 | 0.57 | 64.4 | $3,420,400 | ≥ 16 m |

**v_rated rule for D > 5.** The incremental shallow band [2D, 10) m is
undefined for D > 5 (a larger rotor loses shallow sites rather than unlocking
them), so the upward arm uses the same rule as the Gen5 baseline itself:
v_rated = p99.5 of per-site U_max on the variant's own eligible set
(depth ≥ 2D), computed from `experiments/turbine_modification/diagnosis/`
data. The derivation script's eligible-set branch for D ≥ 5 already encodes
this. Result: v_rated *falls* with D (2.03 → 1.99 → 1.94 → 1.89) because
deeper sites have slower upper-tail currents. v_cut_in = 0.30·v_rated and
P_rated = ½ρACp·v_rated³ as for the rest of the family (Cp = 0.37, ρ = 1025).

**C_device** scales the three turbine-package lines from the Gen5 anchors
exactly as the locked spec does for D < 5: rotors $219K·(D/5)^2.7,
IMA $510K·(D/5)^2.0, NPC $424.5K·(D/5)^2.0; TriFrame ($187K) and SCADA ($62K)
held. The locked spec's caveats on these exponents apply symmetrically to the
upward extrapolation.

## Acknowledged limitations

1. **Installation/crane rule is Gen5-anchored.** TriFrame assembled mass per
   variant was never sourced, so the jack-up crane sizing uses Gen5's mass for
   the whole family — this under-charges installation for D > 5 (heavier
   frames) and over-charges D < 5. Direction-only flag, same status as the
   locked spec.
2. **Step-up transformer cost auto-scales** with P_TriFrame through the Collin
   (2017) curve (exponent 0.63 + $51K fixed term), so smaller variants pay
   proportionally more per kW and larger variants less. This is a consequence
   of holding the electrical architecture fixed family-wide, stated in §2.

## Layout

```
results/<variant>/
  harmonics.nc histograms.nc candidates.nc covariance.nc build.log
  {1,5,25,100}mw/optimization_results.nc + optimize.log
results/run_summary.txt
```

## Reproduction

```bash
./run.sh            # all six variants
./run.sh modvp6     # single variant
```
