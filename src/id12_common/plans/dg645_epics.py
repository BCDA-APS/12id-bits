"""
Bluesky plans & plan stubs for DG645 Delay Generator.

Plan stubs here patterned after 12ID's SPEC macros for DG645.

.. autosummary::

    ~dg645_burst_init
    ~dg645_burst_set
    ~dg645_check_error
    ~dg645_dlay
    ~dg645_set
    ~dg645_struck
    ~dg645_trig
    ~dg645set_1cycle
    ~dg645set_AB
    ~dg645set_CD
    ~dg645set_EF
    ~dg645set_GH
    ~dg645_dsp
    ~dg645_dspamp
"""

import logging

from apstools.devices.delay import DG645Channel, DG645Output
from bluesky import plan_stubs as bps
from bluesky.utils import MsgGenerator
from bluesky.utils import plan
import pyRestTable

# from apstools.devices.delay import DG645Delay
from ..devices import DG645Delay

logger = logging.getLogger(__name__)


@plan
def dg645_burst_init(dg645: DG645Delay) -> MsgGenerator:
    """Initialize burst mode parameters.

    EXAMPLE::

        yield from burst_init(dg645_idc)
    """
    yield from bps.mv(dg645.burst_mode, 1)
    yield from bps.sleep(0.01)
    yield from bps.mv(dg645.burst_T0, 1)
    yield from bps.sleep(0.01)
    yield from bps.mv(dg645.burst_delay, 0)
    yield from bps.sleep(0.01)


@plan
def dg645_burst_set(
    dg645: DG645Delay,
    cycles: int,
    period: float,
    delay: float,
) -> MsgGenerator:
    """Set burst parameters.

    EXAMPLE::

        yield from burst_set(dg645_idc, 1, 1e-5, 0)
    """
    yield from bps.mv(dg645.burst_count, cycles)
    yield from bps.sleep(0.01)
    yield from bps.mv(dg645.burst_period, period)
    yield from bps.sleep(0.01)
    yield from bps.mv(dg645.burst_delay, delay)
    yield from bps.sleep(0.01)


@plan
def dg645_check_error(dg645: DG645Delay, step: str) -> MsgGenerator:
    """Log any DG645 error messages."""
    status = dg645.status.get()
    if status not in (0, ""):
        logger.warning("DG645 Error in step %r: %s", step, status)


@plan
def dg645_dlay(
    dg645: DG645Delay,
    ch: int | str,
    ref: int | str,
    delay: float,
) -> MsgGenerator:
    """dg645_dlay channel reference delay"""
    channels = "T0 T1 A B C D E F G H".split()
    _ch, _ref = ch, ref  # copy the inputs, don't change them
    if isinstance(_ch, str):
        _ch = channels.index(_ch)
    if isinstance(_ref, str):
        _ref = channels.index(_ref)
    ch_name = f"channel_{channels[_ch]}"
    channel = getattr(dg645, ch_name)

    # Two atomic operations.
    yield from bps.mv(channel.reference, _ref)
    yield from bps.mv(channel.delay, delay)

    logger.debug(
        "Channel %i(%s) delay set to Channel %i(%s) plus %e seconds",
        _ch,
        channels[_ch],
        _ref,
        channels[_ref],
        channel.delay.get(),
    )


def dg645_dsp(dg645: DG645Delay) -> None:
    """
    (not a plan) dg645_dsp: print a table of channel delay settings.
    """
    table = pyRestTable.Table()
    table.labels = "channel reference delay,s".split()
    for c_name in dg645.component_names:
        cpt = getattr(dg645, c_name)
        if isinstance(cpt, DG645Channel):
            row = [c_name, cpt.reference.get(), cpt.delay.get()]
            table.addRow(row)
    print(table)


def dg645_dspamp(dg645: DG645Delay) -> None:
    """
    (not a plan) dg645_dsp: print a table of amplitude & polarity settings.
    """
    table = pyRestTable.Table()
    table.labels = "instrument amplitude polarity offset".split()
    for c_name in dg645.component_names:
        cpt = getattr(dg645, c_name)
        if isinstance(cpt, DG645Output):
            row = [c_name, cpt.amplitude.get(), cpt.polarity.get(), cpt.offset.get()]
            table.addRow(row)
    print(table)


@plan
def dg645_set(
    dg645: DG645Delay,
    instr: int | str,
    delay: float,
    duration: float,
) -> MsgGenerator:
    """
    dg645_set instr delay duration
    """
    if isinstance(instr, int):
        instr = "T0 AB CD EF GH".split()[instr]
    ch1, ch2, ref = {
        "T0": [dg645.channel_T0, dg645.channel_T1, 0],
        "AB": [dg645.channel_A, dg645.channel_B, 2],
        "CD": [dg645.channel_C, dg645.channel_D, 4],
        "EF": [dg645.channel_E, dg645.channel_F, 6],
        "GH": [dg645.channel_G, dg645.channel_H, 8],
    }[instr]
    step = "dg645_set"
    yield from _set_2chan_delay(ch1, 0, delay, ch2, ref, duration, step)
    dg645_dsp()


@plan
def _set_2chan_delay(
    ch1: DG645Channel,
    ref1: int,
    delay1: float,
    ch2: DG645Channel,
    ref2: int,
    delay2: float,
    step: str,
) -> MsgGenerator:
    """(internal) Set Reference and Delay for two channels."""
    # fmt: off
    # Two atomic operations.
    yield from bps.mv(
        ch1.reference, ref1,
        ch2.reference, ref2,
    )
    yield from bps.mv(
        ch1.delay, delay1,
        ch2.delay, delay2,
    )
    # fmt: on
    yield from dg645_check_error(step)


@plan
def dg645set_AB(
    dg645: DG645Delay,
    delay1: float,
    delay2: float,
    step: str,
) -> MsgGenerator:
    """Set delays for channels A & B."""
    # fmt: off
    yield from _set_2chan_delay(
        dg645.channel_A, 0, delay1,
        dg645.channel_B, 2, delay2,
        step,
    )
    # fmt: on


@plan
def dg645set_CD(
    dg645: DG645Delay,
    delay1: float,
    delay2: float,
    step: str,
) -> MsgGenerator:
    """Set delays for channels C & D."""
    # fmt: off
    yield from _set_2chan_delay(
        dg645.channel_C, 0, delay1,
        dg645.channel_D, 4, delay2,
        step,
    )
    # fmt: on


@plan
def dg645set_EF(
    dg645: DG645Delay,
    delay1: float,
    delay2: float,
    step: str,
) -> MsgGenerator:
    """Set delays for channels E & F."""
    # fmt: off
    yield from _set_2chan_delay(
        dg645.channel_E, 0, delay1,
        dg645.channel_F, 6, delay2,
        step,
    )
    # fmt: on


@plan
def dg645set_GH(
    dg645: DG645Delay,
    delay1: float,
    delay2: float,
    step: str,
) -> MsgGenerator:
    """Set delays for channels G & H."""
    # fmt: off
    yield from _set_2chan_delay(
        dg645.channel_G, 0, delay1,
        dg645.channel_H, 8, delay2,
        step,
    )
    # fmt: on


@plan
def dg645set_1cycle(
    dg645: DG645Delay,
    delay: float,
    step: str,
) -> MsgGenerator:
    """Set delay for only 1 cycle."""
    # Two atomic operations.
    yield from bps.mv(dg645.channel_T1.reference, 0)
    yield from bps.mv(dg645.channel_T1.delay, delay)
    yield from dg645_check_error(step)


@plan
def dg645_struck(dg645, struck, pilatus) -> MsgGenerator:
    """Setup the dg645 to trigger the Pilatus & Struck."""
    shutter_deadtime = 0  # TODO: Pilatus shutter deadtime

    checking = dg645.status_checking.get()
    if checking == 0:  # enable, if not already
        yield from bps.mv(dg645.status_checking, 1)

    yield from dg645set_AB(dg645, 0, "AB - shutter")
    yield from dg645set_CD(dg645, shutter_deadtime, "CD - Pilatus shutter deadtime")
    yield from dg645set_EF(dg645, 1e-3, "EF - Struck")
    yield from dg645set_GH(dg645, 0, "GH - Struck Inhibitor")

    yield from bps.mv(dg645.burst_mode, 0)  # disable
    yield from dg645_trig(dg645)
    yield from dg645_check_error("trig")

    if checking == 0:  # restore, if necessary
        yield from bps.mv(dg645.status_checking, checking)


@plan
def dg645_trig(dg645) -> MsgGenerator:
    """Initiate or activate the DG645 to trigger."""
    yield from bps.abs_set(dg645.trigger_arm, 1)
