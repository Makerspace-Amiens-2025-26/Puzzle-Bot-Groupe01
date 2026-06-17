---
layout: default
title: Calibration et améliorations liées à la caméra
parent: Etapes de fabrication
nav_order: 5
---

# Calibration et amélioration de la précision d'un système de détection de position par caméra

## Introduction

Dans le cadre du développement d'un système de détection de position basé sur la vision par ordinateur, une étude a été menée afin d'évaluer la précision des coordonnées détectées par une caméra avant et après l'application d'un traitement d'image.

L'objectif du système est d'identifier avec précision la position d'un objet sur un plateau de jeu discret représenté dans un repère bidimensionnel.

Cette étude présente :

- la méthodologie de mesure ;
- la méthode de calcul de l'erreur ;
- les résultats obtenus ;
- les différentes approches de correction étudiées ;
- une nouvelle méthode de correction géométrique locale proposée pour les travaux futurs.

# Mise en place de la calibration

Le plateau de référence est constitué d'une grille de 4 × 4 positions.

Les coordonnées théoriques sont :

<table>
<tr><th>X</th><th>Y</th></tr>
<tr><td>1</td><td>1</td></tr>
<tr><td>1</td><td>2</td></tr>
<tr><td>1</td><td>3</td></tr>
<tr><td>1</td><td>4</td></tr>
<tr><td>2</td><td>1</td></tr>
<tr><td>2</td><td>2</td></tr>
<tr><td>2</td><td>3</td></tr>
<tr><td>2</td><td>4</td></tr>
<tr><td>3</td><td>1</td></tr>
<tr><td>3</td><td>2</td></tr>
<tr><td>3</td><td>3</td></tr>
<tr><td>3</td><td>4</td></tr>
<tr><td>4</td><td>1</td></tr>
<tr><td>4</td><td>2</td></tr>
<tr><td>4</td><td>3</td></tr>
<tr><td>4</td><td>4</td></tr>
</table>


Pour chacune de ces positions, une mesure a été réalisée avant puis après l'application du traitement d'image.

# Mesures obtenues

## Avant traitement d'image

| Position réelle | Position mesurée  |
| --------------- | ----------------- |
| (1,1)           | (0.9399 , 0.9141) |
| (1,2)           | (0.9119 , 1.4834) |
| (1,3)           | (0.9707 , 3.0300) |
| (1,4)           | (1.0301 , 4.0719) |
| (2,1)           | (2.0553 , 0.8971) |
| (2,2)           | (2.3600 , 1.3297) |
| (2,3)           | (2.1807 , 2.9900) |
| (2,4)           | (2.1281 , 4.0797) |
| (3,1)           | (3.1331 , 0.8997) |
| (3,2)           | (3.1700 , 1.9799) |
| (3,3)           | (3.7137 , 2.7206) |
| (3,4)           | (3.4764 , 3.9699) |
| (4,1)           | (4.1084 , 0.9300) |
| (4,2)           | (4.1500 , 1.9500) |
| (4,3)           | (4.1304 , 2.9707) |
| (4,4)           | (4.0500 , 3.8999) |

## Après traitement d'image

| Position réelle | Position mesurée  |
| --------------- | ----------------- |
| (1,1)           | (1.0667 , 0.9699) |
| (1,2)           | (1.0824 , 1.9235) |
| (1,3)           | (1.0825 , 2.8886) |
| (1,4)           | (1.0511 , 3.9148) |
| (2,1)           | (2.0392 , 0.9725) |
| (2,2)           | (2.0549 , 1.9136) |
| (2,3)           | (2.0707 , 2.8704) |
| (2,4)           | (2.0863 , 3.8820) |
| (3,1)           | (3.0118 , 0.9572) |
| (3,2)           | (3.0431 , 1.8979) |
| (3,3)           | (3.0588 , 2.8547) |
| (3,4)           | (3.1059 , 3.8742) |
| (4,1)           | (4.0159 , 0.9411) |
| (4,2)           | (4.0157 , 1.8979) |
| (4,3)           | (4.0784 , 2.8547) |
| (4,4)           | (4.1412 , 3.8899) |

# Méthode de calcul de l'erreur

Pour chaque point de calibration, l'erreur est calculée à partir de la distance de Manhattan :

Erreur = $\sqrt{(X_{\text{mesuré}} - X_{\text{réel}})^2 + (Y_{\text{mesuré}} - Y_{\text{réel}})^2}$


Cette métrique permet de prendre en compte simultanément les erreurs horizontales et verticales.

L'erreur moyenne est ensuite calculée sur les 16 points de calibration :

Erreur moyenne = Somme des erreurs / Nombre de points

# Résultats

## Avant traitement d'image

Erreur moyenne :

0.3194

## Après traitement d'image

Erreur moyenne :

0.1564

Le traitement d'image réduit donc l'erreur moyenne de plus de 50 %, démontrant son efficacité pour améliorer la qualité de détection.

# Méthodes de correction étudiées

Après l'amélioration apportée par le traitement d'image, plusieurs méthodes de recalibration géométrique ont été étudiées.

## Thin Plate Spline (TPS)

Le TPS construit une transformation non linéaire à partir des points de calibration.

Cette méthode est particulièrement efficace lorsque les déformations sont locales et irrégulières.

Elle permet de reproduire très fidèlement les points utilisés lors de la phase de calibration.



![Alt text](https://github.com/Makerspace-Amiens-2025-26/Puzzle-Bot-Groupe01/blob/main/docs/images/TPS.png)

<br>

## Déformation polynomiale cubique

Une seconde approche consiste à ajuster deux surfaces polynomiales :

Xcorr = f(Xmesuré,Ymesuré)

Ycorr = g(Xmesuré,Ymesuré)

Cette méthode est souvent utilisée pour modéliser les distorsions géométriques introduites par les systèmes optiques.

# Comparaison des résultats

Les différentes approches ont été évaluées à partir de l'erreur moyenne calculée sur les points de calibration.

| Méthode                  | Erreur moyenne |
| ------------------------ | -------------- |
| Avant traitement d'image | 0.3194         |
| Après traitement d'image | 0.1564         |
| Cubic Warp               | 0.3456         |
| TPS                      | 0.3706         |

On constate que les configurations testées du modèle Cubic Warp et du TPS n'ont pas permis d'améliorer les performances dans notre contexte d'application.

Le traitement d'image reste actuellement la méthode offrant les meilleurs résultats expérimentaux.

# Proposition d'une nouvelle méthode de correction locale

## Motivation

Les méthodes précédentes construisent une fonction globale sur l'ensemble du plateau.

Or, dans un plateau de jeu, chaque mesure se situe à l'intérieur d'une cellule définie par quatre points de calibration voisins.

Il apparaît donc naturel de construire une correction locale basée uniquement sur ces quatre points.

## Inspiration en une dimension

Considérons deux points de calibration :

1 → 1.034

2 → 1.920

Si une mesure est détectée entre ces deux valeurs, la correction est obtenue par une moyenne pondérée.

Plus la mesure se rapproche d'un point de calibration, plus la correction tend vers la valeur réelle associée à ce point.

Cette idée constitue la base de la généralisation en deux dimensions.

## Généralisation en deux dimensions

Pour une mesure donnée, on commence par identifier le quadrilatère de calibration dans lequel elle se trouve.

Ce quadrilatère est défini par quatre points :

P1 P2 P3 P4

Les côtés opposés sont ensuite prolongés jusqu'à obtenir leurs points d'intersection.

Ces intersections définissent deux points de fuite géométriques.

Deux droites sont alors construites :

- la première relie le premier point de fuite à la mesure ;
- la seconde relie le second point de fuite à la mesure.

Ces droites divisent le quadrilatère en quatre régions :

A1 A2 A3 A4

<br><br><br>
![Alt text](https://github.com/Makerspace-Amiens-2025-26/Puzzle-Bot-Groupe01/blob/main/docs/images/my_correction_algo.png)

## Calcul des poids

Chaque sommet reçoit un poids basé sur la surface de la région opposée.

Ainsi :

Poids(P1) = A1

Poids(P2) = A2

Poids(P3) = A3

Poids(P4) = A4

Cette approche constitue l'extension naturelle de l'interpolation utilisée en une dimension.

## Calcul de la position corrigée

La position corrigée est alors calculée par :

Xcorr = (A1·X1 + A2·X2 + A3·X3 + A4·X4) / (A1 + A2 + A3 + A4)

Ycorr = (A1·Y1 + A2·Y2 + A3·Y3 + A4·Y4) / (A1 + A2 + A3 + A4)

où les coordonnées (Xi,Yi) correspondent aux positions réelles associées aux sommets du quadrilatère.

# Travaux futurs

Les mesures présentées dans cette étude ont été réalisées uniquement sur les coordonnées entières de la grille.

Afin d'améliorer davantage la précision du système et de mieux caractériser les déformations locales, une nouvelle campagne de calibration est prévue.

L'idée est d'échantillonner le plateau avec une résolution trois fois plus fine :

(0,0)

(0,0.333)

(0,0.666)

(0,1)

…

jusqu'à

(4,4)

Cette nouvelle grille de calibration permettra :

- d'augmenter significativement le nombre de points de référence ;
- d'obtenir une cartographie plus précise des erreurs locales ;
- d'évaluer plus finement les performances des différentes méthodes de correction.

Une autre piste de recherche consiste à introduire la notion d'orientation de l'objet détecté.

Actuellement, seules les coordonnées de position sont prises en compte.

À terme, le système devra également estimer l'angle de rotation de l'objet afin d'obtenir une description complète de son état :

(X, Y, θ)

L'intégration simultanée de la position et de l'orientation ouvre la voie à des modèles de calibration plus avancés capables de corriger non seulement les erreurs de translation, mais également les erreurs liées à la perspective et aux rotations observées dans l'image.

# Conclusion

Cette étude a permis de quantifier précisément les performances du système de détection de position et de mesurer l'impact du traitement d'image sur la précision des coordonnées obtenues.

Les résultats montrent une réduction importante de l'erreur moyenne après traitement d'image, passant de 0.3194 à 0.1564.

Plusieurs techniques de recalibration ont ensuite été explorées, notamment les approches TPS et Cubic Warp.

Enfin, une nouvelle méthode de correction locale basée sur une interpolation géométrique par aires a été proposée. Cette approche exploite directement la structure de la grille de calibration et constitue une base prometteuse pour les futurs développements du projet.
