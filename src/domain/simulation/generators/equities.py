"""
Générateur d'actions (Equities) - I11.
Génère des expositions de type Equity (actions détenues).
"""
import uuid
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def generate_equities(config: dict, seed: int) -> pd.DataFrame:
    """
    Génère des positions en actions (equities).
    
    Args:
        config: Configuration contenant:
            - n_equities: Nombre de positions (default: 1000)
            - entities: Liste des entités
            - currencies: Liste des devises
        seed: Seed pour reproductibilité
    
    Returns:
        DataFrame avec colonnes du schéma exposures
    """
    np.random.seed(seed)
    
    # Paramètres
    n_equities = config.get('n_equities', 1000)
    entities = config.get('entities', ['EU', 'US', 'CN'])
    currencies = config.get('currencies', ['EUR', 'USD', 'CNY'])
    
    # IDs
    ids = [str(uuid.uuid4()) for _ in range(n_equities)]
    
    # Product type
    product_types = ['Equity'] * n_equities
    
    # Counterparties (entreprises cotées)
    counterparty_ids = [f'EQUITY_{i:04d}' for i in range(n_equities)]
    
    # Dates
    today = datetime.now().date()
    booking_dates = [today - timedelta(days=int(np.random.exponential(730))) for _ in range(n_equities)]
    
    # Maturity (N/A pour equities, on met None)
    maturity_years = np.zeros(n_equities)
    maturity_dates = [None] * n_equities
    
    # Entities & Currencies
    entity_list = np.random.choice(entities, size=n_equities)
    currency_list = np.random.choice(currencies, size=n_equities)
    
    # Notional (equities: 100k - 50M)
    notional = np.random.lognormal(mean=14, sigma=1.8, size=n_equities)  # ~1.2M median
    notional = np.clip(notional, 100000, 50000000)
    
    # EAD = Notional (valeur de marché)
    ead = notional.copy()
    
    # PD (pour equities, on utilise un proxy basé sur la volatilité)
    # PD = 0.5% - 3%
    pd_values = np.random.beta(a=1.5, b=50, size=n_equities) * 0.03
    
    # LGD (pour equities: 90% - 100% car pas de recovery)
    lgd = np.random.uniform(0.9, 1.0, n_equities)
    
    # CCF = 1.0 (equities on-BS)
    ccf = np.ones(n_equities)
    
    # MTM = Notional +/- variation de prix
    price_variation = np.random.normal(0, 0.15, n_equities)  # +/- 15% volatilité
    mtm = notional * (1 + price_variation)
    
    # Desk
    desks = np.random.choice(['Equity Trading', 'Investment', 'Proprietary Trading'], size=n_equities)
    
    # Is Retail = False (equities sont institutional)
    is_retail = np.array([False] * n_equities)
    
    # Exposure Class (Corporate pour equities)
    exposure_class = np.array(['Corporate'] * n_equities)
    
    # Netting set (N/A)
    netting_set_id = [None] * n_equities
    
    # Collateral (N/A pour equities)
    collateral_value = np.zeros(n_equities)
    
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
        'netting_set_id': netting_set_id,
        'collateral_value': collateral_value,
    })
    
    return df

