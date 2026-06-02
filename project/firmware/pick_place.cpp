/**
 * @file    pick_place.cpp
 * @brief   Implementation of Z-axis, pump, and valve control.
 */

#include "pick_place.h"
#include <Arduino.h>

// ── Private helpers ────────────────────────────────────────────

/**
 * @brief Send a servo pulse with the given width, repeated to lock position.
 *
 * Bit-banged 50 Hz PWM (20 ms period).
 * Sending 50 pulses ≈ 1 second of active holding.
 *
 * @param microseconds  Pulse width in µs (typically 500–2500).
 */
static void sendPulse(int microseconds) {
    for (int i = 0; i < 50; i++) {
        digitalWrite(SERVO_UP_DOWN_PIN, HIGH);
        delayMicroseconds(microseconds);
        digitalWrite(SERVO_UP_DOWN_PIN, LOW);
        delayMicroseconds(20000 - microseconds);
    }
}

// ── Public API ─────────────────────────────────────────────────

void pick_place_setup() {
    pinMode(SERVO_UP_DOWN_PIN, OUTPUT);
    pinMode(PIN_PUMP,          OUTPUT);
    pinMode(PIN_VALVE,         OUTPUT);
}

void servo_up() {
    sendPulse(POS_UP);
}

void servo_down() {
    sendPulse(POS_DOWN);
}

void pompe(int state) {
    // Valve is active-LOW (closes when pump is active)
    digitalWrite(PIN_VALVE, !state);
    digitalWrite(PIN_PUMP,   state);
}

void pick_place(int state) {
    servo_down();
    delay(Z_DOWN_DWELL_MS);

    pompe(state);

    if (state) {
        delay(PICK_SUCTION_MS);   // wait for suction to build
    } else {
        delay(PLACE_RELEASE_MS);  // wait for piece to release
    }

    servo_up();
}
