"""
Générateur de dépôts (Deposits) - I11.
Génère des expositions de type Deposit (passif).
"""
import uuid
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def generate_deposits(config: dict, seed: int) -> pd.DataFrame:
    """
    Génère des dépôts clients (retail + corporate).
    
    Args:
        config: Configuration contenant:
            - n_deposits: Nombre de dépôts (default: 15000)
            - entities: Liste des entités
            - currencies: Liste des devises
            - retail_ratio: Ratio retail vs corporate (default: 0.7)
        seed: Seed pour reproductibilité
    
    Returns:
        DataFrame avec colonnes du schéma exposures
    """
    np.random.seed(seed)
    
    # Paramètres
    n_deposits = config.get('n_deposits', 15000)
    entities = config.get('entities', ['EU', 'US', 'CN'])
    currencies = config.get('currencies', ['EUR', 'USD', 'CNY'])
    retail_ratio = config.get('retail_ratio', 0.7)
    
    # Générer les données
    n_retail = int(n_deposits * retail_ratio)
    n_corporate = n_deposits - n_retail
    
    # IDs
    ids = [str(uuid.uuid4()) for _ in range(n_deposits)]
    
    # Product type
    product_types = ['Deposit'] * n_deposits
    
    # Counterparties
    counterparty_ids = [f'DEP_{i:06d}' for i in range(n_deposits)]
    
    # Dates
    today = datetime.now().date()
    booking_dates = [today - timedelta(days=int(np.random.exponential(180))) for _ in range(n_deposits)]
    
    # Maturity (deposits: 0 = demand, 1M, 3M, 6M, 1Y)
    maturity_years = np.random.choice([0, 0.08, 0.25, 0.5, 1], size=n_deposits, p=[0.4, 0.2, 0.2, 0.1, 0.1])
    maturity_dates = [
        booking_dates[i] + timedelta(days=int(maturity_years[i] * 365)) if maturity_years[i] > 0 else None
        for i in range(n_deposits)
    ]
    
    # Entities & Currencies
    entity_list = np.random.choice(entities, size=n_deposits)
    currency_list = np.random.choice(currencies, size=n_deposits)
    
    # Notional (deposits: 1k - 10M)
    # Retail: 1k - 100k
    # Corporate: 50k - 10M
    notional_retail = np.random.lognormal(mean=9, sigma=1.5, size=n_retail)  # ~8k median
    notional_corporate = np.random.lognormal(mean=12, sigma=1.8, size=n_corporate)  # ~160k median
    notional = np.concatenate([notional_retail, notional_corporate])
    notional = np.clip(notional, 1000, 10000000)
    
    # EAD = Notional (deposits sont des passifs, mais on les track)
    ead = notional.copy()
    
    # PD = 0 (deposits ne sont pas des actifs à risque)
    pd_values = np.zeros(n_deposits)
    
    # LGD = 0
    lgd = np.zeros(n_deposits)
    
    # CCF = 0 (deposits on-BS)
    ccf = np.zeros(n_deposits)
    
    # MTM = Notional
    mtm = notional.copy()
    
    # Desk
    desks = np.random.choice(['Retail Deposits', 'Corporate Deposits', 'Treasury'], size=n_deposits)
    
    # Is Retail
    is_retail = np.array([True] * n_retail + [False] * n_corporate)
    
    # Exposure Class (N/A pour deposits, mais on met Retail/Corporate)
    exposure_class = np.where(is_retail, 'Retail', 'Corporate')
    
    # Netting set (N/A)
    netting_set_id = [None] * n_deposits
    
    # Collateral (N/A pour deposits)
    collateral_value = np.zeros(n_deposits)
    
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

