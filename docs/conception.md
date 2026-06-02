---
layout: default
nav_order: 5
title: Conception et prototypage
---

# Conception et prototypage
Afin d'obtenir un robot optimisé et des plus performant, nous avons décidés de nous séparer les tâches. Chaqu'un à choisis un poste où il pense être le plus productif. Bien que nous étions chacuns sur notre partie, nous restons un groupe, alors s'il y a des imprévus ou si l'on ne comprends pas quelques choses, nous pouvons toujours compter sur les autres.


-Premières pièces 3D:

-Pompe: Nous n'avons pas réçu la pompe dès les premiers jours. Afin de combler ce temps, nous nous sommes renseigner directement sur comment la faire fonctionner. Ainsi, dès l'obtention de cette dernière, nous avons pus la connecter à notre carte arduino et commencer des petits tests. 
Nous avons découvert une petit pépin. Lorsque la pompe aspirait, tout aller bien, en revanche, elle ne la lachait pas correctement. La pièce se décrochait juste avec le temps et le manque d'aspiration, non pas car nous avions décider de lacher la pièce. Suite à de nombreuses minutes de recherches, nous avons réaliser que la puissance envoyer par la carte n'était pas suiffisante et qu'il fallait un nouveau driver. Pour cela, nous avons utiliser Kicad.
<iframe height="400" width="80%" src="https://modelembedder.net/embed?did=dc4e4dc410142a1f5ec17e75&wvm=v&wvmid=8dbde0cae67cbb0ab40cced3&eid=3f834839403a2d3bfa00f478&elementType=PARTSTUDIO" frameborder="0"></iframe>

-Moteur pas a pas: Le moteur pas a pas est utilisé pour se deplacer plus precisement. Il fonctionne en convertissant les impulsions électriques en mouvements angulaires discrets. Chaque impulsion appliquée au moteur le fait tourner d’un certain angle, appelé “pas”. En contrôlant la séquence d’impulsions, il est possible de faire tourner le moteur dans les deux sens, de manière plus ou moins rapide.
<iframe height="400" width="80%" src="https://modelembedder.net/embed?did=dc4e4dc410142a1f5ec17e75&wvm=v&wvmid=8dbde0cae67cbb0ab40cced3&eid=5e57f97f026c1f00d2344900&elementType=PARTSTUDIO" frameborder="0"></iframe>

-Les ServoMoteurs: Utilisé pour piloter un mouvement angulaire limité et pour  pour contrôler les mouvements précis de certaines pièces, comme la direction, les ailerons ou encore les gouvernes. C’est un composant essentiel dans les systèmes qui nécessitent des déplacements angulaires contrôlés. Le servomoteur RC combine un moteur électrique, un réducteur, un potentiomètre et un contrôleur électronique dans un seul boîtier compact.
<iframe height="400" width="80%" src="https://modelembedder.net/embed?did=dc4e4dc410142a1f5ec17e75&wvm=v&wvmid=8dbde0cae67cbb0ab40cced3&eid=f79d90442e1b479fbb8716f7&elementType=PARTSTUDIO" frameborder="0"></iframe>

-La CNC Shield:e CNC Shield est une carte d’extension pour Arduino, qui permet de contrôler facilement des machines à commande numérique (CNC), comme des fraiseuses, des machines de gravure, des imprimantes 3D et des traceurs de dessin
<iframe height="400" width="80%" src="https://modelembedder.net/embed?did=dc4e4dc410142a1f5ec17e75&wvm=v&wvmid=8dbde0cae67cbb0ab40cced3&eid=7ac83cab871f620abcc97dbd&elementType=ASSEMBLY" frameborder="0"></iframe>

-
