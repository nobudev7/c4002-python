#!/usr/bin/env python3
"""
Basic live monitoring example for DFRobot C4002 mmWave sensor.
"""

import time
from c4002 import C4002Sensor, TargetState


def main() -> None:
    print("==================================================")
    print("  DFRobot C4002 mmWave Sensor — Live Monitor      ")
    print("==================================================")

    # Initialize sensor on Raspberry Pi default serial port (/dev/serial0)
    # and optional OUT pin connected to GPIO 17
    sensor = C4002Sensor(port="/dev/serial0", baudrate=115200, out_pin=17)

    try:
        sensor.connect()
        print("Connected to C4002. Press Ctrl+C to stop.\n")

        while True:
            # 1. Read optional digital GPIO OUT pin
            out_pin_high = sensor.read_out_pin()

            # 2. Read parsed UART telemetry frame
            telemetry = sensor.read_packet()

            if telemetry and not getattr(telemetry, "is_calibrating", False):
                ts = time.strftime("%H:%M:%S")
                print(f"[{ts}]")
                if out_pin_high is not None:
                    status_str = "HIGH (Presence)" if out_pin_high else "LOW (Clear)"
                    print(f"  OUT Pin           : {status_str}")
                print(f"  Target State      : {telemetry.target_state_name}")
                print(f"  Ambient Light     : {telemetry.ambient_light_lux} Lux")

                if telemetry.presence_detected:
                    print(f"  Presence Distance : {telemetry.presence_distance_m} m (Energy: {telemetry.presence_energy}/100)")
                    print(f"  Presence Countdown: {telemetry.presence_countdown_s} s")

                    if telemetry.target_state == TargetState.MOTION:
                        print(f"  Motion Distance   : {telemetry.motion_distance_m} m (Energy: {telemetry.motion_energy}/100)")
                        print(f"  Motion Speed      : {telemetry.motion_speed_m_s} m/s")
                        print(f"  Motion Direction  : {telemetry.motion_direction_name}")

                print("-" * 50)

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nStopping monitor...")
    finally:
        sensor.close()
        print("Sensor closed.")


if __name__ == "__main__":
    main()
