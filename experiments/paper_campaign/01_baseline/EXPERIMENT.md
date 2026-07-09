# Campaign 01 — baseline portfolios across deployment scales

**Configuration:** VP Gen5 (D = 5 m, v_rated 2.03, v_cut_in 0.61, 31.2 kW/turbine),
pooled East Coast scope, 6.6 kV per-TriFrame step-up transmission,
LCOE caps $600–$1,500/MWh in $100 steps, targets {1, 5, 25, 100} MW.

## Question

The paper's core result (§3.1–3.3): the candidate pool after eligibility
screening, the variance–LCOE efficient frontier at each deployment scale, and
the portfolio composition along both axes (LCOE cap, scale).

## Structure

- Steps 1–4 run fresh once at `results/` (eligibility pool and covariance are
  capacity-independent; voltage does not enter until step 5).
- Step 5 runs once per MW target into `results/<MW>mw/`.

## Layout

```
results/
  harmonics.nc histograms.nc candidates.nc covariance.nc build.log
  {1,5,25,100}mw/optimization_results.nc + optimize.log + figures
  run_summary.txt
```

## Reproduction

```bash
./run.sh          # full
./run.sh smoke    # steps 1-4 + the 1 MW cell only
```

## Downstream dependencies

- `03_rated_cutin` reads `results/harmonics.nc` + `results/histograms.nc`
  (resource tier, power-curve-independent).
- `04_voltage_justification` reads `results/candidates.nc` +
  `results/covariance.nc` (curve tier, voltage-independent).

Run this experiment first.
