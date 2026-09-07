#!/usr/bin/env python3
"""
Automated environmental background noise calibration for C4002 sensor.

This utility measures stationary background radar reflections (walls, monitors,
curtains, fans) and sets dynamic noise thresholds to eliminate false presence.
"""

import time

from c4002 import C4002Sensor


def main() -> None:
    print("==========================================================")
    print("      C4002 Auto Environmental Calibration Utility        ")
    print("==========================================================")

    sensor = C4002Sensor(port="/dev/serial0", baudrate=115200)

    try:
        sensor.connect()
        print("Connected to sensor.")
        print()
        print("Starting 40-second calibration routine:")
        print("  • Delay Time      : 10 seconds (time to exit the room)")
        print("  • Calibration Time: 30 seconds (measuring background noise)")
        print()
        print("⚠️  PLEASE LEAVE THE ROOM IMMEDIATELY!")
        print("   Ensure the sensor has an unobstructed view and no persons are nearby.")
        print()

        sensor.start_env_calibration(delay_time=10, cont_time=30)

        while True:
            packet = sensor.read_packet()
            if packet and getattr(packet, "is_calibrating", False):
                cd = packet.countdown_s
                print(f"[{time.strftime('%H:%M:%S')}] Calibration countdown: {cd:2d} seconds remaining...")
                if cd == 0:
                    print()
                    print("✅ Calibration complete! Sensor has stored the room's noise floor.")
                    print("   Run 'python3 examples/basic_monitor.py' to test detection.")
                    break
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nCalibration cancelled.")
    finally:
        sensor.close()


if __name__ == "__main__":
    main()
