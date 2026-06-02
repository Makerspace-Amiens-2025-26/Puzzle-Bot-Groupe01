/**
 * @file    rotation.h
 * @brief   Piece-rotation servo control.
 *
 * The servo has a physical travel of 180° mapped to 0–90° in
 * the command interface (angle is doubled internally so the full
 * mechanical range is accessible via a 0–90 logical range).
 */

#pragma once

#include "config.h"

/**
 * @brief Attach the rotation servo to its pin.
 * Call once from setup().
 */
void rotation_setup();

/**
 * @brief Rotate the held piece to the specified angle.
 *
 * @param angle  Logical angle in degrees [0, 90].
 *               The value is doubled before being written to the
 *               servo so the full 0–180° hardware travel is used.
 */
void rotate(int angle);
