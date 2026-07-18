"""Fine-band LCOE frontier sweep, pooled max-energy, per capacity.

Re-solves in-band LCOE targets (distinct portfolios along the cost-energy
frontier) into a *_frontier results dir, then renders baseline-format
spatial_map_L{L}.png via the repo's own plot_results.py.

Sets each child process's env EXPLICITLY (subprocess env=...) so the TIDAL_*
vars survive regardless of the WSL->Windows launch boundary.
"""
import os
import subprocess
import sys

REPO = r"C:\Users\asingh66\tidal-portfolio-siting"
PY = os.path.join(REPO, ".venv", "Scripts", "python.exe")
VP = os.path.join(REPO, "optimization", "vp")
CURVE = os.path.join(REPO, "results", "vp", "turbine_modification",
                     "gen5", "groups", "pooled", "1mw")

JOBS = {
    1:   "646,647,648,649,650,651,652",
    5:   "658,661,664,667,670,673,676,679,681",
    25:  "784,794,804,814,824,834,844,854,858",
    100: "1029,1045,1061,1077,1093,1109,1125,1141,1157,1172",
}


def run(mw, targets):
    out = os.path.join(REPO, "results", "vp", "max_energy", "gen5",
                       "groups", "pooled", f"{mw}mw_frontier")
    log = os.path.join(REPO, f"frontier_{mw}.log")
    env = dict(os.environ)
    env.update({
        "PYTHONIOENCODING": "utf-8",
        "TIDAL_OBJECTIVE": "energy",
        "TIDAL_VARIANT": "gen5",
        "TIDAL_STEPUP_KV": "6.6",
        "TIDAL_CURVE_DIR": CURVE,
        "TIDAL_P_TARGET_MW": str(mw),
        "TIDAL_LCOE_TARGETS": targets,
        "TIDAL_RESULTS_DIR": out,
    })
    print(f"[{mw} MW] solving {len(targets.split(','))} targets ...", flush=True)
    # child stdout/stderr -> logfile opened in Python (no shell redirects,
    # which the remote cmd layer eats before bash sees them)
    with open(log, "w") as lf:
        subprocess.run([PY, "05_optimize.py"], cwd=VP, env=env,
                       stdout=lf, stderr=subprocess.STDOUT, check=True)
        print(f"[{mw} MW] solved, rendering maps ...", flush=True)
        subprocess.run([PY, "plot_results.py"], cwd=VP, env=env,
                       stdout=lf, stderr=subprocess.STDOUT, check=True)
    nmaps = len([f for f in os.listdir(os.path.join(out, "figures"))
                 if f.startswith("spatial_map_")])
    print(f"[{mw} MW] DONE -> {nmaps} spatial maps in {out}\\figures", flush=True)


def main():
    args = sys.argv[1:] or ["all"]
    sel = set(JOBS) if args == ["all"] else {int(a) for a in args}
    for mw, t in JOBS.items():
        if mw in sel:
            run(mw, t)
    print("ALL_DONE", flush=True)


if __name__ == "__main__":
    main()
