"""
Step 4: Plot mean tidal current speed over the East Coast.

Mirrors the project's plot conventions (optimization/vp/plot_results.py:60):
NOAA shoreline + matplotlib scatter. All 671k nodes that survived the
depth ≥ 10 m filter are shown.

Mean speed is a device-agnostic resource metric — it shows the underlying
tidal resource without the Gen5 cut-in cliff. mean_speed is written by
build_histograms.m alongside the speed histograms.

Input:  histograms.nc                                 (from build_histograms.m)
        ../../inputs/geography/NOAA_MedRes/allus80k.shp
Output: mean_speed_map.png
"""

import os

import geopandas as gpd
import matplotlib.pyplot as plt
import xarray as xr

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

HIST_PATH = os.path.join(SCRIPT_DIR, "histograms.nc")
SHORELINE_PATH = os.path.join(ROOT_DIR, "inputs", "geography",
                              "NOAA_MedRes", "allus80k.shp")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "mean_speed_map.png")


def main():
    print(f"Reading: {HIST_PATH}")
    ds = xr.open_dataset(HIST_PATH)
    lon = ds.longitude.values
    lat = ds.latitude.values
    v = ds.mean_speed.values
    n_pts = lon.size
    ds.close()
    print(f"  {n_pts:,} points, mean_speed range {v.min():.4f} to {v.max():.4f} m/s")

    print(f"Reading shoreline: {SHORELINE_PATH}")
    shoreline = gpd.read_file(SHORELINE_PATH)

    fig, ax = plt.subplots(figsize=(8, 10))
    shoreline.plot(ax=ax, color="0.85", linewidth=0.3)

    order = v.argsort()

    sc = ax.scatter(
        lon[order], lat[order], s=1.5, c=v[order],
        cmap="Blues", vmin=0.0, vmax=v.max(), zorder=2,
    )

    ax.set_xlim(lon.min() - 1, lon.max() + 1)
    ax.set_ylim(lat.min() - 1, lat.max() + 1)
    ax.set_title("Mean Tidal Current Speed — US East Coast",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal")

    cbar = fig.colorbar(sc, ax=ax, shrink=0.5, pad=0.02)
    cbar.set_label("Mean Speed (m/s)")

    fig.tight_layout()
    fig.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUTPUT_PATH} ({os.path.getsize(OUTPUT_PATH) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
