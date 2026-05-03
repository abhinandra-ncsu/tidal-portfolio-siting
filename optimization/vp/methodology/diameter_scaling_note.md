# Diameter scaling for the VP TriFrame variance experiment

**Context.** A side experiment swept the VP TriFrame rotor diameter `D ∈ {3, 4, 5, 6} m` to test whether portfolio composition is sensitive to rotor size. The code (`optimization/diameter_experiment/`) and partial outputs (`results/diameter_experiment/`) were removed 2026-04-26; the experiment can be rebuilt cheaply if needed. This note records the one piece of the setup that is not obvious from the rest of the pipeline.

## The shortcut

The per-turbine covariance `Σ^5` is computed once, at the baseline `D = 5 m`. For any other `D`,

    Σ^D = (A_D / A_5)² · Σ^5,    A_D = π (D/2)²

This follows from `P_turbine(t) = ½ ρ A C_p V(t)³`: at a fixed velocity time series and fixed `C_p`, `V_rated`, power is linear in `A`, so its covariance scales by `A²`.

**Saves:** one full re-run of `compute_covariance.m` per diameter. The covariance build is the expensive step.

## What the shortcut does not save

Each `D` still requires a fresh optimization solve, because the feasible set and the target count both depend on `D`:

1. **Depth mask changes with D.** Mounting rule is `depth ≥ 2D`; the candidate set shrinks as `D` grows.
2. **Triframe count changes with D.** `N_D = ⌈P_target / P_triframe(D)⌉` for the 5.25 MW target.

The argmin of `xᵀ Σ^D x` over the feasible binary set is therefore not invariant in `D`. The scaling trick is for `Σ`, not for the MIP.

## Assumptions the scaling depends on

- `V_rated` and `C_p` are `D`-independent. If either varies with rotor size, the `A²` scaling is approximate.
- Velocity time series at each candidate site is `D`-independent — no induction or wake correction tied to rotor size.

## To regenerate

Reuse the baseline `candidates.nc` and `covariance.nc` from `optimization/05_optimize.py`'s outputs as the shared `Σ^5` source. For each `D`: apply `depth ≥ 2D`, scale `Σ` by `(A_D/A_5)²`, recompute `N_D` and `P_triframe(D)`, re-solve the same min-variance MIP. Sweep `cf_target` between the unconstrained min-variance CF and the top-`N_D`-by-CF mean to trace a Pareto frontier.
