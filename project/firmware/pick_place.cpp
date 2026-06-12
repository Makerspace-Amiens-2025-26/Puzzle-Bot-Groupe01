/**
 * @file    pick_place.cpp
 * @brief   Implémentation du contrôle de l'axe Z, de la pompe et de la valve.
 */
#include "pick_place.h"
#include <Arduino.h>

// ── Fonctions utilitaires privées ──────────────────────────────

/**
 * @brief Envoie une impulsion servo de la largeur donnée, répétée pour maintenir la position.
 *
 * PWM 50 Hz généré par bit-banging (période de 20 ms).
 * Envoyer 50 impulsions ≈ 1 seconde de maintien actif.
 *
 * @param microseconds  Largeur d'impulsion en µs (typiquement 500–2500).
 */
static void sendPulse(int microseconds) {
    for (int i = 0; i < 50; i++) {
        digitalWrite(SERVO_UP_DOWN_PIN, HIGH);
        delayMicroseconds(microseconds);
        digitalWrite(SERVO_UP_DOWN_PIN, LOW);
        delayMicroseconds(20000 - microseconds);
    }
}

// ── API publique ───────────────────────────────────────────────

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
    // La valve est active à l'état bas (se ferme quand la pompe est active)
    digitalWrite(PIN_VALVE, !state);
    digitalWrite(PIN_PUMP,   state);
}

void pick_place(int state) {
    servo_down();
    delay(Z_DOWN_DWELL_MS);
    pompe(state);
    if (state) {
        delay(PICK_SUCTION_MS);   // attendre que l'aspiration se stabilise
    } else {
        delay(PLACE_RELEASE_MS);  // attendre que la pièce soit relâchée
    }
    servo_up();
}
