"""
12-ID PyDevice x-ray filter (attenuator) support.

The ``12idPyFilter`` IOC uses PyDevice + ``xraylib`` to pick the optimal
combination of absorber foils for a requested transmission/attenuation at the
working photon energy, then drives the foils through a LabJack. One filter
*system* is deployed (``FL1``); each system carries up to 12 foils (8 active:
4 Al + 4 Ti). PVs live under ``$(P)$(FILTER_ID):``, i.e. ``12idPyFilter:FL1:``.

Read from the IOC's own databases (``pyDevFilters.db`` + the per-foil
``pyDevFilter_individual.db``); internal calc/transform/sequence plumbing is
intentionally not exposed.
"""

from ophyd import Component
from ophyd import Device
from ophyd import EpicsSignal
from ophyd import EpicsSignalRO


class PyFilterUnit(Device):
    """A single absorber foil within a :class:`PyFilter` system.

    ``inserted``  — drive the foil In/Out (``bo``).
    ``readback``  — actual In/Out state (``bi``).
    ``thickness`` / ``material`` — fixed foil properties (set at IOC boot).
    ``lock``      — hold the foil at its current state.
    ``enable``    — include this foil in the attenuation optimization.
    """

    inserted = Component(EpicsSignal, "", string=True)
    readback = Component(EpicsSignalRO, "_RBV", string=True)
    thickness = Component(EpicsSignal, "_thickness")
    material = Component(EpicsSignal, "_material", string=True)
    lock = Component(EpicsSignal, "_Lock", string=True)
    enable = Component(EpicsSignal, "_Enable", string=True)


class PyFilter(Device):
    """12-ID PyDevice x-ray filter bank (system ``FL1``).

    Request a beam attenuation with ``transmission`` (fraction, 0–1) or
    ``attenuation`` (factor ≥ 1 = 1/transmission); the IOC solves for the foil
    set at the active ``energy`` and inserts/retracts the foils. ``filter01``…
    ``filter08`` are the individual foils (:class:`PyFilterUnit`).

    Instantiate with the system prefix, e.g. ``prefix="12idPyFilter:FL1:"``.
    """

    # --- attenuation / transmission control -------------------------------
    transmission = Component(EpicsSignal, "transmission")
    attenuation = Component(EpicsSignal, "attenuation")
    atten_factor = Component(EpicsSignal, "attenFactor")

    transmission_rbv = Component(EpicsSignalRO, "transmission_RBV")
    attenuation_actual = Component(EpicsSignalRO, "attenuation_actual")
    attenuation_preview = Component(EpicsSignalRO, "attenuation_preview")
    attenuation_2e_actual = Component(EpicsSignalRO, "attenuation_2E_actual")
    attenuation_3e_actual = Component(EpicsSignalRO, "attenuation_3E_actual")
    atten_up = Component(EpicsSignalRO, "atten_up")
    atten_dn = Component(EpicsSignalRO, "atten_dn")

    # --- sorted-index navigation (step through achievable attenuations) ----
    sorted_index = Component(EpicsSignal, "sortedIndex")
    sorted_index_rbv = Component(EpicsSignalRO, "sortedIndex_RBV")
    preview_index = Component(EpicsSignal, "previewIndex")

    # --- working photon energy --------------------------------------------
    energy = Component(EpicsSignal, "energy")
    energy_rbv = Component(EpicsSignalRO, "energy_RBV")
    energy_select = Component(EpicsSignal, "EnergySelect", string=True)
    energy_local = Component(EpicsSignal, "EnergyLocal")
    energy_beamline = Component(EpicsSignalRO, "EnergyBeamline")

    # --- configuration bitmask + fixed-in / fixed-out foil masks ----------
    filter_config = Component(EpicsSignalRO, "filterConfig")
    filter_config_rbv = Component(EpicsSignalRO, "filterConfig_RBV")
    filter_config_bw = Component(EpicsSignal, "filterConfig_BW")
    in_mask = Component(EpicsSignal, "inMask")
    out_mask = Component(EpicsSignal, "outMask")
    in_mask_rbv = Component(EpicsSignalRO, "inMask_RBV")
    out_mask_rbv = Component(EpicsSignalRO, "outMask_RBV")

    # --- actions / status -------------------------------------------------
    all_in = Component(EpicsSignal, "allIN.PROC", kind="omitted")
    all_out = Component(EpicsSignal, "allOUT.PROC", kind="omitted")
    inter_filter_delay = Component(EpicsSignal, "interFilterDelay")
    busy = Component(EpicsSignalRO, "filterBusy", string=True)
    verbosity = Component(EpicsSignal, "verbosity", string=True, kind="omitted")

    # --- individual foils (8 active; foils 09–12 exist in the template ----
    #     but are commented out at NUM_FILTERS=8 — add them if enabled) -----
    filter01 = Component(PyFilterUnit, "filter01")
    filter02 = Component(PyFilterUnit, "filter02")
    filter03 = Component(PyFilterUnit, "filter03")
    filter04 = Component(PyFilterUnit, "filter04")
    filter05 = Component(PyFilterUnit, "filter05")
    filter06 = Component(PyFilterUnit, "filter06")
    filter07 = Component(PyFilterUnit, "filter07")
    filter08 = Component(PyFilterUnit, "filter08")
