/**
 * @file    parser.cpp
 * @brief   Implementation of the serial command parser.
 */

#include "parser.h"
#include "steppers.h"
#include "pick_place.h"
#include "rotation.h"

// ── State ─────────────────────────────────────────────────────
bool   instructions_done               = false;
String instructions[MAX_INSTRUCTIONS];
int    instructionCount                = 0;

// ── Private helpers ────────────────────────────────────────────

/**
 * @brief Extract the first integer found in `str` starting at index `from`.
 *
 * Scans forward, collecting digit characters, and stops at the first
 * non-digit after at least one digit has been read.
 *
 * @param str   The source string.
 * @param from  Start index within the string.
 * @return      Parsed integer, or 0 if no digits were found.
 */
static int extractNumber(const String& str, int from) {
    String numStr = "";

    for (int i = from; i < (int)str.length(); i++) {
        char c = str.charAt(i);
        if (isDigit(c)) {
            numStr += c;
        } else if (numStr.length() > 0) {
            break;   // first non-digit after the numeric run
        }
    }

    return numStr.toInt();
}

// ── Public API ─────────────────────────────────────────────────

void parseInstructions(const String& raw) {
    instructionCount = 0;
    int start = 0;

    for (int i = 0; i <= (int)raw.length(); i++) {
        if (raw[i] == ';' || raw[i] == '\0') {
            String token = raw.substring(start, i);
            token.trim();
            if (token.length() > 0 && instructionCount < MAX_INSTRUCTIONS) {
                instructions[instructionCount++] = token;
            }
            start = i + 1;
        }
    }
}

void parseCommand(const String& cmd) {

    // ── END marker ─────────────────────────────────────────────
    if (cmd == "END") {
        instructions_done = true;
        return;
    }

    if (cmd.length() == 0) return;

    char first = tolower(cmd.charAt(0));

    // ── x{pos}s{speed}  —  move X ──────────────────────────────
    if (first == 'x') {
        int s_idx    = cmd.indexOf('s');
        if (s_idx == -1) s_idx = cmd.indexOf('S');

        // X positions are negated because the gantry is inverted
        int position = -extractNumber(cmd, 1);
        int speed    = (s_idx != -1) ? extractNumber(cmd, s_idx + 1) : 0;

        moveX(position);

        Serial.print("Move X → position: ");
        Serial.print(position);
        Serial.print("  speed: ");
        Serial.println(speed);
    }

    // ── y{pos}s{speed}  —  move Y ──────────────────────────────
    else if (first == 'y') {
        int s_idx    = cmd.indexOf('s');
        if (s_idx == -1) s_idx = cmd.indexOf('S');

        int position = extractNumber(cmd, 1);
        int speed    = (s_idx != -1) ? extractNumber(cmd, s_idx + 1) : 0;

        moveY(position);

        Serial.print("Move Y → position: ");
        Serial.print(position);
        Serial.print("  speed: ");
        Serial.println(speed);
    }

    // ── p1 / p0  —  pick or place ───────────────────────────────
    else if (first == 'p') {
        int value = extractNumber(cmd, 1);

        if (value != 0 && value != 1) {
            Serial.println("ERROR: p command must be p0 (place) or p1 (pick)");
        } else {
            pick_place(value);
            Serial.println(value ? "Pick successful" : "Place successful");
        }
    }

    // ── r{angle}  —  rotate ─────────────────────────────────────
    else if (first == 'r') {
        int angle = extractNumber(cmd, 1);
        rotate(angle);
        Serial.print("Rotate → ");
        Serial.print(angle);
        Serial.println(" degrees");
    }

    // ── h  —  homing ────────────────────────────────────────────
    else if (first == 'h') {
        homing();
        Serial.println("Homing complete");
    }

    // ── d  —  delay ─────────────────────────────────────────────
    else if (first == 'd') {
        delay(CMD_DELAY_MS);
        Serial.println("Delay done");
    }

    // ── Unknown ─────────────────────────────────────────────────
    else {
        Serial.print("ERROR: unknown command → ");
        Serial.println(cmd);
    }
}
