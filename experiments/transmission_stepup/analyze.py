"""
Transmission step-up — outcome analysis.

Answers EXPERIMENT.md §Success criteria with the four metrics agreed in
session: min-feasible LCOE, sigma^2 at matched LCOE, E at matched LCOE, and
|feasible candidate set| at L. CV is deliberately not used here (P_rated and
Sigma are bit-identical between 480 V and 6.6 kV because steps 1-4 are reused
via symlinks; raw variance in W^2 is already apples-to-apples, and CV would
hide the small-N "same risk, more energy unlocked" story).

Outputs (results/vp/transmission_stepup/analysis/):
  portfolio_metrics.csv   one row per (voltage, mw, lcoe_target)
  site_overlap.csv        one row per (mw, lcoe_target) where both voltages optimal
  summary.csv             one row per mw with the four matched-L deltas + overlap
  figures/outcome_panels.png   2 x 4 grid: rows = {sigma^2, E}, cols = MW
"""

import os
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BASELINE_BASE = os.path.join(REPO, "results", "vp", "turbine_modification",
                             "gen5", "groups", "new_england_new_york")
STEPUP_BASE = os.path.join(REPO, "results", "vp", "transmission_stepup",
                           "gen5", "groups", "new_england_new_york")
OUT_DIR = os.path.join(REPO, "results", "vp", "transmission_stepup", "analysis")

SCALES_MW = [1, 5, 25, 100]
CASES = [("480V", 0.480, BASELINE_BASE), ("6.6kV", 6.6, STEPUP_BASE)]


def cell_rows(case_label, voltage_kv, base, mw):
    """One row per LCOE target for a single (voltage, MW) cell."""
    path = os.path.join(base, f"{mw}mw", "optimization_results.nc")
    ds = xr.open_dataset(path)
    L = ds["lcoe_target"].values
    status = ds["status"].values.astype(str)
    achieved = ds["achieved_lcoe"].values
    variance = ds["variance"].values
    selected = ds["selected"].values.astype(bool)  # (target, site)
    energy_mwh = ds["energy_mwh"].values           # (site,)
    c_site = ds["c_site"].values                    # (site,)
    ds.close()

    rows = []
    for t in range(len(L)):
        if status[t] == "optimal":
            portfolio_e = float((selected[t] * energy_mwh).sum())
            n_sel = int(selected[t].sum())
        else:
            portfolio_e = np.nan
            n_sel = 0
        # Candidate pool: sites where c_site - L*E < 0 (the screen in 05_optimize.py).
        # Voltage-dependent because c_site changes with voltage (CSA selection differs).
        n_feasible = int((c_site - L[t] * energy_mwh < 0).sum())
        rows.append({
            "voltage": case_label,
            "voltage_kv": voltage_kv,
            "mw": mw,
            "lcoe_target": float(L[t]),
            "status": status[t],
            "achieved_lcoe": float(achieved[t]),
            "variance_w2": float(variance[t]),
            "energy_mwh_yr": portfolio_e,
            "n_selected": n_sel,
            "n_feasible_candidates": n_feasible,
        })
    return rows


def build_table():
    rows = []
    for label, kv, base in CASES:
        for mw in SCALES_MW:
            rows.extend(cell_rows(label, kv, base, mw))
    return pd.DataFrame(rows)


def build_overlap_table():
    """Per (mw, L) overlap of selected sites between 480 V and 6.6 kV.
    Only includes L where both voltages were optimal. shore_distance_km
    is per-site (not voltage-dependent), so either .nc works for it."""
    rows = []
    for mw in SCALES_MW:
        b = xr.open_dataset(os.path.join(BASELINE_BASE, f"{mw}mw",
                                          "optimization_results.nc"))
        s = xr.open_dataset(os.path.join(STEPUP_BASE, f"{mw}mw",
                                          "optimization_results.nc"))
        L = b["lcoe_target"].values
        bst = b["status"].values.astype(str)
        sst = s["status"].values.astype(str)
        bsel = b["selected"].values.astype(bool)
        ssel = s["selected"].values.astype(bool)
        dist = b["shore_distance_km"].values
        b.close()
        s.close()
        for t in range(len(L)):
            if bst[t] != "optimal" or sst[t] != "optimal":
                continue
            bs, ss_ = bsel[t], ssel[t]
            n_b = int(bs.sum())
            n_common = int((bs & ss_).sum())
            rows.append({
                "mw": mw,
                "lcoe_target": float(L[t]),
                "n_selected": n_b,
                "n_common": n_common,
                "n_swap": n_b - n_common,
                "overlap_pct": 100.0 * n_common / n_b,
                "mean_dist_480v_km": float(dist[bs].mean()),
                "mean_dist_6kv_km": float(dist[ss_].mean()),
            })
    return pd.DataFrame(rows)


def per_mw_summary(df, overlap_df):
    """One row per MW: LCOE floor + matched-L deltas at the worst-common L."""
    out = []
    for mw in SCALES_MW:
        base = df[(df.mw == mw) & (df.voltage == "480V")]
        step = df[(df.mw == mw) & (df.voltage == "6.6kV")]

        base_floor = base.loc[base.status == "optimal", "lcoe_target"].min()
        step_floor = step.loc[step.status == "optimal", "lcoe_target"].min()
        worst_common = max(base_floor, step_floor)

        b = base[base.lcoe_target == worst_common].iloc[0]
        s = step[step.lcoe_target == worst_common].iloc[0]
        ov = overlap_df[(overlap_df.mw == mw)
                        & (overlap_df.lcoe_target == worst_common)].iloc[0]

        def pct(new, old):
            return 100.0 * (new - old) / old

        out.append({
            "mw": mw,
            "min_feasible_lcoe_480v": base_floor,
            "min_feasible_lcoe_6kv": step_floor,
            "delta_lcoe_floor": step_floor - base_floor,
            "worst_common_lcoe": worst_common,
            "variance_w2_480v": b.variance_w2,
            "variance_w2_6kv": s.variance_w2,
            "variance_delta_pct": pct(s.variance_w2, b.variance_w2),
            "energy_mwh_480v": b.energy_mwh_yr,
            "energy_mwh_6kv": s.energy_mwh_yr,
            "energy_delta_pct": pct(s.energy_mwh_yr, b.energy_mwh_yr),
            "n_feasible_480v": int(b.n_feasible_candidates),
            "n_feasible_6kv": int(s.n_feasible_candidates),
            "n_feasible_delta_pct": pct(s.n_feasible_candidates, b.n_feasible_candidates),
            "n_common": int(ov.n_common),
            "n_swap": int(ov.n_swap),
            "overlap_pct": float(ov.overlap_pct),
            "mean_dist_480v_km": float(ov.mean_dist_480v_km),
            "mean_dist_6kv_km": float(ov.mean_dist_6kv_km),
        })
    return pd.DataFrame(out)


def plot_outcomes(df, path):
    fig, axes = plt.subplots(2, len(SCALES_MW),
                             figsize=(4 * len(SCALES_MW), 6.5), sharex=True)
    style = {"480V": dict(color="black", linestyle="-", marker="o"),
             "6.6kV": dict(color="#d62728", linestyle="--", marker="s")}

    for c, mw in enumerate(SCALES_MW):
        for label, _, _ in CASES:
            d = df[(df.mw == mw) & (df.voltage == label)
                   & (df.status == "optimal")].sort_values("achieved_lcoe")
            axes[0, c].plot(d.achieved_lcoe, d.variance_w2,
                            label=label, linewidth=2, markersize=4, **style[label])
            axes[1, c].plot(d.achieved_lcoe, d.energy_mwh_yr / 1e3,
                            label=label, linewidth=2, markersize=4, **style[label])
        axes[0, c].set_title(f"{mw} MW")
        axes[0, c].grid(True, alpha=0.3)
        axes[1, c].grid(True, alpha=0.3)
        axes[1, c].set_xlabel("Achieved LCOE ($/MWh)")

    axes[0, 0].set_ylabel("Portfolio variance (W$^2$)")
    axes[1, 0].set_ylabel("Portfolio energy (GWh/yr)")
    axes[0, 0].legend(fontsize=9, loc="upper right")
    fig.suptitle("Step-up (6.6 kV) vs baseline (480 V): risk and energy vs LCOE",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    df = build_table()
    metrics_path = os.path.join(OUT_DIR, "portfolio_metrics.csv")
    df.to_csv(metrics_path, index=False)
    print(f"Wrote {metrics_path}: {len(df)} rows")

    overlap_df = build_overlap_table()
    overlap_path = os.path.join(OUT_DIR, "site_overlap.csv")
    overlap_df.to_csv(overlap_path, index=False)
    print(f"Wrote {overlap_path}: {len(overlap_df)} rows")

    summary = per_mw_summary(df, overlap_df)
    summary_path = os.path.join(OUT_DIR, "summary.csv")
    summary.to_csv(summary_path, index=False)
    print(f"Wrote {summary_path}")
    print()
    print(summary.to_string(index=False))
    print()

    fig_path = os.path.join(OUT_DIR, "figures", "outcome_panels.png")
    plot_outcomes(df, fig_path)
    print(f"Wrote {fig_path}")


if __name__ == "__main__":
    main()
