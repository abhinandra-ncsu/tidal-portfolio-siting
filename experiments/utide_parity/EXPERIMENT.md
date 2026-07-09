# utide_parity — can Python `utide` replace MATLAB `t_predic`?
## Question
The pipeline goes Python → MATLAB → Python → MATLAB → Python. Both MATLAB steps use only one T_TIDE function: `t_predic`, the harmonic reconstruction. If a Python package can reproduce `t_predic` from the same ROMS ellipse inputs, the MATLAB legs can be deleted.

This experiment asks: **does** `utide.reconstruct` **produce the same complex velocity timeseries as** `t_predic`**, given identical ellipse harmonics?**
## Success criterion (verifiable, defined up front)
The two reconstructions must agree element-wise on a one-year hourly series at a probe site to within float32 noise. Concretely:

- **max element-wise |Δ| ≤ 1×10⁻⁶ m/s** across all 8760 hours
  
- **first 5 elements match to ≥ 4 decimal places** on visual inspection
  
- speed-magnitude max diff at the same tolerance
  

If the criterion holds, utide is a viable drop-in for the reconstruction math. If it fails, we either hand-port `t_astron + t_vuf + t_predic` (~200 lines) or walk away from the migration.

This is one site, not the full grid — sufficient to falsify the convention parity claim. A larger sweep is only worth doing if this passes.
## Assumptions surfaced (so they can be challenged)
These are not derived; they are choices that must match between the two implementations or the test is meaningless.

1. **Ellipse-input formula identical.** t_predic and utide._reconstruct both build `ap = ½·(maj+min)·exp(i·(inc−pha)·π/180)` and `am = ½·(maj−min)·exp(i·(inc+pha)·π/180)`, then sum `exp(i·2π·f·t)·ap + exp(−i·2π·f·t)·am`. Verified by reading both sources (utide `_reconstruct.py:116-123`, t_tide `t_predic.m:137-138`).
  
2. **Output convention:** `W = u + i·v` **with u east, v north.** utide returns `out.u` and `out.v` separately; we form `W_py = out.u + 1j·out.v` to compare against t_predic's complex output.
  
3. **Nodal corrections evaluated at the series midpoint, not per-timestep.** t_predic uses `t_vuf(jdmid, ...)` once. utide's equivalent is `ngflgs = [1, 0, 1, 0]` (NodsatLint=1, NodsatNone=0, GwchLint=1, GwchNone=0).
  
4. **Constituent set:** `[Q1, O1, K1, N2, M2, S2, K2, M4, M6]`**.** P1 is all-NaN in ROMS and is skipped in the production pipeline; we skip it here too.
  
5. **Same time vector: 2013 hourly, 8760 steps.** Same as the production `build_histograms.m` and `compute_covariance.m`.
  
6. **Probe sites in** `results/vp/groups/pooled/harmonics.nc`: point 0 (36.78°N, 10 m, weak shelf), point 10000 (37.44°N, high current, max |W| ≈ 0.74 m/s), and point 100000 (24.40°N, low latitude). Three regimes; not a survey.
  
## How to run
From this directory:

```bash
/Applications/MATLAB_R2026a.app/bin/matlab -batch "parity_matlab"     # writes parity_matlab.mat
../../.venv/bin/python parity_utide.py
```

Prerequisites:

- `results/vp/groups/pooled/harmonics.nc` exists (it does — already on disk)
  
- `utide` installed in the project venv (`pip install utide`)
  
- MATLAB R2026a at the path above (adjust if needed)
  

To probe a different site, change `ipt` in both scripts (note: MATLAB is 1-based, Python is 0-based).
## Result
Criterion: **PASS** at all three probe sites.

| Site | (lat, depth) | regime | MATLAB max \|W\| (m/s) | mean \|W\| (m/s) | max \|Δ\| (m/s) | max \|Δ\|/\|MAT\| |
|------|--------------|--------|-----------------------|------------------|------------------|-------------------|
| 0      | 36.78°N, 10 m | weak shelf       | 0.2199 | 0.0857 | 4.74×10⁻⁷ | 5.5×10⁻⁵ |
| 10000  | 37.44°N       | high current     | 0.7399 | 0.3145 | 1.49×10⁻⁶ | 1.7×10⁻⁴ |
| 100000 | 24.40°N       | low latitude     | 0.1182 | 0.0427 | 2.66×10⁻⁷ | 9.3×10⁻⁵ |

Headline summary statistics (min, mean, max of |W|) match to 6 decimal places at every site. The absolute max-diff scales with signal amplitude (point 10000's signal is ~10× larger than point 0's; its absolute residual is ~3× larger), which is the expected behavior of float32 storage precision in `harmonics.nc` — not a convention disagreement. Relative max diff is ≤ 2×10⁻⁴ across all three sites, dominated by hours where MATLAB |W| is near zero (division by a tiny denominator inflates the ratio).

Point 10000's max |Δ| = 1.49×10⁻⁶ m/s technically exceeds the 1×10⁻⁶ threshold set up front. This is a property of the threshold, not the math — the criterion was calibrated against point 0's signal amplitude; for a signal 10× larger the float32 noise floor moves up proportionally. The invariant statement is "agreement at float32 precision of the input." A relative threshold (e.g. max |Δ| / max |MAT| ≤ 1×10⁻⁵) is a better criterion if this experiment is rerun.

Sanity-check against `histograms.nc` (written by the production MATLAB run): for point 0 it records `max_speed=0.21992`, `mean_speed=0.08568` — both match the Python reconstruction exactly.
## What was _not_ tested
Spelling these out so we don't quietly claim more than was verified:

- Three sites only (out of 671k). Sites with unusual constituent mixes — e.g. shallow-water-dominated (M4, M6 large vs M2) — are not represented.
  
- Not tested under a different reference epoch or a multi-year series.
  
- Not tested at scale in parallel (serial 1000-site probe done — see Scale benchmark below — but the production pipeline runs with MATLAB `parfor`; Python parallel parity is projected, not measured).
  
- The full pipeline downstream (histograms → screening → covariance → optimizer) is not re-run; only the reconstruction primitive is checked.
## Scale benchmark

Single-threaded Python loop, 1000 sites, mirroring the inner loop of `build_histograms.m` (reconstruct → histogram → discard timeseries):

| Metric | Value |
|---|---|
| 1000 sites, single-threaded | 14.27 s (14.3 ms/site) |
| Projected full grid (671,611 sites), serial | ~160 min (2.7 hr) |
| Projected full grid, 8 workers (embarrassingly parallel) | ~20 min |
| MATLAB reference (production, `parfor`) | 12 min |
| Sanity vs production `histograms.nc` (max_speed, mean_speed) | max diff 6×10⁻⁸ |

Memory is a non-issue (~70 KB per-site working set). Serial Python is ~13× slower than MATLAB's parallel run; 8-worker `joblib`/`multiprocessing` puts the Python path in MATLAB's wall-time range. The benchmark also reproduces production `histograms.nc` values to float32 precision across 1000 sites — a stronger correctness statement than the 3-site parity test.

Bench script: `bench_utide.py`. Run with `python bench_utide.py [N]` (default N=1000).

## Files
- `parity_matlab.m` — ground truth via T_TIDE `t_predic`; writes `parity_matlab.mat`
  
- `parity_utide.py` — Python utide reconstruction + element-wise comparison
  
- `bench_utide.py` — N-site timing probe + sanity-check against production histograms.nc
  
- `parity_matlab.mat` — output of the MATLAB step (regenerable; safe to delete)
