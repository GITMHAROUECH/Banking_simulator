# I13 : Run Management Advanced

**Date** : 2025-11-05  
**Itération** : I13  
**Objectif** : Améliorer le système Run-ID avec une interface de gestion complète

## Vue d'ensemble

L'itération I11 a introduit l'architecture run-based qui permet de générer des expositions une seule fois et de les réutiliser dans toutes les pages. L'itération I13 améliore ce système avec une interface de gestion avancée des runs.

## Objectifs I13

### Fonctionnalités principales

1. **Interface de gestion des runs**
   - Liste paginée de tous les runs avec filtres
   - Détails complets d'un run (métadonnées, statistiques, logs)
   - Suppression de runs (avec confirmation)
   - Marquage de runs favoris

2. **Comparaison de runs**
   - Sélection de 2-4 runs pour comparaison
   - Tableaux comparatifs des métriques clés
   - Graphiques de différences (RWA, Capital, ECL, LCR)
   - Export des comparaisons

3. **Clonage et variantes**
   - Cloner un run existant avec modifications
   - Créer des variantes de scénarios
   - Historique de clonage

4. **Export/Import de runs**
   - Export complet d'un run (exposures + métriques + config)
   - Import de runs depuis fichiers
   - Formats : JSON, Parquet, ZIP

5. **Nettoyage automatique**
   - Suppression automatique des runs anciens
   - Archivage des runs inactifs
   - Gestion de l'espace disque

6. **Validation et checksums**
   - Validation de l'intégrité des données
   - Checksums SHA256 pour chaque run
   - Détection de corruptions

7. **CLI améliorée**
   - Commandes pour gérer les runs
   - Scripts d'automatisation
   - Batch processing

## Architecture

### Nouvelles tables DB

```sql
-- Métadonnées enrichies pour runs
ALTER TABLE simulation_runs ADD COLUMN status VARCHAR(20);
ALTER TABLE simulation_runs ADD COLUMN duration_seconds FLOAT;
ALTER TABLE simulation_runs ADD COLUMN checksum VARCHAR(64);
ALTER TABLE simulation_runs ADD COLUMN is_favorite BOOLEAN DEFAULT FALSE;
ALTER TABLE simulation_runs ADD COLUMN tags TEXT;
ALTER TABLE simulation_runs ADD COLUMN parent_run_id VARCHAR(50);

-- Logs d'exécution
CREATE TABLE run_logs (
    id VARCHAR(36) PRIMARY KEY,
    run_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    level VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES simulation_runs(id)
);

-- Comparaisons sauvegardées
CREATE TABLE run_comparisons (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    run_ids TEXT NOT NULL,  -- JSON array
    created_at TIMESTAMP NOT NULL,
    notes TEXT
);
```

### Nouveaux services

```python
# src/services/run_management_service.py
- list_runs(filters, pagination)
- get_run_details(run_id)
- delete_run(run_id)
- clone_run(run_id, modifications)
- export_run(run_id, format)
- import_run(file_path)
- compare_runs(run_ids)
- validate_run(run_id)
- cleanup_old_runs(days_threshold)
```

### Nouvelle page UI

```
app/pages/16_🔧_Run_Management.py
```

Avec 6 onglets :
1. **Liste des Runs** : Table paginée avec filtres
2. **Détails** : Vue détaillée d'un run sélectionné
3. **Comparaison** : Interface de comparaison multi-runs
4. **Clonage** : Créer des variantes
5. **Export/Import** : Gérer les fichiers
6. **Maintenance** : Nettoyage et validation

## Spécifications détaillées

### 1. Liste des Runs

**Colonnes affichées** :
- Run ID
- Date de création
- Nombre d'expositions
- Statut (✅ Complet, ⏳ En cours, ❌ Erreur)
- Durée d'exécution
- Favoris (⭐)
- Actions (👁️ Détails, 📋 Cloner, 🗑️ Supprimer)

**Filtres** :
- Par date (plage)
- Par statut
- Par nombre d'expositions (min/max)
- Par tags
- Favoris uniquement

**Pagination** : 20 runs par page

### 2. Détails d'un Run

**Sections** :
- **Métadonnées** : ID, date, durée, statut, checksum
- **Configuration** : Paramètres de génération
- **Statistiques** : Nombre d'expositions par produit, par entité
- **Métriques** : RWA, Capital ratios, ECL, LCR, NSFR
- **Logs** : Historique d'exécution (si disponible)
- **Graphiques** : Distribution des expositions, répartition par classe

### 3. Comparaison de Runs

**Interface** :
- Sélection de 2-4 runs via multiselect
- Tableau comparatif des métriques principales
- Graphiques en barres pour visualiser les différences
- Calcul des variations en % et en valeur absolue
- Export de la comparaison en Excel

**Métriques comparées** :
- Nombre d'expositions
- EAD total
- RWA total
- Ratios de capital (CET1, Tier 1, Total)
- ECL total
- LCR, NSFR

### 4. Clonage de Runs

**Workflow** :
1. Sélectionner un run source
2. Modifier les paramètres :
   - Nombre d'expositions
   - Seed aléatoire
   - Date de reporting
   - Inclusion de produits
3. Générer le nouveau run
4. Lien parent-enfant conservé

### 5. Export/Import

**Export** :
- Format JSON : Métadonnées + exposures + métriques
- Format Parquet : Exposures uniquement (optimisé)
- Format ZIP : Tout inclus avec documentation

**Import** :
- Upload de fichier
- Validation du format
- Création du run importé
- Vérification de l'intégrité

### 6. Maintenance

**Nettoyage** :
- Supprimer les runs > X jours
- Archiver les runs non favoris
- Libérer l'espace disque

**Validation** :
- Vérifier les checksums
- Détecter les corruptions
- Réparer si possible

## CLI

```bash
# Lister les runs
python -m app.cli runs list --status complete --limit 10

# Détails d'un run
python -m app.cli runs show run_20251103_001

# Supprimer un run
python -m app.cli runs delete run_20251103_001 --confirm

# Cloner un run
python -m app.cli runs clone run_20251103_001 --seed 123 --name "run_variant_1"

# Exporter un run
python -m app.cli runs export run_20251103_001 --format json --output run.json

# Importer un run
python -m app.cli runs import run.json

# Comparer des runs
python -m app.cli runs compare run_20251103_001 run_20251103_002 --output comparison.xlsx

# Nettoyer les anciens runs
python -m app.cli runs cleanup --days 30 --dry-run
```

## Tests

### Tests unitaires

```python
# tests/unit/test_run_management.py
- test_list_runs_with_filters()
- test_get_run_details()
- test_delete_run()
- test_clone_run()
- test_export_run_json()
- test_import_run_json()
- test_compare_runs()
- test_validate_run()
- test_cleanup_old_runs()
```

### Tests d'intégration

```python
# tests/integration/test_run_management_e2e.py
- test_create_compare_delete_workflow()
- test_clone_and_validate_workflow()
- test_export_import_workflow()
```

## Livrables I13

1. **Code** :
   - `src/services/run_management_service.py`
   - `app/pages/16_🔧_Run_Management.py`
   - `app/cli.py` (nouveau)
   - Migration Alembic

2. **Tests** :
   - 15+ tests unitaires
   - 3 tests d'intégration

3. **Documentation** :
   - `docs/I13_DESIGN.md` (ce fichier)
   - `docs/README_I13_run_management.md`
   - Mise à jour du CHANGELOG.md

4. **Déploiement** :
   - Application déployée avec lien de test

## Métriques de succès

- ✅ Page Run Management accessible et fonctionnelle
- ✅ Comparaison de 2+ runs avec graphiques
- ✅ Export/Import d'un run complet
- ✅ CLI opérationnelle avec 8+ commandes
- ✅ 18+ tests passing
- ✅ 0 régression sur I1-I12
- ✅ Application déployée et testable

## Prochaines étapes (I14)

- ALM avancé (gaps de repricing, sensibilité NII/EVE)
- Stress testing multi-scénarios
- Backtesting des modèles de risque

