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

## File Structure

```
puzzle_folder/
├── puzzle_solver_3.py       ← main script: orchestrates everything
├── find_aruco_position.py   ← camera pipeline; the objective is main_find_aruco()
├── position_correction.py  ← TPS correction called inside find_aruco_position.py
└── position_correction_2.py  ← Cubic Wrap, optional to use instead of TPS

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

## How It Works

### Full pipeline

```
puzzle_solver_3.py  –  main()
      │
      ├─ Phase 1: move gantry out of camera frame
      │     └─ sends "h;r0;x13000s200;END" via serial
      │         (gantry must not obstruct camera view during detection)
      │
      └─ Phase 2: generate_instructions()
            │
            ├─ find_aruco_position.py  –  main_find_aruco()       ← CAMERA STEP
            │       │
            │       │   Opens webcam, builds undistortion maps once,
            │       │   then loops over each piece marker (IDs 3, 4, 5, 6):
            │       │
            │       └─ find_aruco(id)  ×4
            │               │
            │               │  For each frame (repeated NUM_FRAMES_AVERAGE=70 times):
            │               │
            │               ├─ 1. Grab raw frame from camera
            │               │
            │               ├─ 2. find_aruco_position.py  –  apply_pipeline()
            │               │        Stage 1  raw frame
            │               │        Stage 2  + lens undistortion   (cv2.remap)
            │               │        Stage 3  + crop around ref markers (IDs 0,1,2)
            │               │        Stage 4  + zoom to 1280×720
            │               │        Stage 5  + unsharp-mask sharpen  ← default
            │               │       (display only; coordinate math always uses full pipeline)
            │               │
            │               ├─ 3. Detect all ArUco markers on undistorted frame
            │               │       └─ requires IDs 0, 1, 2 (reference) + target ID
            │               │
            │               ├─ 4. find_aruco_position.py  –  build_coordinate_system_from_frame()
            │               │        ID 0 → origin (0, 0)
            │               │        ID 1 → X-axis ref  →  scale_x = REAL_UNIT / pixel_dist
            │               │        ID 2 → Y-axis ref  →  scale_y = REAL_UNIT / pixel_dist
            │               │
            │               ├─ 5. find_aruco_position.py  –  pixel_to_real()
            │               │        (pixel_x − origin_x) × scale_x  →  real_x
            │               │        (pixel_y − origin_y) × scale_y  →  real_y  (Y flipped)
            │               │
            │               ├─ 6. Accumulate sample  →  average over 70 frames
            │               │
            │               └─ 7. position_correction.py  –  correct_position()
            │                        TPS warp:  raw_avg  →  corrected (x, y)
            │                        returns final position for this marker
            │
            │       main_find_aruco() returns: [ (x0,y0), (x1,y1), (x2,y2), (x3,y3) ]
            │                                    piece 0    piece 1    piece 2    piece 3
            │
            └─ for each piece i:
                    goto(piece_location[i])        ← detected real-world position
                    rotation_management(angle[i])  ← manual angle (see Rotation section), pick() included
                    goto(piece_dest[i])
                    place()
                    rotate(0)
```

### Coordinate system

Three ArUco markers are fixed to the machine frame and define the reference coordinate system:

| Marker ID | Role | Real-world position |
|---|---|---|
| 0 | Origin | (0, 0) |
| 1 | X-axis reference | (REAL_UNIT, 0) |
| 2 | Y-axis reference | (0, REAL_UNIT) |

`REAL_UNIT = 4` (the physical distance between reference markers, in the same unit as your grid).  
All three must be **visible at all times** during detection. If any disappears, the frame is skipped.

Puzzle pieces carry markers **IDs 3, 4, 5, 6** (set in `ARUCO_TO_FIND`).

### `position_correction.py` — why it exists and how it works

Even after lens undistortion, raw camera coordinates carry a small but meaningful systematic error — caused by perspective, camera mounting angle, and residual optical distortion. At the robot's precision requirements, this error is large enough to mis-position the gantry.

**The fix:** a Thin Plate Spline (TPS) warp, fitted once from a calibration grid.

```
Calibration step (done once, results hardcoded):
    Place ArUco markers at exact known grid positions (1,1) → (4,4)
    Detect their camera positions  →  MEASURED_POINTS  (16 points, 4×4 grid)
    Record their true positions    →  TRUE_POINTS       (integer grid coords)
    Fit TPS:  MEASURED_POINTS  →  TRUE_POINTS

At runtime (called inside find_aruco for every detected piece):
    raw_avg  (float, from pixel_to_real + averaging)
         │
         └─  correct_position(x, y)
                   │
                   └─  TPS.correct(x, y)
                             │
                             ├─ affine part:   a0 + a1·x + a2·y
                             └─ radial part:   Σ wᵢ · U(‖p − pᵢ‖)
                                               where U(r) = r²·log(r)
                             │
                             └─ returns (corrected_x, corrected_y)
```

The TPS is a smooth interpolant: it passes exactly through all 16 calibration points and bends smoothly between them. It handles non-uniform distortion (errors that vary across the workspace) that a simple affine correction would miss.

To recalibrate: place markers at exact grid positions, run detection to get new `MEASURED_POINTS`, and update the array in `position_correction.py`.

### Camera pipeline debug stages

Set `DEBUG_STAGE` in `find_aruco_position.py` to inspect intermediate steps at runtime:

| Value | What you see in the window |
|---|---|
| 1 | Raw frame — use first to verify camera is working |
| 2 | After lens undistortion |
| 3 | Undistorted + crop rectangle around reference markers |
| 4 | Cropped and zoomed to 1280×720 |
| 5 | Full pipeline + unsharp-mask sharpening ← **default** |

> Changing `DEBUG_STAGE` only affects the **display**. Coordinate math always runs the full pipeline regardless. The code was written thus to make it easier to debug.

### Rotation management

The rotation servo has a hardware limit of **90°**. For angles beyond that, `rotation_management()` breaks the rotation into multiple pick-place-rotate steps automatically:

| Angle | Strategy |
|---|---|
| `0` | Pick only |
| `0 < angle ≤ 90` | Pick → rotate(angle) |
| `90 < angle ≤ 180` | Pick → rotate(90) → place → rotate(0) → pick → rotate(angle−90) |
| `−90 ≤ angle < 0` | rotate(−angle) → pick → rotate(0) |
| `−180 ≤ angle < −90` | rotate(90) → pick → rotate(0) → place → rotate(−angle−90) → pick → rotate(0) |
| `±180` | Two 90° half-turns |

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
4. Note the COM port shown in the IDE (e.g. `COM7` on Windows, `/dev/ttyUSB0` on Linux).
5. **Close the Serial Monitor** before running Python — only one program can use the port at a time.

> Keep the USB cable connected while Python is running. It carries both power and serial data.

### 3 — Configure

Open `puzzle_solver_3.py`:

```python
PORT = "COM7"   # ← your Arduino COM port
```

Open `find_aruco_position.py`:

```python
CAMERA_INDEX  = 1    # ← 0 = built-in webcam, 1 = first external camera
DEBUG_STAGE   = 5    # ← lower to 1–4 to inspect pipeline steps
ARUCO_TO_FIND = [3, 4, 5, 6]   # ← marker IDs attached to the puzzle pieces
```


### 4 — Set piece angles and destinations

Still configured manually in `puzzle_solver_3.py`:

```python
# Angle of each piece in degrees — index matches ARUCO_TO_FIND order
# Positive = clockwise, negative = counter-clockwise
# rotation_management() handles |angle| > 90° automatically
piece_angles = [ 0,  0,  0,  0 ]

# Destination grid cell for each piece (col, row), 0-indexed
piece_dest   = [ [1,1], [1,2], [1,3], [1,4] ]
```

---

## Running

```bash
python find_aruco_position.py
```

Before Solving : 
<br><br>

![Alt text](https://github.com/Makerspace-Amiens-2025-26/Puzzle-Bot-Groupe01/blob/main/docs/images/puzzle_unsolved_3_py.png)

Through Solving : 
<br><br>

![Alt text](https://github.com/Makerspace-Amiens-2025-26/Puzzle-Bot-Groupe01/blob/main/docs/images/through_solving_3_1.png)
<br><br>

![Alt text](https://github.com/Makerspace-Amiens-2025-26/Puzzle-Bot-Groupe01/blob/main/docs/images/through_solving_3_2.png)
<br><br>

![Alt text](https://github.com/Makerspace-Amiens-2025-26/Puzzle-Bot-Groupe01/blob/main/docs/images/through_solving_3_3.png)
<br><br>




## Running

```bash
python puzzle_solver_3.py
```

**Phase 1 — gantry clears the camera frame:**
```
[→] Sending packet 0: 'h;r0;'
[←] Arduino: ACK0
...
[✓] All instructions completed.
```

**Phase 2 — detection, one window per marker (IDs 3 → 4 → 5 → 6):**
```
[find_aruco] Searching for marker ID=3 ...
  sample   1/70  →  pixel (412, 305)   real (1.0667, 0.9699)
  ...
{"3 ==> 1.0023, 1.0011"}
```

Summary table after all markers are found:
```
============================================================
 RESULTS
============================================================
  Marker ID      Real X      Real Y  Status
  ID 3            1.0023      1.0011  OK
  ID 4            2.0041      3.0087  OK
  ID 5            4.0012      2.9934  OK
  ID 6            3.0091      0.9978  OK
============================================================
```

**Phase 3 — gantry executes the solve:**
```
[→] Sending packet 0: 'h;r0;'
[←] Arduino: ACK0
...
[✓] All instructions completed.
```

Press **Q** in the camera window to abort detection for the current marker.

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
- [ ] If a marker is not visible when detection starts, `find_aruco()` blocks indefinitely (no timeout).
- [ ] `goto()` in v3 computes step counts from real-world floats directly (`STEPS_PER_MM_X/Y × MM_PER_UNIT`), bypassing the `coord_map` lookup table used in v2.
