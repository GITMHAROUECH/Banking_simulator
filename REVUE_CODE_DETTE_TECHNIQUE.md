# Revue de Code - Dette Technique du Projet Banking Simulator

**Date:** 2025-11-03
**Projet:** Banking Simulation & CRR3 Reporting Application
**Version:** 1.0.0

---

## 📋 Résumé Exécutif

Cette revue de code identifie les points de dette technique dans le projet Banking Simulator tout en préservant les fonctionnalités décrites dans le README. L'analyse révèle une dette technique **ÉLEVÉE** avec des impacts significatifs sur la maintenabilité, la testabilité et l'évolutivité du projet.

### Points Critiques Identifiés
- ⚠️ **CRITIQUE**: Aucun test unitaire (0 fichiers de test)
- ⚠️ **CRITIQUE**: Fichier monolithe de 4096 lignes (Banking_Simulator.py)
- ⚠️ **ÉLEVÉ**: Duplication importante de code entre modules
- ⚠️ **ÉLEVÉ**: Absence de validation des données d'entrée
- ⚠️ **MOYEN**: Magic numbers dispersés dans tout le code

---

## 🏗️ Architecture et Structure du Code

### 1. Problème: Fichier Monolithe (Banking_Simulator.py - 4096 lignes)

**Sévérité:** ⚠️ CRITIQUE

**Description:**
Le fichier `Banking_Simulator.py` contient 4096 lignes de code, ce qui viole gravement le principe de responsabilité unique (SRP). Ce fichier contient:
- Logique de simulation
- Interface utilisateur Streamlit
- Calculs RWA
- Gestion de la liquidité
- Génération de rapports
- Logique de consolidation

**Impact:**
- Impossible à maintenir efficacement
- Difficile à tester
- Conflits Git fréquents lors du travail en équipe
- Temps de chargement et refactoring élevés

**Localisation:**
```
/home/user/Banking_simulator/Banking_Simulator.py (4096 lignes)
```

**Recommandation:**
Refactoriser en modules séparés suivant l'architecture déjà existante dans `app/`:
- Utiliser les modules `app/core/*` existants
- Migrer progressivement les fonctionnalités
- Supprimer le fichier monolithe une fois la migration terminée

---

### 2. Problème: Duplication de Code entre Banking_Simulator.py et app/

**Sévérité:** ⚠️ ÉLEVÉ

**Description:**
Il existe une duplication importante entre:
- `Banking_Simulator.py` (4096 lignes) - version monolithe
- `app/streamlit_app.py` (1648 lignes) - version modulaire

Les deux fichiers implémentent la même application Streamlit avec des variations.

**Exemples de Duplication:**
```python
# Banking_Simulator.py:125-314
def generate_positions_advanced(num_positions=1000, seed=42, config=None):
    """Générer des positions avancées - Version sécurisée"""
    # ... 200 lignes de code

# app/core/simulation.py:105-143
def _generate_initial_positions(self) -> pd.DataFrame:
    """Générer les positions initiales"""
    # ... logique similaire mais organisée différemment
```

**Impact:**
- Maintenance en double
- Risque d'incohérences entre les versions
- Confusion pour les développeurs
- Bugs corrigés dans une version mais pas l'autre

**Recommandation:**
1. Choisir UNE version canonique (recommandé: `app/streamlit_app.py` + modules `app/core/`)
2. Supprimer ou archiver `Banking_Simulator.py`
3. Migrer les fonctionnalités uniques si nécessaires

---

### 3. Problème: Imports Try/Except Masquant les Dépendances

**Sévérité:** ⚠️ MOYEN

**Description:**
Plusieurs fichiers utilisent des blocs try/except pour gérer les imports, masquant les problèmes de dépendances:

**Localisation:**
```python
# Banking_Simulator.py:18-22
try:
    from home_page import show_updated_home
except ImportError:
    def show_updated_home():
        st.error("Page d'accueil mise à jour non disponible")

# Banking_Simulator.py:26-32
try:
    from consolidation_complete import show_consolidation_advanced
except ImportError:
    def show_consolidation_advanced():
        st.error("Module de consolidation non disponible")
```

**Impact:**
- Erreurs silencieuses en production
- Difficile de détecter les dépendances manquantes
- Comportement inattendu si les modules ne sont pas disponibles
- Tests difficiles à écrire

**Recommandation:**
1. Rendre tous les imports explicites et obligatoires
2. Utiliser un gestionnaire d'erreur centralisé
3. Créer des dépendances optionnelles claires dans `requirements.txt`
4. Lever des exceptions claires si les dépendances sont manquantes

---

## 🧪 Tests et Qualité

### 4. Problème: Absence Totale de Tests Unitaires

**Sévérité:** ⚠️ CRITIQUE

**Description:**
Le projet ne contient **AUCUN** fichier de test (0 fichiers `test_*.py` ou `*_test.py` trouvés).

**Impact:**
- Impossible de garantir la fiabilité des calculs financiers
- Régression fréquente lors des modifications
- Pas de documentation par l'exemple
- Risque élevé d'erreurs dans les calculs réglementaires (RWA, LCR, NSFR)

**Fonctionnalités Critiques Sans Tests:**
- Calculs RWA selon CRR3 (`app/core/credit_risk.py`)
- Calculs LCR/NSFR (`app/core/liquidity.py`)
- Provisions ECL IFRS 9 (`app/core/accounting.py`)
- Formules IRB complexes (`app/core/credit_risk.py:157-196`)
- Conversion de devises (`app/core/accounting.py:427-442`)

**Recommandation URGENTE:**
Créer une suite de tests minimale pour:

```python
# tests/test_credit_risk.py
def test_irb_formula_basic_case():
    """Test de la formule IRB avec des valeurs connues"""
    engine = CreditRiskEngine({})
    pd_val, lgd_val = 0.02, 0.45
    correlation, maturity = 0.15, 2.5

    rwa_density = engine._irb_formula(pd_val, lgd_val, correlation, maturity)

    # Vérifier que le résultat est dans une plage raisonnable
    assert 0 < rwa_density < 2.0, "RWA density doit être entre 0 et 200%"

# tests/test_accounting.py
def test_ecl_calculation_stage_1():
    """Test du calcul ECL pour Stage 1 (12 mois)"""
    positions = pd.DataFrame([{
        'ead': 100000, 'pd': 0.01, 'lgd': 0.40, 'stage': 1
    }])

    # ECL Stage 1 = EAD * PD * LGD * (1/12)
    expected_ecl = 100000 * 0.01 * 0.40 * (1/12)
    # Vérifier le calcul
```

**Priorités de Tests:**
1. **Haute priorité**: Calculs réglementaires (RWA, LCR, NSFR)
2. **Moyenne priorité**: Logique métier (provisions, consolidation)
3. **Basse priorité**: Interface utilisateur Streamlit

---

### 5. Problème: Absence de Validation des Données d'Entrée

**Sévérité:** ⚠️ ÉLEVÉ

**Description:**
Aucune validation des données d'entrée n'est effectuée, permettant des valeurs invalides:

**Exemples:**
```python
# app/core/simulation.py:175-206
def _generate_risk_parameters(self, entity: EntitySchema,
                            product: ProductSchema) -> Dict:
    params = {}

    # Pas de validation que les taux sont positifs
    if product.product_class == ProductClass.LOAN:
        params['eir'] = np.random.uniform(0.02, 0.06)  # Peut être négatif si bug numpy

    # Pas de validation des bornes PD/LGD
    params['pd'] = np.random.uniform(0.01, 0.05)  # Peut dépasser 100%
    params['lgd'] = np.random.uniform(0.20, 0.60)  # Pas de vérification
```

**Impact:**
- Calculs incorrects avec des données invalides
- Erreurs difficiles à tracer
- Pas de messages d'erreur clairs pour l'utilisateur

**Recommandation:**
Implémenter une couche de validation avec `pydantic` (déjà dans les dépendances):

```python
from pydantic import BaseModel, validator, Field

class RiskParameters(BaseModel):
    pd: float = Field(ge=0.0, le=1.0, description="PD entre 0 et 100%")
    lgd: float = Field(ge=0.0, le=1.0, description="LGD entre 0 et 100%")
    eir: float = Field(gt=0.0, description="Taux d'intérêt positif")

    @validator('pd')
    def validate_pd(cls, v):
        if v < 0.0001:
            raise ValueError("PD trop faible, minimum 0.01%")
        return v
```

---

## 📊 Qualité du Code

### 6. Problème: Magic Numbers Partout

**Sévérité:** ⚠️ MOYEN

**Description:**
Le code contient des centaines de "magic numbers" non documentés:

**Exemples:**
```python
# app/core/accounting.py:306
capital_amount = total_assets * 0.08  # Pourquoi 8% ? CRR3 minimum?

# app/core/accounting.py:317
reserves_amount = total_assets * 0.05  # D'où vient 5% ?

# app/core/accounting.py:328
cash_amount = total_assets * 0.10  # Pourquoi 10% ?

# app/core/credit_risk.py:270
entity_totals['tier1_capital'] = entity_totals['ead'] * 0.12  # 12% ?

# Banking_Simulator.py:168-169
base_ead = 150000 + random.randint(-50000, 300000)  # Valeurs arbitraires
```

**Impact:**
- Code difficile à comprendre
- Impossible de savoir si les valeurs sont réglementaires ou arbitraires
- Difficile à modifier sans risque

**Recommandation:**
Créer un fichier de constantes avec documentation:

```python
# app/config/regulatory_constants.py
"""
Constantes réglementaires CRR3/Bâle III
Source: Règlement (UE) 2024/1623
"""

class CapitalRequirements:
    """Exigences de capital réglementaires"""
    CET1_MINIMUM = 0.045  # 4.5% - Article 92 CRR3
    TIER1_MINIMUM = 0.06  # 6.0% - Article 92 CRR3
    TOTAL_CAPITAL_MINIMUM = 0.08  # 8.0% - Article 92 CRR3
    CONSERVATION_BUFFER = 0.025  # 2.5% - Article 129 CRR3

class SimulationDefaults:
    """Valeurs par défaut pour la simulation (non réglementaires)"""
    MORTGAGE_BASE_AMOUNT = 150_000  # EUR - Moyenne France 2024
    MORTGAGE_VARIANCE_MIN = -50_000
    MORTGAGE_VARIANCE_MAX = 300_000

    # Ratios de structure de bilan (moyennes secteur bancaire)
    CAPITAL_TO_ASSETS = 0.08  # 8% selon moyennes bancaires
    RESERVES_TO_ASSETS = 0.05  # 5% selon moyennes bancaires
    CASH_TO_ASSETS = 0.10  # 10% selon moyennes bancaires
```

Puis utiliser:
```python
capital_amount = total_assets * CapitalRequirements.TOTAL_CAPITAL_MINIMUM
```

---

### 7. Problème: Fonctions Trop Longues

**Sévérité:** ⚠️ MOYEN

**Description:**
Plusieurs fonctions dépassent 100-200 lignes, violant le principe de responsabilité unique:

**Exemples:**
- `generate_positions_advanced()` : ~190 lignes (Banking_Simulator.py:125-314)
- `calculate_rwa_advanced()` : ~150 lignes (Banking_Simulator.py:316-467)
- `show_simulation_page()` : ~146 lignes (app/streamlit_app.py:326-472)

**Impact:**
- Difficile à tester
- Difficile à comprendre
- Difficile à réutiliser
- Augmente le risque de bugs

**Recommandation:**
Appliquer la règle "Une fonction = Une responsabilité":

```python
# Avant (>190 lignes)
def generate_positions_advanced(num_positions, seed, config):
    # Génération
    # Calcul PD
    # Calcul LGD
    # Calcul maturité
    # Classification IFRS 9
    # Calcul ECL
    # Calcul intérêts
    # ...
    return positions

# Après (fonctions ciblées)
def generate_positions_advanced(num_positions, seed, config):
    """Orchestrateur principal"""
    positions = _initialize_positions(num_positions, seed, config)
    positions = _calculate_risk_parameters(positions, config)
    positions = _classify_ifrs9_stages(positions)
    positions = _calculate_ecl_provisions(positions)
    return positions

def _calculate_risk_parameters(positions, config):
    """Calcule PD, LGD, maturité pour chaque position"""
    # Focalisé sur un seul aspect
    ...

def _classify_ifrs9_stages(positions):
    """Classifie les positions en stages IFRS 9"""
    # Logique IFRS 9 isolée
    ...
```

---

### 8. Problème: Taux de Change Hardcodés

**Sévérité:** ⚠️ MOYEN

**Description:**
Les taux de change sont hardcodés dans la configuration au lieu d'utiliser une source dynamique:

**Localisation:**
```python
# app/config/defaults.py:47-80
"fx_rates": [
    {
        "date": "2024-12-31",
        "from_currency": "USD",
        "to_currency": "EUR",
        "rate": 1.10,  # Hardcodé
        "is_closing": True,
        "is_average": False
    },
    {
        "date": "2024-12-31",
        "from_currency": "CNY",
        "to_currency": "EUR",
        "rate": 7.85,  # Hardcodé
        ...
    }
]

# app/core/accounting.py:433-442
def _convert_to_eur(self, amount: float, from_currency: str) -> float:
    fx_rates = self.config.get('fx_rates', {})
    if from_currency == 'USD':
        rate = fx_rates.get('USD_EUR', 1.10)  # Fallback hardcodé
        return amount / rate
    elif from_currency == 'CNY':
        rate = fx_rates.get('CNY_EUR', 7.85)  # Fallback hardcodé
```

**Impact:**
- Calculs de consolidation incorrects avec le temps
- Pas de traçabilité des sources de données
- Impossible d'utiliser des données historiques

**Recommandation:**
1. Pour la démo/éducation: Conserver mais documenter clairement
2. Pour un usage réel: Intégrer une API de taux de change

```python
# app/services/fx_rates.py
from datetime import date
from typing import Dict, Optional
import requests

class FXRateService:
    """Service de gestion des taux de change"""

    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock

    def get_rate(self, from_curr: str, to_curr: str,
                 ref_date: date) -> float:
        """Récupère le taux de change pour une date donnée"""
        if self.use_mock:
            return self._get_mock_rate(from_curr, to_curr)
        else:
            return self._get_live_rate(from_curr, to_curr, ref_date)

    def _get_mock_rate(self, from_curr: str, to_curr: str) -> float:
        """Taux fictifs pour la démo - DOCUMENTÉS"""
        DEMO_RATES = {
            ('USD', 'EUR'): 1.10,  # Source: moyenne 2024
            ('CNY', 'EUR'): 7.85,  # Source: moyenne 2024
        }
        return DEMO_RATES.get((from_curr, to_curr), 1.0)
```

---

### 9. Problème: Mélange Logique Métier et Présentation

**Sévérité:** ⚠️ ÉLEVÉ

**Description:**
La logique métier (calculs financiers) est mélangée avec le code de présentation (Streamlit):

**Exemples:**
```python
# Banking_Simulator.py:469-500 - Calculs dans la fonction d'affichage
def calculate_capital_ratios(rwa_df):
    """Calculer les ratios de capital"""
    total_rwa = rwa_df['rwa_amount'].sum()

    # Capital simulé (en millions d'EUR)
    cet1_capital = total_rwa * 0.12  # CALCUL MÉTIER
    tier1_capital = total_rwa * 0.135
    total_capital = total_rwa * 0.15

    # Ratios
    cet1_ratio = (cet1_capital / total_rwa * 100) if total_rwa > 0 else 0
    ...
    return capital_ratios  # Retourné directement à Streamlit

# app/streamlit_app.py:486-533 - Calculs mélangés avec st.
if st.button("📊 Calculer les états comptables", type="primary"):
    with st.spinner("Calcul des états comptables..."):
        try:
            # LOGIQUE MÉTIER dans le fichier de présentation
            acc_engine = AccountingEngine(config)
            progress_bar = st.progress(0)  # PRÉSENTATION
            trial_balances = acc_engine.calculate_trial_balances(...)  # MÉTIER
            progress_bar.progress(50)  # PRÉSENTATION
```

**Impact:**
- Impossible de réutiliser la logique sans Streamlit
- Tests difficiles (nécessite mock de Streamlit)
- Couplage fort entre couches

**Recommandation:**
Séparer strictement les couches (déjà partiellement fait dans `app/core/`):

```python
# app/core/capital.py - LOGIQUE MÉTIER PURE
class CapitalEngine:
    """Calculs de capital - SANS dépendance à Streamlit"""

    def calculate_capital_ratios(self, rwa_df: pd.DataFrame) -> CapitalRatios:
        """Calcule les ratios de capital selon CRR3"""
        total_rwa = rwa_df['rwa_amount'].sum()

        return CapitalRatios(
            cet1_capital=total_rwa * 0.12,
            tier1_capital=total_rwa * 0.135,
            total_capital=total_rwa * 0.15,
            total_rwa=total_rwa
        )

# app/ui/pages/capital.py - PRÉSENTATION
def show_capital_page():
    """Page Streamlit - UNIQUEMENT présentation"""
    if st.button("📊 Calculer"):
        with st.spinner("Calcul..."):
            # Appel à la logique métier
            engine = CapitalEngine()
            ratios = engine.calculate_capital_ratios(st.session_state['rwa'])

            # Affichage uniquement
            st.metric("CET1", f"{ratios.cet1_ratio:.2f}%")
```

**Bénéfices:**
- Tests unitaires simples (pas de mock Streamlit)
- Réutilisable en API, CLI, ou autre UI
- Séparation des responsabilités claire

---

## 🔧 Configuration et Gestion

### 10. Problème: Configuration Dispersée

**Sévérité:** ⚠️ MOYEN

**Description:**
La configuration est éparpillée entre plusieurs fichiers sans hiérarchie claire:

**Fichiers de Configuration:**
- `app/config/defaults.py` - Configuration par défaut
- `app/config/schemas.py` - Schémas de données
- `Banking_Simulator.py:131-138` - Config inline dans le code
- `app/streamlit_app.py:221-324` - Config UI Streamlit
- Constantes CRR3 dans `defaults.py`

**Exemple de Problème:**
```python
# Banking_Simulator.py:131-138
if config is None:
    config = {
        'base_currency': 'EUR',
        'stress_scenario': 'Baseline',
        'include_derivatives': False,
        'retail_pd_base': 0.02,  # Aussi dans defaults.py
        'corporate_pd_base': 0.03  # Duplication
    }

# app/config/defaults.py:197-214
"irb_parameters": {
    "retail": {
        "mortgages": {
            "pd": 0.015,  # Différent de 0.02 ci-dessus!
```

**Impact:**
- Valeurs par défaut incohérentes
- Difficile de savoir quelle configuration prime
- Impossible de gérer différents environnements (dev, staging, prod)

**Recommandation:**
Hiérarchie de configuration claire:

```python
# app/config/config.py
from typing import Optional
from pydantic import BaseSettings
import os

class Settings(BaseSettings):
    """Configuration globale de l'application"""

    # Environnement
    ENV: str = "development"
    DEBUG: bool = True

    # Simulation
    BASE_CURRENCY: str = "EUR"
    DEFAULT_SEED: int = 42

    # Paramètres de risque (dev)
    RETAIL_PD_BASE: float = 0.02
    CORPORATE_PD_BASE: float = 0.03

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Configuration par environnement
class DevelopmentSettings(Settings):
    """Config développement - données fictives"""
    RETAIL_PD_BASE: float = 0.02
    USE_MOCK_FX_RATES: bool = True

class ProductionSettings(Settings):
    """Config production - données réelles"""
    DEBUG: bool = False
    USE_MOCK_FX_RATES: bool = False

def get_settings() -> Settings:
    """Factory pour obtenir la config selon l'environnement"""
    env = os.getenv("ENV", "development")
    if env == "production":
        return ProductionSettings()
    return DevelopmentSettings()

# Utilisation
settings = get_settings()
```

---

### 11. Problème: Gestion d'Erreurs Insuffisante

**Sévérité:** ⚠️ MOYEN

**Description:**
Les erreurs sont souvent ignorées ou mal gérées:

**Exemples:**
```python
# app/core/credit_risk.py:194-196
except Exception as e:
    logger.warning(f"Erreur dans le calcul IRB: {e}, utilisation d'une valeur par défaut")
    return 1.0  # Masque l'erreur silencieusement

# Banking_Simulator.py:121-123
except Exception as e:
    st.error(f"Erreur création DataFrame: {e}")
    return pd.DataFrame({'id': [1], 'value': [0]})  # Données fictives

# app/streamlit_app.py:399-402
except Exception as e:
    st.error(f"❌ Erreur lors de la simulation: {e}")
    logger.error(f"Erreur simulation: {e}")
    return  # Pas de stack trace, difficile à debugger
```

**Impact:**
- Erreurs masquées difficiles à diagnostiquer
- Comportement inattendu avec des données par défaut
- Pas de traçabilité des erreurs

**Recommandation:**
Créer des exceptions personnalisées et une gestion structurée:

```python
# app/exceptions.py
class BankingSimulatorError(Exception):
    """Exception de base pour l'application"""
    pass

class CalculationError(BankingSimulatorError):
    """Erreur lors d'un calcul financier"""
    pass

class InvalidDataError(BankingSimulatorError):
    """Données d'entrée invalides"""
    pass

class ConfigurationError(BankingSimulatorError):
    """Erreur de configuration"""
    pass

# app/core/credit_risk.py
def _irb_formula(self, pd_val, lgd_val, correlation, maturity):
    """Formule IRB pour calculer la densité de RWA"""
    try:
        # Validation
        if not 0 < pd_val < 1:
            raise InvalidDataError(f"PD invalide: {pd_val} (doit être entre 0 et 1)")

        # Calculs...
        return rwa_density

    except (ValueError, ZeroDivisionError) as e:
        # Erreur de calcul spécifique
        raise CalculationError(
            f"Erreur calcul IRB: PD={pd_val}, LGD={lgd_val}, R={correlation}"
        ) from e

# app/ui/error_handler.py
def handle_streamlit_error(func):
    """Décorateur pour gérer les erreurs dans Streamlit"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except InvalidDataError as e:
            st.error(f"❌ Données invalides: {e}")
            st.info("💡 Vérifiez les paramètres de saisie")
        except CalculationError as e:
            st.error(f"❌ Erreur de calcul: {e}")
            if settings.DEBUG:
                st.exception(e)  # Stack trace en mode debug
        except Exception as e:
            st.error(f"❌ Erreur inattendue: {e}")
            logger.exception("Erreur non gérée")
            if settings.DEBUG:
                st.exception(e)
    return wrapper

@handle_streamlit_error
def show_simulation_page():
    """Page de simulation avec gestion d'erreurs"""
    ...
```

---

## 📚 Documentation

### 12. Problème: Documentation des Fonctions Incomplète

**Sévérité:** ⚠️ MOYEN

**Description:**
De nombreuses fonctions n'ont pas de docstrings ou des docstrings incomplètes:

**Exemples:**
```python
# app/core/credit_risk.py:157
def _irb_formula(self, pd_val: float, lgd_val: float, correlation: float, maturity: float) -> float:
    """Formule IRB pour calculer la densité de RWA"""
    # Pas d'explication de la formule, des paramètres, du retour
    # Pas de référence réglementaire
    # Pas d'exemple

# Banking_Simulator.py:105
def safe_dataframe_creation(data_list, columns=None):
    """Créer un DataFrame de manière sécurisée"""
    # Pas d'explication de ce qui est "sécurisé"
    # Pas d'info sur les types
    # Pas d'exemple

# app/core/liquidity.py:133
def _calculate_hqla(self, positions: pd.DataFrame) -> Dict[str, float]:
    """Calculer les High Quality Liquid Assets"""
    # Pas d'explication de la classification HQLA
    # Pas de référence aux niveaux 1/2A/2B
```

**Impact:**
- Code difficile à comprendre
- Pas de documentation de l'API
- Difficile pour les nouveaux développeurs

**Recommandation:**
Adopter un standard de documentation (Google Style ou NumPy Style):

```python
def _irb_formula(self, pd_val: float, lgd_val: float,
                correlation: float, maturity: float) -> float:
    """Calcule la densité RWA selon la formule IRB de CRR3.

    Implémente la formule réglementaire CRR3 pour le calcul des Risk-Weighted
    Assets (RWA) selon l'approche Internal Ratings-Based (IRB).

    Formule:
        K = LGD * N[(1-R)^(-0.5) * G(PD) + (R/(1-R))^0.5 * G(0.999)] - PD * LGD
        RWA_density = K * 12.5

    Où:
        - N(...) = Fonction de répartition normale standard
        - G(...) = Fonction inverse de répartition normale
        - R = Corrélation d'actifs
        - K = Capital réglementaire requis

    Args:
        pd_val: Probability of Default (0 < PD < 1)
            Exemple: 0.02 pour 2% de probabilité de défaut
        lgd_val: Loss Given Default (0 < LGD < 1)
            Exemple: 0.45 pour 45% de perte en cas de défaut
        correlation: Asset correlation selon CRR3 (0 < R < 1)
            - Retail mortgages: 0.15
            - Retail revolving: 0.04
            - Corporate: 0.12-0.24 (dépend de la taille)
        maturity: Effective maturity en années (1.0 ≤ M ≤ 7.0)
            Exemple: 2.5 pour 2.5 ans

    Returns:
        RWA density (float): Ratio RWA/EAD, typiquement entre 0.0 et 2.0
            Exemple: 0.75 signifie RWA = 75% de l'EAD

    Raises:
        CalculationError: Si les paramètres sont hors limites ou si le calcul échoue

    References:
        - Article 153 du Règlement (UE) 2024/1623 (CRR3)
        - Basel III Framework: https://www.bis.org/basel_framework/

    Example:
        >>> engine = CreditRiskEngine({})
        >>> # Retail mortgage: PD=1.5%, LGD=20%, R=0.15, M=15 ans
        >>> rwa_density = engine._irb_formula(0.015, 0.20, 0.15, 2.5)
        >>> print(f"RWA density: {rwa_density:.2%}")
        RWA density: 45.23%
    """
    try:
        # Validation des paramètres
        if not 0.0001 <= pd_val <= 0.9999:
            raise InvalidDataError(f"PD hors limites: {pd_val}")

        # ... reste du code
```

---

## 🔄 Dépendances et Versions

### 13. Problème: Versions de Dépendances Non Fixées

**Sévérité:** ⚠️ FAIBLE

**Description:**
Le fichier `requirements.txt` utilise des contraintes `>=` au lieu de versions exactes:

```txt
# requirements.txt
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
```

**Impact:**
- Builds non reproductibles
- Risque de breaking changes avec les mises à jour
- Difficile de reproduire les bugs en production

**Recommandation:**
Utiliser un fichier de verrouillage:

```bash
# Générer un fichier requirements.lock avec versions exactes
pip freeze > requirements.lock

# requirements.txt - dépendances logiques
streamlit>=1.28.0,<2.0.0
pandas>=2.0.0,<3.0.0
numpy>=1.24.0,<2.0.0

# requirements.lock - versions exactes (généré automatiquement)
streamlit==1.28.1
pandas==2.1.4
numpy==1.24.3
```

Ou utiliser poetry/pipenv pour la gestion des dépendances.

---

## 📈 Performance

### 14. Problème: Inefficacités dans les Calculs

**Sévérité:** ⚠️ FAIBLE

**Description:**
Certains calculs sont inefficaces:

**Exemples:**
```python
# app/core/simulation.py:268-286 - Itération ligne par ligne
for idx, row in positions.iterrows():  # LENT pour grands DataFrames
    current_stage = row['stage']
    rand = np.random.random()
    # ...
    positions.at[idx, 'stage'] = 2  # Modification ligne par ligne

# Banking_Simulator.py:321-322 - Itération inutile
for index, row in positions_df.iterrows():  # Peut être vectorisé
    pos_id = row['position_id']
    # ... calculs
```

**Impact:**
- Lent avec >10,000 positions
- Ne scale pas

**Recommandation:**
Vectoriser les opérations pandas:

```python
# Avant (lent)
for idx, row in positions.iterrows():
    if row['pd'] > 0.03:
        positions.at[idx, 'stage'] = 2

# Après (rapide)
positions.loc[positions['pd'] > 0.03, 'stage'] = 2

# Avant (lent)
for idx, row in positions.iterrows():
    rwa = row['ead'] * row['risk_weight']
    positions.at[idx, 'rwa'] = rwa

# Après (rapide)
positions['rwa'] = positions['ead'] * positions['risk_weight']
```

---

## 📋 Plan d'Action Recommandé

### Phase 1: Fondations (Semaines 1-2) - PRIORITÉ HAUTE

1. **Tests Critiques**
   - [ ] Créer structure de tests (`tests/` directory)
   - [ ] Tests des calculs RWA (IRB + Standardisé)
   - [ ] Tests des calculs LCR/NSFR
   - [ ] Tests des provisions ECL
   - [ ] CI/CD avec GitHub Actions

2. **Validation des Données**
   - [ ] Implémenter validateurs Pydantic
   - [ ] Valider tous les inputs utilisateur
   - [ ] Valider les résultats de calculs

3. **Gestion d'Erreurs**
   - [ ] Créer hiérarchie d'exceptions
   - [ ] Implémenter gestionnaire d'erreurs global
   - [ ] Ajouter logging structuré

### Phase 2: Refactoring (Semaines 3-6) - PRIORITÉ HAUTE

1. **Éliminer le Monolithe**
   - [ ] Migrer fonctionnalités de `Banking_Simulator.py` vers `app/`
   - [ ] Supprimer duplication de code
   - [ ] Tester après chaque migration

2. **Séparer Logique/Présentation**
   - [ ] Extraire calculs métier des pages Streamlit
   - [ ] Créer couche service (`app/services/`)
   - [ ] Tests unitaires des services

3. **Constantes et Configuration**
   - [ ] Créer fichier de constantes réglementaires
   - [ ] Remplacer tous les magic numbers
   - [ ] Hiérarchie de configuration claire

### Phase 3: Documentation (Semaines 7-8) - PRIORITÉ MOYENNE

1. **Documentation Code**
   - [ ] Docstrings complètes (Google Style)
   - [ ] Références réglementaires
   - [ ] Exemples d'utilisation

2. **Documentation Utilisateur**
   - [ ] Guide de développement
   - [ ] Architecture Decision Records (ADR)
   - [ ] Guide de contribution

### Phase 4: Optimisation (Semaines 9-10) - PRIORITÉ BASSE

1. **Performance**
   - [ ] Vectoriser calculs pandas
   - [ ] Profiling et optimisation
   - [ ] Benchmark avant/après

2. **Qualité**
   - [ ] Couverture de code >80%
   - [ ] Linting (flake8, black)
   - [ ] Type checking (mypy)

---

## 🎯 Métriques de Succès

### Objectifs Quantifiables

| Métrique | État Actuel | Objectif | Priorité |
|----------|-------------|----------|----------|
| Couverture de tests | 0% | >80% | HAUTE |
| Fichiers >500 lignes | 3 | 0 | HAUTE |
| Magic numbers | ~150 | <10 | MOYENNE |
| Fonctions >100 lignes | ~15 | <5 | MOYENNE |
| Docstrings manquantes | ~60% | <10% | MOYENNE |
| Temps de simulation (1000 pos) | ? | <5s | BASSE |

---

## ✅ Conclusion

Le projet Banking Simulator présente une **dette technique élevée** mais **gérable**. Les fonctionnalités principales sont bien conçues et l'architecture modulaire dans `app/` est un bon point de départ.

### Points Positifs
- ✅ Architecture modulaire dans `app/core/` bien pensée
- ✅ Séparation des responsabilités (simulation, accounting, risk, liquidity)
- ✅ Utilisation de pydantic et pandas appropriée
- ✅ Constantes réglementaires CRR3 documentées
- ✅ Fonctionnalités complètes et conformes au README

### Points Critiques à Adresser
- ⚠️ **URGENT**: Ajouter des tests unitaires (couverture 0%)
- ⚠️ **URGENT**: Éliminer le fichier monolithe Banking_Simulator.py
- ⚠️ **IMPORTANT**: Implémenter validation des données
- ⚠️ **IMPORTANT**: Séparer logique métier et présentation

### Estimation d'Effort
- **Phase 1** (Fondations): 2 semaines × 1 développeur = 80h
- **Phase 2** (Refactoring): 4 semaines × 1 développeur = 160h
- **Phase 3** (Documentation): 2 semaines × 1 développeur = 80h
- **Phase 4** (Optimisation): 2 semaines × 1 développeur = 80h

**Total estimé**: 10 semaines × 1 développeur (400h)

---

## 📞 Contact

Pour toute question sur cette revue de code, consulter l'équipe de développement.

---

**Document généré le:** 2025-11-03
**Version:** 1.0
**Révision:** DRAFT
