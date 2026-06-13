# Puzzle-Solver Firmware

Arduino firmware for the autonomous puzzle-solving robot.  
Controls a 3-axis CNC gantry, a Z-arm servo, a rotation servo, and a suction pick-and-place system.
It receives through the serial monitor, from the python code, the custom G-code that controls the components
---

## Hardware

| Component | Description |
|---|---|
| stepper1 / stepper3 | Dual X-axis gantry (both move together) |
| stepper2 | Y axis |
| Servo (bit-banged) | Z up/down arm — pin `A5` |
| Servo (hardware) | Piece rotation — pin `11` |
| Pump + valve | Suction pick-and-place — pins `4` and `7` |
| Endstops | X: pin `9`, Y: pin `10` (INPUT_PULLUP) |

---

## File Structure

```
puzzle_firmware/
├── puzzle_firmware.ino   ← main sketch (setup / loop)
├── config.h              ← ALL tunable parameters (edit this first)
├── steppers.h / .cpp     ← gantry motion
├── pick_place.h / .cpp   ← Z servo + pneumatics
├── rotation.h / .cpp     ← rotation servo
└── parser.h / .cpp       ← serial protocol & command dispatch
```

---

## Configuration

All mechanical parameters, pin assignments, and timing constants live in **`config.h`**.  
You should never need to edit any other file for a basic recalibration.

Key parameters:

| Constant | Default | Meaning |
|---|---|---|
| `STEPS_PER_MM_X` | 10000/245 | X axis calibration |
| `STEPS_PER_MM_Y` | 4000/204 | Y axis calibration |
| `SPEED_X` / `SPEED_Y` | 2000 | Cruise speed (steps/s) |
| `ACCEL_X` / `ACCEL_Y` | 200 / 150 | Acceleration (steps/s²) |
| `PICK_SUCTION_MS` | 3000 | Pump on time during pick |
| `coordMap[col][row]` | see config.h | Grid step-count positions |

---

## Serial Protocol

Connect at **115200 baud**.

Send semicolon-separated commands as a single line:

```
h;x4998s2000;y3724s2000;p1;r45;p0;END
```

### Command Reference - Custom G-code

| Command | Effect |
|---|---|
| `h` | Run homing sequence (must be first command after power-on) |
| `x{pos}s{speed}` | Move X to absolute step position |
| `y{pos}s{speed}` | Move Y to absolute step position |
| `p1` | Pick: lower arm → suction ON → raise |
| `p0` | Place: lower arm → suction OFF → raise |
| `r{angle}` | Rotate piece to `angle` degrees (0–90) |
| `d` | Pause for `CMD_DELAY_MS` milliseconds |
| `END` | Mark end of packet |

### Firmware Replies

| Reply | Meaning |
|---|---|
| `ACK{n}` | Packet n received and executed (no `END` seen) |
| `OK` | Packet fully executed (contained `END`) |
| `ERROR: ...` | Malformed or unknown command |

> **Note:** The speed field in `x`/`y` commands is parsed and echoed back for logging but currently does not override the global speed set in `config.h`.

---

## Calibration and Coordinate Map

The 5x5 grid is defined in `config.h` as `coordMap[col][row]`:

below is the image of our coordinate system where : 

|---|---|---|
| origin | (0,0) | arucoID 0 (dict_6x6_250)| 
| x-axis | (4,0) | arucoID 1 (dict_6x6_250)|
| y-axis | (0,4) | arucoID 2 (dict_6x6_250)|


![Alt text](https://github.com/Makerspace-Amiens-2025-26/Puzzle-Bot-Groupe01/blob/main/docs/images/Coordinate%20system.png?raw=true)


- **Millimeter per unit**  (distance from (0,0) to (0,1), center to center) is 60 mm`

After having setup the stepper motors for the x,y displacement, through experimentations, we found that the center of the arucoID 0 is 
reached at 100 steps in x direction and 196 steps in y direction. 

- **Origin:** ArUco marker #0 → `(100 steps, 196 steps)`
- 
Then, through experiments, we found that the distance covered by 10000 steps is 245 mm along the x-axis and 
the distance covered by 4000 steps is 204 mm along the y-axis. Thus we obtained our parameters :

```cpp
/** Steps per millimetre on the X axis (dual-motor gantry). */
#define STEPS_PER_MM_X   (10000.0f / 245.0f)
/** Steps per millimetre on the Y axis. */
#define STEPS_PER_MM_Y   (4000.0f  / 204.0f)
```
It is critical to repeat these experimenents to find origin location, STEPS_PER_MM_X, STEPS_PER_MM_Y if you consider replicating our machine
since it will depend on mechanical structure of the machine. 

There, when we will later integrate the camera to detection position in terms of our coordinate system, we will be very easily able to determine the number of steps in the x and y directions given the coordinates using the formulas : 

```py
    x_steps = 100 + x_cameraMeasured*STEPS_PER_MM_X*MM_PER_UNIT
    y_steps = 196 + y_cameraMeasured*STEPS_PER_MM_Y*MM_PER_UNIT
```

To make it easier to test at the early stages with no camera integration (see puzzle_solver_2), we calculated all stepps needed for the coordinates all from (0,0) till (4,4). 

```cpp
// ============================================================
//  COORDINATE MAP
//
//  Maps logical grid positions (col 0-4, row 0-4) to raw
//  stepper step counts that position the head over each cell.
//
//  Origin:  ArUco marker #0  →  x=100 steps, y=196 steps
//  Grid pitch: 60 mm         →  ΔX ≈ 2449 steps, ΔY ≈ 1176 steps
//
//  Layout:  coordMap[col][row] = {xSteps, ySteps}
// ============================================================

#define GRID_COLS  5
#define GRID_ROWS  5

static const int coordMap[GRID_COLS][GRID_ROWS][2] = {
    //  row 0          row 1          row 2          row 3          row 4
    { {100,  196}, {100,  1372}, {100,  2548}, {100,  3724}, {100,  4900} }, // col 0
    { {2549, 196}, {2549, 1372}, {2549, 2548}, {2549, 3724}, {2549, 4900} }, // col 1
    { {4998, 196}, {4998, 1372}, {4998, 2548}, {4998, 3724}, {4998, 4900} }, // col 2
    { {7447, 196}, {7447, 1372}, {7447, 2548}, {7447, 3724}, {7447, 4900} }, // col 3
    { {9896, 196}, {9896, 1372}, {9896, 2548}, {9896, 3724}, {9896, 4900} }, // col 4
};
```

To look up the raw step counts for logical position (col=2, row=3):

```cpp
int xSteps = coordMap[2][3][0];   // → 4998
int ySteps = coordMap[2][3][1];   // → 3724
```



---

## Dependencies

- [AccelStepper](https://www.airspayce.com/mikem/arduino/AccelStepper/) — stepper motion with acceleration
- [Servo](https://www.arduino.cc/reference/en/libraries/servo/) — rotation servo (built-in Arduino library)

Install AccelStepper via the Arduino Library Manager or:

```
Sketch → Include Library → Manage Libraries → search "AccelStepper"
```

---

## Known Limitations / TODO

- [ ] The `s{speed}` field in move commands is parsed but not yet applied — motion speed is global.
- [ ] No runtime bounds checking on step positions (moves outside the physical range will stall against endstops).

