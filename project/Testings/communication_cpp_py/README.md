# Python ↔ Arduino Serial Communication — Demo Protocols

Two self-contained demos that establish and test the serial communication layer between a Python host and an Arduino UNO. These are **not** the puzzle solver — they are the building blocks that the puzzle solver's communication protocol was derived from.

In both versions: **upload the `.cpp` first, then run the `.py`** (with the correct COM port set). Keep the USB cable connected throughout.

---

## Why Two Versions?

### The core problem

Sending a long string of instructions over serial to an Arduino is not trivial:

- The Arduino's `String` class has limited heap memory — large strings cause corruption or crashes.
- You cannot simply dump everything at once and hope it arrives intact.
- You need a **handshake**: Python must know the Arduino has finished executing a chunk before sending the next one.

The two versions solve this progressively:

| | v1 | v2 |
|---|---|---|
| Instruction format | One command per line (`\n`-separated) | Commands separated by `;`, sent in packets |
| Who triggers send | Human types `s` | Automatic |
| Packet splitting | No — entire buffer sent at once | Yes — safe chunks of `PACKET_SIZE` chars |
| Arduino memory risk | High for long sequences | Low — Arduino only holds one packet at a time |
| Handshake | `ff` trigger → ACK + full echo | Per-packet `ACK{n}` → `OK` on `END` |
| Use case | Manual testing / debugging | Automated sequences, production use |

---

## Version 1 — Interactive Manual Sender

**Files:** `comm_v1_cpp_py.cpp` · `comm_v1_cpp_py.py`

### What it does

The Python side is an interactive terminal. You type commands one by one; they accumulate in a local buffer. When you type `s`, the entire buffer is sent to the Arduino in one go. The Arduino accumulates the lines, and when it receives the special marker `ff`, it sends back an ACK and echoes every received command back to Python line by line.

### Protocol

```
Python                                Arduino
  │                                      │
  │  x100s200\n                          │
  │ ────────────────────────────────────►│  appended to full_code
  │  y50s100\n                           │
  │ ────────────────────────────────────►│  appended to full_code
  │  p1\n                                │
  │ ────────────────────────────────────►│  appended to full_code
  │  ff\n           (send trigger)       │
  │ ────────────────────────────────────►│
  │                                      │  prints "Codes Received from Arduino"
  │◄────────────────────────────────────│  echoes each line back
  │◄────────────────────────────────────│  prints "END"
  │                                      │  resets full_code = ""
```

The `ff` marker is the commit signal — it tells the Arduino "I'm done sending, now acknowledge and echo back."

### Python terminal usage

```
Enter commands one by one. Type 's' to send all, 'q' to quit.

Enter command: x100s200
  [Appended] Buffer so far: 'x100s200\n'

Enter command: p1
  [Appended] Buffer so far: 'x100s200\np1\n'

Enter command: s

  [Sending]:
'x100s200\np1\nff\n'
  [Waiting for Arduino acknowledgement...]
  Arduino ACK: Codes Received from Arduino
  [Full echo received]:
    x100s200
    p1
```

Valid commands — first character must be one of: `x X y Y p P r R`. Anything else is rejected locally before being added to the buffer.

### Key limitation

The entire buffer is sent at once before the Arduino does anything with it. For long sequences, the Arduino's `full_code` string grows unboundedly in RAM — this is the problem v2 solves.

---

## Version 2 — Automated Packet Sender with ACK Handshake

**Files:** `comm_v2_cpp_py.cpp` · `Create_comm_v2_cpp_py.py`

### What it does

Python builds the full instruction string automatically (no human typing), splits it into small chunks that are safe for Arduino memory, and sends them one at a time. Each chunk is sent only after the previous one is acknowledged. The Arduino signals completion of the full sequence with `OK` when it sees the `END` command.

### Why packet splitting is necessary

The Arduino UNO has **2 KB of SRAM**. A long instruction string like:

```
h;r0;x100s200;y196s200;p1;x2549s200;y1372s200;p0;x4998s200;...
```

can easily exceed what the Arduino can safely hold as a single `String`. Splitting into packets of `PACKET_SIZE` characters (default: 20) means the Arduino only ever holds a small slice in memory at a time.

The split always happens **on a `;` boundary** — never in the middle of a command — so the Arduino always receives complete, parseable instructions.

### Protocol

```
Python                                      Arduino
  │                                            │
  │  "h;r0;x100s200;"    (packet 0)            │
  │ ──────────────────────────────────────────►│  parses: h, r0, x100s200
  │                                            │  executes each command
  │◄──────────────────────────────────────────│  "ACK0"
  │                                            │
  │  "y196s200;p1;"       (packet 1)           │
  │ ──────────────────────────────────────────►│  parses: y196s200, p1
  │◄──────────────────────────────────────────│  "ACK1"
  │                                            │
  │  ...                                       │
  │                                            │
  │  "p0;END;"            (last packet)        │
  │ ──────────────────────────────────────────►│  parses: p0, END
  │                                            │  sets instructions_done = true
  │◄──────────────────────────────────────────│  "OK"
```

Python never sends the next packet until it receives `ACK{n}` for the current one. This prevents buffer overrun on the Arduino side.

### Arduino reply summary

| Reply | Meaning |
|---|---|
| `ACK{n}` | Packet `n` received and executed — send next packet |
| `OK` | `END` command reached — full sequence complete |

### How `split_into_packets()` works

```python
for chunk in full_string.split(";"):
    piece = chunk + ";"
    if len(current) + len(piece) > PACKET_SIZE:
        packets.append(current)   # flush current packet
        current = piece
    else:
        current += piece
```

Commands are greedily packed into the current packet until adding the next one would exceed `PACKET_SIZE`. At that point the current packet is flushed and a new one starts. A command is never split mid-token.

---

## Setup

### Requirements

```bash
pip install pyserial
```

### Steps (same for both versions)

1. Open the `.cpp` file in the Arduino IDE.
2. Upload it to the Arduino UNO.
3. Note the COM port shown in the IDE (e.g. `COM7` on Windows, `/dev/ttyUSB0` on Linux).
4. Open the matching `.py` and set the port:
   - v1: `ser = serial.Serial('COM7', ...)`
   - v2: `PORT = "COM7"`
5. **Close the Arduino Serial Monitor** if it is open — Python and the Serial Monitor cannot share the port.
6. Run the Python script.

> The USB cable must stay connected while Python is running.

---

## File Summary

| File | Role |
|---|---|
| `comm_v1_cpp_py.cpp` | Arduino firmware for v1: accumulates lines, echoes all on `ff` |
| `comm_v1_cpp_py.py` | Python terminal for v1: interactive command entry and manual send |
| `comm_v2_cpp_py.cpp` | Arduino firmware for v2: parses `;`-separated packets, replies `ACK`/`OK` |
| `Create_comm_v2_cpp_py.py` | Python for v2: builds instruction string, splits into packets, sends with handshake |

---

## Relationship to the Puzzle Solver

These demos are the direct ancestors of the protocol used in the puzzle solver:

- The **command syntax** (`x`, `y`, `p`, `r`) was prototyped in v1's `parseCommand()`.
- The **packet + ACK handshake** from v2 is exactly what `puzzle_solver_2/3/4.py` and `puzzle_firmware.ino` use in production.
- `PACKET_SIZE`, `split_into_packets()`, and `send_instructions()` from v2 were carried forward directly into the puzzle solver scripts without modification.
