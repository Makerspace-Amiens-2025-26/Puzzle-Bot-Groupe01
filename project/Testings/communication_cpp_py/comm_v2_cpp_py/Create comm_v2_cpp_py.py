import serial
import time

# ── config ──────────────────────────────────────────────
PORT      = "COM7"       # change to your port, e.g. /dev/ttyUSB0
BAUDRATE  = 115200
PACKET_SIZE = 20         # max chars per packet (safe for Arduino String memory)
TIMEOUT   = 8            # seconds to wait for ACK

# ── coordinate map ───────────────────────────────────────
coord_map = [
    [ [100, 196],  [100, 1372],  [100, 2548],  [100, 3724],  [100, 4900]  ],
    [ [2549, 196], [2549, 1372], [2549, 2548], [2549, 3724], [2549, 4900] ],
    [ [4998, 196], [4998, 1372], [4998, 2548], [4998, 3724], [4998, 4900] ],
    [ [7447, 196], [7447, 1372], [7447, 2548], [7447, 3724], [7447, 4900] ],
    [ [9896, 196], [9896, 1372], [9896, 2548], [9896, 3724], [9896, 4900] ]
]

piece_location = [ [0,1], [0,4], [2,4], [2,1] ]
aruco_dest     = [ [0,2], [0,3], [1,3], [1,2] ]
SPEED = 200

# ── generate full instruction string ─────────────────────
def generate_instructions():
    result = "h;r0;"
    for i in range(4):
        px, py   = piece_location[i]
        oldPX, oldPY = coord_map[px][py]
        dx, dy   = aruco_dest[i]
        oldDX, oldDY = coord_map[dx][dy]

        result += f"x{oldPX}s{SPEED};"
        result += f"y{oldPY}s{SPEED};"
        result += "p1;"
        result += f"x{oldDX}s{SPEED};"
        result += f"y{oldDY}s{SPEED};"
        result += "p0;"

    result += "END;"   # end marker
    return result

# ── split into safe packets (always cut on ';' boundary) ─
def split_into_packets(full_string, max_size):
    packets = []
    current = ""

    for chunk in full_string.split(";"):
        if not chunk:
            continue
        piece = chunk + ";"
        # if adding this instruction exceeds max_size, flush current packet
        if len(current) + len(piece) > max_size:
            if current:
                packets.append(current)
            current = piece
        else:
            current += piece

    if current:
        packets.append(current)

    return packets

# ── send with ACK handshake ───────────────────────────────
def send_instructions(ser, packets):
    for i, packet in enumerate(packets):
        print(f"[→] Sending packet {i}: {repr(packet)}")
        ser.write(packet.encode())

        # wait for ACK or OK
        start = time.time()
        while True:
            if time.time() - start > TIMEOUT:
                print(f"[!] Timeout waiting for response on packet {i}")
                return False

            if ser.in_waiting:
                response = ser.readline().decode(errors="ignore").strip()
                print(f"[←] Arduino: {response}")

                if response.startswith("ACK"):
                    break  # good, send next packet
                elif response.startswith("OK"):
                    print("[✓] All instructions completed.")
                    return True
                # ignore debug lines (like ">>> received...")

    return False

# ── main ─────────────────────────────────────────────────
def main():
    full = generate_instructions()
    print(f"[i] Full string: {full}")

    packets = split_into_packets(full, PACKET_SIZE)
    print(f"[i] Split into {len(packets)} packets:")
    for i, p in enumerate(packets):
        print(f"    [{i}] {repr(p)}")

    with serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT) as ser:
        time.sleep(2)  # wait for Arduino reset
        ser.reset_input_buffer()
        print("[i] Connected. Sending instructions...\n")
        send_instructions(ser, packets)

if __name__ == "__main__":
    main()
