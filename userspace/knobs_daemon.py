#!/usr/bin/env python3

#Usage:
#    python3 knobs_daemon.py [--device /dev/sys_knobs] [--interval 0.1]


import subprocess
import time
import glob
import argparse
import sys
import os

DEVICE_FILE   = "/dev/sys_knobs"
POLL_INTERVAL = 0.1   # seconds between reads


#argument parsing and environment validation
def parse_args():
    parser = argparse.ArgumentParser(description="SysKnobs User-Space Daemon")
    parser.add_argument("--device", default=DEVICE_FILE,
                        help=f"Kernel device file (default: {DEVICE_FILE})")
    parser.add_argument("--interval", type=float, default=POLL_INTERVAL,
                        help=f"Poll interval in seconds (default: {POLL_INTERVAL})")
    return parser.parse_args()


#volume control
def set_volume(pct: int):
    """
    Set the default PipeWire sink volume using wpctl.
    pct is 0–100.  wpctl accepts a normalised float (0.0–1.0).
    """
    normalised = round(pct / 100.0, 2)
    result = subprocess.run(
        ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{normalised}"],
        capture_output=True
    )
    if result.returncode != 0:
        #fall back to pactl if wpctl fails (e.g. on non-KDE desktops)
        subprocess.run(
            ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{pct}%"],
            capture_output=True
        )


#brightness control (sysfs or brightnessctl)

def _find_backlight_dir() -> str | None:
    """Return the sysfs backlight directory, preferring non-'acpi' entries."""
    dirs = glob.glob("/sys/class/backlight/*/max_brightness")
    if not dirs:
        return None
    preferred = [d for d in dirs if "acpi" not in d]
    chosen = preferred[0] if preferred else dirs[0]
    return chosen.replace("/max_brightness", "")


def set_brightness(pct: int):
    """
    Set screen brightness.
    First tries sysfs (requires udev rule or root), then falls back to
    brightnessctl which handles the permissions itself.
    pct is 0–100.
    """
    pct = max(pct, 5) #keeping brightness above 5% to avoid screen going black

    backlight_dir = _find_backlight_dir()

    if backlight_dir:
        max_brightness_path = f"{backlight_dir}/max_brightness"
        brightness_path     = f"{backlight_dir}/brightness"

        try:
            with open(max_brightness_path) as f:
                max_b = int(f.read().strip())
            value = max(1, int(max_b * pct / 100))
            with open(brightness_path, "w") as f:
                f.write(str(value))
            return  # success via sysfs
        except PermissionError:
            pass    # fall through to brightnessctl

    # Fallback: brightnessctl
    subprocess.run(["brightnessctl", "s", f"{pct}%"], capture_output=True)


#data parsing
def parse_knobs(data: str) -> tuple[int | None, int | None]:
    """
    Parse 'V:75 B:50' → (75, 50).
    Returns (None, None) if the format is unexpected.
    """
    vol = bri = None
    for token in data.split():
        try:
            if token.startswith("V:"):
                vol = int(token[2:])
            elif token.startswith("B:"):
                bri = int(token[2:])
        except ValueError:
            pass
    return vol, bri


# main loop
def main():
    args = parse_args()

    if not os.path.exists(args.device):
        print(f"[ERROR] Device file '{args.device}' not found.")
        print("        Make sure the kernel module is loaded and the node created.")
        sys.exit(1)

    print(f"[INFO] Daemon started. Reading from {args.device}")
    print("[INFO] Press Ctrl+C to stop.\n")

    last_vol: int | None = None
    last_bri: int | None = None

    while True:
        try:
            with open(args.device, "r") as dev:
                raw = dev.read().strip()

            if raw:
                vol, bri = parse_knobs(raw)

                if vol is not None and vol != last_vol:
                    set_volume(vol)
                    print(f"[volume]     {vol}%")
                    last_vol = vol

                if bri is not None and bri != last_bri:
                    set_brightness(bri)
                    print(f"[brightness] {bri}%")
                    last_bri = bri

        except KeyboardInterrupt:
            print("\n[INFO] Daemon stopped.")
            break
        except OSError as e:
            print(f"[ERROR] Read failed: {e}")

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
