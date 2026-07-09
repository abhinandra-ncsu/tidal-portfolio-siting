"""
Step 4: Compute power covariance matrix (Python/utide).

Reconstructs hourly 2013 speed timeseries for candidate sites, applies the VP
variant power curve, computes the covariance matrix needed for the portfolio
optimization objective.  Replaces compute_covariance.m.

Input:  results/<scope>/candidates.nc   (from 03_screen_candidates.py)
        results/<scope>/harmonics.nc    (from 01_extract_harmonics.py)
Output: results/<scope>/covariance.nc
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

from config.config import (
    get_results_dir, RHO, AREA, CP, V_CUT_IN, V_RATED, P_RATED_W,
)

# --- Paths ---
RESULTS_DIR = get_results_dir()
CANDIDATES_PATH = os.path.join(RESULTS_DIR, "candidates.nc")
HARMONICS_PATH = os.path.join(RESULTS_DIR, "harmonics.nc")
OUTPUT_PATH = os.path.join(RESULTS_DIR, "covariance.nc")

# --- Parameters (match config.m) ---
VALID_IDX = [0, 1, 3, 4, 5, 6, 7, 8, 9]
VALID_NAMES = ["Q1", "O1", "K1", "N2", "M2", "S2", "K2", "M4", "M6"]
N_CON = len(VALID_NAMES)

T_START = datetime(2013, 1, 1, 0, 0, 0)
N_TIMES = 8760
T = np.array([T_START + dt.timedelta(hours=i) for i in range(N_TIMES)])

_const_names = np.array([n.strip() for n in ut_constants["const"]["name"]])
LIND = np.array([np.where(_const_names == n)[0][0] for n in VALID_NAMES], dtype=int)
FRQ = ut_constants["const"]["freq"][LIND].astype(float)
_T_NORM = _normalize_time(T, None)
REFTIME = float(np.mean(_T_NORM))

N_JOBS = int(os.environ.get("TIDAL_N_JOBS", "-1"))
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
    """Return (n_batch, n_times) power matrix (single precision) for a batch."""
    n = lats.shape[0]
    power = np.zeros((n, N_TIMES), dtype=np.float32)
    for i in range(n):
        major = majors[i]
        if np.all(np.isnan(major)):
            continue
        major = major.copy(); major[np.isnan(major)] = 0
        minor = minors[i].copy(); minor[np.isnan(minor)] = 0
        inc = incs[i].copy(); inc[np.isnan(inc)] = 0
        pha = phas[i].copy(); pha[np.isnan(pha)] = 0

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            coef = _make_coef(major, minor, inc, pha, float(lats[i]))
            out = reconstruct(T, coef, verbose=False)
        speed = np.abs(out.u + 1j * out.v).astype(np.float32)

        # VP power curve: cubic in [V_CUT_IN, V_RATED], capped at P_RATED above
        p = np.zeros(N_TIMES, dtype=np.float32)
        cubic = (speed >= V_CUT_IN) & (speed <= V_RATED)
        p[cubic] = (0.5 * RHO * AREA * CP * speed[cubic] ** 3).astype(np.float32)
        rated = speed > V_RATED
        p[rated] = np.float32(P_RATED_W)
        power[i, :] = p
    return power


def main():
    if os.path.exists(OUTPUT_PATH):
        print(f"Already exists: {OUTPUT_PATH}")
        print("Delete to re-run.")
        return

    print(f"Loading candidates: {CANDIDATES_PATH}")
    cand = xr.open_dataset(CANDIDATES_PATH)
    point_index = cand.point_index.values.astype(int)
    lat_cand = cand.latitude.values.astype(float)
    n_cand = len(point_index)
    cand.close()
    print(f"  {n_cand} candidates")

    print(f"Loading harmonics: {HARMONICS_PATH}")
    h = xr.open_dataset(HARMONICS_PATH)
    cmaj_full = h.current_semimajor.values[VALID_IDX, :].astype(float)
    cmin_full = h.current_semiminor.values[VALID_IDX, :].astype(float)
    cinc_full = h.current_inclination.values[VALID_IDX, :].astype(float)
    cpha_full = h.current_phase.values[VALID_IDX, :].astype(float)
    h.close()
    # Extract candidate rows; result shape (n_cand, n_con)
    cmaj = cmaj_full[:, point_index].T
    cmin = cmin_full[:, point_index].T
    cinc = cinc_full[:, point_index].T
    cpha = cpha_full[:, point_index].T
    del cmaj_full, cmin_full, cinc_full, cpha_full

    print(f"Power curve: cut-in={V_CUT_IN:.2f}, rated={V_RATED:.2f} m/s, "
          f"P_rated={P_RATED_W:.0f} W")
    print(f"\nReconstructing {n_cand} candidates (n_jobs={N_JOBS}, batch={BATCH_SIZE})")

    batch_starts = list(range(0, n_cand, BATCH_SIZE))
    t0 = time.perf_counter()
    results = Parallel(n_jobs=N_JOBS, verbose=5)(
        delayed(_process_batch)(
            cmaj[s:s + BATCH_SIZE], cmin[s:s + BATCH_SIZE],
            cinc[s:s + BATCH_SIZE], cpha[s:s + BATCH_SIZE],
            lat_cand[s:s + BATCH_SIZE],
        )
        for s in batch_starts
    )
    elapsed_recon = time.perf_counter() - t0
    power_matrix = np.concatenate(results, axis=0)   # (n_cand, n_times) float32
    print(f"Reconstruction: {elapsed_recon/60:.1f} min, "
          f"power matrix {power_matrix.shape} ({power_matrix.nbytes/1e6:.0f} MB)")

    # Covariance: rows-as-times, cols-as-sites (matches MATLAB cov(power))
    print(f"\nComputing covariance ({n_cand} x {n_cand}) in double precision...")
    t1 = time.perf_counter()
    Sigma = np.cov(power_matrix.astype(np.float64), rowvar=True)
    elapsed_cov = time.perf_counter() - t1
    print(f"  Done in {elapsed_cov:.1f} s")
    print(f"  Size: {Sigma.nbytes/1e6:.0f} MB")
    print(f"  Symmetric: {np.allclose(Sigma, Sigma.T)}")
    print(f"  Variance range: [{np.diag(Sigma).min():.2f}, {np.diag(Sigma).max():.2f}] W^2")

    # --- Write NetCDF (schema matches compute_covariance.m output) ---
    print(f"\nSaving: {OUTPUT_PATH}")
    out = xr.Dataset(
        {
            "covariance": (
                ["site_i", "site_j"],
                Sigma,
                {"units": "W^2", "long_name": "Power output covariance matrix"},
            ),
        },
        attrs={
            "title": "Covariance matrix of tidal power output",
            "source": "utide (Pawlowicz et al., 2002) from ROMS harmonics",
            "n_candidates": n_cand,
            "n_timesteps": N_TIMES,
            "reconstruction_year": "2013",
            "time_step_hours": 1,
            "power_curve": f"VP Lewis: Cp={CP:.2f}, Vci={V_CUT_IN:.2f}, Vr={V_RATED:.2f} m/s",
            "P_rated_W": P_RATED_W,
            "constituents": ", ".join(VALID_NAMES),
            "created": datetime.now(timezone.utc).isoformat(),
        },
    )
    encoding = {"covariance": {"zlib": True, "complevel": 4}}
    out.to_netcdf(OUTPUT_PATH, encoding=encoding)
    print(f"Saved: {os.path.getsize(OUTPUT_PATH)/1e6:.1f} MB")
    print(f"Total time: {(elapsed_recon + elapsed_cov)/60:.1f} min")


if __name__ == "__main__":
    main()
