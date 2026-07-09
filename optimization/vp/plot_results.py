"""
Visualize portfolio optimization results.

Produces four plot types:
  1. Spatial site maps — one per LCOE target
  2. LCOE tradeoff plot — vs portfolio variance (min-variance objective) or
     vs portfolio annual energy (max-energy objective)
  3. Correlation heatmaps of selected sites (min-variance objective only —
     the max-energy objective never looks at the covariance structure)
  4. Cost breakdown bar chart

Input:  ../results/optimization_results.nc
        ../results/covariance.nc
        ../inputs/geography/NOAA_MedRes/allus80k.shp
Output: ../results/figures/
"""

import os

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

from config.config import get_results_dir, get_curve_dir, get_objective

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

RESULTS_DIR = get_results_dir()
RESULTS_PATH = os.path.join(RESULTS_DIR, "optimization_results.nc")
# covariance.nc is curve-level; read it from the shared curve dir, which
# falls back to RESULTS_DIR when unset.
COVARIANCE_PATH = os.path.join(get_curve_dir(), "covariance.nc")
SHORELINE_PATH = os.path.join(ROOT_DIR, "inputs", "geography", "NOAA_MedRes", "allus80k.shp")
FIG_DIR = os.path.join(RESULTS_DIR, "figures")


def load_data():
    """Load results, covariance, and shoreline."""
    res = xr.open_dataset(RESULTS_PATH)
    cov = xr.open_dataset(COVARIANCE_PATH)
    Sigma = cov["covariance"].values
    cov.close()

    shoreline = gpd.read_file(SHORELINE_PATH)
    return res, Sigma, shoreline


def get_optimal_targets(res):
    """Return indices and LCOE values for optimal solutions only."""
    status = res["status"].values
    lcoe = res["lcoe_target"].values
    mask = status == "optimal"
    return np.where(mask)[0], lcoe[mask]


# =========================================================================
# Plot 1: Spatial site maps
# =========================================================================

def plot_spatial_maps(res, shoreline):
    """One separate figure per LCOE target."""
    target_idx, target_lcoe = get_optimal_targets(res)
    if len(target_idx) == 0:
        print("  Skipped: no optimal solutions")
        return
    lat = res["latitude"].values
    lon = res["longitude"].values
    cf = res["capacity_factor"].values
    N = res.attrs["N_triframes"]

    for tidx, L in zip(target_idx, target_lcoe):
        fig, ax = plt.subplots(figsize=(8, 10))

        # Coastline
        shoreline.plot(ax=ax, color="0.85", linewidth=0.3)

        # All candidates (background)
        ax.scatter(lon, lat, s=1, c="0.80", alpha=0.3, zorder=1)

        # Selected sites
        sel = res["selected"].values[tidx].astype(bool)
        sc = ax.scatter(
            lon[sel], lat[sel], s=50, c=cf[sel],
            cmap="Blues", edgecolors="black", linewidths=0.5,
            vmin=0.05, vmax=0.7, zorder=2,
        )

        ax.set_xlim(lon.min() - 1, lon.max() + 1)
        ax.set_ylim(lat.min() - 1, lat.max() + 1)
        ax.set_title(f"Selected Sites — LCOE target: ${L:,.0f}/MWh "
                     f"(N={N})", fontsize=13, fontweight="bold")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_aspect("equal")

        cbar = fig.colorbar(sc, ax=ax, shrink=0.5, pad=0.02)
        cbar.set_label("Capacity Factor")

        fig.tight_layout()
        path = os.path.join(FIG_DIR, f"spatial_map_L{int(L)}.png")
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"  Saved: {path}")


# =========================================================================
# Plot 2: LCOE vs Variance Pareto
# =========================================================================

def plot_pareto(res):
    """Achieved LCOE vs the objective-relevant portfolio outcome.

    Min-variance objective: y is portfolio variance (the quantity minimized).
    Max-energy objective: y is portfolio annual energy (the quantity
    maximized) — variance is irrelevant to what the budget bought here.
    """
    target_idx, target_lcoe = get_optimal_targets(res)
    if len(target_idx) == 0:
        print("  Skipped: no optimal solutions")
        return
    achieved = res["achieved_lcoe"].values[target_idx]

    if get_objective() == "energy":
        # Portfolio annual energy = sum of delivered-to-shore energy over the
        # selected sites (same field the LCOE constraint and cost breakdown use).
        energy_all = res["energy_mwh"].values
        y = np.array([energy_all[res["selected"].values[t].astype(bool)].sum()
                      for t in target_idx])
        ylabel = "Portfolio Annual Energy (MWh/yr)"
        title = "Achieved LCOE vs Portfolio Energy"
        fname = "lcoe_vs_energy.png"
        sci_y = False
    else:
        y = res["variance"].values[target_idx]
        ylabel = "Portfolio Variance (W²)"
        title = "Cost–Variance Tradeoff"
        fname = "lcoe_vs_variance.png"
        sci_y = True

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(achieved, y, "o--", color="steelblue", markersize=8,
            markeredgecolor="black", markeredgewidth=0.5, linewidth=1.5)

    # Per-point budget labels are readable for the coarse grid but turn to mush
    # on a fine frontier sweep — annotate only when the cells are few.
    if len(target_lcoe) <= 12:
        for i, L in enumerate(target_lcoe):
            ax.annotate(f"${L:,.0f}", (achieved[i], y[i]),
                        textcoords="offset points", xytext=(8, 5), fontsize=9)

    ax.set_xlabel("Achieved LCOE ($/MWh)", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=13, fontweight="bold")
    if sci_y:
        ax.ticklabel_format(axis="y", style="scientific", scilimits=(0, 0))
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    path = os.path.join(FIG_DIR, fname)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# =========================================================================
# Plot 3: Correlation heatmaps
# =========================================================================

def plot_correlation_heatmaps(res, Sigma):
    """Correlation matrices for selected sites at every LCOE target (2x5 grid)."""
    all_lcoe = res["lcoe_target"].values
    all_status = res["status"].values
    n = len(all_lcoe)

    ncols = 5
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(3 * ncols + 1, 3.2 * nrows + 0.5))
    axes = np.atleast_2d(axes).ravel()

    std = np.sqrt(np.diag(Sigma))
    std[std == 0] = 1.0
    corr_full = Sigma / np.outer(std, std)

    im = None
    for tidx in range(n):
        ax = axes[tidx]
        L = all_lcoe[tidx]
        if all_status[tidx] != "optimal":
            ax.text(0.5, 0.5, "No optimal\nsolution",
                    ha="center", va="center", transform=ax.transAxes,
                    fontsize=10, color="0.4")
            ax.set_title(f"LCOE = ${L:,.0f}/MWh", fontsize=10)
            ax.set_xticks([])
            ax.set_yticks([])
            continue

        sel = res["selected"].values[tidx].astype(bool)
        sel_indices = np.where(sel)[0]
        corr_sel = corr_full[np.ix_(sel_indices, sel_indices)]
        im = ax.imshow(corr_sel, cmap="RdBu_r", vmin=-1, vmax=1, aspect="equal")
        ax.set_title(f"LCOE = ${L:,.0f}/MWh\n(n={sel.sum()} sites)", fontsize=10)
        ax.set_xlabel("Site index", fontsize=8)
        ax.set_ylabel("Site index", fontsize=8)

    for tidx in range(n, len(axes)):
        axes[tidx].axis("off")

    fig.subplots_adjust(right=0.90)
    if im is not None:
        cbar_ax = fig.add_axes([0.92, 0.15, 0.015, 0.7])
        cbar = fig.colorbar(im, cax=cbar_ax)
        cbar.set_label("Pearson Correlation")

    fig.suptitle("Power Output Correlation — Selected Sites",
                 fontsize=13, fontweight="bold")

    path = os.path.join(FIG_DIR, "correlation_heatmaps.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# =========================================================================
# Plot 4: Cost breakdown bar chart
# =========================================================================

def plot_cost_breakdown(res):
    """Stacked bars: C_const vs total site costs for each LCOE target."""
    target_idx, target_lcoe = get_optimal_targets(res)
    if len(target_idx) == 0:
        print("  Skipped: no optimal solutions")
        return
    c_const = res.attrs["C_const"]
    c_site_all = res["c_site"].values
    energy_all = res["energy_mwh"].values

    site_costs = []
    energies = []
    for tidx in target_idx:
        sel = res["selected"].values[tidx].astype(bool)
        site_costs.append(c_site_all[sel].sum())
        energies.append(energy_all[sel].sum())

    site_costs = np.array(site_costs)
    energies = np.array(energies)
    total = c_const + site_costs

    x = np.arange(len(target_lcoe))
    width = 0.5

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.bar(x, c_const * np.ones(len(x)) / 1e6, width,
           label="C_const (project-level)", color="steelblue")
    ax.bar(x, site_costs / 1e6, width, bottom=c_const / 1e6,
           label="Site costs (cable + laying + cascade)", color="coral")

    # Annotate achieved LCOE
    for i in range(len(x)):
        lcoe_val = total[i] / energies[i]
        ax.text(x[i], total[i] / 1e6 + 0.2, f"${lcoe_val:,.0f}/MWh",
                ha="center", va="bottom", fontsize=8, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels([f"${L:,.0f}" for L in target_lcoe])
    ax.set_xlabel("LCOE Target ($/MWh)", fontsize=12)
    ax.set_ylabel("Annualized Cost ($M/yr)", fontsize=12)
    ax.set_title("Cost Breakdown by LCOE Target", fontsize=13, fontweight="bold")
    ax.legend(loc="lower left")
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    path = os.path.join(FIG_DIR, "cost_breakdown.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# =========================================================================
# Main
# =========================================================================

def main():
    os.makedirs(FIG_DIR, exist_ok=True)

    print("Loading data...")
    res, Sigma, shoreline = load_data()

    target_idx, target_lcoe = get_optimal_targets(res)
    print(f"  {len(target_lcoe)} optimal solutions: "
          + ", ".join(f"${L:,.0f}" for L in target_lcoe))

    # Spatial maps redraw the shoreline once per LCOE target — minutes of dead
    # time on a fine frontier sweep (dozens of targets). TIDAL_SKIP_SPATIAL=1
    # skips them; the frontier curve doesn't need per-target site maps.
    if os.environ.get("TIDAL_SKIP_SPATIAL", "").strip():
        print("\nPlot 1: Spatial site maps... skipped (TIDAL_SKIP_SPATIAL)")
    else:
        print("\nPlot 1: Spatial site maps...")
        plot_spatial_maps(res, shoreline)

    print("Plot 2: LCOE tradeoff...")
    plot_pareto(res)

    if get_objective() == "energy":
        print("Plot 3: Correlation heatmaps... skipped (max-energy objective "
              "ignores covariance)")
    else:
        print("Plot 3: Correlation heatmaps...")
        plot_correlation_heatmaps(res, Sigma)

    print("Plot 4: Cost breakdown...")
    plot_cost_breakdown(res)

    res.close()
    print(f"\nAll figures saved to: {FIG_DIR}")


if __name__ == "__main__":
    main()
