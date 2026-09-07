"""
Unit tests for C4002 binary packet parser.
Compatible with standard unittest and pytest.
"""

import unittest
from c4002.constants import MotionDirection, TargetState
from c4002.sensor import C4002Sensor, CalibrationStatus, TelemetryData


class TestC4002Parser(unittest.TestCase):

    def test_parse_real_presence_frame(self) -> None:
        # 32-byte frame captured live from physical C4002 sensor
        raw_frame = bytes.fromhex(
            "FAF5AAA52000000460011600011202060000000F004400639400FFFF58019507"
        )

        result = C4002Sensor.parse_packet(raw_frame)
        self.assertIsInstance(result, TelemetryData)
        self.assertEqual(result.target_state, TargetState.STATIC_PRESENCE)
        self.assertTrue(result.presence_detected)
        self.assertEqual(result.ambient_light_lux, 53.0)  # (0x0212 = 530 * 0.1)
        self.assertEqual(result.presence_distance_m, 0.68)  # (0x0044 = 68 cm)
        self.assertEqual(result.presence_energy, 99)
        self.assertEqual(result.presence_countdown_s, 15)
        self.assertEqual(result.motion_distance_m, 1.48)  # (0x0094 = 148 cm)
        self.assertEqual(result.motion_speed_m_s, -0.01)  # (0xFFFF signed = -1 cm/s)
        self.assertEqual(result.motion_energy, 88)
        self.assertEqual(result.motion_direction, MotionDirection.NO_DIRECTION)

    def test_parse_calibration_frame(self) -> None:
        # Valid calibration notification packet (cmd 0x03, countdown = 25s)
        packet_pre = bytearray([
            0xFA, 0xF5, 0xAA, 0xA5,
            0x10, 0x00,
            0x00,
            0x04,
            0x03,
            0x01,
            0x02, 0x00,
            0x19, 0x00  # 25 seconds countdown
        ])
        chk = sum(packet_pre) & 0xFFFF
        packet_pre.append(chk & 0xFF)
        packet_pre.append((chk >> 8) & 0xFF)

        result = C4002Sensor.parse_packet(bytes(packet_pre))
        self.assertIsInstance(result, CalibrationStatus)
        self.assertTrue(result.is_calibrating)
        self.assertEqual(result.countdown_s, 25)

    def test_reject_bad_checksum(self) -> None:
        raw_frame = bytearray.fromhex(
            "FAF5AAA52000000460011600011202060000000F004400639400FFFF58019507"
        )
        raw_frame[-1] ^= 0xFF  # Corrupt checksum
        self.assertIsNone(C4002Sensor.parse_packet(bytes(raw_frame)))

    def test_reject_short_packet(self) -> None:
        short_frame = bytes.fromhex("FAF5AAA52000")
        self.assertIsNone(C4002Sensor.parse_packet(short_frame))

    def test_reject_invalid_header(self) -> None:
        bad_header = bytes.fromhex(
            "001122332000000460011600011202060000000F004400639400FFFF58019507"
        )
        self.assertIsNone(C4002Sensor.parse_packet(bad_header))


if __name__ == "__main__":
    unittest.main()
