/**
 * @file    puzzle_firmware.ino
 * @brief   Puzzle-Solver Robot — Main Sketch
 *
 * Hardware overview
 * -----------------
 *   • 3× stepper motors (AccelStepper)
 *       - stepper1 / stepper3 : dual X-axis gantry
 *       - stepper2             : Y axis
 *   • 1× bit-banged servo  : Z up/down arm
 *   • 1× standard servo    : piece rotation
 *   • 1× suction pump + valve  : pick-and-place pneumatics
 *
 * Communication
 * -------------
 *   UART at SERIAL_BAUD baud.
 *   Receives semicolon-delimited command packets from a Python host.
 *   See parser.h for the full protocol description.
 *
 * File structure
 * --------------
 *   config.h         — all tunable constants (pins, speeds, timing)
 *   steppers.h/.cpp  — gantry motion
 *   pick_place.h/.cpp— Z servo + pneumatics
 *   rotation.h/.cpp  — rotation servo
 *   parser.h/.cpp    — serial protocol & command dispatch
 *
 * @author  Group 1 - (Nicolas Ghandour, Dorian Eugene)
 * @date    Fevrier 2026
 */

#include "config.h"
#include "steppers.h"
#include "pick_place.h"
#include "rotation.h"
#include "parser.h"

// Packet sequence counter (resets to 0 after an END is received)
static int packet_number = 0;

// ── setup ──────────────────────────────────────────────────────
void setup() {
    Serial.begin(SERIAL_BAUD);
    Serial.setTimeout(SERIAL_TIMEOUT_MS);

    steppers_setup();
    pick_place_setup();
    rotation_setup();

    servo_up();   // ensure arm is raised at power-on

    Serial.println(F("=============================="));
    Serial.println(F("Puzzle-Solver Firmware ready."));
    Serial.println(F("Command reference:"));
    Serial.println(F("  h              → homing"));
    Serial.println(F("  x{pos}s{spd}   → move X"));
    Serial.println(F("  y{pos}s{spd}   → move Y"));
    Serial.println(F("  p1             → pick"));
    Serial.println(F("  p0             → place"));
    Serial.println(F("  r{angle}       → rotate [0-90]"));
    Serial.println(F("  d              → delay"));
    Serial.println(F("  END            → end of g-code instructions"));
    Serial.println(F("=============================="));
}

// ── loop ──────────────────────────────────────────────────────
/*Waiting for g-code instructions to be sent through serial-monitor*/
void loop() {
    if (Serial.available() == 0) return;

    String raw = Serial.readString();
    raw.trim();

    if (raw.length() == 0) return;

    instructions_done = false;   // reset END flag for this packet
    parseInstructions(raw);

    Serial.print(F(">>> received "));
    Serial.print(instructionCount);
    Serial.println(F(" instruction(s):"));

    for (int i = 0; i < instructionCount; i++) {
        Serial.print(F("  ["));
        Serial.print(i);
        Serial.print(F("] "));
        Serial.println(instructions[i]);
        parseCommand(instructions[i]);
    }

    if (instructions_done) {
        Serial.println(F("OK"));
        packet_number = 0;
    } else {
        Serial.print(F("ACK"));
        Serial.println(packet_number++);
    }
}
