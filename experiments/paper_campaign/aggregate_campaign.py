"""Aggregate the paper_campaign optimization results into small summary tables.

Runs ON energizelab (Windows), read-only over the campaign netCDFs:

  cd C:\\Users\\asingh66\\tidal-portfolio-siting\\experiments\\paper_campaign
  ..\\..\\.venv\\Scripts\\python.exe aggregate_campaign.py

Outputs (created under paper_campaign\\analysis\\, KB–MB scale, pulled back
to the paper repo at paper_draft/analysis/campaign_summaries/):

  pool_summary.csv       one row per eligibility pool (experiment x variant)
  cell_summary.csv       one row per (experiment, variant, capacity, lcoe_target)
  selected_sites.csv.gz  long format: every selected site in every cell
  run_metadata.csv       global attrs of every optimization_results.nc

Existing run outputs are never modified; only analysis/ is written.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "analysis"
OUT.mkdir(exist_ok=True)

GOM_LAT = 41.0  # Gulf of Maine / Nantucket split used in the 2026-04 draft


def classify(path: Path):
    """(experiment, variant, capacity_label) from a result path.

    Layouts:
      01_baseline/results/<cap>/optimization_results.nc          -> variant gen5
      02_diameter_family/results/<variant>/<cap>/...             -> modvpN
      03_rated_cutin/results/<variant>/<cap>/...                 -> vrX_vciY
      04_voltage_justification/results/<cap>/...                 -> gen5_480v
      05_scope_restriction/results/<cap>/...                     -> gen5_neny
    """
    rel = path.relative_to(ROOT).parts  # (experiment, 'results', [variant,] cap, file)
    experiment = rel[0]
    middle = rel[2:-2]  # parts between 'results' and the capacity folder
    variant = middle[0] if middle else {
        "01_baseline": "gen5",
        "04_voltage_justification": "gen5_480v",
        "05_scope_restriction": "gen5_neny",
    }.get(experiment, "gen5")
    capacity = rel[-2]
    return experiment, variant, capacity


def classify_pool(path: Path):
    """(experiment, variant) for a candidates.nc, which sits one level above
    the capacity folders: <experiment>/results/[<variant>/]candidates.nc"""
    rel = path.relative_to(ROOT).parts
    experiment = rel[0]
    variant = rel[-2] if rel[-2] != "results" else {
        "01_baseline": "gen5",
        "05_scope_restriction": "gen5_neny",
    }.get(experiment, "gen5")
    return experiment, variant


def pool_row(experiment, variant, path):
    ds = xr.open_dataset(path)
    cf = ds.capacity_factor.values
    depth = ds.depth.values
    row = {
        "experiment": experiment,
        "variant": variant,
        "n_candidates": int(ds.sizes["site"]),
        "cf_median": float(np.median(cf)),
        "cf_mean": float(np.mean(cf)),
        "cf_max": float(np.max(cf)),
        "depth_min_m": float(np.min(depth)),
        "depth_median_m": float(np.median(depth)),
        "lat_min": float(ds.latitude.min()),
        "lat_max": float(ds.latitude.max()),
        "path": str(path.relative_to(ROOT)),
    }
    for attr in ("cf_threshold", "turbine", "p_rated_w", "v_cut_in_ms",
                 "v_rated_ms", "cp", "n_candidates", "created"):
        row[f"attr_{attr}"] = ds.attrs.get(attr)
    ds.close()
    return row


def cell_rows(experiment, variant, capacity, path):
    """Per-LCOE-target summary rows + long-format selected-site rows."""
    ds = xr.open_dataset(path)
    meta = {
        "experiment": experiment,
        "variant": variant,
        "capacity": capacity,
        "path": str(path.relative_to(ROOT)),
    }
    for attr in ("P_target_MW", "N_triframes", "C_const", "loss_formula",
                 "objective", "created"):
        meta[f"attr_{attr}"] = ds.attrs.get(attr)

    c_const = float(ds.attrs.get("C_const", np.nan))
    p_target_mw = float(ds.attrs.get("P_target_MW", np.nan))

    lat = ds.latitude.values
    cf = ds.capacity_factor.values
    energy = ds.energy_mwh.values.astype(float)   # MWh/yr per TriFrame
    c_site = ds.c_site.values.astype(float)       # $/yr per TriFrame

    summaries, sites = [], []
    for t in range(ds.sizes["target"]):
        L = float(ds.lcoe_target[t])
        sel = ds.selected[t].values  # TriFrames placed per site
        mask = sel > 0
        n_tf = int(sel.sum())
        sel_e = float((sel * energy).sum())
        sel_c = float((sel * c_site).sum())
        cf_sel = np.repeat(cf[mask], sel[mask])  # TriFrame-weighted CF
        row = {
            "experiment": experiment,
            "variant": variant,
            "capacity": capacity,
            "lcoe_target": L,
            "status": str(ds.status[t].values),
            "variance_w2": float(ds.variance[t]),
            "achieved_lcoe": float(ds.achieved_lcoe[t]),
            "lcoe_slack": float(ds.lcoe_slack[t]),
            "n_sites": int(mask.sum()),
            "n_triframes": n_tf,
            "portfolio_energy_mwh": sel_e,
            "cost_const_usd_yr": c_const,
            "cost_sites_usd_yr": sel_c,
            "cost_total_usd_yr": c_const + sel_c,
            "portfolio_cf": (sel_e / (p_target_mw * 8760.0)
                             if p_target_mw and sel_e else np.nan),
            "cf_sel_median": float(np.median(cf_sel)) if n_tf else np.nan,
            "cf_sel_mean": float(np.mean(cf_sel)) if n_tf else np.nan,
            "frac_tf_gom": (float(np.repeat(lat[mask] >= GOM_LAT,
                                            sel[mask]).mean())
                            if n_tf else np.nan),
            "lat_sel_min": float(lat[mask].min()) if n_tf else np.nan,
            "lat_sel_max": float(lat[mask].max()) if n_tf else np.nan,
            # economic feasibility screen at this target, over the full pool
            "n_econ_feasible": int((c_site - L * energy < 0).sum()),
        }
        summaries.append(row)

        if n_tf:
            idx = np.flatnonzero(mask)
            sites.append(pd.DataFrame({
                "experiment": experiment,
                "variant": variant,
                "capacity": capacity,
                "lcoe_target": L,
                "site": ds.site.values[idx],
                "n_triframes": sel[idx],
                "latitude": lat[idx],
                "longitude": ds.longitude.values[idx],
                "depth_m": ds.depth.values[idx],
                "capacity_factor": cf[idx],
                "energy_mwh": energy[idx],
                "c_site_usd_yr": c_site[idx],
                "shore_distance_km": ds.shore_distance_km.values[idx],
                "cable_csa_mm2": ds.cable_csa_mm2.values[idx],
            }))
    ds.close()
    return meta, summaries, sites


def main():
    results = sorted(ROOT.rglob("optimization_results.nc"))
    pools = sorted(ROOT.rglob("candidates.nc"))
    print(f"found {len(results)} optimization cells, {len(pools)} pools")

    pool_df = pd.DataFrame(
        [pool_row(*classify_pool(p), p) for p in pools]
    )
    pool_df.to_csv(OUT / "pool_summary.csv", index=False)

    metas, cells, sites = [], [], []
    for p in results:
        experiment, variant, capacity = classify(p)
        meta, rows, site_frames = cell_rows(experiment, variant, capacity, p)
        metas.append(meta)
        cells.extend(rows)
        sites.extend(site_frames)
        print(f"  {experiment}/{variant}/{capacity}: {len(rows)} targets")

    pd.DataFrame(metas).to_csv(OUT / "run_metadata.csv", index=False)
    pd.DataFrame(cells).to_csv(OUT / "cell_summary.csv", index=False)
    sites_df = pd.concat(sites, ignore_index=True)
    sites_df.to_csv(OUT / "selected_sites.csv.gz", index=False,
                    compression="gzip")

    print(f"\nwrote {OUT}")
    print(f"  pool_summary.csv    {len(pool_df)} pools")
    print(f"  cell_summary.csv    {len(cells)} cells")
    print(f"  selected_sites.csv.gz  {len(sites_df)} site-selections")
    print(f"  run_metadata.csv    {len(metas)} result files")


if __name__ == "__main__":
    main()
