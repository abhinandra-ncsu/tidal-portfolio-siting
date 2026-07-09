"""
Step 5: Tidal portfolio optimization.

Computes all cost and energy inputs from the documented formulas, then
solves the Binary Quadratic Program:

    min   x^T Sigma x                              (portfolio variance)
    s.t.  sum(x_i) = N                             (deploy N TriFrames)
          C_const(N) + sum x_i (c_site_i - L*E_i) <= 0   (LCOE ceiling)
          x_i in {0,1}

Under TIDAL_OBJECTIVE=energy the objective becomes  max sum(E_i x_i)  with the
same constraints — a linear ILP. See experiments/max_energy_objective/EXPERIMENT.md.

Input:  ../results/candidates.nc  (from 03_screen_candidates.py)
        ../results/covariance.nc  (from compute_covariance.m)
Output: ../results/optimization_results.nc

References (all under methodology/):
    - optimization_formulation.md
    - energy/methodology.md
    - cost/optimization_cost_structure.md
    - cost/capex/capex_cost_components.md
    - cost/capex/installation/methodology.md
    - cost/opex/opex_cost_components.md
"""

import os
from datetime import datetime, timezone

import gurobipy as gp
import numpy as np
import xarray as xr

from config.config import (
    # Turbine
    P_TURBINE_KW, TURBINES_PER_TF, P_TRIFRAME_KW,
    RHO, AREA, CP, V_CUT_IN, V_RATED,
    # Energy
    HOURS_PER_YEAR, ETA_AVAIL,
    # Electrical
    MAX_LOSS, CABLES,
    # Transmission step-up (experiments/transmission_stepup/EXPERIMENT.md)
    STEPUP_KV, C_TRANSFORMER_PER_TF,
    # Cost — device
    C_DEVICE_UNIT1, LEARNING_EXP,
    # Cost — installation
    JACKUP_DAY_RATE, PLACEMENT_DAYS_PER_TF, TRANSIT_DAYS, CABLE_INST_PER_KM,
    # Cost — percentages
    SUBSYS_FRAC, CONTIN_FRAC, EC_FRAC, INSURE_FRAC,
    # Cost — OpEx
    OPEX_FIXED_PER_TF,
    # Annualization
    FCR,
    # Optimization
    P_TARGET_MW, LCOE_TARGETS, OBJECTIVE,
    # Solver
    GUROBI_TIME_LIMIT, GUROBI_MIP_GAP,
    get_results_dir, get_curve_dir,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

RESULTS_DIR = get_results_dir()

# candidates.nc / covariance.nc live at the curve level (shared across
# capacities); the optimizer reads them from the curve dir and writes its
# per-capacity result into RESULTS_DIR. TIDAL_CURVE_DIR falls back to
# RESULTS_DIR when unset.
_CURVE_DIR = get_curve_dir()
CANDIDATES_PATH = os.path.join(_CURVE_DIR, "candidates.nc")
COVARIANCE_PATH = os.path.join(_CURVE_DIR, "covariance.nc")
RESULTS_PATH = os.path.join(RESULTS_DIR, "optimization_results.nc")

# Loss formula: 3 * I^2 * R * L / P, with I = P_TF / (sqrt(3) * V * PF).
# PF = 0.95 held constant across the variant family. Generation voltage is
# 480 V baseline; the transmission step-up experiment overrides to STEPUP_KV
# (see experiments/transmission_stepup/EXPERIMENT.md).
_V_GEN_VOLTS = (STEPUP_KV * 1000.0) if STEPUP_KV is not None else 480.0
_PF = 0.95
_I_AMPS = (P_TRIFRAME_KW * 1000.0) / (np.sqrt(3.0) * _V_GEN_VOLTS * _PF)
LOSS_COEFF = 3.0 * _I_AMPS**2 / (P_TRIFRAME_KW * 1000.0)


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
    Annual energy delivered per TriFrame at a site (MWh/yr).

    E_i = (8766/1000) * eta_avail * (1-loss) * n_t
          * sum_k P(u_k) * p_i(u_k)

    where sum_k P(u_k)*p_i(u_k) is mean power per turbine in W.
    Drivetrain efficiencies are omitted because Lewis et al. (2021) Cp
    is a system Cp (already net of gearbox/generator losses) — see
    docs/energy/methodology.md.
    """
    # Power at each speed bin center (W)
    power_curve = np.zeros(len(centers))
    for k, v in enumerate(centers):
        if v < V_CUT_IN:
            power_curve[k] = 0.0
        elif v <= V_RATED:
            power_curve[k] = 0.5 * RHO * AREA * CP * v**3
        else:
            power_curve[k] = P_TURBINE_KW * 1000  # 35,000 W

    mean_power_w = hist @ power_curve  # W per turbine
    # Doc formula gives kWh (8766/1000 * W = kWh); divide by 1000 more for MWh
    energy_mwh = (HOURS_PER_YEAR / 1e6 * ETA_AVAIL
                  * (1 - loss) * TURBINES_PER_TF * mean_power_w)
    return energy_mwh


def compute_c_const(N):
    """
    Annualized project-level constant cost C_const(N).

    Includes: device manufacturing (learning curve), device installation,
    subsystem integration, constant portions of contingency/compliance/
    insurance, and fixed OpEx. Cable installation is fully portfolio-
    dependent (Mattia per-meter bundled metric).
    """
    # Device manufacturing with learning curve
    units = np.arange(1, N + 1, dtype=np.float64)
    c_device_total = C_DEVICE_UNIT1 * np.sum(units ** LEARNING_EXP)

    # Device installation
    device_days = 2 * TRANSIT_DAYS + PLACEMENT_DAYS_PER_TF * N
    c_inst_device = device_days * JACKUP_DAY_RATE

    # Subsystem integration
    c_subsys = SUBSYS_FRAC * c_device_total

    # Contingency (constant portion). Cable installation is fully
    # portfolio-dependent (Mattia per-meter bundled metric); no constant
    # contribution from cables.
    c_contin_const = CONTIN_FRAC * (c_device_total + c_subsys + c_inst_device)

    # Environmental compliance (constant portion)
    c_ec_const = EC_FRAC * (c_device_total + c_subsys + c_contin_const)

    # Step-up transformer (zero when step-up is off — see experiments/transmission_stepup).
    # Treated like the cable/electrical items: added as raw CapEx so FCR + insurance
    # apply, but NOT the contingency/EC cascade.
    c_transformer = N * C_TRANSFORMER_PER_TF

    # Total constant CapEx
    capex_const = (c_device_total + c_inst_device + c_subsys
                   + c_contin_const + c_ec_const + c_transformer)

    # Annualized constant cost
    annual_capex = FCR * capex_const
    annual_opex = OPEX_FIXED_PER_TF * N
    annual_insurance_const = INSURE_FRAC * capex_const

    c_const = annual_capex + annual_opex + annual_insurance_const
    return c_const


def compute_c_site(cable_cost_total, laying_cost):
    """
    Annualized portfolio-dependent cost for a single site.

    Includes cable purchase, cable laying, and cascading percentages
    (contingency, compliance, insurance) on the portfolio-dependent portion.
    """
    # Contingency on laying
    contin_pd = CONTIN_FRAC * laying_cost

    # Compliance on contingency
    ec_pd = EC_FRAC * contin_pd

    # Total portfolio-dependent CapEx for this site
    capex_pd = cable_cost_total + laying_cost + contin_pd + ec_pd

    # Annualized: FCR * CapEx + insurance on PD CapEx
    c_site = FCR * capex_pd + INSURE_FRAC * capex_pd
    return c_site


def solve_bqp(n, Sigma, N, c_const, c_site, E, L):
    """
    Solve the site-selection program via gurobipy.

    min   x^T Sigma x        (OBJECTIVE == "variance": BQP)
    or
    max   sum(E_i x_i)       (OBJECTIVE == "energy": linear ILP)
    s.t.  sum(x_i) = N
          c_const + sum x_i (c_site_i - L*E_i) <= 0
          x_i binary

    Returns (selected, status) where selected is int array of 0/1.
    """
    model = gp.Model("tidal_portfolio")
    model.Params.TimeLimit = GUROBI_TIME_LIMIT
    model.Params.MIPGap = GUROBI_MIP_GAP
    model.Params.NumericFocus = 2
    if OBJECTIVE == "energy":
        # The ILP solves in seconds; the BQP's 2% gap would leave E_max
        # non-monotone in L and corrupt the top-N degeneracy flag. Solve
        # to proven optimality.
        model.Params.MIPGap = 0.0

    # Binary decision variables
    x = model.addMVar(n, vtype=gp.GRB.BINARY, name="x")

    # Objective: min portfolio variance, or max delivered energy
    if OBJECTIVE == "energy":
        model.setObjective(E @ x, gp.GRB.MAXIMIZE)
    else:
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
    print("\nSelecting cables (loss formula: 0.505 * R * L)...")
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
    # Energy per site (MWh/yr per TriFrame)
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
    N = int(np.ceil(P_TARGET_MW * 1000 / P_TRIFRAME_KW))
    print(f"\n{'='*60}")
    print(f"P_target = {P_TARGET_MW} MW -> N = {N} TriFrames")
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

        margins = c_site - L * E

        if OBJECTIVE != "energy":
            # Screen-consistent pre-check: the margin<0 reduction below needs
            # at least N sites to pick from. (Skipped under max-energy, where
            # positive-margin sites stay selectable.)
            n_feasible = (margins < 0).sum()
            if n_feasible < N:
                print(f"  INFEASIBLE: only {n_feasible} sites can meet LCOE, need {N}")
                results.append({
                    "lcoe_target": L, "status": "infeasible",
                    "variance": np.nan, "achieved_lcoe": np.nan,
                    "selected": np.zeros(n_sites, dtype=np.int32),
                })
                continue

        # Exact feasibility check (objective-independent): the N most negative
        # margins are the best case the LCOE constraint can ever see.
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

        if OBJECTIVE == "energy":
            # Keep every site: a positive-margin site can be optimal when other
            # sites' slack pays for it (experiments/max_energy_objective/
            # EXPERIMENT.md, trap 1). The linear objective builds no dense Q,
            # so the full problem fits; Sigma stays unsliced (unused by the
            # solve, read only for post-hoc variance reporting).
            keep_idx = np.arange(n_sites)
            Sigma_red = Sigma
            print(f"  Full problem: {n_sites} sites (linear objective)")
        else:
            # Restrict to sites with negative LCOE margin: any site with
            # c_site_i - L*E_i >= 0 can never be in an optimal solution at this L
            # (it would push the LCOE constraint the wrong way), so we drop them
            # before building the dense Q. This shrinks Sigma quadratically and
            # is what makes Gurobi fit in memory at n_sites ~ 18k.
            keep_idx = np.where(margins < 0)[0]
            Sigma_red = Sigma[np.ix_(keep_idx, keep_idx)]
            print(f"  Reduced problem: {keep_idx.size} sites "
                  f"(Q terms: {keep_idx.size*(keep_idx.size+1)//2:,})")
        n_red = keep_idx.size
        c_site_red = c_site[keep_idx]
        E_red = E[keep_idx]

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
        # LCOE-constraint slack ($/yr): ~0 = binding, >0 = loose. Under the
        # energy objective, loose means the solve degenerated to top-N-by-E
        # (EXPERIMENT.md, degeneracy check); the set comparison itself is
        # derived offline from the per-site fields saved below.
        lcoe_slack = -(c_const + total_site_cost - L * total_energy)

        print(f"\n  Solution:")
        print(f"    Selected: {n_sel} sites")
        print(f"    Variance: {variance:.2e} W^2")
        print(f"    Total energy: {total_energy:.1f} MWh/yr")
        print(f"    C_const: ${c_const:,.0f}/yr")
        print(f"    Site costs: ${total_site_cost:,.0f}/yr")
        print(f"    Achieved LCOE: ${achieved_lcoe:,.0f}/MWh")
        print(f"    LCOE slack: ${lcoe_slack:,.0f}/yr")
        print(f"    Lat range: {lat[sel].min():.2f} to {lat[sel].max():.2f}")
        print(f"    Lon range: {lon[sel].min():.2f} to {lon[sel].max():.2f}")

        results.append({
            "lcoe_target": L, "status": "optimal",
            "variance": variance, "achieved_lcoe": achieved_lcoe,
            "lcoe_slack": lcoe_slack,
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
    # .get: infeasible/error rows carry no slack
    out_lcoe_slack = np.array([r.get("lcoe_slack", np.nan) for r in results],
                              dtype=np.float64)
    out_status = np.array([r["status"] for r in results])
    out_selected = np.stack([r["selected"] for r in results])  # (n_targets, n_sites)

    out_ds = xr.Dataset(
        {
            # Per LCOE target
            "lcoe_target": (["target"], out_lcoe_target, {"units": "$/MWh"}),
            "variance": (["target"], out_variance, {"units": "W^2"}),
            "achieved_lcoe": (["target"], out_achieved_lcoe, {"units": "$/MWh"}),
            "lcoe_slack": (["target"], out_lcoe_slack, {"units": "$/yr"}),
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
            "title": "Tidal portfolio optimization results",
            "P_target_MW": P_TARGET_MW,
            "N_triframes": N,
            "C_const": c_const,
            "loss_formula": "0.505 * R * L",
            "objective": OBJECTIVE,
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
