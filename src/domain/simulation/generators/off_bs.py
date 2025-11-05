"""
Générateur hors-bilan (Off-Balance Sheet) - I11.
Génère des engagements hors-bilan (commitments, guarantees).
"""
import uuid
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def generate_off_bs(config: dict, seed: int) -> pd.DataFrame:
    """
    Génère des engagements hors-bilan (commitments, guarantees).
    
    Args:
        config: Configuration contenant:
            - n_off_bs: Nombre d'engagements (default: 2000)
            - entities: Liste des entités
            - currencies: Liste des devises
        seed: Seed pour reproductibilité
    
    Returns:
        DataFrame avec colonnes du schéma exposures
    """
    np.random.seed(seed)
    
    # Paramètres
    n_off_bs = config.get('n_off_bs', 2000)
    entities = config.get('entities', ['EU', 'US', 'CN'])
    currencies = config.get('currencies', ['EUR', 'USD', 'CNY'])
    
    # IDs
    ids = [str(uuid.uuid4()) for _ in range(n_off_bs)]
    
    # Product type (Commitment ou Guarantee)
    product_types = np.random.choice(['Commitment', 'Guarantee'], size=n_off_bs, p=[0.6, 0.4])
    
    # Counterparties
    counterparty_ids = [f'OFFBS_{i:05d}' for i in range(n_off_bs)]
    
    # Dates
    today = datetime.now().date()
    booking_dates = [today - timedelta(days=int(np.random.exponential(365))) for _ in range(n_off_bs)]
    maturity_years = np.random.choice([1, 2, 3, 5], size=n_off_bs, p=[0.3, 0.3, 0.25, 0.15])
    maturity_dates = [booking_dates[i] + timedelta(days=int(maturity_years[i] * 365)) for i in range(n_off_bs)]
    
    # Entities & Currencies
    entity_list = np.random.choice(entities, size=n_off_bs)
    currency_list = np.random.choice(currencies, size=n_off_bs)
    
    # Notional (off-BS: 100k - 20M)
    notional = np.random.lognormal(mean=13.5, sigma=1.5, size=n_off_bs)  # ~700k median
    notional = np.clip(notional, 100000, 20000000)
    
    # CCF (Credit Conversion Factor)
    # Commitments: 20% - 50%
    # Guarantees: 100%
    ccf = np.where(
        product_types == 'Commitment',
        np.random.choice([0.2, 0.5], size=n_off_bs, p=[0.6, 0.4]),
        1.0
    )
    
    # EAD = Notional * CCF
    ead = notional * ccf
    
    # PD (off-BS: 0.5% - 5%)
    pd_values = np.random.beta(a=1.5, b=40, size=n_off_bs) * 0.05
    
    # LGD (off-BS: 40% - 60%)
    lgd = np.random.beta(a=4, b=4, size=n_off_bs) * 0.2 + 0.4  # 40-60%
    
    # MTM = 0 (off-BS n'ont pas de MTM)
    mtm = np.zeros(n_off_bs)
    
    # Desk
    desks = np.random.choice(['Corporate Banking', 'Trade Finance', 'Guarantees'], size=n_off_bs)
    
    # Is Retail = False (off-BS sont généralement corporate)
    is_retail = np.array([False] * n_off_bs)
    
    # Exposure Class
    exposure_class = np.array(['Corporate'] * n_off_bs)
    
    # Netting set (N/A)
    netting_set_id = [None] * n_off_bs
    
    # Collateral (20% ont du collateral)
    has_collateral = np.random.rand(n_off_bs) < 0.2
    collateral_value = np.where(has_collateral, ead * np.random.uniform(0.5, 0.8, n_off_bs), 0)
    
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

