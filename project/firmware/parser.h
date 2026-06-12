//**
 * @file    parser.h
 * @brief   Parseur de commandes série — décode les paquets texte et
 *          distribue les commandes de mouvement / E/S.
 *
 * Protocole série
 * ---------------
 * L'hôte Python envoie une ou plusieurs commandes séparées par des
 * points-virgules sur une seule ligne, par exemple :
 *
 *   h;x4998s2000;y3724s2000;p1;r45;p0;END\n
 *
 * Syntaxe des commandes
 * ---------------------
 *   x{pos}s{vitesse}   Déplacer X vers la position absolue en pas
 *   y{pos}s{vitesse}   Déplacer Y vers la position absolue en pas
 *   p1                 Saisir  (descendre, aspiration ON, monter)
 *   p0                 Poser   (descendre, aspiration OFF, monter)
 *   r{angle}           Faire pivoter la pièce [0–90°]
 *   h                  Séquence de homing
 *   d                  Délai (CMD_DELAY_MS)
 *   END                Marque la fin d'un paquet → le firmware répond "OK"
 *
 * Réponses du firmware
 * --------------------
 *   ACK{n}             Paquet n reçu et exécuté (END non détecté)
 *   OK                 Le paquet contenait END — toutes les instructions sont terminées
 *   ERROR: ...         Commande malformée ou inconnue
 *
 * Remarques
 * ---------
 * - Le champ vitesse dans les commandes x/y est analysé et renvoyé en
 *   écho pour la journalisation, mais n'a actuellement aucun effet sur
 *   la vitesse de déplacement (les vitesses des axes sont définies
 *   globalement dans config.h). C'est une limitation connue qui peut
 *   être étendue dans moveX() / moveY().
 */
#pragma once
#include <Arduino.h>
#include "config.h"

/** Vrai dès qu'une commande "END" a été reçue dans le paquet courant. */
extern bool instructions_done;
extern String instructions[MAX_INSTRUCTIONS];
extern int    instructionCount;

/**
 * @brief Découpe une chaîne brute délimitée par des points-virgules dans
 *        le tableau global instructions[].
 * @param raw  La chaîne complète du paquet telle que reçue depuis Serial.
 */
void parseInstructions(const String& raw);

/**
 * @brief Exécute une seule chaîne de commande.
 * @param cmd  Un token de commande, par ex. "x4998s2000" ou "p1".
 */
void parseCommand(const String& cmd);
