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

## Coordinate Map

The 5x5 grid is defined in `config.h` as `coordMap[col][row]`:

- **Origin:** ArUco marker #0 → `(100 steps, 196 steps)`
- **Grid pitch:** 60 mm → ΔX ≈ 2449 steps, ΔY ≈ 1176 steps

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

