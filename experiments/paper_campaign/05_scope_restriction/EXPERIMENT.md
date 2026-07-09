# Campaign 05 — scope restriction (NE+NY vs pooled)

**Configuration:** identical to `../01_baseline` except scope: candidate pool
restricted to NE+NY (ME, NH, MA, RI, CT, NY coastlines).

## Question

Supplementary: what does restricting the candidate pool to the NE+NY region
cost relative to the pooled East Coast baseline, per scale? Under the old
spec at 480 V the answer was nothing at pilot scale (variance ratio 1.00–1.06
at 1–5 MW) and a lot at 100 MW (1.54–1.81, +$100/MWh on the LCOE floor).
This re-measures the restriction cost under the campaign configuration
(6.6 kV), where step-up's pool expansion could move it in either direction.

## Layout

```
results/
  harmonics.nc histograms.nc candidates.nc covariance.nc build.log
  {1,5,25,100}mw/optimization_results.nc + optimize.log
  run_summary.txt
```

## Reproduction

```bash
./run.sh
```
No dependencies (own scope, steps 1–4 fresh). Compare against
`../01_baseline/results/<MW>mw/` at matched LCOE caps.
