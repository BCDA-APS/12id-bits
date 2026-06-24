"""
Granville-Phillips GP307 vacuum gauge for the ``12ida2`` IOC (12-ID-A).

``serial.cmd`` loads the VAC module's ``$(VAC)/db/vs.db`` with
``P=12ida2:, GAUGE=IG5, PORT=serial5, DEV=GP307``. ``vs.db`` is a single synApps
``vs`` (vacuum-gauge) record whose value is the measured pressure.

Instantiate with ``prefix="12ida2:IG5"`` (the gauge record name).
"""

from ophyd import Component
from ophyd import Device
from ophyd import EpicsSignalRO


class GP307Gauge(Device):
    """GP307 ion-gauge pressure readout (``IG5``) on ``12ida2``.

    ``pressure`` reads the ``vs`` record itself (``12ida2:IG5``).
    """

    pressure = Component(EpicsSignalRO, "")  # vs record .VAL — measured pressure
