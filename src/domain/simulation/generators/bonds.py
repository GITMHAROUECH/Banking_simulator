"""
Générateur d'obligations (Bonds) - I11.
Génère des expositions de type Bond (sovereign, corporate).
"""
import uuid
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def generate_bonds(config: dict, seed: int) -> pd.DataFrame:
    """
    Génère des obligations (sovereign + corporate bonds).
    
    Args:
        config: Configuration contenant:
            - n_bonds: Nombre d'obligations (default: 5000)
            - entities: Liste des entités
            - currencies: Liste des devises
            - sovereign_ratio: Ratio sovereign vs corporate (default: 0.6)
        seed: Seed pour reproductibilité
    
    Returns:
        DataFrame avec colonnes du schéma exposures
    """
    np.random.seed(seed)
    
    # Paramètres
    n_bonds = config.get('n_bonds', 5000)
    entities = config.get('entities', ['EU', 'US', 'CN'])
    currencies = config.get('currencies', ['EUR', 'USD', 'CNY'])
    sovereign_ratio = config.get('sovereign_ratio', 0.6)
    
    # Générer les données
    n_sovereign = int(n_bonds * sovereign_ratio)
    n_corporate = n_bonds - n_sovereign
    
    # IDs
    ids = [str(uuid.uuid4()) for _ in range(n_bonds)]
    
    # Product type
    product_types = ['Bond'] * n_bonds
    
    # Counterparties
    # Sovereign: Gouvernements
    # Corporate: Entreprises
    counterparty_ids = (
        [f'GOV_{i:04d}' for i in range(n_sovereign)] +
        [f'CORP_{i:04d}' for i in range(n_corporate)]
    )
    
    # Dates
    today = datetime.now().date()
    booking_dates = [today - timedelta(days=int(np.random.exponential(730))) for _ in range(n_bonds)]
    maturity_years = np.random.choice([2, 5, 10, 15, 30], size=n_bonds, p=[0.1, 0.3, 0.3, 0.2, 0.1])
    maturity_dates = [booking_dates[i] + timedelta(days=int(maturity_years[i] * 365)) for i in range(n_bonds)]
    
    # Entities & Currencies
    entity_list = np.random.choice(entities, size=n_bonds)
    currency_list = np.random.choice(currencies, size=n_bonds)
    
    # Notional (bonds: 1M - 100M)
    notional = np.random.lognormal(mean=15, sigma=1.2, size=n_bonds)  # ~3M median
    notional = np.clip(notional, 1000000, 100000000)
    
    # EAD = Notional (bonds on-balance sheet)
    ead = notional.copy()
    
    # PD (Probability of Default)
    # Sovereign: 0.01% - 2%
    # Corporate: 0.1% - 5%
    pd_sovereign = np.random.beta(a=1, b=100, size=n_sovereign) * 0.02  # Très faible
    pd_corporate = np.random.beta(a=1.5, b=40, size=n_corporate) * 0.05  # Faible à modéré
    pd_values = np.concatenate([pd_sovereign, pd_corporate])
    
    # LGD (Loss Given Default)
    # Sovereign: 20% - 40%
    # Corporate: 30% - 60%
    lgd_sovereign = np.random.beta(a=3, b=5, size=n_sovereign) * 0.2 + 0.2  # 20-40%
    lgd_corporate = np.random.beta(a=4, b=4, size=n_corporate) * 0.3 + 0.3  # 30-60%
    lgd = np.concatenate([lgd_sovereign, lgd_corporate])
    
    # CCF = 1.0 pour bonds on-BS
    ccf = np.ones(n_bonds)
    
    # MTM = Notional +/- variation de prix
    price_variation = np.random.normal(0, 0.05, n_bonds)  # +/- 5%
    mtm = notional * (1 + price_variation)
    
    # Desk
    desks = np.random.choice(['Fixed Income', 'Treasury', 'Investment'], size=n_bonds)
    
    # Is Retail = False (bonds sont institutional)
    is_retail = np.array([False] * n_bonds)
    
    # Exposure Class
    exposure_class = np.array(['Sovereign'] * n_sovereign + ['Corporate'] * n_corporate)
    
    # Netting set (N/A pour bonds)
    netting_set_id = [None] * n_bonds
    
    # Collateral (bonds non collatéralisés généralement)
    collateral_value = np.zeros(n_bonds)
    
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

