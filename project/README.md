# Puzzle Solver Robot — Project Overview

An autonomous robot that picks up puzzle pieces and places them in the correct position and orientation. It combines a CNC-style gantry (3 stepper motors), a suction pick-and-place arm, a rotation servo, and a camera that detects where each piece is and how it is rotated.

---

## How It Works — Big Picture

```
Camera detects piece positions & angles
            │
            ▼
Python generates a sequence of motion commands
            │
            ▼
Commands are split into small packets and sent over USB serial
            │
            ▼
Arduino firmware receives each packet, executes it, replies ACK
            │
            ▼
Robot picks each piece, rotates it, and places it at its destination
```

---

## Project Structure

```
project/
│
├── Testings/                  ← Development & calibration tools (not production)
│   ├── camera/                ← Camera calibration workflow (4 scripts)
│   ├── communication_cpp_py/  ← Serial protocol demos (2 versions)
│   ├── pump/                  ← Pump testing scripts
│   ├── servos/
│   │   ├── servo_rotation/    ← Rotation servo tests
│   │   ├── servo_up_down/     ← Z-arm servo tests
│   │   └── README.md
│   └── steppers/
│       ├── homing/            ← Homing sequence tests
│       ├── movexy/            ← XY motion tests
│       └── README.md
│
├── firmware/                  ← Arduino firmware (production)
│   ├── puzzle_firmware.ino
│   ├── config.h
│   ├── steppers.h / .cpp
│   ├── pick_place.h / .cpp
│   ├── rotation.h / .cpp
│   ├── parser.h / .cpp
│   └── README.md
│
└── puzzle_solver/             ← Python solver scripts (production)
    ├── puzzle_solver_2.py
    ├── puzzle_solver_3.py
    ├── puzzle_solver_4.py
    ├── find_aruco_position.py
    ├── position_correction.py
    └── README_v2 / v3 / v4.md
```

---

## Hardware

| Component | Role |
|---|---|
| Arduino UNO | Runs the firmware, receives commands over USB serial |
| Stepper motor ×2 (X axis) | Dual gantry — both move together for left/right motion |
| Stepper motor ×1 (Y axis) | Forward/back motion |
| Servo — Z arm | Raises and lowers the suction arm (bit-banged PWM on pin A5) |
| Servo — rotation | Rotates the held piece before placing (pin 11) |
| Suction pump + valve | Picks pieces up (pump ON) and releases them (valve open) |
| Endstops ×2 | X and Y homing switches |
| Camera (USB webcam) | Detects ArUco marker positions and angles |
| ArUco markers | ID 0/1/2 = fixed reference frame; ID 3/4/5/6 = puzzle pieces |

---

## Part 1 — Firmware

> **Folder:** `firmware/`  
> **Detailed doc:** `firmware/README.md`

The Arduino firmware receives semicolon-delimited command packets over serial and executes them one by one. It is split into focused modules:

| File | Responsibility |
|---|---|
| `config.h` | **All tunable parameters** — pins, speeds, timing, coordinate map. Edit only this file for recalibration. |
| `steppers.h/.cpp` | Gantry motion: homing, `moveX()`, `moveY()`, `move()` |
| `pick_place.h/.cpp` | Z-arm servo + pump + valve: `pick_place(1/0)` |
| `rotation.h/.cpp` | Rotation servo: `rotate(angle)` |
| `parser.h/.cpp` | Serial protocol: tokenises packets, dispatches commands |
| `puzzle_firmware.ino` | Thin `setup()` / `loop()` that ties everything together |

### Command reference

| Command | Effect |
|---|---|
| `h` | Homing (must run first after power-on) |
| `x{pos}s{speed}` | Move X to absolute step position |
| `y{pos}s{speed}` | Move Y to absolute step position |
| `p1` | Pick: lower arm → suction ON → raise |
| `p0` | Place: lower arm → suction OFF → raise |
| `r{angle}` | Rotate piece (0–90°) |
| `d` | Pause |
| `END` | End of packet — firmware replies `OK` |

### To use

1. Open `firmware/puzzle_firmware.ino` in the Arduino IDE.
2. Upload to the Arduino UNO.
3. Keep the USB cable connected — it is both power and serial link.

---

## Part 2 — Puzzle Solver (Python)

> **Folder:** `puzzle_solver/`  
> **Detailed docs:** `README_v2.md`, `README_v3.md`, `README_v4.md`

Three versions of the Python solver, each building on the previous:

### Version 2 — Manual positions and angles

Everything is specified by hand. Useful for testing without a camera.

```python
piece_location = [ [0,1], [0,4], [2,4], [2,1] ]   # where pieces are (grid col, row)
aruco_angles   = [ -100,  100,   100,   100  ]     # how much each piece is rotated
aruco_dest     = [ [0,2], [0,3], [1,3], [1,2] ]   # where each piece should go
```

### Version 3 — Camera detects positions, angles still manual

`main_find_aruco()` is called to detect piece positions automatically. Angles are still set manually.

### Version 4 — Camera detects positions AND angles *(most complete)*

Both positions and angles come from the camera. The only manual input is the destination for each piece.

```python
coords = main_find_aruco()                           # returns (x, y, angle) per piece
piece_location = [[x, y] for x, y, _ in coords]
piece_angles   = [-angle for _, _, angle in coords]  # sign flip: camera → robot convention
```

### How the solver works

For each puzzle piece:
1. **Go to** the piece's current position
2. **Rotate** to correct orientation (`rotation_management()` handles angles > 90° automatically with multi-step pick-rotate-place sequences)
3. **Go to** the destination
4. **Place** the piece and reset rotation to 0°

The full instruction string is split into small packets (`PACKET_SIZE` characters) and sent one at a time, waiting for `ACK` before sending the next. The Arduino replies `OK` when it sees `END`.

### To use

```bash
pip install pyserial opencv-contrib-python numpy

# Set your COM port at the top of the script:
PORT = "COM7"

python puzzle_solver_4.py
```

---

## Part 3 — Camera Pipeline

> **Used by:** `puzzle_solver_3.py`, `puzzle_solver_4.py`  
> **Files:** `find_aruco_position.py`, `position_correction.py`

### `find_aruco_position.py` — `main_find_aruco()`

The entry point for all camera detection. For each puzzle piece marker (IDs 3–6) it:

1. Grabs frames from the webcam
2. Applies the full image pipeline: **undistort → crop → zoom → sharpen**
3. Detects all ArUco markers in the frame
4. Builds a coordinate system from the three fixed reference markers (IDs 0, 1, 2)
5. Converts the piece marker's pixel position to real-world coordinates
6. Averages over 70 frames to reduce noise
7. Applies TPS position correction (`position_correction.py`)
8. *(v4 only)* Measures the piece's rotation angle relative to the origin marker

Returns a list of `(x, y)` (v3) or `(x, y, angle)` (v4) for each piece.

### `position_correction.py` — `correct_position(x, y)`

Even after lens undistortion, camera coordinates contain small but systematic errors across the workspace. This is corrected with a **Thin Plate Spline (TPS)** warp — a smooth interpolant fitted on a 4×4 calibration grid of known positions.

At runtime: raw `(x, y)` from the camera → `correct_position(x, y)` → corrected `(x, y)` passed to the solver.

To recalibrate: place ArUco markers at exact known grid positions, measure their detected coordinates, and update `MEASURED_POINTS` in `position_correction.py`.

### Angle detection (v4)

Each ArUco marker has four corners in a fixed order (TL, TR, BR, BL). The top edge (TL→TR) and left edge (TL→BL) define two perpendicular axes. The piece's angle is measured relative to the origin marker (ID 0) — so camera tilt is automatically cancelled. Both axes are wrapped to [−90°, 90°] (the 180° ambiguity limit of ArUco), and the one with the smaller absolute value is returned.

---

## Part 4 — Testings

> **Folder:** `Testings/`

Standalone scripts used during development. **Not needed to run the solver** — kept for reference and future recalibration.

### `camera/` — Camera calibration tools

Run these once per camera / mounting position, in order:

| Script | Purpose |
|---|---|
| `camera_calib.py` | Compute `CAMERA_MATRIX` and `DIST_COEFFS` from a printed checkerboard |
| `test_calib_1.py` | Live side-by-side view: distorted vs undistorted — quick visual check |
| `test_calib_2.py` | Interactive slider tuner for every calibration parameter |
| `crop_zoom_sharpen.py` | Preview the full production pipeline (undistort → crop → zoom → sharpen) |

> See `Testings/camera/README.md` for the full calibration workflow.

### `communication_cpp_py/` — Serial protocol demos

Two demos that established the communication protocol now used in the firmware:

| Files | Purpose |
|---|---|
| `comm_v1_cpp_py.cpp/.py` | Interactive terminal: type commands, send with `s`, Arduino echoes back |
| `comm_v2_cpp_py.cpp/.py` | Automated packet sender with ACK handshake — the protocol used in production |

In both: upload the `.cpp` to the Arduino first, then run the `.py`. See `Testings/communication_cpp_py/README.md`.

### `servos/` and `steppers/`

Isolated test scripts for each hardware component — used to verify wiring, calibrate movement ranges, and tune homing behaviour independently before integrating everything into the firmware.

---

## Setup — From Zero to Running

### 1. Install Python dependencies

```bash
pip install pyserial opencv-contrib-python numpy
```

### 2. Calibrate the camera *(if not already done)*

```bash
cd Testings/camera
python camera_calib.py       # follow on-screen instructions
python test_calib_1.py       # visually verify
```

Copy the printed `CAMERA_MATRIX` and `DIST_COEFFS` into `find_aruco_position.py`.

### 3. Upload the firmware

- Open `firmware/puzzle_firmware.ino` in the Arduino IDE
- Upload to the Arduino UNO
- Note the COM port (e.g. `COM7`)
- Close the Serial Monitor

### 4. Configure and run the solver

Open `puzzle_solver_4.py` and set:

```python
PORT       = "COM7"          # your Arduino COM port
piece_dest = [ [1,1], [1,2], [1,3], [1,4] ]   # destination for each piece
```

Then run:

```bash
python puzzle_solver_4.py
```

The robot will:
1. Home the gantry
2. Move out of the camera's view
3. Detect piece positions and angles via camera
4. Pick, rotate, and place each piece

---

## Dependencies Summary

| Library | Used by | Install |
|---|---|---|
| `pyserial` | All puzzle_solver scripts | `pip install pyserial` |
| `opencv-contrib-python` | Camera scripts, find_aruco | `pip install opencv-contrib-python` |
| `numpy` | Camera scripts, position correction | `pip install numpy` |
| `AccelStepper` | Arduino firmware | Arduino Library Manager |
| `Servo` | Arduino firmware | Built-in Arduino library |
