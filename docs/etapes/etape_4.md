---
layout: default
title: Numérique
parent: Etapes de fabrication
nav_order: 4
---


### Numérique

*reference : https://github.com/Makerspace-Amiens-2025-26/Puzzle-Bot-Groupe01/tree/main/project*


<br>

**1\. Configuration du matériel**

Avant d'écrire la moindre ligne de code, il a fallu définir précisément comment chaque composant allait être piloté électroniquement. Le robot repose sur une carte **Arduino UNO**, choisie pour sa simplicité et sa compatibilité avec les bibliothèques de contrôle de moteurs.

Les composants pilotés sont les suivants :

- **2 moteurs pas à pas sur l'axe X** (portique double, les deux bougent en miroir)
- **1 moteur pas à pas sur l'axe Y**
- **1 servo de montée/descente du bras Z** (broche A5)
- **1 servo de rotation de pièce** (broche 11)
- **1 pompe à aspiration + 1 électrovanne** (broches 4 et 7)
- **2 fins de course** (broches 9 et 10, en INPUT_PULLUP)

Toutes les affectations de broches, les vitesses, les accélérations et les constantes de timing sont centralisées dans un seul fichier : config.h. Ce choix architectural est volontaire - modifier le câblage ou recalibrer le robot ne nécessite de toucher qu'un seul endroit dans le code.


<br>

<br>


**2\.Tests unitaires des composants**

Avant d'intégrer les composants ensemble, chaque élément a été testé indépendamment via des scripts dédiés, disponibles dans le dossier Testings/. Cette approche de tests unitaires a permis de valider le câblage, d'affiner les paramètres mécaniques et d'identifier les problèmes avant l'intégration.

Les tests réalisés :

- **Testings/steppers/movexy/** - validation des déplacements X et Y, mesure de la précision en pas par millimètre
- **Testings/steppers/homing/** - mise au point de la séquence de homing
- **Testings/servos/servo_up_down/** - calibration des positions haute et basse du bras Z
- **Testings/servos/servo_rotation/** - vérification de la plage de rotation de la pièce
- **Testings/pump/** - test du circuit pneumatique (pompe + électrovanne)

reference : https://github.com/Makerspace-Amiens-2025-26/Puzzle-Bot-Groupe01/tree/main/project/Testings 

**Calibration mécanique**

Suite aux expérimentations, les paramètres suivants ont été déterminés :

- **10 000 pas = 245 mm** sur l'axe X → STEPS_PER_MM_X = 10000 / 245
- **4 000 pas = 204 mm** sur l'axe Y → STEPS_PER_MM_Y = 4000 / 204
- L'origine physique du marqueur ArUco #0 correspond à **100 pas en X et 196 pas en Y** depuis le point de homing.

Ces valeurs sont le fruit de mesures réelles sur le robot et devront être répétées si la structure mécanique est modifiée.



<br>

<br>

**3\. Intégration de la rotation**

**Contrainte matérielle**

Le servo de rotation a une **plage physique de 180°**, mais en raison de la configuration mécanique, la plage resultante de rotation est limité à 90 degrés seeulement.


Par suite, nous avons concu un algorithme permettant de realiser des rotations de -179 jusqu'à 180 degrées. 


**Gestion des angles dépassant 90°**

La fonction rotation_management(angle) côté Python gère automatiquement les angles supérieurs à 90° en décomposant le mouvement en plusieurs sous-étapes de saisie/pose/rotation :

| **Plage d'angle**    | **Stratégie**                                                               |
| -------------------- | --------------------------------------------------------------------------- |
| 0°                   | Saisir uniquement                                                           |
| 0° < angle ≤ 90°     | Saisir → Tourner(angle)                                                     |
| 90° < angle ≤ 180°   | Saisir → Tourner(90°) → Poser → Tourner(0°) → Saisir → Tourner(angle − 90°) |
| −90° ≤ angle < 0°    | Tourner(−angle) → Saisir → Tourner(0°)                                      |
| −180° ≤ angle < −90° | Séquence inverse symétrique                                                 |

<br>

<br>


**4\. Pompe et électrovanne**

**Principe de fonctionnement**

Le système de préhension fonctionne par **aspiration pneumatique** :

- La **pompe** crée une dépression dans le circuit
- L'**électrovanne** (normalement ouverte) est fermée pendant la saisie pour maintenir la dépression, et ouverte pendant la pose pour relâcher la pièce

**Implémentation**

Le servo du bras Z est piloté en **PWM généré par bit-banging** (pas de timer matériel requis). Une impulsion de 500 µs correspond à la position haute, 2500 µs à la position basse. 50 impulsions sont envoyées en boucle pour maintenir la position pendant environ 1 seconde.

La séquence complète d'un cycle de saisie (pick_place(1)) :

- Descendre le bras (servo → position basse)
- Attendre 2 secondes (Z_DOWN_DWELL_MS)
- Activer la pompe + fermer la valve
- Attendre 3 secondes pour que l'aspiration se stabilise (PICK_SUCTION_MS)
- Remonter le bras

La séquence de pose (pick_place(0)) est similaire, avec la valve ouverte à l'étape 3 et un temps d'attente de 1 seconde pour que la pièce se détache.

<br>

<br>
**5\. Réflexion sur l'architecture logicielle**

**Pourquoi ne pas utiliser GRBL ?**

La première piste envisagée pour piloter le robot était **GRBL**, un firmware open-source très répandu pour les machines CNC. Cependant, GRBL présente une limitation importante pour ce projet : il ne gère pas les servomoteurs. Or le robot en nécessite deux (bras Z et rotation de pièce), en plus de la pompe à aspiration. Intégrer ces éléments dans GRBL aurait demandé des modifications profondes et difficiles à maintenir.

**Solution retenue : firmware sur mesure**

La décision a donc été prise de développer un **firmware Arduino entièrement personnalisé**. Cette approche offre un contrôle total sur le protocole de communication et les comportements des actionneurs.

Le firmware est organisé en modules bien séparés :

| **Fichier**         | **Responsabilité**                        |
| ------------------- | ----------------------------------------- |
| config.h            | Toutes les constantes configurables       |
| steppers.h/.cpp     | Déplacement du portique X/Y               |
| pick_place.h/.cpp   | Servo Z + pneumatique                     |
| rotation.h/.cpp     | Servo de rotation                         |
| parser.h/.cpp       | Protocole série et dispatch des commandes |
| puzzle_firmware.ino | Point d'entrée setup() / loop()           |

Chaque module a une responsabilité unique, ce qui facilite la maintenance et les tests.


<br>

<br>







**6\. Développement de la vision**

**Introduction**

La vision par ordinateur est assurée par une **webcam USB** *https://www.digikey.fr/fr/products/detail/dfrobot/FIT0892/18069226* positionnée au-dessus du plateau. Le traitement d'image repose sur la bibliothèque **OpenCV** et utilise les marqueurs **ArUco** (dictionnaire DICT_6X6_250) pour localiser les pièces du puzzle. *reference Aruco: https://youtu.be/bS00Vs09Upw?si=dmPM06baYDc_qxNE*




**Calibration de la caméra**

Avant toute détection, la caméra doit être calibrée pour corriger la distorsion optique de l'objectif. Ce processus utilise une **mire d'échiquier** imprimée et le script Testings/camera/camera_calib.py.

mire d'échiquier : 
![Alt text](https://github.com/Makerspace-Amiens-2025-26/Puzzle-Bot-Groupe01/blob/main/docs/images/chessboard.png)

La calibration produit deux paramètres essentiels :

- **La matrice intrinsèque** (CAMERA_MATRIX) - décrit la focale et le centre optique
- **Les coefficients de distorsion** (DIST_COEFFS) - décrivent la déformation radiale et tangentielle de l'objectif
  
*Distorsion radiale : due à la forme des lentilles, elle fait varier le grossissement selon la distance au centre de l’image, ce qui peut faire paraître les objets près des bords plus grands ou plus petits et courber les lignes droites (effet barillet ou coussinet).
Distorsion tangentielle : due à un mauvais alignement des lentilles par rapport au capteur, elle décale localement les points de l’image, ce qui déforme les formes et fait apparaître les lignes droites comme légèrement tordues ou asymétriques.*

Ces valeurs sont ensuite intégrées directement dans find_aruco_position.py et utilisées à chaque frame pour "redresser" l'image avant toute détection.

Le dossier Testings/camera/ contient également des outils pour vérifier visuellement le résultat (test_calib_1.py), ajuster les paramètres en temps réel avec des curseurs (test_calib_2.py), et prévisualiser le pipeline complet (crop_zoom_sharpen.py).

**Pipeline de traitement d'image**

Pour maximiser la précision de détection, les frames passent par un **pipeline en 5 étapes** avant d'être analysées :

- **Capture brute** - frame directe depuis la webcam
- **Correction de distorsion** (cv2.remap) - redresse l'image avec les paramètres de calibration
- **Recadrage** - calcul d'une zone d'intérêt autour des marqueurs de référence (IDs 0, 1, 2)
- **Zoom** - agrandissement de la zone recadrée à 1280×720 pixels
- **Netteté** (unsharp mask) - accentuation des contrastes pour améliorer la détection des marqueurs

Pour réduire le bruit de détection lié aux variations de luminosité et aux petits mouvements de la caméra, chaque position est calculée en **moyennant 70 frames consécutives**. Seules les frames où les 4 marqueurs nécessaires sont tous visibles sont prises en compte.

Un paramètre DEBUG_STAGE permet d'arrêter le pipeline à n'importe quelle étape pour visualiser le résultat intermédiaire, ce qui s'est révélé très utile pendant le développement.


<br>

<br>



**7\. Choix du mode de coordonnées**

**Système de référence ArUco**

Trois marqueurs ArUco sont fixés de manière permanente sur le bâti du robot et définissent le repère de coordonnées :

| **Marqueur** | **Rôle** | **Position réelle** |
| ------------ | -------- | ------------------- |
| ID 0         | Origine  | (0, 0)              |
| ID 1         | Axe X    | (4, 0)              |
| ID 2         | Axe Y    | (0, 4)              |


![Alt text](https://github.com/Makerspace-Amiens-2025-26/Puzzle-Bot-Groupe01/blob/main/docs/images/Coordinate%20system.png?raw=true)

La distance entre les marqueurs de référence correspond à **une unité réelle = 4 unités de grille**, avec un **pas de grille de 60 mm**.

**Conversion pixels → coordonnées réelles**

À partir des positions en pixels des trois marqueurs de référence, le code calcule :

- L'**origine** en pixels (position du marqueur ID 0)
- Les **facteurs d'échelle** scale_x et scale_y (distance réelle / distance en pixels)

La conversion d'un point image en coordonnées réelles est ensuite :

real_x = (pixel_x - origin_x) × scale_x

real_y = -((pixel_y - origin_y) × scale_y) ← Y inversé (convention image vs robot)

**Conversion coordonnées réelles → pas moteur**

Une fois les coordonnées réelles connues, la conversion vers les pas moteur suit la formule :

x_steps = 100 + x_réel × STEPS_PER_MM_X × 60

y_steps = 196 + y_réel × STEPS_PER_MM_Y × 60

Les constantes 100 et 196 correspondent à la position du marqueur origine dans l'espace des pas moteur.

**Détection de l'angle par la caméra (v4)**

Dans la version finale du solveur, l'angle de chaque pièce est mesuré directement par la caméra. Chaque marqueur ArUco possède quatre coins dans un ordre fixe (TL, TR, BR, BL). Le vecteur TL→TR définit l'axe horizontal du marqueur.

L'angle est mesuré **par rapport au marqueur de référence ID 0**, ce qui annule automatiquement l'inclinaison physique de la caméra. Les deux axes (horizontal et vertical) du marqueur sont calculés, ramenés dans \[−90°, 90°\], et celui ayant la valeur absolue la plus faible est retenu. Le signe est ensuite inversé lors du passage au solveur (piece_angles = \[-angle for ...\]) pour respecter la convention de rotation du servo.




<br>
<br>


**8. Homographie du plateau**

Une étude a été menée pour quantifier la précision des coordonnées détectées par la caméra, avant et après traitement d'image, sur une grille de calibration 4×4 (16 positions de référence).

L'erreur moyenne (distance euclidienne entre position mesurée et position réelle) passe de **0.3194** avant traitement d'image à **0.1564** après — soit une réduction de plus de 50 %. Le traitement d'image (undistort, crop, zoom, sharpen) reste à ce jour la méthode la plus efficace testée.

Deux méthodes de recalibration géométrique globale ont ensuite été évaluées sur les mêmes points : le **Thin Plate Spline (TPS)** et une **déformation polynomiale cubique**. Dans notre contexte, ni l'une ni l'autre n'a permis d'améliorer les résultats (erreurs de 0.3706 et 0.3456 respectivement, donc supérieures au traitement d'image seul).

Une nouvelle méthode de **correction locale par interpolation géométrique** a été proposée pour la suite : plutôt qu'une fonction globale sur tout le plateau, on identifie le quadrilatère de calibration (4 points voisins) contenant la mesure, et on pondère chaque sommet par l'aire de la région opposée — généralisation en 2D d'une simple interpolation linéaire.

Détails complets de la méthodologie, des mesures, et des formules : voir [étape 5 du journal de bord](https://github.com/Makerspace-Amiens-2025-26/Puzzle-Bot-Groupe01/blob/main/docs/etapes/etape_5.md).

**Conclusion et prochaine étape — notre méthode**

Le traitement d'image reste pour l'instant notre meilleure approche de correction. Les méthodes de recalibration globale (TPS, Cubic Warp) n'ont pas apporté d'amélioration mesurable. La piste retenue pour la suite est la correction locale par aires, combinée à une calibration plus fine (grille à résolution triplée) et à l'intégration de l'angle de rotation de la pièce détectée, pour obtenir une description complète de sa position **(X, Y, θ)**.



<br><br><br>




**9\. Protocole de communication série**

Le firmware reçoit des commandes via le port **USB série à 115 200 bauds**. Les commandes sont regroupées en **paquets** : une suite de tokens séparés par des points-virgules, terminée par le mot-clé END.

Exemple de paquet :

h;x4998s200;y3724s200;p1;r45;p0;END

Le firmware répond ACK{n} après chaque paquet exécuté, et OK lorsqu'il reçoit END. Ce mécanisme de **handshake** garantit que Python n'envoie le paquet suivant qu'une fois le précédent entièrement exécuté.
<br>
![Alt text](https://github.com/Makerspace-Amiens-2025-26/Puzzle-Bot-Groupe01/blob/main/docs/images/communication_v2_1.png)

<br>


![Alt text](https://github.com/Makerspace-Amiens-2025-26/Puzzle-Bot-Groupe01/blob/main/docs/images/communication_v2_2.png)

**Jeu de commandes**

| **Commande**     | **Effet**                                   |
| ---------------- | ------------------------------------------- |
| h                | Homing (indispensable au démarrage)         |
| x{pos}s{vitesse} | Déplacement X vers position absolue en pas  |
| y{pos}s{vitesse} | Déplacement Y vers position absolue en pas  |
| p1               | Saisir : descendre → aspiration ON → monter |
| p0               | Poser : descendre → aspiration OFF → monter |
| r{angle}         | Rotation de la pièce (0-90°)                |
| d                | Pause                                       |
| END              | Fin de paquet → le firmware répond OK       |

**Séquence de homing**

Le homing suit une procédure en 3 temps pour chaque axe :

- **Approche rapide** vers la fin de course
- **Recul** une fois la fin de course déclenchée
- **Approche lente** pour trouver le point de déclenchement précis

Cette triple séquence garantit une position zéro reproductible même si le robot est arrêté en cours de course.


<br><br><br>



**10\. Logique générale de résolution**

**Vue d'ensemble**

Le solveur Python orchestre l'ensemble du processus. Il existe en trois versions progressives :

- **v2** - positions et angles saisis manuellement. Utile pour les tests sans caméra.
- **v3** - positions détectées par caméra, angles encore manuels.
- **v4** - positions et angles tous deux détectés par caméra. Version finale.


