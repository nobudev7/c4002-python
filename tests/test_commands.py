"""
Unit tests for C4002 command frame generation and LED controls.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from c4002.constants import (
    CMD_SET_LED_MODE,
    FRAME_HEADER_BYTES,
    FRAME_TYPE_WRITE_REQUEST,
    LED_KEEP,
    LED_OFF,
    LED_ON,
    LedMode,
)
from c4002.sensor import C4002Sensor


class TestC4002Commands(unittest.TestCase):

    def setUp(self) -> None:
        self.sensor = C4002Sensor(port="/dev/null")
        self.sensor.ser = MagicMock()
        self.sensor.ser.is_open = True

    def test_turn_off_leds(self) -> None:
        self.sensor.turn_off_leds()

        self.sensor.ser.write.assert_called_once()
        written = self.sensor.ser.write.call_args[0][0]

        # Total packet length: 16 bytes (10 overhead + 6 payload)
        self.assertEqual(len(written), 16)
        self.assertEqual(written[:4], FRAME_HEADER_BYTES)
        self.assertEqual(written[4:6], bytes([0x10, 0x00]))  # total_len = 16
        self.assertEqual(written[6], 0x00)  # reserved
        self.assertEqual(written[7], FRAME_TYPE_WRITE_REQUEST)  # pack_type = 0x00
        self.assertEqual(written[8], CMD_SET_LED_MODE)  # 0xA1
        self.assertEqual(written[9], 0x00)  # read_write_req
        self.assertEqual(written[10:12], bytes([0x06, 0x00]))  # inner len = 6
        self.assertEqual(written[12], LedMode.OFF)  # run_led = 0
        self.assertEqual(written[13], LedMode.OFF)  # out_led = 0

        # Validate checksum
        chk = sum(written[:-2]) & 0xFFFF
        written_chk = written[-2] | (written[-1] << 8)
        self.assertEqual(chk, written_chk)

    def test_set_run_led_on_keeps_out_led(self) -> None:
        self.sensor.set_run_led(True)

        self.sensor.ser.write.assert_called_once()
        written = self.sensor.ser.write.call_args[0][0]

        self.assertEqual(written[12], LED_ON)
        self.assertEqual(written[13], LED_KEEP)  # 0xFF

    def test_set_out_led_off_keeps_run_led(self) -> None:
        self.sensor.set_out_led(False)

        self.sensor.ser.write.assert_called_once()
        written = self.sensor.ser.write.call_args[0][0]

        self.assertEqual(written[12], LED_KEEP)  # 0xFF
        self.assertEqual(written[13], LED_OFF)


if __name__ == "__main__":
    unittest.main()
