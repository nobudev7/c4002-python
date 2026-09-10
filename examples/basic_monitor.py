#!/usr/bin/env python3
"""
Basic live monitoring example for DFRobot C4002 mmWave sensor.
"""

import argparse
import time

from c4002 import C4002Sensor, TargetState


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DFRobot C4002 mmWave Sensor — Live Monitor"
    )
    parser.add_argument(
        "--port",
        default="/dev/serial0",
        help="Serial port path (default: /dev/serial0)",
    )
    parser.add_argument(
        "--out-pin",
        type=int,
        default=17,
        help="BCM GPIO pin connected to OUT (default: 17, pass -1 to disable)",
    )
    led_group = parser.add_mutually_exclusive_group()
    led_group.add_argument(
        "--led-off",
        action="store_true",
        help="Turn off onboard blue RUN and detection LEDs (dark/stealth mode)",
    )
    led_group.add_argument(
        "--led-on",
        action="store_true",
        help="Turn on onboard blue RUN and detection LEDs (restore default)",
    )
    args = parser.parse_args()

    print("==================================================")
    print("  DFRobot C4002 mmWave Sensor — Live Monitor      ")
    print("==================================================")

    out_pin = None if args.out_pin < 0 else args.out_pin
    sensor = C4002Sensor(port=args.port, baudrate=115200, out_pin=out_pin)

    try:
        sensor.connect()
        print("Connected to C4002.")

        if args.led_off:
            sensor.turn_off_leds()
            print("Onboard LEDs turned OFF.")
        elif args.led_on:
            sensor.set_led(run_led=True, out_led=True)
            print("Onboard LEDs turned ON.")

        print("Press Ctrl+C to stop.\n")


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

    except KeyboardInterrupt:
        print("\nStopping monitor...")
    finally:
        sensor.close()
        print("Sensor closed.")


if __name__ == "__main__":
    main()
