"""
Non-EPICS support for the DG645 delay generator

Communications via ethernet to reduce overhead (status checking).

SPEC support here:
  /home/beams15/S12STAFF/spec_macros/std_macros/DET_common.mac
  /home/beams15/S12STAFF/spec_macros/std_macros/DG645_lee.mac

=======  ===================
station  address
=======  ===================
12idb    10.54.122.66:5025
12idc    10.54.122.104:5025
=======  ===================
"""

import socket  # https://docs.python.org/3/library/socket.html

from ophyd import Component
from ophyd import Device
from ophyd import Signal

BNC_MAP: dict[str, dict[str, int | str]] = {
    # DG645_INSTR: {DG645_AMP, DG645_OUT}
    "Base": {"amp": 2.5, "out": "T0"},
    "Shutter": {"amp": 4.0, "out": "AB"},
    "Detector": {"amp": 3.0, "out": "CD"},
    "Struck_ADV": {"amp": 2.5, "out": "EF"},
    "Struck_INH": {"amp": 4.5, "out": "GH"},
}

DG645_CH: list[str] = "T0 T1 A B C D E F G H".split()

DG645_TSRC = [
    "Internal",
    "External rising edges",
    "External falling edges",
    "Single shot external rising edges",
    "Single shot external falling edges",
    "Single shot",
    "Line",
]


class SocketDG645DelayGen(Device):
    """DG645 with socket communications"""

    # TODO:

    address = Component(Signal, value="", kind="config")
    burst_maxtime_limit = Component(Signal, value=41, kind="config")

    buffer_size = 1024  # assuming short communications

    def __init__(self, *args, address="0.0.0.0:5025", **kwargs):
        """."""
        super().__init__(*args, **kwargs)
        self.address.put(address)

        host, port = address.split(":")
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((host, int(port)))

        # from SPEC
        # dg645_config
        # dg645_init

        # self.sock_put(f"LAMP 1, {DG645_AMP[1]:0.2f}\n")
        # ...

        # sock_put(DG645_ADDR, sprintf("LAMP 1, %0.2f\n", DG645_AMP[1]))
        # sock_put(DG645_ADDR, sprintf("LAMP 2, %0.2f\n", DG645_AMP[2]))
        # sock_put(DG645_ADDR, sprintf("LAMP 3, %0.2f\n", DG645_AMP[3]))
        # sock_put(DG645_ADDR, sprintf("LAMP 4, %0.2f\n", DG645_AMP[4]))
        # dg645_dspamp

    # TODO: apply ophyd's get/put/set methods

    # https://certif.com/spec_help/sockets.html
    # sock_io  deprecated
    # sock_par  refactor with socket package case-by-case
    def sock_get(self) -> str:
        """Retrieve text from socket buffer up to self.buffer_size."""
        return self._socket.recv(self.buffer_size).decode("UTF-8")

    def sock_put(self, command: str, count: int = 0):
        """Send command to socket."""
        self._socket.send(bytes(command, "UTF-8"))

    def sock_put_get(self, command: str, count: int = 0) -> str:
        """Send command to socket, return response."""
        self.sock_put(command)
        return self.sock_get()

    @property
    def dg645_status(self) -> dict[str, str]:
        """Status of the DG645."""
        return {
            "Serial Poll STATUS": self.sock_put_get("*STB?\n").strip(),
            "Standard Event STATUS": self.sock_put_get("*ESR?\n").strip(),
            "Instrument STATUS": self.sock_put_get("INSR?\n").strip(),
        }
