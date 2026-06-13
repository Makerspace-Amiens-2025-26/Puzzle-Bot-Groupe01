"""
camera_undistort_interactive script 
────────────────────────────────────────────────────────────────────────────────
Live split-screen camera calibration tuner.

  LEFT  panel  – raw (distorted) feed
  RIGHT panel  – undistorted feed with current parameters

A separate "Controls" window exposes trackbars for every parameter.
Changes are applied instantly to the right panel.

Keys
  R  – reset all sliders back to the initial calibration values
  S  – print current parameter values to the terminal
  G  – toggle the reference grid overlay on/off
  Q / ESC – quit
────────────────────────────────────────────────────────────────────────────────
"""

import cv2
import numpy as np

# ── Default calibration (your initial values) ────────────────────────────────
DEFAULT_FX = 470.505135
DEFAULT_FY = 470.358073
DEFAULT_CX = 355.560451
DEFAULT_CY = 234.359449
DEFAULT_K1 = -0.439154
DEFAULT_K2 =  0.321623
DEFAULT_K3 =  -0.143054 
DEFAULT_P1 =    -0.001229
DEFAULT_P2 =  -0.001429

CAMERA_INDEX  = 0          # change if needed

# ── UI constants ─────────────────────────────────────────────────────────────
LABEL_H       = 34
DIVIDER_W     = 3
DIVIDER_COLOR = (255, 215, 0)
FONT          = cv2.FONT_HERSHEY_SIMPLEX
CTRL_WIN      = "Controls  |  R=reset  S=print  G=grid  Q/ESC=quit"
VIEW_WIN      = "Camera Calibration  |  LEFT: distorted   RIGHT: undistorted"

# ── Trackbar encoding helpers ─────────────────────────────────────────────────
# Trackbars only handle integers 0…MAX, so we map each float param to an int
# range and back.

# Focal lengths  200 … 900  (step 0.1)  → int 2000…9000
FXY_SCALE, FXY_MIN, FXY_MAX = 10.0, 200, 900
FXY_INT_MAX = int((FXY_MAX - FXY_MIN) * FXY_SCALE)

# Principal point  0 … frame dimension  (step 0.1) → int 0…MAX
# We use a generous fixed range of 0–1000 px
PP_SCALE, PP_MIN, PP_MAX_PX = 10.0, 0, 1000
PP_INT_MAX = int((PP_MAX_PX - PP_MIN) * PP_SCALE)

# Radial  k1, k2, k3   range -1.5 … +1.5  (step 0.0001) → int 0…30000
K_SCALE, K_MIN, K_MAX = 10000.0, -1.5, 1.5
K_INT_MAX = int((K_MAX - K_MIN) * K_SCALE)

# Tangential  p1, p2  range -0.05 … +0.05  (step 0.000001) → int 0…100000
P_SCALE, P_MIN, P_MAX = 100000.0, -0.05, 0.05
P_INT_MAX = int((P_MAX - P_MIN) * P_SCALE)


def f2i_fxy(v):  return int(round((v - FXY_MIN) * FXY_SCALE))
def i2f_fxy(i):  return FXY_MIN + i / FXY_SCALE

def f2i_pp(v):   return int(round((v - PP_MIN) * PP_SCALE))
def i2f_pp(i):   return PP_MIN + i / PP_SCALE

def f2i_k(v):    return int(round((v - K_MIN) * K_SCALE))
def i2f_k(i):    return K_MIN + i / K_SCALE

def f2i_p(v):    return int(round((v - P_MIN) * P_SCALE))
def i2f_p(i):    return P_MIN + i / P_SCALE


# ── Shared mutable state ──────────────────────────────────────────────────────
state = {
    "fx": DEFAULT_FX, "fy": DEFAULT_FY,
    "cx": DEFAULT_CX, "cy": DEFAULT_CY,
    "k1": DEFAULT_K1, "k2": DEFAULT_K2, "k3": DEFAULT_K3,
    "p1": DEFAULT_P1, "p2": DEFAULT_P2,
    "maps_dirty": True,   # re-compute remap LUTs when True
    "map1": None, "map2": None,
    "show_grid": True,
}

# ── Trackbar callbacks ────────────────────────────────────────────────────────
def cb_fx(v): state["fx"] = i2f_fxy(v); state["maps_dirty"] = True
def cb_fy(v): state["fy"] = i2f_fxy(v); state["maps_dirty"] = True
def cb_cx(v): state["cx"] = i2f_pp(v);  state["maps_dirty"] = True
def cb_cy(v): state["cy"] = i2f_pp(v);  state["maps_dirty"] = True
def cb_k1(v): state["k1"] = i2f_k(v);   state["maps_dirty"] = True
def cb_k2(v): state["k2"] = i2f_k(v);   state["maps_dirty"] = True
def cb_k3(v): state["k3"] = i2f_k(v);   state["maps_dirty"] = True
def cb_p1(v): state["p1"] = i2f_p(v);   state["maps_dirty"] = True
def cb_p2(v): state["p2"] = i2f_p(v);   state["maps_dirty"] = True


def create_controls_window():
    cv2.namedWindow(CTRL_WIN, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(CTRL_WIN, 680, 360)

    cv2.createTrackbar("fx  (focal X)",    CTRL_WIN, f2i_fxy(DEFAULT_FX), FXY_INT_MAX, cb_fx)
    cv2.createTrackbar("fy  (focal Y)",    CTRL_WIN, f2i_fxy(DEFAULT_FY), FXY_INT_MAX, cb_fy)
    cv2.createTrackbar("cx  (principal X)",CTRL_WIN, f2i_pp(DEFAULT_CX),  PP_INT_MAX,  cb_cx)
    cv2.createTrackbar("cy  (principal Y)",CTRL_WIN, f2i_pp(DEFAULT_CY),  PP_INT_MAX,  cb_cy)
    cv2.createTrackbar("k1  radial",       CTRL_WIN, f2i_k(DEFAULT_K1),   K_INT_MAX,   cb_k1)
    cv2.createTrackbar("k2  radial",       CTRL_WIN, f2i_k(DEFAULT_K2),   K_INT_MAX,   cb_k2)
    cv2.createTrackbar("k3  radial",       CTRL_WIN, f2i_k(DEFAULT_K3),   K_INT_MAX,   cb_k3)
    cv2.createTrackbar("p1  tangential",   CTRL_WIN, f2i_p(DEFAULT_P1),   P_INT_MAX,   cb_p1)
    cv2.createTrackbar("p2  tangential",   CTRL_WIN, f2i_p(DEFAULT_P2),   P_INT_MAX,   cb_p2)


def reset_sliders():
    cv2.setTrackbarPos("fx  (focal X)",     CTRL_WIN, f2i_fxy(DEFAULT_FX))
    cv2.setTrackbarPos("fy  (focal Y)",     CTRL_WIN, f2i_fxy(DEFAULT_FY))
    cv2.setTrackbarPos("cx  (principal X)", CTRL_WIN, f2i_pp(DEFAULT_CX))
    cv2.setTrackbarPos("cy  (principal Y)", CTRL_WIN, f2i_pp(DEFAULT_CY))
    cv2.setTrackbarPos("k1  radial",        CTRL_WIN, f2i_k(DEFAULT_K1))
    cv2.setTrackbarPos("k2  radial",        CTRL_WIN, f2i_k(DEFAULT_K2))
    cv2.setTrackbarPos("k3  radial",        CTRL_WIN, f2i_k(DEFAULT_K3))
    cv2.setTrackbarPos("p1  tangential",    CTRL_WIN, f2i_p(DEFAULT_P1))
    cv2.setTrackbarPos("p2  tangential",    CTRL_WIN, f2i_p(DEFAULT_P2))
    state["maps_dirty"] = True


def rebuild_maps(frame_h, frame_w):
    cam_mat = np.array([
        [state["fx"], 0.0,          state["cx"]],
        [0.0,         state["fy"],  state["cy"]],
        [0.0,         0.0,          1.0        ],
    ], dtype=np.float64)
    dist = np.array([[state["k1"], state["k2"],
                      state["p1"], state["p2"],
                      state["k3"]]], dtype=np.float64)
    new_mat, _ = cv2.getOptimalNewCameraMatrix(
        cam_mat, dist, (frame_w, frame_h), alpha=1)
    m1, m2 = cv2.initUndistortRectifyMap(
        cam_mat, dist, None, new_mat, (frame_w, frame_h), cv2.CV_16SC2)
    state["map1"] = m1
    state["map2"] = m2
    state["maps_dirty"] = False


def draw_label(img, text, color):
    h, w = img.shape[:2]
    cv2.rectangle(img, (0, 0), (w, LABEL_H), (20, 20, 20), -1)
    ts, _ = cv2.getTextSize(text, FONT, 0.58, 2)
    cv2.putText(img, text, ((w - ts[0]) // 2, (LABEL_H + ts[1]) // 2),
                FONT, 0.58, color, 2, cv2.LINE_AA)


def draw_grid(img):
    h, w = img.shape[:2]
    c = (0, 200, 80)
    for x in range(0, w, w // 8):  cv2.line(img, (x, 0), (x, h), c, 1)
    for y in range(0, h, h // 6):  cv2.line(img, (0, y), (w, y), c, 1)


def draw_hud(composite, h, w):
    """Bottom-left HUD showing live parameter values."""
    lines = [
        f"fx={state['fx']:.2f}   fy={state['fy']:.2f}   "
        f"cx={state['cx']:.2f}   cy={state['cy']:.2f}",
        f"k1={state['k1']:+.6f}   k2={state['k2']:+.6f}   k3={state['k3']:+.6f}",
        f"p1={state['p1']:+.6f}   p2={state['p2']:+.6f}",
    ]
    for i, line in enumerate(reversed(lines)):
        y = h - 8 - i * 19
        # subtle shadow
        cv2.putText(composite, line, (11, y + 1), FONT, 0.38, (0, 0, 0),    1, cv2.LINE_AA)
        cv2.putText(composite, line, (10, y),     FONT, 0.38, (180,180,180), 1, cv2.LINE_AA)

    # delta indicators (green = closer to default, red = far)
    deltas = {
        "fx": (state["fx"] - DEFAULT_FX) / DEFAULT_FX,
        "k1": state["k1"] - DEFAULT_K1,
        "k2": state["k2"] - DEFAULT_K2,
    }
    dx = w * 2 + DIVIDER_W - 160
    for i, (name, delta) in enumerate(deltas.items()):
        mag  = min(abs(delta) * 4, 1.0)
        r    = int(255 * mag)
        g    = int(255 * (1 - mag))
        col  = (0, g, r)
        text = f"{name}  {'▲' if delta > 0 else '▼'} {delta:+.4f}"
        cv2.putText(composite, text, (dx, h - 8 - i * 19),
                    FONT, 0.38, col, 1, cv2.LINE_AA)


def main():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera {CAMERA_INDEX}. "
                           "Check CAMERA_INDEX or USB connection.")

    ret, frame = cap.read()
    if not ret:
        raise RuntimeError("Could not read from camera.")
    h, w = frame.shape[:2]

    cv2.namedWindow(VIEW_WIN, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(VIEW_WIN, w * 2 + DIVIDER_W, h)

    create_controls_window()

    print("══════════════════════════════════════════════")
    print("  Camera Calibration Interactive Tuner")
    print("  LEFT  – raw (distorted)")
    print("  RIGHT – undistorted (live)")
    print("  R = reset sliders   S = print params")
    print("  G = toggle grid     Q/ESC = quit")
    print("══════════════════════════════════════════════\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Frame grab failed – exiting.")
            break

        # Rebuild remap LUTs only when a slider changed
        if state["maps_dirty"]:
            rebuild_maps(h, w)

        undistorted = cv2.remap(frame, state["map1"], state["map2"], cv2.INTER_LINEAR)

        raw_disp = frame.copy()
        und_disp = undistorted.copy()

        if state["show_grid"]:
            draw_grid(raw_disp)
            draw_grid(und_disp)

        draw_label(raw_disp, "DISTORTED  (original)",    color=(80, 150, 255))
        draw_label(und_disp, "UNDISTORTED  (live tune)", color=(60, 230, 120))

        divider   = np.full((h, DIVIDER_W, 3), DIVIDER_COLOR, dtype=np.uint8)
        composite = np.hstack([raw_disp, divider, und_disp])

        draw_hud(composite, h, w)

        cv2.imshow(VIEW_WIN, composite)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), ord('Q'), 27):
            break
        elif key in (ord('r'), ord('R')):
            reset_sliders()
            print("[R] Parameters reset to default calibration values.")
        elif key in (ord('s'), ord('S')):
            print("\n── Current parameters ──────────────────")
            print(f"  fx = {state['fx']:.6f}   fy = {state['fy']:.6f}")
            print(f"  cx = {state['cx']:.6f}   cy = {state['cy']:.6f}")
            print(f"  k1 = {state['k1']:.6f}   k2 = {state['k2']:.6f}")
            print(f"  k3 = {state['k3']:.6f}")
            print(f"  p1 = {state['p1']:.6f}   p2 = {state['p2']:.6f}")
            print("────────────────────────────────────────")
            print("  numpy copy-paste:")
            print(f"  CAMERA_MATRIX = np.array([[{state['fx']:.6f}, 0, {state['cx']:.6f}],")
            print(f"                            [0, {state['fy']:.6f}, {state['cy']:.6f}],")
            print(f"                            [0, 0, 1]], dtype=np.float64)")
            print(f"  DIST_COEFFS = np.array([[{state['k1']:.6f}, {state['k2']:.6f},")
            print(f"                           {state['p1']:.6f}, {state['p2']:.6f},")
            print(f"                           {state['k3']:.6f}]], dtype=np.float64)\n")
        elif key in (ord('g'), ord('G')):
            state["show_grid"] = not state["show_grid"]
            print(f"[G] Grid overlay {'ON' if state['show_grid'] else 'OFF'}")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
