#!/usr/bin/env python
"""
Check connection status of every device a station's ``startup.py`` loads.

Mirrors the device-loading block of ``startup.py`` -- ``devices.yml`` always,
plus ``devices_aps_only.yml`` when on the APS subnet -- but constructs each
device individually so one unreachable IOC can't hide the rest of the report
(the normal batch loader aborts the whole file on the first failure).

Reports each device with a green check (fully connected) or a red x (not),
a connected/total signal count, and per-component detail:

* all components connected      -> green check
* exactly one component missing -> names that component
* no components connected       -> "nothing loaded"

Usage::

    python scripts/check_devices.py [b|e] [--settle SECONDS]
"""

import argparse
import importlib
import logging
import sys
import time
from pathlib import Path

import guarneri
from apsbits.utils.aps_functions import host_on_aps_subnet
from guarneri.helpers import dynamic_import

OK = "✅"  # green check
BAD = "❌"  # red x

STATIONS = {"b": "id12_b", "e": "id12_e"}


def load_devices(station):
    """Construct the devices ``startup.py`` would load, isolating failures.

    Returns a list of ``(name, device_or_None, error_or_None)`` tuples.
    """
    pkg = importlib.import_module(STATIONS[station])
    configs = Path(pkg.__file__).parent / "configs"

    files = ["devices.yml"]
    if host_on_aps_subnet():
        files.append("devices_aps_only.yml")

    instrument = guarneri.Instrument({})
    results = []
    logging.disable(logging.WARNING)  # quiet guarneri/ophyd chatter; errors we catch
    try:
        for filename in files:
            path = configs / filename
            if not path.exists():
                continue
            with path.open() as fh:
                defns = instrument.parse_yaml_file(fh)
            for defn in defns:
                name = defn["kwargs"].get("name", defn["device_class"])
                try:
                    klass = instrument.device_classes.get(defn["device_class"])
                    if klass is None:
                        klass = dynamic_import(defn["device_class"])
                    device = instrument.make_device(
                        klass, defn.get("args", ()), defn["kwargs"], fake=False
                    )
                except Exception as exc:  # unreachable IOC, bad import, etc.
                    results.append((name, None, exc))
                    continue
                # A factory entry may return several devices (list/generator).
                if hasattr(device, "walk_signals"):
                    results.append((name, device, None))
                else:
                    results.extend((d.name, d, None) for d in device)
    finally:
        logging.disable(logging.NOTSET)
    return results


def component_status(device):
    """Return (connected_count, total_count, disconnected_dotted_names)."""
    signals = list(device.walk_signals(include_lazy=False))
    if not signals:
        connected = bool(device.connected)
        return int(connected), 1, [] if connected else ["<device>"]
    disconnected = [s.dotted_name for s in signals if not s.item.connected]
    return len(signals) - len(disconnected), len(signals), disconnected


def report(results):
    """Print the per-device connection report; return a process exit code."""
    if not results:
        print("No devices were attempted by startup.")
        return 1

    fully_connected = 0
    for name, device, error in results:
        if device is None:
            print(f"{BAD} {name}  -- nothing loaded ({type(error).__name__})")
            continue

        connected, total, disconnected = component_status(device)
        if connected == total:
            fully_connected += 1
            print(f"{OK} {name}  ({connected}/{total} signals)")
        elif connected == 0:
            print(f"{BAD} {name}  ({connected}/{total} signals)  -- nothing loaded")
        elif len(disconnected) == 1:
            print(
                f"{BAD} {name}  ({connected}/{total} signals)  "
                f"-- component '{disconnected[0]}' not connected"
            )
        else:
            shown = ", ".join(disconnected[:5])
            more = "" if len(disconnected) <= 5 else f", +{len(disconnected) - 5} more"
            print(
                f"{BAD} {name}  ({connected}/{total} signals)  "
                f"-- {len(disconnected)} components not connected: {shown}{more}"
            )

    print(f"\nConnected: {fully_connected}/{len(results)} devices fully connected")
    return 0 if fully_connected == len(results) else 1


def main():
    """Parse arguments, load the station's devices, and print the report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "station",
        nargs="?",
        default="b",
        choices=sorted(STATIONS),
        help="12-ID hutch to check (default: b)",
    )
    parser.add_argument(
        "--settle",
        type=float,
        default=2.0,
        help="seconds to wait for connections before reporting (default: 2.0)",
    )
    args = parser.parse_args()

    print(f"Loading station {STATIONS[args.station]} (this attempts connections)...\n")
    results = load_devices(args.station)
    time.sleep(args.settle)  # let channel access settle before reading .connected
    sys.exit(report(results))


if __name__ == "__main__":
    main()
