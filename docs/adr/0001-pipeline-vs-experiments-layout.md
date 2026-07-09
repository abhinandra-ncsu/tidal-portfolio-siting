# ADR-0001 — Pipeline vs. experiments layout

Status: accepted (2026-07-09)

## Context

`optimization/{vp,orpc}/` had accumulated both the canonical five-step pipeline
*and* per-campaign run scripts (`run_transmission_stepup.sh`,
`run_max_energy*.sh`, `run_turbine_modification.sh`), plus methodology notes for
abandoned ideas (diameter scaling, site-depth constraint). Experiments were
gitignored wholesale, so campaign recipes lived untracked on whichever machine
ran them and never synced. This blurred "the pipeline" with "a study using the
pipeline" and left recipes unbacked-up.

## Decision

- **`optimization/{vp,orpc}/` = the pipeline only:** the five steps, the generic
  runners (`run_state/run_group/run_all.sh`), `config/`, `methodology/`,
  `t_tide/`, `plot_results.py`. Generic runners stay because they *are* the
  pipeline's invocation interface.
- **`experiments/<name>/` = one campaign each:** its `run.sh` driver, analysis
  scripts, and `EXPERIMENT.md`.
- **Track the recipe, ignore the output.** Under `experiments/`, git tracks
  `.py .m .sh .md`; it ignores generated output and notebooks. The recipe is the
  reproducible input and must be backed up; output regenerates from recipe +
  pipeline and stays machine-local.

## Consequences

- Experiment recipes are now version-controlled and shared across machines;
  outputs remain local and divergent-by-design.
- Some experiments carry *forked copies* of pipeline steps (e.g.
  `east_coast_cf_map/01_extract_harmonics.py`). These are tracked as recipe, but
  the duplication can drift from `optimization/` — a known risk, accepted for now.
- Moving a driver into `experiments/` does not un-track it (git mv preserves
  tracking despite the folder being otherwise ignored).
