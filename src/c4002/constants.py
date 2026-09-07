"""
Constants for DFRobot C4002 (SEN0691) 24GHz mmWave radar sensor.

DISCLAIMER:
This is an unofficial, community-developed driver and is not affiliated
with, maintained by, or endorsed by DFRobot.
"""

from enum import IntEnum

# Frame Header sequence: 0xFA 0xF5 0xAA 0xA5
FRAME_HEADER_BYTES = bytes([0xFA, 0xF5, 0xAA, 0xA5])

# Frame Types
FRAME_TYPE_WRITE_REQUEST = 0x00
FRAME_TYPE_READ_REQUEST = 0x01
FRAME_TYPE_WRITE_RESPOND = 0x02
FRAME_TYPE_READ_RESPOND = 0x03
FRAME_TYPE_NOTIFICATION = 0x04

# Command IDs
CMD_RESTART = 0x00
CMD_FACTORY_RESET = 0x80
CMD_GET_VERSION = 0x82
CMD_SET_REPORT_PERIOD = 0x83
CMD_SET_TARGET_DISAPPEAR_DELAY = 0x84
CMD_SET_DETECT_RANGE = 0x86
CMD_SET_LIGHT_THRESHOLD = 0x88
CMD_CONFIG_OUT_MODE = 0xA0
CMD_SET_LED_MODE = 0xA1
CMD_ENV_CALIBRATION = 0x60
CMD_SET_DISTANCE_DOOR = 0x62
CMD_SET_DISTANCE_DOOR_THRESHOLD = 0x63
CMD_GET_AND_SET_RESOLUTION_MODE = 0x66

# Notification Sub-Commands
NOTE_RESULT_CMD = 0x60
NOTE_CALIBRATION_CMD = 0x03

# Response Status Codes
RESP_SUCCEED = 0x01
RESP_CMD_ERR = 0x02
RESP_AUTH_ERR = 0x03
RESP_BUSY = 0x04
RESP_PARAMS_ERR = 0x05
RESP_DATA_LEN_ERR = 0x06
RESP_INTERNAL_ERR = 0x07


class TargetState(IntEnum):
    """Detection state of the target."""
    NO_TARGET = 0
    STATIC_PRESENCE = 1
    MOTION = 2

    @property
    def label(self) -> str:
        labels = {
            TargetState.NO_TARGET: "No Target",
            TargetState.STATIC_PRESENCE: "Static Presence (Sitting/Breathing)",
            TargetState.MOTION: "Motion Detected",
        }
        return labels.get(self, "Unknown")


class MotionDirection(IntEnum):
    """Direction of moving target relative to the sensor."""
    AWAY = 0
    NO_DIRECTION = 1
    APPROACHING = 2

    @property
    def label(self) -> str:
        labels = {
            MotionDirection.AWAY: "Moving Away",
            MotionDirection.NO_DIRECTION: "Stationary / No Direction",
            MotionDirection.APPROACHING: "Approaching",
        }
        return labels.get(self, "Unknown")


class ResolutionMode(IntEnum):
    """Distance gate resolution mode."""
    RESOLUTION_80CM = 0x00  # Up to 15 gates, max 11.6m
    RESOLUTION_20CM = 0x01  # Up to 25 gates, max 4.9m
