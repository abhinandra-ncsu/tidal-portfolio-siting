# Site spacing map

Interactive deck.gl map of all 671,611 East Coast ROMS grid points that survive
the pipeline's spatial filter (state bounding boxes + 0.15° buffer, depth ≥ 10 m),
colored by distance to the nearest neighboring site. Built to answer: *what is the
effective spatial resolution of `inputs/roms/tide_data_east.dbf` after filtering?*

Headline: the grid is curvilinear with **median nearest-neighbor spacing ~257 m**
(p5 158 m, p95 370 m); finest in the Gulf of Maine (~180 m), coarsest in the
mid-Atlantic (~314 m).

## Files

- `01_export_sites.py` — reads `../east_coast_cf_map/harmonics.nc`, computes
  nearest-neighbor distance per site (cKDTree on ECEF coordinates), writes
  `results/sites.bin` (4 contiguous Float32 blocks: lon, lat, nn_dist_m, depth_m)
  and `results/meta.json`.
- `index.html` — self-contained deck.gl viewer. Fetches the binary, renders a
  ScatterplotLayer over CARTO light tiles. Hover for per-site spacing/depth;
  dynamic scale bar bottom-right.

## Run

```bash
python 01_export_sites.py          # only needed once (or after upstream changes)
python -m http.server 8000         # from this directory
# open http://localhost:8000
```

The HTML must be served over HTTP (it fetches `results/sites.bin`); opening the
file directly via `file://` will not load data. Basemap tiles require internet.

The view is bookmarkable via URL hash `#lat,lon,zoom`, e.g.:

- `#41.4,-70.2,11` — Nantucket Sound (grid lattice clearly resolved)
- `#40.800,-73.935,14` — Hell Gate / Harlem River confluence
- `#44.0,-68.8,9` — Penobscot Bay (finest spacing, ~180 m)

## Notes

- Source dataset is the pooled extraction cached at
  `experiments/east_coast_cf_map/harmonics.nc` (created 2026-05-22), which uses
  the same filter as `optimization/vp/01_extract_harmonics.py`.
- Point radius is 50 m (vs ~260 m spacing) so inter-site gaps remain visible at
  high zoom. Color is a diverging blue–gray–red ramp centered at the measured
  median (257 m, read from `meta.json`), clamped to 100–500 m: blue = locally
  finer than typical, red = coarser. The midpoint is a visible neutral gray
  rather than RdBu's near-white so median-spaced sites don't vanish against the
  basemap.
- The ~260 m grid spacing is the mechanism behind the ROMS narrow-jet
  under-resolution caveat. Concretely: the East River's Roosevelt Island reach
  (the RITE site, ~40.76–40.77°N) has **zero** surviving grid points — the
  nearest filtered sites are 33 points up at Hell Gate / the Harlem River
  confluence (lat ≥ 40.792). The RITE channel is absent from the filtered set,
  not just under-resolved.
