# Spatial clustering — diagnostic analysis

**Date:** 2026-05-28
**Status:** diagnostic; not a baseline-modifying experiment
**Region:** new_england_new_york (gen5)

---

## Question

The Gen5 / NE+NY optimization results visually look like all selected farms
"cluster around Vineyard Sound / Nantucket Sound" across every MW × LCOE
cell. Is that real, or is it a visual artifact of the **eligible pool itself**
being concentrated there?

Concretely: how spatially clustered is the eligible candidate pool, how
spatially clustered are the optimizer's selections, and is the selected set
*more* or *less* concentrated than the eligible baseline?

## Method

- Cluster the **eligible pool** (`candidates.nc` from step 3) with DBSCAN on
  great-circle distance: **eps = 5 km, min_samples = 3**. 5 km matches the
  scale at which "two sites in the same channel" is intuitive.
- Cluster the **selected sites** for each (MW, LCOE) cell using the same
  parameters.
- Report per-cluster sizes and the top-1 / top-3 share of selected vs eligible.
- Render the eligible pool as a single map colored by cluster ID — the
  headline figure that lets you eyeball whether the pool itself is
  one-big-blob or many-small-blobs.
- Render selected-site maps for representative cells colored by cluster.

## What this does *not* do

- Does **not** modify the pipeline.
- Does **not** re-run optimization. Reads only the existing
  `optimization_results.nc` per scale from
  `results/vp/turbine_modification/gen5/groups/new_england_new_york/<MW>mw/`.

## Outputs

`results/vp/spatial_clustering/analysis/`

- `figures/eligible_pool_clusters.png` — eligible pool, color = cluster ID
- `figures/selected_clusters_grid.png` — 2×2 grid: selected sites per scale
  at a representative LCOE, colored by their cluster
- `cluster_summary.csv` — per-cell DBSCAN summary
