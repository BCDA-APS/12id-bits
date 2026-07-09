"""
CRL transfocator (PyDevice) for the ``12idmsCRL`` IOC (12-ID-MS).

``iocBoot/ioc12idmsCRL/cmds/pydeviceCRL_ms_12ID.cmd`` drives a PyDevice
``focusingSystem`` object (``PY_OBJECT=msCRL``) that runs xraylib optics math for
a two-element beryllium compound-refractive-lens transfocator: an upstream
element (US, 6 stacks) and a downstream element (DS, 4 stacks). The IOC picks a
lens configuration and lookup-table index for a requested beam energy and slit
size, then reports the achievable focal spot size.

All PVs are macro-templated ``pydev`` / soft records. This wrapper substitutes
the deployed macro values so every component suffix is a **real** record name:

======================  ==========================
macro                   resolved value
======================  ==========================
``$(P)`` (PREFIX)       ``12idmsCRL:``
``$(SYSID)`` (SYS_ID)   ``MS``
``$(OBJ)`` (PY_OBJECT)  ``msCRL``
``$(OE)`` per element   ``US`` / ``DS``
``$(SYSA)``/``$(SYSB)`` ``US`` / ``DS`` (system1/2 mbbo states)
``$(SAMA)``/``$(SAMB)`` ``C1`` / ``C2`` (sample-station states)
======================  ==========================

so, e.g., the record ``$(P)$(SYSID):energy`` is ``12idmsCRL:MS:energy`` and
``$(P)$(SYSID):$(OE):slitSize_H`` (with ``OE=US``) is
``12idmsCRL:MS:US:slitSize_H``. Instantiate the top device with the
system-scoped prefix ``prefix="12idmsCRL:MS:"``.

Sources: ``pyDevCRL_general.db`` (system controls, energy, focal size, sysType),
``pyDevCRL_2systems.db`` (system1/system2 assignment + sorted-index tweaks),
``pyDevCRL_2sampleSTN.db`` (sample-station selection), and the per-element
``pyDevCRL_slits.db`` + ``pyDevCRL_elem.db`` / ``pyDevCRL_elem_12IDUS.db``
(US and DS share an identical record set). ``energyTestTools.db`` (testMonoE /
testIDE stand-in energy PVs) is intentionally not wrapped.

.. note::
   The many ``pydev.iointr`` I/O-Intr records are readbacks pushed from Python;
   they are read-only here. The lookup-table / calc intermediates
   (``EnergyCalc``, ``*Conv``, ``*_dfo``, ``lens_decode``, ``lensSetSeq``,
   busy-fanout calcs, per-stack move links) are omitted — this is the
   user-facing interface, not every calc record. Add components from those db
   files if a plan needs them.
"""

from ophyd import Component
from ophyd import Device
from ophyd import EpicsSignal
from ophyd import EpicsSignalRO


class CrlElement(Device):
    """One transfocator optical element (US or DS) on ``12idmsCRL:MS``.

    Both elements are loaded from the identical ``pyDevCRL_elem*.db`` +
    ``pyDevCRL_slits.db`` record set, so the same class serves each; the parent
    mounts it with suffix ``"US:"`` or ``"DS:"``. ``sorted_index`` selects the
    focal-size-sorted lens configuration; ``lens_config`` is the raw bitmask of
    inserted lens stacks; ``slit_size_h``/``slit_size_v`` feed the beam size (in
    metres) into the optics model.
    """

    # --- slit sizes feeding the optics model (pyDevCRL_slits.db) ----------
    slit_size_h = Component(EpicsSignal, "slitSize_H")  # ao (m)
    slit_size_v = Component(EpicsSignal, "slitSize_V")  # ao (m)
    slit_size_h_rbv = Component(EpicsSignalRO, "slitSize_H_RBV")  # ai
    slit_size_v_rbv = Component(EpicsSignalRO, "slitSize_V_RBV")  # ai

    # --- lens configuration (pyDevCRL_elem.db) ---------------------------
    lenses = Component(EpicsSignalRO, "lenses")  # longin: inserted-lens bitmask
    lens_config = Component(EpicsSignal, "lensConfig_BW")  # longout: set bitmask
    lens_config_rbv = Component(EpicsSignal, "lensConfig_RBV")  # longout (pydev)
    sorted_index = Component(EpicsSignal, "sortedIndex")  # longout (pydev)
    sorted_index_rbv = Component(EpicsSignalRO, "sortedIndex_RBV")  # longin
    fsize_twk_up = Component(EpicsSignal, "fSize_twk_up", kind="omitted")  # calcout
    fsize_twk_dn = Component(EpicsSignal, "fSize_twk_dn", kind="omitted")  # calcout

    # --- element z-position offset (pyDevCRL_elem.db) --------------------
    position_offset = Component(EpicsSignal, "oePositionOffset")  # ao (m)
    position_offset_rbv = Component(EpicsSignalRO, "oePositionOffset_RBV")  # ai
    position_rbv = Component(EpicsSignalRO, "oePosition_RBV")  # ai (rel. source)
    inter_lens_delay = Component(EpicsSignal, "interLensDelay", kind="omitted")  # ao

    # --- per-element busy (pyDevCRL_elem.db) -----------------------------
    crl_busy = Component(EpicsSignalRO, "crlBusy")  # busy


class CrlTransfocator(Device):
    """12-ID-MS 2-element CRL transfocator (PyDevice, prefix ``12idmsCRL:MS:``).

    ``us`` / ``ds`` are the upstream/downstream optical elements. Energy can be
    taken from the beamline mono or set locally (``energy_select``); the model
    then optimises the lens picks and reports the achievable spot in
    ``focal_size_actual``. ``sys_type`` (1x/2x/KB) and ``system1``/``system2``
    choose the transfocator layout; ``sample`` selects the target sample
    station (C1/C2).
    """

    # --- optical elements ------------------------------------------------
    us = Component(CrlElement, "US:")  # upstream (6-stack) element
    ds = Component(CrlElement, "DS:")  # downstream (4-stack) element

    # --- energy selection (pyDevCRL_general.db) --------------------------
    energy_select = Component(EpicsSignal, "EnergySelect", string=True)  # bo Mono/Local
    energy_local = Component(EpicsSignal, "EnergyLocal")  # ao (keV)
    energy_beamline = Component(EpicsSignal, "EnergyBeamline")  # ao (keV, from mono)
    energy = Component(EpicsSignal, "energy")  # ao (keV) -> pydev updateE
    energy_rbv = Component(EpicsSignalRO, "energy_RBV")  # ai
    energy_calc = Component(EpicsSignalRO, "EnergyCalc", kind="omitted")  # calc

    # --- beam mode (pyDevCRL_general.db) ---------------------------------
    beam_mode = Component(EpicsSignal, "beamMode", string=True)  # bo Flat/Round
    beam_mode_rbv = Component(EpicsSignalRO, "beamMode_RBV", string=True)  # bi

    # --- focal size (pyDevCRL_general.db) --------------------------------
    focal_size = Component(EpicsSignal, "focalSize")  # ao (m) requested
    focal_size_actual = Component(EpicsSignalRO, "fSize_actual")  # ai (m)
    focal_size_preview = Component(EpicsSignalRO, "fSize_preview")  # ai (m)
    preview_index = Component(EpicsSignal, "previewIndex")  # longout (pydev)
    q = Component(EpicsSignalRO, "q")  # ai: last CRL image distance (m)
    dq = Component(EpicsSignalRO, "dq")  # ai: image distance to sample (m)

    # --- system type / layout (pyDevCRL_general.db + pyDevCRL_2systems.db)
    sys_type = Component(EpicsSignal, "sysType", string=True)  # mbbo 1x/2x/KB
    sys_type_rbv = Component(EpicsSignalRO, "sysType_RBV", string=True)  # mbbi
    single_crl = Component(EpicsSignalRO, "singleCRLbo", string=True)  # bo Double/Single
    system1 = Component(EpicsSignal, "system1", string=True)  # mbbo US/DS
    system1_rbv = Component(EpicsSignalRO, "system1_RBV", string=True)  # mbbi
    system2 = Component(EpicsSignal, "system2", string=True)  # mbbo US/DS
    system2_rbv = Component(EpicsSignalRO, "system2_RBV", string=True)  # mbbi

    # --- sample station (pyDevCRL_2sampleSTN.db) -------------------------
    sample = Component(EpicsSignal, "sample", string=True)  # mbbo C1/C2
    sample_rbv = Component(EpicsSignalRO, "sample_RBV", string=True)  # mbbi

    # --- lookup-table controls (pyDevCRL_general.db) ---------------------
    recalc_enable = Component(EpicsSignal, "recalc_enable", string=True)  # bo
    recalc_table = Component(EpicsSignal, "recalc_table", kind="omitted")  # bo trigger
    refind_config = Component(EpicsSignal, "refind_config", kind="omitted")  # bo trigger
    thickerr_flag = Component(EpicsSignal, "thickerr_flag", string=True)  # bo On/Off
    thickerr_flag_rbv = Component(EpicsSignalRO, "thickerr_flag_RBV")  # bi
    verbosity = Component(EpicsSignal, "verbosity", string=True, kind="omitted")  # bo

    # --- focal-size lookup tables (waveforms, pyDevCRL_general.db) --------
    fsizes = Component(EpicsSignalRO, "fSizes")  # waveform (DOUBLE)
    q_list = Component(EpicsSignalRO, "q_list")  # waveform (DOUBLE)
    dq_list = Component(EpicsSignalRO, "dq_list")  # waveform (DOUBLE)

    # --- system busy (pyDevCRL_general.db) -------------------------------
    sys_busy = Component(EpicsSignalRO, "sysBusy")  # busy
