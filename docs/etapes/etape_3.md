---
layout: default
title: Programmation et électronique
parent: Etapes de fabrication
nav_order: 3
---

# Programmation

## Architecture Logicielle & Programmation

[cite_start]Le contrôle du Puzzle Bot repose sur un écosystème logiciel divisé en deux parties principales : un **firmware embarqué sur mesure** (C++/Arduino) pour la gestion matérielle basse couche, et un **programme superviseur** (Python) pour l'intelligence artificielle et le traitement d'image[cite: 321, 326].

### 1. Firmware Arduino (Basse couche)
[cite_start]Plutôt que d'utiliser un micrologiciel générique comme GRBL, incapable de gérer nativement nos deux servomoteurs et les cycles spécifiques de la pompe pneumatique, nous avons développé un **firmware C++ entièrement personnalisé**[cite: 316, 317, 318, 321].

[cite_start]Le code est structuré de manière modulaire afin d'isoler les responsabilités[cite: 325]:
* [cite_start]`config.h` : Centralisation de l'ensemble des constantes, broches et calibrations mécaniques (ex: rapports de pas/mm)[cite: 296, 308].
* [cite_start]`steppers.cpp` : Gestion des rampes d'accélération et déplacements synchronisés des axes X et Y[cite: 324].
* [cite_start]`pick_place.cpp` : Séquencement temporel de la préhension (Descente du bras $\rightarrow$ temporisation $\rightarrow$ activation du vide $\rightarrow$ remontée)[cite: 324, 392].
* [cite_start]`parser.cpp` : Analyseur syntaxique chargé de décoder les commandes envoyées sur le port série USB (115 200 bauds) selon un protocole textuel strict terminé par le mot-clé `END`[cite: 400, 401].

### 2. Superviseur Python et Vision par Ordinateur
[cite_start]L'intelligence du robot s'exécute sur un ordinateur via un script Python orchestrant la résolution[cite: 429]. 

#### A. Pipeline de traitement d'image (OpenCV)
[cite_start]Une caméra grand angle capture le plateau de jeu[cite: 328]. [cite_start]L'image brute subit un pipeline de traitement numérique avant analyse pour maximiser sa netteté[cite: 339, 340]:
1. [cite_start]**Correction de distorsion :** Redressement de l'image via des coefficients optiques calculés au préalable avec une mire d'échiquier[cite: 331, 332, 341].
2. [cite_start]**Homographie et correction géométrique (TPS) :** Même après correction optique, la perspective et l'angle de la caméra introduisent des erreurs spatiales[cite: 365, 366]. [cite_start]Nous appliquons un algorithme mathématique **Thin Plate Spline (TPS)** basé sur une grille de calibration de 16 points réels[cite: 369, 372]. [cite_start]Cette correction réduit l'erreur moyenne de détection de plus de 50 % (passant de $0.3194$ à $0.1564$ unité), garantissant une précision millimétrique sur le plateau[cite: 485, 487, 488].

#### B. Détection des pièces et angles (ArUco)
[cite_start]Le script utilise la bibliothèque `OpenCV ArUco` pour localiser instantanément les 4 pièces disposées sur la zone de détection[cite: 329, 436]. [cite_start]Les coordonnées en pixels sont converties en pas moteurs réels grâce à des repères d'origine fixes installés sur le châssis[cite: 348, 358]. 
[cite_start]L'angle de chaque pièce est calculé en comparant le vecteur d'orientation de son marqueur à l'axe de référence du robot[cite: 424, 425].

### 3. Cycle d'exécution et protocole d'échange (Handshake)
[cite_start]La communication entre Python et l'Arduino est sécurisée par un mécanisme de *handshake* (poignée de main) pour éviter toute surcharge de la mémoire tampon de l'Arduino[cite: 405]:
1. [cite_start]Python analyse le plateau par la caméra et génère une suite d'instructions (G-code personnalisé)[cite: 436, 437].
2. [cite_start]Cette chaîne est découpée en micro-paquets (ex: `h;x4998s200;y3724s200;p1;END`)[cite: 403, 438].
3. [cite_start]Python transmet un paquet et se met en attente[cite: 439].
4. [cite_start]L'Arduino reçoit les ordres, les exécute fidèlement (déplacement, activation de l'électrovanne, etc.) puis retourne le signal `ACK` ou `OK` une fois la tâche physiquement accomplie[cite: 404, 439, 442].
5. [cite_start]À la réception du signal de confirmation, Python envoie le paquet suivant[cite: 439].


# Electronique


## 🔌 Architecture Électronique & Câblage

[cite_start]L'architecture électronique du Puzzle Bot est conçue autour d'une carte microcontrôleur **Arduino UNO** sur laquelle vient s'emboîter une carte d'extension **CNC Shield V3**. [cite_start]Cette configuration permet de centraliser la distribution de la puissance (12V) et les signaux de commande de l'ensemble des actionneurs et capteurs.

### 1. Tableau des connexions (Brochage)

[cite_start]Pour garantir la maintenabilité du robot, l'intégralité du câblage physique a été répertoriée selon l'affectation suivante[cite: 296]:

| Composant | Broche Arduino | Rôle sur le CNC Shield | Type de signal |
| :--- | :---: | :---: | :--- |
| **Moteurs X (x2)** | D2 / D5 | X.STEP / X.DIR | [cite_start]Impulsions de commande (Miroir) [cite: 290, 446] |
| **Moteur Y** | D3 / D6 | Y.STEP / Y.DIR | [cite_start]Impulsions de commande [cite: 447] |
| **Fin de course X** | D9 | X+ | [cite_start]Entrée numérique (Pull-up) [cite: 295, 448] |
| **Fin de course Y** | D10 | Y+ | [cite_start]Entrée numérique (Pull-up) [cite: 295, 449] |
| **Servo Rotation** | D11 | Z+ | [cite_start]Sortie PWM (0-180°) [cite: 293, 416, 450] |
| **Servo Z (Bras)** | A5 | SCL | [cite_start]Sortie PWM (Bit-banging) [cite: 292, 389, 451] |
| **Pompe à vide** | D4 | Z.STEP | [cite_start]Commande Tout-ou-Rien (via MOSFET) [cite: 453] |
| **Électrovanne** | D7 | Z.DIR | [cite_start]Commande Tout-ou-Rien (via MOSFET) [cite: 454] |

### 2. Gestion de la puissance et carte MOSFET (KiCad)
[cite_start]Les sorties de l'Arduino UNO délivrent un courant maximal insuffisant et une tension limitée à 5V[cite: 288, 445]. [cite_start]Or, l'électrovanne et la pompe pneumatique requièrent une alimentation stable en **12 Volts**. 

Pour résoudre ce problème, nous avons développé une carte électronique d'interface de puissance sous le logiciel **KiCad**. Cette carte intègre des transistors **MOSFET** faisant office de relais électroniques rapides. [cite_start]Lorsqu'un signal 5V est émis par les broches D4 ou D7 de l'Arduino, le MOSFET commute et libère la puissance de la ligne 12V pour actionner la pompe ou ouvrir la valve pneumatique[cite: 452, 453, 454].

### 3. Optimisation et routage
Afin de fiabiliser le fonctionnement du robot et de libérer l'espace supérieur pour les déplacements du portique, l'ensemble des cartes électroniques (Arduino, CNC Shield, circuit MOSFET) a été implanté directement **sous le plateau** de la machine. Les câbles moteurs et capteurs ont été rallongés et guidés au travers du châssis pour éviter tout risque d'arrachement ou d'interférence avec la tête mobile.