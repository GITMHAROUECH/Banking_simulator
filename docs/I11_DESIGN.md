# I11 - Design Document : Run ID Pipeline

**Date** : 2025-11-03  
**Version** : 0.9.0  
**Auteur** : Manus AI

---

## 1. Objectif

Recentrer l'application sur une **simulation source** avec propagation du même `run_id` dans tout le pipeline :
- Génération d'expositions paramétrables (MVP multi-produits)
- Consolidation
- Risques (crédit, contrepartie, liquidité, capital)
- Réconciliation
- Pré-remplissage COREP/FINREP

**Contrainte** : Aucune régression I1-I8.

---

## 2. Architecture Cible

### 2.1. Schéma Canonique `exposures`

Table centrale contenant toutes les expositions générées pour un `run_id` :

```sql
CREATE TABLE exposures (
    id VARCHAR(36) PRIMARY KEY,           -- UUID
    run_id VARCHAR(36) NOT NULL,          -- Clé de regroupement
    product_type VARCHAR(50) NOT NULL,    -- Loan, Bond, Derivative, etc.
    counterparty_id VARCHAR(50),
    booking_date DATE,
    maturity_date DATE,
    currency VARCHAR(3),
    notional DECIMAL(20, 2),
    ead DECIMAL(20, 2),                   -- Exposure at Default
    pd DECIMAL(10, 6),                    -- Probability of Default
    lgd DECIMAL(10, 6),                   -- Loss Given Default
    ccf DECIMAL(10, 6),                   -- Credit Conversion Factor
    maturity_years DECIMAL(10, 2),
    mtm DECIMAL(20, 2),                   -- Mark-to-Market
    desk VARCHAR(50),
    entity VARCHAR(50),
    is_retail BOOLEAN,
    exposure_class VARCHAR(50),           -- Corporate, Sovereign, Bank, Retail
    netting_set_id VARCHAR(50),           -- Pour dérivés
    collateral_value DECIMAL(20, 2),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_exposures_run_id ON exposures(run_id);
CREATE INDEX idx_exposures_product_type ON exposures(product_type);
CREATE INDEX idx_exposures_entity ON exposures(entity);
```

### 2.2. Table `simulation_runs`

Métadonnées des runs de simulation :

```sql
CREATE TABLE simulation_runs (
    run_id VARCHAR(36) PRIMARY KEY,
    params_hash VARCHAR(64) NOT NULL,     -- Lien vers configurations
    run_date TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20),                   -- pending, completed, failed
    total_exposures INTEGER,
    total_notional DECIMAL(20, 2),
    config_json TEXT,                     -- Snapshot config
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2.3. Table `balance_sheet_snapshots`

Snapshots de bilan par run_id :

```sql
CREATE TABLE balance_sheet_snapshots (
    id VARCHAR(36) PRIMARY KEY,
    run_id VARCHAR(36) NOT NULL,
    item_type VARCHAR(20),                -- asset, liability
    category VARCHAR(50),                 -- loans, bonds, deposits, etc.
    entity VARCHAR(50),
    currency VARCHAR(3),
    amount DECIMAL(20, 2),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_bs_run_id ON balance_sheet_snapshots(run_id);
```

---

## 3. Générateurs Multi-Produits (MVP)

### 3.1. Produits Couverts

1. **Loans** : Prêts corporate/retail
2. **Bonds** : Obligations détenues
3. **Deposits** : Dépôts clients
4. **Derivatives** : Dérivés avec netting sets
5. **Off-BS** : Engagements hors-bilan (commitments, guarantees)
6. **Equities** : Actions détenues

### 3.2. Générateurs

Chaque générateur = classe dédiée dans `src/domain/simulation/generators/` :

```python
# src/domain/simulation/generators/loans.py
def generate_loans(config: dict, seed: int) -> pd.DataFrame:
    """Génère des prêts avec distribution réaliste."""
    # Retourne DataFrame avec colonnes exposures
    pass

# src/domain/simulation/generators/bonds.py
def generate_bonds(config: dict, seed: int) -> pd.DataFrame:
    pass

# ... idem pour deposits, derivatives, off_bs, equities
```

### 3.3. Orchestrateur

```python
# src/domain/simulation/exposure_generator.py
def generate_all_exposures(run_id: str, config: dict, seed: int) -> pd.DataFrame:
    """Génère toutes les expositions pour un run_id."""
    dfs = []
    dfs.append(generate_loans(config, seed))
    dfs.append(generate_bonds(config, seed + 1))
    dfs.append(generate_deposits(config, seed + 2))
    dfs.append(generate_derivatives(config, seed + 3))
    dfs.append(generate_off_bs(config, seed + 4))
    dfs.append(generate_equities(config, seed + 5))
    
    df = pd.concat(dfs, ignore_index=True)
    df['run_id'] = run_id
    df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
    return df
```

---

## 4. Services Layer

### 4.1. Simulation Service

```python
# src/services/simulation_service.py
def generate_exposures(run_id: str, config: dict | None = None, use_cache: bool = True) -> tuple[pd.DataFrame, bool]:
    """Génère les exposures pour un run_id."""
    # 1. Calculer params_hash
    # 2. Vérifier cache
    # 3. Si cache miss : générer via domain
    # 4. Sauvegarder en DB (table exposures)
    # 5. Retourner (df, cache_hit)
    pass

def load_exposures(run_id: str) -> pd.DataFrame:
    """Charge les exposures depuis la DB."""
    pass

def snapshot_balance_sheet(run_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Crée un snapshot bilan (assets, liabilities)."""
    # Agrège exposures par catégorie
    pass
```

### 4.2. Risk Service (Adaptation)

```python
# src/services/risk_service.py
def compute_rwa_from_run(run_id: str, params: dict | None = None) -> tuple[dict, bool]:
    """Calcule RWA à partir d'un run_id."""
    # 1. Charger exposures(run_id)
    # 2. Filtrer/transformer selon params
    # 3. Appeler compute_rwa_standardized() existant
    # 4. Retourner (result, cache_hit)
    pass

def compute_saccr_from_run(run_id: str, params: dict | None = None) -> tuple[dict, bool]:
    """Calcule SA-CCR à partir d'un run_id."""
    # Filtre product_type='Derivative'
    pass

def compute_lcr_from_run(run_id: str, params: dict | None = None) -> tuple[dict, bool]:
    """Calcule LCR à partir d'un run_id."""
    pass
```

### 4.3. Reconciliation Service

```python
# src/services/reconciliation_service.py
def reconcile_ledger_vs_risk(run_id: str) -> pd.DataFrame:
    """Réconcilie bilan vs agrégats risques."""
    # 1. Charger balance_sheet_snapshots(run_id)
    # 2. Charger résultats risques (RWA, SA-CCR, etc.)
    # 3. Comparer par classe/entité/devise
    # 4. Retourner DataFrame avec écarts
    pass
```

### 4.4. Reporting Service (Pré-remplissage)

```python
# src/services/reporting_service.py
def create_corep_finrep_stubs(run_id: str) -> dict:
    """Pré-remplit COREP/FINREP à partir d'un run_id."""
    # COREP C34 : Agrégation exposures par exposure_class
    # COREP C07/C08 : Détails IRB/SA
    # COREP Leverage : Total exposure vs Tier1
    # COREP LCR : HQLA vs Net Cash Outflows
    # FINREP F01 : Bilan à partir de balance_sheet_snapshots
    # FINREP F18 : Détail prêts
    pass
```

---

## 5. Flux de Données

```mermaid
graph TD
    A[UI: Bouton "Lancer Simulation E2E"] --> B[generate_exposures(run_id, config)]
    B --> C[Générateurs Multi-Produits]
    C --> D[Table exposures]
    D --> E[snapshot_balance_sheet(run_id)]
    E --> F[Table balance_sheet_snapshots]
    D --> G[compute_rwa_from_run(run_id)]
    D --> H[compute_saccr_from_run(run_id)]
    D --> I[compute_lcr_from_run(run_id)]
    G --> J[Résultats Risques]
    H --> J
    I --> J
    F --> K[reconcile_ledger_vs_risk(run_id)]
    J --> K
    K --> L[Écarts]
    D --> M[create_corep_finrep_stubs(run_id)]
    J --> M
    M --> N[Rapports COREP/FINREP]
```

---

## 6. UI Changes

### 6.1. Page Pipeline

Nouveau bouton **"Lancer Simulation E2E"** :
1. Génère un `run_id` unique (UUID)
2. Appelle `generate_exposures(run_id, config)`
3. Enchaîne automatiquement :
   - `snapshot_balance_sheet(run_id)`
   - `compute_rwa_from_run(run_id)`
   - `compute_saccr_from_run(run_id)`
   - `compute_lcr_from_run(run_id)`
   - `compute_capital_ratios_from_run(run_id)`
   - `reconcile_ledger_vs_risk(run_id)`
   - `create_corep_finrep_stubs(run_id)`
4. Affiche récap KPIs + liens vers pages dédiées

### 6.2. Page Analyse Portfolio

Drill-down minimal par `run_id` :
- Sélecteur `run_id` (liste des runs disponibles)
- Filtres : product_type, entity, currency
- Tableau exposures filtrées
- Export CSV/Parquet

---

## 7. Migrations Alembic

### 7.1. Migration `create_exposures_table`

```python
# alembic/versions/xxx_create_exposures_table.py
def upgrade():
    op.create_table(
        'exposures',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('run_id', sa.String(36), nullable=False, index=True),
        sa.Column('product_type', sa.String(50), nullable=False),
        # ... autres colonnes
    )
```

### 7.2. Migration `create_simulation_runs_table`

### 7.3. Migration `create_balance_sheet_snapshots_table`

---

## 8. Tests

### 8.1. Tests Générateurs

```python
# tests/domain/test_exposure_generators.py
def test_generate_loans_distribution():
    """Vérifie distribution notional, PD, LGD."""
    pass

def test_generate_loans_seed_reproducibility():
    """Vérifie reproductibilité avec même seed."""
    pass

def test_generate_all_exposures_size():
    """Vérifie taille totale (50k lignes < 5s)."""
    pass
```

### 8.2. Tests Pipeline E2E

```python
# tests/services/test_pipeline_e2e.py
def test_pipeline_e2e_two_runs():
    """Vérifie 2 runs indépendants."""
    run_id1 = str(uuid.uuid4())
    run_id2 = str(uuid.uuid4())
    
    df1, _ = generate_exposures(run_id1, config)
    df2, _ = generate_exposures(run_id2, config)
    
    assert len(df1) > 0
    assert len(df2) > 0
    assert df1['run_id'].unique()[0] == run_id1
    assert df2['run_id'].unique()[0] == run_id2
```

### 8.3. Tests Pré-remplissage COREP/FINREP

```python
# tests/services/test_reporting_stubs.py
def test_create_corep_c34_not_empty():
    """Vérifie que COREP C34 est pré-rempli."""
    run_id = create_test_run()
    stubs = create_corep_finrep_stubs(run_id)
    
    assert 'corep_c34' in stubs
    assert len(stubs['corep_c34']) > 0
```

### 8.4. Tests Cache

```python
# tests/services/test_cache_run_id.py
def test_generate_exposures_cache_hit():
    """Vérifie cache hit au 2e run."""
    run_id = str(uuid.uuid4())
    config = {...}
    
    df1, hit1 = generate_exposures(run_id, config)
    df2, hit2 = generate_exposures(run_id, config)
    
    assert not hit1  # Cache miss
    assert hit2      # Cache hit
```

---

## 9. Performance

### 9.1. Objectifs

- **50k expositions** toutes classes < 5s (dev)
- **Mémoire stable** (pas de fuites)
- **Cache actif** : speedup 50-150x

### 9.2. Optimisations

- Utiliser `numpy` pour génération vectorielle
- Batch inserts en DB (SQLAlchemy bulk_insert_mappings)
- Indexation appropriée (run_id, product_type, entity)

---

## 10. Compatibilité Ascendante

### 10.1. Garde-fous

- ✅ Tous les tests I1-I8 doivent passer
- ✅ Pas de changement des signatures publiques existantes
- ✅ UI → Adapters → Services (jamais UI → Domain)
- ✅ Cache I6 conservé via params_hash

### 10.2. Stratégie

- Ajouter nouvelles fonctions `*_from_run()` sans toucher aux existantes
- Adapters exposent les deux versions (legacy + run_id)
- UI peut choisir entre ancien workflow et nouveau workflow E2E

---

## 11. Documentation

### 11.1. README_I11_runid_pipeline.md

- Diagramme flux complet
- Exemples d'utilisation
- Guide migration legacy → run_id

### 11.2. CHANGELOG.md

Ajouter section I11 avec :
- Schéma exposures
- Générateurs multi-produits
- Pipeline E2E
- Pré-remplissage COREP/FINREP

---

## 12. Limitations (Hors Scope I11)

- ❌ ALM avancé (gap analysis détaillé)
- ❌ Risque de marché (VaR, stress tests)
- ❌ Risque opérationnel
- ❌ Calculs COREP/FINREP complets (seulement stubs pré-remplis)

Ces fonctionnalités feront l'objet d'itérations futures (I12+).

---

## 13. Timeline

| Phase | Durée | Statut |
|-------|-------|--------|
| 1. Analyse & Design | 1h | ✅ |
| 2. Schéma DB + Migrations | 1h | ⏳ |
| 3. Générateurs MVP | 2h | ⏳ |
| 4. Adaptation Services | 2h | ⏳ |
| 5. Réconciliation | 1h | ⏳ |
| 6. Pré-remplissage COREP/FINREP | 1h | ⏳ |
| 7. UI Pipeline E2E | 1h | ⏳ |
| 8. Tests + Validation | 2h | ⏳ |

**Total estimé** : ~11h

---

**Statut** : ✅ Design validé, prêt pour implémentation

