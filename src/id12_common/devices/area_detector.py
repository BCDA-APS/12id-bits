"""
EPICS area_detector definitions for 12-ID.
"""

import logging

from apstools.devices import CamMixin_V34
from ophyd.areadetector import CamBase
from ophyd.areadetector.cam import PilatusDetectorCam

logger = logging.getLogger(__name__)
logger.info(__file__)

class CamUpdates_V34(CamMixin_V34, CamBase):
    """
    Updates to CamBase since v22.

    PVs removed from AD now.
    """

    pool_max_buffers = None


class ID12_PilatusCam_V34(CamUpdates_V34, PilatusDetectorCam):
    """Pilatus Area Detector cam module for AD 3.4+"""
