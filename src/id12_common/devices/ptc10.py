"""
PTC10 programmable temperature controllers at 12-ID.

The PTC10 hardware is configurable.
Local support is always needed.
"""
# TODO: USAXS reports this support may need some revision.

import logging

from apstools.devices import PTC10AioChannel
from apstools.devices import PTC10PositionerMixin
from ophyd import Component
from ophyd import EpicsSignalRO
from ophyd import EpicsSignalWithRBV
from ophyd import PVPositioner

# from apstools.devices import PTC10RtdChannel

logger = logging.getLogger(__name__)
logger.info(__file__)


class PTC10_12ID(PTC10PositionerMixin, PVPositioner):
    """
    USAGE

    * Change the temperature and wait to get there: ``yield from bps.mv(ptc10, 75)``
    * Change the temperature and not wait: ``yield from bps.mv(ptc10.setpoint, 75)``
    * Change other parameter: ``yield from bps.mv(ptc10.tolerance, 0.1)``
    * To get temperature: ``ptc10.position``  (because it is a **positioner**)
    * Is it at temperature?:  ``ptc10.done.get()``
    """

    # PVPositioner interface
    readback = Component(EpicsSignalRO, "2A:temperature", kind="hinted")
    setpoint = Component(EpicsSignalWithRBV, "5A:setPoint", kind="hinted")

    # PTC10 base
    enable = Component(EpicsSignalWithRBV, "outputEnable", kind="config", string=True)

    # PTC10 thermocouple module : reads as NaN
    # temperatureB = Component(
    #     EpicsSignalRO, "2B:temperature", kind="config"
    # )
    # temperatureC = Component(EpicsSignalRO, "2C:temperature", kind="config")
    # Next line: it's a NaN now
    # # temperatureD = Component(EpicsSignalRO, "2D:temperature", kind="omitted")
    # coldj2 = Component(
    #     EpicsSignalRO, "ColdJ2:temperature", kind="config"
    # )

    # PTC10 RTD module
    # rtd = Component(PTC10RtdChannel, "3A:")  # reads as NaN
    # rtdB = Component(PTC10RtdChannel, "3B:")  # unused now

    # PTC10 AIO module
    pid = Component(PTC10AioChannel, "5A:")
    # pidB = Component(PTC10AioChannel, "5B:")  # unused now
    # pidC = Component(PTC10AioChannel, "5C:")  # unused now
    # pidD = Component(PTC10AioChannel, "5D:")  # unused now

    def __init__(self, *args, **kwargs):
        """Initialize the PTC10 controller object."""
        super().__init__(*args, **kwargs)

        # Aliases to make PTC10 have same ramp & temperature
        # terms as Linkam controllers.  Use aliaases rather than
        # a Python property method for each.
        self.temperature = self
        self.ramp = self.pid.ramprate

    def ptc10_setup(
        self,
        tolerance: float = 1.0,
        report_dmov_changes: bool = False,
    ):
        """Not a bluesky plan.  Common setup (from USAXS)."""
        self.report_dmov_changes.put(report_dmov_changes)  # a diagnostic
        self.tolerance.put(tolerance)  # done when |readback-setpoint|<=tolerance