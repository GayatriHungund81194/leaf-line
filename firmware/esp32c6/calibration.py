"""Moisture sensor calibration values.

Update these after recalibrating (see the calibration procedure in the
project notes) - nothing else in the firmware should need to change
when you recalibrate.

Last calibrated: 2026-11-03, outdoor patio ~60F, Milpitas CA 95035
Soil: dry potting mix, saturated to field capacity (drained ~8 min)
"""

DRY_VALUE = 40654    # raw ADC reading, dry soil
WET_VALUE = 30944    # raw ADC reading, soil saturated to field capacity
