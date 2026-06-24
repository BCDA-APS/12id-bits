"""Custom shutter support for 12ID."""

from typing import List
from typing import Union

from apstools.devices import ApsPssShutterWithStatus
from apstools.devices.shutters import ApsPssShutter
from ophyd import Component
from ophyd import Device
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
    open_signal: Component[EpicsSignal] = Component(EpicsSignal, "Open")
    close_signal: Component[EpicsSignal] = Component(EpicsSignal, "Close")
    # bi record ZNAM=OFF, ONAM=ON
    pss_state: FormattedComponent[EpicsSignalRO] = FormattedComponent(
        EpicsSignalRO, "{state_pv}"
    )
    pss_state_open_values: List[Union[int, str]] = [1, "ON"]
    pss_state_closed_values: List[Union[int, str]] = [0, "OFF"]


class UniblitzShutter(Device):
    """Uniblitz VCMD-D1 fast shutter (command-driven), shared by 12-ID-B/C.

    From the IOC's ``uniblitzVCMD1.db`` (``<prefix>uniblitz:``). Each signal
    fires a serial command when written: ``open``/``close`` move the blade,
    ``fire`` pulses (trigger), ``reset`` re-initializes, and ``aux_enable``/
    ``aux_disable`` and ``gate_on``/``gate_off`` control the auxiliary and gate
    modes.
    """

    open = Component(EpicsSignal, "shutter:open", kind="omitted")
    close = Component(EpicsSignal, "shutter:close", kind="omitted")
    fire = Component(EpicsSignal, "control:trigger", kind="omitted")
    reset = Component(EpicsSignal, "control:reset", kind="omitted")
    aux_enable = Component(EpicsSignal, "aux:enable", kind="omitted")
    aux_disable = Component(EpicsSignal, "aux:disable", kind="omitted")
    gate_on = Component(EpicsSignal, "gate:on", kind="omitted")
    gate_off = Component(EpicsSignal, "gate:off", kind="omitted")