# BACKLOG PRIORISÉ - BANKING SIMULATOR

**Version** : v0.12.1 → v1.0
**Date** : 5 novembre 2025
**Statut** : Actif

Ce backlog contient tous les items actionnables pour les itérations I13-I18, classés par priorité P0 (Critical), P1 (High), P2 (Medium).

---

## LÉGENDE

**Priorités** :
- **P0 (Critical)** : Bloquant ou requis pour production / réglementaire
- **P1 (High)** : Important mais non-bloquant, améliore significativement
- **P2 (Medium)** : Nice-to-have, améliorations incrémentales

**Efforts** :
- **XS** : <1h
- **S** : 1-4h
- **M** : 4-8h (1 jour)
- **L** : 8-24h (1-3 jours)
- **XL** : >24h (>3 jours)

**Statut** :
- 🔴 **TODO** : Pas démarré
- 🟡 **IN PROGRESS** : En cours
- 🟢 **DONE** : Complété

---

## P0 - CRITICAL (Itération I13-I14)

### I13-001 : CI Coverage Gate ≥85%
**Priorité** : P0
**Effort** : S (1h)
**Itération** : I13
**Statut** : 🔴 TODO

**Description** :
Ajouter un gate dans le CI qui fait échouer le build si la couverture de tests tombe en-dessous de 85%.

**Fichiers Impactés** :
- `.github/workflows/ci.yml`

**Tâches** :
- [ ] Modifier step "Upload coverage to Codecov" : `fail_ci_if_error: true`
- [ ] Ajouter step "Check coverage threshold" : `pytest --cov-fail-under=85`
- [ ] Tester avec code non-testé temporaire pour vérifier échec CI
- [ ] Documenter dans `CONTRIBUTING.md` le seuil 85%

**Test de Validation** :
```bash
# Ajouter une fonction non testée dans src/domain/
# CI doit échouer si coverage <85%
pytest tests/ --cov=src --cov-fail-under=85
```

**Critère d'Acceptation** :
- CI passe si coverage ≥85%
- CI échoue si coverage <85%
- Message d'erreur clair indique module responsable

---

### I13-002 : Badge Coverage dans README
**Priorité** : P0
**Effort** : XS (15min)
**Itération** : I13
**Statut** : 🔴 TODO

**Description** :
Ajouter badge Codecov dans `README.md` pour visibilité immédiate de la couverture de tests.

**Fichiers Impactés** :
- `README.md`

**Tâches** :
- [ ] Ajouter badge Codecov après badge MIT (ligne 6)
- [ ] URL badge : `https://codecov.io/gh/GITMHAROUECH/Banking_simulator/branch/main/graph/badge.svg`
- [ ] Vérifier affichage sur GitHub après push

**Test de Validation** :
- Badge visible sur GitHub
- Badge cliquable vers dashboard Codecov

**Critère d'Acceptation** :
- Badge coverage vert (≥85%) visible dans README
- Clic badge redirige vers Codecov dashboard

---

### I13-003 : QUICKSTART - Section Environment Variables
**Priorité** : P0
**Effort** : S (1h)
**Itération** : I13
**Statut** : 🔴 TODO

**Description** :
Enrichir `QUICKSTART.md` avec section détaillée sur variables d'environnement requises et configuration SQLite vs PostgreSQL.

**Fichiers Impactés** :
- `QUICKSTART.md`

**Tâches** :
- [ ] Ajouter section "Environment Variables" après "Installation"
- [ ] Documenter :
  - `DATABASE_URL` (SQLite local vs PostgreSQL prod)
  - `ARTIFACT_STORE` (file vs database)
  - `ARTIFACT_PATH`
  - `LOG_LEVEL`
- [ ] Exemples configuration SQLite (dev) et PostgreSQL (prod)
- [ ] Référencer `.env.example` explicitement

**Test de Validation** :
- Nouvel utilisateur peut configurer environnement en <5 min
- Documentation couvre 100% variables `.env.example`

**Critère d'Acceptation** :
- Section "Environment Variables" complète (4 variables documentées)
- Exemples SQLite et PostgreSQL clairs
- Référence `.env.example`

---

### I13-004 : QUICKSTART - Section Troubleshooting
**Priorité** : P0
**Effort** : S (1h)
**Itération** : I13
**Statut** : 🔴 TODO

**Description** :
Ajouter section "Troubleshooting" dans `QUICKSTART.md` avec erreurs communes et solutions.

**Fichiers Impactés** :
- `QUICKSTART.md`

**Tâches** :
- [ ] Ajouter section "Troubleshooting" après "Usage"
- [ ] Documenter 5+ erreurs communes :
  1. `ModuleNotFoundError: No module named 'db.models'` → `alembic upgrade head`
  2. `sqlite3.OperationalError: database is locked` → Passer à PostgreSQL
  3. `alembic.util.exc.CommandError: Can't locate revision` → `alembic downgrade -1 && alembic upgrade head`
  4. `ImportError: cannot import name 'X' from 'src.domain'` → Vérifier requirements.txt, réinstaller
  5. `streamlit run app/main.py` → Port 8501 déjà utilisé : `streamlit run app/main.py --server.port 8502`

**Test de Validation** :
- Reproduire chaque erreur → solution fonctionne
- Nouvel utilisateur peut debugger sans aide externe

**Critère d'Acceptation** :
- 5+ erreurs communes documentées avec solutions
- Chaque solution testée et validée

---

### I13-005 : Séparation UI/Services IFRS9
**Priorité** : P0
**Effort** : M (4-6h)
**Itération** : I13
**Statut** : 🔴 TODO

**Description** :
Séparer logique présentation (Streamlit) de logique métier IFRS9 pour améliorer testabilité et atteindre 95% coverage domain.

**Fichiers Impactés** :
- `app/pages/15_ECL.py` (UI uniquement)
- `src/services/ifrs9_service.py` (orchestration)
- `src/domain/ifrs9/ecl.py` (business logic pure)

**Tâches** :
- [ ] Auditer `app/pages/15_ECL.py` : identifier couplage UI/calculs
- [ ] Migrer calculs ECL vers `src/services/ifrs9_service.py::compute_ecl_from_run(run_id, scenario_id)`
- [ ] `15_ECL.py` appelle uniquement services (pas de calculs directs)
- [ ] Refactorer si nécessaire `src/domain/ifrs9/ecl.py` pour pureté fonctions
- [ ] Mettre à jour tests existants

**Test de Validation** :
```bash
pytest tests/domain/test_ifrs9_ecl.py --cov=src/domain/ifrs9/ecl.py --cov-report=term
# Target: 95%+ coverage
```

**Critère d'Acceptation** :
- `app/pages/15_ECL.py` contient 0 calculs métier (appels services uniquement)
- `src/domain/ifrs9/ecl.py` coverage ≥95%
- Tous tests passent (pas de régression)

---

### I13-006 : Tests IFRS9 - 12 → 20+ tests
**Priorité** : P0
**Effort** : M (3-4h)
**Itération** : I13
**Statut** : 🔴 TODO

**Description** :
Ajouter 8-10 tests IFRS9 pour couvrir scénarios edge cases et atteindre 95% coverage.

**Fichiers Impactés** :
- `tests/domain/test_ifrs9_ecl.py`

**Tâches** :
- [ ] Ajouter 3 tests PD curves :
  - `test_pd_curve_simple()` : Méthode simple, validation formule
  - `test_pd_curve_beta()` : Méthode beta, validation shape curve
  - `test_pd_curve_scenario_overlay()` : Application pd_shift
- [ ] Ajouter 5 tests LGD downturn par exposure_class :
  - `test_lgd_downturn_sovereign()` : Floor 20%
  - `test_lgd_downturn_corporate()` : Floor 30%
  - `test_lgd_downturn_retail()` : Floor 40%
  - `test_lgd_downturn_sme()` : Floor 45%
  - `test_lgd_downturn_real_estate()` : Floor 25%
- [ ] Ajouter 2 tests staging edge cases :
  - `test_staging_sicr_threshold_edge()` : PD exactly threshold
  - `test_staging_backstop_days_edge()` : DPD exactly backstop days

**Test de Validation** :
```bash
pytest tests/domain/test_ifrs9_ecl.py -v
# Should have 20+ tests, all passing
```

**Critère d'Acceptation** :
- 20+ tests IFRS9 (vs 12 actuels)
- Tous tests passent
- Coverage `src/domain/ifrs9/ecl.py` ≥95%

---

### I13-007 : Migration PostgreSQL Guide
**Priorité** : P0
**Effort** : S (2h)
**Itération** : I13
**Statut** : 🔴 TODO

**Description** :
Créer guide détaillé migration SQLite → PostgreSQL pour production.

**Fichiers Impactés** :
- `docs/MIGRATION_POSTGRESQL.md` (nouveau)

**Tâches** :
- [ ] Créer fichier `docs/MIGRATION_POSTGRESQL.md`
- [ ] Documenter :
  1. Pourquoi PostgreSQL (multi-user, ACID, performance)
  2. Installation PostgreSQL (Linux, macOS, Windows)
  3. Création database : `CREATE DATABASE banking_simulator;`
  4. Configuration `.env` : `DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/banking_simulator`
  5. Migration données SQLite → PostgreSQL (script Python avec pandas)
  6. Tests post-migration
  7. Backup/restore PostgreSQL

**Test de Validation** :
- Suivre guide sur environnement vierge → migration réussie
- Tests passent après migration

**Critère d'Acceptation** :
- Guide complet (7 sections)
- Testé sur environnement vierge
- Script migration fourni

---

### I14-001 : COREP C07 Full Implementation
**Priorité** : P0
**Effort** : M (5-6h)
**Itération** : I14
**Statut** : 🔴 TODO

**Description** :
Implémenter calculs complets COREP C07 (Crédit - Exposures) conformes EBA v3.3.

**Fichiers Impactés** :
- `src/services/reporting_service.py::_generate_corep_c07()`
- `tests/services/test_corep_c07.py` (nouveau)

**Tâches** :
- [ ] Mapping complet `exposure_class` → lignes COREP C07 (EBA taxonomy)
- [ ] Calcul colonnes :
  - Original Exposure (notional ou ead)
  - RWEA (Risk-Weighted Exposure Amount)
  - Risk Weight (%)
  - Own Funds Requirements (RWEA × 8%)
- [ ] Agrégation par exposure_class, entity
- [ ] Validation rules : sum checks, cross-checks
- [ ] Export XLSX avec formules Excel
- [ ] 10 tests unitaires

**Test de Validation** :
```bash
pytest tests/services/test_corep_c07.py -v
# Compare output avec spécifications EBA v3.3
```

**Critère d'Acceptation** :
- COREP C07 conforme EBA v3.3 (validation externe)
- 10+ tests, tous passent
- Export XLSX lisible avec formules

---

### I14-002 : COREP C08 Full Implementation
**Priorité** : P0
**Effort** : M (4-5h)
**Itération** : I14
**Statut** : 🔴 TODO

**Description** :
Implémenter calculs complets COREP C08 (Crédit - RWA) conformes EBA v3.3.

**Fichiers Impactés** :
- `src/services/reporting_service.py::_generate_corep_c08()`
- `tests/services/test_corep_c08.py` (nouveau)

**Tâches** :
- [ ] Agrégation RWA par exposure_class + approach (STD/IRB)
- [ ] Calcul colonnes :
  - RWEA (Risk-Weighted Exposure Amount)
  - Capital Requirements (RWEA × 8%)
  - Exposure Value (original exposure)
- [ ] Breakdown IRB vs Standardized
- [ ] Validation rules : total RWA = sum(RWA_i)
- [ ] Export XLSX avec formules
- [ ] 8 tests unitaires

**Test de Validation** :
```bash
pytest tests/services/test_corep_c08.py -v
```

**Critère d'Acceptation** :
- COREP C08 conforme EBA v3.3
- 8+ tests, tous passent
- Breakdown STD/IRB visible

---

### I14-003 : COREP C34 Full Implementation (SA-CCR)
**Priorité** : P0
**Effort** : M (6-7h)
**Itération** : I14
**Statut** : 🔴 TODO

**Description** :
Implémenter calculs complets COREP C34 (Counterparty Risk - SA-CCR) conformes CRR3 Article 274.

**Fichiers Impactés** :
- `src/services/reporting_service.py::_generate_corep_c34()`
- `tests/services/test_corep_c34.py` (nouveau)

**Tâches** :
- [ ] Calculs par netting set :
  - RC (Replacement Cost) : max(V - C, 0)
  - PFE (Potential Future Exposure) : Σ Addon_i
  - Multiplier : min(1, Floor + (1-Floor) × exp(...))
  - Alpha : 1.4 (CRR3)
  - EAD : Alpha × (RC + PFE)
- [ ] Agrégation par counterparty
- [ ] Validation formules CRR3 Article 274
- [ ] Export XLSX avec breakdown détaillé
- [ ] 12 tests unitaires

**Test de Validation** :
```bash
pytest tests/services/test_corep_c34.py -v
# Validation formules avec dataset référence EBA
```

**Critère d'Acceptation** :
- COREP C34 conforme CRR3 Article 274
- 12+ tests, tous passent
- Breakdown RC/PFE/Multiplier visible

---

### I14-004 : FINREP F09 Full Implementation (Impairment ECL)
**Priorité** : P0
**Effort** : M (5-6h)
**Itération** : I14
**Statut** : 🔴 TODO

**Description** :
Implémenter pré-remplissage automatique FINREP F09 (Impairment) à partir résultats IFRS9 ECL.

**Fichiers Impactés** :
- `src/services/reporting_service.py::_generate_finrep_f09()`
- `tests/services/test_finrep_f09.py` (nouveau)

**Tâches** :
- [ ] Intégration table `ecl_results` (run_id, scenario_id)
- [ ] Mapping staging :
  - S1 → Performing
  - S2 → Underperforming
  - S3 → Non-performing
- [ ] Calcul colonnes :
  - Gross Carrying Amount (notional)
  - Accumulated Impairment (ecl_amount cumulé)
  - ECL Coverage Ratio (Impairment / Gross Carrying Amount)
- [ ] Agrégation par exposure_class, entity, currency
- [ ] Export XLSX
- [ ] 8 tests unitaires

**Test de Validation** :
```bash
pytest tests/services/test_finrep_f09.py -v
```

**Critère d'Acceptation** :
- FINREP F09 conforme EBA v3.3
- 8+ tests, tous passent
- Mapping S1/S2/S3 correct

---

### I14-005 : FINREP F18 Full Implementation (Loans)
**Priorité** : P0
**Effort** : M (4-5h)
**Itération** : I14
**Statut** : 🔴 TODO

**Description** :
Implémenter pré-remplissage automatique FINREP F18 (Loans) avec breakdown détaillé.

**Fichiers Impactés** :
- `src/services/reporting_service.py::_generate_finrep_f18()`
- `tests/services/test_finrep_f18.py` (nouveau)

**Tâches** :
- [ ] Filtrer exposures : `product_type='Loan'`
- [ ] Agrégation par exposure_class, entity, currency
- [ ] Breakdown par maturity buckets :
  - <1 year
  - 1-5 years
  - >5 years
- [ ] Breakdown par collateral type (si disponible)
- [ ] Export XLSX
- [ ] 6 tests unitaires

**Test de Validation** :
```bash
pytest tests/services/test_finrep_f18.py -v
```

**Critère d'Acceptation** :
- FINREP F18 conforme EBA v3.3
- 6+ tests, tous passent
- Breakdown maturity visible

---

## P1 - HIGH (Itération I15-I16)

### I15-001 : Réconciliation - 10 Contrôles Automatiques
**Priorité** : P1
**Effort** : M (6-8h)
**Itération** : I15
**Statut** : 🔴 TODO

**Description** :
Implémenter 10 contrôles automatiques de réconciliation compta-risque avec export rapport Excel.

**Fichiers Impactés** :
- `src/services/reconciliation_service.py`
- `src/domain/consolidation/reconciliation.py`
- `tests/services/test_reconciliation_controls.py`

**Tâches** :
- [ ] Contrôle #1 : Total Actifs (exposures) vs Balance Sheet (assets) - Tolérance ±0.1%
- [ ] Contrôle #2 : Total Passifs vs Balance Sheet
- [ ] Contrôle #3 : Positions FX derivatives MTM vs FX Balance
- [ ] Contrôle #4 : Notionnels off-BS vs Notes états financiers
- [ ] Contrôle #5 : RWA total vs Capital Requirements (K × 12.5)
- [ ] Contrôle #6 : ECL S1/S2/S3 total vs Provisions comptables
- [ ] Contrôle #7 : Collatéral total vs Assets pledged
- [ ] Contrôle #8 : Netting sets MTM vs Derivative assets/liabilities
- [ ] Contrôle #9 : Sovereign exposures vs Treasury holdings
- [ ] Contrôle #10 : Retail exposures vs Retail loan book
- [ ] Fonction : `run_reconciliation_controls(run_id) -> List[ControlResult]`
- [ ] 20 tests unitaires (2 par contrôle)

**Test de Validation** :
```bash
# Test avec écart artificiel
pytest tests/services/test_reconciliation_controls.py::test_control_1_fail -v

# Test avec données valides
pytest tests/services/test_reconciliation_controls.py::test_all_controls_pass -v
```

**Critère d'Acceptation** :
- 10 contrôles implémentés
- Chaque contrôle retourne : (status: PASS/FAIL/WARN, gap: float, tolerance: float)
- 20+ tests, tous passent
- Détection écarts >98% (validation avec 50 runs)

---

### I15-002 : Export Reconciliation Report XLSX
**Priorité** : P1
**Effort** : S (2-3h)
**Itération** : I15
**Statut** : 🔴 TODO

**Description** :
Créer export Excel détaillé des résultats réconciliation avec 3 onglets (Summary, Gaps, Actions).

**Fichiers Impactés** :
- `src/services/reconciliation_service.py::export_reconciliation_report()`

**Tâches** :
- [ ] Onglet "Summary" :
  - Liste contrôles (1-10)
  - Statut (PASS/FAIL/WARN)
  - Écart (%)
  - Tolérance (%)
  - Timestamp
- [ ] Onglet "Gaps" :
  - Détail écarts par entity, currency, product_type
  - Colonne "Expected" vs "Actual"
- [ ] Onglet "Actions" :
  - Si FAIL : actions recommandées (ex: "Vérifier mapping sovereign")
  - Priorité (HIGH/MEDIUM/LOW)
- [ ] Conditional formatting : vert (PASS), rouge (FAIL), orange (WARN)
- [ ] 5 tests unitaires

**Test de Validation** :
```bash
pytest tests/services/test_reconciliation_report.py -v
# Valider export Excel lisible manuellement
```

**Critère d'Acceptation** :
- Export `reconciliation_report.xlsx` généré depuis `run_id`
- 3 onglets complets
- Conditional formatting fonctionnelle

---

### I15-003 : Consolidation IFRS10/11 - Éliminations Intragroupe
**Priorité** : P1
**Effort** : M (5-6h)
**Itération** : I15
**Statut** : 🔴 TODO

**Description** :
Implémenter éliminations intragroupe complexes (créances/dettes, dividendes) pour consolidation IFRS10/11.

**Fichiers Impactés** :
- `src/domain/consolidation/ifrs_conso.py`
- `tests/domain/test_consolidation_eliminations.py` (nouveau)

**Tâches** :
- [ ] Fonction : `eliminate_intragroup_balances(entities_df, trial_balance_df)`
  - Matching `counterparty_id` intra-groupe
  - Élimination créances/dettes réciproques
  - Élimination dividendes intragroupe
- [ ] Goodwill consolidation (acquisition premium)
- [ ] Minority interests calculation détaillé
- [ ] 10 tests unitaires (scénarios IG, IP, ME)

**Test de Validation** :
```bash
pytest tests/domain/test_consolidation_eliminations.py -v
```

**Critère d'Acceptation** :
- Éliminations créances/dettes fonctionnelles (matching 100%)
- Goodwill & minorities calculés correctement
- 10+ tests, tous passent

---

### I15-004 : Consolidation IFRS10/11 - FX Conversion Avancée
**Priorité** : P1
**Effort** : S (3-4h)
**Itération** : I15
**Statut** : 🔴 TODO

**Description** :
Implémenter conversion FX multi-currencies avec rates spot et average pour consolidation groupe.

**Fichiers Impactés** :
- `src/domain/consolidation/ifrs_conso.py`
- `tests/domain/test_consolidation_fx.py` (nouveau)

**Tâches** :
- [ ] Support rates spot (balance sheet) vs rates average (P&L)
- [ ] Fonction : `convert_fx_multi_currency(entities_df, fx_rates_df, target_currency='EUR')`
- [ ] Gestion différences de change (forex gains/losses)
- [ ] 5 tests unitaires (scénarios EUR/USD/CNY)

**Test de Validation** :
```bash
pytest tests/domain/test_consolidation_fx.py -v
```

**Critère d'Acceptation** :
- Conversion FX correcte (rates spot vs average)
- Différences de change calculées
- 5+ tests, tous passent

---

### I16-001 : Academy - Architecture Learning Path
**Priorité** : P1
**Effort** : M (4-5h)
**Itération** : I16
**Statut** : 🔴 TODO

**Description** :
Créer architecture backend Academy : modules Learning Path, Tutorials, Quiz, Gamification.

**Fichiers Impactés** :
- `src/academy/` (nouveau module)
  - `learning_path.py`
  - `tutorial.py`
  - `quiz_engine.py`
  - `gamification.py`

**Tâches** :
- [ ] Module `learning_path.py` :
  - Classe `Level` (1-5 : Junior → CRO/CFO)
  - Progression user (current_level, xp, completed_tutorials)
- [ ] Module `tutorial.py` :
  - Classe `Tutorial` (id, title, level, content_md, quiz_questions)
  - Loader markdown tutorials
- [ ] Module `quiz_engine.py` :
  - Classe `Quiz` (questions, answers, scoring)
  - Validation answers
- [ ] Module `gamification.py` :
  - Badges (RWA Expert, SA-CCR Master, etc.)
  - XP system (+10 XP tutorial, +50 XP level)
- [ ] 10 tests unitaires

**Test de Validation** :
```bash
pytest tests/academy/test_learning_path.py -v
```

**Critère d'Acceptation** :
- Architecture modulaire claire
- 4 modules créés avec tests
- 10+ tests, tous passent

---

### I16-002 : Academy - 20 Tutorials Content
**Priorité** : P1
**Effort** : XL (30-40h)
**Itération** : I16
**Statut** : 🔴 TODO

**Description** :
Créer contenu 20+ tutorials couvrant tous modules (RWA, SA-CCR, LCR, IFRS9, etc.).

**Fichiers Impactés** :
- `src/academy/tutorials/*.md` (20 fichiers)

**Tâches** :
- [ ] **Niveau 1 (Junior Analyst)** : 5 tutorials
  - T01 : Introduction Risk Management
  - T02 : RWA Standardized Basics
  - T03 : LCR Liquidity Coverage Ratio
  - T04 : Balance Sheet Fundamentals
  - T05 : Exposure at Default (EAD)
- [ ] **Niveau 2 (Analyst)** : 5 tutorials
  - T06 : IRB Foundation Approach
  - T07 : SA-CCR Calculation Step-by-Step
  - T08 : NSFR Net Stable Funding Ratio
  - T09 : Capital Ratios (CET1, Tier1)
  - T10 : Credit Conversion Factor (CCF)
- [ ] **Niveau 3 (Senior Analyst)** : 5 tutorials
  - T11 : CVA Credit Valuation Adjustment
  - T12 : IFRS9 ECL Staging (S1/S2/S3)
  - T13 : IFRS9 PD Term Structures
  - T14 : Consolidation IFRS10/11
  - T15 : Stress Testing Basics
- [ ] **Niveau 4 (Manager)** : 3 tutorials
  - T16 : COREP/FINREP Mapping
  - T17 : Reconciliation Workflows
  - T18 : Scenario Analysis Advanced
- [ ] **Niveau 5 (CRO/CFO)** : 2 tutorials
  - T19 : ICAAP Process (Internal Capital Adequacy)
  - T20 : Regulatory Reporting Strategy

**Format Tutorial** :
```markdown
# [Title]

## Introduction (2-3 paragraphes)

## Key Concepts

## Formulas
[LaTeX formulas]

## Numerical Example
[Step-by-step calculation]

## Interactive Simulation
[Streamlit sliders description]

## Quiz (3-5 questions)
```

**Test de Validation** :
- Chaque tutorial lisible markdown
- Formules LaTeX rendues correctement
- Exemples numériques validés

**Critère d'Acceptation** :
- 20+ tutorials créés
- Format standard respecté
- Review par expert banking (optionnel)

---

### I16-003 : Academy - UI Page Interactive
**Priorité** : P1
**Effort** : M (8-10h)
**Itération** : I16
**Statut** : 🔴 TODO

**Description** :
Créer page Streamlit interactive Academy avec parcours 5 niveaux, tutorials, quiz, gamification.

**Fichiers Impactés** :
- `app/pages/16_Academy.py` (nouveau)

**Tâches** :
- [ ] Section "My Progress" :
  - Current level (1-5)
  - XP bar
  - Badges earned
- [ ] Section "Tutorials" :
  - Liste tutorials par niveau
  - Bouton "Start Tutorial" → affiche content markdown
  - Formules LaTeX rendering (st.latex ou MathJax)
  - Simulation interactive (sliders Streamlit)
- [ ] Section "Quiz" :
  - Affichage questions après tutorial
  - Validation answers
  - Score affiché
- [ ] Section "Leaderboard" (optionnel I17)
  - Top 10 users (multi-user requis)
- [ ] 5 smoke tests

**Test de Validation** :
```bash
pytest tests/ui_smoke/test_academy_page.py -v
# Test navigation : niveau 1 → tutorial 01 → quiz → level up
```

**Critère d'Acceptation** :
- Page Academy fonctionnelle
- Tutorials affichés avec formules LaTeX
- Quiz validation fonctionne
- Progression user sauvegardée (session_state)

---

### I17-001 : Authentication Multi-User (OAuth ou Local)
**Priorité** : P1
**Effort** : M (5-6h)
**Itération** : I17
**Statut** : 🔴 TODO

**Description** :
Implémenter authentication utilisateurs (login/password) avec OAuth 2.0 ou local.

**Fichiers Impactés** :
- `src/auth/auth_service.py` (nouveau)
- `app/pages/00_Login.py` (nouveau)
- `db/migrations/` (nouvelle migration users table)

**Tâches** :
- [ ] Créer table `users` :
  ```sql
  CREATE TABLE users (
      id VARCHAR(36) PRIMARY KEY,
      username VARCHAR(100) UNIQUE NOT NULL,
      password_hash VARCHAR(255) NOT NULL,
      role VARCHAR(20) NOT NULL,  -- Viewer, Analyst, Admin
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );
  ```
- [ ] Fonction `authenticate(username, password) -> User | None`
- [ ] Hash passwords (bcrypt)
- [ ] Session management (JWT tokens ou st.session_state)
- [ ] Page login Streamlit (username/password form)
- [ ] 10 tests unitaires

**Test de Validation** :
```bash
pytest tests/auth/test_auth_service.py -v
```

**Critère d'Acceptation** :
- Authentication fonctionne (login réussi/échec)
- Passwords hashed (bcrypt)
- Session persistée
- 10+ tests, tous passent

---

### I17-002 : RBAC (3 Rôles : Viewer, Analyst, Admin)
**Priorité** : P1
**Effort** : M (4-5h)
**Itération** : I17
**Statut** : 🔴 TODO

**Description** :
Implémenter RBAC avec 3 rôles et permissions différenciées.

**Fichiers Impactés** :
- `src/auth/permissions.py` (nouveau)
- `app/pages/*.py` (vérification permissions)

**Tâches** :
- [ ] Définir permissions par rôle :
  - **Viewer** : Read-only (voir runs, reports), pas de création/modification
  - **Analyst** : Viewer + créer runs, télécharger exports, lancer simulations
  - **Admin** : Analyst + gérer users, voir audit logs, modifier configuration
- [ ] Fonction `check_permission(user, action) -> bool`
- [ ] Decorator `@require_role('Analyst')` pour fonctions sensibles
- [ ] Vérification permissions avant actions sensibles (UI + backend)
- [ ] 8 tests unitaires

**Test de Validation** :
```bash
pytest tests/auth/test_permissions.py -v
# Test : Viewer ne peut pas créer run (permission denied)
# Test : Admin peut tout faire
```

**Critère d'Acceptation** :
- 3 rôles définis avec permissions claires
- Vérification permissions frontend + backend
- 8+ tests, tous passent

---

### I17-003 : Audit Logs (100% Actions Sensibles)
**Priorité** : P1
**Effort** : S (3-4h)
**Itération** : I17
**Statut** : 🔴 TODO

**Description** :
Implémenter audit logging pour tracer toutes actions CRUD sur données sensibles.

**Fichiers Impactés** :
- `src/services/audit_service.py` (nouveau)
- `app/pages/13_Admin.py` (consultation logs)

**Tâches** :
- [ ] Créer table `audit_logs` :
  ```sql
  CREATE TABLE audit_logs (
      id VARCHAR(36) PRIMARY KEY,
      user_id VARCHAR(36) NOT NULL,
      action VARCHAR(50) NOT NULL,  -- CREATE, DELETE, EXPORT, MODIFY
      resource_type VARCHAR(50) NOT NULL,  -- run, exposure, config
      resource_id VARCHAR(36),
      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
      ip_address VARCHAR(45),
      details TEXT  -- JSON additional info
  );
  ```
- [ ] Fonction `log_action(user_id, action, resource_type, resource_id, details)`
- [ ] Intégrer logging dans :
  - CREATE run (`simulation_service.py`)
  - DELETE run
  - EXPORT data (`reporting_service.py`)
  - MODIFY config
- [ ] UI Admin : filtres (user, date range, action, resource_type)
- [ ] 6 tests unitaires

**Test de Validation** :
```bash
pytest tests/services/test_audit_service.py -v
# Créer run → vérifier log CREATE dans audit_logs
```

**Critère d'Acceptation** :
- 100% actions sensibles loggées
- UI Admin consultation logs fonctionnelle
- Retention 2 ans (configurable)
- 6+ tests, tous passent

---

## P2 - MEDIUM (Itération I16-I18)

### I16-004 : Academy - Multilangue i18n (FR/EN)
**Priorité** : P2
**Effort** : M (4-5h)
**Itération** : I16
**Statut** : 🔴 TODO

**Description** :
Support multilangue (français/anglais) pour interface Academy.

**Fichiers Impactés** :
- `src/academy/i18n/fr.json`
- `src/academy/i18n/en.json`
- `app/pages/16_Academy.py`

**Tâches** :
- [ ] Créer fichiers i18n JSON (FR, EN)
- [ ] Fonction `translate(key, lang='en')` loader traductions
- [ ] UI : sélecteur langue (dropdown)
- [ ] Traductions UI uniquement (tutorials EN prioritaire)

**Test de Validation** :
- Changer langue → UI mise à jour
- Aucun label hardcodé en français

**Critère d'Acceptation** :
- Support FR/EN pour UI
- Traductions complètes (100% labels)

---

### I16-005 : Academy - Certificat PDF Téléchargeable
**Priorité** : P2
**Effort** : S (3-4h)
**Itération** : I16
**Statut** : 🔴 TODO

**Description** :
Générer certificat PDF téléchargeable pour niveau 5 CRO/CFO complété.

**Fichiers Impactés** :
- `src/academy/certificate.py` (nouveau)

**Tâches** :
- [ ] Template certificat PDF (logo, nom user, niveau, date)
- [ ] Génération PDF (library : ReportLab ou FPDF)
- [ ] Bouton "Download Certificate" (niveau 5 uniquement)
- [ ] 3 tests unitaires

**Test de Validation** :
```bash
pytest tests/academy/test_certificate.py -v
# Générer certificat → PDF valide
```

**Critère d'Acceptation** :
- Certificat PDF généré (niveau 5)
- Template professionnel
- 3+ tests, tous passent

---

### I18-001 : Docker Compose 1-Click
**Priorité** : P2
**Effort** : S (3-4h)
**Itération** : I18
**Statut** : 🔴 TODO

**Description** :
Créer Docker Compose pour démarrage application en 1 commande (Streamlit + PostgreSQL).

**Fichiers Impactés** :
- `docker-compose.yml` (nouveau)
- `Dockerfile` (nouveau)
- `.dockerignore` (nouveau)

**Tâches** :
- [ ] `docker-compose.yml` :
  ```yaml
  version: '3.8'
  services:
    app:
      build: .
      ports:
        - "8501:8501"
      environment:
        - DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/banking
      depends_on:
        - db
    db:
      image: postgres:16
      environment:
        - POSTGRES_DB=banking
        - POSTGRES_USER=postgres
        - POSTGRES_PASSWORD=postgres
      volumes:
        - postgres_data:/var/lib/postgresql/data
  volumes:
    postgres_data:
  ```
- [ ] `Dockerfile` :
  - Base image : `python:3.11-slim`
  - Install dependencies
  - Run migrations
  - Entrypoint : `streamlit run app/main.py`
- [ ] README section "Quick Start avec Docker"

**Test de Validation** :
```bash
docker-compose up -d
# App accessible http://localhost:8501
```

**Critère d'Acceptation** :
- `docker-compose up -d` démarre app <2 min
- PostgreSQL + Streamlit fonctionnels
- README Docker section complète

---

### I18-002 : API Docs Auto (Sphinx)
**Priorité** : P2
**Effort** : M (5-6h)
**Itération** : I18
**Statut** : 🔴 TODO

**Description** :
Générer documentation API auto depuis docstrings avec Sphinx ou MkDocs.

**Fichiers Impactés** :
- `docs/conf.py` (Sphinx config)
- `docs/index.rst`
- `.github/workflows/docs.yml` (deploy GitHub Pages)

**Tâches** :
- [ ] Setup Sphinx : `sphinx-quickstart docs/`
- [ ] Config autodoc : `sphinx.ext.autodoc`, `sphinx.ext.napoleon`
- [ ] Générer docs : `sphinx-apidoc -o docs/source src/`
- [ ] Build HTML : `sphinx-build -b html docs/ docs/_build/html`
- [ ] Deploy GitHub Pages (workflow CI)
- [ ] Sections :
  - Getting Started
  - Architecture
  - API Reference (domain, services)
  - Guides

**Test de Validation** :
```bash
sphinx-build -b html docs/ docs/_build/html
open docs/_build/html/index.html
```

**Critère d'Acceptation** :
- API docs couvrent 100% modules publics
- Deployment GitHub Pages réussi
- Search fonctionnelle

---

### I18-003 : README & CONTRIBUTING Update
**Priorité** : P2
**Effort** : S (2-3h)
**Itération** : I18
**Statut** : 🔴 TODO

**Description** :
Mettre à jour README avec badges, screenshots, features. Enrichir CONTRIBUTING.

**Fichiers Impactés** :
- `README.md`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md` (nouveau)

**Tâches** :
- [ ] README :
  - Badges : build, coverage, version, license
  - Features list (RWA, SA-CCR, LCR, IFRS9, Academy)
  - Screenshots Streamlit pages
  - Quick Start Docker
- [ ] CONTRIBUTING :
  - Setup dev environment
  - Coding standards (ruff, mypy)
  - PR process (tests required, coverage ≥85%)
  - Release workflow
- [ ] CODE_OF_CONDUCT.md (Contributor Covenant)

**Test de Validation** :
- README lisible, badges visibles
- CONTRIBUTING clair (test avec nouveau contributeur)

**Critère d'Acceptation** :
- README complet avec badges/screenshots
- CONTRIBUTING détaillé (setup, standards, PR)
- CODE_OF_CONDUCT présent

---

### I18-004 : PyPI Packaging (Optionnel)
**Priorité** : P2
**Effort** : S (3-4h)
**Itération** : I18
**Statut** : 🔴 TODO (Optionnel)

**Description** :
Packager application pour distribution PyPI : `pip install banking-simulator`.

**Fichiers Impactés** :
- `setup.py` ou `pyproject.toml`
- `MANIFEST.in`

**Tâches** :
- [ ] `pyproject.toml` :
  ```toml
  [build-system]
  requires = ["setuptools>=61.0"]
  build-backend = "setuptools.build_meta"

  [project]
  name = "banking-simulator"
  version = "1.0.0"
  description = "Banking Risk Management Simulator & Academy"
  dependencies = [...]
  ```
- [ ] Build : `python -m build`
- [ ] Upload PyPI : `twine upload dist/*`
- [ ] Test install : `pip install banking-simulator`

**Test de Validation** :
```bash
pip install banking-simulator
banking-simulator --version
```

**Critère d'Acceptation** (optionnel) :
- Package PyPI publié
- Installation `pip install` fonctionne
- CLI `banking-simulator` démarre app

---

## STATISTIQUES BACKLOG

### Par Priorité
- **P0 (Critical)** : 12 items (I13-I14)
- **P1 (High)** : 12 items (I15-I17)
- **P2 (Medium)** : 6 items (I16-I18)
- **TOTAL** : 30 items

### Par Effort
- **XS (<1h)** : 1 item
- **S (1-4h)** : 11 items
- **M (4-8h)** : 15 items
- **L (8-24h)** : 0 items
- **XL (>24h)** : 3 items (tutorials content, tests exhaustifs)

### Par Itération
- **I13** : 7 items (P0)
- **I14** : 5 items (P0)
- **I15** : 4 items (P1)
- **I16** : 4 items (P1-P2)
- **I17** : 3 items (P1)
- **I18** : 4 items (P2)
- **Transversal** : 3 items (documentation, packaging)

### Effort Total Estimé
- **P0** : ~50-60h
- **P1** : ~45-55h
- **P2** : ~25-30h
- **TOTAL** : **120-145h** (15-20 dev-days)

---

## MAINTENANCE DU BACKLOG

### Processus
1. **Weekly Review** : Réévaluer priorités, statuts
2. **Refinement** : Affiner descriptions, efforts
3. **Grooming** : Supprimer items obsolètes, ajouter nouveaux
4. **Retrospective** : Post-itération, ajuster estimations

### Responsabilités
- **Product Owner** : Priorisation, validation AC
- **Dev Team** : Estimation effort, implémentation
- **QA** : Validation tests, critères acceptation

---

**Backlog créé par** : Claude (Anthropic AI)
**Date** : 5 novembre 2025
**Version** : 1.0
**Statut** : Actif
