"""
OMS MAXv motor stages for the ``12idb2`` VME IOC (12-ID-B).

The ``12idb2`` IOC drives two OMS MAXv controller cards through a vxWorks VME
crate. Only card 0 is populated: eight axes (``12idb2:m1``-``12idb2:m8``) are
loaded from ``iocBoot/ioc12idb2/substitutions/motor.substitutions`` against
``$(MOTOR)/db/motor.db`` (card 1 axes are commented out).

Component names follow the motor record ``DESC`` fields
(``M0X``/``M0Y``/``M1Y``/``M2X``/``M2Y``/``M2Z`` plus two rotation axes),
matching the identical OMS MAXv layout already named ``m0x``/``m0y``/``m1y``/
``m2x``/``m2y``/``m2z``/``m7``/``m8`` for the ``sydor_stage`` and
``acs2_optics`` stages in ``id12_e``.

Instantiate with the IOC prefix, e.g. ``prefix="12idb2:"``.
"""

from ophyd import Component
from ophyd import EpicsMotor
from ophyd import MotorBundle


class Idb2Stages(MotorBundle):
    """Eight OMS MAXv axes on the ``12idb2`` VME crate (card 0, ``m1``-``m8``).

    Each component is a standard ``EpicsMotor`` (synApps ``motor.db``); the
    suffix is the raw OMS axis name appended to the IOC prefix, so
    ``prefix="12idb2:"`` yields ``12idb2:m1`` ... ``12idb2:m8``.
    """

    m0x = Component(EpicsMotor, "m1")  # DESC "M0X" (mm)
    m0y = Component(EpicsMotor, "m2")  # DESC "M0Y" (mm)
    m1y = Component(EpicsMotor, "m3")  # DESC "M1Y" (mm)
    m2x = Component(EpicsMotor, "m4")  # DESC "M2X" (mm)
    m2y = Component(EpicsMotor, "m5")  # DESC "M2Y" (mm)
    m2z = Component(EpicsMotor, "m6")  # DESC "M2Z" (mm)
    m7 = Component(EpicsMotor, "m7")  # DESC "motor 7" (degrees)
    m8 = Component(EpicsMotor, "m8")  # DESC "motor 8" (degrees)
