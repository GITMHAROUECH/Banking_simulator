# ROADMAP I13-I18 : BANKING SIMULATOR ACADEMY

**Version** : v0.12.1 → v1.0 (Academy-Ready)
**Horizon** : 6 itérations (I13-I18)
**Durée Totale Estimée** : 3-4 mois
**Date** : 5 novembre 2025

---

## VISION STRATÉGIQUE

### But du Projet
Construire un **simulateur bancaire / academy** qui réplique le workflow complet d'un arrêté bancaire, de la génération des expositions jusqu'au dépôt régulateur (EBA/BCE), avec un **portail d'apprentissage** permettant à l'utilisateur d'évoluer de "Junior Analyst" à "CRO/CFO".

### Périmètre Fonctionnel
- ✅ **Simulation** : 36k exposures, 6 product types, seed-based reproducibility
- ✅ **Risque Crédit** : RWA (STD/IRB), capital ratios (CET1, Tier1, Total, Leverage)
- ✅ **Risque Contrepartie** : SA-CCR, CVA pricing & capital
- ✅ **Liquidité** : LCR, NSFR, ALMM
- ✅ **IFRS9 ECL** : Staging S1/S2/S3, PD curves, LGD downturn
- ⚠️ **Reporting Régulateur** : COREP/FINREP (stubs → full calculations)
- ⚠️ **Réconciliation Compta-Risque** : Contrôles basiques → avancés
- ⚠️ **Consolidation Groupe** : IFRS10/11 (formules basiques → éliminations complexes)
- ❌ **Academy Learning Path** : Parcours pédagogique Junior → CRO/CFO (à créer)
- ❌ **Multi-User** : Authentication, RBAC, audit logs (à créer)

### Milestone Final (v1.0 - Fin I18)
- **Regulatory Compliance** : COREP/FINREP complets, dépôt EBA-ready
- **Academy Readiness** : 20+ tutorials, 5 niveaux, gamification
- **Production Deployment** : PostgreSQL, RBAC, audit logs, Docker Compose 1-click
- **Packaging** : Documentation complète, API docs, CONTRIBUTING, Docker

---

## PRINCIPES DIRECTEURS

### Definition of Done (DoD) - Standard
Chaque user story/task doit satisfaire :
- [ ] Code implémenté et testé (coverage ≥85%)
- [ ] Tests passent (pytest CI green)
- [ ] Documentation mise à jour (README, QUICKSTART, docstrings)
- [ ] Pas de régression fonctionnelle (100% tests existants passent)
- [ ] Code review (si applicable)
- [ ] Merged dans branche principale

### Critères Mesurables
Chaque itération définit des **métriques quantifiables** :
- Coverage : X% → Y%
- Test count : N → M tests
- Time to first run : X min → Y min
- Modules/fonctionnalités implémentés : A/B → B/B

### Gestion des Risques
Chaque itération identifie :
- **Risques techniques** : complexité, dépendances externes
- **Risques planning** : estimations, disponibilité ressources
- **Mitigation** : actions préventives

---

## ITERATION I13 : HARDENING & QUALITY GATES

### Objectif
Consolider la **qualité du code**, mettre en place des **gates CI/CD stricts**, et améliorer la **documentation opérationnelle** pour garantir la maintenabilité et faciliter l'onboarding.

### Durée Estimée
**2 semaines** (10 jours ouvrés)

### Effort
**M (Medium)** : ~20-30h de développement

### User Stories

#### US1 : CI Coverage Gate
**En tant que** DevOps
**Je veux** un CI qui échoue automatiquement si coverage <85%
**Afin de** empêcher les régressions qualité et garantir maintenabilité

**Acceptance Criteria** :
- [ ] `.github/workflows/ci.yml` passe `fail_ci_if_error: true` pour Codecov
- [ ] Step `pytest --cov-fail-under=85` ajoute
- [ ] CI échoue si coverage <85% (test avec code non-testé temporaire)
- [ ] Badge coverage vert affiché dans README

#### US2 : Documentation Opérationnelle
**En tant que** nouvel utilisateur
**Je veux** démarrer l'application en <10 min sans aide externe
**Afin de** évaluer rapidement le projet

**Acceptance Criteria** :
- [ ] `QUICKSTART.md` contient section "Environment Variables"
  - DATABASE_URL (SQLite vs PostgreSQL examples)
  - ARTIFACT_STORE (file vs db)
  - ARTIFACT_PATH
  - LOG_LEVEL
- [ ] `QUICKSTART.md` contient section "Troubleshooting"
  - Erreur "No module named 'db.models'" → Solution : `alembic upgrade head`
  - Erreur "Database locked" → Solution : PostgreSQL
  - Erreur migrations → Solution : `alembic downgrade -1 && alembic upgrade head`
- [ ] `README.md` référence `.env.example` dans section Installation

#### US3 : Séparation UI/Services IFRS9
**En tant que** développeur
**Je veux** une séparation claire UI/Services pour IFRS9
**Afin de** améliorer testabilité et atteindre 95% coverage domain

**Acceptance Criteria** :
- [ ] Logique présentation dans `app/pages/15_ECL.py` séparée de calculs
- [ ] Calculs ECL orchestrés par `src/services/ifrs9_service.py` uniquement
- [ ] Tests domain `tests/domain/test_ifrs9_ecl.py` couvrent 95%+ de `src/domain/ifrs9/ecl.py`
- [ ] 20+ tests IFRS9 (vs 12 actuels)

### Tasks

| Task | Responsable | Effort | Fichiers Impactés | DoD |
|------|-------------|--------|-------------------|-----|
| ✅ **Audit Complet** | Claude | 2h | `docs/AUDIT.md` | Fichier créé, 15 sections |
| ✅ **Roadmap I13-I18** | Claude | 1h | `docs/ROADMAP_I13.md` | Fichier créé, 6 itérations |
| ✅ **Backlog Priorisé** | Claude | 1h | `docs/BACKLOG.md` | 30-40 items P0/P1/P2 |
| **CI Coverage Gate** | Dev | 30 min | `.github/workflows/ci.yml` | CI fail si <85% |
| **README Badge** | Dev | 10 min | `README.md` | Badge Codecov visible |
| **QUICKSTART Enrichi** | Dev | 1h | `QUICKSTART.md` | Sections env vars + troubleshooting |
| **Séparation IFRS9 UI** | Dev | 2h | `app/pages/15_ECL.py`, `src/services/ifrs9_service.py` | Logique séparée |
| **Tests IFRS9 +8** | Dev | 2h | `tests/domain/test_ifrs9_ecl.py` | 20 tests, 95% coverage |
| **PostgreSQL Guide** | Dev | 1h | `docs/MIGRATION_POSTGRESQL.md` | Guide migration SQLite→PG |

### Definition of Done (I13)

- [ ] CI passe avec coverage ≥85% (fail sinon)
- [ ] README affiche badge coverage vert Codecov
- [ ] QUICKSTART permet démarrage <10 min (testé avec nouvel utilisateur)
- [ ] `src/domain/ifrs9/ecl.py` coverage ≥95%
- [ ] 20+ tests IFRS9 (vs 12 actuels)
- [ ] 0 TODO dans code production (1 seul actuel résolu)
- [ ] Tous tests existants passent (273/273 ou 269/273 minimum)

### Critères Mesurables

| Métrique | Avant (I12) | Cible (I13) | Validation |
|----------|-------------|-------------|------------|
| **Coverage Domain** | 96%+ | 96%+ (maintenu) | `pytest --cov=src/domain` |
| **Coverage Services** | 87%+ | 88%+ | `pytest --cov=src/services` |
| **Test Count** | 273 | 285+ | `pytest --collect-only` |
| **Tests IFRS9** | 12 | 20+ | `pytest tests/domain/test_ifrs9_ecl.py` |
| **TODO Production** | 1 | 0 | `grep -r "TODO" src/` |
| **Time to First Run** | 15-20 min | <10 min | Onboarding test |
| **CI Runtime** | ~2-3 min | ~2-3 min (maintenu) | GitHub Actions logs |

### Risques & Mitigation

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| **Tests IFRS9 flaky** | LOW | MEDIUM | Seed deterministic, mock scenarios |
| **CI coverage gate casse builds** | MEDIUM | HIGH | Gradual rollout : warning → fail après I13 |
| **QUICKSTART incomplet** | LOW | MEDIUM | Test avec 2-3 nouveaux utilisateurs |

### Dépendances
- Aucune dépendance externe critique
- Iteration standalone (hardening interne)

---

## ITERATION I14 : REPORTING RÉGLEMENTAIRE COMPLET

### Objectif
Remplacer les **stubs COREP/FINREP** actuels par des **calculs complets cellule-par-cellule** conformes aux spécifications EBA v3.3, permettant le pré-remplissage automatique des templates régulateurs à partir d'un `run_id`.

### Durée Estimée
**3 semaines** (15 jours ouvrés)

### Effort
**L (Large)** : ~50-80h de développement

### User Stories

#### US4 : COREP C07/C08 Complets
**En tant que** Risk Manager
**Je veux** un COREP C07 (Exposures) et C08 (RWA) complets avec tous les champs requis
**Afin de** déposer le reporting crédit à l'EBA/BCE sans retraitement manuel

**Acceptance Criteria** :
- [ ] COREP C07 : Mapping complet exposure_class → lignes COREP
- [ ] COREP C07 : Colonnes : Original Exposure, RWEA, Risk Weight, Own Funds Requirements
- [ ] COREP C08 : Agrégation RWA par approach (STD/IRB)
- [ ] COREP C08 : Colonnes : RWEA, Capital Requirements, Exposure Value
- [ ] Validation rules : cross-checks, totals (sum checks)
- [ ] Export XLSX avec formules Excel pour double-vérification

#### US5 : COREP C34 (SA-CCR)
**En tant que** Risk Manager
**Je veux** un COREP C34 (Counterparty risk) avec calculs SA-CCR détaillés
**Afin de** reporter les expositions contrepartie conformément CRR3 Article 274

**Acceptance Criteria** :
- [ ] Calculs par netting set : RC (Replacement Cost), PFE (Potential Future Exposure), Multiplier, Alpha, EAD
- [ ] Agrégation par counterparty
- [ ] Validation formules CRR3 Article 274
- [ ] Export XLSX avec breakdown détaillé

#### US6 : FINREP F09 (Impairment ECL)
**En tant que** Contrôleur Financier
**Je veux** un FINREP F09 pré-rempli à partir des résultats IFRS9 ECL
**Afin de** déposer le reporting comptable FINREP à l'EBA/BCE

**Acceptance Criteria** :
- [ ] Intégration table `ecl_results` (run_id, scenario_id)
- [ ] Mapping S1/S2/S3 → FINREP stages (Performing, Underperforming, Non-performing)
- [ ] Colonnes : Gross Carrying Amount, Accumulated Impairment, ECL Coverage Ratio
- [ ] Agrégation par exposure_class, entity, currency

#### US7 : FINREP F18 (Loans)
**En tant que** Contrôleur Financier
**Je veux** un FINREP F18 (Loans) avec breakdown détaillé
**Afin de** reporter les encours crédits par catégorie

**Acceptance Criteria** :
- [ ] Agrégation prêts (product_type='Loan') par exposure_class, entity, currency
- [ ] Breakdown par maturity buckets (<1y, 1-5y, >5y)
- [ ] Breakdown par collateral type

### Tasks

| Task | Effort | Fichiers Impactés | Tests |
|------|--------|-------------------|-------|
| **COREP C07 Full** | 5h | `src/services/reporting_service.py` | 10 tests |
| **COREP C08 Full** | 4h | `src/services/reporting_service.py` | 8 tests |
| **COREP C34 Full** | 6h | `src/services/reporting_service.py` | 12 tests |
| **FINREP F09 Full** | 5h | `src/services/reporting_service.py` | 8 tests |
| **FINREP F18 Full** | 4h | `src/services/reporting_service.py` | 6 tests |
| **Validation Rules** | 4h | `src/domain/reporting/validation.py` | 10 tests |
| **Export XLSX Enhanced** | 3h | `src/services/reporting_service.py` | 5 tests |
| **Integration Tests** | 3h | `tests/services/test_corep_finrep_full.py` | 15 tests |
| **Documentation** | 2h | `docs/REPORTING_GUIDE.md` | - |

### Definition of Done (I14)

- [ ] COREP C07/C08/C34 conformes EBA v3.3 (validation externe specs)
- [ ] FINREP F09/F18 pré-remplis automatiquement depuis `run_id`
- [ ] Export XLSX avec validation rules (formules Excel, conditional formatting)
- [ ] 74+ nouveaux tests reporting (total ~360 tests)
- [ ] Coverage `src/services/reporting_service.py` ≥95%
- [ ] Documentation `docs/REPORTING_GUIDE.md` complète (mapping, formules, exemples)
- [ ] Demo : générer run_id → export COREP/FINREP complet en 1 clic

### Critères Mesurables

| Métrique | Avant (I13) | Cible (I14) | Validation |
|----------|-------------|-------------|------------|
| **COREP Templates** | 3/8 (stubs) | 8/8 (complets) | Validation EBA specs |
| **FINREP Templates** | 2/50 (stubs) | 10/50 (prioritaires) | Validation EBA specs |
| **Test Count** | 285 | 360+ | `pytest --collect-only` |
| **Coverage Reporting** | 60% | 95%+ | `pytest --cov=src/services/reporting_service.py` |
| **Export Time** | 2-5s | 3-8s | Benchmark (acceptable +50%) |

### Risques & Mitigation

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| **Spécifications EBA complexes** | HIGH | HIGH | Itérations incrémentales : C07 → C08 → C34 |
| **Mapping exposure_class incomplet** | MEDIUM | MEDIUM | Validation avec dataset production (si dispo) |
| **Performance dégradation** | LOW | MEDIUM | Profiling, optimisation vectorization |

### Dépendances
- **I13 → I14** : Coverage gate en place pour valider qualité nouvelles implémentations

---

## ITERATION I15 : RÉCONCILIATION & CONSOLIDATION AVANCÉE

### Objectif
Implémenter des **contrôles de réconciliation compta-risque automatiques et exhaustifs** (10+ règles), et enrichir la **consolidation IFRS10/11** avec éliminations intragroupe complexes.

### Durée Estimée
**2 semaines** (10 jours ouvrés)

### Effort
**M (Medium)** : ~30-40h de développement

### User Stories

#### US8 : Réconciliation Automatique
**En tant que** Contrôleur Financier
**Je veux** 10+ contrôles automatiques de réconciliation compta-risque
**Afin de** détecter immédiatement les incohérences entre balance sheet et expositions

**Acceptance Criteria** :
- [ ] Contrôle #1 : Total Actifs (exposures) vs Balance Sheet (assets) - Tolérance ±0.1%
- [ ] Contrôle #2 : Total Passifs (deposits, liabilities) vs Balance Sheet - Tolérance ±0.1%
- [ ] Contrôle #3 : Positions FX (derivatives MTM) vs FX Balance
- [ ] Contrôle #4 : Notionnels off-balance sheet vs Notes états financiers
- [ ] Contrôle #5 : RWA total vs Capital Requirements (K × 12.5)
- [ ] Contrôle #6 : ECL S1/S2/S3 total vs Provisions comptables
- [ ] Contrôle #7 : Collatéral total vs Assets pledged
- [ ] Contrôle #8 : Netting sets MTM vs Derivative assets/liabilities
- [ ] Contrôle #9 : Sovereign exposures vs Treasury holdings
- [ ] Contrôle #10 : Retail exposures vs Retail loan book
- [ ] Export `reconciliation_report.xlsx` avec :
  - Onglet "Summary" : statut contrôles (PASS/FAIL/WARN)
  - Onglet "Gaps" : écarts détaillés par entity/currency
  - Onglet "Actions" : actions recommandées si FAIL

#### US9 : Consolidation IFRS10/11 Avancée
**En tant que** Contrôleur Groupe
**Je veux** une consolidation IFRS10/11 avec éliminations intragroupe complexes
**Afin de** produire des états financiers consolidés conformes IFRS

**Acceptance Criteria** :
- [ ] Éliminations créances/dettes intragroupe (matching counterparty_id)
- [ ] Éliminations dividendes intragroupe
- [ ] Goodwill consolidation (acquisition premium)
- [ ] Minority interests calculation détaillé
- [ ] FX conversion multi-currencies avec rates spot/average
- [ ] Support 3 méthodes : IG (>50%), IP (20-50%), ME (<20%)

### Tasks

| Task | Effort | Fichiers Impactés | Tests |
|------|--------|-------------------|-------|
| **10 Contrôles Réconciliation** | 6h | `src/services/reconciliation_service.py` | 20 tests |
| **Export Reconciliation Report** | 2h | `src/services/reconciliation_service.py` | 5 tests |
| **Éliminations Intragroupe** | 5h | `src/domain/consolidation/ifrs_conso.py` | 10 tests |
| **Goodwill & Minorities** | 3h | `src/domain/consolidation/ifrs_conso.py` | 5 tests |
| **FX Consolidation Avancée** | 3h | `src/domain/consolidation/ifrs_conso.py` | 5 tests |
| **UI Reconciliation Page** | 4h | `app/pages/07_Consolidation.py` | 3 smoke tests |
| **Documentation** | 2h | `docs/RECONCILIATION_GUIDE.md` | - |

### Definition of Done (I15)

- [ ] 10 contrôles réconciliation implémentés et testés
- [ ] Export `reconciliation_report.xlsx` généré depuis `run_id`
- [ ] Test : générer run avec écart artificiel → contrôle FAIL détecté
- [ ] Test : générer run valide → tous contrôles PASS
- [ ] Consolidation IFRS10/11 : éliminations intragroupe fonctionnelles
- [ ] 48+ nouveaux tests (total ~410 tests)
- [ ] Coverage `src/services/reconciliation_service.py` ≥90%
- [ ] Coverage `src/domain/consolidation/` ≥90%

### Critères Mesurables

| Métrique | Avant (I14) | Cible (I15) | Validation |
|----------|-------------|-------------|------------|
| **Contrôles Réconciliation** | 2 | 10+ | Validation avec écarts artificiels |
| **Taux Détection Écarts** | ~70% | >98% | Test avec 50 runs (10% avec écarts) |
| **Test Count** | 360 | 410+ | `pytest --collect-only` |
| **Coverage Reconciliation** | 50% | 90%+ | `pytest --cov=src/services/reconciliation_service.py` |

### Risques & Mitigation

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| **Faux positifs contrôles** | MEDIUM | MEDIUM | Tolérances configurables (±0.1% → ±0.5%) |
| **Performance 10 contrôles** | LOW | MEDIUM | Exécution parallèle (asyncio, threading) |
| **Éliminations complexes** | MEDIUM | HIGH | Validation avec expert comptable IFRS |

### Dépendances
- **I14 → I15** : COREP/FINREP données nécessaires pour réconciliation avancée (matching FINREP vs exposures)

---

## ITERATION I16 : ACADEMY - LEARNING PATH

### Objectif
Créer un **parcours pédagogique interactif** permettant à l'utilisateur d'évoluer de "Junior Analyst" à "CRO/CFO" via 20+ tutorials, quiz, et gamification (badges, niveaux).

### Durée Estimée
**3 semaines** (15 jours ouvrés)

### Effort
**L (Large)** : ~60-80h de développement + contenu

### User Stories

#### US10 : Parcours Pédagogique 5 Niveaux
**En tant que** apprenant
**Je veux** un parcours structuré en 5 niveaux de difficulté
**Afin de** progresser de Junior Analyst à CRO/CFO

**Acceptance Criteria** :
- [ ] Niveau 1 : **Junior Analyst** (Basics)
  - Concepts : Exposition, EAD, PD, LGD, RWA
  - Tutorials : 5 (RWA Standardized, LCR, Balance Sheet basics)
  - Quiz : 10 questions
- [ ] Niveau 2 : **Analyst** (Intermediate)
  - Concepts : IRB, SA-CCR, NSFR
  - Tutorials : 5 (IRB Foundation, SA-CCR calcul, NSFR ratios)
  - Quiz : 15 questions
- [ ] Niveau 3 : **Senior Analyst** (Advanced)
  - Concepts : CVA, IFRS9 ECL, Consolidation
  - Tutorials : 5 (CVA pricing, ECL staging, IFRS10/11)
  - Quiz : 20 questions
- [ ] Niveau 4 : **Manager** (Expert)
  - Concepts : COREP/FINREP, Réconciliation, Stress Testing
  - Tutorials : 3 (COREP mapping, Reconciliation workflows, Scenario analysis)
  - Quiz : 15 questions
- [ ] Niveau 5 : **CRO/CFO** (Strategic)
  - Concepts : Capital Planning, ICAAP, Regulatory Strategy
  - Tutorials : 2 (ICAAP process, Regulatory reporting strategy)
  - Quiz : 10 questions

#### US11 : Tutorials Interactifs
**En tant que** apprenant
**Je veux** des tutorials interactifs avec exemples concrets et simulations
**Afin de** comprendre les concepts en pratique

**Acceptance Criteria** :
- [ ] Chaque tutorial :
  - Introduction (2-3 paragraphes)
  - Formules clés (LaTeX rendering)
  - Exemple numérique step-by-step
  - Simulation interactive (sliders Streamlit : changer PD/LGD → voir impact RWA)
  - Quiz validation (3-5 questions)
- [ ] 20+ tutorials couvrant tous modules (RWA, SA-CCR, LCR, IFRS9, etc.)
- [ ] Support multilangue (FR/EN) via i18n

#### US12 : Gamification
**En tant que** apprenant
**Je veux** des badges et points de progression
**Afin de** rester motivé et visualiser ma progression

**Acceptance Criteria** :
- [ ] Badges : "RWA Expert", "SA-CCR Master", "IFRS9 Guru", etc.
- [ ] Points XP : +10 XP par tutorial complété, +50 XP par niveau débloqué
- [ ] Leaderboard (optionnel, multi-user I17)
- [ ] Certificat PDF téléchargeable (niveau 5 CRO/CFO)

### Tasks

| Task | Effort | Fichiers Impactés | Tests |
|------|--------|-------------------|-------|
| **Architecture Learning Path** | 4h | `src/academy/` (nouveau module) | - |
| **20 Tutorials Content** | 30h | `src/academy/tutorials/*.md` | - |
| **Quiz Engine** | 6h | `src/academy/quiz_engine.py` | 10 tests |
| **Gamification System** | 5h | `src/academy/gamification.py` | 8 tests |
| **UI Academy Page** | 8h | `app/pages/16_Academy.py` (nouveau) | 5 smoke tests |
| **Multilangue i18n** | 4h | `src/academy/i18n/` | - |
| **Certificat PDF** | 3h | `src/academy/certificate.py` | 3 tests |
| **Documentation** | 2h | `docs/ACADEMY_GUIDE.md` | - |

### Definition of Done (I16)

- [ ] 5 niveaux implémentés : Junior → CRO/CFO
- [ ] 20+ tutorials interactifs avec simulations Streamlit
- [ ] Quiz validation (70 questions total)
- [ ] Badges et système XP fonctionnels
- [ ] Certificat PDF téléchargeable (niveau 5)
- [ ] Test utilisateur : 5 personnes complètent niveau 1-2 (taux complétion >80%)
- [ ] 26+ nouveaux tests (total ~440 tests)

### Critères Mesurables

| Métrique | Avant (I15) | Cible (I16) | Validation |
|----------|-------------|-------------|------------|
| **Niveaux Academy** | 0 | 5 | UI visible + tests |
| **Tutorials** | 0 | 20+ | Content markdown + Streamlit pages |
| **Quiz Questions** | 0 | 70+ | Quiz engine tests |
| **Taux Complétion** | - | >80% | Test avec 5 utilisateurs |
| **Test Count** | 410 | 440+ | `pytest --collect-only` |

### Risques & Mitigation

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| **Contenu tutorials long** | HIGH | MEDIUM | Templates réutilisables, AI-assisted content generation |
| **Multilangue complexe** | MEDIUM | LOW | i18n pour UI uniquement, tutorials EN prioritaire |
| **Gamification superflu** | LOW | LOW | MVP : badges uniquement, leaderboard optionnel I17 |

### Dépendances
- **I15 → I16** : Consolidation valide requise pour tutorials niveau 3-4 (données réalistes)

---

## ITERATION I17 : MULTI-USER & RBAC

### Objectif
Implémenter **authentication multi-user** et **RBAC (Role-Based Access Control)** avec 3 rôles minimum (Viewer, Analyst, Admin), et **audit logs** pour traçabilité des actions sensibles.

### Durée Estimée
**2 semaines** (10 jours ouvrés)

### Effort
**M (Medium)** : ~30-40h de développement

### User Stories

#### US13 : Authentication
**En tant que** administrateur
**Je veux** une authentification utilisateurs (login/password)
**Afin de** contrôler l'accès à l'application

**Acceptance Criteria** :
- [ ] Page login Streamlit (username/password)
- [ ] Backend : OAuth 2.0 ou LDAP (configurable)
- [ ] Session management (JWT tokens ou Streamlit session_state)
- [ ] Password hashing (bcrypt, scrypt)
- [ ] User table : `users(id, username, password_hash, role, created_at)`

#### US14 : RBAC (3 Rôles)
**En tant que** administrateur
**Je veux** définir des rôles avec permissions différenciées
**Afin de** limiter l'accès aux fonctionnalités sensibles

**Acceptance Criteria** :
- [ ] **Viewer** : Read-only (voir runs, reports), pas de création/modification
- [ ] **Analyst** : Viewer + créer runs, télécharger exports, lancer simulations
- [ ] **Admin** : Analyst + gérer users, voir audit logs, modifier configuration
- [ ] Permissions vérifiées avant chaque action sensible

#### US15 : Audit Logs
**En tant que** auditeur
**Je veux** tracer toutes les actions CRUD sur données sensibles
**Afin de** garantir conformité et détection fraudes

**Acceptance Criteria** :
- [ ] Table `audit_logs(id, user_id, action, resource_type, resource_id, timestamp, ip_address)`
- [ ] Actions loggées : CREATE run, DELETE run, EXPORT data, MODIFY config
- [ ] UI Admin : page "Audit Logs" avec filtres (user, date, action)
- [ ] Retention logs : 2 ans minimum

### Tasks

| Task | Effort | Fichiers Impactés | Tests |
|------|--------|-------------------|-------|
| **User Authentication** | 5h | `src/auth/auth_service.py` (nouveau) | 10 tests |
| **RBAC Permissions** | 4h | `src/auth/permissions.py` | 8 tests |
| **Audit Logs Backend** | 3h | `src/services/audit_service.py` | 6 tests |
| **UI Login Page** | 3h | `app/pages/00_Login.py` (nouveau) | 3 smoke tests |
| **UI Admin Page** | 5h | `app/pages/13_Admin.py` | 3 smoke tests |
| **Migration DB Users** | 1h | `db/migrations/` | - |
| **Documentation** | 2h | `docs/AUTH_RBAC_GUIDE.md` | - |

### Definition of Done (I17)

- [ ] Authentication OAuth ou local fonctionnelle
- [ ] 3 rôles implémentés : Viewer, Analyst, Admin
- [ ] Permissions RBAC vérifiées sur toutes pages sensibles
- [ ] Audit logs enregistrent 100% actions sensibles (CRUD exposures, runs, exports)
- [ ] UI Admin : gestion users + consultation audit logs
- [ ] 30+ nouveaux tests (total ~470 tests)
- [ ] Documentation `docs/AUTH_RBAC_GUIDE.md` complète

### Critères Mesurables

| Métrique | Avant (I16) | Cible (I17) | Validation |
|----------|-------------|-------------|------------|
| **Rôles RBAC** | 0 | 3+ | Tests permissions |
| **Audit Logs Coverage** | 0% | 100% actions sensibles | Vérification table audit_logs |
| **Test Count** | 440 | 470+ | `pytest --collect-only` |
| **Login Time** | - | <2s | Benchmark |

### Risques & Mitigation

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| **Streamlit multi-user limité** | MEDIUM | HIGH | Session state + cookies, ou backend FastAPI séparé |
| **RBAC complexe** | LOW | MEDIUM | MVP 3 rôles simples, éviter over-engineering |
| **Performance audit logs** | LOW | LOW | Async logging (fire-and-forget), indexer user_id/timestamp |

### Dépendances
- **I16 → I17** : Academy en place, RBAC peut différencier accès tutorials (Viewer vs Analyst)

---

## ITERATION I18 : PACKAGING & DIFFUSION

### Objectif
Préparer le projet pour **diffusion large** : Docker Compose 1-click, documentation complète (API docs auto, guides), README/CONTRIBUTING à jour, packaging PyPI (optionnel).

### Durée Estimée
**1 semaine** (5 jours ouvrés)

### Effort
**S (Small)** : ~15-20h de développement

### User Stories

#### US16 : Docker Compose 1-Click
**En tant que** nouvel utilisateur
**Je veux** démarrer l'application en 1 commande
**Afin de** évaluer le projet sans setup complexe

**Acceptance Criteria** :
- [ ] `docker-compose.yml` avec 2 services : `app` (Streamlit) + `db` (PostgreSQL)
- [ ] Variables d'environnement via `.env` (DATABASE_URL, etc.)
- [ ] Commande : `docker-compose up -d` → app accessible http://localhost:8501
- [ ] README section "Quick Start avec Docker" (3 étapes max)

#### US17 : Documentation Centralisée
**En tant que** développeur
**Je veux** une documentation centralisée avec API docs, guides, tutorials
**Afin de** contribuer facilement au projet

**Acceptance Criteria** :
- [ ] API docs auto-générées (Sphinx ou MkDocs) depuis docstrings
- [ ] Deployment : GitHub Pages ou ReadTheDocs
- [ ] Sections :
  - Getting Started
  - Architecture
  - API Reference (domain, services)
  - Guides (COREP/FINREP, IFRS9, etc.)
  - Contributing
  - Changelog
- [ ] Search fonctionnelle

#### US18 : README & CONTRIBUTING à Jour
**En tant que** contributeur potentiel
**Je veux** un README clair et CONTRIBUTING détaillé
**Afin de** comprendre le projet et savoir comment contribuer

**Acceptance Criteria** :
- [ ] README : badges (build, coverage, version), features, quick start, screenshots
- [ ] CONTRIBUTING : setup dev, coding standards, PR process, release workflow
- [ ] CODE_OF_CONDUCT.md
- [ ] LICENSE.md (MIT ou autre)

### Tasks

| Task | Effort | Fichiers Impactés | Tests |
|------|--------|-------------------|-------|
| **Docker Compose** | 3h | `docker-compose.yml`, `Dockerfile` | Manual tests |
| **API Docs Sphinx** | 5h | `docs/conf.py`, docstrings | - |
| **Docs Deployment** | 2h | `.github/workflows/docs.yml` | - |
| **README Update** | 2h | `README.md` | - |
| **CONTRIBUTING** | 2h | `CONTRIBUTING.md` | - |
| **PyPI Packaging** | 3h | `setup.py`, `pyproject.toml` | - |
| **Release Workflow** | 2h | `.github/workflows/release.yml` | - |

### Definition of Done (I18)

- [ ] Docker Compose up → app démarre en <2 min
- [ ] Documentation centralisée déployée (GitHub Pages ou ReadTheDocs)
- [ ] API docs auto couvrent 100% modules publics (domain, services)
- [ ] README, CONTRIBUTING, CODE_OF_CONDUCT à jour
- [ ] (Optionnel) Package PyPI publié : `pip install banking-simulator`
- [ ] Release v1.0 taguée sur GitHub

### Critères Mesurables

| Métrique | Avant (I17) | Cible (I18) | Validation |
|----------|-------------|-------------|------------|
| **Time to First Run** | 10 min | <5 min (Docker Compose) | Test 5 users |
| **Documentation Pages** | 50 .md dispersés | Docs.html centralisées | ReadTheDocs/GitHub Pages |
| **API Docs Coverage** | 0% | 100% modules publics | Sphinx build success |
| **PyPI Package** | Non | Oui (optionnel) | `pip install banking-simulator` |

### Risques & Mitigation

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| **Docker build complexe** | LOW | MEDIUM | Multi-stage build, image optimisée Alpine |
| **Docs deployment fail** | LOW | LOW | GitHub Pages simple, ou ReadTheDocs |
| **PyPI naming conflict** | MEDIUM | LOW | Nom alternatif : `banking-simulator-academy` |

### Dépendances
- **I17 → I18** : Multi-user prêt, Docker Compose peut inclure setup users par défaut

---

## DEPENDENCIES & CRITICAL PATH

### Diagramme de Dépendances

```
I13 (Hardening)
  ↓ (Coverage gate requis pour valider I14)
I14 (COREP/FINREP)
  ↓ (Données COREP nécessaires pour réconciliation I15)
I15 (Réconciliation & Consolidation)
  ↓ (Consolidation valide pour tutorials I16)
I16 (Academy Learning Path)
  ↓ (Academy prêt pour RBAC différencié I17)
I17 (Multi-User & RBAC)
  ↓ (Multi-user pour Docker Compose setup I18)
I18 (Packaging & Diffusion)
  ↓
v1.0 RELEASE ✅
```

### Critical Path
**I13 → I14 → I15 → I16** (critique pour Academy)

I17 et I18 peuvent être parallélisées partiellement si ressources disponibles.

---

## SUCCESS METRICS (I13-I18)

### Métriques Quantitatives

| Métrique | Avant (I12) | Cible (I18 - v1.0) | Delta |
|----------|-------------|-------------------|-------|
| **Coverage Domain** | 96%+ | 96%+ (maintenu) | - |
| **Coverage Services** | 87%+ | 95%+ | +8% |
| **Test Count** | 273 | 500+ | +227 tests |
| **COREP Templates** | 3/8 (stubs) | 8/8 (complets) | +5 templates |
| **FINREP Templates** | 2/50 (stubs) | 10/50 (prioritaires) | +8 templates |
| **Contrôles Réconciliation** | 2 | 10+ | +8 contrôles |
| **Tutorials Academy** | 0 | 20+ | +20 tutorials |
| **Rôles RBAC** | 0 | 3+ | +3 rôles |
| **Time to First Run** | 15-20 min | <5 min (Docker) | -75% |
| **Documentation Pages** | 50 .md | Docs.html centralisées | Consolidation |

### Métriques Qualitatives

- **Regulatory Readiness** : COREP/FINREP dépôt EBA-ready (vs stubs)
- **Learning Effectiveness** : Taux complétion Academy >80%
- **User Onboarding** : <5 min setup (vs 15-20 min)
- **Security Posture** : RBAC + audit logs (vs aucun)
- **Community Engagement** : CONTRIBUTING clair, issues template, Discord/Slack (optionnel)

---

## RELEASE PLAN

### v0.12.1 (Actuel)
- ✅ Run-ID pipeline
- ✅ IFRS9 ECL
- ✅ RWA/SA-CCR/LCR/NSFR
- ⚠️ COREP/FINREP stubs

### v0.13 (Fin I13 - S2 Nov 2025)
- ✅ CI coverage gate ≥85%
- ✅ QUICKSTART enrichi
- ✅ IFRS9 tests 95%+
- ✅ Audit complet + Roadmap

### v0.14 (Fin I14 - S5 Nov 2025)
- ✅ COREP C07/C08/C34 complets
- ✅ FINREP F09/F18 complets
- ✅ Reporting service 95% coverage

### v0.15 (Fin I15 - S2 Déc 2025)
- ✅ 10+ contrôles réconciliation
- ✅ Consolidation IFRS10/11 avancée
- ✅ Export reconciliation_report.xlsx

### v0.16 (Fin I16 - S5 Déc 2025)
- ✅ Academy 5 niveaux
- ✅ 20+ tutorials
- ✅ Gamification (badges, XP)

### v0.17 (Fin I17 - S2 Jan 2026)
- ✅ Multi-user authentication
- ✅ RBAC 3 rôles
- ✅ Audit logs 100%

### v1.0 (Fin I18 - S3 Jan 2026) 🎉
- ✅ Docker Compose 1-click
- ✅ Documentation centralisée
- ✅ PyPI package (optionnel)
- ✅ **PRODUCTION-READY + ACADEMY-READY**

---

## TEAM & RESOURCES

### Profils Requis

| Profil | Itérations | Compétences |
|--------|-----------|-------------|
| **Backend Dev** | I13-I18 | Python, SQLAlchemy, Domain modeling |
| **Data Engineer** | I14-I15 | Pandas, NumPy, Data pipelines |
| **Regulatory Expert** | I14 | COREP/FINREP specs EBA v3.3 |
| **DevOps** | I13, I18 | CI/CD, Docker, PostgreSQL |
| **Frontend Dev** | I16 | Streamlit, UX, Gamification |
| **Content Writer** | I16 | Banking/Finance, Tutorials pédagogiques |
| **Security Expert** | I17 | OAuth, RBAC, Audit logs |

### Effort Total Estimé

| Itération | Effort | Durée | Dev-Days |
|-----------|--------|-------|----------|
| I13 | M | 2 semaines | 10-15 |
| I14 | L | 3 semaines | 20-30 |
| I15 | M | 2 semaines | 10-15 |
| I16 | L | 3 semaines | 25-35 |
| I17 | M | 2 semaines | 10-15 |
| I18 | S | 1 semaine | 5-10 |
| **TOTAL** | - | **13 semaines (3-4 mois)** | **80-120 dev-days** |

---

## CONCLUSION

Ce roadmap I13-I18 transforme le Banking Simulator v0.12.1 (déjà production-ready) en une **plateforme Academy complète** (v1.0) avec :

✅ **Regulatory Compliance** : COREP/FINREP complets, dépôt EBA-ready
✅ **Learning Platform** : 20+ tutorials, 5 niveaux, gamification
✅ **Enterprise Features** : Multi-user, RBAC, audit logs
✅ **Production Deployment** : Docker Compose 1-click, PostgreSQL, docs centralisées

**Prêt à démarrer l'itération I13 ! 🚀**

---

**Document créé par** : Claude (Anthropic AI)
**Date** : 5 novembre 2025
**Version Roadmap** : 1.0
