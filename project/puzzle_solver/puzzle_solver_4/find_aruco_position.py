"""
ArUco Detection Pipeline  –  puzzle coordinate localiser
=========================================================

Pipeline stages (controlled by DEBUG_STAGE):
  1  →  raw capture only
  2  →  undistort
  3  →  undistort + crop
  4  →  undistort + crop + zoom
  5  →  undistort + crop + zoom + sharpen   (full pipeline, default)

Set DEBUG_STAGE = 5 for production; lower values let you inspect
each intermediate step without touching the rest of the code.
"""

import cv2
import numpy as np
import math
from position_correction import correct_position

# ── Pipeline debug stage ─────────────────────────────────────────────────────
# 1 = raw  |  2 = + undistort  |  3 = + crop  |  4 = + zoom  |  5 = + sharpen 
DEBUG_STAGE = 5

# ── Camera intrinsics ────────────────────────────────────────────────────────
CAMERA_MATRIX = np.array([
    [470.505135, 0.000000, 355.560451],
    [0.000000, 470.358073, 234.359449],
    [0.000000, 0.000000, 1.000000],
], dtype=np.float64)

DIST_COEFFS = np.array(
    [[-0.439154, 0.321623, -0.001229, -0.001429, -0.143054]],
    dtype=np.float64,
)

# ── Config ───────────────────────────────────────────────────────────────────
CAMERA_INDEX   = 1
LABEL_HEIGHT   = 36
DIVIDER_WIDTH  = 4
DIVIDER_COLOR  = (255, 215, 0)     # gold
LABEL_BG       = (20, 20, 20)
FONT           = cv2.FONT_HERSHEY_SIMPLEX

OUTPUT_W       = 1280
OUTPUT_H       = 720

CROP_PADDING   = 30

# ArUco dictionary
ARUCO_DICT     = cv2.aruco.DICT_6X6_250

# Reference marker IDs that define the coordinate system
ID_ORIGIN      = 0    # pixel position = real (0, 0)
ID_X_AXIS      = 1    # pixel position = real (REAL_UNIT, 0)
ID_Y_AXIS      = 2    # pixel position = real (0, REAL_UNIT)
REAL_UNIT      = 4    # real-world distance between reference markers (cm / mm / any unit)

# All three reference IDs must be visible for the crop window
ARUCO_TARGET_IDS = {ID_ORIGIN, ID_X_AXIS, ID_Y_AXIS}

# Sharpening (unsharp mask)
USM_SIGMA      = 1.0
USM_STRENGTH   = 1.8
USM_THRESHOLD  = 4

# Overlay colours
CROP_RECT_COLOR = (0, 215, 255)
CROP_RECT_THICK = 2

# Number of frames averaged for a stable coordinate reading
NUM_FRAMES_AVERAGE = 70


# ── Stage label used in the window title ─────────────────────────────────────
_STAGE_LABELS = {
    1: "RAW",
    2: "UNDISTORT",
    3: "UNDISTORT + CROP",
    4: "UNDISTORT + CROP + ZOOM",
    5: "UNDISTORT + CROP + ZOOM + SHARPEN",
}


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 – camera / image utilities
# ══════════════════════════════════════════════════════════════════════════════

def build_undistort_maps(camera_matrix, dist_coeffs, frame_size):
    """Pre-compute the remap LUTs once per session."""
    h, w = frame_size
    new_cam, roi = cv2.getOptimalNewCameraMatrix(
        camera_matrix, dist_coeffs, (w, h), alpha=1, newImgSize=(w, h)
    )
    map1, map2 = cv2.initUndistortRectifyMap(
        camera_matrix, dist_coeffs, None, new_cam, (w, h), cv2.CV_16SC2
    )
    return map1, map2, new_cam, roi


def unsharp_mask(image, sigma=1.0, strength=1.8, threshold=4):
    """Sharpen by boosting high-frequency content above *threshold*."""
    ksize   = int(6 * sigma + 1) | 1
    blurred = cv2.GaussianBlur(image, (ksize, ksize), sigma)
    img_f   = image.astype(np.float32)
    hf      = img_f - blurred.astype(np.float32)
    hf_t    = np.where(np.abs(hf) > threshold, hf, 0.0)
    return np.clip(img_f + strength * hf_t, 0, 255).astype(np.uint8)


def draw_label(img, text, color=(220, 220, 220)):
    """Draw a centred text banner at the top of *img* (in-place)."""
    h, w = img.shape[:2]
    cv2.rectangle(img, (0, 0), (w, LABEL_HEIGHT), LABEL_BG, -1)
    ts, _ = cv2.getTextSize(text, FONT, 0.65, 2)
    tx = (w  - ts[0]) // 2
    ty = (LABEL_HEIGHT + ts[1]) // 2
    cv2.putText(img, text, (tx, ty), FONT, 0.65, color, 2, cv2.LINE_AA)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 – ArUco bounding-box helpers
# ══════════════════════════════════════════════════════════════════════════════

def get_aruco_detector():
    aruco_dict    = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    aruco_params  = cv2.aruco.DetectorParameters()
    return cv2.aruco.ArucoDetector(aruco_dict, aruco_params)


def detect_aruco_bbox(frame, aruco_detector):
    """
    Return the bounding box around all *reference* markers (IDs 0, 1, 2)
    and the count of those markers found.
    Returns (None, 0) if none are visible.
    """
    corners, ids, _ = aruco_detector.detectMarkers(frame)
    if ids is None or len(ids) == 0:
        return None, 0

    filtered = [
        c for c, mid in zip(corners, ids.flatten())
        if mid in ARUCO_TARGET_IDS
    ]
    if not filtered:
        return None, 0

    all_pts = np.concatenate([c.reshape(-1, 2) for c in filtered], axis=0)
    x_min   = int(np.min(all_pts[:, 0]))
    y_min   = int(np.min(all_pts[:, 1]))
    x_max   = int(np.max(all_pts[:, 0]))
    y_max   = int(np.max(all_pts[:, 1]))
    return (x_min, y_min, x_max - x_min, y_max - y_min), len(filtered)


def square_crop_from_bbox(bbox, frame_h, frame_w, padding):
    """Pad → make square → clamp.  Returns (x1, y1, x2, y2)."""
    x, y, bw, bh = bbox
    x1 = x - padding;  y1 = y - padding
    x2 = x + bw + padding;  y2 = y + bh + padding
    cx = (x1 + x2) // 2;  cy = (y1 + y2) // 2
    half = max(x2 - x1, y2 - y1) // 2
    x1 = max(0, cx - half);  y1 = max(0, cy - half)
    x2 = min(frame_w, cx + half);  y2 = min(frame_h, cy + half)
    return x1, y1, x2, y2


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 – full pipeline (stage-gated)
# ══════════════════════════════════════════════════════════════════════════════

def apply_pipeline(frame, map1, map2, aruco_detector, last_crop_ref, stage=5):
    """
    Run the detection pipeline up to *stage* and return the display image.

    last_crop_ref: a one-element list [crop_tuple | None]  (mutable default trick
                   so the caller persists the crop box across calls).

    Stages:
      1  raw frame
      2  + undistort
      3  + crop around reference ArUco markers
      4  + zoom to OUTPUT_W × OUTPUT_H
      5  + unsharp-mask sharpening
    """
    h, w = frame.shape[:2]
    stage_label = _STAGE_LABELS.get(stage, "UNKNOWN STAGE")

    # ── Stage 1: raw ─────────────────────────────────────────────────────────
    if stage == 1:
        out = frame.copy()
        draw_label(out, f"[STAGE 1] RAW CAPTURE", color=(200, 200, 200))
        return out

    # ── Stage 2: undistort ────────────────────────────────────────────────────


    undistorted = cv2.remap(frame, map1, map2, cv2.INTER_LINEAR)
    if stage == 2:
        out = undistorted.copy()
        draw_label(out, "[STAGE 2] UNDISTORTED", color=(80, 255, 140))
        return out




    # ── Stage 3: detect reference markers and compute crop box ───────────────
    bbox, n_markers = detect_aruco_bbox(undistorted, aruco_detector)
    if bbox is not None:
        x1, y1, x2, y2 = square_crop_from_bbox(bbox, h, w, CROP_PADDING)
        last_crop_ref[0] = (x1, y1, x2, y2)

    if stage == 3:
        # Show undistorted with crop rectangle overlay
        out = undistorted.copy()
        # Grid
        for col in range(0, w, w // 8):
            cv2.line(out, (col, 0), (col, h), (0, 200, 80), 1)
        for row in range(0, h, h // 6):
            cv2.line(out, (0, row), (w, row), (0, 200, 80), 1)
        if last_crop_ref[0] is not None:
            lx1, ly1, lx2, ly2 = last_crop_ref[0]
            cv2.rectangle(out, (lx1, ly1), (lx2, ly2), CROP_RECT_COLOR, CROP_RECT_THICK)
            _draw_corner_accents(out, lx1, ly1, lx2, ly2)
        ids_str = f"{n_markers}/3 ref markers"
        draw_label(out, f"[STAGE 3] UNDISTORT + CROP BOX  |  {ids_str}", color=(255, 200, 0))
        return out

    # ── Stage 4: crop + zoom ─────────────────────────────────────────────────
    if last_crop_ref[0] is None:
        placeholder = np.zeros((OUTPUT_H, OUTPUT_W, 3), dtype=np.uint8)
        cv2.putText(placeholder, "Waiting for reference markers (ID 0,1,2)...",
                    (30, OUTPUT_H // 2), FONT, 0.7, (120, 120, 120), 2, cv2.LINE_AA)
        draw_label(placeholder, f"[STAGE {stage}] {stage_label}  |  no markers", color=(0, 100, 200))
        return placeholder

    lx1, ly1, lx2, ly2 = last_crop_ref[0]
    cropped = undistorted[ly1:ly2, lx1:lx2]
    zoomed  = cv2.resize(cropped, (OUTPUT_W, OUTPUT_H), interpolation=cv2.INTER_LANCZOS4)

    if stage == 4:
        out = zoomed.copy()
        draw_label(out, "[STAGE 4] UNDISTORT + CROP + ZOOM", color=(255, 165, 80))
        return out

    # ── Stage 5: sharpen ─────────────────────────────────────────────────────
    sharpened = unsharp_mask(zoomed, sigma=USM_SIGMA,
                             strength=USM_STRENGTH, threshold=USM_THRESHOLD)
    draw_label(sharpened, "[STAGE 5] FULL PIPELINE  (undistort+crop+zoom+sharpen)",
               color=(255, 80, 80))
    return sharpened


def _draw_corner_accents(img, x1, y1, x2, y2, length=14):
    for px, py in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
        dx = 1 if px == x1 else -1
        dy = 1 if py == y1 else -1
        cv2.line(img, (px, py), (px + dx * length, py), CROP_RECT_COLOR, 3)
        cv2.line(img, (px, py), (px, py + dy * length), CROP_RECT_COLOR, 3)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 – coordinate system helpers  (from code-2)
# ══════════════════════════════════════════════════════════════════════════════

def get_marker_center(corners):
    c = corners[0]
    return (int(np.mean(c[:, 0])), int(np.mean(c[:, 1])))


def undistort_point(point, camera_matrix, dist_coeffs):
    pts = np.array([[[float(point[0]), float(point[1])]]], dtype=np.float32)
    corrected = cv2.undistortPoints(pts, camera_matrix, dist_coeffs, P=camera_matrix)
    return (int(corrected[0][0][0]), int(corrected[0][0][1]))


def build_coordinate_system_from_frame(corners, ids):
    """
    Given raw detector output, extract origin / scale_x / scale_y.
    Returns (origin_px, scale_x, scale_y) or (None, None, None).
    Points are lens-corrected before use.
    """
    if ids is None:
        return None, None, None

    ids_flat = ids.flatten()
    markers  = {}
    for i, mid in enumerate(ids_flat):
        center = get_marker_center(corners[i])
        center = undistort_point(center, CAMERA_MATRIX, DIST_COEFFS)
        markers[int(mid)] = center

    if not all(k in markers for k in [ID_ORIGIN, ID_X_AXIS, ID_Y_AXIS]):
        return None, None, None

    origin  = markers[ID_ORIGIN]
    x_point = markers[ID_X_AXIS]
    y_point = markers[ID_Y_AXIS]

    dx = math.dist(origin, x_point)
    dy = math.dist(origin, y_point)
    if dx == 0 or dy == 0:
        return None, None, None

    scale_x = REAL_UNIT / dx
    scale_y = REAL_UNIT / dy
    return origin, scale_x, scale_y


def pixel_to_real(pixel_point, origin, scale_x, scale_y):
    dx =  (pixel_point[0] - origin[0]) * scale_x
    dy = -((pixel_point[1] - origin[1]) * scale_y)   # flip Y
    return round(dx, 4), round(dy, 4)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 – find_aruco: the main new function
# ══════════════════════════════════════════════════════════════════════════════

def find_aruco(aruco_id, cap, aruco_detector, map1, map2,
               num_frames=NUM_FRAMES_AVERAGE, stage=DEBUG_STAGE):
    """
    Locate *aruco_id* in real-world coordinates by averaging *num_frames*
    measurements.  Detection runs through the full pipeline up to *stage*
    (default = DEBUG_STAGE global) so you can inspect each processing step.

    The pipeline for each frame:
      raw → [undistort] → [crop] → [zoom] → [sharpen] → detect

    Parameters
    ----------
    aruco_id      : int   marker ID to locate (e.g. 3, 4, 5, 6)
    cap           : cv2.VideoCapture
    aruco_detector: cv2.aruco.ArucoDetector
    map1, map2    : undistortion LUTs from build_undistort_maps()
    num_frames    : int   how many valid samples to collect before averaging
    stage         : int   pipeline stage to display (1-5)

    Returns
    -------
    (avg_x, avg_y) in real-world units, or None if interrupted / failed.
    """
    print(f"\n[find_aruco] Searching for marker ID={aruco_id}  "
          f"(need IDs {ID_ORIGIN},{ID_X_AXIS},{ID_Y_AXIS} + {aruco_id} visible)")
    print(f"             Pipeline display stage: {stage} – {_STAGE_LABELS.get(stage)}")
    print(f"             Collecting {num_frames} frames …")

    collected   = []
    last_crop   = [None]    # mutable container so apply_pipeline can persist it
    win_title   = f"find_aruco  ID={aruco_id}  |  stage {stage}: {_STAGE_LABELS[stage]}  |  Q=quit"

    while len(collected) < num_frames:
        cap.read()
        cap.read()
        ret, frame = cap.read()
        if not ret:
            print("[find_aruco] Frame grab failed – aborting.")
            return None

        h, w = frame.shape[:2]

        # ── A. Build the display image for this stage ────────────────────────
        display = apply_pipeline(frame, map1, map2, aruco_detector, last_crop, stage=stage)

        # ── B. Overlay progress counter on the display image ─────────────────
        progress_text = (f"ID {aruco_id}  samples: {len(collected)}/{num_frames}  "
                         f"| stage {stage}")
        cv2.putText(display, progress_text,
                    (10, display.shape[0] - 15),
                    FONT, 0.65, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.imshow(win_title, display)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("[find_aruco] Interrupted by user.")
            cv2.destroyWindow(win_title)
            return None

        # ── C. Coordinate computation always uses the full pipeline ──────────
        #       (display stage controls what you SEE; math always uses all steps)

        # Step C-1: undistort
        undistorted = cv2.remap(frame, map1, map2, cv2.INTER_LINEAR)

        # Step C-2: detect on the undistorted frame (no crop needed for
        #           coordinate accuracy since we undistort_point individually)
        corners, ids, _ = aruco_detector.detectMarkers(undistorted)
        if ids is None:
            continue

        ids_flat = ids.flatten().tolist()

        # All three reference markers must be visible
        if not all(k in ids_flat for k in [ID_ORIGIN, ID_X_AXIS, ID_Y_AXIS]):
            continue

        # Target marker must also be visible
        if aruco_id not in ids_flat:
            continue

        # Step C-3: build coordinate system
        origin, scale_x, scale_y = build_coordinate_system_from_frame(corners, ids)
        if origin is None:
            continue

        # Step C-4: locate target marker
        for i, mid in enumerate(ids_flat):
            if mid == aruco_id:
                center = get_marker_center(corners[i])
                center = undistort_point(center, CAMERA_MATRIX, DIST_COEFFS)
                rx, ry = pixel_to_real(center, origin, scale_x, scale_y)
                collected.append((rx, ry))
                print(f"  sample {len(collected):3d}/{num_frames}  →  "
                      f"pixel {center}   real ({rx:.12f}, {ry:.12f})")
                break

    # ── D. Average            ─────────────────────────────────────────────────
    avg_x = -round(sum(s[0] for s in collected) / len(collected), 4)
    avg_y = -round(sum(s[1] for s in collected) / len(collected), 4)

    # ── E. Position Correction and return ─────────────────────────────────────`
    corrected_x, corrected_y = avg_x, avg_y


# ── F. Measure angle ─────────────────────────────────────────────────────

    def marker_axis_vectors(corners, ids_flat, marker_id):
        """Returns (vec_horizontal, vec_vertical) = (TL→TR, TL→BL)"""
        for i, mid in enumerate(ids_flat):
            if mid == marker_id:
                pts = corners[i][0]        # TL, TR, BR, BL
                return pts[1] - pts[0],  pts[3] - pts[0]
        return None, None

    vec_origin_h, _ = marker_axis_vectors(corners, ids_flat, ID_ORIGIN)
    vec_target_h, vec_target_v = marker_axis_vectors(corners, ids_flat, aruco_id)

    if vec_origin_h is None or vec_target_h is None:
        print("[find_aruco] Warning: could not compute angle (marker not found in last frame).")
        angle = 0.0
    else:
        angle_origin = math.degrees(math.atan2(vec_origin_h[1], vec_origin_h[0]))

        angle_h = math.degrees(math.atan2(vec_target_h[1], vec_target_h[0])) - angle_origin
        angle_v = math.degrees(math.atan2(vec_target_v[1], vec_target_v[0])) - angle_origin

        # Wrap both to [-90, 90]
        for a in [angle_h, angle_v]:
            pass
        def wrap(a):
            while a > 90:  a -= 180
            while a <= -90: a += 180
            return round(a, 2)

        angle_h = wrap(angle_h)
        angle_v = wrap(angle_v)

        # Keep the one with smaller absolute value
        angle = angle_h if abs(angle_h) <= abs(angle_v) else angle_v

    print(f'{{"{aruco_id} ==> {corrected_x:.4f}, {corrected_y:.4f}, angle={angle}"}}')
    cv2.destroyWindow(win_title)
    return (corrected_x, corrected_y, angle)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 – live preview loop  (original code-1 main, kept for reference)
# ══════════════════════════════════════════════════════════════════════════════

def main_live_preview():
    """
    Continuous camera feed with the full pipeline displayed stage by stage.
    Press 1-5 at runtime to switch pipeline stage on the fly.
    Press Q or ESC to quit.
    """
    aruco_detector = get_aruco_detector()

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera index {CAMERA_INDEX}.")

    ret, frame = cap.read()
    if not ret:
        raise RuntimeError("Could not read from camera.")

    h, w    = frame.shape[:2]
    map1, map2, _, _ = build_undistort_maps(CAMERA_MATRIX, DIST_COEFFS, (h, w))

    last_crop = [None]
    stage     = DEBUG_STAGE

    print("Live preview – pipeline stages")
    print("  Press 1-5 to switch stage  |  Q / ESC to quit")
    print(f"  Current stage: {stage} – {_STAGE_LABELS[stage]}\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        display = apply_pipeline(frame, map1, map2, aruco_detector, last_crop, stage=stage)

        # HUD – camera params
        hud = [
            f"fx={CAMERA_MATRIX[0,0]:.1f}  fy={CAMERA_MATRIX[1,1]:.1f}",
            f"cx={CAMERA_MATRIX[0,2]:.1f}  cy={CAMERA_MATRIX[1,2]:.1f}",
            f"k1={DIST_COEFFS[0,0]:.4f}  k2={DIST_COEFFS[0,1]:.4f}",
        ]
        ch = display.shape[0]
        for i, line in enumerate(reversed(hud)):
            cv2.putText(display, line, (10, ch - 10 - i * 20),
                        FONT, 0.42, (160, 160, 160), 1, cv2.LINE_AA)

        cv2.imshow("Pipeline preview  |  1-5 = stage  Q = quit", display)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), ord('Q'), 27):
            break
        if key in [ord(str(s)) for s in range(1, 6)]:
            stage = int(chr(key))
            print(f"  Switched to stage {stage} – {_STAGE_LABELS[stage]}")

    cap.release()
    cv2.destroyAllWindows()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 – test main for find_aruco
# ══════════════════════════════════════════════════════════════════════════════

# Markers to locate; change this list freely
ARUCO_TO_FIND = [3, 4, 5, 6]


def main_find_aruco():
    """
    Test harness for find_aruco().

    For each ID in ARUCO_TO_FIND it:
      1. Opens a live window showing the pipeline at DEBUG_STAGE
      2. Collects NUM_FRAMES_AVERAGE valid samples
      3. Prints and stores the averaged coordinate

    After all markers are done, prints a summary table.

    Tip: set DEBUG_STAGE = 1 first to verify the raw feed,
         then increment to 2, 3, 4, 5 to validate each processing step.
    """
    print("=" * 60)
    print(" find_aruco() test")
    print(f" Pipeline stage : {DEBUG_STAGE} – {_STAGE_LABELS[DEBUG_STAGE]}")
    print(f" Markers to find: {ARUCO_TO_FIND}")
    print(f" Frames averaged: {NUM_FRAMES_AVERAGE}")
    print("=" * 60)

    aruco_detector = get_aruco_detector()

    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)


    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera {CAMERA_INDEX}")

    cap.read()
    cap.read()
    cap.read()
    cap.read()

    # Build undistortion maps once
    ret, first_frame = cap.read()
    if not ret:
        raise RuntimeError("Could not read first frame.")
    h, w = first_frame.shape[:2]
    map1, map2, _, _ = build_undistort_maps(CAMERA_MATRIX, DIST_COEFFS, (h, w))

    results = [ [] for _ in ARUCO_TO_FIND ]

    for aruco_id in ARUCO_TO_FIND:
        coord = find_aruco(
            aruco_id     = aruco_id,
            cap          = cap,
            aruco_detector = aruco_detector,
            map1         = map1,
            map2         = map2,
            num_frames   = NUM_FRAMES_AVERAGE,
            stage        = DEBUG_STAGE,
        )
        results[aruco_id - ARUCO_TO_FIND[0]] = coord

    cap.release()
    cv2.destroyAllWindows()

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(" RESULTS")
    print("=" * 60)
    print(f"  {'Marker ID':<12}  {'Real X':>10}  {'Real Y':>10}  {'Status'}")
    print(f"  {'-'*12}  {'-'*10}  {'-'*10}  {'-'*12}")
    for aid in ARUCO_TO_FIND:
        coord = results[aid - ARUCO_TO_FIND[0]]
        if coord is not None:
            print(f"  ID {aid:<9}  {coord[0]:>10.4f}  {coord[1]:>10.4f}  {coord[2]:>10.4f}  OK")
        else:
            print(f"  ID {aid:<9}  {'—':>10}  {'—':>10}  FAILED / SKIPPED")
    print("=" * 60)

    return results


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # ── Choose which main to run ──────────────────────────────────────────────
    # main_live_preview()   # ← continuous feed, press 1-5 to change stage
    main_find_aruco()       # ← locate markers and return coordinates