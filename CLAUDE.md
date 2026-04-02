# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Control system for large-scale LED neon sign installations with animated effects. Two primary installations:
- "BLACK LIVES MATTER" sign at Rising Sun Center (Emeryville, visible from I-580)
- "K(NO)W JUSTICE, K(NO)W PEACE" animated installation at Oakland City Hall (200+ feet of LEDs on 20 letters)

Python manages illumination and animation via I2C or PWM hardware drivers, with OSC network control (TouchOSC mobile app or any OSC client).

## Commands

```bash
# Install dependencies
cd blmcontrol
pip install -r requirements.txt

# Run standard I2C-based control
python3 -m blmcontrol.blmcontrol --ip 192.168.86.42 --animate_intervals 30 30 30 30 30 30

# Run PWM-based control
python3 -m blmcontrol.pwmcontrol --ip 10.0.0.103 --port 9999 --mobile_ip 10.0.0.101 --mobile_port 9999

# Run tests
cd blmcontrol && python -m pytest test/

# Run a single test file
python -m pytest test/test_animation_order.py
```

## Key CLI Arguments

- `--ip` / `--port`: OSC server bind address (default: 10.0.0.103:9999)
- `--on_offset`: Minutes before sunset to activate (negative = earlier; default: -120)
- `--end_time`: Hard cutoff time HH:MM regardless of sunset (default: 7:15)
- `--animate_intervals`: Per-animation durations (count must match `ANIMATION_ORDER` length)
- `--enable_sun`: Use solar-based on/off (0/1, default: 1)
- `--signal`: Enable buzzer feedback on startup/commands

## Architecture

### Control Flow

```
TouchOSC mobile app / OSC client
        ↓ UDP/OSC
blmcontrol.py (asyncio OSC server)
        ↓
animation_utils.py (push_data abstraction)
        ↓                    ↓
SMBus/I2C (MCP23017)   PCA9685 (PWM)
addresses 0x26, 0x27   address 0x40
        ↓                    ↓
         Physical LED hardware
```

### Animation System

Each animation file defines:
1. Letter bitmasks (e.g., `BLACK_B = 0x0001`, `BLACK_L = 0x0002`)
2. Word/phrase combinations (bitwise OR of letter bits)
3. Animation functions that call `push_data()` with timing delays
4. A `set_display_maps()` function to populate the global `DISPLAY_MAPS` dict

Animations are registered in `ANIMATION_ORDER` (a dict mapping int → function). The main loop auto-advances through these based on `--animate_intervals`.

**Animation files:**
- `animations.py` — "BLACK LIVES MATTER" (16-letter, I2C)
- `animation_justice_peace.py` — "K(NO)W JUSTICE, K(NO)W PEACE" (I2C)
- `animation_pwm_justice_peace.py` — same, with smooth PWM fades
- `animation_tara_reid.py`, `animation_patrick.py`, `animation_vandy.py` — custom variants
- `animations_wedding.py`, `animation_hose.py` — specialized installations

To add a new animation: write the function, add it to `ANIMATION_ORDER` in the relevant animation module.

### Hardware Abstraction (`animation_utils.py`)

`push_data(value, hands=0xFF)` is the core abstraction:
- If PWM driver is available: calls `pwm.set_pwm()` with gamma correction (`val^(1/0.4)`)
- If SMBus is available: writes to MCP23017 I/O expanders at 0x26/0x27
- `value` is a 32-bit integer; each bit controls one LED/letter

**I2C hardware:** MCP23017 chips, registers OLATA/OLATB (0x14/0x15) for output  
**PWM hardware:** PCA9685 at 0x40, 16 channels, 200 Hz, 12-bit resolution  
**GPIO:** Pin 12 = buzzer feedback

### Solar Timing (`earth_data/earth_data.py`)

Loads pre-computed sunrise/sunset data from `sunriseSunset.txt`. The `lights_out()` function determines display state based on `on_offset` and `hard_off` parameters. Tests in `test/test_on_off.py` mock time for solar timing logic.

### OSC Message Handlers

- `/letter/*` — toggle individual letters
- `/word/*` — toggle words
- `/full` — full display on
- `/animation/*` — queue animation by number
- `/parameter/*` — adjust timing parameters
- `/bpm` (PWM variant) — adjust tempo

### Global State (main loop)

```python
QUEUE = {
    "animations": [],       # pending animation indices
    "last_request": datetime,
    "current_animation": 1  # auto-play index
}
```

Main loop: check solar timing → process queue → auto-advance animation → sleep 1s → repeat.

## Deployment

The system runs as a systemd service (`blm-sign.service`) started by `startup.sh`. The service runs as root and restarts automatically.