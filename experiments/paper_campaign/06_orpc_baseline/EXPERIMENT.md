# Campaign 06 — ORPC TidGen 2.0 baseline across deployment scales

**Configuration:** ORPC TidGen 2.0 (500 kW/device, SCM power curve, depth
18–40 m), pooled East Coast scope, LCOE caps $600–$1,500/MWh in $100 steps,
targets {5, 10, 25, 100} MW. Two transmission arms: 6.6 kV per-device step-up
(baseline) and 480 V direct (no step-up) comparison.

## Question

The ORPC counterpart to the VP §3 baseline (01_baseline): the candidate pool
after eligibility screening, the variance–LCOE efficient frontier at each
deployment scale, and how the 6.6 kV step-up vs 480 V transmission choice moves
the frontier. Drives the UMERC poster's ORPC panel.

## Structure

- Steps 1–4 run fresh once into `results/shared/`. The eligibility pool and
  covariance are capacity-independent, and voltage (`TIDAL_STEPUP_KV`) does not
  enter until step 5 — it only touches transformer cost and cable selection in
  `config.py` / `05_optimize.py`.
- Step 5 runs once per (voltage arm × MW target) into `results/<arm>/<mw>mw/`.
  The ORPC pipeline resolves every file off a single `TIDAL_RESULTS_DIR` (no
  RESOURCE/CURVE input-dir split like VP), so each cell is seeded with a copy
  of `candidates.nc` + `covariance.nc` before optimizing.

## Layout

```
results/
  shared/  harmonics.nc histograms.nc candidates.nc covariance.nc build.log
  6600v/{5,10,25,100}mw/  optimization_results.nc + optimize.log + figures + (staged candidates/covariance)
  480v/{5,10,25,100}mw/   optimization_results.nc + optimize.log + figures + (staged candidates/covariance)
  run_summary.txt
```

## Reproduction

```bash
./run.sh          # full: steps 1-4 + both arms x {5,10,25,100} MW
./run.sh smoke    # steps 1-4 + the 5 MW cell in both arms only
```
