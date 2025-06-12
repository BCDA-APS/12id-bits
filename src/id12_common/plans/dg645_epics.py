"""
Bluesky plans & plan stubs for DG645 Delay Generator.

Plan stubs here patterned after 12ID's SPEC macros for DG645.

.. autosummary::

    ~burst_init
    ~burst_set
"""

from bluesky import plan_stubs as bps
from bluesky.utils import MsgGenerator
from bluesky.utils import plan

# from apstools.devices.delay import DG645Delay
from ..devices import DG645Delay


@plan
def burst_init(dg645: DG645Delay) -> MsgGenerator:
    """Initialize burst mode parameters.

    EXAMPLE::

        yield from burst_init(dg645_idc)
    """
    yield from bps.mv(dg645.burst_mode, 1)
    yield from bps.sleep(0.01)
    yield from bps.mv(dg645.burst_T0, 1)
    yield from bps.sleep(0.01)
    yield from bps.mv(dg645.burst_delay, 0)
    yield from bps.sleep(0.01)


@plan
def burst_set(
    dg645: DG645Delay,
    cycles: int,
    period: float,
    delay: float,
) -> MsgGenerator:
    """Set burst parameters.

    EXAMPLE::

        yield from burst_set(dg645_idc, 1, 1e-5, 0)
    """
    yield from bps.mv(dg645.burst_count, cycles)
    yield from bps.sleep(0.01)
    yield from bps.mv(dg645.burst_period, period)
    yield from bps.sleep(0.01)
    yield from bps.mv(dg645.burst_delay, delay)
    yield from bps.sleep(0.01)
