/**
 * @file    pick_place.h
 * @brief   Z-axis servo, suction pump, and valve control.
 *
 * Pick/place cycle
 * ----------------
 *   1. Lower Z-arm  (servo_down)
 *   2. Wait for arm to reach piece
 *   3. Activate / deactivate pump + valve
 *   4. Wait for suction to build (pick) or piece to release (place)
 *   5. Raise Z-arm  (servo_up)
 *
 * The up/down servo is driven by a bit-banged 50 Hz PWM signal so
 * it works on any digital pin without consuming a hardware timer.
 */

#pragma once

#include "config.h"

/**
 * @brief Initialise pump, valve, and servo pins.
 * Call once from setup().
 */
void pick_place_setup();

/**
 * @brief Raise the Z-arm (servo → POS_UP pulse width).
 */
void servo_up();

/**
 * @brief Lower the Z-arm (servo → POS_DOWN pulse width).
 */
void servo_down();

/**
 * @brief Set pump + valve state.
 * @param state  HIGH (1) → pump ON, valve closed (suction active)
 *               LOW  (0) → pump OFF, valve open  (release)
 */
void pompe(int state);

/**
 * @brief Execute a complete pick or place cycle.
 *
 * Lowers the arm, operates the pneumatics, then raises the arm.
 * Blocks until the full cycle is complete.
 *
 * @param state  1 = pick (activate suction), 0 = place (release)
 */
void pick_place(int state);
