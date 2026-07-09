"""
Step 3: Compute pure capacity factor from speed histograms.

Pure CF = Σ_k P(u_k) × p_i(u_k) / P_rated

where P(u) is the Verdant Power Gen5 power curve (cubic between cut-in and
rated, flat at P_r above rated, zero outside) and p_i(u_k) is the bin
probability from histograms.nc.

No availability factor, no transmission loss — see
../../optimization/vp/methodology/energy/methodology.md for the
deployment-level (net) form.

Input:  histograms.nc   (from build_histograms.m)
Output: cf.nc           (lon, lat, depth, cf)
"""

import os

import numpy as np
import xarray as xr

# --- Paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(SCRIPT_DIR, "histograms.nc")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "cf.nc")

# --- Gen5 turbine spec (optimization/vp/methodology/turbine_design_specification.md) ---
RHO = 1025.0       # kg/m^3, seawater density
DIAMETER_M = 5.0
SWEPT_AREA_M2 = np.pi * (DIAMETER_M / 2) ** 2   # 19.635 m^2
CP = 0.37
P_RATED_W = 35_000.0
V_CUT_IN = 0.63
V_RATED = 2.11
V_CUT_OUT = 4.57


def power_curve(u):
    """Gen5 KHPS power curve, W. Vectorized."""
    p = np.zeros_like(u, dtype=np.float64)
    cubic = (u >= V_CUT_IN) & (u <= V_RATED)
    rated = (u > V_RATED) & (u <= V_CUT_OUT)
    p[cubic] = 0.5 * RHO * SWEPT_AREA_M2 * CP * u[cubic] ** 3
    p[rated] = P_RATED_W
    return p


def main():
    if os.path.exists(OUTPUT_PATH):
        print(f"Already exists: {OUTPUT_PATH}")
        print("Delete to re-run.")
        return

    print(f"Reading: {INPUT_PATH}")
    ds = xr.open_dataset(INPUT_PATH)

    lon = ds.longitude.values
    lat = ds.latitude.values
    depth = ds.depth.values
    bin_centers = ds.speed_bin_centers.values         # (100,)
    hist = ds.speed_histogram.values                  # (point, speed_bin) or transposed
    if hist.shape[0] == bin_centers.size:
        hist = hist.T                                  # ensure (point, speed_bin)
    ds.close()

    n_pts = lon.size
    print(f"  {n_pts:,} points, {bin_centers.size} bins")

    # P(u_k) at each bin center — same for every site
    p_bin = power_curve(bin_centers)                  # (100,) W

    # mean power per site = Σ_k P(u_k) p_i(u_k)
    mean_power = hist @ p_bin                          # (n_pts,) W
    cf = mean_power / P_RATED_W

    print(f"  CF range: {cf.min():.4f} to {cf.max():.4f}")
    print(f"  CF mean:  {cf.mean():.4f}, median: {np.median(cf):.4f}")
    print(f"  P50/P90/P99: {np.percentile(cf, [50, 90, 99])}")

    out = xr.Dataset(
        {
            "longitude": (["point"], lon, {"units": "degrees_east"}),
            "latitude":  (["point"], lat, {"units": "degrees_north"}),
            "depth":     (["point"], depth.astype(np.float32), {"units": "m"}),
            "cf":        (["point"], cf.astype(np.float32),
                          {"units": "1", "long_name": "Pure capacity factor"}),
        },
        attrs={
            "title": "Pure capacity factor — Verdant Gen5 KHPS, US East Coast",
            "turbine": "Verdant Power Gen5 KHPS (D=5 m, Pr=35 kW)",
            "cf_definition": "pure: mean(P(u))/Pr, no availability, no transmission loss",
            "v_cut_in_m_s": V_CUT_IN,
            "v_rated_m_s": V_RATED,
            "v_cut_out_m_s": V_CUT_OUT,
            "p_rated_w": P_RATED_W,
            "cp": CP,
            "source_histogram": "histograms.nc (T_TIDE t_predic, 2013 hourly)",
            "n_points": int(n_pts),
        },
    )
    encoding = {"cf": {"zlib": True, "complevel": 4}}
    out.to_netcdf(OUTPUT_PATH, encoding=encoding)
    print(f"Saved: {OUTPUT_PATH} ({os.path.getsize(OUTPUT_PATH) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
