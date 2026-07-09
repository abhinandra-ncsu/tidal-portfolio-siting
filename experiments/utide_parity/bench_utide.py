"""Timing probe: utide reconstruction + histogram on N sites, serial.

Mirrors the inner loop of build_histograms.m: per site, reconstruct hourly
2013 series from ellipse harmonics, bin |W| into 100 bins on [0, 5] m/s,
record max/mean speed, discard the timeseries. No parallelism — single
worker is the honest baseline; MATLAB's 12-min full run uses parfor.

Output: total wall time on N sites, ms/site, projection to 671k sites.

Run:
  ../../.venv/bin/python bench_utide.py [N]
"""
import datetime as dt
import os
import sys
import time

import numpy as np
import xarray as xr
from utide._reconstruct import reconstruct
from utide._time_conversion import _normalize_time
from utide._ut_constants import ut_constants
from utide.utilities import Bunch

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
HARMONICS = os.path.join(REPO, "results", "vp", "groups", "pooled", "harmonics.nc")

N = int(sys.argv[1]) if len(sys.argv) > 1 else 1000

# --- Load harmonics for first N sites ---
ds = xr.open_dataset(HARMONICS)
n_total = ds.sizes["point"]
assert N <= n_total, f"N={N} exceeds available {n_total} sites"

valid_idx = [0, 1, 3, 4, 5, 6, 7, 8, 9]   # skip P1
valid_names = ["Q1", "O1", "K1", "N2", "M2", "S2", "K2", "M4", "M6"]
n_con = len(valid_names)

cmaj_all = ds.current_semimajor.values[valid_idx, :N].astype(float)
cmin_all = ds.current_semiminor.values[valid_idx, :N].astype(float)
cinc_all = ds.current_inclination.values[valid_idx, :N].astype(float)
cpha_all = ds.current_phase.values[valid_idx, :N].astype(float)
lat_all  = ds.latitude.values[:N].astype(float)

for arr in (cmaj_all, cmin_all, cinc_all, cpha_all):
    arr[np.isnan(arr)] = 0.0

# Sites with all-NaN harmonics are skipped (matches MATLAB build_histograms)
skip_mask = (cmaj_all == 0).all(axis=0)
print(f"Loaded {N} sites, {skip_mask.sum()} all-zero (skipped)")

# --- Precompute time-vector + lookup tables (constant across sites) ---
const_names = np.array([n.strip() for n in ut_constants["const"]["name"]])
lind = np.array([np.where(const_names == n)[0][0] for n in valid_names], dtype=int)
frq = ut_constants["const"]["freq"][lind].astype(float)

t_start = dt.datetime(2013, 1, 1, 0, 0, 0)
t = np.array([t_start + dt.timedelta(hours=i) for i in range(8760)])
t_norm = _normalize_time(t, None)
reftime = float(np.mean(t_norm))

edges = np.arange(0.0, 5.0001, 0.05)   # 101 edges → 100 bins
n_bins = len(edges) - 1

# --- Output arrays (analogous to MATLAB) ---
histograms = np.zeros((N, n_bins), dtype=np.float32)
max_speeds = np.zeros(N, dtype=np.float32)
mean_speeds = np.zeros(N, dtype=np.float32)

# --- Reusable Bunch template (overwrite arrays in-place each site) ---
def make_coef(cmaj, cmin, cinc, cpha, lat):
    return Bunch(
        name=np.array(valid_names),
        Lsmaj=cmaj, Lsmin=cmin, theta=cinc, g=cpha,
        Lsmaj_ci=np.zeros(n_con), Lsmin_ci=np.zeros(n_con),
        umean=0.0, vmean=0.0,
        aux=Bunch(
            frq=frq, lind=lind, lat=lat, reftime=reftime,
            opt=Bunch(
                twodim=True, nodiagn=True, notrend=True, prefilt=[],
                nodsatlint=1, nodsatnone=0, gwchlint=1, gwchnone=0,
            ),
        ),
    )

# --- Time the loop ---
t0 = time.perf_counter()
for i in range(N):
    if skip_mask[i]:
        continue
    coef = make_coef(cmaj_all[:, i], cmin_all[:, i], cinc_all[:, i],
                     cpha_all[:, i], lat_all[i])
    out = reconstruct(t, coef, verbose=False)
    speed = np.abs(out.u + 1j * out.v)
    hist, _ = np.histogram(speed, bins=edges, density=False)
    histograms[i, :] = hist / hist.sum()
    max_speeds[i] = speed.max()
    mean_speeds[i] = speed.mean()

elapsed = time.perf_counter() - t0
ms_per_site = elapsed / max(N - skip_mask.sum(), 1) * 1000

print(f"\nElapsed: {elapsed:.2f} s on {N} sites ({(N - skip_mask.sum())} processed)")
print(f"Per-site: {ms_per_site:.2f} ms")
print(f"Projected for {n_total:,} sites: "
      f"{elapsed * n_total / N / 60:.1f} min serial, "
      f"{elapsed * n_total / N / 60 / 8:.1f} min on 8 workers")

# Sanity-check against histograms.nc for the same sites
ref = xr.open_dataset(os.path.join(REPO, "results/vp/groups/pooled/histograms.nc"))
ref_max = ref.max_speed.values[:N]
ref_mean = ref.mean_speed.values[:N]
max_err = np.max(np.abs(max_speeds - ref_max))
mean_err = np.max(np.abs(mean_speeds - ref_mean))
print(f"\nSanity vs production histograms.nc:")
print(f"  max(|max_speed - ref|)  = {max_err:.3e}")
print(f"  max(|mean_speed - ref|) = {mean_err:.3e}")
