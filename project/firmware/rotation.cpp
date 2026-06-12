/**
 * @file    rotation.cpp
 * @brief   Implémentation du contrôle servo pour la rotation de pièce.
 */
#include "rotation.h"
#include <Servo.h>

static Servo servo_rotation;

void rotation_setup() {
    servo_rotation.attach(SERVO_ROTATION_PIN);
}

void rotate(int angle) {
    // Multiplier l'angle logique par 2 pour couvrir toute la plage 0–180° du servo
    servo_rotation.write(angle * 2);
}
