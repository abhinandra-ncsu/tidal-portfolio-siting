#!/usr/bin/env python
"""
Two per-capacity plots for the rated x cut-in sweep, reading the long-form
results_table.csv written by summarize.py:

  cv_vs_lcoe.png      CV (steadiness) vs LCOE target, one panel per capacity
  energy_vs_lcoe.png  delivered energy vs LCOE target, one panel per capacity

Each (v_rated, v_cut_in) cell is one line, traced over its feasible LCOE band --
a cell's line simply starts at the cheapest LCOE where it can be built, so
feasibility shows up as where the line begins. Color = v_rated (5 distinct hues),
linestyle = v_cut_in; gen5 (2.03 / 0.61) is bold black, the baseline.

These plots answer one question: does gen5 beat the others? To make that a glance
rather than a 15-line decode, gen5's curve shades the panel into a BETTER and a
WORSE half, colored by outcome: green is the half where a competitor beats gen5
(the good direction), pink the half where gen5 wins. The good direction differs
by metric, so green flips sides: lower CV is steadier (green BELOW gen5's CV
curve), higher energy is more (green ABOVE its energy curve). The shading spans
only gen5's own feasible LCOE band -- left of it, gen5 cannot be built, so no
comparison exists.

Why TWO plots and not one verdict. At a fixed installed capacity the optimizer
buys steadiness by selecting lower-CF sites as the LCOE ceiling relaxes, so it
trades delivered energy for a lower CV. CV-vs-LCOE shows steadiness-per-cost;
energy-vs-LCOE shows what that steadiness costs in MWh. Read both at one vertical
(cost) line. The cost constraint binds (achieved ~ target to <0.5%), so the swept
target is an honest x-axis. CV (not raw variance) because variance scales with
mean output, which differs across cells; CV = sigma / mean normalizes that out.

Read-only. Usage:
  python plot_sweep.py [SWEEP_ROOT]
Defaults SWEEP_ROOT to results/vp/rated_cutin_sweep relative to the repo.
"""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import MultipleLocator

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(os.path.dirname(_HERE))
DEFAULT_ROOT = os.path.join(_REPO, "results", "vp", "rated_cutin_sweep")

VR0, VCI0 = 2.03, 0.61          # the as-built gen5 baseline curve
HOURS_PER_YEAR = 8760.0

# 5 distinct hues for the ratings (qualitative, well-separated); gen5 overrides
# to black, and its rating family (2.03 at the other cut-ins) is gray so it
# reads as "baseline rating, alternate cut-in" rather than a separate design.
# tab:* avoids the viridis green-on-green that made ratings blur.
PALETTE = ["tab:blue", "tab:orange", "tab:gray", "tab:green", "tab:brown"]
BETTER, WORSE = "#4caf50", "#e57373"   # beats-gen5 (green) / gen5-wins (pink) tint


def load(root):
    """Optimal rows only, with CV and energy(GWh) appended."""
    df = pd.read_csv(os.path.join(root, "results_table.csv"))
    df = df[df["status"] == "optimal"].copy()
    sigma = np.sqrt(df["variance_w2"].values)                 # std-dev of aggregate power [W]
    mean_w = df["total_energy_mwh"].values * 1e6 / HOURS_PER_YEAR
    df["cv"] = sigma / mean_w
    df["energy_gwh"] = df["total_energy_mwh"].values / 1e3
    return df


def _cell(df, vr, vci, cap):
    """The one cell's rows, sorted by LCOE (may be empty if never feasible)."""
    m = (np.isclose(df["v_rated"], vr) & np.isclose(df["v_cut_in"], vci)
         & np.isclose(df["capacity_mw"], cap))
    return df[m].sort_values("lcoe_target")


def plot_metric(df, caps, vrs, vcis, ycol, ylabel, title, path, lower_is_better):
    """One figure: a panel per capacity, a line per (v_rated, v_cut_in) cell.
    Color = v_rated, linestyle = v_cut_in; gen5 bold black. gen5's curve shades
    the panel into a better (green = beats gen5) and worse (pink = gen5 wins)
    half so 'does gen5 beat the others' reads off the shading rather than off
    15 lines."""
    vr_color = {vr: PALETTE[i % len(PALETTE)] for i, vr in enumerate(vrs)}
    vci_style = {vci: s for vci, s in zip(vcis, ["-", "--", ":"])}
    # 2x2 grid, not 1x4: the doc renders the image at text width, so panels
    # two-across are twice the size and the $100-step LCOE axis stays legible.
    ncols = 2
    nrows = int(np.ceil(len(caps) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(6.4 * ncols, 4.6 * nrows),
                             squeeze=False)
    flat = axes.ravel()
    for ax in flat[len(caps):]:        # blank any unused trailing panel
        ax.set_visible(False)
    for ax, cap in zip(flat, caps):
        # --- the 15 cell lines -------------------------------------------
        for vr in vrs:
            for vci in vcis:
                sub = _cell(df, vr, vci, cap)
                if sub.empty:
                    continue
                x, y = sub["lcoe_target"].values, sub[ycol].values
                if np.isclose(vr, VR0) and np.isclose(vci, VCI0):
                    ax.plot(x, y, color="black", lw=2.8, marker="o", ms=3, zorder=6)
                else:
                    ax.plot(x, y, color=vr_color[vr], ls=vci_style[vci],
                            lw=1.3, alpha=0.9, marker="o", ms=2, zorder=3)
        # --- gen5 win/lose shading, over gen5's own feasible LCOE span ----
        g = _cell(df, VR0, VCI0, cap)
        if len(g) >= 2:
            gx, gy = g["lcoe_target"].values, g[ycol].values
            y0, y1 = ax.get_ylim()
            top, bot = (WORSE, BETTER) if lower_is_better else (BETTER, WORSE)
            ax.fill_between(gx, gy, y1, color=top, alpha=0.12, lw=0, zorder=0)
            ax.fill_between(gx, gy, y0, color=bot, alpha=0.12, lw=0, zorder=0)
            ax.set_ylim(y0, y1)
        # --- name each rating at the right edge (its vci=0.61 endpoint) ---
        for vr in vrs:
            s = _cell(df, vr, VCI0, cap)
            if s.empty:
                continue
            xe, ye = s["lcoe_target"].values[-1], s[ycol].values[-1]
            col = "black" if np.isclose(vr, VR0) else vr_color[vr]
            ax.annotate(f"{vr:g}", (xe, ye), textcoords="offset points",
                        xytext=(5, 0), fontsize=7.5, color=col, va="center",
                        fontweight="bold" if np.isclose(vr, VR0) else "normal")
        ax.set_title(f"{cap:g} MW")
        ax.set_xlabel("LCOE target ($/MWh)")
        ax.set_ylabel(ylabel)
        ax.xaxis.set_major_locator(MultipleLocator(200))   # $200 labels,
        ax.xaxis.set_minor_locator(MultipleLocator(100))   # $100 gridlines
        ax.grid(True, alpha=0.3)
        ax.grid(True, which="minor", alpha=0.12)
    # --- legend: gen5, cut-in styles, and what the shading means ----------
    better_txt = "beats gen5 (steadier)" if lower_is_better else "beats gen5 (more energy)"
    worse_txt = "gen5 wins"
    handles = ([Line2D([0], [0], color="black", lw=2.8, marker="o", ms=3,
                       label="gen5 (2.03/0.61), rating labels at right")]
               + [Line2D([0], [0], color="gray", ls=vci_style[vci], lw=1.5,
                         label=f"cut-in {vci:g}") for vci in vcis]
               + [Patch(facecolor=BETTER, alpha=0.4, label=better_txt),
                  Patch(facecolor=WORSE, alpha=0.4, label=worse_txt)])
    fig.suptitle(title, y=1.02)
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, -0.04), fontsize=9)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROOT
    df = load(root)
    caps = sorted(df["capacity_mw"].unique())
    vrs = sorted(df["v_rated"].unique())
    vcis = sorted(df["v_cut_in"].unique())

    plot_metric(df, caps, vrs, vcis, "cv", "CV  (lower = steadier)",
                "Portfolio steadiness vs cost  --  CV vs LCOE per capacity  (color = v_rated, gen5 bold black)",
                os.path.join(root, "cv_vs_lcoe.png"), lower_is_better=True)
    plot_metric(df, caps, vrs, vcis, "energy_gwh", "energy delivered (GWh/yr)",
                "Delivered energy vs cost  --  energy vs LCOE per capacity  (color = v_rated, gen5 bold black)",
                os.path.join(root, "energy_vs_lcoe.png"), lower_is_better=False)

    print(f"Sweep root: {root}")
    print("Wrote cv_vs_lcoe.png, energy_vs_lcoe.png")


if __name__ == "__main__":
    main()
