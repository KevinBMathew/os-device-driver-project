#!/usr/bin/env python3

#Usage:
#    sudo python3 serial_bridge.py [--port /dev/ttyUSB0] [--baud 9600]

import serial
import time
import argparse
import sys
import os

SERIAL_PORT  = "/dev/ttyUSB0" #default serial port. you can change using --port argument in command line
BAUD_RATE    = 9600
DEVICE_FILE  = "/dev/sys_knobs"
READY_TOKEN  = "SYS_KNOBS_READY"


def parse_args():
    parser = argparse.ArgumentParser(description="SysKnobs Serial Bridge")
    parser.add_argument("--port", default=SERIAL_PORT,
                        help=f"Serial port (default: {SERIAL_PORT})")
    parser.add_argument("--baud", type=int, default=BAUD_RATE,
                        help=f"Baud rate (default: {BAUD_RATE})")
    parser.add_argument("--device", default=DEVICE_FILE,
                        help=f"Kernel device file (default: {DEVICE_FILE})")
    return parser.parse_args()


def validate_env(device_file):
    """Check device node exists before starting the main loop."""
    if not os.path.exists(device_file):
        print(f"[ERROR] Device file '{device_file}' not found.")
        print("        Load the kernel module and create the device node first:")
        print("          sudo insmod driver/sys_knobs.ko")
        print("          sudo mknod /dev/sys_knobs c <MAJOR> 0")
        print("          sudo chmod a+rw /dev/sys_knobs")
        sys.exit(1)


def is_valid_data(line: str) -> bool:
    """Accept lines that look like  'V:75 B:50'."""
    parts = line.split()
    if len(parts) != 2:
        return False
    return parts[0].startswith("V:") and parts[1].startswith("B:")


def main():
    args = parse_args()
    validate_env(args.device)

    print(f"[INFO] Opening serial port {args.port} at {args.baud} baud …")
    try:
        ser = serial.Serial(args.port, args.baud, timeout=2)
    except serial.SerialException as e:
        print(f"[ERROR] Cannot open serial port: {e}")
        print("        Is the Arduino connected? Try: ls /dev/ttyUSB*")
        sys.exit(1)

    # waiting for the Arduino to reset and send the READY_TOKEN
    print("[INFO] Waiting for Arduino …")
    time.sleep(2)
    ser.reset_input_buffer()

    print(f"[INFO] Bridge running. Writing to {args.device}")
    print("[INFO] Press Ctrl+C to stop.\n")

    while True:
        try:
            raw = ser.readline()
            line = raw.decode("utf-8", errors="ignore").strip()

            if not line:
                continue

            # skipping hanshaking
            if line == READY_TOKEN:
                print(f"[INFO] Arduino ready.")
                continue

            if not is_valid_data(line):
                print(f"[SKIP] Unexpected data: '{line}'")
                continue

            # putting the data to the devie file
            with open(args.device, "w") as dev:
                dev.write(line)

            print(f"[→ driver] {line}")

        except KeyboardInterrupt:
            print("\n[INFO] Bridge stopped.")
            break
        except OSError as e:
            print(f"[ERROR] Device write failed: {e}")
            time.sleep(1)

    ser.close()


if __name__ == "__main__":
    main()
