"""
Driver for DFRobot C4002 (SEN0691) 24GHz mmWave radar sensor.

DISCLAIMER:
This is an independent, unofficial community-developed Python library.
It is not affiliated with, maintained by, or endorsed by DFRobot.
"""

from __future__ import annotations

import logging
import struct
import time
from dataclasses import dataclass
from typing import Any

try:
    import serial
except ImportError:
    serial = None  # type: ignore

try:
    from RPi import GPIO
    HAS_GPIO = True
except (ImportError, RuntimeError):
    HAS_GPIO = False

from c4002.constants import (
    CMD_ENV_CALIBRATION,
    CMD_SET_DETECT_RANGE,
    CMD_SET_LED_MODE,
    CMD_SET_REPORT_PERIOD,
    CMD_SET_TARGET_DISAPPEAR_DELAY,
    FRAME_HEADER_BYTES,
    FRAME_TYPE_NOTIFICATION,
    FRAME_TYPE_WRITE_REQUEST,
    NOTE_CALIBRATION_CMD,
    NOTE_RESULT_CMD,
    LedMode,
    MotionDirection,
    TargetState,
)

logger = logging.getLogger(__name__)


@dataclass
class TelemetryData:
    """Parsed sensor telemetry frame."""
    target_state: TargetState
    target_state_name: str
    presence_detected: bool
    ambient_light_lux: float
    gate_bitmask: int
    presence_countdown_s: int
    presence_distance_m: float
    presence_energy: int
    motion_distance_m: float
    motion_speed_m_s: float
    motion_energy: int
    motion_direction: MotionDirection
    motion_direction_name: str


@dataclass
class CalibrationStatus:
    """Status during environmental background noise calibration."""
    is_calibrating: bool
    countdown_s: int


class C4002Sensor:
    """
    Python interface for DFRobot C4002 mmWave Human Presence Module (SEN0691).

    Communicates via 115200 baud UART and optional digital GPIO OUT pin.
    """

    def __init__(
        self,
        port: str = "/dev/serial0",
        baudrate: int = 115200,
        out_pin: int | None = None,
        timeout: float = 1.0,
    ) -> None:
        """
        Initialize the sensor instance.

        :param port: UART serial port path (default '/dev/serial0' for Raspberry Pi)
        :param baudrate: Serial baud rate (default 115200)
        :param out_pin: BCM GPIO pin number connected to C4002 OUT pin (None to disable)
        :param timeout: Serial read timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.out_pin = out_pin
        self.timeout = timeout
        self.ser: Any = None

        if self.out_pin is not None:
            if not HAS_GPIO:
                logger.warning(
                    "RPi.GPIO is not available in this environment. OUT pin monitoring disabled."
                )
                self.out_pin = None
            else:
                GPIO.setwarnings(False)
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.out_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def connect(self) -> None:
        """Open the serial port connection."""
        if serial is None:
            raise ImportError(
                "pyserial is required to connect to hardware. Install it via: pip install pyserial"
            )
        self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        self.ser.flushInput()
        logger.info("Connected to C4002 on %s at %d baud", self.port, self.baudrate)

    def close(self) -> None:
        """Close serial port and clean up GPIO resources."""
        if self.ser and hasattr(self.ser, "is_open") and self.ser.is_open:
            self.ser.close()
            logger.info("Closed serial port %s", self.port)
        if self.out_pin is not None and HAS_GPIO:
            GPIO.cleanup(self.out_pin)

    def __enter__(self) -> C4002Sensor:
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def read_out_pin(self) -> bool | None:
        """
        Read the digital OUT pin if configured.
        :return: True if HIGH (presence detected), False if LOW (clear), or None if unconfigured.
        """
        if self.out_pin is not None and HAS_GPIO:
            return GPIO.input(self.out_pin) == GPIO.HIGH
        return None

    @staticmethod
    def verify_checksum(packet: bytes) -> bool:
        """
        Validate packet checksum: sum of bytes [0..N-3] & 0xFFFF == uint16 LE at [N-2..N-1].
        """
        if len(packet) < 8:
            return False
        calc = sum(packet[:-2]) & 0xFFFF
        recv = packet[-2] | (packet[-1] << 8)
        return calc == recv

    @classmethod
    def parse_packet(cls, packet: bytes) -> TelemetryData | CalibrationStatus | None:
        """
        Parse a raw binary frame without requiring an open serial port.

        Frame Layout (32 bytes standard notification):
          [0..3]   Header (FA F5 AA A5)
          [4..5]   Total length (uint16 LE)
          [6]      Reserved (0x00)
          [7]      Pack type (0x04 = Notification)
          [8]      Command ID (0x60 = Result, 0x03 = Calibration)
          [9]      Response code (0x01 = Success)
          [10..11] Inner data length (uint16 LE)
          [12..N]  Payload
          [N+1..]  Checksum (uint16 LE)
        """
        if len(packet) < 14:
            return None
        if not packet.startswith(FRAME_HEADER_BYTES):
            return None
        if not cls.verify_checksum(packet):
            logger.debug("Packet checksum mismatch")
            return None

        pack_type = packet[7]
        cmd = packet[8]

        # Normal detection notification (type 0x04, cmd 0x60)
        if pack_type == FRAME_TYPE_NOTIFICATION and cmd == NOTE_RESULT_CMD:
            payload = packet[12:-2]
            if len(payload) < 18:
                return None

            status_val = payload[0]
            light_raw = payload[1] | (payload[2] << 8)
            gate_bitmask = payload[3] | (payload[4] << 8) | (payload[5] << 16) | (payload[6] << 24)
            countdown = payload[7] | (payload[8] << 8)
            pres_dist_cm = payload[9] | (payload[10] << 8)
            pres_energy = payload[11]
            motion_dist_cm = payload[12] | (payload[13] << 8)
            motion_speed_raw = struct.unpack('<h', bytes([payload[14], payload[15]]))[0]
            motion_energy = payload[16]
            motion_dir_val = payload[17]

            target_state = TargetState(status_val) if status_val in TargetState._value2member_map_ else TargetState.NO_TARGET
            direction = MotionDirection(motion_dir_val) if motion_dir_val in MotionDirection._value2member_map_ else MotionDirection.NO_DIRECTION

            return TelemetryData(
                target_state=target_state,
                target_state_name=target_state.label,
                presence_detected=target_state != TargetState.NO_TARGET,
                ambient_light_lux=round(light_raw * 0.1, 1),
                gate_bitmask=gate_bitmask,
                presence_countdown_s=countdown,
                presence_distance_m=round(pres_dist_cm * 0.01, 2),
                presence_energy=pres_energy,
                motion_distance_m=round(motion_dist_cm * 0.01, 2),
                motion_speed_m_s=round(motion_speed_raw * 0.01, 2),
                motion_energy=motion_energy,
                motion_direction=direction,
                motion_direction_name=direction.label,
            )

        # Environmental calibration progress notification (cmd 0x03)
        if pack_type == FRAME_TYPE_NOTIFICATION and cmd == NOTE_CALIBRATION_CMD:
            countdown = packet[12] | (packet[13] << 8)
            return CalibrationStatus(is_calibrating=True, countdown_s=countdown)

        return None

    def read_packet(self) -> TelemetryData | CalibrationStatus | None:
        """
        Synchronously synchronize to the next frame header and read the full packet.
        :return: TelemetryData, CalibrationStatus, or None on timeout.
        """
        if not self.ser or not hasattr(self.ser, "is_open") or not self.ser.is_open:
            raise RuntimeError("Serial port is not connected. Call connect() first.")

        header_buf = bytearray()
        start = time.time()

        # Synchronize to 4-byte header
        while len(header_buf) < 4:
            if time.time() - start > self.timeout:
                return None
            b = self.ser.read(1)
            if not b:
                continue
            header_buf.append(b[0])
            if len(header_buf) == 4 and bytes(header_buf) != FRAME_HEADER_BYTES:
                header_buf.pop(0)

        # Read 2-byte total length
        len_bytes = self.ser.read(2)
        if len(len_bytes) < 2:
            return None
        total_len = len_bytes[0] | (len_bytes[1] << 8)

        if total_len < 14 or total_len > 128:
            return None

        # Read remaining packet body
        remaining_len = total_len - 6
        remaining = self.ser.read(remaining_len)
        if len(remaining) < remaining_len:
            return None

        full_packet = bytes(header_buf + len_bytes + remaining)
        return self.parse_packet(full_packet)

    def start_env_calibration(self, delay_time: int = 10, cont_time: int = 30) -> None:
        """
        Trigger automatic environmental background noise calibration.
        :param delay_time: Seconds before calibration starts (0-65535s)
        :param cont_time: Duration of background measurement (15-65535s)
        """
        data = [
            CMD_ENV_CALIBRATION,
            0x00,               # Read/Write request
            0x09, 0x00,         # Data length
            delay_time & 0xFF, (delay_time >> 8) & 0xFF,
            cont_time & 0xFF, (cont_time >> 8) & 0xFF,
            0x01
        ]
        self._send_frame(data, 9, FRAME_TYPE_WRITE_REQUEST)

    def set_report_period(self, period_100ms: int = 10) -> None:
        """
        Set sensor telemetry report period in units of 100ms (10 = 1.0s).
        """
        data = [
            CMD_SET_REPORT_PERIOD,
            0x00,
            0x05, 0x00,
            period_100ms & 0xFF
        ]
        self._send_frame(data, 5, FRAME_TYPE_WRITE_REQUEST)

    def set_detect_range(self, closest_cm: int = 0, farthest_cm: int = 1100) -> None:
        """
        Set minimum and maximum detection range in centimeters (0 - 1100 cm).
        """
        farthest = min(max(farthest_cm, 0), 1100)
        closest = max(closest_cm, 0)
        data = [
            CMD_SET_DETECT_RANGE,
            0x00,
            0x08, 0x00,
            closest & 0xFF, (closest >> 8) & 0xFF,
            farthest & 0xFF, (farthest >> 8) & 0xFF
        ]
        self._send_frame(data, 8, FRAME_TYPE_WRITE_REQUEST)

    def set_target_disappear_delay(self, delay_s: int = 1) -> None:
        """
        Set delay time in seconds before reporting target disappearance (0 - 65535s).
        """
        data = [
            CMD_SET_TARGET_DISAPPEAR_DELAY,
            0x00,
            0x06, 0x00,
            delay_s & 0xFF, (delay_s >> 8) & 0xFF
        ]
        self._send_frame(data, 6, FRAME_TYPE_WRITE_REQUEST)

    def set_led(
        self,
        run_led: int | bool = LedMode.OFF,
        out_led: int | bool = LedMode.OFF,
    ) -> None:
        """
        Configure the onboard RUN (operation) and OUT (detection) LEDs.

        :param run_led: LedMode.OFF (or False), LedMode.ON (or True), or LedMode.KEEP
        :param out_led: LedMode.OFF (or False), LedMode.ON (or True), or LedMode.KEEP
        """
        run_val = int(run_led)
        out_val = int(out_led)
        data = [
            CMD_SET_LED_MODE,
            0x00,  # Read/Write request
            0x06, 0x00,  # Data length = 6
            run_val & 0xFF,
            out_val & 0xFF,
        ]
        self._send_frame(data, 6, FRAME_TYPE_WRITE_REQUEST)

    def set_run_led(self, state: int | bool) -> None:
        """
        Configure the onboard blue RUN (operation/power) LED.

        :param state: LedMode.OFF (False) or LedMode.ON (True)
        """
        self.set_led(run_led=state, out_led=LedMode.KEEP)

    def set_out_led(self, state: int | bool) -> None:
        """
        Configure the onboard OUT (detection indicator) LED.

        :param state: LedMode.OFF (False) or LedMode.ON (True)
        """
        self.set_led(run_led=LedMode.KEEP, out_led=state)

    def turn_off_leds(self) -> None:
        """Convenience method to turn off both onboard LEDs (stealth/dark mode)."""
        self.set_led(run_led=LedMode.OFF, out_led=LedMode.OFF)


    def _send_frame(self, data: list[int], data_len: int, msg_type: int) -> None:
        """Internal helper to construct and transmit a validated command frame."""
        total_len = data_len + 10
        frame = bytearray([
            FRAME_HEADER_BYTES[0], FRAME_HEADER_BYTES[1],
            FRAME_HEADER_BYTES[2], FRAME_HEADER_BYTES[3],
            total_len & 0xFF, (total_len >> 8) & 0xFF,
            0x00, msg_type
        ])
        frame.extend(data)
        checksum = sum(frame) & 0xFFFF
        frame.append(checksum & 0xFF)
        frame.append((checksum >> 8) & 0xFF)

        if self.ser and hasattr(self.ser, "is_open") and self.ser.is_open:
            self.ser.flushInput()
            self.ser.write(frame)
