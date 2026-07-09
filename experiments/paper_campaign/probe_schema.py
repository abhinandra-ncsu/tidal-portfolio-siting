"""Dump the schema (dims, variables, attrs) of campaign netCDF files.

Run on energizelab:
  .venv\\Scripts\\python.exe probe_schema.py <file.nc> [<file.nc> ...]
"""
import sys

import xarray as xr


def dump(path: str) -> None:
    print(f"\n{'=' * 70}\n{path}\n{'=' * 70}")
    ds = xr.open_dataset(path)
    print(f"dims: {dict(ds.sizes)}")
    print("\n-- global attrs --")
    for k, v in ds.attrs.items():
        text = str(v)
        if len(text) > 200:
            text = text[:200] + "..."
        print(f"  {k} = {text}")
    print("\n-- coords --")
    for name, c in ds.coords.items():
        print(f"  {name}  {c.dims}  {c.dtype}")
    print("\n-- data_vars --")
    for name, v in ds.data_vars.items():
        attrs = f"  attrs={dict(v.attrs)}" if v.attrs else ""
        print(f"  {name}  {v.dims}  {v.dtype}{attrs}")
    ds.close()


for p in sys.argv[1:]:
    dump(p)
