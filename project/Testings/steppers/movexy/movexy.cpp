// ============================================================
//  MINIMAL STEPPER FIRMWARE — with HOMING
//  Commands entered in serial monitor:
//    x{pos}s{speed}  → move X
//    y{pos}s{speed}  → move Y
//    h               → homing (X then Y)
// ============================================================


/*
  This firmware provides a lightweight serial‑controlled interface for testing and driving the three stepper motors connected to a CNC Shield V3. 
  It supports direct movement commands for the X and Y axes, as well as a dedicated homing routine triggered by the h instruction.
  The homing sequence uses mechanical endstop switches to establish a precise and repeatable origin: each axis first approaches its switch at high speed, 
  retracts slightly, then slowly approaches again to compensate for switch hysteresis and mechanical play. Once contact is detected during the slow pass,
  the motor position is reset to zero, defining an accurate (0,0) reference point. This minimal firmware is ideal for debugging motion,
  validating mechanics, and observing stepper behavior without any additional pick‑and‑place or servo‑related features.
*/

#include <AccelStepper.h>

const int endstopPinY = 10;
const int endstopPinX = 9;

// Stepper X
AccelStepper stepper1(1, 2, 5);

// Stepper Y
AccelStepper stepper2(1, 3, 6);

// Stepper A (copy of X)
AccelStepper stepper3(1, 12, 13);

const byte enablePin = 8;

String command = "";

// ============================================================
//  PARSE HELPERS
// ============================================================

int extractNumber(String str, int from) {
    String numStr = "";
    for (int i = from; i < str.length(); i++) {
        char c = str.charAt(i);
        if (isDigit(c)) numStr += c;
        else if (numStr.length() > 0) break;
    }
    return numStr.toInt();
}

// ============================================================
//  STEPPER MOVEMENT
// ============================================================

void moveX(int x){
  stepper1.moveTo(x);
  stepper3.moveTo(x);

  while (stepper1.distanceToGo() != 0 || stepper3.distanceToGo() != 0) {
      stepper1.run();
      stepper3.run();
  }
}

void moveY(int y){
  stepper2.moveTo(y);

  while (stepper2.distanceToGo() != 0)
      stepper2.run();
}

// ============================================================
//  HOMING FUNCTIONS
// ============================================================

void homingX() {
  // Fast approach
  stepper1.setSpeed(1500);
  stepper3.setSpeed(1500);
  while (digitalRead(endstopPinX) == HIGH) {
    stepper1.runSpeed();
    stepper3.runSpeed();
  }

  delay(200);

  // Retract
  stepper1.setSpeed(-500);
  stepper3.setSpeed(-500);
  while (digitalRead(endstopPinX) == LOW) {
    stepper1.runSpeed();
    stepper3.runSpeed();
  }

  delay(200);

  // Slow approach
  stepper1.setSpeed(200);
  stepper3.setSpeed(200);
  while (digitalRead(endstopPinX) == HIGH) {
    stepper1.runSpeed();
    stepper3.runSpeed();
  }

  stepper1.setCurrentPosition(0);
  stepper3.setCurrentPosition(0);
}

void homingY() {
  // Fast approach
  stepper2.setSpeed(-1500);
  while (digitalRead(endstopPinY) == HIGH)
    stepper2.runSpeed();

  delay(200);

  // Retract
  stepper2.setSpeed(500);
  while (digitalRead(endstopPinY) == LOW)
    stepper2.runSpeed();

  delay(200);

  // Slow approach
  stepper2.setSpeed(-200);
  while (digitalRead(endstopPinY) == HIGH)
    stepper2.runSpeed();

  stepper2.setCurrentPosition(0);
}

void homing() {
  Serial.println("Homing X...");
  homingX();
  Serial.println("Homing Y...");
  homingY();
  Serial.println("Homing done.");
}

// ============================================================
//  COMMAND PARSER
// ============================================================

void parseCommand(String cmd) {
    cmd.trim();
    if (cmd.length() == 0) return;

    char first = cmd.charAt(0);

    // X move
    if (first == 'x' || first == 'X') {
        int s_index = cmd.indexOf('s');
        if (s_index == -1) s_index = cmd.indexOf('S');

        int position = extractNumber(cmd, 1);
        moveX(-position);

        Serial.print("Move X → ");
        Serial.println(position);
    }

    // Y move
    else if (first == 'y' || first == 'Y') {
        int s_index = cmd.indexOf('s');
        if (s_index == -1) s_index = cmd.indexOf('S');

        int position = extractNumber(cmd, 1);
        moveY(position);

        Serial.print("Move Y → ");
        Serial.println(position);
    }

    // HOMING
    else if (first == 'h' || first == 'H') {
        homing();
    }

    else {
        Serial.print("ERROR: unknown command → ");
        Serial.println(cmd);
    }
}

// ============================================================
//  SETUP
// ============================================================

void setup() {

    pinMode(enablePin, OUTPUT);
    digitalWrite(enablePin, LOW);

    pinMode(endstopPinX, INPUT_PULLUP);
    pinMode(endstopPinY, INPUT_PULLUP);

    stepper1.setMaxSpeed(1500);
    stepper1.setAcceleration(300);

    stepper2.setMaxSpeed(1500);
    stepper2.setAcceleration(300);

    stepper3.setMaxSpeed(1500);
    stepper3.setAcceleration(300);

    Serial.begin(115200);

    Serial.println("==============================");
    Serial.println("Stepper firmware ready.");
    Serial.println("Commands:");
    Serial.println("  x100     → move X");
    Serial.println("  y50      → move Y");
    Serial.println("  h        → homing");
    Serial.println("==============================");
}

// ============================================================
//  LOOP
// ============================================================

void loop() {
    if (Serial.available() > 0) {
        char c = Serial.read();

        if (c == '\n' || c == '\r') {
            if (command.length() > 0) {
                Serial.print(">>> ");
                Serial.println(command);
                parseCommand(command);
                command = "";
            }
        } else {
            command += c;
        }
    }
}
