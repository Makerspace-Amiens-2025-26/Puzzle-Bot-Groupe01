# Puzzle Solver — Python Controller

Python-side controller for the puzzle-solving robot.
Generates a sequence of motion/pick-place instructions, splits them into serial packets, and sends them to the Arduino firmware over USB.

> **No camera integration yet.**  
> Piece positions and angles are entered manually in `config` at the top of the script.

---

## How It Works

### Overview

```
puzzle_solver.py
      │
      ├─ generate_instructions()
      │       │
      │       ├─ for each puzzle piece:
      │       │       goto(current position)
      │       │       rotation_management(angle)   ← handles multi-step rotations, pick() stis inside
      │       │       goto(destination)
      │       │       place()
      │       │       rotate(0)                    ← reset rotation servo
      │       │
      │       └─ produces one long semicolon-delimited string
      │              e.g.  "h;r0;x4998s200;y3724s200;p1;r45;..."
      │
      ├─ split_into_packets(string, PACKET_SIZE)
      │       └─ splits the string into chunks ≤ PACKET_SIZE chars,
      │          never cutting in the middle of a command
      │
      └─ send_instructions(ser, packets)
              └─ sends one packet at a time, waits for ACK/OK before sending the next
```

### Coordinate system

- Three ArUco markers (0, 1, 2) define the physical reference frame.
- The grid is 5 × 5. Each cell is identified by `(col, row)` — both 0-indexed.
- `coord_map[col][row]` gives the raw X/Y step counts sent to the firmware.

### Rotation management

The rotation servo has a maximum range of **90°**.  
For angles beyond ±90° the piece is picked, rotated 90°, placed, then picked again to continue — handled automatically by `rotation_management(angle)`.

| Angle range | Strategy |
|---|---|
| `0` | Pick only |
| `0 < angle ≤ 90` | Pick → rotate(angle) |
| `90 < angle ≤ 180` | Pick → rotate(90) → place → rotate(0) → pick → rotate(angle−90) |
| `−90 ≤ angle < 0` | rotate(−angle) → pick → rotate(0) |
| `−180 ≤ angle < −90` | rotate(90) → pick → rotate(0) → place → rotate(−angle−90) → pick → rotate(0) |
| `±180` | rotate(90) → pick → rotate(0) → place → rotate(90) → pick → rotate(0)|

---

## Setup

### Requirements

```bash
pip install pyserial
```

### Connect the hardware

1. Upload `firmware/puzzle_firmware.ino` to the Arduino UNO using the Arduino IDE.
2. Keep the **USB cable connected** — it is the serial link used while Python is running.
3. Open the Arduino IDE **Serial Monitor** (115200 baud) to check the firmware printed:
   ```
   Firmware ready. Send commands: ...
   ```
4. Note the COM port shown in the Arduino IDE (e.g. `COM8` on Windows, `/dev/ttyUSB0` on Linux).
5. Close the Serial Monitor — **it must be closed before running Python** (only one program can use the port at a time).

---

## Configuration

Open `puzzle_solver.py` and edit the block at the top:

```python
PORT        = "COM8"      # ← change to your COM port
BAUDRATE    = 115200      # must match firmware (do not change)
PACKET_SIZE = 30          # max characters per serial packet
TIMEOUT     = 100         # seconds to wait for Arduino response
SPEED       = 200         # motion speed sent in x/y commands (steps/s)
```

Regarding the angles, if we do rotate(45), he will do it in the [(o,y), (o,x)], so we adopted it as the positive direction. Notice that you should enter the angles in the opposite direction of how you place them : if you set the angle of a piece to 30 degrees, you should manually rotate it -30 degrees before the execution of the code.   

Then set the puzzle state:


```python
# Current grid positions of each piece  (col, row)
piece_location = [ [0,1], [0,4], [2,4], [2,1] ]

# Current angle of each piece in degrees (from -179 to 180 degrees)
piece_angles   = [ -100,   100,  100,   100  ]

# Destination grid position for each piece  (col, row)
piece_dest     = [ [0,2], [0,3], [1,3], [1,2] ]
```

`piece_location[i]`, `piece_angles[i]`, and `piece_dest[i]` all refer to the **same piece**.

---

## Running

- Run firmware/puzzle_firmware.ino
- see the COM port used and use in the code in python ;
- Run python 

```bash
python puzzle_solver.py
```

(needless to say, the upload cable should stay connected to the arduino UNO while python is running)


Expected output:

```
[i] Full string:
h;r0;x100s200;y196s200;...;h;END;

[i] Split into 12 packets:
    [0] 'h;r0;x100s200;'
    [1] 'y196s200;p1;'
    ...

[i] Connected. Sending instructions...

[→] Sending packet 0: 'h;r0;x100s200;'
[←] Arduino: >>> received 3 instruction(s):
[←] Arduino:   [0] h
[←] Arduino:   [1] r0
[←] Arduino:   [2] x100s200
[←] Arduino: ACK0
[→] Sending packet 1: ...
...
[←] Arduino: OK
[✓] All instructions completed.
```

---

## Serial Protocol (summary)

| Direction | Message | Meaning |
|---|---|---|
| Python → Arduino | `h;x100s200;y196s200;p1;` | Packet of semicolon-delimited commands |
| Arduino → Python | `ACK{n}` | Packet `n` received and executed, send next |
| Arduino → Python | `OK` | `END` command reached — all done |
| Arduino → Python | `ERROR: ...` | Unknown or malformed command |

Full command reference is in `firmware/README.md`.

---

## File Structure

```
puzzle_folder/
└── puzzle_solver.py      ← this script

firmware/
├── puzzle_firmware.ino
├── config.h
├── steppers.h / .cpp
├── pick_place.h / .cpp
├── rotation.h / .cpp
├── parser.h / .cpp
└── README.md
```
