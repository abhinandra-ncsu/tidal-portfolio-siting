"""
Step 3: Screen candidate sites and compute shore distances.

Applies VP Gen5 power curve to speed histograms, filters to CF > 0.05,
computes shore distance to NOAA NOS80K coastline.

Input:  ../results/histograms.nc  (from build_histograms.m)
        ../inputs/geography/NOAA_MedRes/allus80k.shp
Output: ../results/candidates.nc
"""

import os
from datetime import datetime, timezone

import geopandas as gpd
import numpy as np
import xarray as xr
from scipy.spatial import cKDTree

from config.config import (
    CF_THRESHOLD, RHO, AREA, CP, P_RATED_W, V_CUT_IN, V_RATED,
    get_results_dir, get_resource_dir, get_curve_dir,
)

# --- Paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

RESULTS_DIR = get_results_dir()
# histograms.nc is resource-only (identical for every power curve); read it from
# the shared resource dir, which falls back to RESULTS_DIR when unset.
HISTOGRAM_PATH = os.path.join(get_resource_dir(), "histograms.nc")
SHORELINE_PATH = os.path.join(
    ROOT_DIR, "inputs", "geography", "NOAA_MedRes", "allus80k.shp",
)
# candidates.nc is curve-level (shared across capacities within a power
# curve); it lives in the shared curve dir, which falls back to RESULTS_DIR
# when unset.
OUTPUT_PATH = os.path.join(get_curve_dir(), "candidates.nc")

R_EARTH_KM = 6371.0


def compute_power_curve(bin_centers):
    """VP Gen5 power at each speed bin center (W)."""
    power = np.zeros(len(bin_centers))
    for k, v in enumerate(bin_centers):
        if v < V_CUT_IN:
            power[k] = 0.0
        elif v <= V_RATED:
            power[k] = 0.5 * RHO * AREA * CP * v**3
        else:
            power[k] = P_RATED_W
    return power


def haversine(lat1, lon1, lat2, lon2):
    """Haversine distance in km. All inputs in degrees. Vectorized."""
    lat1, lat2 = np.radians(lat1), np.radians(lat2)
    dlat = lat2 - lat1
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    return R_EARTH_KM * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


def compute_shore_distances(lats, lons, shoreline_path):
    """Distance to nearest coastline point via KDTree + Haversine."""
    print(f"  Loading shapefile: {shoreline_path}")
    shoreline = gpd.read_file(shoreline_path)

    coast_coords = []
    for geom in shoreline.geometry:
        if geom is None:
            continue
        if geom.geom_type == "MultiPolygon":
            for poly in geom.geoms:
                coast_coords.append(np.array(poly.exterior.coords))
        elif geom.geom_type == "Polygon":
            coast_coords.append(np.array(geom.exterior.coords))
        elif geom.geom_type == "MultiLineString":
            for line in geom.geoms:
                coast_coords.append(np.array(line.coords))
        elif geom.geom_type == "LineString":
            coast_coords.append(np.array(geom.coords))
    coast_coords = np.vstack(coast_coords)
    print(f"  Coastline vertices: {len(coast_coords):,}")

    # KDTree on (lon, lat) for approximate nearest neighbor
    tree = cKDTree(coast_coords)
    _, idx = tree.query(np.column_stack([lons, lats]))

    # Refine with Haversine
    distances = haversine(lats, lons, coast_coords[idx, 1], coast_coords[idx, 0])
    return distances


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    if os.path.exists(OUTPUT_PATH):
        print(f"Already exists: {OUTPUT_PATH}")
        print("Delete to re-run.")
        return

    # Load histograms
    print(f"Reading: {HISTOGRAM_PATH}")
    ds = xr.open_dataset(HISTOGRAM_PATH)

    lat = ds["latitude"].values
    lon = ds["longitude"].values
    depth = ds["depth"].values
    mean_speed = ds["mean_speed"].values
    max_speed = ds["max_speed"].values
    centers = ds["speed_bin_centers"].values

    # Histogram shape from MATLAB NetCDF: (speed_bin, point)
    hist = ds["speed_histogram"].values
    if hist.shape[0] == len(centers):
        # (speed_bin, point) -> need (point, speed_bin) for matrix multiply
        hist_pt = hist.T
    else:
        hist_pt = hist
    n_pts = len(lat)
    print(f"  {n_pts:,} points, {len(centers)} speed bins")

    # Compute capacity factor
    print("Computing capacity factors...")
    power_curve = compute_power_curve(centers)  # (n_bins,)
    mean_power = hist_pt @ power_curve           # (n_pts,)
    cf = mean_power / P_RATED_W

    # Screen
    mask = cf > CF_THRESHOLD
    n_cand = mask.sum()
    print(f"  CF > {CF_THRESHOLD}: {n_cand:,} candidates ({100 * n_cand / n_pts:.1f}%)")

    cand_lat = lat[mask]
    cand_lon = lon[mask]
    cand_depth = depth[mask]
    cand_cf = cf[mask].astype(np.float32)
    cand_mean_speed = mean_speed[mask]
    cand_max_speed = max_speed[mask]
    cand_hist = hist_pt[mask, :]  # (n_cand, n_bins)
    cand_point_index = np.where(mask)[0].astype(np.int32)

    print(f"  CF range: {cand_cf.min():.3f} to {cand_cf.max():.3f}")

    # Shore distances
    print("Computing shore distances...")
    distances = compute_shore_distances(cand_lat, cand_lon, SHORELINE_PATH)
    print(f"  Distance range: {distances.min():.2f} to {distances.max():.2f} km")

    # Save
    print("Saving...")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    out = xr.Dataset(
        {
            "latitude": (["site"], cand_lat, {"units": "degrees_north"}),
            "longitude": (["site"], cand_lon, {"units": "degrees_east"}),
            "depth": (["site"], cand_depth, {"units": "m"}),
            "capacity_factor": (["site"], cand_cf),
            "mean_speed": (["site"], cand_mean_speed, {"units": "m/s"}),
            "max_speed": (["site"], cand_max_speed, {"units": "m/s"}),
            "shore_distance_km": (["site"], distances.astype(np.float32),
                                  {"units": "km"}),
            "point_index": (["site"], cand_point_index,
                            {"long_name": "Index into harmonics.nc for covariance lookup"}),
            "speed_histogram": (["site", "speed_bin"], cand_hist.astype(np.float32),
                                {"units": "probability"}),
            "speed_bin_centers": (["speed_bin"], centers, {"units": "m/s"}),
        },
        coords={
            "site": np.arange(n_cand),
            "speed_bin": np.arange(len(centers)),
        },
        attrs={
            "title": "Candidate sites for tidal portfolio optimization",
            "cf_threshold": CF_THRESHOLD,
            "turbine": "VP Gen5, Lewis et al. (2021)",
            "p_rated_w": P_RATED_W,
            "v_cut_in_ms": V_CUT_IN,
            "v_rated_ms": V_RATED,
            "cp": CP,
            "shoreline": "NOAA NOS80K (allus80k.shp)",
            "n_candidates": int(n_cand),
            "created": datetime.now(timezone.utc).isoformat(),
        },
    )

    ds.close()
    encoding = {v: {"zlib": True, "complevel": 4}
                for v in out.data_vars if out[v].dtype in (np.float32, np.float64)}
    out.to_netcdf(OUTPUT_PATH, encoding=encoding)
    out.close()

    print(f"Saved: {OUTPUT_PATH} ({os.path.getsize(OUTPUT_PATH) / 1e6:.1f} MB)")
    print("Done.")


if __name__ == "__main__":
    main()
