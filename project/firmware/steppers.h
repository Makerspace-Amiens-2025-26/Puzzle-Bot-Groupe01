/**
 * @file    steppers.h
 * @brief   X/Y gantry motion — three AccelStepper axes.
 *
 * Hardware topology
 * -----------------
 *   stepper1  →  left X motor
 *   stepper3  →  right X motor  (mirrors stepper1 exactly)
 *   stepper2  →  Y motor
 *
 * All public functions block until motion is complete.
 * Homing must be called once before any move command.
 */

#pragma once

#include <AccelStepper.h>
#include "config.h"

// ── External state ────────────────────────────────────────────
/** True once homing has completed successfully. */
extern bool homing_done;

/** Current head position in step counts (updated after every move). */
extern int current_x;
extern int current_y;

// ── Lifecycle ─────────────────────────────────────────────────

/**
 * @brief Initialise pins, driver enable, and default speeds.
 * Call once from setup().
 */
void steppers_setup();

/**
 * @brief Run the full homing sequence (X then Y).
 *
 * Drives each axis toward its endstop, backs off, then touches
 * slowly to find the exact trigger point.  Sets position zero
 * and configures cruise speeds / accelerations for normal moves.
 */
void homing();

// ── Motion primitives ─────────────────────────────────────────

/**
 * @brief Move X and Y simultaneously to absolute step positions.
 * @param x  Target position in steps (negative = away from home).
 * @param y  Target position in steps.
 */
void move(int x, int y);

/**
 * @brief Move X axis only to an absolute step position.
 * @param x  Target position in steps.
 */
void moveX(int x);

/**
 * @brief Move Y axis only to an absolute step position.
 * @param y  Target position in steps.
 */
void moveY(int y);
