"""
Step 1: Extract tidal harmonics from the ROMS database.

Streams tide_data_east.dbf, keeps points inside East Coast state bounding
boxes (+ buffer), filters to depth >= 10 m, and saves harmonic ellipse
parameters for 10 tidal constituents.

Input:  ../inputs/roms/tide_data_east.dbf
        config/east_coast_state_boundaries.csv
Output: ../results/harmonics.nc
"""

import os
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import xarray as xr
from dbfread import DBF

from config.config import MIN_DEPTH_M, BBOX_BUFFER_DEG

# --- Paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

DBF_PATH = os.path.join(ROOT_DIR, "inputs", "roms", "tide_data_east.dbf")
BOUNDARIES_CSV = os.path.join(SCRIPT_DIR, "config", "east_coast_state_boundaries.csv")

RESULTS_DIR = os.path.join(ROOT_DIR, "results")
OUTPUT_PATH = os.path.join(RESULTS_DIR, "harmonics.nc")

# --- Parameters ---
CONSTITUENTS = ["q1", "o1", "p1", "k1", "n2", "m2", "s2", "k2", "m4", "m6"]
MISSING = -999.999

# DBF field name prefixes for current ellipse parameters
FIELD_PREFIXES = {
    "current_semimajor":   "CMAJ",
    "current_semiminor":   "CMIN",
    "current_inclination": "CINC",
    "current_phase":       "CPHA",
}


def load_bounding_boxes(csv_path, buffer_deg):
    """Load state bounding boxes. Returns list of (south, north, west, east)."""
    df = pd.read_csv(csv_path)
    boxes = []
    for _, row in df.iterrows():
        boxes.append((
            row["South_Boundary"] - buffer_deg,
            row["North_Boundary"] + buffer_deg,
            row["West_Boundary"] - buffer_deg,
            row["East_Boundary"] + buffer_deg,
        ))
    return boxes


def point_in_any_box(lat, lon, boxes):
    for south, north, west, east in boxes:
        if south <= lat <= north and west <= lon <= east:
            return True
    return False


def extract_points(dbf_path, boxes, min_depth):
    """Stream DBF, keep East Coast points with depth >= min_depth."""
    table = DBF(dbf_path, load=False)

    lons, lats, depths = [], [], []
    harmonics = {var: {c: [] for c in CONSTITUENTS} for var in FIELD_PREFIXES}

    t0 = time.time()
    n_scanned = 0
    n_shallow = 0

    for rec in table:
        n_scanned += 1
        if n_scanned % 200_000 == 0:
            elapsed = time.time() - t0
            print(f"  {n_scanned:,} scanned, {len(lons):,} kept, "
                  f"{n_shallow:,} too shallow ({elapsed:.0f}s)")

        lat, lon = rec["LATITU"], rec["LONGIT"]
        if not point_in_any_box(lat, lon, boxes):
            continue

        depth = rec["WDEPTH"]
        if depth < min_depth:
            n_shallow += 1
            continue

        lons.append(lon)
        lats.append(lat)
        depths.append(depth)

        for var_name, prefix in FIELD_PREFIXES.items():
            for c in CONSTITUENTS:
                field = f"{prefix}{c.upper()}"
                val = rec[field]
                harmonics[var_name][c].append(np.nan if val == MISSING else val)

    elapsed = time.time() - t0
    print(f"  Done: {n_scanned:,} scanned, {len(lons):,} kept, "
          f"{n_shallow:,} too shallow ({elapsed:.0f}s)")

    arrays = {
        "longitude": np.array(lons, dtype=np.float64),
        "latitude": np.array(lats, dtype=np.float64),
        "depth": np.array(depths, dtype=np.float32),
    }
    for var_name in FIELD_PREFIXES:
        arrays[var_name] = np.stack(
            [np.array(harmonics[var_name][c], dtype=np.float32)
             for c in CONSTITUENTS]
        )  # shape: (n_constituents, n_points)

    return arrays


def save_dataset(arrays, out_path):
    """Build xarray Dataset and write compressed NetCDF."""
    n_pts = len(arrays["longitude"])

    var_meta = {
        "current_semimajor":   ("m/s", "Tidal current ellipse semi-major axis"),
        "current_semiminor":   ("m/s", "Tidal current ellipse semi-minor axis (signed)"),
        "current_inclination": ("degrees", "Tidal current ellipse inclination from east"),
        "current_phase":       ("degrees", "Tidal current Greenwich phase lag"),
    }

    data_vars = {
        "longitude": (["point"], arrays["longitude"], {"units": "degrees_east"}),
        "latitude":  (["point"], arrays["latitude"],  {"units": "degrees_north"}),
        "depth":     (["point"], arrays["depth"],     {"units": "m", "long_name": "Water depth"}),
    }

    for var_name, (units, long_name) in var_meta.items():
        data_vars[var_name] = (
            ["constituent", "point"],
            arrays[var_name],
            {"units": units, "long_name": long_name},
        )

    ds = xr.Dataset(
        data_vars,
        coords={
            "constituent": CONSTITUENTS,
            "point": np.arange(n_pts),
        },
        attrs={
            "title": f"Tidal harmonic constituents — US East Coast, depth >= {MIN_DEPTH_M} m",
            "source": "ROMS tidal model (Haas et al., 2011)",
            "min_depth_m": MIN_DEPTH_M,
            "bbox_buffer_deg": BBOX_BUFFER_DEG,
            "n_points": n_pts,
            "constituents": ", ".join(CONSTITUENTS),
            "created": datetime.now(timezone.utc).isoformat(),
        },
    )

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    encoding = {v: {"zlib": True, "complevel": 4}
                for v in ds.data_vars if ds[v].dtype in (np.float32, np.float64)}
    ds.to_netcdf(out_path, encoding=encoding)
    ds.close()
    print(f"  Saved: {out_path} ({os.path.getsize(out_path) / 1e6:.1f} MB)")


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    if os.path.exists(OUTPUT_PATH):
        print(f"Output already exists: {OUTPUT_PATH}")
        print("Delete it to re-extract.")
        return

    print(f"Min depth: {MIN_DEPTH_M} m")
    boxes = load_bounding_boxes(BOUNDARIES_CSV, BBOX_BUFFER_DEG)
    print(f"Loaded {len(boxes)} bounding boxes (buffer: {BBOX_BUFFER_DEG} deg)")

    print("Streaming DBF...")
    arrays = extract_points(DBF_PATH, boxes, MIN_DEPTH_M)

    n = len(arrays["longitude"])
    print(f"\n{n:,} points extracted")
    print(f"  Lon:   {arrays['longitude'].min():.4f} to {arrays['longitude'].max():.4f}")
    print(f"  Lat:   {arrays['latitude'].min():.4f} to {arrays['latitude'].max():.4f}")
    print(f"  Depth: {arrays['depth'].min():.1f} to {arrays['depth'].max():.1f} m")

    print("\nSaving NetCDF...")
    save_dataset(arrays, OUTPUT_PATH)
    print("Done.")


if __name__ == "__main__":
    main()
