"""
Camera Calibration Script
─────────────────────────
HOW TO USE:
  1. Print the checkerboard:
       https://github.com/opencv/opencv/blob/master/doc/pattern.png
     (it's a 9x6 inner-corner board — tape it flat on a rigid surface)

  2. Mount your camera at the EXACT height/position it will be in production.

  3. Run this script — it will open your webcam live.
     Move the checkerboard around under the camera (tilt, rotate, different positions).
     Press SPACE to capture a frame when the board is detected (green corners = detected).
     Capture at least 15 good frames, then press Q to run calibration.

  4. The script prints your camera_matrix and dist_coeffs — copy them into aruco_pose.py.

Requirements:
    pip install opencv-contrib-python numpy
"""

import cv2
import numpy as np

# ─────────────────────────────────────────────
# CONFIG — must match YOUR printed checkerboard
# ─────────────────────────────────────────────
CHECKERBOARD     = (9, 6)       # number of INNER corners (columns, rows)
                                # The standard OpenCV pattern.png is 9x6
SQUARE_SIZE_MM   = 25.0         # size of one square on your printout in mm        
                                # measure with a ruler after printing!
MIN_CAPTURES     = 15           # minimum good frames before calibration runs
WEBCAM_INDEX     = 0            # 0 = built-in webcam


# ─────────────────────────────────────────────
# PREPARE 3D OBJECT POINTS
# e.g. (0,0,0), (25 ,0,0), (50,0,0) ... in mm
# ─────────────────────────────────────────────
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)
objp *= SQUARE_SIZE_MM

objpoints = []   # 3D points in real world space
imgpoints = []   # 2D points in image plane


# ─────────────────────────────────────────────
# LIVE CAPTURE LOOP   
# ─────────────────────────────────────────────
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
#cap = cv2.VideoCapture(WEBCAM_INDEX, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("[✗] Cannot open webcam.")
    exit()

capture_count = 0
print(f"[✓] Webcam opened.")
print(f"    Move the checkerboard around under the camera.")
print(f"    SPACE = capture frame  |  Q = run calibration (need {MIN_CAPTURES} captures first)\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    found, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)

    display = frame.copy()

    if found:
        # Refine corner locations to sub-pixel accuracy
        corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        cv2.drawChessboardCorners(display, CHECKERBOARD, corners_refined, found)
        status_text = f"Board detected! SPACE to capture ({capture_count}/{MIN_CAPTURES})"
        color = (0, 255, 0)
    else:
        status_text = f"No board detected... ({capture_count}/{MIN_CAPTURES} captured)"
        color = (0, 0, 255)

    cv2.putText(display, status_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.putText(display, "SPACE=capture  Q=calibrate", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
    cv2.imshow("Camera Calibration — Move checkerboard around", display)

    key = cv2.waitKey(1) & 0xFF

    if key == ord(' ') and found:
        objpoints.append(objp)
        imgpoints.append(corners_refined)
        capture_count += 1
        print(f"  [+] Captured frame {capture_count}")

    elif key == ord('q'):
        if capture_count < MIN_CAPTURES:
            print(f"[!] Only {capture_count} captures — need at least {MIN_CAPTURES}. Keep going!")
        else:
            break

cap.release()
cv2.destroyAllWindows()


# ─────────────────────────────────────────────
# RUN CALIBRATION
# ─────────────────────────────────────────────
if capture_count < MIN_CAPTURES:
    print("[✗] Not enough captures to calibrate. Re-run and capture more frames.")
    exit()

print(f"\n[...] Running calibration on {capture_count} frames...")

h, w = gray.shape
ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
    objpoints, imgpoints, (w, h), None, None
)

# ─────────────────────────────────────────────
# REPROJECTION ERROR (lower = better, <1.0 is good)
# ─────────────────────────────────────────────
mean_error = 0
for i in range(len(objpoints)):
    imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], camera_matrix, dist_coeffs)
    error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
    mean_error += error
reprojection_error = mean_error / len(objpoints)

# ─────────────────────────────────────────────
# PRINT RESULTS — copy these into aruco_pose.py
# ─────────────────────────────────────────────
print("\n" + "="*60)
print(" CALIBRATION COMPLETE")
print(f"   Reprojection error: {reprojection_error:.4f}  (< 1.0 is good)")
print("="*60)

print("\n Copy these values into aruco_pose.py:\n")

print("CAMERA_MATRIX = np.array([")
for row in camera_matrix:
    print(f"    [{row[0]:.6f}, {row[1]:.6f}, {row[2]:.6f}],")
print("], dtype=np.float64)\n")

d = dist_coeffs.flatten()
print(f"DIST_COEFFS = np.array([[{d[0]:.6f}, {d[1]:.6f}, "
      f"{d[2]:.6f}, {d[3]:.6f}, {d[4]:.6f}]], "
      f"dtype=np.float64)")

# ─────────────────────────────────────────────
# SAVE TO FILE as well
# ─────────────────────────────────────────────
np.savez("camera_calibration.npz",
         camera_matrix=camera_matrix,
         dist_coeffs=dist_coeffs)
print("\n[✓] Also saved to 'camera_calibration.npz' for later use.")
