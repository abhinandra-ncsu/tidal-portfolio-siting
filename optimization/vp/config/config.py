"""
Centralized parameters for the tidal portfolio optimization pipeline.

All Python scripts (01_extract_harmonics, 03_screen_candidates, 05_optimize)
import from this module instead of defining their own copies.

Sources are documented inline; see docs/ for full derivations.
"""

import os
import numpy as np

# =========================================================================
# Per-state run selection
# =========================================================================
# STATES: list of state names (matching the State column of
# east_coast_state_boundaries.csv) to include in this run.
# None / empty  -> pooled east-coast run (all bboxes).
# Set via TIDAL_STATE env var — single name or comma-separated list.
# TIDAL_GROUP names the results subdir when a group of states is selected
# (e.g. "new_england"); otherwise the subdir is the single state name or
# "pooled".
_state_env = os.environ.get("TIDAL_STATE", "").strip()
STATES = [s.strip() for s in _state_env.split(",") if s.strip()] or None
# Legacy single-state alias (None when STATES has >1 entry).
STATE = STATES[0] if STATES and len(STATES) == 1 else None
GROUP = os.environ.get("TIDAL_GROUP", "").strip() or None

_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
_VP_DIR = os.path.dirname(_CONFIG_DIR)
_OPT_DIR = os.path.dirname(_VP_DIR)
_ROOT_DIR = os.path.dirname(_OPT_DIR)

# =========================================================================
# Turbine variant family — experiments/turbine_modification/EXPERIMENT.md
# =========================================================================
VARIANTS = {
    "gen5":   {"D": 5.0, "area": 19.63, "v_rated": 2.03, "v_cut_in": 0.61,
               "p_turbine_kw": 31.2, "c_device": 1_402_500.0, "min_depth_m": 10.0},
    "modvp4": {"D": 4.0, "area": 12.57, "v_rated": 2.33, "v_cut_in": 0.70,
               "p_turbine_kw": 30.1, "c_device":   967_000.0, "min_depth_m":  8.0},
    "modvp3": {"D": 3.0, "area":  7.07, "v_rated": 2.32, "v_cut_in": 0.70,
               "p_turbine_kw": 16.8, "c_device":   640_500.0, "min_depth_m":  6.0},
    "modvp2": {"D": 2.0, "area":  3.14, "v_rated": 2.22, "v_cut_in": 0.67,
               "p_turbine_kw":  6.5, "c_device":   417_000.0, "min_depth_m":  4.0},
}

_variant_env = os.environ.get("TIDAL_VARIANT", "").strip().lower()
VARIANT = _variant_env or "gen5"
if VARIANT not in VARIANTS:
    raise ValueError(f"Unknown TIDAL_VARIANT={VARIANT!r}; expected one of {list(VARIANTS)}")
_v = VARIANTS[VARIANT]


def get_results_dir():
    """Return the results directory for the current run.

    Resolution order:
      1. TIDAL_RESULTS_DIR env var (absolute path), if set.
      2. <repo>/results/vp/turbine_modification/<variant>/{groups,states}/<scope>/
         when TIDAL_VARIANT is explicitly set.
      3. <repo>/results/vp/groups/<TIDAL_GROUP>/ if TIDAL_GROUP is set.
      4. <repo>/results/vp/states/<single_state>/ if exactly one state is selected.
      5. <repo>/results/vp/groups/pooled/ otherwise.
    """
    override = os.environ.get("TIDAL_RESULTS_DIR")
    if override:
        return override
    base = os.path.join(_ROOT_DIR, "results", "vp")
    if _variant_env:
        base = os.path.join(base, "turbine_modification", VARIANT)
    if GROUP:
        return os.path.join(base, "groups", GROUP)
    if STATES and len(STATES) == 1:
        return os.path.join(base, "states", STATES[0])
    return os.path.join(base, "groups", "pooled")

# =========================================================================
# VP turbine — values resolved from VARIANTS[VARIANT] (see EXPERIMENT.md)
# =========================================================================
RHO = 1025.0                       # seawater density (kg/m^3)
CP = 0.37                          # power coefficient (Lewis et al. 2021, held across family)
AREA = _v["area"]                  # swept area (m^2)
V_CUT_IN = _v["v_cut_in"]          # cut-in speed (m/s)
V_RATED = _v["v_rated"]            # rated speed (m/s)
P_TURBINE_KW = _v["p_turbine_kw"]  # rated power per turbine (kW)
P_RATED_W = P_TURBINE_KW * 1000    # rated power per turbine (W)
TURBINES_PER_TF = 3
P_TRIFRAME_KW = P_TURBINE_KW * TURBINES_PER_TF

# =========================================================================
# Energy parameters (energy/methodology.md)
# =========================================================================
HOURS_PER_YEAR = 8766    # Julian year (365.25 * 24)
ETA_AVAIL = 0.95         # operational availability (Sandia SAND2014-9040)

# =========================================================================
# Electrical parameters (../methodology/cost/capex/electrical/source_data.md)
# =========================================================================
MAX_LOSS = 0.10          # maximum acceptable cable loss (10%)

# Cable table: (CSA mm^2, R ohm/km, cost $/m)
# Cost from Nakhai 2023 Eq.3: 4 * 0.3476 * CSA
CABLES = [
    (70,  0.254, 4 * 0.3476 * 70),
    (95,  0.187, 4 * 0.3476 * 95),
    (120, 0.148, 4 * 0.3476 * 120),
    (150, 0.119, 4 * 0.3476 * 150),
    (185, 0.096, 4 * 0.3476 * 185),
    (240, 0.074, 4 * 0.3476 * 240),
    (300, 0.059, 4 * 0.3476 * 300),
    (400, 0.045, 4 * 0.3476 * 400),
    (500, 0.036, 4 * 0.3476 * 500),
]

# =========================================================================
# Cost parameters — Device (../methodology/cost/capex/capex_cost_components.md)
# =========================================================================
C_DEVICE_UNIT1 = _v["c_device"]            # $ per TriFrame (unit 1), variant-dependent
LEARNING_RATE = 0.12                       # 12% (Hassan 2024)
LEARNING_EXP = np.log(1 - LEARNING_RATE) / np.log(2)  # b = -0.1699

# =========================================================================
# Cost parameters — Installation (../methodology/cost/capex/installation/methodology.md)
# =========================================================================
JACKUP_DAY_RATE = 33_647.0       # $/day (Mattia 2025: 31,155 EUR/day × 1.08)
PLACEMENT_DAYS_PER_TF = 1.5      # device placement time per TriFrame (days)
TRANSIT_DAYS = 2.0               # jack-up mob/demob each side of work (days)

# Cable installation: per-meter bundled metric (Mattia Eqs. 72-74).
# Bundles vessel charter, drilling rig, mob, crew, consumables.
# c_blend = (2/3)×100 + (1/3)×282 = 160.67 €/m × 1.08 USD/EUR × 1000 m/km
CABLE_INST_PER_KM = 173_523.6    # $/km

# =========================================================================
# Cost parameters — Percentages (Hassan 2024)
# =========================================================================
SUBSYS_FRAC = 0.10    # subsystem integration
CONTIN_FRAC = 0.10    # contingency
EC_FRAC = 0.05        # environmental compliance
INSURE_FRAC = 0.01    # insurance (annual, on CapEx)

# =========================================================================
# Cost parameters — OpEx (../methodology/cost/opex/opex_cost_components.md)
# =========================================================================
OPEX_REPLACE = 74_804.0                    # $/yr per TriFrame
OPEX_REPAIR = 37_619.0                     # $/yr per TriFrame ($4,355 vessel + $33,264 labor)
OPEX_FIXED_PER_TF = OPEX_REPLACE + OPEX_REPAIR  # $112,423/yr

# =========================================================================
# Annualization
# =========================================================================
FCR = 0.113              # Fixed Charge Rate (11.3%)

# =========================================================================
# Filtering thresholds
# =========================================================================
MIN_DEPTH_M = float(os.environ.get("TIDAL_MIN_DEPTH_M", _v["min_depth_m"]))  # min water depth (m); variant default, TIDAL_MIN_DEPTH_M env var overrides
CF_THRESHOLD = 0.05      # capacity factor screening threshold
BBOX_BUFFER_DEG = 0.15   # buffer added to state bounding boxes (degrees)

# =========================================================================
# Optimization sweep
# =========================================================================
P_TARGET_MW = float(os.environ.get("TIDAL_P_TARGET_MW", 5.25))  # target power (MW); TIDAL_P_TARGET_MW env var overrides
_lcoe_env = os.environ.get("TIDAL_LCOE_TARGETS", "").strip()
LCOE_TARGETS = [int(x) for x in _lcoe_env.split(",")] if _lcoe_env else [800, 1200, 2000]  # $/MWh; TIDAL_LCOE_TARGETS env var overrides (comma-separated)

# =========================================================================
# Solver settings
# =========================================================================
GUROBI_TIME_LIMIT = 1800   # seconds
GUROBI_MIP_GAP = 0.02      # 2%
