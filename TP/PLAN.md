
## Introduction

Ce document décrit la mise en place d'un plan de tests, il décrira les différents tests mit en place et pourquoi/comment ça sera fait. 

### Organisation des tests 

#### Tests de comportement  
- La triangulation donne de bons résultats 
- Bon fonctionnement de PointSetMananger
- Gestion des différentes situations (autre que "happy path") 

L'ensemble du code doit être couvert par des tests, on pourra le vérifier avec l'outil `coverage`.

#### Tests de performances
- Choisir de les exécutés ou non
- Retourne des métriques
- Permet d'identifié les goulots d'étranglement (dans le cas d'opérations gourmandes)

### Tests principaux

#### Validation du format binaire

Ce qui sera testé : 
- La conversion des structures de données vers le format binaire
- La conversion du format binaire vers les structures de données 
- La conservation des données après conversion 
- La gestion des cas limites (données vide, très grandes, très petites)

**Approche** : on vérifie que les données transformés respectent le format byte par byte. Des tests seront effectués avec des valeurs connus afin de vérifie la conformité de la conversion. Des tests de "roundtrip" seront effectués pour valider le bon fonctionnement dans les deux sens.
`
#### Validation de l'algorithme de triangulation 

Ce qui sera testé : 
- Les cas simples avec des résultats connus (triangle, carré, pentagone)
- Les propriétés mathématiques
- Les cas spéciaux (points alignés, points identiques, points insuffisants)
- La cohérence des résultats (pas de triangles qui se chevauchent, tous les points utilisés)

**Approche** : Pour les cas simple, il suffit d'une comparaison avec des résultats connus et calculer manuellement. Pour des cas plus complexes, on vérifiera les propriétés mathématiques. On fera des tests avec des cas spéciaux pour vérifier que l'algorithme ne crash pas.

#### Validation de la communication avec PointSetManager

Ce qui sera testé : 
- Les requêtes réussies 
- Les différents type d'erreur (ressource inexistante, serveur down, timeout)
- Les réponses malformées ou inattendues
- La gestion des cas d'erreur réseau

**Approche** : On simulera le comportement du PointSetManager en mockant les réponses HTTP. Cela permettra de tester tous les scénarios d'erreur de manière contrôlée et reproductible.

#### Validation de l'API 

**Comportement nominal :**

- Requête de triangulation avec un ID valide
- Réception d'une réponse au format binaire correct (Triangles)
- Codes HTTP appropriés (200 pour succès)
- Headers de réponse corrects (Content-Type binaire)

**Gestion des erreurs :**

- Requête avec un ID invalide ou mal formé → 400 Bad Request
- Requête avec un ID de PointSet inexistant → 404 Not Found
- Erreur lors de la récupération du PointSet auprès du PointSetManager → 502 Bad Gateway
- Erreur interne lors de la triangulation → 500 Internal Server Error

**Cas limites :**

- PointSet vide ou avec trop peu de points
- PointSet très volumineux
- Requêtes avec méthodes HTTP non supportées (POST, PUT, DELETE sur un endpoint GET)
- Requêtes malformées ou incomplètes

**Approche :** On utilisera le client de test Flask pour interroger l'API sans démarrer un vrai serveur. On mockera la communication avec le PointSetManager pour contrôler les différents scénarios. On vérifiera systématiquement :

- Les codes de statut HTTP retournés
- Les headers de réponse (notamment Content-Type)
- La structure et le contenu des réponses binaires
- Les messages d'erreur éventuels

### Tests de performances

#### Obectifs
Identifier les limites du système et s'assurer que les performances sont acceptables pour différentes tailles de données.

**Sérialisation/Désérialisation :**

- Mesurer le temps nécessaire pour différentes tailles d'ensembles de points (10, 100, 1000, 10000, 100000 points)
- Observer comment le temps évolue avec la taille (linéaire, quadratique ?)

**Triangulation :**

- Mesurer le temps de calcul pour différentes tailles
- Identifier la configuration la plus défavorable
- Estimer la taille maximale gérable en un temps raisonnable

**API complète :**

- Mesurer le temps de réponse total (incluant toutes les opérations)
- Évaluer le débit (requêtes par seconde)
- Tester la latence avec différentes tailles de PointSet

###  Métriques collectées

- Temps d'exécution (moyenne, médiane, percentiles)
- Consommation mémoire
- Observation de la complexité algorithmique

## Stratégie pour les Cas Limites et Erreurs

###  Données invalides ou limites

- Ensembles vides
- Nombre insuffisant de points pour trianguler
- Points en double ou colinéaires
- Valeurs numériques extrêmes (très grandes, très petites, négatives)
- Données binaires corrompues ou incomplètes

###  Erreurs de communication

- Service externe indisponible
- Timeout réseau
- Réponses malformées
- Identifiants invalides

###  Principe général

Le système ne doit jamais crasher. Toute erreur doit être gérée proprement avec un message approprié et un code d'erreur HTTP correct pour le Client.

##  Qualité et Documentation du Code

###  Couverture de code

**Approche** :

- Mesurer la couverture régulièrement
- Identifier les branches non testées
- Ne pas ajouter de tests inutiles juste pour atteindre 100%

**Attention** : 100% de couverture ne garantit pas la qualité. Des tests bidon peuvent couvrir du code sans rien valider.

### Qualité du code 

**Vérifications** :

- Respect des conventions Python
- Documentation de toutes les fonctions et classes
- Nommage cohérent et explicite
- Pas de code mort ou inutilisé
- Complexité raisonnable

L'outil `ruff` sera utilisé pour vérifier automatiquement ces critères.


