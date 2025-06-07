"""Custom shutter support for 12ID."""

from typing import List
from typing import Union

from apstools.devices import ApsPssShutterWithStatus
from apstools.devices.shutters import ApsPssShutter
from ophyd import Component
from ophyd import EpicsSignal
from ophyd import EpicsSignalRO
from ophyd import FormattedComponent

class ID12_ApsPssShutter(ApsPssShutter):
    """Adjust the delay time as a kwarg."""

    def __init__(self, prefix, *args, delay_s=1.2, **kwargs):
        """."""
        self.delay_s = delay_s
        super().__init__(prefix, *args, **kwargs)


class My12IdPssShutter(ApsPssShutterWithStatus):
    """
    Controls a single APS PSS shutter at 12IDE (from USAXS-bits).

    ======  =========  =====
    action  PV suffix  value
    ======  =========  =====
    open    _opn       1
    close   _cls       1
    ======  =========  =====
    """

    # bo records that reset after a short time, set to 1 to move
    open_signal: Component[EpicsSignal] = Component(EpicsSignal, "_opn")
    close_signal: Component[EpicsSignal] = Component(EpicsSignal, "_cls")
    # bi record ZNAM=OFF, ONAM=ON
    pss_state: FormattedComponent[EpicsSignalRO] = FormattedComponent(
        EpicsSignalRO, "{self.state_pv}"
    )
    pss_state_open_values: List[Union[int, str]] = [1, "ON"]
    pss_state_closed_values: List[Union[int, str]] = [0, "OFF"]
