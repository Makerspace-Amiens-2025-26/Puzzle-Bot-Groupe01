/**
 * @file    parser.cpp
 * @brief   Implémentation du parseur de commandes série.
 */

#include "parser.h"
#include "steppers.h"
#include "pick_place.h"
#include "rotation.h"

// ── État ───────────────────────────────────────────────────────
bool   instructions_done               = false;
String instructions[MAX_INSTRUCTIONS];
int    instructionCount                = 0;

// ── Fonctions utilitaires privées ──────────────────────────────

/**
 * @brief Extrait le premier entier trouvé dans `str` à partir de l'index `from`.
 *
 * Parcourt la chaîne en collectant les chiffres, et s'arrête au premier
 * caractère non-numérique après qu'au moins un chiffre ait été lu.
 *
 * @param str   La chaîne source.
 * @param from  Index de départ dans la chaîne.
 * @return      L'entier analysé, ou 0 si aucun chiffre n'a été trouvé.
 */
static int extractNumber(const String& str, int from) {
    String numStr = "";

    for (int i = from; i < (int)str.length(); i++) {
        char c = str.charAt(i);
        if (isDigit(c)) {
            numStr += c;
        } else if (numStr.length() > 0) {
            break;   // premier caractère non-numérique après la séquence de chiffres
        }
    }

    return numStr.toInt();
}

// ── API publique ───────────────────────────────────────────────

void parseInstructions(const String& raw) {
    instructionCount = 0;
    int start = 0;

    for (int i = 0; i <= (int)raw.length(); i++) {
        if (raw[i] == ';' || raw[i] == '\0') {
            String token = raw.substring(start, i);
            token.trim();
            if (token.length() > 0 && instructionCount < MAX_INSTRUCTIONS) {
                instructions[instructionCount++] = token;
            }
            start = i + 1;
        }
    }
}

void parseCommand(const String& cmd) {

    // ── Marqueur de fin ────────────────────────────────────────
    if (cmd == "END") {
        instructions_done = true;
        return;
    }

    if (cmd.length() == 0) return;

    char first = tolower(cmd.charAt(0));

    // ── x{pos}s{vitesse}  —  déplacement X ────────────────────
    if (first == 'x') {
        int s_idx    = cmd.indexOf('s');
        if (s_idx == -1) s_idx = cmd.indexOf('S');

        // Les positions X sont inversées car le portique est monté à l'envers
        int position = -extractNumber(cmd, 1);
        int speed    = (s_idx != -1) ? extractNumber(cmd, s_idx + 1) : 0;

        moveX(position);

        Serial.print("Move X → position: ");
        Serial.print(position);
        Serial.print("  speed: ");
        Serial.println(speed);
    }

    // ── y{pos}s{vitesse}  —  déplacement Y ────────────────────
    else if (first == 'y') {
        int s_idx    = cmd.indexOf('s');
        if (s_idx == -1) s_idx = cmd.indexOf('S');

        int position = extractNumber(cmd, 1);
        int speed    = (s_idx != -1) ? extractNumber(cmd, s_idx + 1) : 0;

        moveY(position);

        Serial.print("Move Y → position: ");
        Serial.print(position);
        Serial.print("  speed: ");
        Serial.println(speed);
    }

    // ── p1 / p0  —  saisir ou poser ───────────────────────────
    else if (first == 'p') {
        int value = extractNumber(cmd, 1);

        if (value != 0 && value != 1) {
            Serial.println("ERROR: p command must be p0 (place) or p1 (pick)");
        } else {
            pick_place(value);
            Serial.println(value ? "Pick successful" : "Place successful");
        }
    }

    // ── r{angle}  —  rotation ─────────────────────────────────
    else if (first == 'r') {
        int angle = extractNumber(cmd, 1);
        rotate(angle);
        Serial.print("Rotate → ");
        Serial.print(angle);
        Serial.println(" degrees");
    }

    // ── h  —  homing ──────────────────────────────────────────
    else if (first == 'h') {
        homing();
        Serial.println("Homing complete");
    }

    // ── d  —  délai ───────────────────────────────────────────
    else if (first == 'd') {
        delay(CMD_DELAY_MS);
        Serial.println("Delay done");
    }

    // ── Commande inconnue ──────────────────────────────────────
    else {
        Serial.print("ERROR: unknown command → ");
        Serial.println(cmd);
    }
}
