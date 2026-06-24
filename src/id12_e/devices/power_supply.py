"""
BK Precision 9205B programmable power supply for the ``12ida2`` IOC (12-ID-A).

``serial.cmd`` loads ``12ida2App/Db/BK9205B.db`` (streamDevice, ``BK9205B.proto``)
with ``P=12ida2:, PS=1, PORT=serial2``. Records live under
``12ida2:BK9205B:1:``.

Instantiate with ``prefix="12ida2:BK9205B:1:"``.
"""

from ophyd import Component
from ophyd import Device
from ophyd import EpicsSignal
from ophyd import EpicsSignalRO


class BK9205B(Device):
    """BK Precision 9205B power supply (unit ``1``) on ``12ida2``.

    ``voltage``/``current`` are the setpoints; ``*_rbv`` their device-reported
    readbacks; ``v_meas``/``i_meas`` the live measured output; ``on``/``off``
    are momentary output-enable pushbuttons.
    """

    # --- measured output --------------------------------------------------
    v_meas = Component(EpicsSignalRO, "Vmeas")
    i_meas = Component(EpicsSignalRO, "Imeas")
    watts = Component(EpicsSignalRO, "Watts")

    # --- setpoints + readbacks -------------------------------------------
    voltage = Component(EpicsSignal, "Vset")
    current = Component(EpicsSignal, "Iset")
    voltage_rbv = Component(EpicsSignalRO, "Vset_rbk")
    current_rbv = Component(EpicsSignalRO, "Iset_rbk")
    voltage_limit = Component(EpicsSignal, "Vlimit_Set")
    current_limit = Component(EpicsSignal, "Ilimit_Set")

    # --- output enable (momentary) ---------------------------------------
    on = Component(EpicsSignal, "On", kind="omitted")
    off = Component(EpicsSignal, "Off", kind="omitted")

    # --- local/remote -----------------------------------------------------
    local = Component(EpicsSignal, "Local", kind="omitted")
    remote = Component(EpicsSignal, "Remote", kind="omitted")
