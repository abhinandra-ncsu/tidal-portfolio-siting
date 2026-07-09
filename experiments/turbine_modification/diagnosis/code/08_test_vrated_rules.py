"""
Step 8: Test candidate rules for v_rated(D).

User wants v_rated to vary with D, derived from the resource of each device's
eligible site set (depth >= 2D). Each candidate rule is a (percentile,
multiplier) pair applied to per-site max_speed.

Two questions answered:
  Q1: Do the four eligible sets actually differ in their max_speed distributions?
  Q2: Which (percentile, multiplier) rule reproduces Gen5's 2.11 m/s at D=5
      and gives sensible v_rated for D = 2, 3, 4?

Output: stdout tables. No file output.
"""

import os
import numpy as np
import xarray as xr

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "results"))
HARMONICS_PATH = os.path.join(RESULTS_DIR, "harmonics.nc")
HISTOGRAM_PATH = os.path.join(RESULTS_DIR, "histograms.nc")

DIAMETERS = [2.0, 3.0, 4.0, 5.0]
PERCENTILES = [50, 75, 90, 95, 99, 99.5, 99.9]
MULTIPLIERS = [1.00, 0.97, 0.87]  # Lewis 2021: maxyield, neutral, high-CF

GEN5_TARGET = 2.11  # m/s — what we want the rule to reproduce at D=5


def main():
    harm = xr.open_dataset(HARMONICS_PATH)
    depth = harm["depth"].values
    hist_ds = xr.open_dataset(HISTOGRAM_PATH)
    max_speed = hist_ds["max_speed"].values
    print(f"  Loaded {len(max_speed):,} sites, max_speed in "
          f"[{max_speed.min():.2f}, {max_speed.max():.2f}] m/s")
    print()

    # ============================================================
    # Q1: Distribution of max_speed in each D's eligible set
    # ============================================================
    print("=" * 78)
    print("Q1: max_speed distribution across the four eligible sets")
    print("=" * 78)
    print(f"  {'D':>3} {'depth>=':>8} {'n_sites':>10} {'mean':>6} "
          f"{'p50':>6} {'p75':>6} {'p90':>6} {'p95':>6} {'p99':>6} "
          f"{'p99.5':>6} {'p99.9':>6} {'max':>6}")
    eligible_us = {}
    for D in DIAMETERS:
        floor = 2.0 * D
        mask = depth >= floor
        u = max_speed[mask]
        eligible_us[D] = u
        stats = [np.mean(u)] + [np.percentile(u, p) for p in PERCENTILES] + [u.max()]
        print(f"  {D:>3.0f} {floor:>7.0f}m {mask.sum():>10,} " +
              " ".join(f"{x:>6.2f}" for x in stats))
    print()

    # ============================================================
    # Q2: Candidate rules
    # ============================================================
    print("=" * 78)
    print(f"Q2: v_rated under each (percentile, multiplier) rule, by D")
    print(f"    Target at D=5: {GEN5_TARGET:.2f} m/s (reproduce Gen5)")
    print("=" * 78)
    print()
    for mult in MULTIPLIERS:
        print(f"--- multiplier = {mult:.2f} ---")
        header = f"  {'percentile':>10}" + "".join(f"{f'D={int(D)}':>9}" for D in DIAMETERS) + f" {'D=5 match?':>14}"
        print(header)
        for p in PERCENTILES:
            vr_by_D = [mult * np.percentile(eligible_us[D], p) for D in DIAMETERS]
            err = abs(vr_by_D[-1] - GEN5_TARGET)
            flag = ""
            if err < 0.05:
                flag = "<- EXACT"
            elif err < 0.15:
                flag = "<- close"
            row = f"  {f'p{p}':>10}" + "".join(f"{v:>9.2f}" for v in vr_by_D) + f" {flag:>14}"
            print(row)
        print()

    # ============================================================
    # Q3: Does the chosen rule give meaningful per-D variation?
    # ============================================================
    print("=" * 78)
    print("Q3: For each rule, how much does v_rated vary across D?")
    print("    (max - min across D=2..5 / value at D=5)")
    print("=" * 78)
    print(f"  {'rule':>20} {'D=5':>8} {'min(D)':>8} {'max(D)':>8} "
          f"{'spread':>8} {'spread%':>9}")
    for mult in MULTIPLIERS:
        for p in PERCENTILES:
            vr_by_D = np.array([mult * np.percentile(eligible_us[D], p) for D in DIAMETERS])
            spread = vr_by_D.max() - vr_by_D.min()
            spread_pct = 100.0 * spread / vr_by_D[-1]
            name = f"{mult:.2f} * p{p}"
            print(f"  {name:>20} {vr_by_D[-1]:>8.2f} {vr_by_D.min():>8.2f} "
                  f"{vr_by_D.max():>8.2f} {spread:>8.2f} {spread_pct:>8.1f}%")


if __name__ == "__main__":
    main()
