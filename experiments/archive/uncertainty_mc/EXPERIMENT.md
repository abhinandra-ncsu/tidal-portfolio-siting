# Uncertainty Monte Carlo — experiment design
Propagate harmonic-constant uncertainty through the deterministic two-device MVP pipeline via Monte Carlo perturbation of ROMS harmonics. Used to support the INFORMS 2026 talk "Tidal Energy Portfolios on the U.S. East Coast: A Technoeconomic Assessment Under Resource Uncertainty" (Anderson de Queiroz's session).

**Date design locked:** 2026-05-19 **Status:** methodology design complete; implementation pending **Scope discipline:** v1 only — Layer 2 (CVaR MILP) deferred until v1 gates pass

* * *
## Question
Under per-constituent amplitude and phase uncertainty in the ROMS-derived tidal harmonics, (i) where does the deterministic efficient frontier sit inside the distribution of perturbed frontiers, (ii) which siting decisions are robust to harmonic uncertainty versus contingent on model fidelity, and (iii) how do amplitude and phase uncertainty separately shape portfolio composition through the covariance matrix?
## Why this experiment exists
Anderson invited the deterministic MVP work into his INFORMS session on "Energy Systems Optimization Under Uncertainty." The deterministic frontier treats Σ as exactly known when it is in fact a point estimate from a tidal model with finite fidelity. This experiment makes the resource-side uncertainty explicit, propagates it through the existing pipeline, and characterizes the distribution of portfolio outcomes that the deterministic single-point answer hides.

The INFORMS abstract (`writing/informs-2026/abstract.md`) commits to the methodology — not to any specific finding. This experiment must produce defensible frontier-cloud and site-frequency results by the talk; it does _not_ need to produce a particular verdict.
## Methodology decisions (locked 2026-05-19)
| #   | Decision | Choice |
| --- | --- | --- |
| 1   | Candidate pool | **Fixed** from the deterministic run for the chosen device/scope. MC does NOT re-screen via the 1.65 M-point histograms step. |
| 2   | Perturbation target | Per-constituent **amplitude (CMAJ)** and **phase (CPHA)** only. CMIN and CINC held at deterministic values. |
| 3   | Noise model | **Amplitude: multiplicative**, `a' = a × (1 + ε_a)`, `ε_a ~ N(0, σ_a²)`. **Phase: additive**, `φ' = φ + ε_φ`, `ε_φ ~ N(0, σ_φ²)` in degrees. |
| 4   | Noise structure | **i.i.d. per (site, constituent)**. No spatial correlation, no constituent correlation in v1. |
| 5   | What MC refreshes per sample | Both per-site **capacity factor** (drives LCOE constraint) and cross-site **Σ** (drives variance objective). Confirmed via `optimization/vp/05_optimize.py:234` that CF is read from `candidates.nc`. |
| 6   | LCOE cap sweep per sample | **Full sweep** — the same LCOE caps the deterministic run uses, so each sample produces a full frontier. |
| 7   | Per-sample artifact retention | **Keep all sample directories** (debuggable end-to-end; storage cost accepted). |
| 8   | Architecture | Option A: **MATLAB stays in the loop, driven from Python.** New MATLAB script in this experiment folder (mirror of `compute_covariance.m` extended with CF output); existing `optimization/{vp,orpc}/` untouched. |
| 9   | Optimization formulation | **Markowitz only in v1** (existing `05_optimize.py` invoked unchanged via env var). CVaR-MILP (Layer 2) deferred to v2. |
| 10  | Device / scope / target for v1 | **VP, NE+NY, 50 MW.** Matches an existing deterministic run with locked candidate pool. |
| 11  | σ-grid for v1 | σ_a ∈ {0, 5%, 10%} × σ_φ ∈ {0°, 5°, 10°} = **9 cells**; N = 20 samples per cell. |
## Verification gates (must pass before full sweep)
Before any analysis figures, the MC driver must pass these four checks. Code is done when all four pass.

1. **Zero-noise round-trip.** Running with σ_a = 0, σ_φ = 0, one sample, produces a per-sample `covariance.nc` and `candidates.nc` whose contents match the deterministic outputs to numerical tolerance (covariance within 1e-9 relative; CF within 1e-6 absolute). _Verifies the harness adds no bias._
  
2. **Determinism under seed.** Two runs with the same seed produce bit-identical per-sample outputs across all 9 σ-cells, single sample each. _Verifies reproducibility._
  
3. **Monotonic noise propagation.** Holding σ_a fixed at 0, increasing σ_φ from 5° → 10° produces strictly larger frontier-cloud width (measured as standard deviation of frontier-LCOE at fixed variance level). Same check with σ_a varying, σ_φ = 0. _Verifies perturbation reaches the output and the metric responds._
  
4. **End-to-end dry-run at N = 20, one cell.** σ_a = 10%, σ_φ = 10°, the full pipeline (perturb → MATLAB → optimize → summarize) runs through and produces (i) frontier cloud plot, (ii) site-inclusion frequency table, (iii) realized-CVaR of the deterministic-optimal portfolio under the 20 perturbed worlds. _Verifies the analysis layer._
  

If any gate fails, fix before the full 180-sample sweep.
## What v1 is NOT designed to answer
(Explicitly out of scope.)

- **CVaR-MILP (Layer 2).** Reformulation of the optimization to maximize CVaR under perturbed scenarios. Deferred to v2 after v1 gates pass.
  
- **ORPC device.** v1 is VP-only; ORPC sweep deferred to v2 once VP results are validated.
  
- **Scopes other than NE+NY.** Pooled and other state scopes deferred to v2.
  
- **Spatially-correlated noise.** Sub-grid coherence of ROMS error not modeled; i.i.d. is the v1 default.
  
- **Constituent-correlated noise.** Errors in M2 and N2 are physically related (both lunar semi-diurnal); not modeled in v1.
  
- **Noise calibration from validation data.** No ROMS-vs-NOAA validation numbers in hand. σ_a and σ_φ are treated as _sensitivity axes_, not calibrated point values.
  
- **Re-screening of candidate pool under uncertainty.** Candidate pool is fixed; under heavy noise some sites might newly pass/fail the CF floor — not modeled.
  
- **CMIN / CINC perturbation.** Minor-axis and inclination held fixed; second-order effect.
  
- **Cost-side uncertainty.** CapEx exponents, OpEx, FCR all held at deterministic values; this experiment is resource-uncertainty-only.
  
## Layout
```
experiments/uncertainty_mc/
├── EXPERIMENT.md             (this file)
├── src/
│   ├── perturb.py            (noise sampler; writes perturbed harmonics.nc per sample)
│   ├── mc_reconstruct.m      (mirrors compute_covariance.m; adds per-site annual-energy output)
│   ├── mc_driver.py          (the loop: σ-cells × samples; tmux-safe single process)
│   └── analyze.py            (frontier cloud + site-frequency + realized-CVaR from summaries)
├── config/
│   └── mc_v1.py              (N=20, σ-grid, device=VP, scope=NE+NY, target=50 MW, seed)
├── results/
│   └── {device}_{scope}_{target}/
│       └── sigma_a={..}_sigma_phi={..}/
│           ├── sample_{k:04d}/
│           │   ├── harmonics_perturbed.nc
│           │   ├── candidates.nc           (updated CFs)
│           │   ├── covariance.nc           (updated Σ)
│           │   └── frontier.nc             (from 05_optimize.py)
│           └── summary.parquet              (per-sample scalars aggregated)
└── logs/                                    (per-sample stdout/stderr)
```
## Dependencies on existing pipeline (surgical — no modifications)
| File | Treatment |
|---|---|
| `optimization/vp/01_extract_harmonics.py` | Unchanged. Deterministic `harmonics.nc` is read once by `mc_driver.py`. |
| `optimization/vp/build_histograms.m` | Unchanged. Not invoked in MC loop. |
| `optimization/vp/03_screen_candidates.py` | Unchanged. Deterministic `candidates.nc` is the fixed candidate pool. |
| `optimization/vp/compute_covariance.m` | **Unchanged.** `mc_reconstruct.m` is a separate file in this folder that mirrors its logic + adds annual-energy output. |
| `optimization/vp/05_optimize.py` | **Unchanged.** Invoked per sample via `TIDAL_RESULTS_DIR` env var pointing at the per-sample directory. |

Every line of new code lives under `experiments/uncertainty_mc/`. The deterministic pipeline at `optimization/vp/` is read-only for this experiment.
## Compute budget (estimated)
| Step | Per sample | Cells × samples | Wall clock |
| --- | --- | --- | --- |
| Perturb + write NetCDF | ~1 s | 180 | ~3 min |
| MATLAB startup + `mc_reconstruct.m` | ~10 s + 1–3 min | 180 | ~6–10 h |
| `05_optimize.py` (full LCOE-cap sweep) | ~1–5 min | 180 | ~3–15 h |
| Aggregation + analysis | one-shot | —   | ~5 min |
| **Total v1** |     | **180 samples** | **~10–25 h** (overnight, remote) |

Optional optimization deferred: batch K samples per MATLAB invocation to amortize the ~10 s startup. Only worth doing if MATLAB startup dominates per-sample wall clock after a first dry run.
## Next steps (implementation order — strict)
1. **Write** `EXPERIMENT.md` (this file). ✓
  
2. **Write** `src/perturb.py` + a small zero-noise sanity test. Verify gate 1 candidate exists.
  
3. **Write** `src/mc_reconstruct.m` by copying `compute_covariance.m` and adding annual-energy output.
  
4. **Write** `src/mc_driver.py` with a flag to run a single sample (for gate 1 + gate 2).
  
5. **Run gates 1 and 2** on a small candidate set. Fix bugs.
  
6. **Add σ-cell loop + sample loop** to `mc_driver.py`. Run gate 3.
  
7. **Write** `src/analyze.py` (frontier cloud + site-frequency). Run gate 4.
  
8. **Full 180-sample sweep** only after all four gates pass.
  
## Source-of-truth links
- INFORMS 2026 abstract: `writing/informs-2026/abstract.md`
  
- Reference paper (Anderson's prior framework, cited in talk not abstract): `papers/1-s2.0-S0360544223003407-main.pdf` (Faria, de Queiroz, DeCarolis 2023, _Energy_ 270:126946)
  
- Existing VP pipeline: `optimization/vp/`
  
- Existing deterministic NE+NY 50 MW VP run (candidate pool source): `results/vp/groups/ne_ny/` (path subject to verification)
  
- Experiment-folder conventions: `experiments/turbine_modification/EXPERIMENT.md`
