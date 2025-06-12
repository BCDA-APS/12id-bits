"""
Bluesky plans & plan stubs for DG645 Delay Generator.

.. autosummary::
"""

from bluesky import plan_stubs as bps
from bluesky.utils import MsgGenerator
from bluesky.utils import plan

from ..devices import SocketDG645DelayGen


@plan
def burst_init(dg645: SocketDG645DelayGen) -> MsgGenerator:
    """Initialize burst parameters."""
    yield from bps.mv(dg645.burst_mode_enable, True)
    yield from bps.sleep(0.01)
    yield from bps.mv(dg645.burst_T0_config, True)
    yield from bps.sleep(0.01)
    yield from bps.mv(dg645.burst_delay, 0)
    yield from bps.sleep(0.01)


@plan
def burst_set(
    dg645: SocketDG645DelayGen,
    cycles: int,
    period: float,
    delay: float,
) -> MsgGenerator:
    """Set burst parameters."""
    yield from bps.mv(dg645.burst_count, cycles)
    yield from bps.sleep(0.01)
    yield from bps.mv(dg645.burst_period, period)
    yield from bps.sleep(0.01)
    yield from bps.mv(dg645.burst_delay, delay)
    yield from bps.sleep(0.01)
