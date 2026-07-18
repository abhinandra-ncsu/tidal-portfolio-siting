"""Aggregate campaign 06 (ORPC baseline) into one per-cell/per-target CSV.

Run on energizelab:
  .venv\Scripts\python.exe aggregate_orpc.py <path-to-06_orpc_baseline/results>

Prints a readable table and writes orpc_cell_summary.csv next to run_summary.txt.
Mirrors the quantities the VP campaign's cell_summary.csv carries: status,
achieved LCOE, variance, portfolio energy, CV, selected-site count, median
selected CF, and the northern (>=41N) fraction.
"""
import csv
import os
import sys

import numpy as np
import xarray as xr

root = sys.argv[1]

pool_path = os.path.join(root, "shared", "candidates.nc")
with xr.open_dataset(pool_path) as pool:
    n_pool = pool.sizes[list(pool.sizes)[0]]
print(f"candidate pool: {n_pool} sites\n")

rows = []
for arm in ("6600v", "480v"):
    for mw in (5, 10, 25, 100):
        path = os.path.join(root, arm, f"{mw}mw", "optimization_results.nc")
        if not os.path.exists(path):
            print(f"MISSING: {path}")
            continue
        ds = xr.open_dataset(path)
        n_dev = int(ds.attrs["N_devices"])
        for t in range(ds.sizes["target"]):
            target = float(ds["lcoe_target"][t])
            status = str(ds["status"][t].values)
            sel = ds["selected"][t].values.astype(bool)
            feasible = status.lower() in ("optimal", "suboptimal") and sel.any()
            if feasible:
                variance = float(ds["variance"][t])
                achieved = float(ds["achieved_lcoe"][t])
                energy = float(ds["energy_mwh"].values[sel].sum())
                mean_w = energy * 1e6 / 8760.0
                cv = float(np.sqrt(variance) / mean_w)
                lat_sel = ds["latitude"].values[sel]
                frac_north = float((lat_sel >= 41.0).mean())
                cf_med = float(np.median(ds["capacity_factor"].values[sel]))
                n_sel = int(sel.sum())
            else:
                variance = achieved = energy = cv = frac_north = cf_med = float("nan")
                n_sel = 0
            rows.append(dict(
                arm=arm, mw=mw, n_devices=n_dev, lcoe_target=target,
                status=status, achieved_lcoe=achieved, variance_w2=variance,
                energy_mwh=energy, cv=cv, n_selected=n_sel,
                cf_sel_median=cf_med, frac_north=frac_north,
            ))
        ds.close()

out = os.path.join(root, "orpc_cell_summary.csv")
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"wrote {out}  ({len(rows)} rows)\n")

fmt = ("{arm:>6} {mw:>4} {lcoe_target:>6.0f} {status:>12} {achieved_lcoe:>9.1f} "
       "{variance_w2:>12.4g} {energy_mwh:>12.1f} {cv:>7.3f} {n_selected:>6} "
       "{cf_sel_median:>7.3f} {frac_north:>6.2f}")
print(f"{'arm':>6} {'MW':>4} {'L':>6} {'status':>12} {'achLCOE':>9} "
      f"{'variance':>12} {'MWh/yr':>12} {'CV':>7} {'nsel':>6} {'CFmed':>7} {'fN41':>6}")
for r in rows:
    print(fmt.format(**r))
