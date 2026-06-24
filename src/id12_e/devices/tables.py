"""
Optical tables for the ``12ida2`` IOC (12-ID-A).

``optics.cmd`` loads four synApps ``table`` records (``$(OPTICS)`` ``table.db``)
that solve the 6-DOF kinematics of each kinematic-mount optical table from its
underlying jack/translation motors:

======  ================  ==============================  ========
record  table             motors (M0X,M0Y,M1Y,M2X,M2Y)    geometry
======  ================  ==============================  ========
table1  WB mirror table   m12, m10, m9, m13, m11          SRI
table2  Mono table        m17, m15, m14, m18, m16         SRI
table3  Vmirror table     -, m27, m26, -, m25             NEWPORT
table4  Table 4           -, m34, m35, -, m33             SRI
======  ================  ==============================  ========

Each table is a single EPICS ``table`` record; the lab-frame degrees of freedom
are *fields* of that record. Drive fields ``X/Y/Z/AX/AY/AZ`` move the table;
``XRB/YRB/ZRB/AXRB/AYRB/AZRB`` are the raw readbacks (where the table really is,
computed from the motor positions). Instantiate with the record name as prefix,
e.g. ``prefix="12ida2:table2"``.
"""

from ophyd import Component
from ophyd import Device
from ophyd import EpicsSignal
from ophyd import EpicsSignalRO


class OpticalTable(Device):
    """A synApps 6-DOF kinematic optical ``table`` record on ``12ida2``.

    ``x``/``y``/``z`` are translation drive fields and ``ax``/``ay``/``az`` the
    angle drive fields; the ``*_rb`` signals are the corresponding raw
    readbacks. ``geometry`` reports the mount type (SRI/NEWPORT/...). Note that
    a table only moves the DOF its motors support (e.g. NEWPORT/Vmirror tables
    leave X/AZ unpopulated).
    """

    # --- drive fields (lab-frame setpoints) -------------------------------
    x = Component(EpicsSignal, ".X")
    y = Component(EpicsSignal, ".Y")
    z = Component(EpicsSignal, ".Z")
    ax = Component(EpicsSignal, ".AX")
    ay = Component(EpicsSignal, ".AY")
    az = Component(EpicsSignal, ".AZ")

    # --- raw readbacks (computed from motor positions) --------------------
    x_rb = Component(EpicsSignalRO, ".XRB")
    y_rb = Component(EpicsSignalRO, ".YRB")
    z_rb = Component(EpicsSignalRO, ".ZRB")
    ax_rb = Component(EpicsSignalRO, ".AXRB")
    ay_rb = Component(EpicsSignalRO, ".AYRB")
    az_rb = Component(EpicsSignalRO, ".AZRB")

    # --- configuration ----------------------------------------------------
    geometry = Component(EpicsSignalRO, ".GEOM", string=True)
