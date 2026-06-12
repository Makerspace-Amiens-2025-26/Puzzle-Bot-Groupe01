/**
 * @file    rotation.h
 * @brief   Contrôle servo pour la rotation de pièce.
 *
 * Le servo dispose d'une course physique de 180° mappée sur 0–90°
 * dans l'interface de commande (l'angle est doublé en interne afin
 * que toute la plage mécanique soit accessible via une plage logique
 * de 0–90).
 */
#pragma once
#include "config.h"

/**
 * @brief Attache le servo de rotation à sa broche.
 * À appeler une fois depuis setup().
 */
void rotation_setup();

/**
 * @brief Fait pivoter la pièce saisie vers l'angle spécifié.
 *
 * @param angle  Angle logique en degrés [0, 90].
 *               La valeur est doublée avant d'être écrite sur le servo
 *               afin d'utiliser toute la course matérielle de 0–180°.
 */
void rotate(int angle);
