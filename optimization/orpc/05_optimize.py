"""
Step 5: ORPC TidGen 2.0 portfolio optimization.

Computes all cost and energy inputs from the documented formulas, then
solves the Binary Quadratic Program:

    min   x^T Sigma x                              (portfolio variance)
    s.t.  sum(x_i) = N                             (deploy N devices)
          C_const(N) + sum x_i (c_site_i - L*E_i) <= 0   (LCOE ceiling)
          x_i in {0,1}

Input:  results/orpc/<group>/candidates.nc  (from 03_screen_candidates.py)
        results/orpc/<group>/covariance.nc  (from compute_covariance.m)
Output: results/orpc/<group>/optimization_results.nc

References (in optimization/orpc/methodology/):
    - turbine_design_specification.md
    - cost/capex/capex_cost_components.md
    - cost/capex/installation/methodology.md
    - cost/capex/electrical/methodology.md
    - cost/opex/opex_cost_components.md
"""

import os
from datetime import datetime, timezone

import gurobipy as gp
import numpy as np
import xarray as xr

from config.config import (
    # Turbine
    P_TURBINE_KW, DEVICES_PER_SITE, P_DEVICE_KW,
    SCM_SPEEDS_MS, SCM_POWER_KW,
    V_CUT_IN, V_RATED, V_PLATEAU_END,
    # Energy
    HOURS_PER_YEAR, ETA_AVAIL,
    # Electrical
    MAX_LOSS, CABLES, PF,
    # Transmission step-up (cost/capex/electrical/methodology.md)
    STEPUP_KV, C_TRANSFORMER_PER_DEVICE,
    # Cost — device
    C_DEVICE_UNIT1, LEARNING_EXP,
    # Cost — installation (ORPC: 3-phase tug + multicat + per-meter cable)
    TUG_DAY_RATE, MULTICAT_DAY_RATE,
    TUG_DAYS_PER_DEVICE, MULTICAT_DAYS_PER_DEVICE, TRANSIT_DAYS,
    MOORING_MAT_PER_DEVICE, CABLE_INST_PER_KM,
    # Cost — percentages
    SUBSYS_FRAC, CONTIN_FRAC, EC_FRAC, INSURE_FRAC,
    # Cost — OpEx
    OPEX_FIXED_PER_TF,
    # Annualization
    FCR,
    # Optimization
    P_TARGET_MW, LCOE_TARGETS,
    # Solver
    GUROBI_TIME_LIMIT, GUROBI_MIP_GAP,
    get_results_dir,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

RESULTS_DIR = get_results_dir()

CANDIDATES_PATH = os.path.join(RESULTS_DIR, "candidates.nc")
COVARIANCE_PATH = os.path.join(RESULTS_DIR, "covariance.nc")
RESULTS_PATH = os.path.join(RESULTS_DIR, "optimization_results.nc")

# Loss formula: 3 * I^2 * R * L / P, with I = P_device / (sqrt(3) * V * PF).
# Generation is 480 V; the baseline steps up to STEPUP_KV (6.6 kV) before
# transmission, cutting the current ~13.75x (electrical/methodology.md).
# At 6.6 kV: I = 46.0 A, LOSS_COEFF ≈ 0.0127 (=> ~1.272% * R * L).
_V_TX_VOLTS = (STEPUP_KV * 1000.0) if STEPUP_KV is not None else 480.0
_I_AMPS = (P_DEVICE_KW * 1000.0) / (np.sqrt(3.0) * _V_TX_VOLTS * PF)
LOSS_COEFF = 3.0 * _I_AMPS**2 / (P_DEVICE_KW * 1000.0)


# =========================================================================
# Functions
# =========================================================================

def select_cable(distance_km):
    """Select cheapest cable with loss <= MAX_LOSS. Returns (csa, cost_per_m, loss)."""
    for csa, r, cost_m in CABLES:
        loss = LOSS_COEFF * r * distance_km
        if loss <= MAX_LOSS:
            return csa, cost_m, loss
    # Fallback: largest cable
    csa, r, cost_m = CABLES[-1]
    return csa, cost_m, LOSS_COEFF * r * distance_km


def compute_energy(hist, centers, loss):
    """
    Annual energy delivered per device at a site (MWh/yr).

    E_i = (8766/1000) * eta_avail * (1-loss) * sum_k P(u_k) * p_i(u_k)

    Power curve is the SCM-tabulated electrical curve (0.5-3.0 m/s),
    plateau 3.0-3.5 m/s at rated, zero outside. SCM gives net electrical
    power, so no separate drivetrain efficiency is applied.
    """
    speeds = np.asarray(centers, dtype=float)
    power_w = np.interp(speeds, SCM_SPEEDS_MS, SCM_POWER_KW,
                        left=0.0, right=P_TURBINE_KW) * 1000.0
    power_w[speeds < V_CUT_IN] = 0.0
    power_w[speeds > V_PLATEAU_END] = 0.0

    mean_power_w = hist @ power_w  # W per device
    energy_mwh = (HOURS_PER_YEAR / 1e6 * ETA_AVAIL
                  * (1 - loss) * DEVICES_PER_SITE * mean_power_w)
    return energy_mwh


def compute_c_const(N):
    """
    Annualized project-level constant cost C_const(N) for ORPC.

    Includes: device manufacturing (learning curve), tow + moor installation
    (tug + multicat), per-device mooring materials, the per-device step-up
    transformer, subsystem integration, constant portions of
    contingency/compliance, the non-insurance OpEx bundle, and the constant
    (device + BOS) share of insurance. Cable installation is fully
    portfolio-dependent (Mattia per-meter bundled metric); insurance is
    re-modeled as 1% × CapEx (INSURE_FRAC = 0.01), harmonized with VP —
    ORPC's bundled $20k insurance line is stripped from OPEX_FIXED_PER_TF.
    """
    # Device manufacturing with learning curve
    units = np.arange(1, N + 1, dtype=np.float64)
    c_device_total = C_DEVICE_UNIT1 * np.sum(units ** LEARNING_EXP)

    # Phase 1: Tow (tug)
    tug_days = 2 * TRANSIT_DAYS + TUG_DAYS_PER_DEVICE * N
    c_inst_tow = tug_days * TUG_DAY_RATE

    # Phase 2: Moor (multicat)
    multicat_days = 2 * TRANSIT_DAYS + MULTICAT_DAYS_PER_DEVICE * N
    c_inst_moor = multicat_days * MULTICAT_DAY_RATE

    # Mooring materials (chains + gravity anchors)
    c_mooring_mat = MOORING_MAT_PER_DEVICE * N

    c_inst_const = c_inst_tow + c_inst_moor + c_mooring_mat

    # Subsystem integration
    c_subsys = SUBSYS_FRAC * c_device_total

    # Contingency (constant portion)
    c_contin_const = CONTIN_FRAC * (c_device_total + c_subsys + c_inst_const)

    # Environmental compliance (constant portion)
    c_ec_const = EC_FRAC * (c_device_total + c_subsys + c_contin_const)

    # Step-up transformer (zero for the 480 V comparison arm). Site-independent,
    # one per device; added as raw CapEx (FCR applies; the contingency/EC
    # cascade does not), the same treatment VP gives it.
    c_transformer = N * C_TRANSFORMER_PER_DEVICE

    # Total constant CapEx
    capex_const = (c_device_total + c_inst_const + c_subsys
                   + c_contin_const + c_ec_const + c_transformer)

    # Annualized constant cost
    annual_capex = FCR * capex_const
    annual_opex = OPEX_FIXED_PER_TF * N
    annual_insurance_const = INSURE_FRAC * capex_const  # 1% × CapEx (VP-harmonized)

    c_const = annual_capex + annual_opex + annual_insurance_const
    return c_const


def compute_c_site(cable_cost_total, laying_cost):
    """
    Annualized portfolio-dependent cost for a single ORPC site.

    Includes cable purchase, cable laying, and cascading percentages
    (contingency, compliance) applied to laying only — same cascade
    pattern as the VP pipeline. No onshore inverter: it was retired with
    the DC architecture (electrical/methodology.md).
    """
    # Contingency on laying
    contin_pd = CONTIN_FRAC * laying_cost

    # Compliance on contingency
    ec_pd = EC_FRAC * contin_pd

    # Total portfolio-dependent CapEx for this site
    capex_pd = cable_cost_total + laying_cost + contin_pd + ec_pd

    # Annualized: FCR * CapEx + insurance (1% × CapEx, VP-harmonized)
    c_site = FCR * capex_pd + INSURE_FRAC * capex_pd
    return c_site


def solve_bqp(n, Sigma, N, c_const, c_site, E, L):
    """
    Solve the BQP via gurobipy.

    min   x^T Sigma x
    s.t.  sum(x_i) = N
          c_const + sum x_i (c_site_i - L*E_i) <= 0
          x_i binary

    Returns (selected, status) where selected is int array of 0/1.
    """
    model = gp.Model("tidal_portfolio")
    model.Params.TimeLimit = GUROBI_TIME_LIMIT
    model.Params.MIPGap = GUROBI_MIP_GAP
    model.Params.NumericFocus = 2

    # Binary decision variables
    x = model.addMVar(n, vtype=gp.GRB.BINARY, name="x")

    # Objective: min x^T Sigma x
    model.setObjective(x @ Sigma @ x, gp.GRB.MINIMIZE)

    # Constraint 1: sum(x_i) = N
    model.addConstr(x.sum() == N, name="deploy")

    # Constraint 2: c_const + sum x_i (c_site_i - L*E_i) <= 0
    lcoe_coeffs = c_site - L * E
    model.addConstr(lcoe_coeffs @ x <= -c_const, name="lcoe")

    model.optimize()

    if model.Status in (gp.GRB.OPTIMAL, gp.GRB.SUBOPTIMAL):
        selected = np.round(x.X).astype(np.int32)
        return selected, "optimal"
    elif model.Status == gp.GRB.INFEASIBLE:
        return np.zeros(n, dtype=np.int32), "infeasible"
    elif model.Status == gp.GRB.TIME_LIMIT:
        if model.SolCount > 0:
            selected = np.round(x.X).astype(np.int32)
            return selected, "time_limit"
        return np.zeros(n, dtype=np.int32), "time_limit_no_sol"
    else:
        return np.zeros(n, dtype=np.int32), f"status_{model.Status}"


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # -----------------------------------------------------------------
    # Load data
    # -----------------------------------------------------------------
    print("Loading candidates...")
    cand = xr.open_dataset(CANDIDATES_PATH)
    n_sites = cand.sizes["site"]
    lat = cand["latitude"].values
    lon = cand["longitude"].values
    depth = cand["depth"].values
    cf = cand["capacity_factor"].values
    shore_dist = cand["shore_distance_km"].values

    # Histograms for energy computation
    hist = cand["speed_histogram"].values       # (n_sites, n_bins)
    centers = cand["speed_bin_centers"].values   # (n_bins,)
    print(f"  {n_sites:,} candidates")

    print("Loading covariance matrix...")
    cov_ds = xr.open_dataset(COVARIANCE_PATH)
    Sigma = cov_ds["covariance"].values  # (n_sites, n_sites), W^2
    cov_ds.close()
    # Rescale W^2 -> kW^2 to keep Q coefficients in a sane numerical range.
    # Pure positive scaling of the objective; argmin is unchanged. Reported
    # variance below is converted back to W^2 for consistency with prior runs.
    SIGMA_SCALE = 1e-6
    Sigma = (Sigma * SIGMA_SCALE).astype(np.float64)
    print(f"  Shape: {Sigma.shape} (scaled to kW^2)")

    # -----------------------------------------------------------------
    # Cable selection and losses per site
    # -----------------------------------------------------------------
    _tx_label = f"{STEPUP_KV} kV step-up" if STEPUP_KV is not None else "480 V (no step-up)"
    print(f"\nSelecting cables (3-phase AC, {_tx_label}; loss = {LOSS_COEFF:.4f} * R * L)...")
    cable_csa = np.zeros(n_sites, dtype=np.int32)
    cable_cost_total = np.zeros(n_sites)
    cable_loss = np.zeros(n_sites)

    for i in range(n_sites):
        csa, cost_m, loss = select_cable(shore_dist[i])
        cable_csa[i] = csa
        cable_cost_total[i] = cost_m * shore_dist[i] * 1000  # total cable $
        cable_loss[i] = loss

    n_over = np.sum(cable_loss > MAX_LOSS)
    print(f"  Sites exceeding {MAX_LOSS*100:.0f}% loss: {n_over} "
          f"({100*n_over/n_sites:.1f}%)")
    print(f"  Loss — median: {np.median(cable_loss)*100:.1f}%, "
          f"max: {cable_loss.max()*100:.1f}%")

    # -----------------------------------------------------------------
    # Energy per site (MWh/yr per device)
    # -----------------------------------------------------------------
    print("\nComputing annual energy...")
    E = np.array([compute_energy(hist[i], centers, cable_loss[i])
                  for i in range(n_sites)])
    print(f"  E range: {E.min():.1f} to {E.max():.1f} MWh/yr")
    print(f"  E median: {np.median(E):.1f} MWh/yr")

    # -----------------------------------------------------------------
    # Cost per site (c_site_i, annualized $/yr)
    # -----------------------------------------------------------------
    print("\nComputing site costs...")
    laying_costs = CABLE_INST_PER_KM * shore_dist
    c_site = np.array([compute_c_site(cable_cost_total[i], laying_costs[i])
                       for i in range(n_sites)])
    print(f"  c_site range: ${c_site.min():,.0f} to ${c_site.max():,.0f} /yr")

    # -----------------------------------------------------------------
    # Optimization sweep over P_target and LCOE target
    # -----------------------------------------------------------------
    N = int(np.ceil(P_TARGET_MW * 1000 / P_DEVICE_KW))
    print(f"\n{'='*60}")
    print(f"P_target = {P_TARGET_MW} MW -> N = {N} devices")
    print(f"{'='*60}")

    c_const = compute_c_const(N)
    print(f"C_const({N}) = ${c_const:,.0f}/yr")

    # Check feasibility: which LCOE targets can possibly work?
    # A site is feasible if c_site_i - L*E_i < 0 (cost < revenue at target)
    print("\nFeasibility check:")
    for L in LCOE_TARGETS:
        n_feasible = np.sum(c_site - L * E < 0)
        margin_best = (L * E - c_site).max()
        print(f"  L={L:>5} $/MWh: {n_feasible:>6} feasible sites "
              f"(best margin: ${margin_best:>12,.0f}/yr)")

    # Store results for each LCOE target
    results = []

    for L in LCOE_TARGETS:
        print(f"\n{'─'*60}")
        print(f"Solving: N={N}, LCOE target={L} $/MWh")
        print(f"{'─'*60}")

        # Quick feasibility: need at least N sites with c_site_i < L*E_i
        feasible_mask = (c_site - L * E) < 0
        n_feasible = feasible_mask.sum()
        if n_feasible < N:
            print(f"  INFEASIBLE: only {n_feasible} sites can meet LCOE, need {N}")
            results.append({
                "lcoe_target": L, "status": "infeasible",
                "variance": np.nan, "achieved_lcoe": np.nan,
                "selected": np.zeros(n_sites, dtype=np.int32),
            })
            continue

        # Check if constraint can be satisfied
        # Best case: pick N sites with most negative (c_site_i - L*E_i)
        margins = c_site - L * E
        best_n = np.sort(margins)[:N]
        if c_const + best_n.sum() > 0:
            print(f"  INFEASIBLE: even best {N} sites can't meet LCOE "
                  f"(slack = ${c_const + best_n.sum():,.0f})")
            results.append({
                "lcoe_target": L, "status": "infeasible",
                "variance": np.nan, "achieved_lcoe": np.nan,
                "selected": np.zeros(n_sites, dtype=np.int32),
            })
            continue

        # Restrict to sites with negative LCOE margin: any site with
        # c_site_i - L*E_i >= 0 can never be in an optimal solution at this L
        # (it would push the LCOE constraint the wrong way), so we drop them
        # before building the dense Q. This shrinks Sigma quadratically and
        # is what makes Gurobi fit in memory at n_sites ~ 18k.
        keep_idx = np.where(margins < 0)[0]
        n_red = keep_idx.size
        Sigma_red = Sigma[np.ix_(keep_idx, keep_idx)]
        c_site_red = c_site[keep_idx]
        E_red = E[keep_idx]
        print(f"  Reduced problem: {n_red} sites "
              f"(Q terms: {n_red*(n_red+1)//2:,})")

        # Solve BQP on the reduced problem
        print("  Solving with Gurobi...")
        selected_red, status = solve_bqp(
            n_red, Sigma_red, N, c_const, c_site_red, E_red, L
        )

        # Map reduced solution back to the global site index
        selected = np.zeros(n_sites, dtype=np.int32)
        selected[keep_idx] = selected_red

        if status != "optimal" and not status.startswith("time_limit"):
            print(f"  Solver status: {status}")
            results.append({
                "lcoe_target": L, "status": status,
                "variance": np.nan, "achieved_lcoe": np.nan,
                "selected": np.zeros(n_sites, dtype=np.int32),
            })
            continue

        if selected.sum() == 0:
            print(f"  No solution found (status: {status})")
            results.append({
                "lcoe_target": L, "status": status,
                "variance": np.nan, "achieved_lcoe": np.nan,
                "selected": np.zeros(n_sites, dtype=np.int32),
            })
            continue

        # Compute solution metrics
        sel = selected.astype(bool)
        n_sel = selected.sum()
        # Sigma is in kW^2 (rescaled at load); undo for reporting in W^2.
        variance = float(selected @ Sigma @ selected) / SIGMA_SCALE
        total_energy = E[sel].sum()
        total_site_cost = c_site[sel].sum()
        achieved_lcoe = (c_const + total_site_cost) / total_energy

        print(f"\n  Solution:")
        print(f"    Selected: {n_sel} sites")
        print(f"    Variance: {variance:.2e} W^2")
        print(f"    Total energy: {total_energy:.1f} MWh/yr")
        print(f"    C_const: ${c_const:,.0f}/yr")
        print(f"    Site costs: ${total_site_cost:,.0f}/yr")
        print(f"    Achieved LCOE: ${achieved_lcoe:,.0f}/MWh")
        print(f"    Lat range: {lat[sel].min():.2f} to {lat[sel].max():.2f}")
        print(f"    Lon range: {lon[sel].min():.2f} to {lon[sel].max():.2f}")

        results.append({
            "lcoe_target": L, "status": "optimal",
            "variance": variance, "achieved_lcoe": achieved_lcoe,
            "selected": selected,
        })

    # -----------------------------------------------------------------
    # Save results
    # -----------------------------------------------------------------
    print(f"\n{'='*60}")
    print("Saving results...")

    # Build arrays for all LCOE targets
    n_targets = len(LCOE_TARGETS)
    out_lcoe_target = np.array(LCOE_TARGETS, dtype=np.float64)
    out_variance = np.array([r["variance"] for r in results], dtype=np.float64)
    out_achieved_lcoe = np.array([r["achieved_lcoe"] for r in results], dtype=np.float64)
    out_status = np.array([r["status"] for r in results])
    out_selected = np.stack([r["selected"] for r in results])  # (n_targets, n_sites)

    out_ds = xr.Dataset(
        {
            # Per LCOE target
            "lcoe_target": (["target"], out_lcoe_target, {"units": "$/MWh"}),
            "variance": (["target"], out_variance, {"units": "W^2"}),
            "achieved_lcoe": (["target"], out_achieved_lcoe, {"units": "$/MWh"}),
            "status": (["target"], out_status),
            "selected": (["target", "site"], out_selected),

            # Per site (inputs for reference)
            "latitude": (["site"], lat, {"units": "degrees_north"}),
            "longitude": (["site"], lon, {"units": "degrees_east"}),
            "depth": (["site"], depth, {"units": "m"}),
            "capacity_factor": (["site"], cf.astype(np.float32)),
            "shore_distance_km": (["site"], shore_dist, {"units": "km"}),
            "cable_csa_mm2": (["site"], cable_csa),
            "cable_loss": (["site"], cable_loss.astype(np.float32)),
            "energy_mwh": (["site"], E.astype(np.float32), {"units": "MWh/yr"}),
            "c_site": (["site"], c_site.astype(np.float32), {"units": "$/yr"}),
        },
        coords={
            "target": np.arange(n_targets),
            "site": np.arange(n_sites),
        },
        attrs={
            "title": "ORPC TidGen 2.0 portfolio optimization results",
            "P_target_MW": P_TARGET_MW,
            "N_devices": N,
            "C_const": c_const,
            "loss_formula": f"{LOSS_COEFF:.4f} * R * L  (3-phase AC, "
                            f"V_tx={_V_TX_VOLTS:.0f} V, I={_I_AMPS:.1f} A, P=500 kW)",
            "stepup_kv": STEPUP_KV if STEPUP_KV is not None else 0.0,
            "transformer_cost_per_device": C_TRANSFORMER_PER_DEVICE,
            "solver": "Gurobi via gurobipy",
            "created": datetime.now(timezone.utc).isoformat(),
        },
    )

    cand.close()
    out_path = RESULTS_PATH
    encoding = {v: {"zlib": True, "complevel": 4}
                for v in out_ds.data_vars
                if out_ds[v].dtype in (np.float32, np.float64, np.int32)}
    out_ds.to_netcdf(out_path, encoding=encoding)
    out_ds.close()

    print(f"Saved: {out_path}")

    # Summary table
    print(f"\n{'='*60}")
    print(f"{'LCOE Target':>12} {'Status':>12} {'Variance':>14} {'Achieved':>10}")
    print(f"{'($/MWh)':>12} {'':>12} {'(W^2)':>14} {'($/MWh)':>10}")
    print(f"{'─'*60}")
    for r in results:
        if r["status"] == "optimal":
            print(f"{r['lcoe_target']:>12,.0f} {'optimal':>12} "
                  f"{r['variance']:>14.2e} {r['achieved_lcoe']:>10,.0f}")
        else:
            print(f"{r['lcoe_target']:>12,.0f} {r['status']:>12} "
                  f"{'—':>14} {'—':>10}")
    print(f"{'='*60}")
    print("Done.")


if __name__ == "__main__":
    main()
