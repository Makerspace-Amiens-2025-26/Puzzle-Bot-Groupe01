/**
 * @file    pick_place.h
 * @brief   Contrôle du servo de l'axe Z, de la pompe à aspiration et de la valve.
 *
 * Cycle de saisie/pose
 * --------------------
 *   1. Descendre le bras Z  (servo_down)
 *   2. Attendre que le bras atteigne la pièce
 *   3. Activer / désactiver la pompe et la valve
 *   4. Attendre que l'aspiration se stabilise (saisie) ou que la pièce soit relâchée (pose)
 *   5. Monter le bras Z  (servo_up)
 *
 * Le servo montée/descente est piloté par un signal PWM 50 Hz généré
 * par bit-banging, ce qui le rend compatible avec n'importe quelle
 * broche numérique sans utiliser de timer matériel.
 */
#pragma once
#include "config.h"

/**
 * @brief Initialise les broches de la pompe, de la valve et du servo.
 * À appeler une fois depuis setup().
 */
void pick_place_setup();

/**
 * @brief Monter le bras Z (servo → largeur d'impulsion POS_UP).
 */
void servo_up();

/**
 * @brief Descendre le bras Z (servo → largeur d'impulsion POS_DOWN).
 */
void servo_down();

/**
 * @brief Définit l'état de la pompe et de la valve.
 * @param state  HIGH (1) → pompe ON, valve fermée (aspiration active)
 *               LOW  (0) → pompe OFF, valve ouverte (relâchement)
 */
void pompe(int state);

/**
 * @brief Exécute un cycle complet de saisie ou de pose.
 *
 * Descend le bras, actionne le circuit pneumatique, puis remonte le bras.
 * Bloquant jusqu'à la fin du cycle complet.
 *
 * @param state  1 = saisir (activer l'aspiration), 0 = poser (relâcher)
 */
void pick_place(int state);
