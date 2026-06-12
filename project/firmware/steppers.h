/**
 * @file    steppers.h
 * @brief   Déplacement du portique X/Y — trois axes AccelStepper.
 *
 * Topologie matérielle
 * --------------------
 *   stepper1  →  moteur X gauche
 *   stepper3  →  moteur X droite  (miroir exact de stepper1)
 *   stepper2  →  moteur Y
 *
 * Toutes les fonctions publiques sont bloquantes jusqu'à la fin du mouvement.
 * Le homing doit être appelé une fois avant toute commande de déplacement.
 */
#pragma once
#include <AccelStepper.h>
#include "config.h"

// ── État externe ──────────────────────────────────────────────
/** Vrai une fois que le homing s'est terminé avec succès. */
extern bool homing_done;
/** Position actuelle de la tête en nombre de pas (mise à jour après chaque déplacement). */
extern int current_x;
extern int current_y;

// ── Cycle de vie ──────────────────────────────────────────────
/**
 * @brief Initialise les broches, l'activation des pilotes et les vitesses par défaut.
 * À appeler une fois depuis setup().
 */
void steppers_setup();

/**
 * @brief Exécute la séquence de homing complète (X puis Y).
 *
 * Déplace chaque axe vers sa fin de course, recule, puis avance
 * lentement pour trouver le point de déclenchement exact. Définit
 * la position zéro et configure les vitesses de croisière et les
 * accélérations pour les déplacements normaux.
 */
void homing();

// ── Primitives de déplacement ─────────────────────────────────
/**
 * @brief Déplace X et Y simultanément vers des positions absolues en pas.
 * @param x  Position cible en pas (négatif = éloignement du point d'origine).
 * @param y  Position cible en pas.
 */
void move(int x, int y);

/**
 * @brief Déplace uniquement l'axe X vers une position absolue en pas.
 * @param x  Position cible en pas.
 */
void moveX(int x);

/**
 * @brief Déplace uniquement l'axe Y vers une position absolue en pas.
 * @param y  Position cible en pas.
 */
void moveY(int y);
