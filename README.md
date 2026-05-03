# tidal-portfolio-siting

Portfolio optimization pipeline for siting tidal current turbines along a
coastline. Given a target installed capacity and an LCOE ceiling, the
pipeline selects which candidate sites to deploy at in order to minimize
the variance of the combined power output.

The repository supports two devices, each with its own self-contained
pipeline:

- **Verdant Power Gen5 KHPS** (TriFrame, 105 kW per frame) — `optimization/vp/`
- **ORPC TidGen 2.0** (single device, 500 kW) — `optimization/orpc/`

Each device folder ships its own code, config, methodology docs, raw vendor
data, T_TIDE library, and run scripts.

## Repository layout

    inputs/                Third-party inputs (tidal dataset, coastline shapefile)
    optimization/
      vp/                  VP Gen5 pipeline
      orpc/                ORPC TidGen 2.0 pipeline (t_tide symlinks to vp/t_tide)
    results/               Generated outputs (not tracked):
      vp/{groups,states}/<name>/
      orpc/{groups,states}/<name>/

Inside each pipeline folder:

    01_extract_harmonics.py / 03_screen_candidates.py / 05_optimize.py / plot_results.py
    build_histograms.m / compute_covariance.m
    config/                config.py + config.m + east_coast_state_boundaries.csv
    methodology/           Turbine spec, energy methodology, cost components, raw vendor data
    run_state.sh / run_group.sh / run_all.sh

## Inputs you must supply

The tidal dataset is not included in this repository. Place your DBF of
harmonic tidal constants at:

    inputs/roms/tide_data_east.dbf

The field names read by `01_extract_harmonics.py` are defined in that script
under `FIELD_PREFIXES`.

## Dependencies

- Python 3.10+ (see `requirements.txt`)
- MATLAB with Parallel Computing Toolbox (for steps 2 and 4)
- Gurobi with a valid license (for step 5)

Setup:

    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt

## Running a pipeline

Pick a device folder and use one of the three drivers, which run all six
pipeline steps in order:

    cd optimization/vp          # or optimization/orpc

    ./run_state.sh Maine_coastline      # single state
    ./run_state.sh pooled               # entire east coast in one solve
    ./run_group.sh new_england_ny \
        Maine_coastline,New_Hampshire_coastline,...
    ./run_all.sh                        # pooled + every state in the boundaries CSV

Outputs land in `results/<device>/{groups,states}/<name>/`. Each driver
captures stdout/stderr to `<results_dir>/log.txt` and skips upstream steps
whose `.nc` output already exists — delete the target file to re-run a step.

The pipeline reads four environment variables for one-off overrides:

- `TIDAL_STATE` — single state name or comma-separated list
- `TIDAL_GROUP` — name for a multi-state group; controls the results subdir
- `TIDAL_P_TARGET_MW` — deployment target in MW
- `TIDAL_LCOE_TARGETS` — comma-separated LCOE caps in $/MWh

## Configuration

Per-device parameters — turbine specs, site filters, cost components,
power target, LCOE targets — live in:

    optimization/vp/config/config.py + config.m
    optimization/orpc/config/config.py + config.m

Full sourcing for each parameter (with citations) lives alongside the code
under `optimization/<device>/methodology/`.

## License

MIT. See `LICENSE`.
