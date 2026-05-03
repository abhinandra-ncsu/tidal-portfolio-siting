# ORPC TidGen 2.0 Portfolio Optimization — Mathematical Formulation

## Problem Statement

Pick where to deploy `N` ORPC TidGen 2.0 devices along the US East Coast so that the *aggregate* hourly power timeseries has the smallest possible variance, subject to a portfolio-level levelized-cost-of-energy (LCOE) ceiling.

Each candidate site holds at most one device, and that device runs a dedicated DC subsea cable directly to shore — no array cables, no shared offshore substation. See `turbine_design_specification.md` for device parameters and `cost/capex/electrical/methodology.md` for the cable design.

Implementation: `optimization/orpc/05_optimize.py`.

---

## Sets and Indices

| Symbol | Definition |
|--------|-----------|
| I | Candidate sites surviving the depth window (18–40 m), state bbox, and CF threshold (CF > 0.05) |
| i, j | Site indices, i, j ∈ I |
| T | Hourly timesteps for the year-2013 reconstruction (|T| = 8760) |
| t | Timestep index, t ∈ T |

I is the index set written into `candidates.nc` by `03_screen_candidates.py`. The covariance matrix Σ is built over the same set in `compute_covariance.m`.

---

## Decision Variable

$$x_i \in \{0, 1\} \quad \forall \, i \in I$$

x_i = 1 if a TidGen 2.0 device is deployed at site i, else 0. Exactly one device per selected site.

---

## Objective Function

$$\min \; x^{\top} \Sigma x \;=\; \min \sum_{i,j \in I} x_i \, x_j \, \Sigma_{ij}$$

where Σ_ij is the covariance of the per-device power timeseries at sites i and j over the year-long reconstruction.

- Diagonal Σ_ii is the per-site power variance.
- Off-diagonal Σ_ij is the cross-site covariance — the diversification term that lets a portfolio of two anti-correlated sites have a smaller aggregate variance than either site alone.

Σ is computed once (`compute_covariance.m`) and reused across all LCOE targets.

---

## Constraints

### 1. Fixed Deployment Size

$$\sum_{i \in I} x_i \;=\; N$$

with

```
N = ceil(P_TARGET_MW * 1000 / P_DEVICE_KW)
```

For the configured `P_TARGET_MW = 50 MW` and `P_DEVICE_KW = 500`, **N = 100 devices**.

### 2. Portfolio LCOE Ceiling

$$C_{\text{const}}(N) \;+\; \sum_{i \in I} x_i \, ( c_{\text{site},i} \,-\, L \cdot E_i ) \;\leq\; 0$$

This is the linearized form of the ratio constraint:

$$\frac{C_{\text{const}}(N) + \sum_i x_i \cdot c_{\text{site},i}}{\sum_i x_i \cdot E_i} \;\leq\; L$$

Multiplying both sides by the strictly positive energy denominator (guaranteed positive by constraint 1 with N ≥ 1) gives the linear inequality above.

| Term | Definition | Source |
|------|-----------|--------|
| C_const(N) | Annualized cost depending only on N, not on site selection | `cost/optimization_cost_structure.md` |
| c_site_i | Annualized cost at site i ($/yr); function of shore distance only | `cost/optimization_cost_structure.md` |
| E_i | Annual energy delivered at site i (MWh/yr) | `energy/methodology.md` |
| L | LCOE target ($/MWh) | swept over `LCOE_TARGETS` in `config/config.py` |

C_const(N), c_site_i, and E_i are all precomputed before the BQP is constructed, so the LCOE constraint is fully linear in x.

---

## Problem Class and Solver

Binary Quadratic Program:

- Binary decision variables
- Quadratic objective `x^T Σ x`
- Linear constraints

Solver: Gurobi via `gurobipy` (`solve_bqp` in `05_optimize.py`). Time limit and MIP gap come from `GUROBI_TIME_LIMIT` and `GUROBI_MIP_GAP` in config.

Numerical note: Σ is rescaled by 1e-6 before being passed to Gurobi (W² → kW²) to keep the quadratic coefficients in a sane range. The rescaling is a positive scalar on the objective, so it does not change the argmin; reported variance is converted back to W² for output.

---

## Pre-solve Reduction

Before constructing the BQP for a given LCOE target L, sites with non-negative LCOE margin are dropped:

```python
margins = c_site - L * E
keep_idx = np.where(margins < 0)[0]
```

A site with `c_site_i - L · E_i ≥ 0` can never improve feasibility — selecting it never relaxes the LCOE constraint, only tightens it. Dropping these sites shrinks Σ from |I|×|I| to a smaller dense block over `keep_idx`. This is what makes the BQP fit in memory at |I| of a few thousand sites; without it the dense quadratic form would be too large.

The reduced solution is mapped back to the global site index after the solve.

If fewer than N sites have negative margin at a given L, or if the best-N margins still cannot satisfy `C_const(N) + Σ best_n ≤ 0`, the target is reported infeasible and skipped.

---

## Configuration Sweep

The pipeline solves the BQP for each L ∈ `LCOE_TARGETS = [700, 800, 900, ..., 1500]` $/MWh (configured in `config/config.py`). For each target, the result records:

- Selected sites (indicator vector x)
- Achieved LCOE (the binding value of the cost ratio)
- Portfolio variance `x^T Σ x` (in W²)
- Solver status

Output: `results/orpc/<group>/optimization_results.nc`.

---

## Summary

```
    min   x^T Σ x
    s.t.  Σ_i x_i = N                                          (deploy N devices)
          C_const(N) + Σ_i x_i (c_site_i - L · E_i) ≤ 0       (LCOE ≤ target)
          x_i ∈ {0, 1}                                          (binary site selection)
```

Solver: Gurobi BQP with per-target reduction to feasible-margin sites only.

---

## References

- Marnagh, C. & McEntee, J. (2018). DOE MHKDR submissions 269 and 273. Award DE-EE0007820.
- Pawlowicz, R., Beardsley, B., Lentz, S. (2002). Classical tidal harmonic analysis with errors in MATLAB using T_TIDE. *Computers & Geosciences*, 28(8), 929–937.
