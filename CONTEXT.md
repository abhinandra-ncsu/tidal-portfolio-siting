# Context — tidal-portfolio-siting

Glossary for the tidal-turbine siting/optimization codebase. Definitions only —
no implementation detail. See `docs/adr/` for the decisions behind the structure.

## Pipeline
The canonical five-step siting analysis, run per turbine **track** and per
**scope** (state / group / pooled). The steps alternate language and MATLAB
stays in the loop:

1. `01_extract_harmonics.py` — extract tidal harmonic constituents (Python)
2. `build_histograms.m` — velocity histograms (MATLAB)
3. `03_screen_candidates.py` — screen candidate sites (Python)
4. `compute_covariance.m` — site covariance (MATLAB)
5. `05_optimize.py` — portfolio optimisation (Python)

Lives in `optimization/{vp,orpc}/`. Python steps are numbered `01/03/05`; the
MATLAB steps keep name-only identifiers because MATLAB forbids a leading digit
in a callable script name.

## Step
One stage of the **Pipeline**. Steps read shared parameters from `config/` and
never define their own copies.

## Generic runner
`run_state.sh`, `run_group.sh`, `run_all.sh` — invoke the whole Pipeline over
the standard scope domain (one state / a named group / pooled + every state).
Part of the Pipeline's interface, so they live in `optimization/{vp,orpc}/`.
They are **not** experiments.

## Experiment (Campaign)
A specific study that varies config or inputs away from the baseline
(e.g. `transmission_stepup`, `turbine_modification`, `rated_cutin_sweep`). One
folder per experiment under `experiments/<name>/`.

## Driver
An Experiment's `run.sh` — sets a config matrix (variants × scopes × targets)
and calls the Pipeline. A thin wrapper, not new pipeline logic.

## Recipe
Everything an Experiment needs to be reproduced: its Driver, any analysis /
plotting scripts, and its `EXPERIMENT.md`. All Recipe files (`.py .m .sh .md`)
are **tracked**. Notebooks are treated as scratch, not Recipe, and are ignored.

## Output
Anything a run generates — results, figures, logs. Machine-local and
**gitignored** (top-level `results/`, plus any generated files inside an
experiment folder). Reproducible from Recipe + Pipeline, so it never needs to
travel through git.

## Variant
A turbine specification (`gen5`, `modvp2`–`modvp8`): rotor area, cut-in / rated
speed, rated power. Selected at runtime via `TIDAL_VARIANT`.

## Track
One of the two turbine technology families the Pipeline runs for: **VP**
(`optimization/vp/`) and **ORPC** (`optimization/orpc/`). Same five-step shape,
different specs and cost model.

## Trunk (`main`)
The canonical Pipeline. Includes the drivers work as of the June reorg.

## `python-port` (branch)
A parked experiment: a Python re-implementation of the two MATLAB steps
(2 and 4). Never merged into `main` — see ADR-0002. MATLAB is canonical.

## Authoring machine / Execution machine
**Mac** = where Pipeline code is authored (edit → commit → push). **Lab box**
(`energizelab`, Windows) = where the Pipeline runs (pull → run → results). The
same committed config + runners work on both, unchanged.

## Results cache
`.remote-results-cache/` on the Mac — the landing zone for **Output** pulled
back from the Execution machine, before it is curated into the paper repo.
