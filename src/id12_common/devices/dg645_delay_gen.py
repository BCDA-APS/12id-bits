"""
Non-EPICS support for the DG645 delay generator

Communications via ethernet to reduce overhead (status checking).

SPEC support here:
  /home/beams15/S12STAFF/spec_macros/std_macros/DET_common.mac
  /home/beams15/S12STAFF/spec_macros/std_macros/DG645_lee.mac
  https://github.com/APS-12IDB-GISAXS/spec_macros
  https://github.com/BCDA-APS/12id-bits

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
from ophyd.signal import AttributeSignal

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


class AttributeSignalEnum(AttributeSignal):
    """AttributeSignal with enum_strs support."""

    def __init__(self, *args, enum_strs: list[str] = None, **kwargs):
        """."""
        super().__init__(*args, **kwargs)
        self._metadata.update(enum_strs=enum_strs)


class Socket:
    """Manage socket communications."""

    # https://certif.com/spec_help/sockets.html
    # sock_io  deprecated
    # sock_par  refactor with socket package case-by-case

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5025,
        buffer_size: int = 1024,  # assuming short communications
    ):
        """."""
        self.host = host
        self.port = port
        self.buffer_size = buffer_size

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((host, port))

    def receive(self) -> str:
        """Retrieve text from socket buffer up to self.buffer_size."""
        return self._socket.recv(self.buffer_size).decode("UTF-8")

    def send(self, command: str, count: int = 0):
        """Send command to socket."""
        self._socket.send(bytes(command, "UTF-8"))

    def send_receive(self, command: str, count: int = 0) -> str:
        """Send command to socket, return response."""
        self.send(command)
        return self.receive()


class SocketDG645DelayGen(Device):
    """DG645 with socket communications"""

    # TODO:

    address = Component(Signal, value="", kind="config")
    burst_maxtime_limit = Component(Signal, value=41, kind="config")
    trigger_source = Component(
        AttributeSignalEnum,
        attr="_trigger_source",
        write_access=True,
        kind="config",
        enum_strs=DG645_TSRC,
    )

    def __init__(self, *args, address: str = "localhost:5025", **kwargs):
        """."""
        host, port = address.split(":")
        self._socket = Socket(host=host, port=int(port))

        super().__init__(*args, **kwargs)
        self.address.put(address)

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

    @property
    def _trigger_source(self) -> str:
        """Return the DG645 trigger source (text)."""
        # TODO: implement a cache to avoid unnecessary comms.
        idx = int(self._socket.send_receive("TSRC?\r").strip())
        return self.enum_strs[idx]  # as string

    @_trigger_source.setter
    def _trigger_source(self, value: int | str) -> str:
        """Set the DG645 trigger source (int or text)."""
        if isinstance(value, str):
            if value not in self.enum_strs:
                raise ValueError(
                    f"Unknown trigger source {value=!r}."
                    # .
                    f" Must be one of: {self.enum_strs}"
                )
            value = self.enum_strs.index(value)

        elif isinstance(value, int):
            if value < 0 or value >= len(self.enum_strs):
                raise ValueError(
                    "Trigger source value must be in range 0 .."
                    # .
                    f" {len(self.enum_strs)}  Received {value=}"
                )
        else:
            raise TypeError(f"Unexpected {value=!r}")

        if value >= 0:
            self._socket.send(f"TSRC {value}\r")  # DG645 uses int value

    # TODO: apply ophyd's get/put/set methods

    ######################################
    # SPEC-inspired commands

    @property
    def dg645_identity(self) -> dict[str, str]:
        """DG645 Model."""
        return {
            "DG645 model": self._socket.send_receive("*IDN?\n").strip(),
        }

    @property
    def dg645_status(self) -> dict[str, str]:
        """Status of the DG645."""
        return {
            "Serial Poll STATUS": self._socket.send_receive("*STB?\n").strip(),
            "Standard Event STATUS": self._socket.send_receive("*ESR?\n").strip(),
            "Instrument STATUS": self._socket.send_receive("INSR?\n").strip(),
        }

    def dg645_tsrc(self, value: int | str) -> str:
        """Set trigger source."""
        if isinstance(value, str):
            if value not in DG645_TSRC:
                raise ValueError(
                    f"Unknown trigger source {value=!r}."
                    # .
                    f" Must be one of: {DG645_TSRC}"
                )
            value = DG645_TSRC.index(value)

        elif isinstance(value, int):
            if value >= len(DG645_TSRC):
                raise ValueError(
                    "Trigger source value must be in range 0 .."
                    # .
                    f" {len(DG645_TSRC)}  Received {value=}"
                )
        else:
            raise TypeError(f"Unexpected {value=!r}")

        if value >= 0:
            self._socket.send(f"TSRC {value}\r")

        idx = int(self._socket.send_receive("TSRC?\r").strip())
        return DG645_TSRC[idx]  # as string
