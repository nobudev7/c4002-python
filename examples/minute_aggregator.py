#!/usr/bin/env python3
"""
1-Minute Windowed Aggregator & CSV Time-Series Logger.

Continuously samples C4002 telemetry (1 Hz) and computes clean 1-minute
aggregations (occupancy ratio, average distance, peak motion, average lux)
logged to a CSV file for time-series charting.
"""

from __future__ import annotations

import argparse
import statistics
import time
from pathlib import Path

from c4002 import C4002Sensor


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aggregate C4002 mmWave radar telemetry into 1-minute time-series records."
    )
    parser.add_argument(
        "--port",
        default="/dev/serial0",
        help="Serial port path (default: /dev/serial0)",
    )
    parser.add_argument(
        "--output",
        default="presence_1min_timeseries.csv",
        help="Output CSV file path (default: presence_1min_timeseries.csv)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Aggregation window in seconds (default: 60)",
    )
    args = parser.parse_args()

    csv_path = Path(args.output)
    csv_header = "timestamp,occupancy_pct,avg_distance_m,max_motion_energy,avg_light_lux,sample_count\n"

    # Create CSV and write header if file doesn't exist or is empty
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(csv_header)

    print("==========================================================")
    print("      C4002 Time-Series 1-Minute Aggregator Logger        ")
    print("==========================================================")
    print(f"  • Serial Port       : {args.port}")
    print(f"  • Aggregation Window: {args.interval} seconds")
    print(f"  • CSV Output File   : {csv_path.resolve()}")
    print("Press Ctrl+C to stop.\n")

    sensor = C4002Sensor(port=args.port, baudrate=115200)

    try:
        sensor.connect()

        # Set sensor hardware reporting interval to 1.0s (10 * 100ms)
        sensor.set_report_period(10)
        time.sleep(0.1)

        # Flush any stale packets that were buffered before starting
        if sensor.ser and hasattr(sensor.ser, "reset_input_buffer"):
            sensor.ser.reset_input_buffer()

        minute_samples = []
        window_start = time.time()

        while True:
            # Blocks until the next packet arrives from the sensor
            packet = sensor.read_packet()
            if packet and not getattr(packet, "is_calibrating", False):
                minute_samples.append(packet)

            # Check if aggregation window has elapsed
            now = time.time()
            elapsed = now - window_start
            if elapsed >= args.interval:
                if minute_samples:
                    total_samples = len(minute_samples)

                    # 1. Occupancy percentage (% of samples detecting presence/motion)
                    present_samples = [s for s in minute_samples if s.presence_detected]
                    occupancy_pct = round((len(present_samples) / total_samples) * 100, 1)

                    # 2. Average distance (calculated ONLY when someone was actually present)
                    if present_samples:
                        avg_distance: float | None = round(
                            statistics.mean(s.presence_distance_m for s in present_samples), 2
                        )
                    else:
                        avg_distance = None

                    # 3. Peak motion energy observed during the window (0 - 100)
                    max_motion_energy = max(s.motion_energy for s in minute_samples)

                    # 4. Average ambient light intensity (Lux)
                    avg_light = round(
                        statistics.mean(s.ambient_light_lux for s in minute_samples), 1
                    )

                    # Format timestamp and CSV row
                    timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
                    dist_str = f"{avg_distance:.2f}" if avg_distance is not None else ""
                    csv_row = (
                        f"{timestamp_str},{occupancy_pct},{dist_str},"
                        f"{max_motion_energy},{avg_light},{total_samples}\n"
                    )

                    # Append to CSV and flush to disk immediately
                    with open(csv_path, "a", encoding="utf-8") as f:
                        f.write(csv_row)
                        f.flush()

                    dist_display = f"{avg_distance:.2f} m" if avg_distance is not None else "Vacant"
                    print(
                        f"[{timestamp_str}] Occupancy: {occupancy_pct:5.1f}% | "
                        f"Distance: {dist_display:<8} | "
                        f"Max Motion: {max_motion_energy:3d} | "
                        f"Light: {avg_light:5.1f} Lux ({total_samples} samples)"
                    )

                # Reset window
                minute_samples.clear()
                window_start = now

    except KeyboardInterrupt:
        print("\nStopping aggregator logger...")
    finally:
        sensor.close()
        print("Sensor connection closed.")


if __name__ == "__main__":
    main()
