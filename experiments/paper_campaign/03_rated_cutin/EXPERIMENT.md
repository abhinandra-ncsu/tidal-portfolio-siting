# Campaign 03 — turbine modification: rated × cut-in sweep

**Configuration:** Gen5 geometry (D = 5 m, A = 19.63 m²), pooled East Coast,
6.6 kV step-up, LCOE caps $600–$1,500 × {1, 5, 25, 100} MW.

## Question

§3 turbine-modification (power-curve axis): is the frontier sensitive to the
two power-curve design conventions — v_rated = p99.5 of per-site U_max (2.03)
and v_cut_in = 0.30·v_rated (0.61)? The grid brackets both: v_rated down to
the energy-bulk argument's optimum (~1.5–1.75) and up past Lewis's published
2.59 extrapolation (2.30, 2.60); v_cut_in at 0.40 / 0.61 / 0.80.

## Grid

v_rated {2.03, 1.75, 1.50, 2.30, 2.60} × v_cut_in {0.61, 0.40, 0.80} = 15
curves, reference curve first. P_rated tracks v_rated by the cubic law (rotor
geometry and per-device cost held); fleet size N follows from each capacity
target.

This re-runs the design of `experiments/archive/rated_cutin_sweep/` (NE+NY,
2026-05-31) at the campaign's pooled scope and as part of the single
campaign configuration.

## Structure

Steps 1–2 are power-curve-independent: copied once from
`../01_baseline/results` (same variant, same scope). Per curve: step 3
(screen) + step 4 (covariance). Per (curve, capacity): step 5.

## Layout

```
results/
  harmonics.nc histograms.nc          (copied from 01_baseline)
  vr<rated>_vci<cutin>/
    candidates.nc covariance.nc build.log
    {1,5,25,100}mw/optimization_results.nc + optimize.log
  run_summary.txt
```

## Reproduction

```bash
../01_baseline/run.sh   # prerequisite (resource tier)
./run.sh
```
