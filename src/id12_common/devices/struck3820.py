"""Struck3820 at 12-ID is missing a clock frequency PV."""

from apstools.devices.struck3820 import Struck3820


class ID12_Struck3820(Struck3820):
    """Override for Struck3820 at 12ID."""

    clock_frequency = None
