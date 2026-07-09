#!/usr/bin/env python
"""
Roll up the rated × cut-in sweep into one comparative table.

The per-cell optimization_results.nc files hold the answer, but scattered across
60 directories. This walks the sweep tree and collapses each
(v_rated, v_cut_in, capacity, LCOE) cell into one row so the effect of the two
swept design speeds is visible at a glance — how the candidate count, the
optimal portfolio variance, the delivered energy and the achieved LCOE move as
v_rated and v_cut_in change.

Read-only. Safe to run mid-sweep — cells without a result yet are skipped, and a
note is printed for partially-complete curves.

Outputs (to the sweep root):
  results_table.csv   one row per (v_rated, v_cut_in, capacity, LCOE target)

Usage:
  python summarize.py [SWEEP_ROOT]
Defaults SWEEP_ROOT to results/vp/rated_cutin_sweep relative to the repo.
"""
import os
import re
import sys

import numpy as np
import pandas as pd
import xarray as xr

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(os.path.dirname(_HERE))
DEFAULT_ROOT = os.path.join(_REPO, "results", "vp", "rated_cutin_sweep")

# Rated power is the physical quantity the sweep varies (P_rated = ½ρACp·v_rated³),
# but it's not stored in the .nc — derive it per curve from the parsed v_rated using
# the SAME constants the engine uses (single-sourced from config, no magic number).
# The sweep is gen5 with rotor geometry held fixed, so area is pinned to gen5.
sys.path.insert(0, os.path.join(_REPO, "optimization", "vp"))
from config.config import VARIANTS, RHO, CP, TURBINES_PER_TF  # noqa: E402
_AREA = VARIANTS["gen5"]["area"]


def rated_power_kw(v_rated):
    """(per-turbine, per-TriFrame) rated power in kW for a swept rated speed."""
    p_turbine = 0.5 * RHO * _AREA * CP * v_rated ** 3 / 1000.0
    return round(p_turbine, 3), round(p_turbine * TURBINES_PER_TF, 3)


_CURVE_RE = re.compile(r"^vr(?P<vr>[0-9.]+)_vci(?P<vci>[0-9.]+)$")
_MW_RE = re.compile(r"^(?P<mw>[0-9_]+)mw$")


def _mw_value(seg):
    """'25mw' -> 25.0 ; '5_25mw' -> 5.25 (inverse of config._mw_label)."""
    m = _MW_RE.match(seg)
    if not m:
        return None
    return float(m.group("mw").replace("_", "."))


def collect(root):
    """Walk the sweep tree, returning a long-form DataFrame (one row per
    (curve, capacity, LCOE target)) and a list of human-readable status notes."""
    rows = []
    notes = []
    curves = sorted(
        d for d in os.listdir(root) if _CURVE_RE.match(d)
    ) if os.path.isdir(root) else []
    if not curves:
        notes.append(f"No curve directories (vr*_vci*) under {root}")

    for curve in curves:
        m = _CURVE_RE.match(curve)
        vr, vci = float(m.group("vr")), float(m.group("vci"))
        p_turb_kw, p_tf_kw = rated_power_kw(vr)   # cube-law rating that v_rated sets
        cdir = os.path.join(root, curve)

        # Candidate count (shared across this curve's capacities).
        n_cand = np.nan
        cand_path = os.path.join(cdir, "candidates.nc")
        if os.path.isfile(cand_path):
            with xr.open_dataset(cand_path) as cand:
                n_cand = int(cand.sizes["site"])
        else:
            notes.append(f"{curve}: no candidates.nc (screen not done)")

        mw_dirs = sorted(
            (d for d in os.listdir(cdir) if _MW_RE.match(d)),
            key=lambda d: _mw_value(d),
        )
        n_done = 0
        for mwd in mw_dirs:
            mw = _mw_value(mwd)
            res_path = os.path.join(cdir, mwd, "optimization_results.nc")
            if not os.path.isfile(res_path):
                continue
            n_done += 1
            with xr.open_dataset(res_path) as ds:
                N = int(ds.attrs.get("N_triframes", -1))
                lcoe_t = ds["lcoe_target"].values
                status = ds["status"].values.astype(str)
                variance = ds["variance"].values
                achieved = ds["achieved_lcoe"].values
                # Derive per-target selection count and delivered energy from the
                # per-site energy and the (target × site) selection matrix.
                sel = ds["selected"].values                      # (target, site)
                e_site = ds["energy_mwh"].values                 # (site,)
                n_sel = sel.sum(axis=1)
                total_e = sel @ e_site
            for k in range(len(lcoe_t)):
                rows.append({
                    "v_rated": vr,
                    "v_cut_in": vci,
                    "p_rated_turbine_kw": p_turb_kw,
                    "p_rated_triframe_kw": p_tf_kw,
                    "n_candidates": n_cand,
                    "capacity_mw": mw,
                    "N_triframes": N,
                    "lcoe_target": float(lcoe_t[k]),
                    "status": status[k],
                    "n_selected": int(n_sel[k]),
                    "variance_w2": float(variance[k]),
                    "total_energy_mwh": float(total_e[k]),
                    "achieved_lcoe": float(achieved[k]),
                })
        if mw_dirs and n_done < 4:
            notes.append(f"{curve}: {n_done}/4 capacities solved")

    cols = ["v_rated", "v_cut_in", "p_rated_turbine_kw", "p_rated_triframe_kw",
            "n_candidates", "capacity_mw", "N_triframes",
            "lcoe_target", "status", "n_selected", "variance_w2",
            "total_energy_mwh", "achieved_lcoe"]
    df = pd.DataFrame(rows, columns=cols)
    if not df.empty:
        df = df.sort_values(
            ["v_rated", "v_cut_in", "capacity_mw", "lcoe_target"]
        ).reset_index(drop=True)
    return df, notes


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROOT
    df, notes = collect(root)

    out_csv = os.path.join(root, "results_table.csv")
    df.to_csv(out_csv, index=False)

    n_curves = df[["v_rated", "v_cut_in"]].drop_duplicates().shape[0] if not df.empty else 0
    n_cells = df[["v_rated", "v_cut_in", "capacity_mw"]].drop_duplicates().shape[0] if not df.empty else 0
    print(f"Sweep root: {root}")
    print(f"Wrote {out_csv}")
    print(f"  {len(df)} rows  |  {n_curves}/15 curves  |  {n_cells}/60 cells with results")

    if not df.empty:
        # n_candidates per curve — shows the screen's sensitivity to the speeds.
        print("\n=== candidate count per (v_rated, v_cut_in) ===")
        cc = (df.groupby(["v_rated", "v_cut_in"])
                .agg(p_rated_turbine_kw=("p_rated_turbine_kw", "first"),
                     p_rated_triframe_kw=("p_rated_triframe_kw", "first"),
                     n_candidates=("n_candidates", "first"),
                     N_triframes=("N_triframes", "first"))
                .reset_index())
        print(cc.to_string(index=False))

        # Portfolio variance pivot at a representative LCOE target, per capacity.
        # (Variance is the experiment's real output once the LCOE constraint binds.)
        for cap in sorted(df["capacity_mw"].unique()):
            sub = df[(df["capacity_mw"] == cap) & (df["status"] == "optimal")]
            if sub.empty:
                continue
            piv = sub.pivot_table(index="v_rated", columns="v_cut_in",
                                  values="variance_w2", aggfunc="min")
            print(f"\n=== min portfolio variance (W^2) — {cap:g} MW, optimal cells ===")
            print(piv.to_string())

    if notes:
        print("\n=== notes (incomplete cells) ===")
        for n in notes:
            print(f"  - {n}")


if __name__ == "__main__":
    main()
