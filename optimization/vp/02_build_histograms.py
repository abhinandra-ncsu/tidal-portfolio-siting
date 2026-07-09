"""
Step 2: Build speed histograms from tidal harmonics (Python/utide).

Reconstructs a 1-year hourly tidal current timeseries for each point using
utide (Python port of T_TIDE), bins |W| into probability histograms.
Replaces build_histograms.m.

Input:  results/<scope>/harmonics.nc   (from 01_extract_harmonics.py)
Output: results/<scope>/histograms.nc

Schema is preserved byte-for-byte from the MATLAB version so that
03_screen_candidates.py reads it unchanged.
"""
import datetime as dt
import os
import time
import warnings
from datetime import datetime, timezone

import numpy as np
import xarray as xr
from joblib import Parallel, delayed
from utide._reconstruct import reconstruct
from utide._time_conversion import _normalize_time
from utide._ut_constants import ut_constants
from utide.utilities import Bunch

from config.config import get_results_dir

# --- Paths ---
RESULTS_DIR = get_results_dir()
INPUT_PATH = os.path.join(RESULTS_DIR, "harmonics.nc")
OUTPUT_PATH = os.path.join(RESULTS_DIR, "histograms.nc")

# --- Parameters (match config.m) ---
VALID_IDX = [0, 1, 3, 4, 5, 6, 7, 8, 9]            # skip P1 (all-NaN in ROMS)
VALID_NAMES = ["Q1", "O1", "K1", "N2", "M2", "S2", "K2", "M4", "M6"]
N_CON = len(VALID_NAMES)

BIN_EDGES = np.arange(0.0, 5.0001, 0.05)   # 101 edges -> 100 bins, 0-5 m/s
N_BINS = len(BIN_EDGES) - 1
BIN_CENTERS = BIN_EDGES[:-1] + 0.025

# 2013 hourly, matching build_histograms.m
T_START = datetime(2013, 1, 1, 0, 0, 0)
N_TIMES = 8760
T = np.array([T_START + dt.timedelta(hours=i) for i in range(N_TIMES)])

# Lookup tables into utide's constituent table (computed once)
_const_names = np.array([n.strip() for n in ut_constants["const"]["name"]])
LIND = np.array([np.where(_const_names == n)[0][0] for n in VALID_NAMES], dtype=int)
FRQ = ut_constants["const"]["freq"][LIND].astype(float)
_T_NORM = _normalize_time(T, None)
REFTIME = float(np.mean(_T_NORM))

N_JOBS = int(os.environ.get("TIDAL_N_JOBS", "-1"))   # -1 = all cores
BATCH_SIZE = int(os.environ.get("TIDAL_BATCH_SIZE", "256"))


def _make_coef(major, minor, inc, pha, lat):
    return Bunch(
        name=np.array(VALID_NAMES),
        Lsmaj=major, Lsmin=minor, theta=inc, g=pha,
        Lsmaj_ci=np.zeros(N_CON), Lsmin_ci=np.zeros(N_CON),
        umean=0.0, vmean=0.0,
        aux=Bunch(
            frq=FRQ, lind=LIND, lat=lat, reftime=REFTIME,
            opt=Bunch(
                twodim=True, nodiagn=True, notrend=True, prefilt=[],
                nodsatlint=1, nodsatnone=0, gwchlint=1, gwchnone=0,
            ),
        ),
    )


def _process_batch(majors, minors, incs, phas, lats):
    """Process one batch of sites; return (hists, max_v, mean_v, skipped)."""
    n = lats.shape[0]
    hists = np.zeros((n, N_BINS), dtype=np.float32)
    max_v = np.zeros(n, dtype=np.float32)
    mean_v = np.zeros(n, dtype=np.float32)
    skipped = np.zeros(n, dtype=bool)

    for i in range(n):
        major = majors[i]
        if np.all(np.isnan(major)):
            skipped[i] = True
            continue
        minor = minors[i].copy(); minor[np.isnan(minor)] = 0
        inc = incs[i].copy(); inc[np.isnan(inc)] = 0
        pha = phas[i].copy(); pha[np.isnan(pha)] = 0
        major = major.copy(); major[np.isnan(major)] = 0

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            coef = _make_coef(major, minor, inc, pha, float(lats[i]))
            out = reconstruct(T, coef, verbose=False)

        speed = np.abs(out.u + 1j * out.v)
        hist, _ = np.histogram(speed, bins=BIN_EDGES)
        s = hist.sum()
        if s > 0:
            hists[i, :] = hist / s
        max_v[i] = speed.max()
        mean_v[i] = speed.mean()

    return hists, max_v, mean_v, skipped


def main():
    if os.path.exists(OUTPUT_PATH):
        print(f"Already exists: {OUTPUT_PATH}")
        print("Delete to re-run.")
        return

    print(f"Reading: {INPUT_PATH}")
    ds = xr.open_dataset(INPUT_PATH)
    n_pts = ds.sizes["point"]
    print(f"  {n_pts:,} points, {ds.sizes['constituent']} constituents")

    cmaj = ds.current_semimajor.values[VALID_IDX, :].astype(float)
    cmin = ds.current_semiminor.values[VALID_IDX, :].astype(float)
    cinc = ds.current_inclination.values[VALID_IDX, :].astype(float)
    cpha = ds.current_phase.values[VALID_IDX, :].astype(float)
    lat = ds.latitude.values.astype(float)
    lon = ds.longitude.values.astype(float)
    depth = ds.depth.values
    ds.close()

    # Transpose to (n_pts, n_con) for per-site indexing
    cmaj = cmaj.T; cmin = cmin.T; cinc = cinc.T; cpha = cpha.T

    # Split into batches
    batch_starts = list(range(0, n_pts, BATCH_SIZE))
    print(f"Processing {n_pts:,} sites in {len(batch_starts)} batches "
          f"of up to {BATCH_SIZE} (n_jobs={N_JOBS})")

    t0 = time.perf_counter()
    results = Parallel(n_jobs=N_JOBS, verbose=5)(
        delayed(_process_batch)(
            cmaj[s:s + BATCH_SIZE], cmin[s:s + BATCH_SIZE],
            cinc[s:s + BATCH_SIZE], cpha[s:s + BATCH_SIZE],
            lat[s:s + BATCH_SIZE],
        )
        for s in batch_starts
    )
    elapsed = time.perf_counter() - t0

    histograms = np.concatenate([r[0] for r in results], axis=0)
    max_speeds = np.concatenate([r[1] for r in results], axis=0)
    mean_speeds = np.concatenate([r[2] for r in results], axis=0)
    skipped_mask = np.concatenate([r[3] for r in results], axis=0)
    n_skipped = int(skipped_mask.sum())

    print(f"Done: {elapsed/60:.1f} min, {n_pts - n_skipped:,} processed, "
          f"{n_skipped:,} skipped")
    valid = ~skipped_mask
    if valid.any():
        print(f"  Mean speed: {mean_speeds[valid].mean():.4f} m/s, "
              f"Max speed: {max_speeds.max():.4f} m/s")

    # --- Write NetCDF (schema matches build_histograms.m output) ---
    print(f"\nSaving: {OUTPUT_PATH}")
    out = xr.Dataset(
        {
            "latitude":  (["point"], lat, {"units": "degrees_north"}),
            "longitude": (["point"], lon, {"units": "degrees_east"}),
            "depth":     (["point"], depth.astype(np.float32), {"units": "m"}),
            # MATLAB writes (point, speed_bin) but xarray-reads it back as
            # (speed_bin, point) due to column-major storage. Match that here
            # so downstream (03_screen_candidates.py) sees the same shape.
            "speed_histogram": (
                ["speed_bin", "point"],
                histograms.T.astype(np.float32),
                {"units": "probability"},
            ),
            "speed_bin_edges":   (["edge"], BIN_EDGES, {"units": "m/s"}),
            "speed_bin_centers": (["speed_bin"], BIN_CENTERS, {"units": "m/s"}),
            "mean_speed": (["point"], mean_speeds, {"units": "m/s"}),
            "max_speed":  (["point"], max_speeds, {"units": "m/s"}),
        },
        attrs={
            "title": "Tidal current speed histograms — US East Coast",
            "source": "utide (Pawlowicz et al., 2002) from ROMS harmonics",
            "reconstruction_year": "2013",
            "time_step_hours": 1,
            "n_time_steps": N_TIMES,
            "n_points": n_pts,
            "n_skipped": n_skipped,
            "constituents": ", ".join(VALID_NAMES),
            "histogram_bins": f"{N_BINS} bins, 0-5 m/s, 0.05 m/s step",
            "created": datetime.now(timezone.utc).isoformat(),
        },
    )
    encoding = {"speed_histogram": {"zlib": True, "complevel": 4}}
    out.to_netcdf(OUTPUT_PATH, encoding=encoding)
    print(f"Saved: {os.path.getsize(OUTPUT_PATH) / 1e6:.1f} MB")
    print(f"Total time: {elapsed/60:.1f} min")


if __name__ == "__main__":
    main()
