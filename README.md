# vp-gen5-resource

Portfolio optimization pipeline for siting tidal current turbines along a
coastline. Given a target installed capacity and LCOE ceiling, selects which
candidate sites to deploy at in order to minimize the variance of the
combined power output.

## Repository layout

    inputs/        Third-party inputs (tidal dataset, coastline shapefile, turbine specs)
    optimization/  Pipeline scripts + config + T_TIDE library
    results/       Generated outputs (not tracked)

## Inputs you must supply

The tidal dataset is not included in this repository. Place your DBF of
harmonic tidal constants at:

    inputs/roms/tide_data_east.dbf

The field names read by `01_extract_harmonics.py` are defined in that script
under `FIELD_PREFIXES`.

## Dependencies

- Python 3.10+ (see `requirements.txt`)
- MATLAB with Statistics Toolbox (for steps 2 and 4)
- Gurobi with a valid license (for step 5)

Setup:

    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt

## Running the pipeline

Activate the environment and run from `optimization/`, in order. Each step
writes to `results/` and skips if its output already exists — delete the
target file to re-run a step.

    source .venv/bin/activate
    cd optimization

    python 01_extract_harmonics.py
    matlab -batch "build_histograms"
    python 03_screen_candidates.py
    matlab -batch "compute_covariance"
    python 05_optimize.py
    python plot_results.py

## Configuration

All parameters — turbine specs, site filters, cost components, power target,
and LCOE targets — live in `optimization/config/config.py` (Python pipeline)
and `optimization/config/config.m` (MATLAB pipeline).

## License

MIT. See `LICENSE`.
