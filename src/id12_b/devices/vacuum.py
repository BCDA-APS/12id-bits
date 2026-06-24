"""
Vacuum devices for 12-ID-B and the 12-ID-A front end.

``TPG261`` is the single-gauge readout from the ``12idb`` IOC's ``TPG261.db``
(gauge ``G1`` → ``12idb:G1:``): pressure plus unit/status/id and two relay
setpoints.

``IonGauge``, ``IonPump`` and ``CryoLevelMeter`` wrap the front-end vacuum
hardware on the ``12ida1`` IOC: Granville-Phillips GP307 ion gauges
(``vs.db`` → ``12ida1:IG1``…), Digitel/PI-MPC ion pumps (``digitelPump.db`` →
``12ida1:IP1``…) and Oxford ILM202 cryogen level meters
(``Oxford_ILM202.db`` → ``12ida1:s1``…). The ``vs``/``digitel`` records are
single special-record types whose ``.VAL`` is the pressure, so those devices
expose only that grounded readback.
"""

from ophyd import Component
from ophyd import Device
from ophyd import EpicsSignal
from ophyd import EpicsSignalRO


class TPG261(Device):
    """TPG261 vacuum gauge (one gauge channel).

    ``pressure`` — gauge pressure readback. ``unit``/``status``/``gauge_id``
    describe the reading. ``setpoint1``/``setpoint2`` write the two relay
    thresholds; ``sp1_value``/``sp2_value`` and ``sp1_status``/``sp2_status``
    read them back.
    """

    pressure = Component(EpicsSignalRO, "PRES")
    unit = Component(EpicsSignalRO, "UNIT", string=True)
    status = Component(EpicsSignalRO, "STATUS", string=True)
    gauge_id = Component(EpicsSignalRO, "ID", string=True)

    setpoint1 = Component(EpicsSignal, "SET1")
    setpoint2 = Component(EpicsSignal, "SET2")
    sp1_value = Component(EpicsSignalRO, "SP1V")
    sp2_value = Component(EpicsSignalRO, "SP2V")
    sp1_status = Component(EpicsSignalRO, "SP1S", string=True)
    sp2_status = Component(EpicsSignalRO, "SP2S", string=True)

    set_unit = Component(EpicsSignal, "SUNIT", string=True)
    start = Component(EpicsSignal, "START", kind="omitted")


class IonGauge(Device):
    """Granville-Phillips GP307 ion gauge (12-ID-A ``vs`` record).

    The whole device is a single ``vs`` record (e.g. ``12ida1:IG1``); its
    value is the gauge ``pressure``. Instantiate with the full record name as
    the prefix.
    """

    pressure = Component(EpicsSignalRO, "")


class IonPump(Device):
    """Digitel / PI-MPC ion pump (12-ID-A ``digitel`` record).

    The whole device is a single ``digitel`` record (e.g. ``12ida1:IP1``); its
    value is the pump ``pressure``. Instantiate with the full record name as
    the prefix.
    """

    pressure = Component(EpicsSignalRO, "")


class CryoLevelMeter(Device):
    """Oxford ILM202 cryogen level meter (12-ID-A, prefix ``12ida1:s1``).

    ``level1``/``level2`` are the two channel level readbacks and ``usage`` is
    the raw helium-usage readback; ``on_off`` enables/disables the meter.
    """

    level1 = Component(EpicsSignalRO, "_ILM_level1")
    level2 = Component(EpicsSignalRO, "_ILM_level2")
    usage = Component(EpicsSignalRO, "_ILM_usage_raw")
    on_off = Component(EpicsSignal, "_ILM_on_off")
