# Puzzle Solver 4 — Full Camera Detection (Position + Angle)

Python controller for the puzzle-solving robot — **Version 4**.  
Extends v3 by also detecting piece **angles** from the camera — no more manual input required for positions or angles.

> For everything not mentioned here (file structure, serial protocol, setup steps, TPS position correction, camera pipeline stages, rotation management) refer to **README_v3.md**.

---

## What's New vs Version 3

| Feature | v3 | v4 |
|---|---|---|
| Piece positions | Camera ✓ | Camera ✓ |
| Piece angles | **Manual** | **Camera ✓** |
| `main_find_aruco()` return type | `(x, y)` | `(x, y, angle)` |

---

## How Angle Detection Works

### Concept

Every ArUco marker has four corners returned by the detector in a fixed order: **TL, TR, BR, BL**. These four points naturally define two perpendicular axes:

- **Horizontal axis:** TL → TR (top edge)
- **Vertical axis:** TL → BL (left edge)

Rather than measuring the target piece's angle relative to the image frame (which would be affected by how the camera is physically mounted), the angle is measured **relative to the origin marker (ID 0)**. Its top-edge vector defines the "zero angle" of the board as seen by the camera — so any camera tilt or rotation is automatically cancelled out.

![Alt text](https://github.com/Makerspace-Amiens-2025-26/Puzzle-Bot-Groupe01/blob/main/docs/images/angle_detection.png?raw=true)


### Algorithm

```
For the last averaged frame:

1. Extract corner vectors for ID 0 (origin) and the target marker:
       vec_origin_h  =  TR − TL   of marker ID 0
       vec_target_h  =  TR − TL   of target marker
       vec_target_v  =  BL − TL   of target marker

2. Compute angles relative to camera X-axis (atan2):
       angle_origin  =  atan2(vec_origin_h)
       angle_h       =  atan2(vec_target_h) − angle_origin
       angle_v       =  atan2(vec_target_v) − angle_origin

3. Wrap both into [−90°, 90°]:
       while a >  90 : a -= 180
       while a <= −90 : a += 180
       (ArUco markers are ambiguous at 180° — the detector can't distinguish
        a marker rotated +91° from one rotated −89°, so wrapping is lossless)

4. The two wrapped angles are complementary by construction (|angle_h − angle_v| ≈ 90°).
   Return the one with the smaller absolute value:
       angle = angle_h  if |angle_h| ≤ |angle_v|  else  angle_v
```

This gives a robust, unambiguous rotation measurement in **[−90°, 90°]** regardless of which physical edge the detector anchored on.

### Sign convention

`main_find_aruco()` returns the raw camera angle. In `generate_instructions()` the sign is **negated** before being passed to `rotation_management()`:

```python
piece_angles = [-angle for _, _, angle in coords]
```

This maps the camera's coordinate convention to the robot's rotation direction (positive = clockwise for the servo).

---

## Changes in `generate_instructions()`

In v3, positions came from the camera and angles were set manually:

```python
# v3
piece_location = main_find_aruco()   # returns [(x,y), ...]
# piece_angles set manually at top of file
```

In v4, both come from the camera in a single call:

```python
# v4
coords = main_find_aruco()                          # returns [(x, y, angle), ...]
piece_location = [[x, y] for x, y, _ in coords]
piece_angles   = [-angle for _, _, angle in coords]  # sign flip: camera → robot convention
```

Everything downstream (`goto()`, `rotation_management()`, `place()`, `rotate(0)`) is unchanged.

---

## Known Limitations / TODO

- [ ] Angle is computed from the **last** collected frame only (not averaged over `NUM_FRAMES_AVERAGE` like position). A noisy final frame could give a slightly off angle.
- [ ] If either the origin marker (ID 0) or the target marker is not detected in that last frame, angle defaults to `0.0` with a warning — no retry.
- [ ] All other limitations from v3 still apply (no detection timeout, etc.) — see README_v3.md.
