import serial
import time

# verify which port was used during the cpp code upload
ser = serial.Serial('COM7', 115200, timeout=1)
time.sleep(2)

VALID_COMMANDS = ('x', 'X', 'y', 'Y', 'p', 'P', 'r', 'R')

def is_valid_command(cmd: str) -> bool:
    if len(cmd) == 0:
        return False
    return cmd[0] in VALID_COMMANDS

def send_code_to_monitor(g_code: str):
    full_string = g_code + "ff\n"
    print(f"\n  [Sending]:\n{repr(full_string)}")

    for line in full_string.split('\n'):
        if line:
            ser.write((line + '\n').encode())
            ser.flush()
            time.sleep(0.05)

    print("  [Waiting for Arduino acknowledgement...]")
    timeout = time.time() + 10
    received_lines = []
    while time.time() < timeout:
        if ser.in_waiting > 0:
            response = ser.readline().decode().strip()
            if response == "Codes Received from Arduino":
                print(f"  Arduino ACK: {response}")
            elif response == "END":
                print("  [Full echo received]:")
                for line in received_lines:
                    print(f"    {line}")
                break
            elif response:
                received_lines.append(response)
        time.sleep(0.05)

g_code_string = ""
print("Enter commands one by one. Type 's' to send all, 'q' to quit.")

while True:
    key = input("Enter command: ").strip()

    if key == 'q':
        print("Exiting...")
        break

    elif key == 's':
        if g_code_string == "":
            print("  [Nothing to send]")
        else:
            send_code_to_monitor(g_code_string)
            g_code_string = ""

    elif is_valid_command(key):
        g_code_string += key + '\n'
        print(f"  [Appended] Buffer so far:\n{repr(g_code_string)}")

    else:
        print(f"  [Invalid command '{key}' — not added]")

ser.close()
