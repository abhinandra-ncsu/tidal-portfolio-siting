# ADR-0002 — MATLAB stays in steps 2 & 4; the Python port is parked

Status: accepted (2026-07-09)

## Context

The canonical pipeline alternates languages: Python (step 1) → MATLAB (step 2)
→ Python (step 3) → MATLAB (step 4) → Python (step 5). A side experiment ported
the two MATLAB steps (`build_histograms.m`, `compute_covariance.m`) to Python
using `utide`. Having a working Python port creates a standing temptation — for
a future maintainer or an AI assistant "tidying up" — to fold it into `main` and
drop the MATLAB dependency.

## Decision

- **MATLAB stays canonical** for steps 2 and 4. The pipeline on `main` invokes
  the `.m` scripts.
- **The Python port is not merged into `main`.** It lives on the `python-port`
  branch (pushed to GitHub for backup) as a parallel, parked line of work.
- The `utide_parity` experiment (which benchmarks the `utide` port against the
  MATLAB steps) stays on `main` as the *evidence* for this decision; only the
  port *implementation* lives on the `python-port` branch.

## Consequences

- `main` keeps a MATLAB runtime dependency on the execution machine. Accepted.
- The port is preserved and revisitable — it rebases onto `main` if ever
  resumed — but does not silently become the default.
- **Do not merge `python-port` into `main` without an explicit decision that
  supersedes this ADR.**
