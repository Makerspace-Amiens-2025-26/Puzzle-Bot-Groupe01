# Puzzle Solver 3 — Camera-Assisted Controller

Python controller for the puzzle-solving robot — **Version 3**.  
Same pick-place-rotate logic as v2, but piece positions are now **detected automatically by camera** using ArUco markers, instead of being entered manually.

> **Angle detection is not yet camera-assisted.**  
> Piece angles (`piece_angles[]`) are still set manually.

---

## What's New vs Version 2

| Feature | v2 | v3 |
|---|---|---|
| Piece positions | Manual (`piece_location[]`) | **Camera — ArUco detection** |
| Piece angles | Manual | Manual (unchanged) |
| Destinations | Manual | Manual (unchanged) |
| Extra dependencies | `pyserial` | `pyserial`, `opencv-python`, `numpy` |

---

## How It Works

### Overview

```
puzzle_solver_3.py
      │
      ├─ main()
      │     │
      │     ├─ 1. Move gantry to a safe position for camera capture
      │     │       (sends "h;r0;x13000s200;END" before opening camera)
      │     │
      │     └─ 2. generate_instructions()
      │               │
      │               ├─ main_find_aruco()          ← camera step
      │               │       │
      │               │       ├─ Opens webcam (CAMERA_INDEX)
      │               │       ├─ For each puzzle piece marker (IDs 3,4,5,6):
      │               │       │     - Collects NUM_FRAMES_AVERAGE frames
      │               │       │     - Builds coordinate system from ref markers (0,1,2)
      │               │       │     - Averages pixel position → real-world coord
      │               │       │     - Applies TPS position correction
      │               │       │     - Returns (corrected_x, corrected_y)
      │               │       └─ Returns list of 4 real-world positions
      │               │
      │               └─ for each piece i:
      │                       goto(piece_location[i])       ← detected position
      │                       rotation_management(angle[i]) ← manual angle
      │                       goto(piece_dest[i])
      │                       place()
      │                       rotate(0)
```

### Coordinate system

Three fixed ArUco reference markers (IDs 0, 1, 2) are mounted on the machine frame:

| Marker | Role | Real position |
|---|---|---|
| ID 0 | Origin | (0, 0) |
| ID 1 | X-axis reference | (REAL_UNIT, 0) |
| ID 2 | Y-axis reference | (0, REAL_UNIT) |

All three must be visible to the camera at all times during detection.  
Puzzle pieces carry markers **IDs 3, 4, 5, 6**.

### Camera pipeline (5 stages)

Each frame passes through up to 5 processing steps before coordinate extraction:

| Stage | Processing |
|---|---|
| 1 | Raw capture only |
| 2 | + Lens undistortion |
| 3 | + Crop around reference markers |
| 4 | + Zoom to output resolution |
| 5 | + Unsharp-mask sharpening ← **default (production)** |

Set `DEBUG_STAGE` in `find_aruco_position.py` to a lower value to inspect intermediate steps.

### Position correction (Thin Plate Spline)

Raw camera coordinates contain systematic distortion even after lens undistortion.  
`position_correction.py` applies a **Thin Plate Spline (TPS)** warp fitted on a 4×4 calibration grid (`MEASURED_POINTS` → `TRUE_POINTS`) to remap detected positions to their true grid coordinates.

---

## File Structure

```
puzzle_folder/
├── puzzle_solver_3.py       ← main script
├── find_aruco_position.py   ← camera detection pipeline
└── position_correction.py  ← TPS position correction model

firmware/
├── puzzle_firmware.ino
├── config.h
├── steppers.h / .cpp
├── pick_place.h / .cpp
├── rotation.h / .cpp
├── parser.h / .cpp
└── README.md
```

---

## Setup

### 1 — Install dependencies

```bash
pip install pyserial opencv-python numpy
```

### 2 — Upload the firmware

1. Open `firmware/puzzle_firmware.ino` in the Arduino IDE.
2. Upload it to the Arduino UNO.
3. Open the **Serial Monitor** (115200 baud) and confirm the firmware prints:
   ```
   Firmware ready. Send commands: ...
   ```
4. Note the COM port (e.g. `COM7` on Windows, `/dev/ttyUSB0` on Linux).
5. **Close the Serial Monitor** — it must be closed before running Python.

> Keep the USB cable connected while Python is running. It carries both power and serial data.

### 3 — Configure the script

Open `puzzle_solver_3.py` and set the serial port:

```python
PORT = "COM7"   # ← your Arduino COM port
```

Open `find_aruco_position.py` and check the camera index:

```python
CAMERA_INDEX = 1   # ← 0 = built-in webcam, 1 = first external camera, etc.
```

### 4 — Set piece angles and destinations

Still configured manually at the top of `puzzle_solver_3.py`:

```python
# Rotation angle of each piece in degrees (camera detection not yet implemented)
# Positive = clockwise, negative = counter-clockwise, max hardware range = 90°
# rotation_management() handles multi-step rotations automatically for |angle| > 90°
piece_angles = [ 0,  0,  0,  0 ]

# Destination grid cell for each piece  (col, row), 0-indexed
piece_dest   = [ [1,1], [1,2], [1,3], [1,4] ]
```

`piece_angles[i]` and `piece_dest[i]` correspond to the piece carrying **ArUco marker ID** `ARUCO_TO_FIND[i]`.  
The default marker IDs to find are set in `find_aruco_position.py`:

```python
ARUCO_TO_FIND = [3, 4, 5, 6]
```

---

## Running

```bash
python puzzle_solver_3.py
```

### What you will see

**Step 1 — gantry moves to camera position:**
```
[i] Full string:
h;r0;x13000s200;END

[→] Sending packet 0: 'h;r0;'
[←] Arduino: ACK0
...
[✓] All instructions completed.
```

**Step 2 — camera opens, one window per marker:**

A live preview window appears for each piece marker in turn (IDs 3 → 4 → 5 → 6).  
The window title shows the current pipeline stage and sample count:

```
find_aruco  ID=3  |  stage 5: UNDISTORT+CROP+ZOOM+SHARPEN  |  Q=quit
```

Progress is printed in the terminal:
```
[find_aruco] Searching for marker ID=3 ...
  sample   1/70  →  pixel (412, 305)   real (1.0667, 0.9699)
  sample   2/70  →  ...
  ...
{"3 ==> 1.0023, 1.0011"}
```

Once all 4 markers are found, a summary table is printed:
```
============================================================
 RESULTS
============================================================
  Marker ID      Real X      Real Y  Status
  ------------  ----------  ----------  ------------
  ID 3            1.0023      1.0011  OK
  ID 4            2.0041      3.0087  OK
  ID 5            4.0012      2.9934  OK
  ID 6            3.0091      0.9978  OK
============================================================
```

**Step 3 — gantry executes the solve:**
```
[i] Full string:
h;r0;x100s200;y196s200;p1;...;h;END;

[→] Sending packet 0: ...
[←] Arduino: ACK0
...
[✓] All instructions completed.
```

### Interrupting during detection

Press **Q** in the camera window to abort detection for the current marker.

---

## Calibration

### Camera intrinsics

The lens calibration matrix and distortion coefficients are hardcoded in `find_aruco_position.py`:

```python
CAMERA_MATRIX = np.array([...])
DIST_COEFFS   = np.array([...])
```

To recalibrate for a different camera, run a standard OpenCV chessboard calibration and replace these values.

### Position correction (TPS)

`position_correction.py` contains `MEASURED_POINTS` and `TRUE_POINTS` — a 4×4 grid of camera-measured vs. true positions used to fit the TPS warp.  
To recalibrate: place known ArUco markers at exact grid positions, measure their detected coordinates, and update the arrays.

---

## Serial Protocol (summary)

| Direction | Message | Meaning |
|---|---|---|
| Python → Arduino | `h;x100s200;y196s200;p1;` | Packet of semicolon-delimited commands |
| Arduino → Python | `ACK{n}` | Packet `n` done, send next |
| Arduino → Python | `OK` | `END` received — all done |
| Arduino → Python | `ERROR: ...` | Unknown or malformed command |

Full command reference is in `firmware/README.md`.

---

## Known Limitations / TODO

- [ ] Angle detection by camera not yet implemented — `piece_angles[]` is manual.
- [ ] If a marker is not visible when detection starts, the script blocks indefinitely (no timeout in `find_aruco()`).
- [ ] `goto()` in v3 computes step counts from real-world coordinates directly (using `STEPS_PER_MM_X/Y`), bypassing the `coord_map` table used in v2.
