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

Devices are looked up from the registry by their **exact registered names**. The
defaults target 12-ID-C/E (``id12_e``) and are overridable per call, so the same
plans work at ``id12_b`` by passing that station's device names.

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

from apsbits.core.instrument_init import with_registry
from apstools.plans import lineup2
from bluesky import plan_stubs as bps
from bluesky import plans as bp

logger = logging.getLogger(__name__)

DEFAULT_MD = {"title": "12-ID SAXS acquisition"}

# id12_e-flavored defaults; every plan lets the caller override them.
DEFAULT_DETECTORS = ["pilatus2m"]  # SAXS Pilatus 2M (prefix S12-PILATUS1:)
DEFAULT_ALIGN_DETECTORS = ["struck"]  # scaler: a scalar signal for lineup2
DEFAULT_MOTOR = "saxs_sample_stage_hor"  # SAXSDaq sth
DEFAULT_MOTOR2 = "saxs_sample_stage_ver"  # SAXSDaq stv
DEFAULT_THETA = "c_motors_theta"  # SAXSDaq theta


def _detectors(oregistry, names):
    """Resolve a list of registered device names to device objects."""
    return [oregistry[name] for name in names]


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


@with_registry
def saxs_count(
    oregistry,
    exposure: float = 1.0,
    num: int = 1,
    period: float | None = None,
    detectors: list | None = None,
    md: dict | None = None,
):
    """Acquire ``num`` frames at the current position (SAXSDaq ``takeshot``).

    ``period`` is the frame-to-frame interval in seconds; when given, the
    bluesky inter-frame ``delay`` is set to ``period - exposure`` so the total
    cadence matches. ``detectors`` is a list of registered device names.
    """
    logger.debug("saxs_count()")
    dets = _detectors(oregistry, detectors or DEFAULT_DETECTORS)
    delay = 0.0 if period is None else max(0.0, period - exposure)

    _md = dict(DEFAULT_MD)
    _md.update(md or {})

    yield from _count(dets, exposure, num, delay, _md)


@with_registry
def saxs_time_series(
    oregistry,
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
    dets = _detectors(oregistry, detectors or DEFAULT_DETECTORS)
    delay = max(0.0, period - exposure)

    _md = dict(DEFAULT_MD)
    _md.update({"purpose": "time series", "period": period})
    _md.update(md or {})

    yield from _count(dets, exposure, num, delay, _md)


@with_registry
def saxs_rel_scan(
    oregistry,
    start: float,
    finish: float,
    delta: float,
    exposure: float = 1.0,
    motor: str = DEFAULT_MOTOR,
    detectors: list | None = None,
    md: dict | None = None,
):
    """Relative line scan (SAXSDaq ``scanshot``).

    Step ``motor`` from ``start`` to ``finish`` (offsets from its current
    position) in steps of ``delta``, acquiring one point at each position. The
    motor returns to its starting position afterward.
    """
    logger.debug("saxs_rel_scan()")
    dets = _detectors(oregistry, detectors or DEFAULT_DETECTORS)
    mot = oregistry[motor]
    num = _steps(start, finish, delta)

    _md = dict(DEFAULT_MD)
    _md.update(md or {})

    yield from _set_exposure(dets, exposure)
    yield from bp.rel_scan(dets, mot, start, finish, num=num, md=_md)


@with_registry
def saxs_list_scan(
    oregistry,
    positions: list,
    exposure: float = 1.0,
    motor: str = DEFAULT_MOTOR,
    detectors: list | None = None,
    relative: bool = False,
    md: dict | None = None,
):
    """Scan a motor over an explicit list of positions, one point each.

    Bluesky translation of the §3.10 ``for``-loop-over-a-position-list macro;
    use it for irregular points. ``relative=True`` treats ``positions`` as
    offsets from the current position (and returns there afterward).
    """
    logger.debug("saxs_list_scan()")
    dets = _detectors(oregistry, detectors or DEFAULT_DETECTORS)
    mot = oregistry[motor]

    _md = dict(DEFAULT_MD)
    _md.update(md or {})

    yield from _set_exposure(dets, exposure)
    scan = bp.rel_list_scan if relative else bp.list_scan
    yield from scan(dets, mot, list(positions), md=_md)


@with_registry
def saxs_rel_grid(
    oregistry,
    fast_start: float,
    fast_finish: float,
    fast_delta: float,
    slow_start: float,
    slow_finish: float,
    slow_delta: float,
    exposure: float = 1.0,
    fast_motor: str = DEFAULT_MOTOR,
    slow_motor: str = DEFAULT_MOTOR2,
    detectors: list | None = None,
    snake: bool = False,
    md: dict | None = None,
):
    """Relative 2-D grid / raster map (SAXSDaq ``gridshot`` and the §3.10 map).

    Acquire one point at every node of a grid spanned by ``fast_motor`` (inner
    loop) and ``slow_motor`` (outer loop), with all ranges relative to the
    current positions. ``snake=True`` reverses alternate fast rows.
    """
    logger.debug("saxs_rel_grid()")
    dets = _detectors(oregistry, detectors or DEFAULT_DETECTORS)
    fast = oregistry[fast_motor]
    slow = oregistry[slow_motor]
    nfast = _steps(fast_start, fast_finish, fast_delta)
    nslow = _steps(slow_start, slow_finish, slow_delta)

    _md = dict(DEFAULT_MD)
    _md.update(md or {})

    yield from _set_exposure(dets, exposure)
    # bluesky orders grid args slowest-first.
    yield from bp.rel_grid_scan(
        dets,
        slow,
        slow_start,
        slow_finish,
        nslow,
        fast,
        fast_start,
        fast_finish,
        nfast,
        snake_axes=snake,
        md=_md,
    )


@with_registry
def saxs_temperature_series(
    oregistry,
    setpoints: list,
    exposure: float = 1.0,
    num: int = 1,
    settle: float = 30.0,
    temperature: str = "ptc10",
    detectors: list | None = None,
    md: dict | None = None,
):
    """Acquire at each of a list of temperature setpoints.

    Bluesky translation of the §3.10 ``while``-loop-over-temperature-setpoints
    macro. For each setpoint: command the controller and wait (the temperature
    device's own set-completion provides the "reached setpoint" wait, replacing
    SAXSDaq's raw ``caget`` loop), soak for ``settle`` seconds, then acquire
    ``num`` frames. Pass ``temperature=`` the registered controller name.
    """
    logger.debug("saxs_temperature_series()")
    dets = _detectors(oregistry, detectors or DEFAULT_DETECTORS)
    temp = oregistry[temperature]

    for setpoint in setpoints:
        yield from bps.mv(temp, setpoint)
        yield from bps.sleep(settle)

        _md = dict(DEFAULT_MD)
        _md.update({"purpose": "temperature series", "setpoint": setpoint})
        _md.update(md or {})

        yield from _count(dets, exposure, num, 0.0, _md)


@with_registry
def align_theta(
    oregistry,
    rel_start: float = -0.5,
    rel_finish: float = 0.5,
    points: int = 75,
    motor: str = DEFAULT_THETA,
    detectors: list | None = None,
    md: dict | None = None,
):
    """Center theta on the intensity peak (SAXSDaq ``thcent``).

    Step ``motor`` over ``[rel_start, rel_finish]`` (offsets from the current
    position) reading a scalar detector, then move to the peak. Uses apstools
    ``lineup2`` with ``feature="centroid"`` (robust); use ``"x_at_max_y"`` for
    the literal move-to-maximum behavior of ``thcent``. The feedback detector
    must read a scalar intensity (a scaler), not an area detector.
    """
    logger.debug("align_theta()")
    dets = _detectors(oregistry, detectors or DEFAULT_ALIGN_DETECTORS)
    mot = oregistry[motor]

    _md = dict(DEFAULT_MD)
    _md.update(md or {})

    yield from lineup2(
        dets, mot, rel_start, rel_finish, points, feature="centroid", md=_md
    )
