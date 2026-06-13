/**
 * @file    config.h
 * @brief   Central configuration for the Puzzle-Solver Firmware.
 *
 * Edit ONLY this file to tune mechanical parameters, pin assignments,
 * speeds, and the logical-to-physical coordinate map.
 * No other source file should contain magic numbers.
 */

#pragma once

// ============================================================
//  MECHANICAL CALIBRATION
// ============================================================

/** Steps per millimetre on the X axis (dual-motor gantry). */
#define STEPS_PER_MM_X   (10000.0f / 245.0f)

/** Steps per millimetre on the Y axis. */
#define STEPS_PER_MM_Y   (4000.0f  / 204.0f)

// ============================================================
//  MOTION SPEEDS  (steps / second)
// ============================================================

/** Cruise speed for stepper1 (X-left) and stepper3 (X-right copy). */
#define SPEED_X          3000

/** Cruise speed for stepper2 (Y axis). */
#define SPEED_Y          3000

/** Acceleration for X axes (steps / s²). */
#define ACCEL_X          200

/** Acceleration for Y axis (steps / s²). */
#define ACCEL_Y          150

/** Slow approach speed used during homing (steps / s). */
#define HOMING_CREEP_SPEED   200

/** Back-off speed after endstop trigger (steps / s). */
#define HOMING_BACKOFF_SPEED 500

// ============================================================
//  PIN ASSIGNMENTS
// ============================================================

// --- Stepper drivers (STEP / DIR) ---
#define PIN_X_STEP       2
#define PIN_X_DIR        5
#define PIN_Y_STEP       3
#define PIN_Y_DIR        6
#define PIN_A_STEP      12    ///< Slave motor that mirrors X
#define PIN_A_DIR       13

/** Active-LOW enable shared by all stepper drivers. */
#define PIN_ENABLE       8

// --- Endstops (INPUT_PULLUP → HIGH = open, LOW = triggered) ---
#define PIN_ENDSTOP_X    9
#define PIN_ENDSTOP_Y   10

// --- Pneumatics ---
#define PIN_PUMP         4    ///< Suction pump relay / H-bridge input
#define PIN_VALVE        7    ///< Normally-open valve relay

// --- Servos ---
/**
 * Up/down servo driven by bit-banged PWM (no hardware timer needed).
 * Pulse width in microseconds:  POS_UP / POS_DOWN.
 */
#define SERVO_UP_DOWN_PIN   A5
#define POS_UP              500    ///< µs → fully raised
#define POS_DOWN            2500   ///< µs → fully lowered

/** Rotation servo (standard Arduino Servo library). */
#define SERVO_ROTATION_PIN  11

// ============================================================
//  TIMING CONSTANTS  (milliseconds)
// ============================================================

/** Dwell after endstop trigger before reversing. */
#define HOMING_SETTLE_MS     200

/** Time given to the pump to build suction before lifting. */
#define PICK_SUCTION_MS     3000

/** Time the valve stays open after placing before lifting. */
#define PLACE_RELEASE_MS    1000

/** Total time the Z-axis stays down on any pick/place cycle. */
#define Z_DOWN_DWELL_MS     2000

/** Duration of a 'd' (delay) command. */
#define CMD_DELAY_MS        2000

// ============================================================
//  SERIAL PROTOCOL
// ============================================================

#define SERIAL_BAUD          115200
#define SERIAL_TIMEOUT_MS    300     ///< readString() timeout
#define MAX_INSTRUCTIONS      20     ///< Max commands per packet

// ============================================================
//  COORDINATE MAP
//
//  Maps logical grid positions (col 0-4, row 0-4) to raw
//  stepper step counts that position the head over each cell.
//
//  Origin:  ArUco marker #0  →  x=100 steps, y=196 steps
//  Grid pitch: 60 mm         →  ΔX ≈ 2449 steps, ΔY ≈ 1176 steps
//
//  Layout:  coordMap[col][row] = {xSteps, ySteps}
// ============================================================

#define GRID_COLS  5
#define GRID_ROWS  5

static const int coordMap[GRID_COLS][GRID_ROWS][2] = {
    //  row 0          row 1          row 2          row 3          row 4
    { {100,  196}, {100,  1372}, {100,  2548}, {100,  3724}, {100,  4900} }, // col 0
    { {2549, 196}, {2549, 1372}, {2549, 2548}, {2549, 3724}, {2549, 4900} }, // col 1
    { {4998, 196}, {4998, 1372}, {4998, 2548}, {4998, 3724}, {4998, 4900} }, // col 2
    { {7447, 196}, {7447, 1372}, {7447, 2548}, {7447, 3724}, {7447, 4900} }, // col 3
    { {9896, 196}, {9896, 1372}, {9896, 2548}, {9896, 3724}, {9896, 4900} }, // col 4
};
