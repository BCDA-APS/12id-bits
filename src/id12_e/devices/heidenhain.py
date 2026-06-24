"""
Heidenhain ND280 encoder readout for the ``12ida2`` IOC (12-ID-A).

``optics.cmd`` loads ``12ida2App/Db/heid.db`` with ``P=12ida2:, H=heid1,
PORT=serial1``. A ``bo`` (``heid1Trigger``) polls the ND280 over the serial
``asyn`` port once per second; a ``scalcout`` parses the reply string into the
``heid1Reading`` ``ai`` (the encoder position).

Instantiate with ``prefix="12ida2:heid1"``.
"""

from ophyd import Component
from ophyd import Device
from ophyd import EpicsSignal
from ophyd import EpicsSignalRO


class Heidenhain(Device):
    """Heidenhain ND280 encoder position readout (``heid1``) on ``12ida2``."""

    reading = Component(EpicsSignalRO, "Reading")  # ai: parsed encoder value
    trigger_poll = Component(EpicsSignal, "Trigger", kind="omitted")  # bo poll
