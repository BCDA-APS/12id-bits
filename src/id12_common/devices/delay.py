"""
Changes to apstools DG645 support.

.. seealso:: https://github.com/BCDA-APS/apstools/issues/1109
"""

from apstools.devices.delay import DG645Delay as aps_DG645Delay
from apstools.devices.delay import EpicsSignalWithIO
from ophyd import Component as Cpt, EpicsSignal


class DG645Delay(aps_DG645Delay):
    """Changes per apstools issue #1109."""

    burst_mode = Cpt(EpicsSignalWithIO, "BurstModeB", kind="config")
    burst_T0 = Cpt(EpicsSignalWithIO, "BurstConfigB", kind="config")
    # Initiate or arm a trigger (write only, like a pushbutton)
    trigger_delay = Cpt(EpicsSignal, "TriggerDelayBO", kind="omitted")
