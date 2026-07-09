# TODO — IOCs without a working BITS device

_Scope: EPICS IOCs under `../epics/` with **no active (uncommented) device** in
`src/id12_b` or `src/id12_e`. Verified against the config files on 2026-07-09:
21 of 33 IOCs implemented, **12 remaining** — all listed below, grouped by the
reason each can't be finished right now. Package mapping: B-hutch + A1 →
`id12_b`; C/D/E/MS + A2 + shared → `id12_e`._

## Reason: IOC does not load its hardware yet

The device PVs do not exist even when the IOC runs — hardware loading is
commented out in the IOC's `st.cmd` / `iocsh/motors.iocsh` (or loaded only via
example iocsh). Nothing can be built on the BITS side until the IOC is activated.
Each already has a commented placeholder in the `id12_*` configs; uncomment (and
confirm the axis/PV map) once the IOC loads its hardware.

- [ ] **12iddMCS2** (`id12_e`) — OMS MAXv table motors; all motor/scaler/MCA loading commented in `motors.iocsh`.
- [ ] **12idbLJ1** (`id12_b`) — 2× LabJack T7 + BLEPS; loaded via `examples/` iocsh, not the active `st.cmd`.
- [ ] **12idcACS2** (`id12_e`) — ACS/OMS optics (MLL, Bragg mono, slits); loading commented in `motors.iocsh`.
- [ ] **12idcCRL** (`id12_e`) — SmarAct MCS2 piezo CRL optics; commented stub in `devices.yml`.
- [ ] **12ideACS1** (`id12_e`) — ACS SPiiPlus + BLEPS; ACS axes not activated.
- [ ] **12ideCC** (`id12_e`) — E-endstation combo (ACS 32-axis, MCA, LabJack, quadEM, KB); not wired in `st.cmd`.
- [ ] **12ideGALIL** (`id12_e`) — Galil controller; scaffold IOC with placeholder DTYP (no real driver loaded).
- [ ] **12ideSydor** (`id12_e`) — OMS MAXv Sydor stages; loading commented in `motors.iocsh`.

## Reason: awaiting a design decision (buildable once decided)

Source is ready — these could be built now, but a choice is pending.

- [ ] **12idPS1** — AVT Mako G319B camera (`12idPS1:`). areaDetector, ADVimba (**no stock ophyd cam**). Needs `ID12_MakoCam_V34(CamMixin_V34, CamBase_V34)` in `id12_common/devices/area_detector.py` + an `ad_creator` entry (cam, image). **Decision: which package?** (the BFS Blackfly cameras went to `id12_e`.)
- [ ] **12idPS2** — AVT Mako G319C camera (`12idPS2:`). Same as PS1.
- [ ] **12idPS3** — AVT Mako G319C camera (`12idPS3:`). Same as PS1.

## Reason: combo IOC — not a single device

- [ ] **12idbCC** (`id12_b`) — 12-ID-B C-endstation combo (`12idbCC:`). Multiple subsystems, build each separately: ACS SPiiPlus motors (`mb_creator`), LabJack T7 (`apstools…LabJackT7`), Canberra MCA (`ophyd.mca.EpicsMCA`), quadEM (`ophyd.quadem.QuadEM`), KB pseudo-motors. Its `$(INSTANCE)`-templated camera options (adsc/andor/andor3/eiger) **cannot be pinned** until the concrete camera is known.

---

_Implemented this pass (not in this list): 12idbEGR (Eiger), 12idbACS1 (ACS),
12idmsCRL (CRL transfocator), 12idBFS1/12idBFS2 (Blackfly-S). Also open: the
incomplete `xsp3` entry in `id12_e/configs/ad_devices.yml` is commented out —
complete or remove it._
