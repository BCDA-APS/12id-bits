"""
Motor stages for the ``12ida2`` VME IOC (12-ID-A general support).

The ``12ida2`` IOC drives 40 stepper axes through five OMS MAXv VME controller
cards (``12ida2:m1``-``12ida2:m40``, loaded from ``motor.substitutions`` against
``$(MOTOR)/db/motor.db``) plus ten ``softMotor`` axes (``12ida2:SM1``-``SM10``,
``$(STD)/stdApp/Db/softMotor.db``). The DESC fields are generic ("motor N"), so
the axes are exposed under their raw OMS names.

It also exposes the APS-Upgrade Variable Mask Aperture Slit (VMAS) assembly
``SL2`` as a bundle of four pseudo-motors (``$(MOTOR)/motorApp/Db/pseudoMotor.db``
loaded by ``vmas.iocsh``): horizontal/vertical aperture *size* and *center*,
which the IOC computes from the underlying yaw/pitch/horizontal/diagonal stages.

Instantiate each bundle with the IOC prefix (``prefix="12ida2:"``) except the
VMAS aperture, whose prefix already includes the ``SL2:`` assembly segment.
"""

from ophyd import Component
from ophyd import EpicsMotor
from ophyd import MotorBundle


class Ida2Stages(MotorBundle):
    """The 40 OMS MAXv axes on ``12ida2`` (five cards, ``m1``-``m40``).

    Generic axes (DESC "motor N"); several are wired into the optical tables,
    mono, and slits declared in the other ``id12_e`` device modules. Instantiate
    with ``prefix="12ida2:"`` so each component resolves to ``12ida2:m1`` ...
    ``12ida2:m40``.
    """

    m1 = Component(EpicsMotor, "m1")
    m2 = Component(EpicsMotor, "m2")
    m3 = Component(EpicsMotor, "m3")
    m4 = Component(EpicsMotor, "m4")
    m5 = Component(EpicsMotor, "m5")
    m6 = Component(EpicsMotor, "m6")
    m7 = Component(EpicsMotor, "m7")
    m8 = Component(EpicsMotor, "m8")
    m9 = Component(EpicsMotor, "m9")
    m10 = Component(EpicsMotor, "m10")
    m11 = Component(EpicsMotor, "m11")
    m12 = Component(EpicsMotor, "m12")
    m13 = Component(EpicsMotor, "m13")
    m14 = Component(EpicsMotor, "m14")
    m15 = Component(EpicsMotor, "m15")
    m16 = Component(EpicsMotor, "m16")
    m17 = Component(EpicsMotor, "m17")
    m18 = Component(EpicsMotor, "m18")
    m19 = Component(EpicsMotor, "m19")  # BESSRC mono theta (MTH)
    m20 = Component(EpicsMotor, "m20")
    m21 = Component(EpicsMotor, "m21")
    m22 = Component(EpicsMotor, "m22")  # BESSRC mono slide (MSLD)
    m23 = Component(EpicsMotor, "m23")
    m24 = Component(EpicsMotor, "m24")
    m25 = Component(EpicsMotor, "m25")
    m26 = Component(EpicsMotor, "m26")
    m27 = Component(EpicsMotor, "m27")
    m28 = Component(EpicsMotor, "m28")
    m29 = Component(EpicsMotor, "m29")
    m30 = Component(EpicsMotor, "m30")
    m31 = Component(EpicsMotor, "m31")
    m32 = Component(EpicsMotor, "m32")
    m33 = Component(EpicsMotor, "m33")
    m34 = Component(EpicsMotor, "m34")
    m35 = Component(EpicsMotor, "m35")
    m36 = Component(EpicsMotor, "m36")
    m37 = Component(EpicsMotor, "m37")  # mini-hutch V slit
    m38 = Component(EpicsMotor, "m38")  # mini-hutch V slit
    m39 = Component(EpicsMotor, "m39")  # mini-hutch H slit
    m40 = Component(EpicsMotor, "m40")  # mini-hutch H slit


class Ida2SoftMotors(MotorBundle):
    """The ten ``softMotor`` axes on ``12ida2`` (``SM1``-``SM10``).

    Soft (calc-backed) motor records from ``$(STD)/stdApp/Db/softMotor.db``.
    Instantiate with ``prefix="12ida2:"``.
    """

    sm1 = Component(EpicsMotor, "SM1")
    sm2 = Component(EpicsMotor, "SM2")
    sm3 = Component(EpicsMotor, "SM3")
    sm4 = Component(EpicsMotor, "SM4")
    sm5 = Component(EpicsMotor, "SM5")
    sm6 = Component(EpicsMotor, "SM6")
    sm7 = Component(EpicsMotor, "SM7")
    sm8 = Component(EpicsMotor, "SM8")
    sm9 = Component(EpicsMotor, "SM9")
    sm10 = Component(EpicsMotor, "SM10")


class VmasAperture(MotorBundle):
    """APS-U Variable Mask Aperture Slit ``SL2`` on ``12ida2``.

    Four pseudo-motors (``$(MOTOR)/motorApp/Db/pseudoMotor.db``) that the IOC
    drives from the yaw/pitch/horizontal/diagonal stages (m2/m4/m1/m3):

    * ``hsize`` / ``vsize``     — aperture horizontal / vertical size
    * ``hcenter`` / ``vcenter`` — aperture horizontal / vertical center

    Instantiate with ``prefix="12ida2:SL2:"`` so the components resolve to
    ``12ida2:SL2:hSize`` etc.
    """

    hsize = Component(EpicsMotor, "hSize")
    vsize = Component(EpicsMotor, "vSize")
    hcenter = Component(EpicsMotor, "hCenter")
    vcenter = Component(EpicsMotor, "vCenter")
