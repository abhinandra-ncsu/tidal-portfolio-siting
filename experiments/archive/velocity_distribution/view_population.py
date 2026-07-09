"""Stage 2 — all-sites speed histogram (population view).

Pools the 671k per-site PMFs in histograms.nc into a single distribution: the
fraction of all coastal site-hours spent in each 0.05 m/s speed bin. Because
every site contributes the same 8760 reconstructed hours, this mean-of-PMFs is
identical to pooling every site-hour directly. Log y-axis: the distribution
spans ~7 orders of magnitude, from the ~0.30 slack-water spike in the first bin
down to the energetic tail near 4.5 m/s.

Input : results/histograms.nc   (from build_histograms.m)
Output: results/population_histogram.png
"""
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from pathlib import Path

results = Path(__file__).resolve().parent / "results"
ds = xr.open_dataset(results / "histograms.nc")

centers = ds.speed_bin_centers.values
fraction = ds.speed_histogram.mean("point").values   # fraction of site-hours per bin
assert abs(fraction.sum() - 1.0) < 1e-4, fraction.sum()

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.bar(centers, fraction, width=0.05, edgecolor="none")
ax.set_yscale("log")
ax.set_xlim(0, 5)
ax.set_xlabel("speed |W|  (m/s)")
ax.set_ylabel("fraction of site-hours")
ax.set_title("all-sites speed histogram (0-5 m/s @ 0.05)")
ax.grid(True, which="major", axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(results / "population_histogram.png", dpi=150)
print(f"wrote {results / 'population_histogram.png'}")
print(f"sum={fraction.sum():.6f}  peak bin={centers[fraction.argmax()]:.3f} @ {fraction.max():.4f}")
