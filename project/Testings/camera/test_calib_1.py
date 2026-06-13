import cv2
import numpy as np


## Code that tests the calibration ; before and after calibration 

# # ── Camera intrinsics ────────────────────────────────────────────────────────

CAMERA_MATRIX = np.array([
    [470.505135, 0.000000, 355.560451],
    [0.000000, 470.358073, 234.359449],
    [0.000000, 0.000000, 1.000000],
], dtype=np.float64)

DIST_COEFFS = np.array([[-0.439154, 0.321623, -0.001229, -0.001429, -0.143054]], dtype=np.float64)

# ── Config ───────────────────────────────────────────────────────────────────
CAMERA_INDEX  = 1          # change if your webcam isn't /dev/video0
LABEL_HEIGHT  = 36         # pixels reserved for the label bar at the top
DIVIDER_WIDTH = 3          # px width of the centre divider line
DIVIDER_COLOR = (255, 215, 0)   # gold
LABEL_BG      = (30, 30, 30)
FONT          = cv2.FONT_HERSHEY_SIMPLEX


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


def main():
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera index {CAMERA_INDEX}. "
                           "Check CAMERA_INDEX or USB connection.")

    # Read one frame just to learn the resolution
    ret, frame = cap.read()
    if not ret:
        raise RuntimeError("Could not read from camera.")

    h, w = frame.shape[:2]
    map1, map2, new_cam_mat, roi = build_undistort_maps(CAMERA_MATRIX, DIST_COEFFS, (h, w))
    x_roi, y_roi, w_roi, h_roi = roi

    print("Camera calibration preview running.")
    print("  LEFT  – raw (distorted)")
    print("  RIGHT – undistorted")
    print("Press  Q  or  ESC  to quit.\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Frame grab failed – exiting.")
            break

        # ── Undistort using precomputed maps (fast) ──────────────────────────
        undistorted = cv2.remap(frame, map1, map2, cv2.INTER_LINEAR)

        # ── Draw lens-distortion grid overlay on the raw frame ───────────────
        raw_display = frame.copy()
        grid_color  = (0, 200, 80)
        for col in range(0, w, w // 8):
            cv2.line(raw_display, (col, 0), (col, h), grid_color, 1)
        for row in range(0, h, h // 6):
            cv2.line(raw_display, (0, row), (w, row), grid_color, 1)

        und_display = undistorted.copy()
        for col in range(0, w, w // 8):
            cv2.line(und_display, (col, 0), (col, h), grid_color, 1)
        for row in range(0, h, h // 6):
            cv2.line(und_display, (0, row), (w, row), grid_color, 1)

        # ── Labels ───────────────────────────────────────────────────────────
        draw_label(raw_display, "DISTORTED  (original)",   color=(80, 160, 255))
        draw_label(und_display, "UNDISTORTED (calibrated)", color=(80, 255, 140))

        # ── Side-by-side composite ───────────────────────────────────────────
        divider = np.full((h, DIVIDER_WIDTH, 3), DIVIDER_COLOR, dtype=np.uint8)
        composite = np.hstack([raw_display, divider, und_display])

        # ── HUD: bottom-left corner info ─────────────────────────────────────
        hud_lines = [
            f"fx={CAMERA_MATRIX[0,0]:.1f}  fy={CAMERA_MATRIX[1,1]:.1f}",
            f"cx={CAMERA_MATRIX[0,2]:.1f}  cy={CAMERA_MATRIX[1,2]:.1f}",
            f"k1={DIST_COEFFS[0,0]:.4f}  k2={DIST_COEFFS[0,1]:.4f}  k3={DIST_COEFFS[0,4]:.4f}",
            f"p1={DIST_COEFFS[0,2]:.6f}  p2={DIST_COEFFS[0,3]:.6f}",
        ]
        cw = composite.shape[1]
        ch = composite.shape[0]
        for i, line in enumerate(reversed(hud_lines)):
            y_pos = ch - 10 - i * 20
            cv2.putText(composite, line, (10, y_pos),
                        FONT, 0.42, (160, 160, 160), 1, cv2.LINE_AA)

        cv2.imshow("Camera Calibration Preview  |  Q / ESC = quit", composite)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), ord('Q'), 27):   # Q or ESC
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
