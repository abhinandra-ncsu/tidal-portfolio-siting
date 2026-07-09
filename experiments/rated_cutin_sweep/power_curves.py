#!/usr/bin/env python
"""
Power-curve views for the rated x cut-in sweep.

  power_curves.png   all 15 (v_rated, v_cut_in) power curves, analytical.
                     color = v_rated, linestyle = v_cut_in, gen5 bold black.

  band table (stdout + bands_table.csv)   for each of the 15 designs, the
                     fraction of the year the current spends IDLE (< cut-in),
                     RAMPING (cut-in..rated, the cubic part) and PLATEAU
                     (>= rated). Each design is scored on ITS OWN candidate
                     pool's speed histogram (vrX_vciY/candidates.nc), so the
                     table reads as the design *as deployed*, not a controlled
                     rating sweep.

The curves need no run data (pure cube law); the band table reads each design's
candidates.nc. Region edges use the same bin-center test as the screen's
compute_power_curve, so the splits are consistent with how CF is computed.

Read-only. Usage:  python power_curves.py [SWEEP_ROOT]
Defaults SWEEP_ROOT to results/vp/rated_cutin_sweep relative to the repo.
"""
import glob
import os
import sys

import numpy as np
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(os.path.dirname(_HERE))
DEFAULT_ROOT = os.path.join(_REPO, "results", "vp", "rated_cutin_sweep")

# Held constant across the family (config.py, gen5 rotor geometry).
RHO, AREA, CP = 1025.0, 19.63, 0.37
VR0, VCI0 = 2.03, 0.61                       # the as-built gen5 baseline

# Same palette as plot_sweep.py so the two figures read consistently.
PALETTE = ["tab:blue", "tab:orange", "tab:purple", "tab:green", "tab:brown"]


def p_turbine_kw(v, vr, vci):
    """VP power curve, kW per turbine: 0 below cut-in, cubic to rated, flat at
    P_rated above (no cut-out)."""
    p_rated = 0.5 * RHO * AREA * CP * vr ** 3
    p = np.where(v < vci, 0.0,
                 np.where(v <= vr, 0.5 * RHO * AREA * CP * v ** 3, p_rated))
    return p / 1000.0


def plot_curves(vrs, vcis, path):
    vr_color = {vr: PALETTE[i % len(PALETTE)] for i, vr in enumerate(vrs)}
    vci_style = {vci: s for vci, s in zip(vcis, ["-", "--", ":"])}
    v = np.linspace(0, 3.0, 600)
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for vr in vrs:
        for vci in vcis:
            y = p_turbine_kw(v, vr, vci)
            if np.isclose(vr, VR0) and np.isclose(vci, VCI0):
                ax.plot(v, y, color="black", lw=2.8, zorder=6)
            else:
                ax.plot(v, y, color=vr_color[vr], ls=vci_style[vci],
                        lw=1.4, alpha=0.9, zorder=3)
        # name each rating at its plateau (right edge)
        yr = p_turbine_kw(np.array([3.0]), vr, VCI0)[0]
        col = "black" if np.isclose(vr, VR0) else vr_color[vr]
        ax.annotate(f"{vr:g}", (3.0, yr), textcoords="offset points",
                    xytext=(5, 0), fontsize=8, color=col, va="center",
                    fontweight="bold" if np.isclose(vr, VR0) else "normal")
    ax.set_xlabel("current speed  v = |u|  (m/s)")
    ax.set_ylabel("power per turbine (kW)")
    ax.set_title("VP power curves -- 5 v_rated x 3 v_cut_in\n"
                 "color = v_rated, linestyle = v_cut_in, gen5 bold black")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 3.2)
    ax.set_ylim(bottom=0)

    # All 15 ride one cube-law envelope, so they collapse to 5 plateaus at this
    # scale -- the 3 cut-ins differ only in the near-zero liftoff. Inset zooms
    # there so the cut-in spread (and the 15 curves) are visible.
    axins = ax.inset_axes([0.07, 0.46, 0.32, 0.40])
    for vr in vrs:
        for vci in vcis:
            y = p_turbine_kw(v, vr, vci)
            if np.isclose(vr, VR0) and np.isclose(vci, VCI0):
                axins.plot(v, y, color="black", lw=2.4, zorder=6)
            else:
                axins.plot(v, y, color=vr_color[vr], ls=vci_style[vci],
                           lw=1.3, alpha=0.9, zorder=3)
    for vci in vcis:
        axins.axvline(vci, color="gray", lw=0.6, ls=":", zorder=1)
    axins.set_xlim(0.30, 0.95)
    axins.set_ylim(0, 3.3)
    axins.set_title("cut-in liftoff (near-zero power)", fontsize=7.5)
    axins.tick_params(labelsize=6)
    ax.indicate_inset_zoom(axins, edgecolor="gray", alpha=0.4)

    handles = ([Line2D([0], [0], color="black", lw=2.8, label="gen5 (2.03 / 0.61)")]
               + [Line2D([0], [0], color=vr_color[vr], lw=1.8,
                         label=f"v_rated {vr:g}") for vr in vrs]
               + [Line2D([0], [0], color="gray", ls=vci_style[vci], lw=1.4,
                         label=f"cut-in {vci:g}") for vci in vcis])
    fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False,
               bbox_to_anchor=(0.5, -0.01), fontsize=8)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {os.path.basename(path)}")


def band_table(root):
    """Per-design idle/ramping/plateau fractions, each on its own candidates."""
    rows = []
    for d in sorted(glob.glob(os.path.join(root, "vr*_vci*"))):
        cpath = os.path.join(d, "candidates.nc")
        if not os.path.isfile(cpath):
            continue
        name = os.path.basename(d)
        vr = float(name.split("_")[0][2:])      # vr2.03 -> 2.03
        vci = float(name.split("_")[1][3:])     # vci0.61 -> 0.61
        ds = xr.open_dataset(cpath)
        c = ds["speed_bin_centers"].values
        dens = ds["speed_histogram"].mean(dim="site").values
        dens = dens / dens.sum()                # pooled time-density f(v)
        idle = dens[c < vci].sum()
        ramping = dens[(c >= vci) & (c <= vr)].sum()
        plateau = dens[c > vr].sum()
        rows.append({
            "v_rated": vr, "v_cut_in": vci, "n_sites": int(ds.sizes["site"]),
            "mean_speed": float(ds["mean_speed"].mean()),
            "idle": idle, "ramping": ramping, "plateau": plateau,
        })
        ds.close()
    rows.sort(key=lambda r: (r["v_rated"], r["v_cut_in"]))

    # CSV
    csv_path = os.path.join(root, "bands_table.csv")
    with open(csv_path, "w", encoding="utf-8") as fh:
        fh.write("v_rated,v_cut_in,n_sites,mean_speed_ms,idle_pct,ramping_pct,plateau_pct\n")
        for r in rows:
            fh.write(f"{r['v_rated']:.2f},{r['v_cut_in']:.2f},{r['n_sites']},"
                     f"{r['mean_speed']:.3f},{100*r['idle']:.1f},"
                     f"{100*r['ramping']:.1f},{100*r['plateau']:.1f}\n")
    print(f"Wrote {os.path.basename(csv_path)}\n")

    # Markdown (ASCII-safe for Windows consoles)
    print("| design (v_rated / v_cut_in) | mean speed (m/s) | "
          "idle (<cut-in) | ramping (cubic) | plateau (>=rated) |")
    print("|---|---:|---:|---:|---:|")
    for r in rows:
        tag = "**{:.2f} / {:.2f}**".format(r["v_rated"], r["v_cut_in"]) \
            if (np.isclose(r["v_rated"], VR0) and np.isclose(r["v_cut_in"], VCI0)) \
            else "{:.2f} / {:.2f}".format(r["v_rated"], r["v_cut_in"])
        print(f"| {tag} | {r['mean_speed']:.2f} | "
              f"{100*r['idle']:.1f}% | {100*r['ramping']:.1f}% | "
              f"{100*r['plateau']:.1f}% |")


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROOT
    vrs = [1.50, 1.75, 2.03, 2.30, 2.60]        # swept ratings (config / EXPERIMENT.md)
    vcis = [0.40, 0.61, 0.80]                   # swept cut-ins
    plot_curves(vrs, vcis, os.path.join(root, "power_curves.png"))
    band_table(root)
    print(f"\nSweep root: {root}")


if __name__ == "__main__":
    main()
