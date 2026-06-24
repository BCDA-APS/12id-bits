"""
BLEPS (Beamline Equipment Protection System) status for ``12ida2`` (12-ID-A).

``bleps.cmd`` connects an EtherIP driver to the BLEPS PLC and loads
``bleps_ai/bi/bo.db`` from ``bleps.substitutions``. **These records use the
``12id:`` prefix, not ``12ida2:``** (the BLEPS PLC is shared across 12-ID).

This device exposes the high-level operational summary, the visual/audible
alarms, the per-beam-path permit/closed status, and the fault/trip reset
pushbuttons. The bulk of ``bleps_ai.db`` is a 210-record rolling fault / trip /
warning *history* (``12id:BLEPS:{FAULT,TRIP,WARN}:{ID,YEAR,...,SEC}:0-9``), and
the per-component sensor detail (gate valves ``GV*``, flows ``FLOW*``, temps
``TEMP*``, gauges ``IG*``/``IP*``) is intentionally **not** wrapped here — add
those components if a plan needs them.

Instantiate with ``prefix="12id:BLEPS:"``.
"""

from ophyd import Component
from ophyd import Device
from ophyd import EpicsSignal
from ophyd import EpicsSignalRO


class Bleps(Device):
    """BLEPS PLC operational status + reset controls (prefix ``12id:BLEPS:``)."""

    # --- global summary (bi) ---------------------------------------------
    fault_exists = Component(EpicsSignalRO, "FAULT_EXISTS")
    trip_exists = Component(EpicsSignalRO, "TRIP_EXISTS")
    warning_exists = Component(EpicsSignalRO, "WARNING_EXISTS")
    comm_fault = Component(EpicsSignalRO, "COMM_FAULT")

    # --- annunciator / alarm tower (bi) ----------------------------------
    alarm_red = Component(EpicsSignalRO, "ALARM:RED")
    alarm_yellow = Component(EpicsSignalRO, "ALARM:YELLOW")
    alarm_green = Component(EpicsSignalRO, "ALARM:GREEN")
    alarm_buzzer = Component(EpicsSignalRO, "ALARM:BUZZER")

    # --- beam-path permits + closed status (bi) --------------------------
    #     FES = front-end, SBS = B station, SCS = C station, BIV = isolation valve
    fes_permit = Component(EpicsSignalRO, "FES:PERMIT")
    fes_closed = Component(EpicsSignalRO, "FES:CLOSED")
    sbs_permit = Component(EpicsSignalRO, "SBS:PERMIT")
    sbs_closed = Component(EpicsSignalRO, "SBS:CLOSED")
    scs_permit = Component(EpicsSignalRO, "SCS:PERMIT")
    scs_closed = Component(EpicsSignalRO, "SCS:CLOSED")
    biv_permit = Component(EpicsSignalRO, "BIV:PERMIT")
    biv_closed = Component(EpicsSignalRO, "BIV:CLOSED")

    # --- reset pushbuttons (bo) ------------------------------------------
    fault_reset = Component(EpicsSignal, "FLT:RESET", kind="omitted")
    trip_reset = Component(EpicsSignal, "TRP:RESET", kind="omitted")
