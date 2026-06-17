---
layout: default
title: Contrôle Qualité
parent: Etapes de fabrication
nav_order: 7
---
# Contrôle qualité

## Vérifications à effectuer

Une fois l’assemblage de la machine terminé, plusieurs contrôles ont été réalisés afin de garantir son bon fonctionnement global, son respect du cahier des charges établi au préalable et de valider les améliorations apportées lors de la phase de finition.
Ces vérifications ont porté sur les principaux éléments mécaniques, électroniques et fonctionnels de la machine.

**Alignement des composants**

Les vérifications suivantes ont été effectuées :

- Contrôle de l’équerrage du châssis
- Vérification du parallélisme des guidages
- Alignement des moteurs avec les poulies
- Vérification du positionnement du portique
- Contrôle de la fixation de la caméra sur le bras

Ces contrôles permettent de limiter les contraintes mécaniques et d’améliorer la précision des déplacements. Ils sont essentiels, notamment après les ajustements réalisés sur la calibration du système et la position de la caméra.

**Stabilité de la structure**

Nous avons également vérifié :

- La rigidité du châssis
- Le serrage des fixations
- L’absence de mouvements parasites entre les différentes pièces assemblées
- La stabilité du plateau et du portique
- La bonne tension des courroies après retouches

Ces tests permettent de s’assurer que les modifications effectuées lors de la phase de finition (retension des courroies, ajustements mécaniques) ont bien amélioré la stabilité générale de la machine.

**Test des déplacements et du système**

Enfin, des essais de fonctionnement ont été réalisés pour vérifier :

- La fluidité des mouvements sur les axes X et Y
- La précision du bras lors de la prise et du positionnement des pièces
- Le comportement du support de pompe, notamment sa régularité de déplacement
- Le bon fonctionnement de la pompe après modifications
- L’absence de points de blocage mécaniques
- Le comportement des pièces imprimées en 3D sous contrainte

Ces tests ont également permis de confirmer les améliorations apportées à la carte électronique, qui a été révisée à plusieurs reprises pour corriger différents dysfonctionnements et améliorer la stabilité globale du système.

## Validation générale

Les essais réalisés montrent que la machine fonctionne de manière globalement stable et cohérente. Après les différentes corrections apportées en finition (mécanique, électronique et esthétique), le système est devenu plus fiable, plus précis et mieux optimisé pour réaliser sa tâche de manière autonome.

## Conclusion

Le développement du Puzzle Bot a constitué un projet d'ingénierie complet et particulièrement formateur, associant la conception mécanique, la réalisation électronique et l'intégration de la vision par ordinateur. L'objectif initial a été pleinement atteint.

### Synthèse des résultats et réussites

Au cours des différentes phases d'itérations, notre groupe a su surmonter des défis techniques majeurs :

Fiabilisation de l'aspiration : l'intégration conjointe d'une pompe à air et d'une électrovanne pilotées par notre propre carte d'interface MOSFET conçue sur KiCad et qui a permis d'obtenir un cycle d'aspiration et de relâchement instantané et propre.

Précision millimétrique : l'apport du traitement d'image combiné à l'algorithme de recalibration géométrique s'est avéré déterminant. Les mesures expérimentales ont mis en évidence une réduction drastique de l'erreur moyenne de positionnement assurant une déposition chirurgicale des pièces sur le plateau.

### Perspectives d'évolution

Bien que le robot soit aujourd'hui totalement fonctionnel, plusieurs pistes restent envisagées pour optimiser le système :

Échantillonnage de calibration plus fin : Augmenter la résolution de la grille de référence (passer d'une matrice 4×4 à un maillage trois fois plus dense) pour cartographier et corriger encore plus finement les déformations optiques.

Optimisation des trajectoires : Améliorer le solveur pour intégrer un algorithme de tri des pièces permettant de minimiser la distance totale parcourue par le portique lors de la résolution du puzzle.

En conclusion, ce projet nous aura permis de mettre en pratique une véritable méthodologie "try, test and learn" au sein du Makerspace. Face aux imprévus matériels (délais de livraison de la caméra, mise au point de la puissance du circuit de la pompe), l'entraide, la répartition rigoureuse des tâches et la documentation continue sur GitHub ont été les clés de la réussite de notre groupe.
