"""
Non-EPICS support for the DG645 delay generator

Communications via ethernet to reduce overhead (status checking).

SPEC support here:
  /home/beams15/S12STAFF/spec_macros/std_macros/DET_common.mac
  /home/beams15/S12STAFF/spec_macros/std_macros/DG645_lee.mac
  https://github.com/APS-12IDB-GISAXS/spec_macros (out of sync with local)
  https://github.com/BCDA-APS/12id-bits

=======  ===================
station  address
=======  ===================
12idb    10.54.122.66:5025
12idc    10.54.122.104:5025
=======  ===================
"""

import logging
import socket  # https://docs.python.org/3/library/socket.html
import time

from ophyd import Component
from ophyd import Device
from ophyd import Signal
from ophyd.signal import AttributeSignal

logger = logging.getLogger(__name__)

DG645_BNC_MAP: dict[str, dict[str, int | str]] = {
    # DG645_INSTR: {DG645_AMP, DG645_OUT}
    "Base": {"amp": 2.5, "out": "T0"},
    "Shutter": {"amp": 4.0, "out": "AB"},
    "Detector": {"amp": 3.0, "out": "CD"},
    "Struck_ADV": {"amp": 2.5, "out": "EF"},
    "Struck_INH": {"amp": 4.5, "out": "GH"},
}
DG645_CH: list[str] = "T0 T1 A B C D E F G H".split()
DG645_DEFAULT_BUFFER_SIZE: int = 1024  # assuming short communications
DG645_DEFAULT_HOST: str = "localhost"
DG645_DEFAULT_PORT: int = 5025
DG645_DEFAULT_OUTPUT_TERMINATOR: str = "\n"
DG645_DEFAULT_TIMEOUT = 2.0  # seconds
DG645_TSRC = [
    "Internal",
    "External rising edges",
    "External falling edges",
    "Single shot external rising edges",
    "Single shot external falling edges",
    "Single shot",
    "Line",
]
DG645_ERROR_CODES: dict[int, list[str, str]] = {
    # code  brief  full
    -1: [  # Custom error added by this ophyd Device support.
        "Unknown",
        "DG645 last error code has not yet been requested by ophyd Device support.",
    ],
    0: ["No Error", "No more errors left in the queue."],
    10: ["Illegal Value", "A parameter was out of range."],
    11: [
        "Illegal Mode",
        "The action is illegal in the current mode. This might happen,"
        " for instance, if a single shot is requested when the trigger"
        " source is not single shot.",
    ],
    12: ["Illegal Delay", "The requested delay is out of range."],
    13: ["Illegal Link", "The requested delay linkage is illegal."],
    14: [
        "Recall Failed",
        "The recall of instrument settings from nonvolatile storage failed."
        " The instrument settings were invalid.",
    ],
    15: [
        "Not Allowed",
        "The requested action is not allowed because the instrument is locked"
        " by another interface.",
    ],
    16: ["Failed Self Test", "The DG645 self test failed."],
    17: ["Failed Auto Calibration", "The DG645 auto calibration failed."],
    30: [
        "Lost Data",
        "Data in the output buffer was lost. This occurs if the output buffer"
        " overflows, or if a communications error occurs and data in output"
        " buffer is discarded.",
    ],
    32: [
        "No Listener",
        "This is a communications error that occurs if the DG645 is addressed"
        " to talk on the GPIB bus, but there are no listeners. The DG645 discards"
        " any pending output.",
    ],
    40: [
        "Failed ROM Check",
        "The ROM checksum failed. The firmware code is likely corrupted.",
    ],
    41: [
        "Failed Offset T0 Test",
        "Self test of offset functionality for output T0 failed.",
    ],
    42: [
        "Failed Offset AB Test",
        "Self test of offset functionality for output AB failed.",
    ],
    43: [
        "Failed Offset CD Test",
        "Self test of offset functionality for output CD failed.",
    ],
    44: [
        "Failed Offset EF Test",
        "Self test of offset functionality for output EF failed.",
    ],
    45: [
        "Failed Offset GH Test",
        "Self test of offset functionality for output GH failed.",
    ],
    46: [
        "Failed Amplitude T0 Test",
        "Self test of amplitude functionality for output T0 failed.",
    ],
    47: [
        "Failed Amplitude AB Test",
        "Self test of amplitude functionality for output AB failed.",
    ],
    48: [
        "Failed Amplitude CD Test",
        "Self test of amplitude functionality for output CD failed.",
    ],
    49: [
        "Failed Amplitude EF Test",
        "Self test of amplitude functionality for output EF failed.",
    ],
    50: [
        "Failed Amplitude GH Test",
        "Self test of amplitude functionality for output GH failed.",
    ],
    51: ["Failed FPGA Communications Test", "Self test of FPGA communications failed."],
    52: ["Failed GPIB Communications Test", "Self test of GPIB communications failed."],
    53: ["Failed DDS Communications Test", "Self test of DDS communications failed."],
    54: [
        "Failed Serial EEPROM Communications Test",
        "Self test of serial EEPROM communications failed.",
    ],
    55: [
        "Failed Temperature Sensor Communications Test",
        "Self test of the temperature sensor communications failed.",
    ],
    56: ["Failed PLL Communications Test", "Self test of PLL communications failed."],
    57: [
        "Failed DAC 0 Communications Test",
        "Self test of DAC 0 communications failed.",
    ],
    58: [
        "Failed DAC 1 Communications Test",
        "Self test of DAC 1 communications failed.",
    ],
    59: [
        "Failed DAC 2 Communications Test",
        "Self test of DAC 2 communications failed.",
    ],
    60: [
        "Failed Sample and Hold Operations Test",
        "Self test of sample and hold operations failed.",
    ],
    61: ["Failed Vjitter Operations Test", "Self test of Vjitter operation failed."],
    62: [
        "Failed Channel T0 Analog Delay Test",
        "Self test of channel T0 analog delay failed.",
    ],
    63: [
        "Failed Channel T1 Analog Delay Test",
        "Self test of channel T1 analog delay failed.",
    ],
    64: [
        "Failed Channel A Analog Delay Test",
        "Self test of channel A analog delay failed.",
    ],
    65: [
        "Failed Channel B Analog Delay Test",
        "Self test of channel B analog delay failed.",
    ],
    66: [
        "Failed Channel C Analog Delay Test",
        "Self test of channel C analog delay failed.",
    ],
    67: [
        "Failed Channel D Analog Delay Test",
        "Self test of channel D analog delay failed.",
    ],
    68: [
        "Failed Channel E Analog Delay Test",
        "Self test of channel E analog delay failed.",
    ],
    69: [
        "Failed Channel F Analog Delay Test",
        "Self test of channel F analog delay failed.",
    ],
    70: [
        "Failed Channel G Analog Delay Test",
        "Self test of channel G analog delay failed.",
    ],
    71: [
        "Failed Channel H Analog Delay Test",
        "Self test of channel H analog delay failed.",
    ],
    80: [
        "Failed Sample and Hold Calibration",
        "Auto calibration of sample and hold DAC failed.",
    ],
    81: ["Failed T0 Calibration", "Auto calibration of channel T0 failed."],
    82: ["Failed T1 Calibration", "Auto calibration of channel T1 failed."],
    83: ["Failed A Calibration", "Auto calibration of channel A failed."],
    84: ["Failed B Calibration", "Auto calibration of channel B failed."],
    85: ["Failed C Calibration", "Auto calibration of channel C failed."],
    86: ["Failed D Calibration", "Auto calibration of channel D failed."],
    87: ["Failed E Calibration", "Auto calibration of channel E failed."],
    88: ["Failed F Calibration", "Auto calibration of channel F failed."],
    89: ["Failed G Calibration", "Auto calibration of channel G failed."],
    90: ["Failed H Calibration", "Auto calibration of channel H failed."],
    91: ["Failed Vjitter Calibration", "Auto calibration of Vjitter failed."],
    110: [
        "Illegal Command",
        "The command syntax used was illegal. A command is normally a"
        " sequence of four letters, or a '*' followed by three letters.",
    ],
    111: ["Undefined Command", "The specified command does not exist."],
    112: ["Illegal Query", "The specified command does not permit queries"],
    113: ["Illegal Set", "The specified command can only be queried."],
    114: ["Null Parameter", "The parser detected an empty parameter."],
    115: [
        "Extra Parameters",
        "The parser detected more parameters than allowed by the command.",
    ],
    116: [
        "Missing Parameters",
        "The parser detected missing parameters required by the command.",
    ],
    117: [
        "Parameter Overflow",
        "The buffer for storing parameter values overflowed. This probably"
        " indicates a syntax error.",
    ],
    118: [
        "Invalid Floating Point Number",
        "The parser expected a floating point number, but was unable to parse it.",
    ],
    120: [
        "Invalid Integer",
        "The parser expected an integer, but was unable to parse it.",
    ],
    121: ["Integer Overflow", "A parsed integer was too large to store correctly."],
    122: [
        "Invalid Hexadecimal",
        "The parser expected hexadecimal characters but was unable to parse them.",
    ],
    126: ["Syntax Error", "The parser detected a syntax error in the command."],
    170: [
        "Communication Error",
        "A communication error was detected. This is reported if the hardware"
        " detects a framing, or parity error in the data stream.",
    ],
    171: [
        "Over run",
        "The input buffer of the remote interface overflowed. All data in both"
        " the input and output buffers will be flushed.",
    ],
    254: [
        "Too Many Errors",
        "The error buffer is full. Subsequent errors have been dropped.",
    ],
}


class AttributeSignalRO(AttributeSignal):
    """Read-only AttributeSignal."""

    def __init__(self, *args, enum_strs: list[str] = None, **kwargs):
        """."""
        kwargs["write_access"] = False
        super().__init__(*args, **kwargs)


class AttributeSignalEnum(AttributeSignal):
    """AttributeSignal with enum_strs support."""

    def __init__(self, *args, enum_strs: list[str] = None, **kwargs):
        """."""
        super().__init__(*args, **kwargs)
        self._metadata.update(enum_strs=enum_strs)

    @property
    def enum_strs(self) -> list[str]:
        """Return the enumeration list."""
        return self._metadata["enum_strs"]


class Socket:
    """Manage socket communications."""

    # For expected features, see:
    # https://certif.com/spec_help/sockets.html
    # sock_io  deprecated
    # sock_par  refactor with socket package case-by-case

    # TODO: connected?

    def __init__(
        self,
        host: str = DG645_DEFAULT_HOST,
        port: int = DG645_DEFAULT_PORT,
        buffer_size: int = DG645_DEFAULT_BUFFER_SIZE,
        output_terminator: str = DG645_DEFAULT_OUTPUT_TERMINATOR,
        timeout: float = DG645_DEFAULT_TIMEOUT,
    ):
        """."""
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.output_terminator = output_terminator

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(timeout)
        self._socket.connect((host, port))

    def receive(self) -> str:
        """Retrieve text from socket buffer up to self.buffer_size."""
        return self._socket.recv(self.buffer_size).decode("UTF-8").strip()

    def send(self, command: str, count: int = 0):
        """Send command to socket."""
        command = f"{command.strip()}{self.output_terminator}"
        self._socket.send(bytes(command, "UTF-8"))

    def send_receive(self, command: str, count: int = 0, delay_s: float = 0,) -> str:
        """Send command to socket, return response."""
        self.send(command)
        if delay_s > 0:
            time.sleep(delay_s)
        return self.receive()


class SocketDG645DelayGen(Device):
    """
    SRS DG645 ophyd device with socket communications.

    PARAMETERS

    address *str* :
        Network host and port of the DG645, in the form of 'HOST:PORT".
        Host may be a name or a set of IPv4 numbers.  The ':' separator
        is required.
    trigger_source *str* | None :
        Trigger source text (or None to accept the current DG645 setting).

    .. rubric:: User-facing Support methods
    .. autosummary::

        ~check_error
        ~last_error_brief
        ~last_error_full
    """

    address = Component(Signal, value="", kind="config")
    burst_maxtime_limit = Component(Signal, value=41, kind="config")
    last_error_code = Component(
        AttributeSignalRO,
        attr="_last_error_code",
        kind="config",
    )
    identify = Component(AttributeSignalRO, attr="_identify", kind="config")
    instrument_status = Component(
        AttributeSignalRO,
        attr="_instrument_status",
        kind="config"
    )
    serial_poll_status = Component(
        AttributeSignalRO,
        attr="_serial_poll_status",
        kind="config"
    )
    standard_event_status = Component(
        AttributeSignalRO,
        attr="_standard_event_status",
        kind="config"
    )
    trigger_source = Component(
        AttributeSignalEnum,
        attr="_trigger_source",
        kind="config",
        enum_strs=DG645_TSRC,
    )

    def __init__(
        self,
        *args,
        address: str = f"{DG645_DEFAULT_HOST}:{DG645_DEFAULT_PORT}",
        trigger_source: str = None,
        **kwargs,
    ):
        """."""
        host, port = address.split(":")
        self._socket = Socket(host=host, port=int(port))
        self._last_error_code = -1  # Unknown, at the start.

        super().__init__(*args, **kwargs)

        self.address.put(address)
        if trigger_source is not None:
            self.trigger_source.put(trigger_source)

    #################
    # User-facing Support methods

    def check_error(self, step: str) -> None:
        """Request the last DG645 error code, log if non-zero."""
        code = self._request_last_error_code()
        if code != 0:
            logger.warning(
                "DG645 error in step %r: code=%d, brief=%r, full=%r",
                step,
                code,
                self.last_error_brief(code),
                self.last_error_full(code),
            )

    def last_error_brief(self, code: int) -> str:
        """Return the DG645 brief error message from the code."""
        return DG645_ERROR_CODES.get(code, ["unknown"])[0]

    def last_error_full(self, code: int) -> str:
        """Return the DG645 full error message from the code."""
        return DG645_ERROR_CODES.get(code, ["unknown"])[-1]

    #################
    # Internal Support methods

    def _request_last_error_code(self) -> int:
        """(internal) Request & cache the last DG645 error code."""
        self._last_error_code = int(self._socket.send_receive("LERR?"))
        return self._last_error_code

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

    #################
    # Property methods (used with AttributeSignal Components)

    @property
    def _identify(self) -> str:
        """(internal) DG645 Model (text)."""
        return self._socket.send_receive("*IDN?")

    @property
    def _instrument_status(self) -> str:
        """(internal) DG645 Instrument STATUS (text)."""
        return self._socket.send_receive("INSR?")

    @property
    def _serial_poll_status(self) -> str:
        """(internal) DG645 Serial Poll STATUS (text)."""
        return self._socket.send_receive("*STB?")

    @property
    def _standard_event_status(self) -> str:
        """(internal) DG645 Standard Event STATUS (text)."""
        return self._socket.send_receive("*ESR?")

    @property
    def _trigger_source(self) -> str:
        """(internal) Return the DG645 trigger source (text)."""
        # TODO: implement a cache to avoid unnecessary comms.
        idx = int(self._socket.send_receive("TSRC?"))
        return self.trigger_source.enum_strs[idx]  # as string

    @_trigger_source.setter
    def _trigger_source(self, value: int | str) -> str:
        """(internal) Set the DG645 trigger source (int or text)."""
        if isinstance(value, str):
            if value not in self.trigger_source.enum_strs:
                raise ValueError(
                    f"Unknown trigger source {value=!r}."
                    # .
                    f" Must be one of: {self.trigger_source.enum_strs}"
                )
            value = self.trigger_source.enum_strs.index(value)

        elif isinstance(value, int):
            if value < 0 or value >= len(self.trigger_source.enum_strs):
                raise ValueError(
                    "Trigger source value must be in range 0 .."
                    # .
                    f" {len(self.trigger_source.enum_strs)}  Received {value=}"
                )
        else:
            raise TypeError(f"Unexpected {value=!r}")

        if value >= 0:
            self._socket.send(f"TSRC {value}")  # DG645 uses int value
