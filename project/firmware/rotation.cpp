/**
 * @file    rotation.cpp
 * @brief   Implementation of piece-rotation servo control.
 */

#include "rotation.h"
#include <Servo.h>

static Servo servo_rotation;

void rotation_setup() {
    servo_rotation.attach(SERVO_ROTATION_PIN);
}

void rotate(int angle) {
    // Double the logical angle to span the full 0–180° servo range
    servo_rotation.write(angle * 2);
}
