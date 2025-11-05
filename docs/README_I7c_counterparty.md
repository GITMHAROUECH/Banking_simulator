# I7c - Contrepartie : Unifier SA-CCR & CVA

**Date**: 28 octobre 2025  
**Version**: 0.7.3  
**Statut**: ✅ Complété

---

## 🎯 Objectif

Unifier le **risque de contrepartie** en intégrant **SA-CCR** (I7b) et **CVA** (Credit Valuation Adjustment) dans un agrégateur unique avec :
- **BA-CVA** (Basic Approach for CVA Capital) selon CRR3 Article 384
- **CVA Pricing v1** (approche simplifiée)
- **Page UI Contrepartie** unifiée avec 4 onglets
- **Cache I6** actif sur tous les calculs
- **Aucune régression** I1-I7b

---

## 📋 Fonctionnalités Implémentées

### 1. BA-CVA (Capital CVA)

Nouveau calcul dans `src/domain/risk/counterparty.py` :

```python
from src.domain.risk.counterparty import compute_cva_capital_ba

result = compute_cva_capital_ba(ead_df, params)

# Résultat
{
    "k_cva": 123456.78,  # Capital CVA total
    "by_counterparty": pd.DataFrame(...)  # Détails par contrepartie
}
```

**Formule BA-CVA** (CRR3 Article 384) :

```
K_CVA = 2.33 × sqrt(Σ_i (w_i × M_i × EAD_i)²)
```

où :
- **w_i** = poids de la contrepartie (proxy rating/spread bucket)
- **M_i** = maturité effective (en années)
- **EAD_i** = Exposure At Default de la contrepartie

### 2. CVA Pricing v1 (Simplified)

Nouveau calcul dans `src/domain/risk/counterparty.py` :

```python
from src.domain.risk.counterparty import compute_cva_pricing_v1

result = compute_cva_pricing_v1(trades_df, params)

# Résultat
{
    "cva": 98765.43,  # CVA total
    "by_bucket": pd.DataFrame(...)  # Détails par bucket de temps
}
```

**Formule CVA Pricing** :

```
CVA ≈ (1 - R) × Σ_t DF(t) × ΔPD(t) × EE(t)
```

où :
- **R** = Recovery Rate (taux de recouvrement)
- **DF(t)** = Discount Factor au temps t = exp(-r × t)
- **ΔPD(t)** = Probabilité de défaut incrémentale sur [t-1, t]
- **EE(t)** = Expected Exposure au temps t (proxy depuis EAD SA-CCR)

**Simplifications v1** :
- EE(t) constant = EAD (profil plat)
- ΔPD(t) via hazard rate constant (λ = spread / LGD)
- DF(t) = exp(-r × t) avec r = taux sans risque

### 3. Agrégateur Risque Contrepartie

Nouveau service dans `src/services/risk_service.py` :

```python
from src.services import compute_counterparty_risk

result, cache_hit = compute_counterparty_risk(
    trades_df,
    collateral_df=None,
    params={
        "alpha": 1.4,
        "enable_cva_pricing": True,
        "cva_params": {
            "recovery_rate": 0.4,
            "risk_free_rate": 0.02,
        },
    },
    use_cache=True
)

# Résultat agrégé
{
    "saccr": {
        "ead_df": pd.DataFrame(...),
        "rc": 10000.0,
        "pfe": 50000.0,
        "pfe_addons": {...},
        "multiplier": 0.95,
        "alpha": 1.4,
        "rwa": 123456.78,
        "k": 1.0
    },
    "cva_capital": {
        "k_cva": 123456.78,
        "by_counterparty": pd.DataFrame(...)
    },
    "cva_pricing": {  # None si désactivé
        "cva": 98765.43,
        "by_bucket": pd.DataFrame(...)
    }
}
```

### 4. Page UI Contrepartie

Page unifiée **🔁 Contrepartie** (`app/pages/14_🔁_Contrepartie.py`) avec :

- **Upload fichier** : CSV/XLSX de trades
- **Génération démo** : Portefeuille synthétique (10-20k trades)
- **Paramètres SA-CCR** : Alpha personnalisable
- **Paramètres CVA** : Recovery rate, taux sans risque, toggle CVA pricing
- **Cache** : Affichage cache_hit (✅/❌)
- **4 onglets** :
  1. **📊 SA-CCR** : EAD, RC, PFE, multiplier, add-ons par classe
  2. **💰 CVA Capital** : K_CVA, détails par contrepartie, formule BA-CVA
  3. **📈 CVA Pricing** : CVA, détails par bucket de temps, graphique
  4. **📥 Export** : Download CSV (SA-CCR, CVA Capital, CVA Pricing) et JSON global

---

## 🚀 Quickstart

### Lancer l'Application

```bash
cd /home/ubuntu/AUDIT_COMPLET_BANKING_APP
./run_app.sh
```

### Utilisation

1. Cliquez sur **🔁 Contrepartie** dans la sidebar
2. **Option 1** : Upload fichier CSV/XLSX de trades
3. **Option 2** : Générer portefeuille démo (100 trades, seed 42)
4. Configurez les paramètres :
   - **Alpha** : 1.4 (défaut)
   - **Recovery Rate** : 0.4 (défaut)
   - **Taux sans risque** : 0.02 (défaut)
   - **Activer CVA Pricing v1** : Cocher pour activer
5. Cliquez sur **Calculer Risque Contrepartie**
6. Observez le cache_hit (❌ au 1er run, ✅ au 2ème)
7. Explorez les 4 onglets de résultats
8. Téléchargez les exports (CSV, JSON)

### Format de Fichier Attendu

Même format que SA-CCR (I7b) :

| Colonne | Type | Description |
|---------|------|-------------|
| trade_id | str | Identifiant unique du trade |
| netting_set | str | Identifiant du netting set (CSA) |
| asset_class | str | Classe d'actifs (IR, FX, Equity, Commodity, Credit) |
| notional | float | Notionnel du trade |
| mtm | float | Mark-to-Market (positif = créance, négatif = dette) |
| maturity_bucket | str | Bucket de maturité pour IR (0-1Y, 1-5Y, >5Y) [optionnel] |
| rating | str | Rating pour Credit (IG, HY) [optionnel] |

---

## 📊 Tests

### Tests CVA Capital

8 tests dans `tests/services/test_counterparty_cva_capital.py` :

```bash
pytest tests/services/test_counterparty_cva_capital.py -v
# ✅ 8 tests passent
```

**Couverture** :
- ✅ Calcul CVA capital basique
- ✅ Monotonicité (↑EAD ⇒ ↑K_CVA)
- ✅ Multiples contreparties
- ✅ Paramètres par défaut et personnalisés
- ✅ Cache hit/miss
- ✅ Validations (EAD vide, colonnes manquantes)

### Tests CVA Pricing

8 tests dans `tests/services/test_counterparty_cva_pricing.py` :

```bash
pytest tests/services/test_counterparty_cva_pricing.py -v
# ✅ 8 tests passent
```

**Couverture** :
- ✅ Calcul CVA pricing basique
- ✅ Sensibilité LGD (↑LGD ⇒ ↑CVA)
- ✅ Sensibilité horizon (↑maturité ⇒ ↑CVA)
- ✅ Sensibilité spread (↑spread ⇒ ↑CVA)
- ✅ Multiples contreparties
- ✅ Cache hit/miss
- ✅ Validations (trades vide, colonnes manquantes)

### Tests Agrégateur

7 tests dans `tests/services/test_counterparty_aggregate.py` :

```bash
pytest tests/services/test_counterparty_aggregate.py -v
# ✅ 7 tests passent
```

**Couverture** :
- ✅ Calcul risque contrepartie basique
- ✅ Avec CVA pricing activé
- ✅ Toutes les clés présentes (SA-CCR + CVA)
- ✅ Cache hit/miss (2ᵉ run → cache_hit=True)
- ✅ Multiples netting sets
- ✅ Validations (trades vide, colonnes manquantes)

### Tests UI Smoke

2 tests dans `tests/ui_smoke/test_counterparty_page.py` :

```bash
pytest tests/ui_smoke/test_counterparty_page.py -v
# ✅ 2 tests passent
```

### Tous les Tests

```bash
pytest tests/ -q
# ✅ 241 tests passent (4 échecs legacy pré-existants)
```

---

## 📈 Métriques Globales

| Métrique | I7b | I7c | Évolution |
|----------|-----|-----|-----------|
| Pages Streamlit | 14 | 14 | = |
| Tests CVA | 0 | 23 | **+23** |
| Tests Total | 218 | 241 | **+23** |
| Lignes de code | 6 400 | 7 200 | **+800** |
| Fonctions Services | 12 | 15 | **+3** |

---

## 🔧 Architecture

### Flux Risque Contrepartie

```
User Input (Upload CSV ou Génération Démo)
    ↓
app/pages/14_🔁_Contrepartie.py
    ↓
src/services/risk_service.py (compute_counterparty_risk)
    ↓
    ├─→ compute_saccr_ead / compute_saccr_rwa (SA-CCR)
    ├─→ compute_cva_capital (BA-CVA)
    └─→ compute_cva_pricing (CVA Pricing v1, si activé)
    ↓
src/domain/risk/counterparty.py
    ├─→ compute_saccr_ead_detailed (SA-CCR)
    ├─→ compute_cva_capital_ba (BA-CVA)
    └─→ compute_cva_pricing_v1 (CVA Pricing)
    ↓
db/models.py (persistance cache I6)
```

### Nouveaux Fichiers I7c

- `src/domain/risk/counterparty.py` : Ajout BA-CVA et CVA Pricing v1
- `src/services/risk_service.py` : Ajout compute_cva_capital, compute_cva_pricing, compute_counterparty_risk
- `app/adapters/legacy_compat.py` : Ajout adaptateurs CVA
- `app/pages/14_🔁_Contrepartie.py` : Page unifiée (renommée depuis Dérivés)
- `tests/services/test_counterparty_cva_capital.py` : Tests CVA capital
- `tests/services/test_counterparty_cva_pricing.py` : Tests CVA pricing
- `tests/services/test_counterparty_aggregate.py` : Tests agrégateur
- `tests/ui_smoke/test_counterparty_page.py` : Tests UI smoke

---

## 🎯 Prochaines Étapes (I8-I10)

### I8 - Export Avancé

- Export Parquet natif (sans Excel)
- Export JSON/CSV pour interopérabilité
- Compression gzip pour exports volumineux
- Sélection colonnes à exporter

### I9 - Qualité Globale

- mypy --strict sur Domain
- Couverture >80% globale
- Optimisations performance supplémentaires
- Documentation API complète

### I10 - Documentation & CI/CD

- ARCHITECTURE.md complet (diagrammes C4)
- README_RUN.md détaillé
- GitHub Actions CI/CD
- Déploiement automatique

---

## 📝 Changelog I7c

### Ajouté

- ✅ BA-CVA (capital CVA) dans Domain (`compute_cva_capital_ba`)
- ✅ CVA Pricing v1 dans Domain (`compute_cva_pricing_v1`)
- ✅ Service CVA capital (`compute_cva_capital`)
- ✅ Service CVA pricing (`compute_cva_pricing`)
- ✅ Agrégateur risque contrepartie (`compute_counterparty_risk`)
- ✅ Adaptateurs CVA (`calculate_cva_capital_advanced`, `calculate_cva_pricing_advanced`, `calculate_counterparty_risk_advanced`)
- ✅ Page UI Contrepartie unifiée (4 onglets : SA-CCR, CVA Capital, CVA Pricing, Export)
- ✅ 8 tests CVA capital
- ✅ 8 tests CVA pricing
- ✅ 7 tests agrégateur
- ✅ 2 tests UI smoke
- ✅ Documentation README_I7c_counterparty.md

### Modifié

- ✅ `src/domain/risk/counterparty.py` : Ajout BA-CVA et CVA Pricing v1
- ✅ `src/services/risk_service.py` : Ajout services CVA et agrégateur
- ✅ `app/adapters/legacy_compat.py` : Ajout adaptateurs CVA
- ✅ `app/pages/14_🔁_Contrepartie.py` : Renommée depuis Dérivés, ajout onglets CVA

### Supprimé

- ✅ `tests/ui_smoke/test_derivatives_page.py` : Remplacé par test_counterparty_page.py

### Dépendances

Aucune nouvelle dépendance (numpy, pandas déjà installés)

---

## 🐛 Problèmes Connus

### CVA Pricing v1 Simplifié

Le CVA pricing est une approche simplifiée v1 :
- EE(t) constant = EAD (profil plat)
- Hazard rate constant (λ = spread / LGD)
- Pas de modèle de diffusion des spreads

**Solution** : Implémenter CVA Pricing v2 dans I8 avec profil EE(t) dynamique

### Collatéral Simplifié

Le collatéral est géré de manière simplifiée (soustraction directe du RC).  
La gestion avancée (MTA, threshold, haircuts, CSA) n'est pas encore implémentée.

**Solution** : Implémenter dans I8

---

## 📞 Support

### Documentation

- **README_I7c_counterparty.md** : Ce fichier
- **README_I7b.md** : Guide SA-CCR
- **README_I7a.md** : Guide UI refactoring
- **README_I6.md** : Guide persistance

### Commandes Utiles

```bash
# Lancer l'application
./run_app.sh

# Tests CVA capital
pytest tests/services/test_counterparty_cva_capital.py -v

# Tests CVA pricing
pytest tests/services/test_counterparty_cva_pricing.py -v

# Tests agrégateur
pytest tests/services/test_counterparty_aggregate.py -v

# Tests UI smoke
pytest tests/ui_smoke/test_counterparty_page.py -v

# Tous les tests
pytest tests/ -q
```

---

**🎉 I7c complété avec succès ! 241 tests passent, SA-CCR + CVA opérationnels, page Contrepartie unifiée !**

