# Campaign 04 — voltage justification arm (480 V)

**Configuration:** identical to `../01_baseline` except transmission: 480 V
direct cable per TriFrame (no step-up transformer), i.e. Verdant's as-built
RITE configuration.

## Question

Supplementary evidence for the §2 design statement: per-TriFrame 6.6 kV
step-up is the modeled design because the as-built 480 V configuration does
not scale beyond pilot deployments. The 01-vs-04 comparison quantifies it at
matched LCOE caps: feasible-pool size, LCOE floor, variance, and delivered
energy per scale.

## Structure

Voltage enters the pipeline at step 5 only (cable re-selection and the
transformer CapEx term live in the optimizer), so this arm reads steps 1–4
from `../01_baseline/results` and re-runs only step 5 per MW target —
the same reuse pattern the original `transmission_stepup` experiment used,
inverted (the campaign baseline is now 6.6 kV; the comparison arm is 480 V).

## Layout

```
results/{1,5,25,100}mw/optimization_results.nc + optimize.log
results/run_summary.txt
```

## Reproduction

```bash
../01_baseline/run.sh   # prerequisite (steps 1-4)
./run.sh
```
