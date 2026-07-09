# Scope × scale × device experiment — design

Cross-device, cross-scope, cross-scale grid. Each cell is one step-5 optimization that sweeps 7 LCOE caps.

## Grid

| | scope | scales (MW) |
|---|---|---|
| VP Gen5 TriFrame (105 kW) | pooled, NE+NY | 5, 25, 50, 100, 250 |
| ORPC TidGen 2.0 (500 kW) | pooled, NE+NY | 25, 50, 100, 250 |

ORPC at 5 MW (= 10 devices) was dropped — 10-device portfolio is not a meaningful diversification problem.

**Cells:** 10 VP + 8 ORPC = **18 step-5 invocations**.

## LCOE caps

Fixed grid: **$500, $700, $1000, $1200, $1500, $2000, $2500** ($/MWh).

Same grid in every cell. Cells where a cap is below the cell's feasibility floor return `status="infeasible"` — expected, not an error.

## Scope sources

Steps 1–4 (`harmonics.nc`, `candidates.nc`, `covariance.nc`, `histograms.nc`) are scale-independent within a scope. Each cell directory contains symlinks to the canonical scope's upstream files:

- VP pooled → `results/vp/groups/pooled/`
- VP NE+NY → `results/vp/groups/new_england/` (the `new_england` group includes NY)
- ORPC pooled → `results/orpc/groups/pooled/`
- ORPC NE+NY → `results/orpc/groups/new_england_ny/`

## Layout

```
experiments/scope_x_scale/
├── EXPERIMENT.md          (this file)
├── run_all.sh             (orchestrator, 18 serial cells)
├── results/
│   ├── vp/{pooled,new_england_ny}_{5,25,50,100,250}mw/
│   └── orpc/{pooled,new_england_ny}_{25,50,100,250}mw/
└── logs/                  (per-cell step-5 stdout/stderr)
```

Each cell directory: 4 symlinks in + 1 `optimization_results.nc` out.

## What each axis answers

- **Device axis (VP vs ORPC):** does the depth-window / device-kW asymmetry matter at every scale, or only at some?
- **Scope axis (pooled vs NE+NY):** does pooling buy anything beyond NE+NY, and where does that gap open up?
- **Scale axis (5 → 250 MW):** at what point does each device's geographic / phase strategy saturate?
- **LCOE axis (within each cell):** the variance-cost frontier for that cell.

## What this experiment is NOT designed to answer

(Out of scope per 2026-05-14 design session.)

- Mixed-device (per-site VP or ORPC) portfolios.
- Demand-weighted or CVaR objectives.
- Temporal / out-of-sample robustness.
- Rotor-diameter or device-internal-parameter sensitivity (covered by `experiments/rotor_resizing/`).
- ORPC at 5 MW.

## Reproduction

```bash
./run_all.sh           # all 18 cells, serial
./run_all.sh 0         # only cell index 0 (VP pooled 5 MW — smoke test)
```

Each cell sets `TIDAL_RESULTS_DIR`, `TIDAL_P_TARGET_MW`, `TIDAL_LCOE_TARGETS` and invokes `optimization/{vp,orpc}/05_optimize.py`. Per-cell log at `logs/<device>_<scope>_<mw>mw.log`.
