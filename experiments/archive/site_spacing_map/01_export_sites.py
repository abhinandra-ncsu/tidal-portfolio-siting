"""Export East Coast site locations + nearest-neighbor spacing for the deck.gl map.

Reads the pooled East Coast extraction (671,611 sites, state bboxes + 0.15 deg
buffer, depth >= 10 m) from experiments/east_coast_cf_map/harmonics.nc,
computes each site's nearest-neighbor distance on the sphere, and writes a
compact binary the HTML map can fetch.

Input:  ../east_coast_cf_map/harmonics.nc
Output: results/sites.bin   (4 contiguous Float32 blocks: lon, lat, nn_dist_m, depth_m)
        results/meta.json   (n_points, block order, NN-distance percentiles)
"""

import json
import os

import numpy as np
import xarray as xr
from scipy.spatial import cKDTree

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HARMONICS_PATH = os.path.join(SCRIPT_DIR, "..", "east_coast_cf_map", "harmonics.nc")
RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")
BIN_PATH = os.path.join(RESULTS_DIR, "sites.bin")
META_PATH = os.path.join(RESULTS_DIR, "meta.json")

EARTH_RADIUS_M = 6_371_000.0


def main():
    print(f"Loading {HARMONICS_PATH} ...")
    ds = xr.open_dataset(HARMONICS_PATH)
    lon = ds.longitude.values.astype(np.float64)
    lat = ds.latitude.values.astype(np.float64)
    depth = ds.depth.values.astype(np.float32)
    n = len(lon)
    print(f"  {n:,} sites")

    print("Computing nearest-neighbor distances (ECEF chord ~ arc at these scales) ...")
    latr, lonr = np.deg2rad(lat), np.deg2rad(lon)
    xyz = np.column_stack([
        np.cos(latr) * np.cos(lonr),
        np.cos(latr) * np.sin(lonr),
        np.sin(latr),
    ]) * EARTH_RADIUS_M
    tree = cKDTree(xyz)
    d, _ = tree.query(xyz, k=2, workers=-1)
    nn = d[:, 1].astype(np.float32)

    pcts = {f"p{q}": round(float(np.percentile(nn, q)), 1)
            for q in [1, 5, 25, 50, 75, 95, 99]}
    print(f"  NN distance: median={pcts['p50']} m, p5={pcts['p5']}, p95={pcts['p95']}")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(BIN_PATH, "wb") as f:
        f.write(lon.astype(np.float32).tobytes())
        f.write(lat.astype(np.float32).tobytes())
        f.write(nn.tobytes())
        f.write(depth.tobytes())
    meta = {
        "n_points": n,
        "blocks": ["lon", "lat", "nn_dist_m", "depth_m"],
        "dtype": "float32",
        "nn_percentiles_m": pcts,
        "source": "experiments/east_coast_cf_map/harmonics.nc",
        "filter": "East Coast state bboxes + 0.15 deg buffer, depth >= 10 m",
    }
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Wrote {BIN_PATH} ({os.path.getsize(BIN_PATH) / 1e6:.1f} MB)")
    print(f"Wrote {META_PATH}")


if __name__ == "__main__":
    main()
