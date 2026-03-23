# 📦 Code VRPTW_GA_2017

## 📌 Informations Générales

-   **Référence** : CVRPTW-AG\
-   **Année** : 2017\
-   **Langage** : Python\
-   **Point d'entrée** :

``` bash
python evolver.py
```

------------------------------------------------------------------------

## 📂 Benchmark

-   **Jeu de données** : Solomon (C, R et RC)\
-   **Format des fichiers** :

```{=html}
<!-- -->
```
    ProblemType_VehicleCapacity.csv

-   **Dossier des données** : `data/`

------------------------------------------------------------------------

## 🎯 Fonction Objectif

Définie dans : `chromosome.py → get_cost_score`

### Formulation mathématique

min Z = C_distance + C_vehicules_temps

= total_travel_cost + total_vehicles_and_deport_working_hours_cost

### Détails des composantes

-   **Coût distance** :

C_distance = vehicle_cost_per_dist × distance_totale

avec :

vehicle_cost_per_dist = 1.0

------------------------------------------------------------------------

-   **Coût véhicules et temps** :

C_vehicules_temps = α . V + H

avec :

-   α = 1.0\
-   V = nombre de véhicules\
-   H = temps total de fonctionnement du dépôt

Formule complète :

Z = 1.0 × distance_totale + 1000 × nb_vehicules + temps_max_depot

------------------------------------------------------------------------

## 🏆 Objectif d'optimisation

On cherche à :

1.  **Minimiser le nombre de véhicules (priorité très forte)**
2.  Minimiser la distance totale
3.  Minimiser le temps total d'exploitation

Le coefficient 1000 impose une priorité hiérarchique : - D'abord réduire
le nombre de véhicules\
- Ensuite réduire la distance

------------------------------------------------------------------------

## ⏳ Type de Time Window

**Hard Time Window**

-   Arriver avant `ready_time` → Autorisé (le véhicule attend)
-   Arriver après `due_time` → Interdit (nécessite un nouveau véhicule)

------------------------------------------------------------------------

## 🧬 Algorithme

Algorithme Génétique (AG)

-   **Croisement** : (à préciser)
-   **Mutation** : (à préciser)
-   **Sélection** : (à préciser)

------------------------------------------------------------------------

## 📊 Paramètres d'Exécution

-   MAX_GEN = 10 000
-   Pop_size = 10
-   Instance testée : R101_200.csv
