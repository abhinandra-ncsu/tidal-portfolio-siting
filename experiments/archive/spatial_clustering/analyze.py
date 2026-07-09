"""
Spatial clustering diagnostic — see EXPERIMENT.md.

DBSCAN (eps=5 km, min_samples=3) on the eligible pool and on each
(MW, LCOE) selected set. Renders:

  - eligible_pool_clusters.png      eligible pool, color = cluster ID
  - selected_clusters_grid.png      2x2 grid (1/5/25/100 MW) of selected
                                    sites at a representative LCOE,
                                    colored by their own cluster
  - cluster_summary.csv             per-cell DBSCAN stats
"""

import os

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib import colormaps
from scipy.spatial import cKDTree

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BASE = os.path.join(REPO, "results", "vp", "turbine_modification",
                    "gen5", "groups", "new_england_new_york")
SHORELINE = os.path.join(REPO, "inputs", "geography",
                         "NOAA_MedRes", "allus80k.shp")
OUT_DIR = os.path.join(REPO, "results", "vp", "spatial_clustering", "analysis")
FIG_DIR = os.path.join(OUT_DIR, "figures")

SCALES_MW = [1, 5, 25, 100]
# Representative L per scale: the highest infeasible-free L we have so the
# selected set is as spread-out as the budget allows (gives the optimizer
# room to diversify; under-tight L collapses to whichever single cluster is
# cheapest).
REPRESENTATIVE_L = {1: 1500, 5: 1500, 25: 1500, 100: 1500}

EPS_KM = 5.0
MIN_SAMPLES = 3
EARTH_R = 6371.0


# -----------------------------------------------------------------------
# DBSCAN on the sphere (chord distance in 3D, then BFS)
# -----------------------------------------------------------------------

def latlon_to_xyz(lat, lon):
    la = np.deg2rad(lat); lo = np.deg2rad(lon)
    return np.column_stack([
        np.cos(la) * np.cos(lo),
        np.cos(la) * np.sin(lo),
        np.sin(la),
    ]) * EARTH_R


def dbscan(lat, lon, eps_km=EPS_KM, min_samples=MIN_SAMPLES):
    """Returns labels (n,), -1 for noise. Sorted descending by cluster size."""
    n = len(lat)
    if n == 0:
        return np.zeros(0, dtype=int)
    xyz = latlon_to_xyz(lat, lon)
    tree = cKDTree(xyz)
    eps_chord = 2.0 * EARTH_R * np.sin(eps_km / (2.0 * EARTH_R))
    nbrs = tree.query_ball_tree(tree, r=eps_chord)
    labels = -np.ones(n, dtype=int)
    cid = 0
    for i in range(n):
        if labels[i] != -1 or len(nbrs[i]) < min_samples:
            continue
        stack = [i]; labels[i] = cid
        while stack:
            j = stack.pop()
            if len(nbrs[j]) < min_samples:
                continue
            for k in nbrs[j]:
                if labels[k] == -1:
                    labels[k] = cid
                    stack.append(k)
        cid += 1

    # Re-label by descending cluster size so cluster 0 is the largest.
    sizes = np.array([(labels == c).sum() for c in range(cid)])
    order = np.argsort(-sizes)
    remap = {old: new for new, old in enumerate(order)}
    new_labels = labels.copy()
    for c in range(cid):
        new_labels[labels == c] = remap[c]
    return new_labels


# -----------------------------------------------------------------------
# Plot helpers
# -----------------------------------------------------------------------

def cluster_colors(labels, top_n_distinct=20):
    """Return per-point RGBA colors: top-N clusters distinct, rest gray, noise = light gray."""
    cmap = colormaps["tab20"]
    colors = np.zeros((len(labels), 4))
    colors[:] = (0.75, 0.75, 0.75, 0.5)  # default = noise gray
    for c in range(top_n_distinct):
        m = labels == c
        if not m.any():
            break
        colors[m] = cmap(c % 20)
    # Clusters beyond top_n: still distinguishable from noise, use dark gray
    high = labels >= top_n_distinct
    colors[high] = (0.3, 0.3, 0.3, 0.6)
    return colors


def plot_pool_with_clusters(ax, lat, lon, labels, shoreline, point_size=4,
                            label_top_n=8, title=""):
    shoreline.plot(ax=ax, color="0.88", linewidth=0.3, zorder=0)
    colors = cluster_colors(labels)
    # Noise drawn first / underneath
    noise = labels == -1
    ax.scatter(lon[noise], lat[noise], s=point_size, c="0.78",
               alpha=0.4, zorder=1, linewidths=0)
    ax.scatter(lon[~noise], lat[~noise], s=point_size,
               c=colors[~noise], alpha=0.85, zorder=2, linewidths=0)

    # Centroid + size label for the top clusters
    n_clusters = int(labels.max() + 1) if (labels >= 0).any() else 0
    for c in range(min(label_top_n, n_clusters)):
        m = labels == c
        if not m.any():
            continue
        clat = float(lat[m].mean()); clon = float(lon[m].mean())
        n_pts = int(m.sum())
        ax.annotate(
            f"#{c} (n={n_pts})", xy=(clon, clat),
            xytext=(6, 6), textcoords="offset points",
            fontsize=8, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="0.4",
                      alpha=0.85, lw=0.5),
            zorder=5,
        )
    ax.set_xlim(lon.min() - 0.5, lon.max() + 0.5)
    ax.set_ylim(lat.min() - 0.5, lat.max() + 0.5)
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=11, fontweight="bold")


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def main():
    os.makedirs(FIG_DIR, exist_ok=True)
    print(f"Output dir: {OUT_DIR}")

    print("Loading shoreline...")
    shoreline = gpd.read_file(SHORELINE)

    # Eligible pool — use any scale (the eligible set is identical across MW)
    ref_path = os.path.join(BASE, "100mw", "optimization_results.nc")
    print(f"Loading eligible pool from {ref_path}")
    ds_ref = xr.open_dataset(ref_path)
    elig_lat = ds_ref["latitude"].values
    elig_lon = ds_ref["longitude"].values
    print(f"  Eligible sites: {len(elig_lat):,}")

    # -------------------------------------------------------------------
    # 0. Eligible pool — plain map (no clustering)
    # -------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 9))
    shoreline.plot(ax=ax, color="0.88", linewidth=0.3, zorder=0)
    ax.scatter(elig_lon, elig_lat, s=4, c="#1f77b4", alpha=0.55,
               linewidths=0, zorder=1)
    ax.set_xlim(elig_lon.min() - 0.5, elig_lon.max() + 0.5)
    ax.set_ylim(elig_lat.min() - 0.5, elig_lat.max() + 0.5)
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    ax.set_aspect("equal")
    ax.set_title(f"Eligible candidate sites — gen5 / new_england_new_york "
                 f"(n={len(elig_lat):,})",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    out = os.path.join(FIG_DIR, "eligible_pool_plain.png")
    fig.savefig(out, dpi=160, bbox_inches="tight"); plt.close(fig)
    print(f"  Saved: {out}")

    # -------------------------------------------------------------------
    # 1. Cluster eligible pool
    # -------------------------------------------------------------------
    print(f"\nDBSCAN on eligible pool (eps={EPS_KM} km, min_samples={MIN_SAMPLES})...")
    elig_labels = dbscan(elig_lat, elig_lon)
    elig_n_clusters = int(elig_labels.max() + 1) if (elig_labels >= 0).any() else 0
    elig_noise = int((elig_labels == -1).sum())
    sizes = [int((elig_labels == c).sum()) for c in range(elig_n_clusters)]
    print(f"  Clusters: {elig_n_clusters}  Noise: {elig_noise}")
    print(f"  Top sizes: {sizes[:10]}")

    fig, ax = plt.subplots(figsize=(11, 9))
    plot_pool_with_clusters(
        ax, elig_lat, elig_lon, elig_labels, shoreline,
        point_size=5, label_top_n=8,
        title=(f"Eligible pool — DBSCAN clusters "
               f"(eps={EPS_KM} km, min_samples={MIN_SAMPLES})\n"
               f"n={len(elig_lat):,} sites · {elig_n_clusters} clusters · "
               f"{elig_noise} noise points"),
    )
    fig.tight_layout()
    out = os.path.join(FIG_DIR, "eligible_pool_clusters.png")
    fig.savefig(out, dpi=160, bbox_inches="tight"); plt.close(fig)
    print(f"  Saved: {out}")

    # -------------------------------------------------------------------
    # 2. Selected sites per scale, colored by their own cluster
    # -------------------------------------------------------------------
    summary_rows = []
    print("\nSelected-site clustering per scale...")
    fig, axes = plt.subplots(2, 2, figsize=(20, 17))
    for ax, mw in zip(axes.flat, SCALES_MW):
        p = os.path.join(BASE, f"{mw}mw", "optimization_results.nc")
        ds = xr.open_dataset(p)
        L_target = REPRESENTATIVE_L[mw]
        t_idx = int(np.where(ds["lcoe_target"].values == L_target)[0][0])
        sel = ds["selected"].isel(target=t_idx).values.astype(bool)
        lat = ds["latitude"].values[sel]
        lon = ds["longitude"].values[sel]
        ds.close()

        labels = dbscan(lat, lon)
        n_clusters = int(labels.max() + 1) if (labels >= 0).any() else 0
        noise = int((labels == -1).sum())
        sizes = [int((labels == c).sum()) for c in range(n_clusters)]
        top1 = sizes[0] / len(lat) if sizes else 0.0
        top3 = sum(sizes[:3]) / len(lat) if sizes else 0.0
        print(f"  {mw}MW @ L=${L_target}: n_sel={len(lat)} clusters={n_clusters} "
              f"top1={top1*100:.1f}% top3={top3*100:.1f}% sizes={sizes[:5]}")

        # Shoreline + eligible pool (gray background) so the selected
        # sites can be read against the "what was available" baseline.
        shoreline.plot(ax=ax, color="0.90", linewidth=0.3, zorder=0)
        ax.scatter(elig_lon, elig_lat, s=2, c="0.72", alpha=0.35,
                   linewidths=0, zorder=1)

        # Selected sites colored by their cluster
        colors = cluster_colors(labels)
        noise_mask = labels == -1
        ax.scatter(lon[noise_mask], lat[noise_mask],
                   s=24 if mw <= 5 else 14,
                   c="black", marker="x", linewidths=0.8, zorder=2)
        ax.scatter(lon[~noise_mask], lat[~noise_mask],
                   s=40 if mw <= 5 else 18,
                   c=colors[~noise_mask], edgecolors="black",
                   linewidths=0.4, zorder=3)

        # Centroid labels for top clusters
        for c in range(min(6, n_clusters)):
            m = labels == c
            if not m.any():
                continue
            clat = float(lat[m].mean()); clon = float(lon[m].mean())
            ax.annotate(
                f"#{c} (n={int(m.sum())})", xy=(clon, clat),
                xytext=(6, 6), textcoords="offset points",
                fontsize=9, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.2", fc="white",
                          ec="0.4", alpha=0.9, lw=0.5),
                zorder=6,
            )

        ax.set_xlim(elig_lon.min() - 0.5, elig_lon.max() + 0.5)
        ax.set_ylim(elig_lat.min() - 0.5, elig_lat.max() + 0.5)
        ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
        ax.set_aspect("equal")
        ax.set_title(
            f"{mw} MW · L=${L_target}/MWh · n_sel={len(lat)} · "
            f"{n_clusters} clusters · top-1={top1*100:.1f}% · "
            f"top-3={top3*100:.1f}%",
            fontsize=12, fontweight="bold",
        )

        summary_rows.append({
            "scale_mw": mw, "lcoe_target": L_target, "n_selected": len(lat),
            "n_clusters": n_clusters, "n_noise": noise,
            "top1_frac": round(top1, 4), "top3_frac": round(top3, 4),
            "top_sizes": ";".join(str(s) for s in sizes[:5]),
        })

    fig.suptitle(
        f"Selected sites · DBSCAN clusters (eps={EPS_KM} km, min_samples={MIN_SAMPLES})",
        fontsize=13, fontweight="bold",
    )
    fig.tight_layout()
    out = os.path.join(FIG_DIR, "selected_clusters_grid.png")
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  Saved: {out}")

    # -------------------------------------------------------------------
    # 3. CSV summary (also include the eligible-pool row for comparison)
    # -------------------------------------------------------------------
    summary_rows.insert(0, {
        "scale_mw": "ELIGIBLE", "lcoe_target": "-",
        "n_selected": len(elig_lat),
        "n_clusters": elig_n_clusters, "n_noise": elig_noise,
        "top1_frac": round(sizes_elig := [int((elig_labels == c).sum())
                                          for c in range(elig_n_clusters)][0]
                           / len(elig_lat), 4),
        "top3_frac": round(sum(
            [int((elig_labels == c).sum()) for c in range(elig_n_clusters)][:3]
        ) / len(elig_lat), 4),
        "top_sizes": ";".join(
            str(int((elig_labels == c).sum())) for c in range(min(5, elig_n_clusters))
        ),
    })
    df = pd.DataFrame(summary_rows)
    csv_path = os.path.join(OUT_DIR, "cluster_summary.csv")
    df.to_csv(csv_path, index=False)
    print(f"  Saved: {csv_path}")
    print("\n" + df.to_string(index=False))

    ds_ref.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
