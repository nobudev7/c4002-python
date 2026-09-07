"""
c4002-python — Python library for DFRobot C4002 24GHz mmWave radar sensor.

DISCLAIMER:
This is an independent, community-developed open-source library.
It is not affiliated with, maintained by, or endorsed by DFRobot.
"""

from c4002.constants import MotionDirection, ResolutionMode, TargetState
from c4002.sensor import C4002Sensor, CalibrationStatus, TelemetryData

__version__ = "0.1.0"
__all__ = [
    "C4002Sensor",
    "CalibrationStatus",
    "MotionDirection",
    "ResolutionMode",
    "TargetState",
    "TelemetryData",
]
