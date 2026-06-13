---
layout: default
title: Programmation et électronique
parent: Etapes de fabrication
nav_order: 3
---

# Programmation

## Architecture Logicielle & Programmation

Le contrôle du Puzzle Bot repose sur un écosystème logiciel divisé en deux parties principales : un **firmware embarqué sur mesure** (C++/Arduino) pour la gestion matérielle basse couche, et un **programme superviseur** (Python) pour l'intelligence artificielle et le traitement d'image.

### Firmware Arduino
Plutôt que d'utiliser un micrologiciel générique comme GRBL, incapable de gérer nativement nos deux servomoteurs et les cycles spécifiques de la pompe pneumatique, nous avons développé un firmware C++ entièrement personnalisé.

Le code est structuré de manière modulaire afin d'isoler les responsabilités :
* `config.h` : Centralisation de l'ensemble des constantes, broches et calibrations mécaniques (ex: rapports de pas/mm).
* `steppers.cpp` : Gestion des rampes d'accélération et déplacements synchronisés des axes X et Y.
* `pick_place.cpp` : Séquencement temporel de la préhension (Descente du bras, temporisation, activation du vide, remontée)
* `parser.cpp` : Analyseur syntaxique chargé de décoder les commandes envoyées sur le port série USB selon un protocole textuel strict terminé par le mot-clé.

### Superviseur Python et Vision par Ordinateur
L'intelligence du robot s'exécute sur un ordinateur via un script Python orchestrant la résolution. 

#### Pipeline de traitement d'image
Une caméra grand angle capture le plateau. L'image brute subit une série de traitement numérique avant analyse pour maximiser sa netteté:
**Correction de distorsion :** Redressement de l'image via des coefficients optiques calculés au préalable avec une mire d'échiquier.
**Homographie et correction géométrique (TPS) :** Même après correction optique, la perspective et l'angle de la caméra introduisent des erreurs spatiales. Nous appliquons un algorithme mathématique **Thin Plate Spline (TPS)** basé sur une grille de calibration de 16 points réels. Cette correction réduit l'erreur moyenne de détection de plus de 50 % (passant de $0.3194$ à $0.1564$ unité), garantissant une précision millimétrique sur le plateau

#### B. Détection des pièces et angles (ArUco)
Le script utilise la bibliothèque `OpenCV ArUco` pour localiser instantanément les 4 pièces disposées sur la zone de détection. Les coordonnées en pixels sont converties en pas moteurs réels grâce à des repères d'origine fixes installés sur le châssis.
L'angle de chaque pièce est calculé en comparant le vecteur d'orientation de son marqueur à l'axe de référence du robot.

### 3. Cycle d'exécution et protocole d'échange (Handshake)
La communication entre Python et l'Arduino est sécurisée par un mécanisme de *handshake* (poignée de main) pour éviter toute surcharge de la mémoire tampon de l'Arduino
Python analyse le plateau par la caméra et génère une suite d'instructions (G-code personnalisé).
Cette chaîne est découpée en micro-paquets (ex: `h;x4998s200;y3724s200;p1;END`).
Python transmet un paquet et se met en attente.
L'Arduino reçoit les ordres, les exécute fidèlement (déplacement, activation de l'électrovanne, etc.) puis retourne le signal `ACK` ou `OK` une fois la tâche physiquement accomplie.
À la réception du signal de confirmation, Python envoie le paquet suivant.


# Electronique


## 🔌 Architecture Électronique & Câblage

L'architecture électronique du Puzzle Bot est conçue autour d'une carte microcontrôleur **Arduino UNO** sur laquelle vient s'emboîter une carte d'extension **CNC Shield V3**. Cette configuration permet de centraliser la distribution de la puissance (12V) et les signaux de commande de l'ensemble des actionneurs et capteurs.

Voici le schéma synoptique de notre installation électronique (mettant en évidence les liaisons entre l'Arduino, le CNC Shield, les moteurs et les capteurs) :

![Schéma de câblage](../images/SchémaDorian.png)


### 1. Tableau des connexions (Brochage)

Pour garantir la maintenabilité du robot, l'intégralité du câblage physique a été répertoriée selon l'affectation suivante :

| Composant | Broche Arduino | Rôle sur le CNC Shield | Type de signal |
| :--- | :---: | :---: | :--- |
| **Moteurs X (x2)** | D2 / D5 | X.STEP / X.DIR | Impulsions de commande (Miroir) |
| **Moteur Y** | D3 / D6 | Y.STEP / Y.DIR | Impulsions de commande |
| **Fin de course X** | D9 | X+ | Entrée numérique (Pull-up) |
| **Fin de course Y** | D10 | Y+ | Entrée numérique (Pull-up) |
| **Servo Rotation** | D11 | Z+ | Sortie PWM (0-180°) |
| **Servo Z (Bras)** | A5 | SCL | Sortie PWM (Bit-banging) |
| **Pompe à vide** | D4 | Z.STEP | Commande Tout-ou-Rien (via MOSFET) |
| **Électrovanne** | D7 | Z.DIR | Commande Tout-ou-Rien (via MOSFET) |

### 2. Gestion de la puissance et carte MOSFET (KiCad)
Les sorties de l'Arduino UNO délivrent un courant maximal insuffisant et une tension limitée à 5V. Or, l'électrovanne et la pompe pneumatique requièrent une alimentation stable en **12 Volts**. 

Pour résoudre ce problème, nous avons développé une carte électronique d'interface de puissance sous le logiciel **KiCad**. Cette carte intègre des transistors **MOSFET** faisant office de relais électroniques rapides. Lorsqu'un signal 5V est émis par les broches D4 ou D7 de l'Arduino, le MOSFET commute et libère la puissance de la ligne 12V pour actionner la pompe ou ouvrir la valve pneumatique.

### 3. Optimisation et routage
Afin de fiabiliser le fonctionnement du robot et de libérer l'espace supérieur pour les déplacements du portique, l'ensemble des cartes électroniques (Arduino, CNC Shield, circuit MOSFET) a été implanté directement **sous le plateau** de la machine. Les câbles moteurs et capteurs ont été rallongés et guidés au travers du châssis pour éviter tout risque d'arrachement ou d'interférence avec la tête mobile.