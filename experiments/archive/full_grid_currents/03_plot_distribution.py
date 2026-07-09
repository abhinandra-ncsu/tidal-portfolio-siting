"""
Step 3: Pooled hourly tidal current speed distribution.

Plots the single pooled histogram of every reconstructed hourly speed value
(every site x every hour): x = speed (m/s, 0.05 bins), y = count of site-hours.

Input:  results/speed_histogram.nc   (from reconstruct_currents.m)
Output: results/speed_distribution.png
"""
import os

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(SCRIPT_DIR, "results", "speed_histogram.nc")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "results", "speed_distribution.png")


def main():
    ds = xr.open_dataset(INPUT_PATH)
    centers = ds.speed_bin_centers.values
    count = ds["count"].values
    n_pts = int(ds.attrs["n_points"])
    n_times = int(ds.attrs["n_time_steps"])

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(centers, count, width=0.05, color="#2c7fb8", edgecolor="none")
    ax.set_xlabel("Tidal current speed (m/s)")
    ax.set_ylabel("Count of site-hours")
    ax.set_xlim(0, centers[count > 0].max() + 0.1 if (count > 0).any() else 5)
    ax.set_title(
        f"Pooled hourly current speed - full East Coast grid, no depth filter\n"
        f"{n_pts:,} sites x {n_times:,} hours = {n_pts * n_times:,} site-hours"
    )
    fig.tight_layout()
    fig.savefig(OUTPUT_PATH, dpi=150)
    print(f"Saved: {OUTPUT_PATH}")

    # Summary: where the mass sits (counts are per 0.05 m/s bin)
    total = count.sum()
    cdf = np.cumsum(count) / total
    for q in (0.5, 0.9, 0.99):
        i = int(np.searchsorted(cdf, q))
        print(f"  {int(q*100)}% of site-hours below {centers[i]:.2f} m/s")
    print(f"  share of site-hours >= 1.0 m/s: {count[centers >= 1.0].sum()/total:.3%}")


if __name__ == "__main__":
    main()
