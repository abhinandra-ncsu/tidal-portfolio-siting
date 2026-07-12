"""
Centralized parameters for the ORPC TidGen 2.0 portfolio optimization.

All Python scripts in this folder import from this module instead of
defining their own copies. Sources are documented inline; see
methodology/ (alongside this folder) for full derivations.
"""

import os
import numpy as np

# =========================================================================
# Per-state run selection (same env-var protocol as the VP pipeline)
# =========================================================================
_state_env = os.environ.get("TIDAL_STATE", "").strip()
STATES = [s.strip() for s in _state_env.split(",") if s.strip()] or None
STATE = STATES[0] if STATES and len(STATES) == 1 else None
GROUP = os.environ.get("TIDAL_GROUP", "").strip() or None

_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
_OPT_DIR = os.path.dirname(_CONFIG_DIR)              # .../optimization/orpc
_ROOT_DIR = os.path.dirname(os.path.dirname(_OPT_DIR))  # repo root


def get_results_dir():
    """Return the results directory for the current run.

    Resolution order:
      1. TIDAL_RESULTS_DIR env var (absolute path), if set.
      2. <repo>/results/orpc/groups/<TIDAL_GROUP>/ if TIDAL_GROUP is set.
      3. <repo>/results/orpc/states/<single_state>/ if exactly one state is selected.
      4. <repo>/results/orpc/groups/pooled/ otherwise.
    """
    override = os.environ.get("TIDAL_RESULTS_DIR")
    if override:
        return override
    if GROUP:
        return os.path.join(_ROOT_DIR, "results", "orpc", "groups", GROUP)
    if STATES and len(STATES) == 1:
        return os.path.join(_ROOT_DIR, "results", "orpc", "states", STATES[0])
    return os.path.join(_ROOT_DIR, "results", "orpc", "groups", "pooled")

# =========================================================================
# ORPC TidGen 2.0 turbine (turbine_design_specification.md)
# =========================================================================
RHO = 1025.0              # seawater density (kg/m^3)
V_CUT_IN = 0.5            # cut-in speed (m/s) — SCM first non-zero
V_RATED = 3.0             # rated speed (m/s) — SCM electrical reaches 500 kW
V_PLATEAU_END = 3.5       # max operational speed (m/s); zero past this
P_TURBINE_KW = 500.0      # rated electrical power per device (kW)
P_RATED_W = P_TURBINE_KW * 1000

# Single device per site. SCM power curve already aggregates the device's
# 2 TGUs / 8 rotors, so this multiplier is just a structural hook and = 1.
DEVICES_PER_SITE = 1
P_DEVICE_KW = P_TURBINE_KW * DEVICES_PER_SITE  # 500 kW

# SCM-tabulated electrical power curve (D7.2.8 SCM workbook,
# `CEC Resource and Power` sheet column F, rows 12–42).
# Speeds in m/s, electrical power in kW.
# Below 0.5 m/s: 0 (cut-in). At 3.0 m/s: 499.13 kW (regulation reaches rated).
# 3.0 < u <= 3.5 m/s: plateau at P_TURBINE_KW (our convention).
# u > 3.5 m/s: 0 (cutout, per design).
SCM_SPEEDS_MS = np.arange(0.0, 3.01, 0.1)
SCM_POWER_KW = np.array([
    0.0,           # 0.0
    0.0,           # 0.1
    0.0,           # 0.2
    0.0,           # 0.3
    0.0,           # 0.4
    2.74828125,    # 0.5  — Cp = 0.39 region begins
    4.74903,       # 0.6
    7.54128375,    # 0.7
    11.25696,      # 0.8
    16.02797625,   # 0.9
    21.98625,      # 1.0
    29.26369875,   # 1.1
    37.99224,      # 1.2
    48.30379125,   # 1.3
    60.33027,      # 1.4
    74.20359375,   # 1.5
    90.05568,      # 1.6
    108.01844625,  # 1.7
    128.22381,     # 1.8
    150.80368875,  # 1.9
    175.89,        # 2.0
    203.61466125,  # 2.1
    234.10959,     # 2.2
    267.50670375,  # 2.3
    303.93792,     # 2.4  — declining-Cp regulation begins
    338.56064564,  # 2.5
    371.97404738,  # 2.6
    404.66591768,  # 2.7
    436.71356348,  # 2.8
    468.18362869,  # 2.9
    499.13387137,  # 3.0
])

# =========================================================================
# Energy parameters (energy/methodology.md)
# =========================================================================
HOURS_PER_YEAR = 8766     # Julian year (365.25 * 24)
ETA_AVAIL = 0.92          # operational availability (LCOE Metrics C24)

# =========================================================================
# Electrical parameters (cost/capex/electrical/{methodology,source_data}.md)
# =========================================================================
MAX_LOSS = 0.10           # maximum acceptable cable loss (10%)
PF = 0.95                 # power factor (DNV GL 2015; Nakhai 2023 Table 1)

# Transmission step-up. The ORPC baseline mirrors VP: each device steps its
# 480 V generation up to 6.6 kV at the seabed before transmitting on its own
# radial 3-core AC cable (electrical/methodology.md). STEPUP_KV is the step-up
# voltage in kV; set TIDAL_STEPUP_KV=0 (or none/off) to model the 480 V
# comparison arm (no step-up, transformer cost = $0).
_stepup_env = os.environ.get("TIDAL_STEPUP_KV", "").strip().lower()
if _stepup_env in ("0", "none", "off"):
    STEPUP_KV = None                       # 480 V comparison arm
elif _stepup_env:
    STEPUP_KV = float(_stepup_env)
else:
    STEPUP_KV = 6.6                        # baseline: 480 V -> 6.6 kV step-up

# 3-core AC cable table: (CSA mm^2, R ohm/km, cost $/m). Same catalog as VP
# (ABB Rev 5 Table 41, 10 kV three-core; the 10 kV class covers 6.6 kV).
# Cost per Nakhai (2023) Eq. 3, 3-phase AC (4 conductors): $/m = 4 * 0.3476 * CSA.
# Resistance from copper resistivity: R = 0.0178 * 1000 / CSA (ohm/km).
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

# Step-up transformer cost — Collin 2017 Eq. 2, LV:MV Wet (same coefficients
# as VP). Applied per device to S = P_device / PF (MVA); $0 when step-up is off.
# S = 0.500 / 0.95 = 0.526 MVA -> ~$354k/device. See electrical/methodology.md.
if STEPUP_KV is not None:
    _S_mva = (P_DEVICE_KW / PF) / 1000.0
    C_TRANSFORMER_PER_DEVICE = 454_800.0 * _S_mva**0.6329 + 51_115.0
else:
    C_TRANSFORMER_PER_DEVICE = 0.0

# =========================================================================
# Cost parameters — Device (capex/capex_cost_components.md §1)
# =========================================================================
C_DEVICE_UNIT1 = 3_182_500.0                          # $ per device (CBS 1.1)
LEARNING_RATE = 0.10                                   # ORPC LCOE Whitepaper
LEARNING_EXP = np.log(1 - LEARNING_RATE) / np.log(2)   # b = -0.152

# =========================================================================
# Cost parameters — Installation (capex/installation/methodology.md)
# =========================================================================
TUG_DAY_RATE = 3_641.0                # $/day (Mattia tier-2 tug, 3,371 EUR × 1.08)
MULTICAT_DAY_RATE = 3_732.0           # $/day (Mattia tier-1 multicat, 3,456 EUR × 1.08)
TUG_DAYS_PER_DEVICE = 1.0             # tow time per device
MULTICAT_DAYS_PER_DEVICE = 7.33       # 4 lines × (12+22+10) h / 24
TRANSIT_DAYS = 2.0                    # one-way transit (tug + multicat)
MOORING_MAT_PER_DEVICE = 40_000.0     # $/device (CBS-A30 1.2.8)

# Cable installation: per-meter bundled metric (Mattia Eqs. 72-74).
# Bundles vessel charter (CLV), drilling rig, mob, crew, consumables.
# c_blend = (2/3)×100 + (1/3)×282 = 160.67 €/m × 1.08 USD/EUR × 1000 m/km
CABLE_INST_PER_KM = 173_523.6    # $/km

# =========================================================================
# Cost parameters — Percentages (Hassan 2024)
# =========================================================================
SUBSYS_FRAC = 0.10
CONTIN_FRAC = 0.10
EC_FRAC = 0.05
INSURE_FRAC = 0.0    # ORPC OpEx is bundled — insurance not added separately

# =========================================================================
# Cost parameters — OpEx (cost/opex/opex_cost_components.md)
# =========================================================================
# ORPC publishes a single bundled per-device annual OpEx; no replace/repair
# split, no separate insurance term.
OPEX_FIXED_PER_TF = 160_422.0          # $/yr per device (LCOE Summary F7)

# =========================================================================
# Annualization
# =========================================================================
FCR = 0.113

# =========================================================================
# Filtering thresholds
# =========================================================================
MIN_DEPTH_M = float(os.environ.get("TIDAL_MIN_DEPTH_M", 18.0))   # ORPC min
MAX_DEPTH_M = float(os.environ.get("TIDAL_MAX_DEPTH_M", 40.0))   # ORPC max
CF_THRESHOLD = 0.05
BBOX_BUFFER_DEG = 0.15

# =========================================================================
# Optimization sweep
# =========================================================================
P_TARGET_MW = float(os.environ.get("TIDAL_P_TARGET_MW", 50.0))  # target power (MW); TIDAL_P_TARGET_MW env var overrides
_lcoe_env = os.environ.get("TIDAL_LCOE_TARGETS", "").strip()
LCOE_TARGETS = [int(x) for x in _lcoe_env.split(",")] if _lcoe_env else list(range(700, 1501, 100))  # $/MWh; TIDAL_LCOE_TARGETS env var overrides (comma-separated)

# =========================================================================
# Solver settings
# =========================================================================
GUROBI_TIME_LIMIT = 1800
GUROBI_MIP_GAP = 0.02
