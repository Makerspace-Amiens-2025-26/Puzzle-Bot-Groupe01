
# Camera Calibration Tools

Four scripts that cover the full camera calibration workflow — from computing intrinsic parameters to visually verifying and fine-tuning them, to previewing the final image processing pipeline used in production.

Run them **in the order presented below**.

---

## Why Camera Calibration?

Every camera lens introduces geometric distortion — straight lines appear curved, and pixel coordinates do not map linearly to real-world positions. OpenCV's calibration pipeline models this with two sets of parameters:

**Camera matrix** (intrinsics):
```
[ fx   0   cx ]
[  0  fy   cy ]
[  0   0    1 ]
```
- `fx`, `fy` — focal lengths in pixels
- `cx`, `cy` — principal point (optical centre, usually near image centre)

**Distortion coefficients** `[k1, k2, p1, p2, k3]`:
- `k1, k2, k3` — radial distortion (barrel / pincushion effect)
- `p1, p2` — tangential distortion (lens not perfectly parallel to sensor)

These parameters are used in every other script in this project (`find_aruco_position.py`, `position_correction.py`) via `cv2.remap()`. **They must be calibrated for your specific camera and mounting position.**

---

## Workflow

```
Step 1 — camera_calib.py
    Compute CAMERA_MATRIX and DIST_COEFFS from a physical checkerboard.
    Output: prints values + saves camera_calibration.npz

Step 2 — test_calib_1.py
    Quick visual check: side-by-side live feed (distorted vs undistorted).
    Confirms the calibration visually before doing anything else.

Step 3 — test_calib_2.py   (optional but recommended)
    Interactive fine-tuner: live sliders for every parameter.
    Use if test_calib_1 shows residual distortion you want to correct manually.

Step 4 — crop_zoom_sharpen.py
    Previews the full production image pipeline:
    undistort → ArUco-guided crop → zoom → unsharp-mask sharpening.
    This is what find_aruco_position.py runs on every frame.
```

---

## Step 1 — `camera_calib.py` — Compute Calibration Parameters

### What it does

Uses a printed checkerboard and OpenCV's `calibrateCamera()` to solve for `CAMERA_MATRIX` and `DIST_COEFFS`. You move the board around under the camera while it captures frames; after ≥15 captures it runs the solver and prints copy-pasteable numpy arrays.

### Setup

1. Print the standard OpenCV checkerboard:  
   `https://github.com/opencv/opencv/blob/master/doc/pattern.png`  
   (9×6 inner corners — tape it flat on a rigid surface, no wrinkles)

![Alt text](https://github.com/Makerspace-Amiens-2025-26/Puzzle-Bot-Groupe01/blob/main/docs/images/chessboard.png)

2. **Mount the camera at its exact production position and height.**  
   Calibration is only valid for the position it was done in — moving the camera means re-running this script.

3. Set `SQUARE_SIZE_MM` to the actual measured size of one square on your printout (use a ruler).

4. Set `WEBCAM_INDEX` to your camera index.

### Running

```bash
python camera_calib.py
```

- Green corners = board detected → press `SPACE` to capture
- Capture from many angles, positions, and distances — diversity matters
- Press `Q` after ≥15 captures to run calibration

### Output

```
==============================
 CALIBRATION COMPLETE
   Reprojection error: 0.3821  (< 1.0 is good)
==============================

CAMERA_MATRIX = np.array([
    [470.505135, 0.000000, 355.560451],
    [0.000000, 470.358073, 234.359449],
    [0.000000, 0.000000, 1.000000],
], dtype=np.float64)

DIST_COEFFS = np.array([[-0.439154, 0.321623, -0.001229, -0.001429, -0.143054]], dtype=np.float64)
```

Also saved to `camera_calibration.npz`.  
**Copy the printed values into `test_calib_1.py`, `test_calib_2.py`, `crop_zoom_sharpen.py`, and `find_aruco_position.py`.**

**Reprojection error** is the average pixel distance between the detected checkerboard corners and where the calibration model predicts them. Below 1.0 is good; below 0.5 is excellent.

---

## Step 2 — `test_calib_1.py` — Visual Verification

### What it does

Opens a live side-by-side window: **LEFT** = raw distorted feed with a grid overlay, **RIGHT** = undistorted feed with the same grid. The grid makes barrel/pincushion distortion immediately visible — straight grid lines on the right panel mean good calibration.


![Alt text](https://github.com/Makerspace-Amiens-2025-26/Puzzle-Bot-Groupe01/blob/main/docs/images/undistortion.png)

The bottom-left HUD displays the active `fx, fy, cx, cy, k1, k2, k3, p1, p2` values.

### Keys

| Key | Action |
|---|---|
| `Q` / `ESC` | Quit |

### What to look for

- Grid lines should be straight on the RIGHT panel.
- The image should not look heavily cropped or warped.
- If lines are still curved, recapture more frames in `camera_calib.py` with more variety, or proceed to `test_calib_2.py` to fine-tune manually.

---

## Step 3 — `test_calib_2.py` — Interactive Fine-Tuner *(optional)*

### What it does

Same side-by-side live view as `test_calib_1.py`, but with a separate **Controls** window that exposes trackbars for every calibration parameter. Changes apply instantly to the right panel — no restart needed. Use this if the output of `camera_calib.py` is close but not quite right.

### Parameter ranges and encoding

Trackbars only handle integers, so each float parameter is mapped to an integer range:

| Parameter | Float range | Step |
|---|---|---|
| `fx`, `fy` | 200 – 900 | 0.1 |
| `cx`, `cy` | 0 – 1000 px | 0.1 |
| `k1`, `k2`, `k3` | −1.5 – +1.5 | 0.0001 |
| `p1`, `p2` | −0.05 – +0.05 | 0.000001 |

The bottom-right of the composite shows delta indicators (green = close to original calibration, red = far) for `fx`, `k1`, `k2`.

### Keys

| Key | Action |
|---|---|
| `R` | Reset all sliders to the original calibration values |
| `S` | Print current values to terminal + numpy copy-paste block |
| `G` | Toggle grid overlay on/off |
| `Q` / `ESC` | Quit |

### Workflow

1. Adjust sliders until grid lines are straight.
2. Press `S` to print the current values.
3. Copy the printed numpy arrays into the other scripts.

---

## Step 4 — `crop_zoom_sharpen.py` — Production Pipeline Preview

### What it does

Previews the **exact image processing pipeline** that `find_aruco_position.py` applies to every frame during ArUco detection. This is the most complete visual tool — use it to verify that the final cropped/zoomed image is sharp enough for reliable marker detection.

### Pipeline (in order)

```
Raw frame
    │
    ▼
1. Lens undistortion          cv2.remap() with precomputed LUTs
    │
    ▼
2. ArUco detection            detect markers with IDs {0, 1, 2}
    │                         (reference frame markers)
    ▼
3. Bounding box + padding     tight box around all ref markers + CROP_PADDING px
    │                         expanded to a square, clamped to frame
    ▼
4. Crop                       extract the ROI from the undistorted frame
    │
    ▼
5. Zoom                       cv2.resize to OUTPUT_W × OUTPUT_H (1280×720)
    │                         using Lanczos4 interpolation (high quality)
    ▼
6. Unsharp mask sharpening    edge enhancement without ringing artefacts
    │                         USM_SIGMA=1.0, USM_STRENGTH=1.8, USM_THRESHOLD=4
    ▼
Final frame fed to ArUco detector in find_aruco_position.py
```

**Why crop and zoom?** The reference markers (IDs 0, 1, 2) define the working area. Cropping tightly around them removes irrelevant background and maximises the pixel resolution available for detecting the smaller puzzle-piece markers — directly improving detection reliability.

**Why unsharp masking?** Zooming with interpolation softens edges. The unsharp mask restores high-frequency detail (marker edges, corner sharpness) which is critical for sub-pixel ArUco corner localisation. The threshold parameter (`USM_THRESHOLD=4`) suppresses noise amplification on flat regions.

### Display mode

Controlled by `BEFORE_AND_AFTER` at the top of the file:

```python
BEFORE_AND_AFTER = False   # show only the final sharpened output (production view)
BEFORE_AND_AFTER = True    # show undistorted+crop-rect on left, final output on right
```

Set to `True` while tuning, `False` to see exactly what the detector sees.

### Key tuning parameters

| Parameter | Default | Effect |
|---|---|---|
| `CROP_PADDING` | 30 px | Extra margin around the reference marker bounding box |
| `OUTPUT_W/H` | 1280×720 | Final zoom resolution |
| `USM_SIGMA` | 1.0 | Gaussian blur radius for unsharp mask |
| `USM_STRENGTH` | 1.8 | Sharpening intensity (higher = stronger edges) |
| `USM_THRESHOLD` | 4 | Min difference to sharpen (suppresses noise on flat areas) |

### Keys

| Key | Action |
|---|---|
| `Q` / `ESC` | Quit |

---

## File Summary

| File | Purpose | Run order |
|---|---|---|
| `camera_calib.py` | Compute `CAMERA_MATRIX` and `DIST_COEFFS` from a checkerboard | 1st — do this once per camera/mounting |
| `test_calib_1.py` | Live side-by-side visual check of the calibration | 2nd — quick sanity check |
| `test_calib_2.py` | Interactive slider tuner for all calibration parameters | 3rd — only if manual correction needed |
| `crop_zoom_sharpen.py` | Preview the full production image pipeline | 4th — verify detection quality before running the solver |

## Requirements

```bash
pip install opencv-contrib-python numpy
```

> `opencv-contrib-python` is required (not plain `opencv-python`) — it includes the ArUco module used in `crop_zoom_sharpen.py`.
