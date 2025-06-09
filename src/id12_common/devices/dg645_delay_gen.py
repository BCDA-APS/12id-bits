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
from ophyd import DeviceStatus
from ophyd import Signal
from ophyd.signal import AttributeSignal

logger = logging.getLogger(__name__)

DG645_OUTPUT_MAP = {
    # DG645 front-panel BNC connectors.
    #
    # timing pulses
    "TO": {"instrument": "Base", "amplitude": 2.5},
    #
    # output pulses
    "AB": {"instrument": "Shutter", "amplitude": 4.0},
    "CD": {"instrument": "Detector", "amplitude": 3.0},
    "EF": {"instrument": "Struck_ADV", "amplitude": 2.5},
    "GH": {"instrument": "Struck_INH", "amplitude": 4.5},
}
DG645_CH: list[str] = "T0 T1 A B C D E F G H".split()
DG645_DEFAULT_BUFFER_SIZE: int = 1024  # assuming short communications
DG645_DEFAULT_HOST: str = "localhost"
DG645_DEFAULT_PORT: int = 5025
DG645_DEFAULT_OUTPUT_TERMINATOR: str = "\n"
DG645_DEFAULT_TIMEOUT = 2.0  # seconds
DG645_AMPLITUDE_ABS_MAX = 5.0
DG645_AMPLITUDE_ABS_MIN = 0.5
DG645_BURST_MAX = 25.0  # TODO: ?or? 2000 - 10ns
DG645_BURST_MIN = 100.0e-9
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
DG645_AMP = [v["amplitude"] for v in DG645_OUTPUT_MAP.values()]


class AttributeSignalRO(AttributeSignal):
    """Read-only AttributeSignal."""

    def __init__(self, *args, enum_strs: list[str] = None, **kwargs):
        """."""
        kwargs["write_access"] = False
        super().__init__(*args, **kwargs)


class AttributeSignalEnum(AttributeSignal):
    """AttributeSignal with enum_strs support (writeable)."""

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

    def send_receive(
        self,
        command: str,
        count: int = 0,
        delay_s: float = 0,
    ) -> str:
        """Send command to socket, return response."""
        self.send(command)
        if delay_s > 0:
            time.sleep(delay_s)
        return self.receive()


class SocketDG645DelayGen(Device):
    """
    SRS DG645 ophyd device with socket communications.

    PARAMETERS

    host *str* :
        Network host or IPv4 number string.
    port *int* :
        Network port of the DG645.  Default: 5025.
    trigger_source *str* | None :
        Trigger source text (or None to accept the current DG645 setting).

    .. rubric:: User-facing Support methods
    .. autosummary::

        ~burst_init
        ~burst_set
        ~check_error
        ~last_error_brief
        ~last_error_full
        ~set_defaults
        ~set_delay_AB
        ~set_delay_CD
        ~set_delay_EF
        ~set_delay_GH
        ~set_delay_T0

    EXAMPLE::

        >>> dg645 = SocketDG645DelayGen(host="localhost", name="dg645")
        >>> dg645.identify.get()
        burst_init
        >>> dg645.burst_init()
        >>> dg645.burst_mode_enable.get()
        True
    """

    amplitudeT0 = Component(AttributeSignal, attr="_amplitude0", kind="normal")
    amplitudeAB = Component(AttributeSignal, attr="_amplitude1", kind="normal")
    amplitudeCD = Component(AttributeSignal, attr="_amplitude2", kind="normal")
    amplitudeEF = Component(AttributeSignal, attr="_amplitude3", kind="normal")
    amplitudeGH = Component(AttributeSignal, attr="_amplitude4", kind="normal")

    polarityT0 = Component(AttributeSignal, attr="_polarity0", kind="normal")
    polarityAB = Component(AttributeSignal, attr="_polarity1", kind="normal")
    polarityCD = Component(AttributeSignal, attr="_polarity2", kind="normal")
    polarityEF = Component(AttributeSignal, attr="_polarity3", kind="normal")
    polarityGH = Component(AttributeSignal, attr="_polarity4", kind="normal")

    # TODO: delay, duration, basis channel: refactor?
    # TODO: dg645_set instr delay duration
    # How to set these terms?  Not ideal as an ophyd.Signal
    # since two parameters are specified.  Need local cache.
    delayT0 = Component(AttributeSignalRO, attr="_delay0", kind="normal")
    delayT1 = Component(AttributeSignalRO, attr="_delay1", kind="normal")
    delayA = Component(AttributeSignalRO, attr="_delay2", kind="normal")
    delayB = Component(AttributeSignalRO, attr="_delay3", kind="normal")
    delayC = Component(AttributeSignalRO, attr="_delay4", kind="normal")
    delayD = Component(AttributeSignalRO, attr="_delay5", kind="normal")
    delayE = Component(AttributeSignalRO, attr="_delay6", kind="normal")
    delayF = Component(AttributeSignalRO, attr="_delay7", kind="normal")
    delayG = Component(AttributeSignalRO, attr="_delay8", kind="normal")
    delayH = Component(AttributeSignalRO, attr="_delay9", kind="normal")

    host = Component(Signal, value=DG645_DEFAULT_HOST, kind="config")
    port = Component(Signal, value=DG645_DEFAULT_PORT, kind="config")
    burst_maxtime_limit = Component(Signal, value=41, kind="config")
    burst_count = Component(AttributeSignal, attr="_burst_count", kind="config")
    burst_delay = Component(AttributeSignal, attr="_burst_delay", kind="config")
    burst_mode_enable = Component(AttributeSignal, attr="_burst_mode", kind="config")
    burst_period = Component(AttributeSignal, attr="_burst_period", kind="config")
    burst_T0_config = Component(AttributeSignal, attr="_burst_T0_config", kind="config")
    delaytextT0 = Component(AttributeSignalRO, attr="_delaytext0", kind="config")
    delaytextT1 = Component(AttributeSignalRO, attr="_delaytext1", kind="config")
    delaytextA = Component(AttributeSignalRO, attr="_delaytext2", kind="config")
    delaytextB = Component(AttributeSignalRO, attr="_delaytext3", kind="config")
    delaytextC = Component(AttributeSignalRO, attr="_delaytext4", kind="config")
    delaytextD = Component(AttributeSignalRO, attr="_delaytext5", kind="config")
    delaytextE = Component(AttributeSignalRO, attr="_delaytext6", kind="config")
    delaytextF = Component(AttributeSignalRO, attr="_delaytext7", kind="config")
    delaytextG = Component(AttributeSignalRO, attr="_delaytext8", kind="config")
    delaytextH = Component(AttributeSignalRO, attr="_delaytext9", kind="config")
    last_error_code = Component(
        AttributeSignalRO,
        attr="_last_error_code",
        kind="config",
    )
    identify = Component(AttributeSignalRO, attr="_identify", kind="config")
    instrument_status = Component(
        AttributeSignalRO, attr="_instrument_status", kind="config"
    )
    serial_poll_status = Component(
        AttributeSignalRO, attr="_serial_poll_status", kind="config"
    )
    standard_event_status = Component(
        AttributeSignalRO, attr="_standard_event_status", kind="config"
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
        host: str = DG645_DEFAULT_HOST,
        port: int = DG645_DEFAULT_PORT,
        trigger_source: str = None,
        **kwargs,
    ):
        """
        Constructor

        PARAMETERS

        host *str* :
            Network host or IPv4 number string.
        port *int* :
            Network port of the DG645.  Default: 5025.
        trigger_source *str* | None :
            Trigger source text (or None to accept the current DG645 setting).
        """
        self._socket = Socket(host=host, port=int(port))
        self._last_error_code = -1  # Unknown, at the start.

        super().__init__(*args, **kwargs)

        self.host.put(host)
        self.port.put(port)
        if trigger_source is not None:
            self.trigger_source.put(trigger_source)

    def trigger(self) -> DeviceStatus:
        """Trigger the DG645 and return the status object."""
        status = DeviceStatus(self)
        self._initiate_trigger()
        status.set_finished()
        return status

    #################
    # User-facing Support methods

    def burst_init(self) -> None:
        """Initialize burst parameters."""
        self.burst_mode_enable.put(True)
        time.sleep(0.01)
        self.burst_T0_config.put(True)
        time.sleep(0.01)
        self.burst_delay.put(0)
        time.sleep(0.01)

    def burst_set(self, cycles: int, period: float, delay: float) -> None:
        """Set burst parameters."""
        self.burst_count.put(cycles)
        time.sleep(0.01)
        self.burst_period.put(period)
        time.sleep(0.01)
        self.burst_delay.put(delay)
        time.sleep(0.01)

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

    def set_defaults(self) -> None:
        """(dg645_init) Set default amplitudes for all DG645 output channels."""
        self.amplitude1.put(DG645_AMP[1])
        self.amplitude2.put(DG645_AMP[2])
        self.amplitude3.put(DG645_AMP[3])
        self.amplitude4.put(DG645_AMP[4])

    def set_delay_T0(self, delay: float) -> None:
        """(dg645set_1cycle) Set delay for T0 output."""
        # TODO: refactor to ophyd
        self._set_channel_delay(1, 0, delay)

    def set_delay_AB(self, delay: float, duration: float) -> None:
        """(dg645set_AB) Set delays for AB output."""
        # TODO: refactor to ophyd
        ch = 2
        self._set_channel_delay(ch, 0, delay)
        self._set_channel_delay(ch + 1, ch, duration)

    def set_delay_CD(self, delay: float, duration: float) -> None:
        """(dg645set_CD) Set delays for CD output."""
        # TODO: refactor to ophyd
        ch = 4
        self._set_channel_delay(ch, 0, delay)
        self._set_channel_delay(ch + 1, ch, duration)

    def set_delay_EF(self, delay: float, duration: float) -> None:
        """(dg645set_EF) Set delays for EF output."""
        # TODO: refactor to ophyd
        ch = 6
        self._set_channel_delay(ch, 0, delay)
        self._set_channel_delay(ch + 1, ch, duration)

    def set_delay_GH(self, delay: float, duration: float) -> None:
        """(dg645set_GH) Set delays for GH output."""
        # TODO: refactor to ophyd
        ch = 8
        self._set_channel_delay(ch, 0, delay)
        self._set_channel_delay(ch + 1, ch, duration)

    #################
    # Internal Support methods

    def _request_last_error_code(self) -> int:
        """(internal) Request & cache the last DG645 error code."""
        self._last_error_code = int(self._socket.send_receive("LERR?"))
        return self._last_error_code

    def _get_channel_delay(self, channel: int | str) -> tuple[int, float]:
        """(internal) Get DG645 basis & delay for 'channel'."""
        ch = self._validate_enum(channel, "channel", DG645_CH)
        basis, duration = self._socket.send_receive(f"DLAY? {ch}").split(",")
        return int(basis), float(duration)

    def _get_channel_delay_text(self, channel: int | str) -> str:
        """(internal) Get DG645 basis & delay for 'channel' as text."""
        ch = self._validate_enum(channel, "channel", DG645_CH)
        basis, duration = self._socket.send_receive(f"DLAY? {ch}").split(",")
        basis = int(basis)
        duration = float(duration)

        if basis == 0:
            basis = ch
        text = (
            f"Channel {ch} ({DG645_CH[ch]!r}) delay set to"
            f" Channel {basis} ({DG645_CH[basis]!r})"
            f" plus {duration:e} seconds"
        )
        return text

    def _initiate_trigger(self) -> None:
        """(internal) Initiate DG645 (internal) or arm (external) trigger."""
        self._socket.send("*TRG")

    def _set_channel_delay(self, channel: int | str, basis: int, delay: float) -> None:
        """(internal) (dg645_dlay) Set DG645 'delay' for 'channel'."""
        ch = self._validate_enum(channel, "channel", DG645_CH)
        self._socket.send(f"DLAY {ch},{basis},{delay}")

    def _get_level_amplitude(self, channel: int | str) -> float:
        """(internal) Get DG645 level amplitude for output 'channel'."""
        ch = self._validate_enum(channel, "output channel", list(DG645_OUTPUT_MAP))
        return float(self._socket.send_receive(f"LAMP? {ch}"))

    def _set_level_amplitude(self, channel: int | str, amplitude: float) -> None:
        """(internal) Set DG645 level 'amplitude' for output 'channel'."""
        ch = self._validate_enum(channel, "output channel", list(DG645_OUTPUT_MAP))
        if not (DG645_AMPLITUDE_ABS_MIN <= abs(amplitude) <= DG645_AMPLITUDE_ABS_MAX):
            raise ValueError(
                f"Received {amplitude=:%f} for {channel=}."
                f"  Must be in range {DG645_AMPLITUDE_ABS_MIN}"
                f" <= |amplitude| <="
                f"  {DG645_AMPLITUDE_ABS_MAX}"
            )
        self._socket.send(f"LAMP {ch},{amplitude:0.2f}")

    def _get_level_polarity(self, channel: int | str) -> int:
        """(internal) Get DG645 level polarity for output 'channel'."""
        ch = self._validate_enum(channel, "output channel", list(DG645_OUTPUT_MAP))
        return int(self._socket.send_receive(f"LPOL? {ch}"))

    def _set_level_polarity(self, channel: int | str, polarity: float) -> None:
        """(internal) Set DG645 level 'polarity' for output 'channel'."""
        ch = self._validate_enum(channel, "output channel", list(DG645_OUTPUT_MAP))
        if polarity not in (0, 1):
            raise ValueError(
                f"Received {polarity=} for {channel=}.  Must be either 0 or 1."
            )
        self._socket.send(f"LPOL {ch},{polarity}")

    def _validate_enum(
        self,
        value: str | int,
        label: str,
        choices: list[str],
        only_str: bool = False,
    ) -> str | int:
        """(internal) Validate 'value' from 'choices', return final value."""
        vv = value
        if isinstance(vv, str):
            if value not in choices:
                raise KeyError(f"Unknown {label}={vv!r}.  Expect one of {choices!r}.")
        if only_str:
            if not isinstance(vv, str):
                raise TypeError(f"Must be text.  Received {label}={vv!r}")
        else:
            if isinstance(vv, str):
                vv = choices.index(vv)
            hi = len(choices) - 1
            if not (0 <= vv <= hi):
                raise KeyError(f"Unknown {label}={vv}.  Must be in range 0..{hi}.")
        return vv

    #################
    # Property methods (used with AttributeSignal Components)

    @property
    def _amplitude0(self) -> float:
        """(internal) DG645 channel 0 amplitude."""
        return self._get_level_amplitude(0)

    @_amplitude0.setter
    def _amplitude0(self, value: float) -> None:
        """(internal) Set DG645 channel 0 amplitude."""
        self._set_level_amplitude(0, value)

    @property
    def _amplitude1(self) -> float:
        """(internal) DG645 channel 1 amplitude."""
        return self._get_level_amplitude(1)

    @_amplitude1.setter
    def _amplitude1(self, value: float) -> None:
        """(internal) Set DG645 channel 1 amplitude."""
        self._set_level_amplitude(1, value)

    @property
    def _amplitude2(self) -> float:
        """(internal) DG645 channel 2 amplitude."""
        return self._get_level_amplitude(2)

    @_amplitude2.setter
    def _amplitude2(self, value: float) -> None:
        """(internal) Set DG645 channel 2 amplitude."""
        self._set_level_amplitude(2, value)

    @property
    def _amplitude3(self) -> float:
        """(internal) DG645 channel 3 amplitude."""
        return self._get_level_amplitude(3)

    @_amplitude3.setter
    def _amplitude3(self, value: float) -> None:
        """(internal) Set DG645 channel 3 amplitude."""
        self._set_level_amplitude(3, value)

    @property
    def _amplitude4(self) -> float:
        """(internal) DG645 channel 4 amplitude."""
        return self._get_level_amplitude(4)

    @_amplitude4.setter
    def _amplitude4(self, value: float) -> None:
        """(internal) Set DG645 channel 4 amplitude."""
        self._set_level_amplitude(4, value)

    @property
    def _burst_count(self) -> int:
        """(internal) DG645 burst count."""
        return int(self._socket.send_receive("BURC?"))

    @_burst_count.setter
    def _burst_count(self, value: int) -> None:
        """(internal) Set DG645 burst count."""
        hi = self.burst_maxtime_limit.get()
        if not (0 <= value <= hi):
            raise ValueError(
                f"Burst count value must be in range 0 .. {hi}." f"  Received {value=}."
            )
        self._socket.send(f"BURC {value}")

    @property
    def _burst_delay(self) -> float:
        """(internal) DG645 burst delay."""
        return float(self._socket.send_receive("BURD?"))

    @_burst_delay.setter
    def _burst_delay(self, value: float) -> None:
        """(internal) Set DG645 burst delay."""
        self._socket.send(f"BURD {value:e}")

    @property
    def _burst_mode(self) -> bool:
        """(internal) DG645 burst mode."""
        return self._socket.send_receive("BURM?") == "1"

    @_burst_mode.setter
    def _burst_mode(self, value: bool) -> None:
        """(internal) Set DG645 burst mode."""
        vv = 1 if value else 0
        self._socket.send(f"BURM {vv}")

    @property
    def _burst_period(self) -> float:
        """(internal) DG645 burst period."""
        return float(self._socket.send_receive("BURP?"))

    @_burst_period.setter
    def _burst_period(self, value: float) -> None:
        """(internal) Set DG645 burst period."""
        if not (DG645_BURST_MIN <= value <= DG645_BURST_MAX):
            raise ValueError(
                "Burst period value must be in range"
                f" {DG645_BURST_MIN} .. {DG645_BURST_MAX}"
                # .
                f"  Received {value=}."
            )
        self._socket.send(f"BURP {value:e}")

    @property
    def _burst_T0_config(self) -> int:
        """(internal) DG645 burst T0 configuration."""
        return int(self._socket.send_receive("BURT?"))

    @_burst_T0_config.setter
    def _burst_T0_config(self, value: int) -> None:
        """(internal) Set DG645 burst period."""
        if value not in (0, 1):
            raise ValueError(
                "Burst T0 configuration value must be 0 or 1."
                # .
            )
        self._socket.send(f"BURT {value}")

    @property
    def _delay0(self) -> float:
        """(internal) DG645 channel 0 delay_time."""
        return self._get_channel_delay(0)[1]

    @property
    def _delay1(self) -> float:
        """(internal) DG645 channel 1 delay_time."""
        return self._get_channel_delay(1)[1]

    @property
    def _delay2(self) -> float:
        """(internal) DG645 channel 2 delay_time."""
        return self._get_channel_delay(2)[1]

    @property
    def _delay3(self) -> float:
        """(internal) DG645 channel 3 delay_time."""
        return self._get_channel_delay(3)[1]

    @property
    def _delay4(self) -> float:
        """(internal) DG645 channel 4 delay_time."""
        return self._get_channel_delay(4)[1]

    @property
    def _delay5(self) -> float:
        """(internal) DG645 channel 5 delay_time."""
        return self._get_channel_delay(5)[1]

    @property
    def _delay6(self) -> float:
        """(internal) DG645 channel 6 delay_time."""
        return self._get_channel_delay(6)[1]

    @property
    def _delay7(self) -> float:
        """(internal) DG645 channel 7 delay_time."""
        return self._get_channel_delay(7)[1]

    @property
    def _delay8(self) -> float:
        """(internal) DG645 channel 8 delay_time."""
        return self._get_channel_delay(8)[1]

    @property
    def _delay9(self) -> float:
        """(internal) DG645 channel 9 delay_time."""
        return self._get_channel_delay(9)[1]

    @property
    def _delaytext0(self) -> float:
        """(internal) DG645 channel 0 delay text."""
        return self._get_channel_delay_text(0)

    @property
    def _delaytext1(self) -> float:
        """(internal) DG645 channel 1 delay text."""
        return self._get_channel_delay_text(1)

    @property
    def _delaytext2(self) -> float:
        """(internal) DG645 channel 2 delay text."""
        return self._get_channel_delay_text(2)

    @property
    def _delaytext3(self) -> float:
        """(internal) DG645 channel 3 delay text."""
        return self._get_channel_delay_text(3)

    @property
    def _delaytext4(self) -> float:
        """(internal) DG645 channel 4 delay text."""
        return self._get_channel_delay_text(4)

    @property
    def _delaytext5(self) -> float:
        """(internal) DG645 channel 5 delay text."""
        return self._get_channel_delay_text(5)

    @property
    def _delaytext6(self) -> float:
        """(internal) DG645 channel 6 delay text."""
        return self._get_channel_delay_text(6)

    @property
    def _delaytext7(self) -> float:
        """(internal) DG645 channel 7 delay text."""
        return self._get_channel_delay_text(7)

    @property
    def _delaytext8(self) -> float:
        """(internal) DG645 channel 8 delay text."""
        return self._get_channel_delay_text(8)

    @property
    def _delaytext9(self) -> float:
        """(internal) DG645 channel 9 delay text."""
        return self._get_channel_delay_text(9)

    @property
    def _identify(self) -> str:
        """(internal) DG645 Model (text)."""
        return self._socket.send_receive("*IDN?")

    @property
    def _instrument_status(self) -> str:
        """(internal) DG645 Instrument STATUS (text)."""
        return self._socket.send_receive("INSR?")

    @property
    def _polarity0(self) -> int:
        """(internal) DG645 channel 0 polarity."""
        return self._get_level_polarity(0)

    @_polarity0.setter
    def _polarity0(self, value: int) -> None:
        """(internal) Set DG645 channel 0 polarity."""
        self._set_level_polarity(0, value)

    @property
    def _polarity1(self) -> int:
        """(internal) DG645 channel 1 polarity."""
        return self._get_level_polarity(1)

    @_polarity1.setter
    def _polarity1(self, value: int) -> None:
        """(internal) Set DG645 channel 1 polarity."""
        self._set_level_polarity(1, value)

    @property
    def _polarity2(self) -> int:
        """(internal) DG645 channel 2 polarity."""
        return self._get_level_polarity(2)

    @_polarity2.setter
    def _polarity2(self, value: int) -> None:
        """(internal) Set DG645 channel 2 polarity."""
        self._set_level_polarity(2, value)

    @property
    def _polarity3(self) -> int:
        """(internal) DG645 channel 3 polarity."""
        return self._get_level_polarity(3)

    @_polarity3.setter
    def _polarity(self, value: int) -> None:
        """(internal) Set DG645 channel 3 polarity."""
        self._set_level_polarity(3, value)

    @property
    def _polarity4(self) -> int:
        """(internal) DG645 channel 4 polarity."""
        return self._get_level_polarity(4)

    @_polarity.setter
    def _polarity4(self, value: int) -> None:
        """(internal) Set DG645 channel 4 polarity."""
        self._set_level_polarity(4, value)

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
