# RETEX.md - Retour d'Expérience

## Introduction
Ce projet de microservice de triangulation a été pour moi l'occasion d'appliquer rigoureusement l'approche **Test-First**. Ce document analyse comment cette méthodologie a façonné mon architecture, sécurisé mon code, mais aussi les pièges dans lesquels je suis tombé en voulant trop bien faire.

## 1. L'impact positif du Test-First (Ce que j'ai bien fait)

### Une architecture dictée par les tests
C'est sans doute le point le plus marquant. En voulant écrire les tests *avant* le code, je me suis vite rendu compte que je ne pouvais pas tout mélanger.
* Pour tester le contrôleur sans appeler le vrai réseau, j'ai été **forcé** d'utiliser l'injection de dépendances dans `app.py`. Ce n'était pas un choix esthétique, mais une nécessité pour pouvoir passer des "Mocks" dans mes tests.
* Résultat : Le code est naturellement découplé. `algorithm.py` est pur et testable isolément car j'ai commencé par écrire `test_triangulation_algorithm.py` avant même de savoir comment j'allais coder l'algo.

### Une robustesse native
En écrivant d'abord les tests pour les cas d'erreurs (ce que je faisais en suivant le `PLAN.md`), j'ai blindé l'application dès le départ.
* J'ai écrit un test qui envoie un payload binaire coupé en deux *avant* de coder la désérialisation. Cela m'a obligé à gérer les exceptions de `struct` et les vérifications de longueur immédiatement dans `serialization.py`.
* Sans cette approche, j'aurais probablement codé le "happy path" et oublié de gérer les paquets corrompus ou les Timeouts réseaux.

## 2. Les limites et excès (Ce que j'ai moins bien fait)

### Le piège de la "Sur-couverture"
L'approche Test-First m'a parfois poussé à tester pour le plaisir de voir la barre devenir verte, plutôt que pour la valeur métier.
* J'ai écrit des tests très artificiels pour atteindre 100% de coverage, comme mocker `struct.unpack` pour simuler une erreur interne à Python.
* **Critique :** C'est du "paranoïa coding". Tester que Python lève une erreur quand on lui passe une `string` au lieu d'un `float` n'apporte pas de valeur réelle au projet et alourdit la maintenance.

### L'illusion de sécurité sur l'algorithme
Le Test-First ne protège pas contre les mauvais choix de conception.
* J'ai écrit des tests pour des carrés et des pentagones (convexes). Mes tests passaient, donc je me sentais confiant.
* Cependant, je n'ai pas écrit de test "Test-First" pour une forme concave (comme une étoile). Résultat : mon code valide mes tests, mais l'algorithme de "Fan Triangulation" choisi est géométriquement insuffisant pour des cas réels complexes. Le vert des tests m'a donné une fausse assurance.

## 3. Analyse du Plan Initial vs Réalisation

Le `PLAN.md` a agi comme une spécification technique pour mes tests :

* **Adéquation :** Le plan listait les scénarios d'erreurs (404, 502, Invalid UUID). En Test-First, j'ai simplement traduit ces lignes du plan en fonctions de test dans `test_api.py` et `test_point_set_manager_client.py`, puis j'ai implémenté le code pour les satisfaire.
* **Manque :** Le plan mentionnait des tests de performance pour identifier les goulots d'étranglement. J'ai implémenté des tests de performance unitaires (temps d'exécution) pour respecter la consigne, mais ils sont arrivés *après* le code. Contrairement au reste, la performance n'a pas été pilotée par le "Test-First", et cela se sent : je n'ai pas optimisé la mémoire, juste vérifié le temps.

## 4. Ce que je ferais autrement (Leçons apprises)

Avec le recul, voici comment j'ajusterais ma pratique du Test-First :

1.  **Être plus pragmatique sur le Coverage :** J'arrêterais de tester les mécanismes internes du langage ou les situations impossibles (comme mocker des bibliothèques standards stables) juste pour le coverage.
2.  **Tester les limites métier avant le code :** J'aurais dû écrire un test avec un polygone concave *dès le début*. Cela m'aurait forcé à voir immédiatement que mon algorithme simpliste ne suffisait pas, au lieu de m'en rendre compte à la fin.
3.  **Tests de charge réels :** Les tests unitaires de performance sont insuffisants. J'aurais dû intégrer des tests de charge (type JMeter) dans ma boucle de feedback pour valider la tenue en charge du serveur Flask, et pas seulement de la fonction de calcul.

## Conclusion
Ce projet m'a prouvé que le **Test-First** est un excellent outil d'architecture logicielle : il force à écrire du code modulaire et robuste. Cependant, il ne remplace pas l'analyse métier : avoir des tests verts sur un mauvais algorithme ne rend pas l'algorithme bon. C'est la leçon principale que je retiens.