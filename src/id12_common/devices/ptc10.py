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
    PTC10 as seen from the GUI screen.

    The IOC templates and .db files provide a more general depiction.
    The PTC10 has feature cards, indexed by the slot where each is
    installed (2A, 3A, 5A, ...).  Here, slot 2 has four temperature
    sensor channels (2A, 2B, 2C, 2D).  The EPICS database template file
    calls for these EPICS database files:

    * PTC10_tc_chan.db  (channels 2A, 2B, 2C, 2D, ColdJ2)
    * PTC10_rtd_chan.db (channels 3A, 3B)
    * PTC10_aio_chan.db (channels 5A, 5B, 5C, 5D)

    USAGE

    * Change the temperature and wait to get there: ``yield from bps.mv(ptc10, 75)``
    * Change the temperature and not wait: ``yield from bps.mv(ptc10.setpoint, 75)``
    * Change other parameter: ``yield from bps.mv(ptc10.tolerance, 0.1)``
    * To get temperature: ``ptc10.position``  (because it is a **positioner**)
    * Is it at temperature?:  ``ptc10.done.get()``

    PTC10 PID parameters for different heaters from spec:

    def PTC10_PID_Flowcell_Heater '{
    epics_put("9idcTEMP:tc1:5A:pid:P", 0.0344)
    epics_put("9idcTEMP:tc1:5A:pid:I", 0.0013)
    epics_put("9idcTEMP:tc1:5A:pid:D", 0.0253)
    p "PID values are set for the Gas Flow Cell!"
    }'
    def PTC10_PID_NMR_Heater '{
    epics_put("9idcTEMP:tc1:5A:pid:P", 0.5)
    epics_put("9idcTEMP:tc1:5A:pid:I", 0.03)
    epics_put("9idcTEMP:tc1:5A:pid:D", 1.7)
    p "PID values are set for the NMR tube heater!"
    }'
    def PTC10_PID_Rheo_Heater '{
    epics_put("9idcTEMP:tc1:5A:pid:P", 1)
    epics_put("9idcTEMP:tc1:5A:pid:I", 0.01)
    epics_put("9idcTEMP:tc1:5A:pid:D", 10.)
    p "PID values are set for the Rheo heater!"
    }'
    PTC10 NMR tube heater offsets:

    The NMR tube heater was insulated with ceramic pieces; the custom-made
    DC cartridge from Maxiwatt company replaced the previous low power
    heating element. The tests showed a significant temperature gradient
    across the holder (20 deg difference @300 deg C).

    temperatures (C)
    ======  =========   ======  ========
    Holder  Right end   Middle  Left end
    ======  =========   ======  ========
    100	    89	        86      83
    150     130         126     120
    200     173         168     160
    250     215         210     198
    300     259         252     239
    ======  =========  ====== ========

    Note: at 70C the offset is under 7 degrees for right end NMR tube,
    heater set to 77 degrees, NMR tube is 70.4C.
    For 5th NMR tube from right, the offset is pretty much 0 - 70C and sample
    temperature is 71. So we need to verify offset every time, it clearly
    varies at different positions a  lot.
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
