"""
Centralized parameters for the tidal portfolio optimization pipeline.

All Python scripts (01_extract_harmonics, 03_screen_candidates, 05_optimize)
import from this module instead of defining their own copies.

Sources are documented inline; see docs/ for full derivations.
"""

import numpy as np

# =========================================================================
# VP Gen5 turbine (Lewis et al. 2021, turbine_design_specification.md)
# =========================================================================
RHO = 1025.0            # seawater density (kg/m^3)
AREA = 19.63             # swept area (m^2), D = 5 m
CP = 0.37                # power coefficient (system Cp, net of drivetrain)
V_CUT_IN = 0.63          # cut-in speed (m/s), 0.3 * V_rated
V_RATED = 2.11           # rated speed (m/s)
P_TURBINE_KW = 35.0      # rated power per turbine (kW)
P_RATED_W = P_TURBINE_KW * 1000  # rated power per turbine (W)
TURBINES_PER_TF = 3
P_TRIFRAME_KW = P_TURBINE_KW * TURBINES_PER_TF  # 105 kW

# =========================================================================
# Energy parameters (energy/methodology.md)
# =========================================================================
HOURS_PER_YEAR = 8766    # Julian year (365.25 * 24)
ETA_AVAIL = 0.95         # operational availability (Sandia SAND2014-9040)

# =========================================================================
# Electrical parameters (cost/capex/electrical/source_data.md)
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
# Cost parameters — Device (capex_cost_components.md)
# =========================================================================
C_DEVICE_UNIT1 = 1_402_500.0              # $ per TriFrame (unit 1)
LEARNING_RATE = 0.12                       # 12% (Hassan 2024)
LEARNING_EXP = np.log(1 - LEARNING_RATE) / np.log(2)  # b = -0.1699

# =========================================================================
# Cost parameters — Installation (installation/methodology.md)
# =========================================================================
JACKUP_DAY_RATE = 33_960.0       # $/day (Mattia 2025, EUR converted)
CLV_DAY_RATE = 62_400.0          # $/day (Mattia 2025, EUR converted)
PLACEMENT_DAYS_PER_TF = 1.5      # device placement time per TriFrame (days)
TRANSIT_DAYS = 2.0               # one-way transit time (days)

# Cable laying speeds (Mattia Eqs. 72-74)
SURFACE_SPEED_KMH = 1.0          # surface laying (km/h)
BURIAL_SPEED_KMH = 0.355         # burial in drilled duct (km/h)
SURFACE_FRACTION = 2.0 / 3.0     # fraction laid on surface
BURIAL_FRACTION = 1.0 / 3.0      # fraction buried

# =========================================================================
# Cost parameters — Percentages (Hassan 2024)
# =========================================================================
SUBSYS_FRAC = 0.10    # subsystem integration
CONTIN_FRAC = 0.10    # contingency
EC_FRAC = 0.05        # environmental compliance
INSURE_FRAC = 0.01    # insurance (annual, on CapEx)

# =========================================================================
# Cost parameters — OpEx (opex_cost_components.md)
# =========================================================================
OPEX_REPLACE = 74_804.0                    # $/yr per TriFrame
OPEX_REPAIR = 55_039.0                     # $/yr per TriFrame
OPEX_FIXED_PER_TF = OPEX_REPLACE + OPEX_REPAIR  # $129,843/yr

# =========================================================================
# Annualization
# =========================================================================
FCR = 0.113              # Fixed Charge Rate (11.3%)

# =========================================================================
# Filtering thresholds
# =========================================================================
MIN_DEPTH_M = 10.0       # minimum water depth (m)
CF_THRESHOLD = 0.05      # capacity factor screening threshold
BBOX_BUFFER_DEG = 0.15   # buffer added to state bounding boxes (degrees)

# =========================================================================
# Optimization sweep
# =========================================================================
P_TARGET_MW = 5.25       # target power (MW), = 50 TriFrames at 105 kW
LCOE_TARGETS = [700, 800, 900, 1000, 1200, 1500, 2000]  # $/MWh

# =========================================================================
# Solver settings
# =========================================================================
GUROBI_TIME_LIMIT = 1800   # seconds
GUROBI_MIP_GAP = 0.02      # 2%
