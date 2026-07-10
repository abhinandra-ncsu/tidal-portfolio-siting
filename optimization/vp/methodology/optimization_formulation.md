# Tidal Energy Portfolio Optimization — Mathematical Formulation

## Problem Statement

Given a set of candidate tidal energy sites along the US East Coast, select where to deploy a fixed number of Verdant Power Gen5 TriFrame units to minimize the temporal variability of aggregate power generation, subject to a portfolio-level LCOE ceiling.

Each TriFrame is deployed at a single ROMS mesh point and transmits to shore on its own radial cable via a per-TriFrame step-up to 6.6 kV — no offshore collection points or shared export cable. See `turbine_design_specification.md` for TriFrame parameters and `cost/capex/electrical/methodology.md` for the step-up and cable design.

---

## Sets and Indices

| Symbol | Definition |
|--------|-----------|
| I | Set of candidate sites (pre-screened by minimum depth requirement) |
| i, j | Site indices, i, j ∈ I |
| T | Set of timesteps for reconstructed power timeseries |
| t | Timestep index, t ∈ T |

---

## Decision Variable

$$x_i \in \{0, 1\} \quad \forall \, i \in I$$

x_i = 1 if a TriFrame is deployed at site i, 0 otherwise.

---

## Objective Function

Minimize portfolio variance of power generation:

$$\min \sum_{i \in I} \sum_{j \in I} x_i \, x_j \, \Sigma_{ij}$$

Or equivalently: **min x^T Σ x**

where Σ_ij = Cov(P_i(t), P_j(t)) is the temporal covariance of power output between sites i and j, computed over the reconstructed timeseries.

**Intuition:** Select sites whose power generation patterns are temporally uncorrelated — when one site is at slack tide, another is at peak flow — reducing aggregate variability.

---

## Constraints

### 1. Fixed Deployment Size

$$\sum_{i \in I} x_i = N$$

where:

```
N = ceil(P_target / P_TriFrame)
```

P_TriFrame = 93.6 kW (see `turbine_design_specification.md`).

| P_target | N (TriFrames) |
|----------|---------------|
| 1 MW     | 11            |
| 5 MW     | 54            |
| 25 MW    | 268           |
| 100 MW   | 1069          |

### 2. Portfolio LCOE Ceiling

$$C_{\text{const}}(N) + \sum_{i \in I} x_i \left( c_{\text{site},i} - L \cdot E_i \right) \leq 0$$

This is the linearized form of the ratio constraint:

$$\frac{C_{\text{const}}(N) + \sum_i x_i \cdot c_{\text{site},i}}{\sum_i x_i \cdot E_i} \leq L$$

where:
- C_const(N) = annualized project-level constant cost (depends only on N, not on site selection). See `cost/optimization_cost_structure.md`.
- c_site_i = annualized portfolio-dependent cost at site i ($/yr) — includes cable purchase, cable installation, and cascading percentage-based costs (contingency, environmental compliance, insurance), all functions of shore distance d_i. See `cost/optimization_cost_structure.md`.
- E_i = annual energy delivered at site i (MWh/yr). See `energy/methodology.md`.
- L = LCOE target ($/MWh)

The linearization is valid because multiplying both sides by the (positive) energy denominator converts the ratio into a linear inequality in x_i. C_const(N) is a constant in the optimization — it does not affect which sites are selected, only whether a given LCOE target is feasible. c_site_i is precomputed per site before the optimization runs.

---

## Problem Class

Binary Quadratic Program (BQP):
- Binary decision variables
- Quadratic objective (x^T Σ x)
- Linear constraints

Solver: Gurobi via Pyomo.

---

## Optimizer Inputs

| Input | Symbol | Defined in |
|-------|--------|-----------|
| Covariance matrix | Σ_ij | See Covariance Matrix section below |
| Annual energy delivered | E_i (MWh/yr) | `energy/methodology.md` |
| Annualized site cost | c_site_i ($/yr) | `cost/optimization_cost_structure.md` |
| Annualized project-level constant cost | C_const(N) | `cost/optimization_cost_structure.md` |
| Number of TriFrames | N | Derived from P_target / P_TriFrame |
| LCOE target | L ($/MWh) | User-specified |

Site-specific data (per candidate site i ∈ I):

| Data | Source |
|------|--------|
| Latitude, Longitude, Depth | Phase 3 pipeline output |
| Shore distance | Phase 3 pipeline output |
| Tidal harmonic constituents | Phase 1 pipeline: `harmonics_east_coast.nc` |

---

## Covariance Matrix Computation

For each candidate site i ∈ I:

**Step 1 — Reconstruct current speed timeseries.** Use T_TIDE's `t_predic` (Pawlowicz et al. 2002) to reconstruct tidal current velocity from harmonic ellipse parameters (semi-major, semi-minor, inclination, phase) and constituent frequencies. `t_predic` returns complex velocity; current speed is S_i(t) = |v_pred|.

**Step 2 — Apply power curve.** Convert speed timeseries to power timeseries using the turbine power curve (see `turbine_design_specification.md`).

**Step 3 — Compute covariance matrix:**

```
Σ_ij = (1/|T|) Σ_t P_i(t) P_j(t)  −  [(1/|T|) Σ_t P_i(t)] [(1/|T|) Σ_t P_j(t)]
```

### Pre-screening

Candidate sites are pre-screened by minimum depth requirement before covariance computation to manage computational cost. The resulting covariance matrix is |I| × |I| and must fit in memory.

---

## Summary

```
    min   x^T Σ x
    s.t.  Σ_i x_i = N                                          (deploy N TriFrames)
          C_const(N) + Σ_i x_i (c_site_i - L · E_i) ≤ 0       (LCOE ≤ target)
          x_i ∈ {0, 1}                                          (binary site selection)
```

**Inputs:**
- Σ — covariance matrix of power generation (|I| × |I|)
- C_const(N) — annualized project-level constant cost (scalar)
- c_site_i — annualized portfolio-dependent cost at site i
- E_i — annual energy delivered at site i
- N — number of TriFrames to deploy
- L — LCOE target ($/MWh)

**Output:** Set of sites S = {i : x_i = 1} that minimizes aggregate power variability while meeting cost and capacity targets.

---

## References

- Verdant Power Gen5 KHPS — FERC P-12611, DOE MHKDR Submission 318.
- Neary, V.S. et al. (2014). SAND2014-9040 — Methodology for Design & Economic Analysis of MEC Technologies. Sandia National Laboratories.
