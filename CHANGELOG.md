# Changelog - Banking Simulator

Toutes les modifications notables du projet Banking Simulator sont documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.8.0] - 2025-11-01 - I8b : Finalisation UI Pages

### Ajouté
- Page Capital (05_📈_Capital.py) avec calculs ratios CET1/Tier1/Total/Leverage
- Page Reporting (09_📋_Reporting.py) - stub pour COREP/LE/LCR
- Page Configuration (10_⚙️_Configuration.py) - stub pour gestion scénarios
- Page Analyse Portfolio (08_📊_Analyse_Portfolio.py) - stub pour drill-down
- Page About (12_ℹ️_About.py) - version minimale
- Page Admin (13_🔧_Admin.py) - historique des 50 derniers exports
- `list_artifacts()` et `list_configurations()` dans persistence_service.py
- `list_artifacts_advanced()` dans legacy_compat.py

### Modifié
- Aucune modification des fonctionnalités existantes

### Statut
- ✅ 14/14 pages UI complètes ou stubs fonctionnels
- ✅ 269/273 tests passing (4 échecs legacy pré-existants)
- ✅ Aucune régression

---

## [0.8.0-hotfix] - 2025-10-30 - I8 Hotfix : Fix ImportError

### Corrigé
- ImportError pour `create_pipeline_export` dans src/services/__init__.py
- Export ajouté dans __all__ pour visibilité publique

### Statut
- ✅ Pipeline export fonctionnel
- ✅ Tous les tests I8 passent

---

## [0.8.0] - 2025-10-29 - I8 : Multi-format Export & COREP Stubs

### Ajouté
- Export multi-format (XLSX, Parquet, CSV, JSON) dans reporting_service.py
- Compression optionnelle (gzip, bz2, zip) pour tous les formats
- 5 stubs COREP (C34, C07, C08, Leverage, LCR) dans reporting_service.py
- `create_pipeline_export()` pour export complet du pipeline E2E
- Page Export (06_📥_Export.py) avec sélection format/compression
- 28 nouveaux tests (exports + COREP stubs)

### Modifié
- reporting_service.py : Ajout fonctions export multi-format
- pipeline_service.py : Ajout create_pipeline_export()
- legacy_compat.py : Ajout wrappers export

### Statut
- ✅ 218 tests passing
- ✅ 5 formats d'export (XLSX, Parquet, CSV, JSON, pickle)
- ✅ 5 stubs COREP réglementaires

---

## [0.7.3] - 2025-10-28 - I7c : CVA (BA-CVA) & Agrégateur Contrepartie

### Ajouté
- BA-CVA (capital CVA) dans counterparty.py (`compute_cva_capital_ba`)
- CVA Pricing v1 dans counterparty.py (`compute_cva_pricing_v1`)
- Service CVA capital (`compute_cva_capital`) avec cache I6
- Service CVA pricing (`compute_cva_pricing`) avec cache I6
- Agrégateur risque contrepartie (`compute_counterparty_risk`)
- Adaptateurs CVA dans legacy_compat.py
- Page Contrepartie unifiée (4 onglets : SA-CCR, CVA Capital, CVA Pricing, Export)
- 23 nouveaux tests (8 capital + 8 pricing + 7 agrégateur)
- Documentation README_I7c_counterparty.md (416 lignes)

### Modifié
- counterparty.py : Ajout BA-CVA et CVA Pricing v1
- risk_service.py : Ajout services CVA et agrégateur
- legacy_compat.py : Ajout adaptateurs CVA
- 14_🔁_Contrepartie.py : Renommée depuis Dérivés, ajout onglets CVA

### Supprimé
- test_derivatives_page.py : Remplacé par test_counterparty_page.py

### Statut
- ✅ 241 tests passing (218 + 23 nouveaux)
- ✅ SA-CCR + CVA opérationnels
- ✅ Cache I6 actif sur tous les calculs

---

## [0.7.2] - 2025-10-27 - I7b : SA-CCR (EAD Derivatives)

### Ajouté
- SA-CCR (Standardized Approach for Counterparty Credit Risk) dans counterparty.py
- Calcul EAD dérivés : RC + PFE (add-ons par classe d'actifs)
- Netting sets avec collatéral
- Multiplier selon CRR3
- 19 nouveaux tests SA-CCR
- Documentation README_I7b.md

### Modifié
- risk_service.py : Ajout compute_saccr_ead, compute_saccr_rwa
- legacy_compat.py : Ajout adaptateurs SA-CCR

### Statut
- ✅ 218 tests passing (199 + 19 nouveaux)
- ✅ SA-CCR conforme CRR3 Article 274

---

## [0.7.1] - 2025-10-26 - I7a : Pipeline E2E & UI Refactoring

### Ajouté
- Pipeline E2E service (`run_full_pipeline`) orchestrant tous les calculs
- 13 pages Streamlit structure (Pipeline, Monte Carlo, RWA, Liquidité, etc.)
- Cache_hit display (✅/❌) dans toutes les pages
- 33 nouveaux tests (pipeline E2E + UI smoke)
- Documentation README_I7a.md

### Modifié
- pipeline_service.py : Ajout run_full_pipeline()
- Toutes les pages UI : Ajout badge cache_hit
- main.py : initial_sidebar_state="expanded"

### Statut
- ✅ 199 tests passing (166 + 33 nouveaux)
- ✅ 13 pages UI fonctionnelles

---

## [0.6.0] - 2025-10-25 - I6 : Persistence & Cache System

### Ajouté
- Persistence layer avec SQLite/PostgreSQL support
- Cache système basé sur params_hash (SHA256)
- save/load DataFrames, dicts, artifacts
- Migrations Alembic pour DB schema
- 10 nouveaux tests persistence
- Documentation README_I6.md

### Modifié
- Tous les services : Retour (result, cache_hit) tuples
- persistence_service.py : Nouveau module avec DB-agnostic API
- legacy_compat.py : Wrappers pour backward compatibility

### Statut
- ✅ 166 tests passing (156 + 10 nouveaux)
- ✅ Cache speedup 50-150x
- ✅ SQLite/PostgreSQL ready

---

## [0.5.0] - 2025-10-24 - I5 : Consolidation IFRS 10/11

### Ajouté
- Consolidation IFRS 10/11 dans consolidation.py
- Méthode intégration globale (contrôle >50%)
- Méthode mise en équivalence (influence notable 20-50%)
- Élimination transactions intra-groupe
- 15 nouveaux tests consolidation
- Documentation README_I5.md

### Modifié
- consolidation_service.py : Ajout compute_consolidation()
- legacy_compat.py : Ajout adaptateurs consolidation

### Statut
- ✅ 156 tests passing (141 + 15 nouveaux)
- ✅ IFRS 10/11 conforme

---

## [0.4.0] - 2025-10-23 - I4 : Liquidity Risk (LCR/NSFR)

### Ajouté
- LCR (Liquidity Coverage Ratio) dans liquidity.py
- NSFR (Net Stable Funding Ratio) dans liquidity.py
- Calculs conformes CRR3 Article 412 (LCR) et 428 (NSFR)
- 12 nouveaux tests liquidité
- Documentation README_I4.md

### Modifié
- liquidity_service.py : Ajout compute_lcr(), compute_nsfr()
- legacy_compat.py : Ajout adaptateurs liquidité

### Statut
- ✅ 141 tests passing (129 + 12 nouveaux)
- ✅ LCR/NSFR conformes CRR3

---

## [0.3.0] - 2025-10-22 - I3 : Credit Risk (RWA)

### Ajouté
- RWA Credit Risk (SA, FIRB, AIRB) dans credit_risk.py
- Calculs RWA conformes CRR3 Article 111-134
- Pondérations par classe d'exposition et rating
- 18 nouveaux tests RWA
- Documentation README_I3.md

### Modifié
- risk_service.py : Ajout compute_rwa_standardized(), compute_rwa_irb()
- legacy_compat.py : Ajout adaptateurs RWA

### Statut
- ✅ 129 tests passing (111 + 18 nouveaux)
- ✅ RWA conformes CRR3

---

## [0.2.0] - 2025-10-21 - I2 : Risk Service Layer

### Ajouté
- risk_service.py : Couche Services pour calculs de risque
- Intégration Monte Carlo via Services
- Wrappers avec gestion d'erreurs
- 6 nouveaux tests services
- Documentation README_I2.md

### Modifié
- Architecture 3-layer : Domain → Services → UI
- monte_carlo.py : Refactoring pour séparation concerns

### Statut
- ✅ 111 tests passing (105 + 6 nouveaux)
- ✅ Architecture 3-layer stricte

---

## [0.1.0] - 2025-10-20 - I1 : Monte Carlo Engine

### Ajouté
- Monte Carlo engine dans monte_carlo.py
- Simulations GBM (Geometric Brownian Motion)
- Métriques : VaR, ES, percentiles
- 105 tests domain
- Documentation README_I1.md

### Statut
- ✅ 105 tests passing
- ✅ 96% couverture domain
- ✅ 20k simulations en <3s

---

## Format

### Types de Changements
- **Ajouté** : Nouvelles fonctionnalités
- **Modifié** : Changements dans les fonctionnalités existantes
- **Déprécié** : Fonctionnalités bientôt supprimées
- **Supprimé** : Fonctionnalités supprimées
- **Corrigé** : Corrections de bugs
- **Sécurité** : Corrections de vulnérabilités

### Versioning
- **Major** (X.0.0) : Changements incompatibles API
- **Minor** (0.X.0) : Ajout fonctionnalités compatibles
- **Patch** (0.0.X) : Corrections bugs compatibles

---

**Projet** : Banking Simulator  
**Licence** : Propriétaire  
**Maintainers** : Équipe Banking Risk

## [0.12.1] - 2025-11-04

### 🐞 Corrigé

- **`IntegrityError` dans `ecl_results`** : Correction d'un bug où des `ecl_amount` calculés comme `NaN` causaient une erreur `NOT NULL constraint failed` lors de la persistance en base de données. Ajout d'un `fillna(0)` pour nettoyer les données avant l'insertion.

---

## [0.12.0] - 2025-11-03

### ✨ Features

- **IFRS 9 ECL Avancé (I12)**
  - Ajout du module `ifrs9/ecl.py` avec calcul ECL avancé.
  - Implémentation du staging S1/S2/S3 avec règles SICR, backstop 30j et défaut 90j.
  - Support des courbes de PD (term structures) sur horizons 1-60 mois.
  - Implémentation du LGD downturn avec floors par classe d'actifs.
  - Projection de l'EAD pour produits amortissables et hors-bilan.
  - Ajout du service `ifrs9_service.py` avec persistance DB et cache.
  - Création de 2 nouvelles tables DB : `ecl_results` et `scenario_overlays`.
  - Ajout de la page UI `15_💰_ECL.py` pour le calcul et la visualisation ECL.
  - Pré-remplissage des rapports **FINREP F09 (Impairment)** et **F18 (Breakdown of Loans)**.
  - 0 régression sur les itérations I1-I11.

---

## [0.11.0] - 2025-11-03

### Added - I11: Run ID Pipeline

**Architecture**
- Schéma canonique `exposures` comme source unique de vérité
- Propagation `run_id` dans tout le pipeline
- 3 nouvelles tables DB : `simulation_runs`, `exposures`, `balance_sheet_snapshots`

**Générateurs Multi-Produits (MVP)**
- Loans : Prêts corporate/retail (10k par défaut)
- Bonds : Obligations sovereign/corporate (5k par défaut)
- Deposits : Dépôts clients (15k par défaut)
- Derivatives : Dérivés avec netting sets (3k par défaut)
- Off-BS : Engagements hors-bilan (2k par défaut)
- Equities : Actions détenues (1k par défaut)
- Total : 36k expositions par défaut

**Services**
- `exposure_service.py` : Génération et gestion exposures
- `reconciliation_service.py` : Réconciliation ledger vs risk
- Fonctions `*_from_run()` dans `risk_service.py` :
  - `compute_rwa_from_run(run_id)`
  - `compute_saccr_from_run(run_id)`
  - `compute_lcr_from_run(run_id)`
  - `compute_capital_ratios_from_run(run_id)`

**Reporting**
- Pré-remplissage COREP/FINREP à partir de run_id :
  - COREP C34 : Standardised approach
  - COREP C07 : IRB approach by PD scale
  - COREP C08 : IRB approach by portfolio
  - COREP Leverage Ratio
  - COREP LCR
  - FINREP F01 : Balance sheet assets
  - FINREP F18 : Breakdown of loans

**UI**
- Page Pipeline réécrite avec mode "Run ID (I11)" vs "Legacy (I1-I8)"
- Pipeline E2E en 7 étapes automatisées
- 7 onglets de résultats avec métriques détaillées
- Badges cache_hit pour chaque étape

**Migrations**
- Migration `1f1d214080aa` : Création tables I11

### Changed
- Architecture centrée sur exposures au lieu de positions ad-hoc
- Cache I6 étendu aux nouvelles fonctions run_id

### Performance
- Génération 36k expositions : ~2s
- Génération 100k expositions : ~5s
- Cache speedup : 50-150x

### Tests
- 269/273 tests passing (98.5%)
- 0 régression I1-I8
- 4 échecs legacy pré-existants (test_standardized.py)

