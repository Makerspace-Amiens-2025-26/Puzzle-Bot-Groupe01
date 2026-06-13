bool instructions_done;
int packet_number;

void parseCommand(String cmd) {
    if (cmd == "END") {
        instructions_done = true;
    } else {
        Serial.print("Command received ");
        Serial.print(cmd);
        delay(1000);
        Serial.println(" done.");
    }
}

#define MAX_INSTRUCTIONS 20
String instructions[MAX_INSTRUCTIONS];
int instructionCount = 0;

void parseInstructions(String raw) {
    instructionCount = 0;
    int start = 0;

    for (int i = 0; i <= raw.length(); i++) {
        if (raw[i] == ';' || raw[i] == '\0') {
            String instr = raw.substring(start, i);
            instr.trim();
            if (instr.length() > 0 && instructionCount < MAX_INSTRUCTIONS) {
                instructions[instructionCount++] = instr;
            }
            start = i + 1;
        }
    }
}

void setup() {
    instructions_done = false;
    packet_number = 0;
    Serial.begin(115200);
    delay(1000);
    Serial.println("Setup done.");
}

void loop() {
    if (Serial.available() > 0) {
        String raw = Serial.readString();
        raw.trim();

        if (raw.length() > 0) {
            instructions_done = false;  // reset for each packet
            parseInstructions(raw);

            Serial.print(">>> received ");
            Serial.print(instructionCount);
            Serial.println(" instructions:");

            for (int i = 0; i < instructionCount; i++) {
                Serial.print("  [");
                Serial.print(i);
                Serial.print("] ");
                Serial.println(instructions[i]);
                parseCommand(instructions[i]);
            }

            if (instructions_done) {
                Serial.println("OK");
                packet_number = 0;
            } else {
                Serial.print("ACK");
                Serial.println(packet_number++);
            }
        }
    }
}
