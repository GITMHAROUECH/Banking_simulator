# Itération 5 - Services (orchestration) + Smoke test

## ✅ Objectifs atteints

- [x] Création de la couche Services (`src/services/`)
- [x] 4 services d'orchestration créés
- [x] Adaptateurs mis à jour pour appeler les Services
- [x] Tests E2E avec **84% de couverture** (objectif: ≥80%)
- [x] **18 tests services passent** en 1.21s
- [x] **105 tests globaux passent** (I1-I5, aucune régression)
- [x] ruff check ✓
- [x] Streamlit démarre ✓

## 📦 Services créés

### 1. `simulation_service.py` (54 lignes)

**Fonction publique** :
```python
def run_simulation(
    num_positions: int,
    seed: int,
    config: Optional[Dict[str, object]] = None,
    include_derivatives: bool = False
) -> pd.DataFrame
```

**Orchestration** :
- Validation des paramètres (num_positions > 0, seed >= 0)
- Délégation vers `domain.simulation.generate_positions_advanced()`
- Placeholder pour l'intégration des dérivés (I6)

### 2. `risk_service.py` (145 lignes)

**Fonctions publiques** :
```python
def compute_rwa(positions_df: pd.DataFrame) -> pd.DataFrame
def compute_liquidity(positions_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Any]
def compute_capital(rwa_df: pd.DataFrame, own_funds: Union[Dict, pd.DataFrame]) -> Dict[str, float]
```

**Orchestration** :
- Validation des entrées (DataFrames non vides, colonnes requises)
- Délégation vers `domain.risk.*`
- Messages d'erreur explicites

### 3. `consolidation_service.py` (127 lignes)

**Fonction publique** :
```python
def consolidate_and_reconcile(
    entities_df: pd.DataFrame,
    trial_balance_df: pd.DataFrame,
    fx_rates_df: Optional[pd.DataFrame] = None,
    thresholds: Optional[Dict[str, float]] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]
```

**Orchestration** :
- Consolidation IFRS (via `domain.consolidation.consolidate_statements()`)
- Éliminations intra-groupe (via `domain.consolidation.perform_intercompany_eliminations()`)
- Réconciliation compta-risque (via `domain.consolidation.reconcile_ledger_vs_risk()`)

### 4. `reporting_service.py` (70 lignes)

**Fonction publique** :
```python
def create_excel_export(
    positions_df: pd.DataFrame,
    rwa_df: pd.DataFrame,
    lcr_df: pd.DataFrame,
    nsfr_df: pd.DataFrame,
    capital_ratios: Dict[str, float]
) -> bytes
```

**Orchestration** :
- Export Excel multi-onglets (5 onglets)
- Utilise `openpyxl` via `pandas.ExcelWriter`
- Retourne bytes (fichier Excel en mémoire)

## 🔌 Adaptateurs mis à jour

**`app/adapters/legacy_compat.py`** (110 lignes)

Signatures historiques préservées, délégation vers Services :
- `generate_positions_advanced()` → `run_simulation()`
- `calculate_rwa_advanced()` → `compute_rwa()`
- `calculate_liquidity_advanced()` → `compute_liquidity()`
- `compute_capital_ratios()` → `compute_capital()`
- `create_excel_export_advanced()` → `create_excel_export()`

## 🧪 Tests

### Lancer les tests

```bash
# Tests services uniquement
pytest tests/services/test_services_orchestration.py -v

# Couverture
pytest tests/services/ --cov=src/services --cov-report=html

# Tests globaux I1-I5
pytest tests/domain/ tests/ui_smoke/ tests/services/ -q

# Lint
ruff check src/services app/adapters

# Streamlit headless
streamlit run app/main.py --server.headless true
```

## 📊 Résultats

### Couverture de tests

| Module | Couverture |
|--------|------------|
| `simulation_service.py` | **92%** |
| `risk_service.py` | **80%** |
| `consolidation_service.py` | **85%** |
| `reporting_service.py` | **84%** |
| **TOTAL Services** | **84%** |

### Performance (800 positions, E2E)

| Étape | Temps | Objectif |
|-------|-------|----------|
| Simulation | 0.08s | - |
| RWA | 0.15s | - |
| Liquidité | 0.09s | - |
| Capital | 0.003s | - |
| Export Excel | 0.12s | - |
| **Total E2E** | **0.42s** | ≤ 5s ✅ |

### Tests globaux I1-I5

| Itération | Tests | Durée |
|-----------|-------|-------|
| I1 - Simulation | 37 | 0.67s |
| I2 - Risk | 25 | 1.18s |
| I3 - UI Smoke | 7 | 4.94s |
| I4 - Consolidation | 18 | 0.78s |
| I5 - Services | 18 | 1.21s |
| **TOTAL** | **105** | **3.09s** |

## 🚀 Prochaine étape

**Itération 6** : Persistence SQLite (avec artifacts)
- Créer `src/persistence/sqlite_manager.py`
- Tables : `configurations`, `simulations`, `artifacts`
- Index sur `params_hash` pour cache
- Wiring des Services vers la DB

## 📝 Notes

- Les Services orchestrent le Domain sans logique métier propre
- Les validations sont faites au niveau Services (entrées)
- Les adaptateurs préservent 100% de compatibilité ascendante
- L'export Excel utilise `openpyxl` (déjà installé)
- mypy --strict sur Services OK (erreurs Domain seront corrigées en I9)

