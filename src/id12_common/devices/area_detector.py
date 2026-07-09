"""areaDetector support for 12-ID.

Site cam and NDPlugin subclasses referenced by the ``ad_creator`` entries in
each station's ``ad_devices.yml``. The cam subclasses adapt the stock ophyd cam
to the ADCore revision deployed at 12-ID (drop PVs no longer served, add the
Eiger ``Initialize``); the ``ID12_*`` plugin subclasses null a property that
current AD IOCs no longer expose. Nothing here connects to hardware at import
time — the objects are only built when guarneri loads ``ad_devices.yml``.

Pattern mirrors ``id8_common.devices.area_detector`` at 8-ID.
"""

from apstools.devices import AD_EpicsFileNameHDF5Plugin
from apstools.devices import CamMixin_V34
from ophyd import ADComponent
from ophyd import EpicsSignal
from ophyd.areadetector import CamBase
from ophyd.areadetector import EigerDetectorCam
from ophyd.areadetector.cam import PilatusDetectorCam
from ophyd.areadetector.plugins import CodecPlugin_V34
from ophyd.areadetector.plugins import ImagePlugin_V34
from ophyd.areadetector.plugins import OverlayPlugin_V34
from ophyd.areadetector.plugins import PluginBase_V34
from ophyd.areadetector.plugins import ProcessPlugin_V34
from ophyd.areadetector.plugins import PvaPlugin_V34
from ophyd.areadetector.plugins import ROIPlugin_V34
from ophyd.areadetector.plugins import StatsPlugin_V34
from ophyd.areadetector.plugins import TransformPlugin_V34
from ophyd.ophydobj import Kind


class CamBase_V34(CamBase):
    """CamBase minus PVs removed from current ADCore."""

    pool_max_buffers = None


class ID12_EigerCam_V34(CamMixin_V34, EigerDetectorCam):
    """Dectris Eiger cam for the ADCore revision at 12-ID (12idbEGR)."""

    initialize = ADComponent(EpicsSignal, "Initialize", kind="config")

    # Not present on the 12-ID Eiger2.
    file_number_sync = None
    file_number_write = None


class ID12_PilatusCam_V34(CamMixin_V34, PilatusDetectorCam):
    """Dectris Pilatus cam for 12-ID (used by the pilatus ad_devices entries)."""

    file_number_sync = None
    file_number_write = None


class ID12_SpinnakerCam_V34(CamMixin_V34, CamBase_V34):
    """FLIR/Point Grey Blackfly-S cam (ADSpinnaker) for 12-ID (12idBFS1/12idBFS2).

    ADSpinnaker has no dedicated stock ophyd cam class, so this is a thin
    subclass over the standard AD cam interface. The camera's model-specific
    GenICam feature PVs (from ``spinnaker.template`` / the IOC's jxVimbaApp
    model template) can be added as ADComponents later if a scan needs them.
    """


class ID12_PluginMixin(PluginBase_V34):
    """Null a property no longer served by current AD IOCs."""

    _asyn_pipeline_configuration_names = None


class ID12_CodecPlugin(ID12_PluginMixin, CodecPlugin_V34):
    """Site codec plugin (needed by PVA and HDF)."""


class ID12_ImagePlugin(ID12_PluginMixin, ImagePlugin_V34):
    """Site image plugin."""


class ID12_OverlayPlugin(ID12_PluginMixin, OverlayPlugin_V34):
    """Site overlay plugin."""


class ID12_ProcessPlugin(ID12_PluginMixin, ProcessPlugin_V34):
    """Site process plugin."""


class ID12_PvaPlugin(ID12_PluginMixin, PvaPlugin_V34):
    """Site PVA plugin."""


class ID12_ROIPlugin(ID12_PluginMixin, ROIPlugin_V34):
    """Site region-of-interest plugin."""


class ID12_StatsPlugin(ID12_PluginMixin, StatsPlugin_V34):
    """Site statistics plugin."""


class ID12_TransformPlugin(ID12_PluginMixin, TransformPlugin_V34):
    """Site transform plugin."""


class ID12_EpicsFileNameHDF5Plugin(ID12_PluginMixin, AD_EpicsFileNameHDF5Plugin):
    """HDF5 file writer with EPICS-controlled file names."""


def ad_setup(det):
    """not a plan: prepare a 12-ID area detector after instantiation.

    Call from a station ``startup.py`` after the detector is created (guarneri
    builds the object; this tunes stage_sigs). Safe to call off-subnet — it only
    edits stage_sigs and does not connect.
    """
    det.cam.stage_sigs["wait_for_plugins"] = "Yes"
    for nm in det.component_names:
        obj = getattr(det, nm)
        if "blocking_callbacks" in dir(obj):  # it's a plugin
            obj.stage_sigs["blocking_callbacks"] = "No"
    if hasattr(det, "hdf1"):
        det.hdf1.kind = Kind.config | Kind.normal  # ensure the writer is read
        if "capture" in det.hdf1.stage_sigs:
            det.hdf1.stage_sigs.move_to_end("capture", last=True)
