"""
Double-crystal monochromator (DCM) at the 12-ID-A front end.

Wraps the custom ``SB_DCM.db`` loaded by the ``12ida1`` IOC (prefix
``12ida1:``). The monochromator energy is driven through a chain of
``transform``/``calcout`` records: writing a photon energy (keV) to
``12ida1:DCM:E2P_driveValue.A`` recomputes the Bragg angles and moves the two
crystal-rotation motors (``m9``/``m11``) and the second-crystal height
(``m14``); ``12ida1:DCM:EnRBV`` is the energy readback and ``12ida1:DCM_DMOV``
reports done-moving. The B hutch reads/scans this energy because the
front-end DCM defines the beam delivered downstream.
"""

from ophyd import Component
from ophyd import Device
from ophyd import EpicsMotor
from ophyd import EpicsSignal
from ophyd import EpicsSignalRO
from ophyd import PVPositioner


class DcmEnergy(PVPositioner):
    """Photon-energy positioner for the 12-ID-A DCM (keV).

    ``setpoint`` writes the requested energy to the ``E2P_driveValue``
    transform's ``A`` field, which clamps it to the configured limits and
    drives the crystal motors. ``readback`` is the soft energy readback and
    ``done`` is the composite done-moving flag (true when the Bragg motor has
    settled); ``stop_signal`` fans out a stop to the crystal motors.
    """

    setpoint = Component(EpicsSignal, "DCM:E2P_driveValue.A")
    readback = Component(EpicsSignalRO, "DCM:EnRBV")
    done = Component(EpicsSignalRO, "DCM_DMOV")
    stop_signal = Component(EpicsSignal, "DCM_STOP", kind="omitted")

    done_value = 1
    stop_value = 1


class DoubleCrystalMonochromator(Device):
    """12-ID-A double-crystal monochromator (``12ida1:`` prefix).

    ``energy`` is the keV positioner (use it to ``mv``/scan energy);
    ``wavelength`` is the matching wavelength readback (Angstrom). ``offset``
    is the nominal crystal offset (mm) and ``crystal1_2d``/``crystal2_2d`` are
    the crystal 2d-spacings (Angstrom) used by the energy transform;
    ``hc_over_e`` is the hc/E constant. ``z2_mode`` selects the
    second-crystal height-tracking mode and ``calibrate`` triggers a
    calibration (write-to-act). ``bragg1``/``chi1``/``bragg2``/``chi2``/
    ``height2``/``z2`` are the six crystal-stage motors (m9-m14).
    """

    energy = Component(DcmEnergy, "")
    wavelength = Component(EpicsSignalRO, "DCM:LambdaRBV")

    offset = Component(EpicsSignal, "DCM:Offset")
    crystal1_2d = Component(EpicsSignal, "DCM:C1_2D")
    crystal2_2d = Component(EpicsSignal, "DCM:C2_2D")
    hc_over_e = Component(EpicsSignal, "DCM:HC_OVER_E")

    z2_mode = Component(EpicsSignal, "Z2_Mode")
    calibrate = Component(EpicsSignal, "DCM_Calibrate", kind="omitted")

    bragg1 = Component(EpicsMotor, "m9")
    chi1 = Component(EpicsMotor, "m10")
    bragg2 = Component(EpicsMotor, "m11")
    chi2 = Component(EpicsMotor, "m12")
    height2 = Component(EpicsMotor, "m13")
    z2 = Component(EpicsMotor, "m14")
