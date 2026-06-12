/**
 * @file    puzzle_firmware.ino
 * @brief   Robot Résolveur de Puzzle — Sketch Principal
 *
 * Aperçu du matériel
 * ------------------
 *   • 3× moteurs pas à pas (AccelStepper)
 *       - stepper1 / stepper3 : portique X double axe
 *       - stepper2             : axe Y
 *   • 1× servo bit-bangé  : bras Z montée/descente
 *   • 1× servo standard   : rotation de la pièce
 *   • 1× pompe à aspiration + valve  : pneumatique de saisie/pose
 *
 * Communication
 * -------------
 *   UART à SERIAL_BAUD bauds.
 *   Reçoit des paquets de commandes délimitées par des points-virgules
 *   depuis un hôte Python.
 *   Voir parser.h pour la description complète du protocole.
 *
 * Structure des fichiers
 * ----------------------
 *   config.h         — toutes les constantes configurables (broches, vitesses, timing)
 *   steppers.h/.cpp  — déplacement du portique
 *   pick_place.h/.cpp— servo Z + pneumatique
 *   rotation.h/.cpp  — servo de rotation
 *   parser.h/.cpp    — protocole série & distribution des commandes
 *
 * @author  Groupe 1 - (Nicolas Ghandour, Dorian Eugene)
 * @date    Février 2026
 */
#include "config.h"
#include "steppers.h"
#include "pick_place.h"
#include "rotation.h"
#include "parser.h"

// Compteur de séquence de paquets (remis à 0 après réception d'un END)
static int packet_number = 0;

// ── setup ──────────────────────────────────────────────────────
void setup() {
    Serial.begin(SERIAL_BAUD);
    Serial.setTimeout(SERIAL_TIMEOUT_MS);
    steppers_setup();
    pick_place_setup();
    rotation_setup();
    servo_up();   // s'assurer que le bras est relevé à la mise sous tension
    Serial.println(F("=============================="));
    Serial.println(F("Puzzle-Solver Firmware ready."));
    Serial.println(F("Command reference:"));
    Serial.println(F("  h              → homing"));
    Serial.println(F("  x{pos}s{spd}   → move X"));
    Serial.println(F("  y{pos}s{spd}   → move Y"));
    Serial.println(F("  p1             → pick"));
    Serial.println(F("  p0             → place"));
    Serial.println(F("  r{angle}       → rotate [0-90]"));
    Serial.println(F("  d              → delay"));
    Serial.println(F("  END            → end of g-code instructions"));
    Serial.println(F("=============================="));
}

// ── loop ──────────────────────────────────────────────────────
/* En attente de réception des instructions g-code via le moniteur série */
void loop() {
    if (Serial.available() == 0) return;
    String raw = Serial.readString();
    raw.trim();
    if (raw.length() == 0) return;
    instructions_done = false;   // réinitialise le flag END pour ce paquet
    parseInstructions(raw);
    Serial.print(F(">>> received "));
    Serial.print(instructionCount);
    Serial.println(F(" instruction(s):"));
    for (int i = 0; i < instructionCount; i++) {
        Serial.print(F("  ["));
        Serial.print(i);
        Serial.print(F("] "));
        Serial.println(instructions[i]);
        parseCommand(instructions[i]);
    }
    if (instructions_done) {
        Serial.println(F("OK"));
        packet_number = 0;
    } else {
        Serial.print(F("ACK"));
        Serial.println(packet_number++);
    }
}
