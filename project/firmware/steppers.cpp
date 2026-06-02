/**
 * @file    steppers.cpp
 * @brief   Implementation of X/Y gantry motion.
 */

#include "steppers.h"

// ── State ─────────────────────────────────────────────────────
bool homing_done = false;
int  current_x   = 0;
int  current_y   = 0;

// ── Driver objects ─────────────────────────────────────────────
// AccelStepper(interface, stepPin, dirPin)
// Interface type 1 = DRIVER (external step/dir driver)
static AccelStepper stepper1(1, PIN_X_STEP, PIN_X_DIR);   // X left
static AccelStepper stepper2(1, PIN_Y_STEP, PIN_Y_DIR);   // Y
static AccelStepper stepper3(1, PIN_A_STEP, PIN_A_DIR);   // X right (slave)

// ── Private helpers ────────────────────────────────────────────

/** Drive X toward endstop, back off, then find trigger precisely. */
static void homingX() {
    // 1. Fast approach
    stepper1.setSpeed( HOMING_CREEP_SPEED * 10);
    stepper3.setSpeed( HOMING_CREEP_SPEED * 10);

    while (digitalRead(PIN_ENDSTOP_X) == HIGH) {
        stepper1.runSpeed();
        stepper3.runSpeed();
    }
    stepper1.stop();
    stepper3.stop();
    delay(HOMING_SETTLE_MS);

    // 2. Back off
    stepper1.setSpeed(-HOMING_BACKOFF_SPEED);
    stepper3.setSpeed(-HOMING_BACKOFF_SPEED);

    while (digitalRead(PIN_ENDSTOP_X) == LOW) {
        stepper1.runSpeed();
        stepper3.runSpeed();
    }
    delay(HOMING_SETTLE_MS);

    // 3. Slow creep to find exact trigger point
    stepper1.setSpeed(HOMING_CREEP_SPEED);
    stepper3.setSpeed(HOMING_CREEP_SPEED);

    while (digitalRead(PIN_ENDSTOP_X) == HIGH) {
        stepper1.runSpeed();
        stepper3.runSpeed();
    }

    // 4. Define this as position zero
    stepper1.setCurrentPosition(0);
    stepper3.setCurrentPosition(0);
}

/** Drive Y toward endstop, back off, then find trigger precisely. */
static void homingY() {
    // 1. Fast approach
    stepper2.setSpeed(-HOMING_CREEP_SPEED * 10);

    while (digitalRead(PIN_ENDSTOP_Y) == HIGH) {
        stepper2.runSpeed();
    }
    stepper2.stop();
    delay(HOMING_SETTLE_MS);

    // 2. Back off
    stepper2.setSpeed(HOMING_BACKOFF_SPEED);

    while (digitalRead(PIN_ENDSTOP_Y) == LOW) {
        stepper2.runSpeed();
    }
    delay(HOMING_SETTLE_MS);

    // 3. Slow creep
    stepper2.setSpeed(-HOMING_CREEP_SPEED);

    while (digitalRead(PIN_ENDSTOP_Y) == HIGH) {
        stepper2.runSpeed();
    }

    stepper2.setCurrentPosition(0);
}

// ── Public API ─────────────────────────────────────────────────

void steppers_setup() {
    pinMode(PIN_ENDSTOP_X, INPUT_PULLUP);
    pinMode(PIN_ENDSTOP_Y, INPUT_PULLUP);
    pinMode(PIN_ENABLE, OUTPUT);
    digitalWrite(PIN_ENABLE, LOW);   // LOW = drivers enabled

    stepper1.setMaxSpeed(SPEED_X);
    stepper2.setMaxSpeed(SPEED_Y);
    stepper3.setMaxSpeed(SPEED_X);
}

void homing() {
    // Use speed-only mode during the homing sweep
    stepper1.setSpeed( SPEED_X);
    stepper2.setSpeed(-SPEED_Y);
    stepper3.setSpeed( SPEED_X);

    homingX();
    homingY();

    // Switch to acceleration mode for normal moves
    stepper1.setMaxSpeed(SPEED_X);  stepper1.setAcceleration(ACCEL_X);
    stepper2.setMaxSpeed(SPEED_Y);  stepper2.setAcceleration(ACCEL_Y);
    stepper3.setMaxSpeed(SPEED_X);  stepper3.setAcceleration(ACCEL_X);

    homing_done = true;
    current_x = 0;
    current_y = 0;
}

void move(int x, int y) {
    stepper1.moveTo(x);
    stepper3.moveTo(x);
    stepper2.moveTo(y);

    while (stepper1.distanceToGo() != 0 ||
           stepper2.distanceToGo() != 0 ||
           stepper3.distanceToGo() != 0) {
        stepper1.run();
        stepper2.run();
        stepper3.run();
    }

    current_x = x;
    current_y = y;
}

void moveX(int x) {
    stepper1.moveTo(x);
    stepper3.moveTo(x);

    while (stepper1.distanceToGo() != 0 ||
           stepper3.distanceToGo() != 0) {
        stepper1.run();
        stepper3.run();
    }

    current_x = x;
}

void moveY(int y) {
    stepper2.moveTo(y);

    while (stepper2.distanceToGo() != 0) {
        stepper2.run();
    }

    current_y = y;
}
