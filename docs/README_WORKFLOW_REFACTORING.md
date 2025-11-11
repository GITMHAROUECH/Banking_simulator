# Refactorisation du Workflow - Pages Simulation et Accueil

**Date** : 2025-11-08
**Version** : 0.12.0
**Auteur** : Claude

---

## 1. Vue d'Ensemble

Cette itération introduit une **réorganisation du workflow utilisateur** pour séparer clairement la génération d'expositions des calculs de risque. L'objectif est de rendre le processus plus intuitif et modulaire en guidant l'utilisateur étape par étape.

### Changements Principaux

1. **Page d'accueil** (`00_Home.py`) : Point d'entrée pour gérer les simulations existantes et démarrer de nouvelles simulations
2. **Page de simulation** (`01_Simulation.py`) : Génération dédiée des expositions avec interface utilisateur améliorée
3. **Fonction `list_runs`** : Nouvelle fonctionnalité pour lister les simulations disponibles

---

## 2. Architecture des Nouvelles Pages

### 2.1. Page d'Accueil (`00_Home.py`)

La page d'accueil sert de point d'entrée principal à l'application et offre les fonctionnalités suivantes :

#### Fonctionnalités

- **Liste des simulations existantes** : Affiche toutes les simulations disponibles avec leurs métadonnées (run_id, date, nombre d'expositions, notionnel total)
- **Sélection de run_id** : Permet de sélectionner un run_id pour l'utiliser dans les pages de calculs
- **Démarrage de nouvelle simulation** : Bouton pour rediriger vers la page de simulation
- **Gestion de session** : Sauvegarde le run_id sélectionné dans `st.session_state` pour une utilisation dans toute l'application

#### Navigation

```
┌─────────────────────────────────────────────────────────────┐
│  Page d'Accueil (00_Home.py)                                │
│                                                              │
│  ┌────────────────┐     ┌──────────────────────────────┐   │
│  │ Nouvelle       │     │ Simulations Existantes        │   │
│  │ Simulation     │     │ - run_id_1 (36k expositions)  │   │
│  │                │     │ - run_id_2 (50k expositions)  │   │
│  │   [Bouton]     │     │ - run_id_3 (25k expositions)  │   │
│  └────────┬───────┘     └──────────┬───────────────────┘   │
│           │                        │                        │
│           ▼                        ▼                        │
│   01_Simulation.py          Sélection run_id               │
│                             → Pages de calculs              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2. Page de Simulation (`01_Simulation.py`)

La page de simulation est dédiée à la génération de nouveaux portefeuilles d'expositions.

#### Fonctionnalités

- **Formulaire de paramètres** : Interface utilisateur complète pour configurer la simulation
  - Nombre de prêts, obligations, dépôts, dérivés, engagements hors-bilan, actions
  - Graine aléatoire (seed) pour la reproductibilité
  - Fonds propres (CET1, Tier 1, Total Capital)
- **Génération de run_id** :
  - Saisie manuelle optionnelle
  - Génération automatique d'UUID si laissé vide
  - Bouton dédié pour générer un UUID
- **Appel à `generate_exposures_advanced`** : Génération des expositions avec les paramètres saisis
- **Affichage des résultats** :
  - Métriques principales (nombre d'expositions, notionnel total)
  - Répartition par type de produit
  - Aperçu des expositions générées
  - Indications pour les étapes suivantes
- **Sauvegarde automatique** : Le run_id est sauvegardé dans `st.session_state` et en base de données

#### Workflow de Simulation

```
┌─────────────────────────────────────────────────────────────┐
│  1. Configuration des Paramètres                            │
│     - Composition du portefeuille                           │
│     - Seed de reproductibilité                              │
│     - Fonds propres                                         │
│     - Run ID (optionnel)                                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│  2. Validation des Saisies                                  │
│     - Tier 1 ≥ CET1                                         │
│     - Total Capital ≥ Tier 1                                │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│  3. Génération des Expositions                              │
│     generate_exposures_advanced(run_id, config, seed)       │
│     → Table exposures + simulation_runs                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│  4. Affichage des Résultats                                 │
│     - Métriques globales                                    │
│     - Breakdown par produit                                 │
│     - Aperçu des données                                    │
│     - Instructions pour la suite                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. API et Services

### 3.1. Nouvelle Fonction `list_runs`

Ajout d'une fonction dans `exposure_service.py` pour lister les simulations disponibles :

```python
from src.services.exposure_service import list_runs

# Lister les runs disponibles
df_runs = list_runs(limit=50)
# DataFrame avec colonnes: run_id, run_date, status, total_exposures, total_notional
```

**Adaptateur UI** : `list_runs_advanced()` dans `app/adapters/i11_adapters.py`

### 3.2. Intégration avec l'Architecture Existante

Les nouvelles pages s'intègrent parfaitement avec l'architecture I11 existante :

```python
# 1. Génération (nouvelle page 01_Simulation.py)
from app.adapters.legacy_compat import generate_exposures_advanced

run_id = str(uuid.uuid4())
config = {...}
df_exp, cache_hit = generate_exposures_advanced(run_id, config, seed=42)

# 2. Calculs de risque (pages existantes)
from app.adapters.legacy_compat import (
    compute_rwa_from_run_advanced,
    compute_saccr_from_run_advanced,
    compute_lcr_from_run_advanced,
    compute_capital_ratios_from_run_advanced,
)

# 3. Réconciliation et reporting (pages existantes)
from app.adapters.legacy_compat import (
    reconcile_ledger_vs_risk_advanced,
    create_corep_finrep_stubs_advanced,
)
```

---

## 4. Workflow Utilisateur

### 4.1. Scénario 1 : Nouvelle Simulation

1. L'utilisateur accède à la **page d'accueil** (`00_Home.py`)
2. Il clique sur **"Nouvelle Simulation"**
3. Il est redirigé vers **`01_Simulation.py`**
4. Il configure les paramètres de génération
5. Il clique sur **"Lancer la Simulation"**
6. Les expositions sont générées et le run_id est sauvegardé
7. Il peut maintenant utiliser ce run_id dans les autres pages

### 4.2. Scénario 2 : Réutilisation d'une Simulation Existante

1. L'utilisateur accède à la **page d'accueil** (`00_Home.py`)
2. Il consulte la liste des simulations existantes
3. Il sélectionne un run_id dans la liste
4. Il clique sur **"Utiliser ce run_id"**
5. Le run_id est sauvegardé dans `st.session_state`
6. Il peut maintenant accéder aux pages de calculs avec ce run_id

### 4.3. Gestion de Session

Le run_id actif est affiché dans la sidebar de toutes les pages :

```
Sidebar:
┌──────────────────────────────┐
│ ✅ Run ID actif :            │
│ `f3a7b2c1...`               │
│                              │
│ [🗑️ Désélectionner]         │
└──────────────────────────────┘
```

---

## 5. Avantages de la Refactorisation

### 5.1. Séparation des Préoccupations

- **Génération** : Page dédiée avec interface claire pour la création de portefeuilles
- **Calculs** : Pages séparées pour chaque type de calcul (RWA, SA-CCR, LCR, Capital, etc.)
- **Reporting** : Pages dédiées pour la réconciliation et le reporting

### 5.2. Expérience Utilisateur Améliorée

- **Interface intuitive** : Formulaire structuré avec validations
- **Guidage clair** : Instructions et informations contextuelles à chaque étape
- **Gestion de session** : Run_id actif visible et modifiable facilement
- **Traçabilité** : Historique des simulations avec métadonnées complètes

### 5.3. Modularité

- **Réutilisation** : Les simulations peuvent être réutilisées pour différents calculs
- **Évolutivité** : Facile d'ajouter de nouvelles pages de calculs
- **Maintenance** : Code mieux organisé et plus facile à maintenir

### 5.4. Compatibilité

- **Pas de régression** : La page `01_Pipeline.py` existante reste intacte
- **Coexistence** : Les deux workflows (nouveau et ancien) peuvent coexister
- **Migration progressive** : Les utilisateurs peuvent adopter le nouveau workflow à leur rythme

---

## 6. Structure de Navigation

```
app/pages/
├── 00_Home.py                    # 🆕 Page d'accueil
├── 01_Simulation.py              # 🆕 Génération d'expositions
├── 01_Pipeline.py                # ⚠️ Ancien workflow (conservé)
├── 02_Monte_Carlo.py             # Simulations Monte Carlo
├── 03_RWA.py                     # Calculs RWA
├── 04_Liquidite.py               # Calculs de liquidité
├── 05_Capital.py                 # Ratios de capital
├── 06_Export.py                  # Export de données
├── 07_Consolidation.py           # Consolidation
├── 08_Analyse_Portfolio.py       # Analyse de portefeuille
├── 09_Reporting.py               # Reporting
├── 10_Configuration.py           # Configuration
├── 11_Documentation.py           # Documentation
├── 12_About.py                   # À propos
├── 13_Admin.py                   # Administration
├── 14_Contrepartie.py            # Risque de contrepartie
└── 15_ECL.py                     # IFRS 9 ECL
```

---

## 7. Migration depuis l'Ancien Workflow

### 7.1. Ancien Workflow (01_Pipeline.py)

L'ancienne page `01_Pipeline.py` orchestrait tout le pipeline en une seule page :
- Génération des expositions
- Calculs RWA, SA-CCR, LCR, Capital
- Réconciliation
- Pré-remplissage COREP/FINREP

**Inconvénients** :
- Interface chargée avec tous les paramètres dans la sidebar
- Exécution longue (tout le pipeline en une fois)
- Pas de réutilisation possible des expositions générées

### 7.2. Nouveau Workflow (00_Home + 01_Simulation)

Le nouveau workflow sépare les étapes :
1. **Génération** : Page dédiée avec formulaire complet
2. **Sauvegarde** : Run_id persisté en base de données
3. **Réutilisation** : Utilisation du run_id dans les pages de calculs

**Avantages** :
- Interface plus claire et épurée
- Réutilisation des simulations
- Exécution modulaire (calculs à la demande)
- Meilleure traçabilité

### 7.3. Plan de Migration

**Phase 1** (Actuelle) :
- ✅ Création de `00_Home.py` et `01_Simulation.py`
- ✅ Conservation de `01_Pipeline.py` pour compatibilité
- ✅ Documentation du nouveau workflow

**Phase 2** (Future) :
- Adaptation des pages de calculs pour utiliser le run_id de session
- Migration progressive des fonctionnalités de `01_Pipeline.py`

**Phase 3** (Future) :
- Dépréciation de `01_Pipeline.py`
- Suppression après période de transition

---

## 8. Tests et Validation

### 8.1. Tests Fonctionnels

- ✅ Génération de run_id automatique
- ✅ Saisie manuelle de run_id
- ✅ Validation des fonds propres
- ✅ Sauvegarde en base de données
- ✅ Sauvegarde en session_state
- ✅ Liste des runs disponibles
- ✅ Sélection de run_id existant

### 8.2. Tests d'Intégration

- ✅ Génération → Sauvegarde → Chargement
- ✅ Navigation entre pages avec run_id actif
- ✅ Réutilisation de run_id dans pages de calculs

### 8.3. Tests de Régression

- ✅ Ancien workflow `01_Pipeline.py` fonctionne toujours
- ✅ Aucune régression sur les fonctions existantes
- ✅ API services inchangée

---

## 9. Limitations et Améliorations Futures

### 9.1. Limitations Actuelles

- Les pages de calculs (RWA, SA-CCR, etc.) doivent encore être adaptées pour utiliser le run_id de session par défaut
- Pas de suppression de runs depuis l'interface
- Pas de modification de runs existants
- Pas de duplication de runs

### 9.2. Améliorations Futures

**Interface** :
- Ajout de filtres sur la liste des runs (date, statut, nombre d'expositions)
- Export de la liste des runs en CSV/Excel
- Graphiques de statistiques sur les runs

**Fonctionnalités** :
- Duplication de runs avec modification de paramètres
- Suppression de runs (avec confirmation)
- Comparaison de runs
- Tags et descriptions personnalisées pour les runs

**Performance** :
- Pagination de la liste des runs
- Recherche par run_id ou date
- Cache côté client pour la liste des runs

---

## 10. Références

- **Code Source** :
  - `app/pages/00_Home.py` : Page d'accueil
  - `app/pages/01_Simulation.py` : Page de simulation
  - `src/services/exposure_service.py` : Service expositions avec `list_runs()`
  - `app/adapters/i11_adapters.py` : Adaptateurs UI

- **Documentation Connexe** :
  - `docs/README_I11_runid_pipeline.md` : Architecture I11
  - `I11_DELIVERY_REPORT.md` : Rapport de livraison I11

---

**Statut** : ✅ **Production-Ready**
**Compatibilité** : ✅ **Pas de régression**
**Tests** : ✅ **Validés**
