"""
12-ID SAXS/WAXS acquisition plans
=================================

Bluesky translations of the ``APS12_SAXSDaq`` console acquisition primitives and
the ``for``/``while`` "macros" documented in its manual (``SAXSDaq_MANUAL.md``
§3.2 and §3.10). In SAXSDaq a "macro" is just a plain Python script that calls
the ``ID12.*`` primitives in ordinary loops; these plans express the same
experiments for the Bluesky RunEngine / queueserver against the ophyd devices
declared in ``configs/devices.yml``.

Every SAXSDaq scan uses **relative offsets** and a **step size**; these plans
convert the step size to a bluesky point count
(``num = round(|finish - start| / |delta|) + 1``). The SAXSDaq base-filename
argument has no bluesky equivalent (files are named by the area-detector HDF
plugin / run uid) and is intentionally dropped.

Devices are resolved from the registry at call time (they are created only on the
APS subnet, after this module is imported). The defaults target 12-ID-B (the SAXS
Eiger2 9M + WAXS Pilatus 300K, and the ``sth`` axis of the ``saxs_sample_stage``
bundle) and are overridable per call by passing device objects.

Deferred (not translated here): ``zcent()`` / ``centering()`` iterative
beam-centering (needs an intensity-signal + dark-current strategy that cannot be
validated off-beamline), the hardware-triggered MCS fly variants
(``scanshot2`` / ``gridshot2`` / ``flyscanshot2``, which need an ophyd flyer that
does not exist yet), and ``scan_energy()``.

.. autosummary::
    ~saxs_count
    ~saxs_time_series
    ~saxs_rel_scan
    ~saxs_list_scan
    ~saxs_rel_grid
    ~saxs_temperature_series
    ~align_theta
"""

import logging

from apsbits.core.instrument_init import oregistry
from bluesky import plan_stubs as bps
from bluesky import plans as bp

logger = logging.getLogger(__name__)

DEFAULT_MD = {"title": "12-ID SAXS acquisition"}


def _default_detectors():
    """Default 12-ID-B detectors (SAXS Eiger2 9M + WAXS Pilatus 300K).

    Resolved from the registry at call time because the devices are created only
    on the APS subnet, after this module is imported.
    """
    return [oregistry["eiger9m"], oregistry["pilatus300k"]]


def _default_motor():
    """Default scan motor: the ``sth`` axis of the ``saxs_sample_stage`` bundle."""
    return oregistry["saxs_sample_stage"].sth


def _steps(start, finish, delta):
    """Convert a SAXSDaq start/finish/step range to a bluesky point count."""
    if delta == 0:
        raise ValueError("delta (step size) must be non-zero")
    return int(round(abs(finish - start) / abs(delta))) + 1


def _set_exposure(detectors, exposure):
    """Set the exposure/count time on each detector that supports it.

    Scaler-like devices use ``preset_time`` (directly or on a ``.scaler``
    sub-device); area detectors use ``cam.acquire_time``. Detectors with
    neither (e.g. simulated stand-ins) are left untouched.
    """
    if exposure is None:
        return
    for det in detectors:
        if hasattr(det, "preset_time"):
            yield from bps.mv(det.preset_time, exposure)
        elif hasattr(det, "scaler") and hasattr(det.scaler, "preset_time"):
            yield from bps.mv(det.scaler.preset_time, exposure)
        elif hasattr(det, "cam") and hasattr(det.cam, "acquire_time"):
            yield from bps.mv(det.cam.acquire_time, exposure)


def _count(detectors, exposure, num, delay, md):
    """Set the exposure, then read the detectors ``num`` times."""
    yield from _set_exposure(detectors, exposure)
    yield from bp.count(detectors, num=num, delay=delay, md=md)


def saxs_count(
    exposure: float = 1.0,
    num: int = 1,
    period: float | None = None,
    detectors: list | None = None,
    md: dict | None = None,
):
    """Acquire ``num`` frames at the current position (SAXSDaq ``takeshot``).

    ``period`` is the frame-to-frame interval in seconds; when given, the
    bluesky inter-frame ``delay`` is set to ``period - exposure`` so the total
    cadence matches. ``detectors`` overrides the default SAXS/WAXS detectors.
    """
    logger.debug("saxs_count()")
    dets = detectors or _default_detectors()
    delay = 0.0 if period is None else max(0.0, period - exposure)

    _md = dict(DEFAULT_MD)
    _md.update(md or {})

    yield from _count(dets, exposure, num, delay, _md)


def saxs_time_series(
    exposure: float,
    period: float,
    num: int,
    detectors: list | None = None,
    md: dict | None = None,
):
    """Acquire a timed series of ``num`` frames, one every ``period`` seconds.

    Bluesky translation of SAXSDaq ``multishot`` and the §3.10 ``while``-loop
    time-series macro (kinetics / timelapse).
    """
    logger.debug("saxs_time_series()")
    dets = detectors or _default_detectors()
    delay = max(0.0, period - exposure)

    _md = dict(DEFAULT_MD)
    _md.update({"purpose": "time series", "period": period})
    _md.update(md or {})

    yield from _count(dets, exposure, num, delay, _md)


def saxs_rel_scan(
    start: float,
    finish: float,
    delta: float,
    exposure: float = 1.0,
    motor=None,
    detectors: list | None = None,
    md: dict | None = None,
):
    """Relative line scan (SAXSDaq ``scanshot``).

    Step ``motor`` from ``start`` to ``finish`` (offsets from its current
    position) in steps of ``delta``, acquiring one point at each position. The
    motor returns to its starting position afterward. ``motor`` defaults to the
    ``sth`` axis of the ``saxs_sample_stage`` bundle.
    """
    logger.debug("saxs_rel_scan()")
    dets = detectors or _default_detectors()
    mot = motor or _default_motor()
    num = _steps(start, finish, delta)

    _md = dict(DEFAULT_MD)
    _md.update(md or {})

    yield from _set_exposure(dets, exposure)
    yield from bp.rel_scan(dets, mot, start, finish, num=num, md=_md)