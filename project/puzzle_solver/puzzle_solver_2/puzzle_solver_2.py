import serial
import time

# ── config ───────────────────────────────────────────────
PORT        = "COM8"
BAUDRATE    = 115200
PACKET_SIZE = 30
TIMEOUT     = 100
SPEED = 200

# ── coordinate map ───────────────────────────────────────
coord_map = [
    [ [100, 196],  [100, 1372],  [100, 2548],  [100, 3724],  [100, 4900]  ],
    [ [2549, 196], [2549, 1372], [2549, 2548], [2549, 3724], [2549, 4900] ],
    [ [4998, 196], [4998, 1372], [4998, 2548], [4998, 3724], [4998, 4900] ],
    [ [7447, 196], [7447, 1372], [7447, 2548], [7447, 3724], [7447, 4900] ],
    [ [9896, 196], [9896, 1372], [9896, 2548], [9896, 3724], [9896, 4900] ]
]

piece_location = [ [0,1], [0,4], [2,4], [2,1] ]
piece_angles   = [ -100,   100,  100,   100  ]
piece_dest     = [ [0,2], [0,3], [1,3], [1,2] ]



# ── instruction builder ──────────────────────────────────
g_code_string = ""

def goto(pos):
    global g_code_string
    oldX, oldY = coord_map[pos[0]][pos[1]]
    g_code_string += f"x{oldX}s{SPEED};"
    g_code_string += f"y{oldY}s{SPEED};"

def pick():
    global g_code_string
    g_code_string += "p1;"
    
def delay():
    global g_code_string
    g_code_string += "d;"

def place():
    global g_code_string
    g_code_string += "p0;"

def rotate(angle):
    global g_code_string
    g_code_string += f"r{angle};"

# maximum angle possible is 90 ; so we adapt for higher and negative angles 
def rotation_management(angle):
    # delays below are need to allow enough time to switch from rotation to pick/place and vice-versa
    if abs(angle) == 180:
        pick()
        delay()  ##############
        rotate(90)
        delay()  ##############
        place()
        delay()  ##############
        rotate(0)
        delay()  ##############
        pick()
        delay()  ##############
        rotate(90)
        delay()  ##############

    elif angle > 0:
        alpha = 0
        if angle > 90:
            pick()
            delay()  ##############
            rotate(90)
            delay()  ##############
            place()
            delay()  ##############
            rotate(0)
            alpha = 90
            delay()  ##############
        
        pick()
        delay()  ##############
        rotate(angle - alpha)

    elif angle < 0:
        alpha = 0
        if -angle > 90:
            rotate(90)
            delay()  ##############
            pick()
            delay()  ##############
            rotate(0)
            delay()  ##############
            place()
            alpha = 90
            delay()  ##############
        rotate(-angle - alpha)
        delay()  ##############
        pick()
        delay()  ##############
        rotate(0)

    else:  # angle == 0
        pick()

# ── solving the puzzle ──────────────────────────────────────
def generate_instructions():
    global g_code_string
    g_code_string = "h;r0;"

    for i in range(4):
        goto(piece_location[i])
        rotation_management(piece_angles[i])
        goto(piece_dest[i])
        place()
        rotate(0)

    g_code_string += "h;END;"

# ── communication with the Arduino UNO though serial monitor──
def split_into_packets(full_string, max_size):
    packets = []
    current = ""

    for chunk in full_string.split(";"):
        if not chunk:
            continue
        piece = chunk + ";"
        if len(current) + len(piece) > max_size:
            if current:
                packets.append(current)
            current = piece
        else:
            current += piece

    if current:
        packets.append(current)

    return packets

def send_instructions(ser, packets):
    for i, packet in enumerate(packets):
        print(f"[→] Sending packet {i}: {repr(packet)}")
        ser.write(packet.encode())

        start = time.time()
        while True:
            if time.time() - start > TIMEOUT:
                print(f"[!] Timeout waiting for response on packet {i}")
                return False

            if ser.in_waiting:
                response = ser.readline().decode(errors="ignore").strip()
                print(f"[←] Arduino: {response}")

                if response.startswith("ACK"):
                    break
                elif response.startswith("OK"):
                    print("[✓] All instructions completed.")
                    return True

    return False

# ── main ─────────────────────────────────────────────────
def main():
    generate_instructions()
    print(f"[i] Full string:\n{g_code_string}\n")

    packets = split_into_packets(g_code_string, PACKET_SIZE)
    print(f"[i] Split into {len(packets)} packets:")
    for i, p in enumerate(packets):
        print(f"    [{i}] {repr(p)}")

    with serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT) as ser:
        time.sleep(2)
        ser.reset_input_buffer()
        print("[i] Connected. Sending instructions...\n")
        send_instructions(ser, packets)

if __name__ == "__main__":
    main()