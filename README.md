# sys_knobs — Volume & Brightness Control via Hardware Knobs

A custom Linux kernel character device driver that lets you control your system's volume and display brightness in real time using two physical rotary potentiometers wired to an Arduino Nano.

Built as part of **CS F372: Operating Systems** at BITS Pilani.

---

## How It Works

The system spans three layers:

```
[Potentiometers] → [Arduino Nano] → (USB Serial) → [serial_bridge.py]
                                                           ↓
                                                   /dev/sys_knobs   ← sys_knobs.ko (kernel driver)
                                                           ↓
                                                   [knobs_daemon.py]
                                                           ↓
                                          wpctl/pactl (audio) · brightnessctl (display)
```

- **Hardware Layer** — An Arduino Nano reads two potentiometers over analog pins A0 (volume) and A2 (brightness). It transmits data over USB serial only when a value changes, keeping the bus quiet.
- **Kernel Layer** — `sys_knobs.c` is a loadable kernel module that registers a character device at `/dev/sys_knobs`. It acts as a shared memory buffer between the serial bridge and the daemon.
- **User-Space Layer** — Two Python services run concurrently:
  - `serial_bridge.py` reads raw `V:XX B:XX` frames from `/dev/ttyUSB0` and writes them to the driver.
  - `knobs_daemon.py` polls the driver and calls `wpctl`/`pactl` or `brightnessctl` to apply the changes.

---

## Repository Structure

```
os-device-driver-project/
├── arduino_code/        # Arduino sketch (.ino) for the ATmega328p
├── driver/
│   ├── sys_knobs.c      # Linux kernel character device driver
│   └── Makefile
└── userspace/
    ├── serial_bridge.py # Reads serial → writes to /dev/sys_knobs
    └── knobs_daemon.py  # Reads /dev/sys_knobs → calls system APIs
```

---

## Hardware

**Parts needed:**
- Arduino Nano (ATmega328p)
- 2× rotary potentiometers (any value, 10kΩ recommended)
- USB-A to Mini-B cable
- Optional: 3D-printed enclosure

**Wiring:**

| Arduino Pin | Connection |
|-------------|------------|
| A0 | Middle (wiper) pin of Pot 1 — Volume |
| A2 | Middle (wiper) pin of Pot 2 — Brightness |
| 5V | One outer pin of **both** pots |
| GND | Other outer pin of **both** pots |
| USB | USB cable to PC |

---

## Setup & Usage

### Prerequisites

- Linux (tested on Fedora with kernel 6.19)
- Kernel headers for your running kernel
- `python3`, `pyserial`
- `wpctl` or `pactl` (PipeWire/PulseAudio) for audio control
- `brightnessctl` for display brightness control

```bash
# Install Python dependency
pip install pyserial

# Install brightnessctl (Fedora example)
sudo dnf install brightnessctl
```

### Step 1 — Flash the Arduino

Open `arduino_code/` in the Arduino IDE and upload the sketch to your Nano. Connect it via USB.

### Step 2 — Build the Kernel Module

```bash
cd driver/
make
```

### Step 3 — Load the Module

```bash
sudo insmod sys_knobs.ko

# Verify it loaded
cat /proc/devices | grep sys_knobs
cat /proc/modules | grep sys_knobs
```

### Step 4 — Create the Device Node

```bash
# Replace 506 with the major number shown in /proc/devices
sudo mknod /dev/sys_knobs c 506 0
sudo chmod a+rw /dev/sys_knobs
```

### Step 5 — Run the Serial Bridge

```bash
cd userspace/
python3 serial_bridge.py
```

This will wait for the Arduino to initialise and then begin forwarding potentiometer readings to `/dev/sys_knobs`.

### Step 6 — Run the Knobs Daemon (separate terminal)

```bash
cd userspace/
python3 knobs_daemon.py
```

Turn the knobs — volume and brightness will update in real time.

---

## Removing the Module

```bash
sudo rmmod sys_knobs
sudo rm /dev/sys_knobs
```

---

## License

This project was submitted for academic evaluation at BITS Pilani. Feel free to use it as a reference for your own kernel module or embedded Linux projects.

---

## Note on LLM Usage

This README has entirely generated using an LLM and human reviewed. Auto-complete feature within VSCode (using Copilot) to assist code writing.
