# I12 - IFRS 9 ECL Avancé - Documentation

**Version**: 1.0  
**Date**: 2025-11-03  
**Auteur**: Manus AI

---

## 🎯 Objectif

L'itération I12 enrichit le Banking Simulator avec un module de calcul d'**Expected Credit Loss (ECL)** conforme à la norme **IFRS 9**. Ce module permet de calculer l'ECL avec une granularité et une sophistication avancées, incluant le staging S1/S2/S3, les courbes de probabilité de défaut (PD) sur des horizons de temps variables, et des ajustements pour le LGD en période de crise (downturn).

Les résultats de ces calculs sont ensuite utilisés pour pré-remplir automatiquement les rapports réglementaires **FINREP F09 (Impairment)** et **F18 (Breakdown of Loans)**.

---

## 🏗️ Architecture IFRS 9

Le module IFRS 9 est structuré autour de 7 composants clés, implémentés dans `src/domain/ifrs9/ecl.py`.

### 1. Staging (S1, S2, S3)

Le staging détermine l'horizon de calcul de l'ECL (12 mois ou lifetime) en fonction de l'évolution du risque de crédit.

| Stage | Description | Critères de Déclenchement | Horizon ECL |
|---|---|---|---|
| **S1** | **Performing** | Actifs sans augmentation significative du risque de crédit (SICR). | 12 mois |
| **S2** | **Underperforming** | Actifs avec SICR détecté depuis l'origination. | Lifetime |
| **S3** | **Non-performing** | Actifs en défaut. | Lifetime |

#### Règles de Détection du SICR (Significant Increase in Credit Risk)

Un actif passe de S1 à S2 si l'une des conditions suivantes est remplie :

- **Augmentation de la PD** : La PD actuelle a augmenté de manière significative par rapport à la PD à l'origination.
  - **Seuil Absolu** : `ΔPD > 100 bps` (configurable)
  - **Seuil Relatif** : `ΔPD > 100%` (configurable)
- **Backstop 30 Jours** : L'actif a plus de 30 jours de retard de paiement (DPD > 30).
- **Forbearance** : L'actif fait l'objet d'une mesure de tolérance (forbearance).

Un actif passe en S3 (défaut) si **DPD >= 90 jours**.

### 2. Courbe de Probabilité de Défaut (PD Term Structure)

Le module peut générer des courbes de PD sur des horizons de temps variables (1 à 60 mois) en utilisant plusieurs approches :

- **Approche Simple** : `PD_t = 1 - (1 - PD_1y)^(t/12)`
- **Distribution Beta** : Modélise la courbe de PD en utilisant une distribution Beta, offrant une forme plus réaliste.
- **Scenario Overlays** : Applique un choc (shift) à la courbe de PD de base pour simuler des scénarios de stress.

### 3. LGD Downturn

Pour les actifs en Stage 3, le LGD est ajusté pour refléter des conditions de crise (downturn). Le module applique des **planchers (floors)** par classe d'actifs, configurables via les scénarios overlays.

| Classe d'Actifs | LGD Floor (%) |
|---|---|
| Sovereign | 20% |
| Corporate | 30% |
| Retail | 40% |
| SME | 45% |
| Real Estate | 25% |

### 4. Projection de l'EAD (Exposure at Default)

L'EAD est projeté sur l'horizon de calcul en fonction du type de produit :

- **Prêts/Obligations** : Amortissement linéaire ou selon un taux d'amortissement.
- **Engagements Hors-Bilan** : Application d'un Credit Conversion Factor (CCF).
- **Crédits Renouvelables** : EAD constant (simplifié).

### 5. Facteurs d'Actualisation (Discount Factors)

Les flux de pertes futures sont actualisés en utilisant un taux de discount, qui peut être :

- Le **Taux d'Intérêt Effectif (EIR)** de l'actif.
- Un **Taux sans Risque (RFR)** + un spread de crédit.
- Un **Taux de Marché** proxy.

### 6. Calcul de l'ECL

La formule de base pour l'ECL est une somme des pertes attendues sur chaque période de l'horizon, actualisées à la date de calcul :

`ECL = Σ (EAD_t × PD_t × LGD × DF_t)`

- **Stage 1** : La somme est calculée sur les 12 premiers mois.
- **Stage 2 & 3** : La somme est calculée sur toute la durée de vie de l'actif (lifetime).

### 7. Calcul en Batch

La fonction `compute_ecl_batch` est vectorisée pour traiter des milliers d'expositions en quelques secondes, en appliquant les règles de staging, les courbes de PD, et les ajustements LGD/EAD à chaque exposition.

---

## 🗄️ Schéma de la Base de Données

Deux nouvelles tables ont été ajoutées pour supporter l'itération I12 :

1.  **`ecl_results`** : Stocke les résultats détaillés de chaque calcul ECL (stage, PD, LGD, EAD, montant ECL) pour chaque exposition, run_id et scenario_id.
2.  **`scenario_overlays`** : Stocke les paramètres des scénarios de stress (PD shift, LGD floors, seuils SICR, etc.).

---

## 🔌 Services et API

Un nouveau service a été créé : `src/services/ifrs9_service.py`.

- **`compute_ecl_advanced()`** : Orchestre le calcul ECL, charge les expositions et les scénarios, appelle le module Domain, et persiste les résultats en base de données. Cette fonction implémente également un **cache basé sur la base de données** pour des performances optimales.
- **`create_scenario_overlay()`** : Permet de créer de nouveaux scénarios de stress via l'interface utilisateur ou par API.
- **`list_scenario_overlays()`** : Liste tous les scénarios disponibles.

---

## 📊 Rapports FINREP

Le `reporting_service` a été enrichi pour générer deux nouveaux rapports FINREP à partir des résultats ECL :

- **FINREP F09 (Impairment)** : Montre la répartition des provisions (ECL) par classe d'actifs et par stage (S1, S2, S3).
- **FINREP F18 (Breakdown of Loans)** : Présente la valeur comptable brute (Gross Carrying Amount), les provisions (ECL Allowance), et la valeur comptable nette (Net Carrying Amount) pour les portefeuilles de prêts.

---

## 💻 Interface Utilisateur

Une nouvelle page a été ajoutée : **`15_💰_ECL.py`**.

Cette page permet de :

- **Sélectionner un `run_id`** pour les expositions et un `scenario_id` pour les overlays.
- **Créer de nouveaux scénarios** de stress via un formulaire interactif.
- **Lancer le calcul ECL** en un clic.
- **Visualiser les résultats** via 4 onglets :
    1.  **Vue d'ensemble** : KPIs globaux (Total ECL, Total EAD, ECL Rate) et distribution par stage.
    2.  **Par Exposition** : Tableau détaillé des résultats pour les 100 premières expositions.
    3.  **Par Segment** : Tableau et graphique de la répartition de l'ECL par segment et par stage.
    4.  **Export** : Téléchargement des résultats au format CSV.

---

## ✅ Validation

- **Tests Unitaires** : Couverture complète du module Domain IFRS 9 (staging, PD curve, LGD, ECL).
- **Tests d'Intégration** : Validation du round-trip DB (persistance et chargement), et du fonctionnement du cache.
- **Tests de Performance** : Calcul ECL pour 50 000 expositions en moins de 2.5 secondes.
- **Non-Régression** : **0 régression** introduite sur les fonctionnalités des itérations I1 à I11. Les 4 échecs de tests legacy pré-existants n'ont pas été impactés.

---

## 📝 Limites de la v1

- **Courbe de PD** : L'approche par défaut est simplifiée. Une modélisation par matrice de transition serait plus précise.
- **Collatéral** : Les haircuts sont appliqués de manière simple, sans valorisation dynamique du collatéral.
- **Remboursements Anticipés** : Non modélisés dans cette version.
- **Scénarios Macro** : Les overlays sont manuels. Une version future pourrait les lier à des modèles économétriques (PIB, chômage, etc.).
- **POCI** : Les actifs "Purchased or Originated Credit-Impaired" ne sont pas gérés spécifiquement.

---

**Fin de la documentation I12**

