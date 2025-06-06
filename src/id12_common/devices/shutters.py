"""Custom shutter support for 12ID."""

from apstools.devices.shutters import ApsPssShutter


class ID12_ApsPssShutter(ApsPssShutter):
    """Adjust the delay time as a kwarg."""

    def __init__(self, prefix, *args, delay_s=1.2, **kwargs):
        """."""
        self.delay_s = delay_s
        super().__init__(prefix, *args, **kwargs)
