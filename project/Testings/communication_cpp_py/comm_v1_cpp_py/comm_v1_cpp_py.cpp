String command   = "";
String full_code = "";

int extractNumber(String str, int from) {
    String numStr = "";
    for (int i = from; i < str.length(); i++) {
        char c = str.charAt(i);
        if (isDigit(c)) {
            numStr += c;
        } else if (numStr.length() > 0) {
            break;
        }
    }
    return numStr.toInt();
}

void parseCommand(String cmd) {
    cmd.trim();
    if (cmd.length() == 0) return;
    char first = cmd.charAt(0);

    if (first == 'x' || first == 'X') {
        int s_index = cmd.indexOf('s');
        if (s_index == -1) s_index = cmd.indexOf('S');
        int position = extractNumber(cmd, 1);
        int speed    = (s_index != -1) ? extractNumber(cmd, s_index + 1) : 0;
        Serial.print("Move X → position: "); Serial.print(position);
        Serial.print("  speed: ");           Serial.println(speed);
    }
    else if (first == 'y' || first == 'Y') {
        int s_index = cmd.indexOf('s');
        if (s_index == -1) s_index = cmd.indexOf('S');
        int position = extractNumber(cmd, 1);
        int speed    = (s_index != -1) ? extractNumber(cmd, s_index + 1) : 0;
        Serial.print("Move Y → position: "); Serial.print(position);
        Serial.print("  speed: ");           Serial.println(speed);
    }
    else if (first == 'p' || first == 'P') {
        int value = extractNumber(cmd, 1);
        if      (value == 1) Serial.println("PICK → servo down | pump ON | servo up");
        else if (value == 0) Serial.println("PLACE → servo down | pump OFF | servo up");
        else                 Serial.println("ERROR: p command must be p0 or p1");
    }
    else if (first == 'r' || first == 'R') {
        int angle = extractNumber(cmd, 1);
        Serial.print("ROTATE → "); Serial.print(angle); Serial.println(" degrees");
    }
    else {
        Serial.print("ERROR: unknown command → "); Serial.println(cmd);
    }
}

void setup() {
    Serial.begin(115200);
}

void loop() {
    if (Serial.available() > 0) {
        char c = Serial.read();

        if (c == '\n' || c == '\r') {
            command.trim();

            if (command.length() > 0) {

                if (command == "ff") {
                    // Send ACK first
                    Serial.println("Codes Received from Arduino");

                    // Echo back line by line
                    int start = 0;
                    for (int i = 0; i <= full_code.length(); i++) {
                        if (i == full_code.length() || full_code.charAt(i) == '\n') {
                            String line = full_code.substring(start, i);
                            if (line.length() > 0) {
                                Serial.println(line);
                            }
                            start = i + 1;
                        }
                    }

                    Serial.println("END");   // marks end of echo
                    full_code = "";          // reset for next batch
                }
                else {
                    full_code.concat(command);
                    full_code.concat("\n");
                }

                command = "";
            }

        } else {
            command += c;
        }
    }
}
