class mono:
    def __init__(self, beamline='12idc'):
        if beamline == '12idc' or beamline == '12ide':
            self.mono     = PV("12ida2:E2P_driveValue.A")
            self.mono_RBV = PV("12ida2:EnCalc")
            self.th       = Motor('12ida2:m19')  # theta mono
        if beamline == '12idb':
            self.mono     = PV("12ida1:DCM:E2P_driveValue.A")
            self.mono_RBV = PV("12ida1:DCM:EnRBV")
            self.th       = Motor('12ida1:m9')  # theta mono
        self._abort = False
class energy(mono):
    def __init__(self, beamline='12idc'):
        super().__init__(beamline)
        self.beamline = beamline
        if beamline == '12idc' or beamline == '12ide':
            self.harmonics  = PV("S12ID:USID:HarmonicValueC")
            self.engset     = PV("S12ID:USID:EnergySetC.VAL")
            self.undstart   = PV("S12ID:USID:StartC.VAL")
            self.mirrorY    = PV("12ida2:table1.Y")
        if beamline == '12idb':
            self.harmonics  = PV("S12ID:DSID:HarmonicValueC")
            self.engset     = PV("S12ID:DSID:EnergySetC.VAL")
            self.undstart   = PV("S12ID:DSID:StartC.VAL")
            self.mirrorY    = None
class ptc10:
    def __init__(self, beamlinepv="12idTEMP"):
        self.pvProgTemp = epics.PV("%s:tc1:5A:rampTemp_RBV" % beamlinepv)
        self.pvsetTemp = epics.PV("%s:tc1:5A:setPoint" % beamlinepv)
        self.pvSampleTemp = epics.PV("%s:tc1:1B:temperature" % beamlinepv)
        self.pvRateRead = epics.PV("%s:tc1:5A:rampRate_RBV" % beamlinepv)
        self.pvRate = epics.PV("%s:tc1:5A:rampRate" % beamlinepv)
        self.pvTemp = epics.PV("%s:tc1:1A:temperature" % beamlinepv)
        self.pvUpdateRate = epics.PV("%s:tc1:1A:temperature.SCAN" % beamlinepv)
        self.pvRamp = epics.PV("%s:tc1:outputEnable" % beamlinepv)
        self.pvOutput = epics.PV("%s:tc1:5A:voltage_RBV" % beamlinepv)
        self.pvOutputHL = epics.PV("%s:tc1:5A:highLimit_RBV" % beamlinepv)
        self.RAMP_UNIT = 60.0
        self.pvUpdateRate.put(7)  # temperature update rate 0.5 second.
 
BEAMLINE_12IDB = 0
BEAMLINE_12IDC = 1
 
ADDRESS_12IDB = "tcpip://10.54.122.66:5025" # 12idb
ADDRESS_12IDC = "tcpip://dg645.xray.aps.anl.gov:5025" # 12idc
#DG = ik.srs.SRSDG645.open_from_uri(address)
UBZ_SHUTTER_DEADTIME = 0.005   # 5 ms.
SOFTWARE_INIT_DEADTIME = 0.001
DG645_BURST_MAX_TIME = 41
# Example:
# import dg645 as DG
# a = DG.dg645_12ID.open_from_uri(DG.addressB)
# a.pilatus(0.1, 5, 2)
#
# a.instrument["shutter"].delay
# a.instrument["shutter"].pulsewidth
# a.instrument["shutter"].polarity
# a.instrument["shutter"].level_amplitude
# a.instrument["shutter"].level_offset
 
TRSC_INTERNAL = 0
TSRC_EXTERNAL_RISING_EGDES = 1
TSRC_EXTERNAL_FALLING_EGDES = 2
TSRC_SINGLE_SHOT_EXTERNAL_RISING_EGDES = 3
TSRC_SINGLE_SHOT_EXTERNAL_FALLING_EGDES = 4
TSRC_SINGLE_SHOT = 5
TSRC_LINE = 6
 
INHIBIT_OFF = 0
INHIBIT_TRIGGERS = 1
INHIBIT_AB = 2
INHIBIT_AB_AND_CD = 3
INHIBIT_AB_CD_AND_EF = 4
INHIBIT_AB_CD_EF_AND_GH = 5
 
PRESCALE_TRIGGER_INPUT = 0
PRESCALE_OUTPUT_AB = 1
PRESCALE_OUTPUT_CD = 2
PRESCALE_OUTPUT_EF = 3
PRESCALE_OUTPUT_GH = 4
 
INSTRUMENT_STATUS = {0: 'A trigger has been detected',
                    1: 'A trigger was detected while a delay or burst cycle was in progress.',
                    2: 'A delay cycle has completed.',
                    3: 'A burst of delay cycles has completed.',
                    4: 'A delay cycle was inhibited.',
                    5: 'A delay cycle was aborted prematurely in order to change instrument delay settings.',
                    6: 'The 100 MHz PLL came unlocked.',
                    7: 'The Rb timebase came unlocked. '}
STANDARD_EVENT_STATUS = {0: 'Operation complete. All previous commands have completed.',
                    1: 'Reserved',
                    2: 'Query error occurred.',
                    3: 'Device dependent error.',
                    4: 'Execution error. A command failed to execute correctly because a parameter was out of range. ',
                    5: 'Command error. The parser detected a syntax error ',
                    6: 'Reserved',
                    7: 'Power on. The CG635 has been power cycled. '}
SERIAL_POLL_STATUS = {0: 'An unmasked bit in the instrument status register (INSR) has been set. ',
                    1: 'Set if a delay cycle is in progress. Otherwise cleared.',
                    2: 'Set if a burst cycle is in progress. Otherwise cleared.',
                    3: '',
                    4: 'The interface output buffer is non-empty.',
                    5: 'An unmasked bit in the standard event status register (*ESR) has been set.',
                    6: 'Master summary bit. Indicates that the CG635 is requesting service because an unmasked bit in this register has been set. ',
                    7: ''}
ERRORS = {0: 'No Error',
          10: 'Illigal Value',
          11: 'Illigal Mode',
          12: 'Illigal Delay',
          13: 'Illigal Link',
          14: 'Recall Failed',
          15: 'Not Allowed',
          16: 'Failed Self Test',
          17: 'Failed Auto Calibration',
          30: 'Lost Data',
          32: 'No Listener',
          110: 'Illegal Command',
          111: 'Undefined Command',
          112: 'Illegal Query',
          113: 'Illegal Set',
          114: 'Null Parameter',
          115: 'Extra Parameters',
          116: 'Missing Parameters',
          117: 'Parameter Overflow',
          118: 'Invalid Floating Point Number',
          120: 'Invalid Integer',
          121: 'Integer Overflow',
          122: 'Invalid Hexadecimal',
          126: 'Syntax Error',
          170: 'Communication Error',
          171: 'Over run',
          254: 'Too Many Errors'}
 
class DG645_Error(Exception):
    pass
 
'''
Trigger holdoff :
Trigger holdoff sets the minimum allowed time between successive triggers.
For example, if the trigger holdoff is set to 10 µs, then successive triggers
will be ignored until at least 10 µs have passed since the last trigger.
The red RATE LED will flash with each ignored trigger. Specifying holdoff is
useful if a trigger event in your application generates a significant noise
transient that must have time to decay away before the next trigger is generated.  
Trigger holdoff can also be used to trigger the DG645 at a sub-multiple of
a known input trigger rate. For example, by selecting LINE as the trigger source
and setting the holdoff to 0.99 s, the DG645 can be triggered synchronously with
the power line, but at 1 Hz. This technique works as long as the timebase of
the trigger source doesn't vary significantly relative to the DG645's timebase.
Otherwise, trigger prescaling should be used.
Note that trigger holdoff is available only after advanced triggering is enabled.
Once advanced triggering is enabled, the user can view and modify the trigger
holdoff by successively pressing the 'TRIG' key in the DISPLAY section of
the front panel until the display prefix is 'HOLD'.
If the trigger holdoff is 10 µs, then the main display will show 'HOLD 0.000010000000',
and the STATUS LED just below the main display will be highlighted.
Once displayed, the user can modify the trigger holdoff using any of the methods
discussed in the section Front-Panel Interface earlier in this chapter.
 
 
Trigger Prescaling: (Not available)
The DG645 supports a number of complex triggering requirements through a set of
prescaling registers. Trigger prescaling enables the DG645 to be triggered synchronously
with a much faster source, but at a sub-multiple of the original trigger frequency.
For example, the DG645 can be triggered at 1 kHz, but synchronously with a mode locked laser
running at 80 MHz, by prescaling the trigger input by 80,000.  
Furthermore, the DG645 also contains a separate prescaler for each front panel output
that enables it to operate at a sub-multiple of the prescaled trigger input frequency.
Continuing with the example above, if the AB prescaler is set to 100, the AB output will
only be enabled for 1 out of every 100 delay cycles which is equivalent to a rate of
1 kHz/100 = 10 Hz.
Lastly, the DG645 contains a separate phase register for each output prescaler
that determines the phase of the prescaler output relative to the other prescaled outputs.
For example, if both the AB and CD prescalers are set to 100 and their phase registers to
0 and 50, respectively, then AB and CD will both run at 10 Hz, but CD's output will be
enabled 50 delay cycles after AB's output.
'''
def connect(beamline=BEAMLINE_12IDB):
    if beamline==BEAMLINE_12IDB:
        addr = ADDRESS_12IDB
    if beamline==BEAMLINE_12IDC:
        addr = ADDRESS_12IDC
    return dg645_12ID.open_from_uri(addr)
 
class _dg645Instrument(object):
    def __init__(self, ddg, chan):
        if not isinstance(ddg, dg645_12ID):
            raise TypeError("Don't do that.")
        if isinstance(chan, dg645_12ID.Instruments):
            self._chan = chan.value
        else:
            self._chan = chan
        self._ddg = ddg
 
 
beamlinePV = '12idc:'
 
from threading import Thread
from epics import caget, caput, PV
import time
from PyQt5 import QtCore
from PyQt5.QtCore import QObject
 
beamline = '12IDC'
 
def keepshutteropen(beamline='12IDC'):
    if beamline.lower() == '12idb':
        station = 'B'
    if beamline.lower() == '12idc':
        station = 'C'
    pv_a_shutter = f"PB:12ID:STA_{station}_S{station}S_CLSD_PL.VAL"
    pv_exp_shutter = f"12ida2:rShtr{station}:Open"
    val = caget(pv_a_shutter)
    if val == 0:
        caput(pv_exp_shutter, 1)
 
## shutter stuff.. Could be eventually separated out.
def open_shutter(beamline='12IDC'):
    if beamline.lower() == '12idb':
        station = 'B'
    if beamline.lower() == '12idc':
        station = 'C'
    pv_exp_shutter = f"12ida2:rShtr{station}:Open"
    caput(pv_exp_shutter, 1)
 
def close_shutter(beamline='12IDC'):
    if beamline.lower() == '12idb':
        station = 'B'
    if beamline.lower() == '12idc':
        station = 'C'
    pv_exp_shutter = f"12ida2:rShtr{station}:Close"
    caput(pv_exp_shutter, 1)
 
class beamstatus(QObject):
    onChange = QtCore.pyqtSignal()
    def __init__(self, beamline="12IDC"):
        if beamline.lower() == '12idb':
            station = 'B'
        if beamline.lower() == '12idc':
            station = 'C'
        # A station shutter..
        self.shutter_val = PV('PB:12ID:STA_A_FES_CLSD_PL', callback=self.check_A_shutter)
        self.shutterA = PV('12ida2:rShtrA:Open')
        self.shutterC_open = PV(f'12ida2:rShtr{station}:Open')
        self.shutterC_close = PV(f'12ida2:rShtr{station}:Close')
 
 