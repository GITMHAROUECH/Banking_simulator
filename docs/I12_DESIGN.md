# I12 - IFRS 9 ECL Avancé - Document de Conception

**Version** : 1.0  
**Date** : 2025-11-03  
**Auteur** : Manus AI

---

## 🎯 Objectif

Implémenter un calcul avancé d'Expected Credit Loss (ECL) selon IFRS 9 avec :
- **Staging S1/S2/S3** (SICR, backstop, default)
- **PD term structures** (courbes PD sur horizons 1-60 mois)
- **LGD downturn** avec floors par asset class
- **Pré-remplissage FINREP F09/F18** depuis les résultats ECL

---

## 📐 Architecture IFRS 9

### 1. Staging (S1/S2/S3)

#### Stage 1 : Performing (12-month ECL)
- **Critère** : Pas de SICR (Significant Increase in Credit Risk)
- **ECL** : 12 mois
- **Formule** : `ECL = EAD × PD_12m × LGD × DF`

#### Stage 2 : Underperforming (Lifetime ECL)
- **Critère** : SICR détecté
- **Règles SICR** :
  - ΔPD > seuil (ex: +100 bps ou +100% relatif)
  - Backstop 30 jours (DPD > 30)
  - Forbearance flags
- **ECL** : Lifetime (horizon complet, ex: 60 mois)
- **Formule** : `ECL = Σ_t EAD_t × PD_t × LGD × DF_t`

#### Stage 3 : Non-performing (Lifetime ECL)
- **Critère** : Default (DPD > 90 jours)
- **ECL** : Lifetime avec LGD downturn
- **Formule** : `ECL = EAD × LGD_downturn × DF`

### 2. PD Term Structure

#### Approches supportées

**A. Transition Matrix** (si disponible)
```
PD_t = 1 - (1 - PD_1y)^t  # Approximation simple
```

**B. Beta Distribution** (proxy rating)
```
PD_t = Beta(α, β, t/T)  # α, β calibrés par rating
```

**C. Scenario Overlays**
```
PD_t = PD_base_t × (1 + overlay_shift_t)
```

#### Horizons
- **Stage 1** : 12 mois
- **Stage 2/3** : Lifetime (paramétrable, défaut 60 mois)

### 3. LGD Downturn

#### Floors par Asset Class
| Asset Class | LGD Floor (%) |
|-------------|---------------|
| Sovereign   | 20%           |
| Corporate   | 30%           |
| Retail      | 40%           |
| SME         | 45%           |
| Real Estate | 25%           |

#### Haircuts Collatéraux
```
LGD_downturn = max(LGD_base, LGD_floor) × (1 + haircut_stress)
```

### 4. EAD Projection

#### Loans/Bonds (Amortizing)
```
EAD_t = Notional × (1 - amortization_rate)^t
```

#### Off-Balance Sheet
```
EAD_t = Notional × CCF_bucket
```

#### Revolving (Credit Cards)
```
EAD_t = max(Outstanding, Limit × CCF)
```

### 5. Discount Factor

#### Approches
**A. Effective Interest Rate (EIR)**
```
DF_t = 1 / (1 + EIR)^t
```

**B. Risk-Free Rate + Spread**
```
DF_t = 1 / (1 + (RFR + spread))^t
```

**C. Market Proxy**
```
DF_t = 1 / (1 + market_rate)^t
```

---

## 🗄️ Schéma DB

### Table `ecl_results`

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID | Clé primaire |
| run_id | VARCHAR(50) | Run source |
| scenario_id | VARCHAR(50) | Scénario overlay |
| exposure_id | INTEGER | FK vers exposures |
| stage | VARCHAR(2) | S1, S2, S3 |
| pd_12m | FLOAT | PD 12 mois (%) |
| pd_lifetime | FLOAT | PD lifetime (%) |
| lgd | FLOAT | LGD utilisée (%) |
| ead | FLOAT | EAD (montant) |
| ecl_amount | FLOAT | ECL calculée |
| ecl_currency | VARCHAR(3) | Devise |
| segment_id | VARCHAR(50) | Segment (Retail/Corporate/...) |
| calculation_date | TIMESTAMP | Date calcul |
| created_at | TIMESTAMP | Date création |

**Indexes** :
- `(run_id, scenario_id)`
- `(exposure_id)`
- `(stage)`

### Table `scenario_overlays`

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID | Clé primaire |
| scenario_id | VARCHAR(50) | Identifiant scénario |
| name | VARCHAR(200) | Nom scénario |
| description | TEXT | Description |
| pd_shift | FLOAT | Shift PD (bps) |
| lgd_floor_by_class | JSONB | Floors LGD par classe |
| sicr_threshold_abs | FLOAT | Seuil SICR absolu (bps) |
| sicr_threshold_rel | FLOAT | Seuil SICR relatif (%) |
| backstop_days | INTEGER | Backstop jours (défaut 30) |
| discount_rate_mode | VARCHAR(20) | EIR, RFR, Market |
| discount_rate_value | FLOAT | Taux si fixe (%) |
| horizon_months | INTEGER | Horizon lifetime (mois) |
| created_at | TIMESTAMP | Date création |

---

## 🔧 Implémentation Domain

### Module `src/domain/ifrs9/ecl.py`

#### Fonction 1 : Staging
```python
def determine_stage(
    exposure: dict,
    pd_current: float,
    pd_origination: float,
    dpd: int,
    forbearance: bool,
    sicr_threshold_abs: float = 1.0,  # 100 bps
    sicr_threshold_rel: float = 1.0,  # 100%
    backstop_days: int = 30,
) -> str:
    """
    Détermine le stage IFRS 9.
    
    Returns:
        'S1', 'S2', ou 'S3'
    """
```

#### Fonction 2 : PD Term Structure
```python
def compute_pd_curve(
    pd_1y: float,
    horizon_months: int,
    method: str = 'simple',  # 'simple', 'beta', 'overlay'
    scenario_overlay: dict | None = None,
) -> np.ndarray:
    """
    Calcule la courbe PD sur l'horizon.
    
    Returns:
        Array de PD_t pour t=1..horizon_months
    """
```

#### Fonction 3 : LGD Downturn
```python
def compute_lgd_downturn(
    lgd_base: float,
    asset_class: str,
    lgd_floors: dict[str, float],
    haircut_stress: float = 0.0,
) -> float:
    """
    Calcule LGD downturn avec floor.
    
    Returns:
        LGD ajustée (%)
    """
```

#### Fonction 4 : EAD Projection
```python
def project_ead(
    notional: float,
    product_type: str,
    maturity_months: int,
    horizon_months: int,
    ccf: float = 1.0,
) -> np.ndarray:
    """
    Projette EAD sur l'horizon.
    
    Returns:
        Array de EAD_t pour t=1..horizon_months
    """
```

#### Fonction 5 : ECL Calculation
```python
def compute_ecl_single_exposure(
    exposure: dict,
    pd_curve: np.ndarray,
    lgd: float,
    ead_curve: np.ndarray,
    discount_rates: np.ndarray,
    stage: str,
) -> dict:
    """
    Calcule ECL pour une exposition.
    
    Returns:
        {
            'ecl_amount': float,
            'ecl_12m': float,
            'ecl_lifetime': float,
            'stage': str,
        }
    """
```

---

## 🔌 Services

### `src/services/ifrs9_service.py`

```python
def compute_ecl_advanced(
    run_id: str,
    scenario_id: str,
    *,
    horizon_months: int = 12,
    use_cache: bool = True,
) -> tuple[dict, bool]:
    """
    Calcule ECL avancé pour un run_id + scenario_id.
    
    Returns:
        ({
            'by_exposure': DataFrame,
            'by_segment': DataFrame,
            'totals': DataFrame,
            'stage_mix': dict,
        }, cache_hit)
    """
```

---

## 📊 FINREP

### F09 : Impairment

| Colonne | Description |
|---------|-------------|
| Asset Class | Sovereign, Corporate, Retail, etc. |
| Stage 1 ECL | ECL 12 mois |
| Stage 2 ECL | ECL lifetime (SICR) |
| Stage 3 ECL | ECL lifetime (default) |
| Total ECL | Somme |

### F18 : Breakdown of Loans

| Colonne | Description |
|---------|-------------|
| Loan Segment | Retail, Corporate, SME, etc. |
| Gross Carrying Amount | Notional |
| ECL Allowance | ECL totale |
| Net Carrying Amount | Notional - ECL |

---

## ✅ Validation

### Tests Unitaires

1. **Staging** : SICR détecté correctement
2. **PD Curve** : Monotonicité (PD_t croissante)
3. **LGD Downturn** : Floors appliqués
4. **ECL** : Monotonicité (↑PD/LGD ⇒ ↑ECL)

### Tests d'Intégration

1. **Round-trip** : run_id + scenario_id → persist → reload
2. **Cache** : 2e run = cache_hit=True
3. **FINREP** : F09/F18 non vides, totaux cohérents

### Tests de Performance

- **50k expositions, horizon 12m** : ≤ 2.5s (vectorisé)
- **50k expositions, horizon 60m** : ≤ 10s (vectorisé)

---

## 📝 Limites v1

1. **PD Curve** : Approche simple (pas de transition matrix complète)
2. **Collateral** : Haircuts simplifiés (pas de valorisation dynamique)
3. **Prepayment** : Non modélisé
4. **Macro Scenarios** : Overlays manuels (pas de modèle économétrique)
5. **POCI** : Non supporté (Purchased or Originated Credit-Impaired)

---

## 🚀 Extensions Futures (I13+)

1. **Transition Matrix** complète par rating
2. **Collateral Valuation** dynamique avec LTV
3. **Prepayment Models** (CPR/SMM)
4. **Macro Scenarios** automatisés (GDP, unemployment, etc.)
5. **POCI** support
6. **Multi-currency** ECL avec FX risk

---

**Fin du document de conception I12**

