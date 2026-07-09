"""
Step 9: Apply the locked v_rated rule to produce the variant table.

Locked rule (see EXPERIMENT.md):
  v_rated = p99.5 of per-site max_speed on the device's eligible set:
    D = 5 (baseline):  depth >= 10 m  (full Gen5 candidate pool)
    D in {2, 3, 4}:    depth in [2D, 10) m  (incremental shallow band)
  P_rated  = 0.5 * rho * A * Cp * v_rated^3
  v_cut_in = 0.30 * v_rated

Rule selection (sweep evidence for the p99.5 choice) is in
08_test_vrated_rules.py — this script just applies the locked result.

Inputs:  ../results/harmonics.nc  (depth)
         ../results/histograms.nc (per-site max_speed)
Output:  stdout variant table reproducing the EXPERIMENT.md spec.
"""

import os
import numpy as np
import xarray as xr

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "results"))
HARMONICS_PATH = os.path.join(RESULTS_DIR, "harmonics.nc")
HISTOGRAM_PATH = os.path.join(RESULTS_DIR, "histograms.nc")

RHO = 1025.0          # kg/m^3 seawater
CP = 0.37             # Lewis 2021, 14-device population mean
PCT = 99.5            # locked percentile
CUT_RATIO = 0.30      # Lewis 2021 mean v_cut_in / v_rated
GEN5_FLOOR_M = 10.0   # baseline floor and ceiling of the incremental band

DIAMETERS = [2.0, 3.0, 4.0, 5.0]


def eligible_mask(depth, D):
    floor = 2.0 * D
    if D >= 5.0:
        return depth >= floor
    return (depth >= floor) & (depth < GEN5_FLOOR_M)


def main():
    depth = xr.open_dataset(HARMONICS_PATH)["depth"].values
    max_speed = xr.open_dataset(HISTOGRAM_PATH)["max_speed"].values

    print(f"  {'D':>3} {'band (m)':>11} {'n_sites':>10} "
          f"{'v_rated':>9} {'v_cut_in':>10} {'P_rated_kW':>12}")
    for D in DIAMETERS:
        mask = eligible_mask(depth, D)
        u = max_speed[mask]
        v_rated = float(np.percentile(u, PCT))
        v_cut_in = CUT_RATIO * v_rated
        A = np.pi * (D / 2) ** 2
        P_rated_kw = 0.5 * RHO * A * CP * v_rated ** 3 / 1000.0
        band = f"[{2*D:.0f}, 10)" if D < 5 else "[10, inf)"
        print(f"  {D:>3.0f} {band:>11} {mask.sum():>10,} "
              f"{v_rated:>9.2f} {v_cut_in:>10.2f} {P_rated_kw:>12.1f}")


if __name__ == "__main__":
    main()
