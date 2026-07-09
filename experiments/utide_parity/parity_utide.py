"""Reconstruct one site with utide, compare element-wise to MATLAB t_predic.

Run order:
  1) /Applications/MATLAB_R2026a.app/bin/matlab -batch "parity_matlab"
     (in this directory; writes parity_matlab.mat)
  2) python parity_utide.py
"""
import datetime as dt
import os

import numpy as np
import scipy.io
import xarray as xr
from utide._reconstruct import reconstruct
from utide._time_conversion import _normalize_time
from utide._ut_constants import ut_constants
from utide.utilities import Bunch

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

HARMONICS = os.path.join(REPO, "results", "vp", "groups", "pooled", "harmonics.nc")
MAT_FILE = os.path.join(SCRIPT_DIR, "parity_matlab.mat")

# --- Load harmonics, same point as MATLAB script ---
ds = xr.open_dataset(HARMONICS)
ipt = 0  # change to probe another site (must match parity_matlab.m's ipt-1)
valid_idx = [0, 1, 3, 4, 5, 6, 7, 8, 9]   # skip P1 (index 2 here, 0-based)
valid_names = ["Q1", "O1", "K1", "N2", "M2", "S2", "K2", "M4", "M6"]

cmaj = ds.current_semimajor.values[valid_idx, ipt].astype(float)
cmin = ds.current_semiminor.values[valid_idx, ipt].astype(float)
cinc = ds.current_inclination.values[valid_idx, ipt].astype(float)
cpha = ds.current_phase.values[valid_idx, ipt].astype(float)
lat = float(ds.latitude.values[ipt])

# Zero out any NaNs (matches MATLAB behavior in build_histograms.m)
for arr in (cmaj, cmin, cinc, cpha):
    arr[np.isnan(arr)] = 0.0

# --- Look up frequencies and indices in utide's constituent table ---
const_names = np.array([n.strip() for n in ut_constants["const"]["name"]])
lind = np.array([np.where(const_names == n)[0][0] for n in valid_names], dtype=int)
frq = ut_constants["const"]["freq"][lind].astype(float)  # cycles/hour

# --- Time vector: 2013 hourly, same as the pipeline ---
t_start = dt.datetime(2013, 1, 1, 0, 0, 0)
n = 8760
t = np.array([t_start + dt.timedelta(hours=i) for i in range(n)])

# --- Build the coef Bunch by hand ---
# This is the recipe for reconstruction from externally-supplied ellipse
# constituents (e.g. from ROMS). All fields required by utide._reconstruct
# are populated; CIs and means/slopes are zero because we are not fitting.
n_con = len(valid_names)
coef = Bunch(
    name=np.array(valid_names),
    Lsmaj=cmaj,
    Lsmin=cmin,
    theta=cinc,
    g=cpha,
    Lsmaj_ci=np.zeros(n_con),
    Lsmin_ci=np.zeros(n_con),
    umean=0.0,
    vmean=0.0,
    aux=Bunch(
        frq=frq,
        lind=lind,
        lat=lat,
        reftime=None,  # set below after _normalize_time
        opt=Bunch(
            twodim=True,
            nodiagn=True,     # skip SNR/PE filter (we have no CIs)
            notrend=True,
            prefilt=[],
            nodsatlint=1,     # midpoint-evaluated nodal correction (matches t_predic)
            nodsatnone=0,
            gwchlint=1,       # midpoint-evaluated Greenwich phase
            gwchnone=0,
        ),
    ),
)
t_norm = _normalize_time(t, None)
coef.aux.reftime = float(np.mean(t_norm))

# --- Reconstruct ---
out = reconstruct(t, coef, verbose=False)
W_py = out.u + 1j * out.v   # complex velocity: u east + i·v north

# --- Load MATLAB ground truth ---
mat = scipy.io.loadmat(MAT_FILE)
W_mat = mat["v_pred"].squeeze()
assert W_py.shape == W_mat.shape, (W_py.shape, W_mat.shape)

# --- Compare ---
diff = W_py - W_mat
abs_diff = np.abs(diff)
abs_mat = np.abs(W_mat)
print(f"shape: {W_py.shape}")
print(f"MATLAB |W|: min={abs_mat.min():.6f}  mean={abs_mat.mean():.6f}  max={abs_mat.max():.6f}")
print(f"Python |W|: min={np.abs(W_py).min():.6f}  mean={np.abs(W_py).mean():.6f}  max={np.abs(W_py).max():.6f}")
print(f"Element-wise diff:")
print(f"  max |Δ|       = {abs_diff.max():.3e}")
print(f"  mean |Δ|      = {abs_diff.mean():.3e}")
print(f"  RMS Δ         = {np.sqrt((abs_diff**2).mean()):.3e}")
print(f"  max |Δ|/|MAT| = {(abs_diff / np.maximum(abs_mat, 1e-12)).max():.3e}")

print("\nFirst 5 elements:")
for i in range(5):
    print(f"  i={i}: MAT={W_mat[i].real:+.6f}{W_mat[i].imag:+.6f}j  "
          f"PY={W_py[i].real:+.6f}{W_py[i].imag:+.6f}j  Δ={diff[i]:.3e}")

speed_mat = np.abs(W_mat)
speed_py = np.abs(W_py)
print(f"\nSpeed diff: max={np.max(np.abs(speed_py - speed_mat)):.3e}  "
      f"RMS={np.sqrt(np.mean((speed_py - speed_mat)**2)):.3e}")
