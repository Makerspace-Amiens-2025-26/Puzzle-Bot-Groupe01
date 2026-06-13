
import cv2
import numpy as np


# ── Camera intrinsics ────────────────────────────────────────────────────────

CAMERA_MATRIX = np.array([
    [470.505135, 0.000000, 355.560451],
    [0.000000, 470.358073, 234.359449],
    [0.000000, 0.000000, 1.000000],
], dtype=np.float64)

DIST_COEFFS = np.array([[-0.439154, 0.321623, -0.001229, -0.001429, -0.143054]], dtype=np.float64)

# ── Config ───────────────────────────────────────────────────────────────────
CAMERA_INDEX    = 1
LABEL_HEIGHT    = 36
DIVIDER_WIDTH   = 4
DIVIDER_COLOR   = (255, 215, 0)     # gold
LABEL_BG        = (20, 20, 20)
FONT            = cv2.FONT_HERSHEY_SIMPLEX

OUTPUT_W        = 1280             # zoomed crop output width  # was 1280
OUTPUT_H        = 720               # zoomed crop output height

BEFORE_AND_AFTER = False

# Padding (in pixels) added around the tight ArUco bounding box before crop
CROP_PADDING    = 30

# ArUco dictionary and target IDs
ARUCO_DICT      = cv2.aruco.DICT_6X6_250
ARUCO_TARGET_IDS = {0, 1, 2}          # only these three markers are used for the crop

# Sharpening: unsharp mask parameters
USM_BLUR_SIZE   = (0, 0)           # auto-computed from sigma below
USM_SIGMA       = 1.0              # Gaussian sigma for unsharp mask
USM_STRENGTH    = 1.8              # how strongly to boost high-frequencies (>1 = stronger)
USM_THRESHOLD   = 4               # ignore differences below this (reduces noise amplification)

# Colour for the crop-rectangle drawn on the left panel
CROP_RECT_COLOR = (0, 215, 255)    # cyan-yellow
CROP_RECT_THICK = 2


# ── Helpers ──────────────────────────────────────────────────────────────────

def build_undistort_maps(camera_matrix, dist_coeffs, frame_size):
    """Pre-compute the remap look-up tables once for efficiency."""
    h, w = frame_size
    new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
        camera_matrix, dist_coeffs, (w, h), alpha=1, newImgSize=(w, h)
    )
    map1, map2 = cv2.initUndistortRectifyMap(
        camera_matrix, dist_coeffs, None, new_camera_matrix, (w, h), cv2.CV_16SC2
    )
    return map1, map2, new_camera_matrix, roi


def draw_label(img, text, color=(220, 220, 220)):
    """Draw a centred label on a pre-sized banner region."""
    h, w = img.shape[:2]
    cv2.rectangle(img, (0, 0), (w, LABEL_HEIGHT), LABEL_BG, -1)
    text_size, _ = cv2.getTextSize(text, FONT, 0.65, 2)
    tx = (w - text_size[0]) // 2
    ty = (LABEL_HEIGHT + text_size[1]) // 2
    cv2.putText(img, text, (tx, ty), FONT, 0.65, color, 2, cv2.LINE_AA)


def unsharp_mask(image, sigma=1.0, strength=1.8, threshold=4):
    """
    Unsharp masking: sharpen edges without introducing ringing artefacts.

    Steps:
      1. Gaussian blur  → low-frequency content
      2. high-freq mask = original − blurred
      3. Apply mask only where |mask| > threshold  (suppresses noise)
      4. result = original + strength × masked high-freq
    """
    # kernel size must be odd; derive from sigma
    ksize = int(6 * sigma + 1) | 1      # next odd integer
    blurred = cv2.GaussianBlur(image, (ksize, ksize), sigma)

    # high-frequency component (signed, float)
    image_f   = image.astype(np.float32)
    blurred_f = blurred.astype(np.float32)
    high_freq = image_f - blurred_f

    # threshold: zero out small differences (mostly noise)
    mask = np.abs(high_freq) > threshold
    high_freq_thresholded = np.where(mask, high_freq, 0.0)

    # blend
    sharpened = image_f + strength * high_freq_thresholded
    return np.clip(sharpened, 0, 255).astype(np.uint8)


def detect_aruco_bbox(frame, aruco_detector):
    """
    Return (x, y, w, h) bounding box around corners of markers with IDs in
    ARUCO_TARGET_IDS (0, 1, 2), plus the count of those markers found.
    Returns (None, 0) if none of the target markers are visible.
    """
    corners, ids, _ = aruco_detector.detectMarkers(frame)
    if ids is None or len(ids) == 0:
        return None, 0

    # Keep only corners whose ID is in ARUCO_TARGET_IDS
    filtered = [
        c for c, mid in zip(corners, ids.flatten())
        if mid in ARUCO_TARGET_IDS
    ]
    if not filtered:
        return None, 0

    # Flatten all corner points of the filtered markers: shape (N*4, 2)
    all_pts = np.concatenate([c.reshape(-1, 2) for c in filtered], axis=0)

    x_min = int(np.min(all_pts[:, 0]))
    y_min = int(np.min(all_pts[:, 1]))
    x_max = int(np.max(all_pts[:, 0]))
    y_max = int(np.max(all_pts[:, 1]))

    return (x_min, y_min, x_max - x_min, y_max - y_min), len(filtered)


def square_crop_from_bbox(bbox, frame_h, frame_w, padding):
    """
    Expand bbox by padding, make it square, and clamp to frame bounds.
    Returns (x1, y1, x2, y2) — pixel coordinates of the square crop.
    """
    x, y, bw, bh = bbox
    x1 = x - padding
    y1 = y - padding
    x2 = x + bw + padding
    y2 = y + bh + padding

    # Make square: expand the shorter side from its centre
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    half = max(x2 - x1, y2 - y1) // 2

    x1 = cx - half
    y1 = cy - half
    x2 = cx + half
    y2 = cy + half

    # Clamp to frame
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(frame_w, x2)
    y2 = min(frame_h, y2)

    return x1, y1, x2, y2


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    # ── ArUco detector setup ─────────────────────────────────────────────────
    aruco_dict   = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    aruco_params = cv2.aruco.DetectorParameters()
    aruco_detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)

    # ── Camera ───────────────────────────────────────────────────────────────
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera index {CAMERA_INDEX}.")

    ret, frame = cap.read()
    if not ret:
        raise RuntimeError("Could not read from camera.")

    h, w = frame.shape[:2]
    map1, map2, new_cam_mat, roi = build_undistort_maps(CAMERA_MATRIX, DIST_COEFFS, (h, w))


    print("Camera calibration + ArUco crop preview running.")
    print("  LEFT  – undistorted with crop rectangle overlay")
    print("  RIGHT – cropped, zoomed, sharpened ROI")
    print("Press  Q  or  ESC  to quit.\n")

    # Persistent crop box (keeps last valid detection when markers disappear briefly)
    last_crop = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Frame grab failed – exiting.")
            break

        # ── 1. Undistort ─────────────────────────────────────────────────────
        undistorted = cv2.remap(frame, map1, map2, cv2.INTER_LINEAR)

        # ── 2. Detect ArUco markers on undistorted frame ─────────────────────
        corners, ids, _ = aruco_detector.detectMarkers(undistorted)





        found_ids = set()
        if ids is not None:
            found_ids = {int(i) for i in ids.flatten() if int(i) in ARUCO_TARGET_IDS}

        bbox, n_markers = detect_aruco_bbox(undistorted, aruco_detector)

        if bbox is not None:
            x1, y1, x2, y2 = square_crop_from_bbox(bbox, h, w, CROP_PADDING)
            last_crop = (x1, y1, x2, y2)

        # ── 3. Build left panel: undistorted + crop rect overlay + grid ──────
        left_panel = undistorted.copy()

        grid_color = (0, 200, 80)
        for col in range(0, w, w // 8):
            cv2.line(left_panel, (col, 0), (col, h), grid_color, 1)
        for row in range(0, h, h // 6):
            cv2.line(left_panel, (0, row), (w, row), grid_color, 1)

        if last_crop is not None:
            x1, y1, x2, y2 = last_crop
            cv2.rectangle(left_panel, (x1, y1), (x2, y2), CROP_RECT_COLOR, CROP_RECT_THICK)
            # Small corner accents for visibility
            accent_len = 14
            for px, py in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
                dx = 1 if px == x1 else -1
                dy = 1 if py == y1 else -1
                cv2.line(left_panel, (px, py), (px + dx * accent_len, py), CROP_RECT_COLOR, 3)
                cv2.line(left_panel, (px, py), (px, py + dy * accent_len), CROP_RECT_COLOR, 3)

        ids_str = f"IDs: {sorted(found_ids)}" if found_ids else "IDs: none"
        draw_label(left_panel, f"UNDISTORTED  |  {ids_str}  ({n_markers}/3)", color=(80, 255, 140))

        # ── 4. Build right panel: crop → zoom → sharpen ──────────────────────
        if last_crop is not None:
            x1, y1, x2, y2 = last_crop
            cropped = undistorted[y1:y2, x1:x2]

            # Zoom to target output size with high-quality interpolation
            zoomed = cv2.resize(cropped, (OUTPUT_W, OUTPUT_H), interpolation=cv2.INTER_LANCZOS4)

            # Sharpening (unsharp mask)
            sharpened = unsharp_mask(zoomed, sigma=USM_SIGMA,
                                     strength=USM_STRENGTH,
                                     threshold=USM_THRESHOLD)
            right_panel = sharpened
        else:
            # No markers yet – show placeholder
            right_panel = np.zeros((h, OUTPUT_W, 3), dtype=np.uint8)
            msg = "Waiting for ArUco markers..."
            ts, _ = cv2.getTextSize(msg, FONT, 0.8, 2)
            cv2.putText(right_panel, msg,
                        ((OUTPUT_W - ts[0]) // 2, h // 2),
                        FONT, 0.8, (120, 120, 120), 2, cv2.LINE_AA)

        draw_label(right_panel, "CROPPED  |  ZOOMED  |  SHARPENED", color=(255, 165, 80))

        # ── 5. Match heights for side-by-side ────────────────────────────────
        rh = right_panel.shape[0]
        lh = left_panel.shape[0]

        if rh != lh:
            # Scale left panel to match right panel height, keeping aspect ratio
            scale  = rh / lh
            new_lw = int(left_panel.shape[1] * scale)
            left_panel = cv2.resize(left_panel, (new_lw, rh), interpolation=cv2.INTER_LINEAR)

        divider  = np.full((rh, DIVIDER_WIDTH, 3), DIVIDER_COLOR, dtype=np.uint8)

        if (BEFORE_AND_AFTER) : 
            composite = np.hstack([left_panel, divider, right_panel])  #seeing before and after
        else :
            composite = right_panel # seeing only the new version 
        
        # ── 6. HUD: camera params bottom-left ────────────────────────────────
        hud_lines = [
            f"fx={CAMERA_MATRIX[0,0]:.1f}  fy={CAMERA_MATRIX[1,1]:.1f}",
            f"cx={CAMERA_MATRIX[0,2]:.1f}  cy={CAMERA_MATRIX[1,2]:.1f}",
            f"k1={DIST_COEFFS[0,0]:.4f}  k2={DIST_COEFFS[0,1]:.4f}  k3={DIST_COEFFS[0,4]:.4f}",
            f"p1={DIST_COEFFS[0,2]:.6f}  p2={DIST_COEFFS[0,3]:.6f}",
        ]
        ch = composite.shape[0]
        for i, line in enumerate(reversed(hud_lines)):
            y_pos = ch - 10 - i * 20
            cv2.putText(composite, line, (10, y_pos),
                        FONT, 0.42, (160, 160, 160), 1, cv2.LINE_AA)

        cv2.imshow("Calibration + ArUco Crop  |  Q / ESC = quit", composite)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), ord('Q'), 27):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
