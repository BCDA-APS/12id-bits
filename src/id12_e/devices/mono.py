"""
BESSRC monochromator support for the ``12ida2`` IOC (12-ID-A).

The mono is described by ``12ida2App/Db/BESSRCMono_new.db`` (loaded in
``optics.cmd`` with ``P=12ida2:, MTH=m19, MSLD=m22``). It computes photon
energy / wavelength / slide position from the Bragg angle (``m19``) and crystal
lattice spacing, and drives the slide (``m22``) to keep the exit beam fixed.

This wraps the energy/wavelength/lattice/mode records plus the two underlying
motors. All component suffixes are record names that exist in the loaded db.

.. note::
   ``EnCalc`` is the synApps ``calcout`` that holds the energy; whether you set
   energy by writing it directly or through a separate drive transform
   (``E2P_driveValue``) depends on the deployed configuration. Confirm the
   energy-drive entry point against the IOC / operator screen before scanning
   energy with this device.
"""

from ophyd import Component
from ophyd import Device
from ophyd import EpicsMotor
from ophyd import EpicsSignal
from ophyd import EpicsSignalRO


class BessrcMono(Device):
    """BESSRC double-crystal monochromator on ``12ida2``.

    Instantiate with ``prefix="12ida2:"``. ``theta`` is the Bragg-angle motor
    (m19) and ``slide`` the fixed-exit slide motor (m22).
    """

    # --- energy / wavelength / slide kinematics ---------------------------
    energy = Component(EpicsSignal, "EnCalc")  # calcout: photon energy
    wavelength = Component(EpicsSignalRO, "LambdaCalc")  # calcout
    slide_position = Component(EpicsSignalRO, "SlideCalc")  # calcout

    # --- crystal / calibration -------------------------------------------
    lattice_d = Component(EpicsSignal, "LatticeD")  # ao: d-spacing
    lattice_type = Component(EpicsSignal, "LatticeTypeMO", string=True)  # mbbo
    offset = Component(EpicsSignal, "Offset")  # angle offset

    # --- mode / motion control -------------------------------------------
    mode = Component(EpicsSignal, "Mono_Mode", string=True)  # bo
    use_mode = Component(EpicsSignal, "Mono_UseMode", string=True)  # bo
    done = Component(EpicsSignalRO, "Mono_DMOV")  # calcout: done-moving flag
    # NOTE: named ``mono_stop`` (not ``stop``) — ``stop`` is reserved by the
    # bluesky Device interface (``Device.stop()``).
    mono_stop = Component(EpicsSignal, "Mono_STOP", kind="omitted")  # dfanout
    slide_stop = Component(EpicsSignal, "MSLD_STOP", kind="omitted")  # calcout

    # --- underlying motors ------------------------------------------------
    theta = Component(EpicsMotor, "m19")  # MTH — Bragg angle
    slide = Component(EpicsMotor, "m22")  # MSLD — fixed-exit slide
