# SPEC command cross-reference

To help transition from SPEC, these tables list macros
from file `DG645_lee.mac` and their counterparts with the
EPICS/bluesky support.

## DG645 signals

Some macros are available directly from the `dg645` object as ophyd signal objects.

SPEC macro              | signal                    | setting
---                     | ---                       | ---
dg645_burst_disable     | dg645.burst_mode          | 0
dg645_burst_enable      | dg645.burst_mode          | 1
dg645_dlay 0            | dg645.channel_T0.delay    | delay time, s
dg645_dlay 1            | dg645.channel_T1.delay    | delay time, s
dg645_dlay 2            | dg645.channel_A.delay     | delay time, s
dg645_dlay 3            | dg645.channel_B.delay     | delay time, s
dg645_dlay 4            | dg645.channel_C.delay     | delay time, s
dg645_dlay 5            | dg645.channel_D.delay     | delay time, s
dg645_dlay 6            | dg645.channel_E.delay     | delay time, s
dg645_dlay 7            | dg645.channel_F.delay     | delay time, s
dg645_dlay 8            | dg645.channel_G.delay     | delay time, s
dg645_dlay 9            | dg645.channel_H.delay     | delay time, s
dg645_idn               | dg645.device_id           | (read-only)
dg645_polarity          | dg645.output_AB.polarity  | polarity
dg645_polarity          | dg645.output_CD.polarity  | polarity
dg645_polarity          | dg645.output_EF.polarity  | polarity
dg645_polarity          | dg645.output_GH.polarity  | polarity
dg645_polarity          | dg645.output_T0.polarity  | polarity
dg645_tsrc              | dg645.trigger_source      | 0..6 (or EPICS mbbo text)
error checking OFF      | dg645.status_checking     | 0
error checking ON       | dg645.status_checking     | 1
error status text       | dg645.status              | (read-only)


## DG645 plan stubs

These bluesky plan stubs (and Python functions) configure or show various DG645 settings.

SPEC macro              | Bluesky plan stub
---                     | ---
dg645_burst_init        | dg645_burst_init
dg645_burst_set         | dg645_burst_set
dg645_burst_set_new     | dg645_burst_set
dg645_check_error       | dg645_check_error
dg645_config            | set trigger source on startup
dg645_dlay              | dg645_dlay
dg645_dsp               | dg645_dsp (function, not a plan)
dg645_dspamp            | dg645_dspamp
dg645_set               | dg645_set
dg645_trig              | dg645_trig
dg645set_1cycle         | dg645set_1cycle
dg645set_AB             | dg645set_AB
dg645set_CD             | dg645set_CD
dg645set_EF             | dg645set_EF
dg645set_GH             | dg645set_GH
dg645_status            | -N/A- (No EPICS PVs available now)


## DG645 plan stubs with other devices

The macros integrate a DG645 with other beamline devices.

SPEC macro              Bluesky plan stub
---                     | ---
dg645_struck            | dg645_struck
dg645_done              | TODO
dg645_mar               | TODO
dg645_PE                | TODO
dg645_pilatus           | TODO
dg645_pilatus_func      | TODO
dg645_set_mar           | TODO
dg645_set_PE            | TODO
dg645_set_PE2           | TODO
dg645_set_PE3           | TODO
dg645_set_pilatus       | TODO
dg645_set_pilatus_fly   | TODO
dg645_set_pilatus2      | TODO
dg645_struck            | TODO
dg645_struck_terminate  | TODO
