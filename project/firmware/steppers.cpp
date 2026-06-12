/**
 * @file    steppers.cpp
 * @brief   Implémentation du déplacement du portique X/Y.
 */

#include "steppers.h"

// ── État ───────────────────────────────────────────────────────
bool homing_done = false;
int  current_x   = 0;
int  current_y   = 0;

// ── Objets pilotes ─────────────────────────────────────────────
// AccelStepper(interface, stepPin, dirPin)
// Type d'interface 1 = DRIVER (pilote externe step/dir)
static AccelStepper stepper1(1, PIN_X_STEP, PIN_X_DIR);   // X gauche
static AccelStepper stepper2(1, PIN_Y_STEP, PIN_Y_DIR);   // Y
static AccelStepper stepper3(1, PIN_A_STEP, PIN_A_DIR);   // X droite (esclave)

// ── Fonctions utilitaires privées ──────────────────────────────

/** Déplace X vers la fin de course, recule, puis trouve le déclencheur précisément. */
static void homingX() {
    // 1. Approche rapide
    stepper1.setSpeed( HOMING_CREEP_SPEED * 10);
    stepper3.setSpeed( HOMING_CREEP_SPEED * 10);

    while (digitalRead(PIN_ENDSTOP_X) == HIGH) {
        stepper1.runSpeed();
        stepper3.runSpeed();
    }
    stepper1.stop();
    stepper3.stop();
    delay(HOMING_SETTLE_MS);

    // 2. Recul
    stepper1.setSpeed(-HOMING_BACKOFF_SPEED);
    stepper3.setSpeed(-HOMING_BACKOFF_SPEED);

    while (digitalRead(PIN_ENDSTOP_X) == LOW) {
        stepper1.runSpeed();
        stepper3.runSpeed();
    }
    delay(HOMING_SETTLE_MS);

    // 3. Avance lente pour trouver le point de déclenchement exact
    stepper1.setSpeed(HOMING_CREEP_SPEED);
    stepper3.setSpeed(HOMING_CREEP_SPEED);

    while (digitalRead(PIN_ENDSTOP_X) == HIGH) {
        stepper1.runSpeed();
        stepper3.runSpeed();
    }

    // 4. Définir cette position comme zéro
    stepper1.setCurrentPosition(0);
    stepper3.setCurrentPosition(0);
}

/** Déplace Y vers la fin de course, recule, puis trouve le déclencheur précisément. */
static void homingY() {
    // 1. Approche rapide
    stepper2.setSpeed(-HOMING_CREEP_SPEED * 10);

    while (digitalRead(PIN_ENDSTOP_Y) == HIGH) {
        stepper2.runSpeed();
    }
    stepper2.stop();
    delay(HOMING_SETTLE_MS);

    // 2. Recul
    stepper2.setSpeed(HOMING_BACKOFF_SPEED);

    while (digitalRead(PIN_ENDSTOP_Y) == LOW) {
        stepper2.runSpeed();
    }
    delay(HOMING_SETTLE_MS);

    // 3. Avance lente
    stepper2.setSpeed(-HOMING_CREEP_SPEED);

    while (digitalRead(PIN_ENDSTOP_Y) == HIGH) {
        stepper2.runSpeed();
    }

    stepper2.setCurrentPosition(0);
}

// ── API publique ───────────────────────────────────────────────

void steppers_setup() {
    pinMode(PIN_ENDSTOP_X, INPUT_PULLUP);
    pinMode(PIN_ENDSTOP_Y, INPUT_PULLUP);
    pinMode(PIN_ENABLE, OUTPUT);
    digitalWrite(PIN_ENABLE, LOW);   // LOW = pilotes activés

    stepper1.setMaxSpeed(SPEED_X);
    stepper2.setMaxSpeed(SPEED_Y);
    stepper3.setMaxSpeed(SPEED_X);
}

void homing() {
    // Utiliser le mode vitesse seule pendant le balayage de homing
    stepper1.setSpeed( SPEED_X);
    stepper2.setSpeed(-SPEED_Y);
    stepper3.setSpeed( SPEED_X);

    homingX();
    homingY();

    // Passer en mode accélération pour les déplacements normaux
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
