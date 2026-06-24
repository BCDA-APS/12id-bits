# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`12id-bits` is an APS (Advanced Photon Source) beamline instrument package built on top of [`apsbits`](https://github.com/BCDA-APS/BITS) — the only runtime dependency. BITS = Bluesky Instrument starter; it wraps Bluesky's RunEngine, ophyd device abstractions, and EPICS PV access into a per-beamline package layout.

This repo was scaffolded from the BITS starter template (via `create-bits`, provided by `apsbits`) and has since been built out into a **multi-station** package. `src/` contains three packages:

- `id12_b`, `id12_c` — one self-contained instrument package per 12-ID experimental hutch (B/C). Each has its own `startup.py`, `configs/` (`iconfig.yml`, `devices.yml`, `devices_aps_only.yml`), `plans/`, `callbacks/`, and `qserver/`.
- `id12_common` — device and plan code shared across the stations: custom ophyd subclasses for 12-ID hardware (`devices/struck.py` Struck3820 scaler, `devices/delays.py` DG645 delay generator, `devices/ptc10.py` temperature controller, `devices/shutters.py` PSS shutters). Station configs reference these by import path, e.g. `id12_common.devices.struck.Struck`.

The two stations are near-identical in structure; they differ mainly in their `configs/*.yml` (which real devices each hutch has). When changing shared behavior, edit `id12_common` rather than copy-pasting across stations. This package's parent workspace also has a root `../CLAUDE.md` and an `../epics/` tree of the IOCs whose PVs these devices connect to.

## Environment & install

```bash
conda create -y -n BITS_env python=3.11
conda activate BITS_env
pip install -e ".[dev]"     # dev extras: build, isort, mypy, pre-commit, pytest, ruff
pre-commit install
```

Python 3.11 is the only supported version (CI matrix is pinned; 3.12/3.13 are commented out pending upstream packages — don't enable them without checking `apsbits` compatibility).

## Common commands

```bash
pre-commit run --all-files           # same lint gate as CI (ruff + ruff-format + standard hooks)
pytest                                # runs with --import-mode=importlib -x (stops on first failure)
pytest path/to/test_file.py::test_name -v
```

There is no separate build/lint script — CI runs `pre-commit run --all-files` then `pytest`. Reproduce CI locally with those two commands.

## Running the instrument

Each station package exposes a `startup` module — pick the hutch you want:

```python
from id12_b.startup import *   # or id12_c — creates RE, loads devices, registers plans
RE(sim_count_plan())          # smoke test (simulated detector)
```

`startup.py` is where everything wires together (same flow in all three stations): `init_RE`, then `make_devices(file="devices.yml")` always, plus `make_devices(file="devices_aps_only.yml")` only when `host_on_aps_subnet()` is true (real hardware), then `setup_baseline_stream` (any device labeled `baseline` is recorded once per run). So on a non-APS machine only the simulated devices load.

Queueserver host scripts live in `scripts/` (one per station), not inside the package:

```bash
./scripts/id12_b_qs_host.sh {start|stop|restart|status|console|run}
```

The QS host runs in `screen` by default; use `run` to run in the foreground for debugging. Per-station QS config is `src/id12_<x>/qserver/qs-config.yml`.

> `test.py` at the repo top is a standalone legacy pyepics script (direct `PV(...)`/`Motor(...)` access to mono/energy/PTC10), **not** part of the BITS package or the pytest suite. It predates the ophyd device migration — don't treat it as the device API.

## Conventions worth knowing

- **Line length:** ruff is configured to 88, but `[tool.black]` and `[tool.flake8]` are set to 115. Ruff is authoritative (it's what pre-commit runs); the 115 settings are legacy and don't gate anything.
- **Docstrings:** ruff enforces `D100`–`D107` (module/class/function/method docstrings required). New Python files and public symbols need them or pre-commit will fail.
- **isort:** `force-single-line = true` — one import per line, no grouping with commas. Ruff's import sorter enforces this.
- **Package layout:** src-layout. `[tool.setuptools.package-dir] "" = "src"`. YAML files are bundled as package data — config files belong inside `src/<instrument_name>/configs/`, not at repo root.
- **Version:** managed via `setuptools_scm`; `_version.py` is gitignored. Don't hand-edit version strings.

## Config files (per station, in `src/id12_<x>/`)

- `configs/iconfig.yml` — data collection config (catalog, RunEngine metadata, enables for NEXUS/SPEC callbacks, baseline)
- `configs/devices.yml` — devices loaded everywhere (currently the simulated `sim_motor`/`sim_det`); the file is mostly commented examples of real-device declarations
- `configs/devices_aps_only.yml` — real hardware, loaded only on the APS subnet; device prefixes here (e.g. `12idb:DG1:`, `12idc:3820:`) map to the IOCs under `../epics/`
- `qserver/qs-config.yml` — queueserver host config

## Upstream

When adding devices/plans, the patterns come from `apsbits` itself — check the installed package (`python -c "import apsbits; print(apsbits.__file__)"`) or [BCDA-APS/BITS](https://github.com/BCDA-APS/BITS) for the canonical examples before inventing new structure.
