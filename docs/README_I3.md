# Itération 3 - Adaptateurs & Point d'entrée + Smoke test

## ✅ Objectifs atteints

- [x] Créer `app/main.py` (point d'entrée Streamlit unique)
- [x] Créer `app/adapters/legacy_compat.py` (adaptateurs compatibilité)
- [x] Brancher l'UI sur les adaptateurs sans casser les imports
- [x] Smoke test Streamlit (7/7 tests passent)
- [x] ruff check ✓
- [x] mypy --check-untyped-defs ✓ (sur fichiers I3)

## 📦 Fichiers créés

### 1. `app/adapters/legacy_compat.py` (35 lignes)

**Rôle** : Expose les signatures historiques attendues par l'UI en déléguant au Domain.

**Exports** :
```python
from app.adapters.legacy_compat import (
    generate_positions_advanced,
    calculate_rwa_advanced,
    calculate_liquidity_advanced,
    compute_capital_ratios
)
```

### 2. `app/main.py` (180 lignes)

**Rôle** : Point d'entrée Streamlit avec navigation sidebar et routage vers les pages.

**Pages supportées** :
- 🏠 Accueil
- ⚙️ Configuration Avancée
- 📊 Simulation Monte Carlo
- 🔄 Consolidation IFRS
- 🔍 Réconciliation Compta-Risque
- ⚠️ Risque de Crédit CRR3
- 💧 Liquidité (LCR/NSFR/ALMM)
- 🏛️ Ratios de Capital
- 📈 Reporting Réglementaire
- 📥 Export Excel Avancé
- 📋 Templates & Import
- ℹ️ Documentation CRR3

### 3. `tests/ui_smoke/test_app_boot.py` (135 lignes)

**Tests** :
- Import de `app/main.py` sans exception
- Import des adaptateurs sans exception
- Exports des fonctions attendues
- Appel de `generate_positions_advanced()` via adaptateur
- Appel de `calculate_rwa_advanced()` via adaptateur
- Appel de `calculate_liquidity_advanced()` via adaptateur
- Appel de `compute_capital_ratios()` via adaptateur

## 🧪 Commandes de validation

```bash
# Smoke test
pytest -q tests/ui_smoke/test_app_boot.py

# Lint
ruff check app/main.py app/adapters/

# Typage (fichiers I3 uniquement)
mypy --check-untyped-defs app/main.py app/adapters/legacy_compat.py --no-error-summary --follow-imports=skip

# Démarrage Streamlit headless
streamlit run app/main.py --server.headless true --server.port 8501
```

## 🎯 Résultats

- ✅ **7/7 smoke tests passent** en 4.94s
- ✅ **ruff check** : All checks passed
- ✅ **Compatibilité ascendante** : Aucun import cassé
- ✅ **Point d'entrée fonctionnel** : `streamlit run app/main.py`

## 🚀 Prochaine étape

**Itération 4** : Domain / Consolidation & Réconciliation
- Extraction de la logique de consolidation IFRS
- Extraction de la logique de réconciliation compta-risque
- Tests ≥80% de couverture

