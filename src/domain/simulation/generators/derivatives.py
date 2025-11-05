"""
Générateur de dérivés (Derivatives) - I11.
Génère des expositions de type Derivative avec netting sets.
"""
import uuid
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def generate_derivatives(config: dict, seed: int) -> pd.DataFrame:
    """
    Génère des dérivés (swaps, options, forwards) avec netting sets.
    
    Args:
        config: Configuration contenant:
            - n_derivatives: Nombre de dérivés (default: 3000)
            - entities: Liste des entités
            - currencies: Liste des devises
            - n_netting_sets: Nombre de netting sets (default: 200)
        seed: Seed pour reproductibilité
    
    Returns:
        DataFrame avec colonnes du schéma exposures
    """
    np.random.seed(seed)
    
    # Paramètres
    n_derivatives = config.get('n_derivatives', 3000)
    entities = config.get('entities', ['EU', 'US', 'CN'])
    currencies = config.get('currencies', ['EUR', 'USD', 'CNY'])
    n_netting_sets = config.get('n_netting_sets', 200)
    
    # IDs
    ids = [str(uuid.uuid4()) for _ in range(n_derivatives)]
    
    # Product type
    product_types = ['Derivative'] * n_derivatives
    
    # Counterparties (banques, hedge funds)
    counterparty_ids = [f'DERIV_CP_{i % 500:04d}' for i in range(n_derivatives)]
    
    # Dates
    today = datetime.now().date()
    booking_dates = [today - timedelta(days=int(np.random.exponential(365))) for _ in range(n_derivatives)]
    maturity_years = np.random.choice([0.25, 0.5, 1, 2, 5, 10], size=n_derivatives, p=[0.1, 0.15, 0.25, 0.25, 0.15, 0.1])
    maturity_dates = [booking_dates[i] + timedelta(days=int(maturity_years[i] * 365)) for i in range(n_derivatives)]
    
    # Entities & Currencies
    entity_list = np.random.choice(entities, size=n_derivatives)
    currency_list = np.random.choice(currencies, size=n_derivatives)
    
    # Notional (derivatives: 1M - 500M)
    notional = np.random.lognormal(mean=16, sigma=1.5, size=n_derivatives)  # ~9M median
    notional = np.clip(notional, 1000000, 500000000)
    
    # EAD (pour dérivés, EAD calculé via SA-CCR, ici on met MTM + Add-On simplifié)
    # EAD = max(0, MTM) + Add-On
    # Add-On = Notional * Factor (simplifié)
    addon_factor = np.random.uniform(0.01, 0.05, n_derivatives)
    
    # MTM (Mark-to-Market: peut être positif ou négatif)
    mtm = np.random.normal(0, 0.02, n_derivatives) * notional  # +/- 2% du notional
    
    # EAD = max(0, MTM) + Notional * addon_factor
    ead = np.maximum(0, mtm) + notional * addon_factor
    
    # PD (contreparties bancaires/institutionnelles: 0.1% - 3%)
    pd_values = np.random.beta(a=1.5, b=50, size=n_derivatives) * 0.03
    
    # LGD (dérivés: 40% - 60%)
    lgd = np.random.beta(a=4, b=4, size=n_derivatives) * 0.2 + 0.4  # 40-60%
    
    # CCF = 1.0 (dérivés on-BS)
    ccf = np.ones(n_derivatives)
    
    # Desk
    desks = np.random.choice(['Derivatives Trading', 'Hedging', 'Structured Products'], size=n_derivatives)
    
    # Is Retail = False (dérivés sont institutional)
    is_retail = np.array([False] * n_derivatives)
    
    # Exposure Class (Bank pour contreparties bancaires)
    exposure_class = np.array(['Bank'] * n_derivatives)
    
    # Netting sets (regroupement par contrepartie)
    netting_set_ids = [f'NS_{i % n_netting_sets:04d}' for i in range(n_derivatives)]
    
    # Collateral (50% des dérivés ont du collateral)
    has_collateral = np.random.rand(n_derivatives) < 0.5
    collateral_value = np.where(has_collateral, ead * np.random.uniform(0.7, 1.0, n_derivatives), 0)
    
    # Créer le DataFrame
    df = pd.DataFrame({
        'id': ids,
        'product_type': product_types,
        'counterparty_id': counterparty_ids,
        'booking_date': booking_dates,
        'maturity_date': maturity_dates,
        'currency': currency_list,
        'notional': notional,
        'ead': ead,
        'pd': pd_values,
        'lgd': lgd,
        'ccf': ccf,
        'maturity_years': maturity_years,
        'mtm': mtm,
        'desk': desks,
        'entity': entity_list,
        'is_retail': is_retail,
        'exposure_class': exposure_class,
        'netting_set_id': netting_set_ids,
        'collateral_value': collateral_value,
    })
    
    return df

