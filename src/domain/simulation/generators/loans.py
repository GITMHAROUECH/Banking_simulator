"""
Générateur de prêts (Loans) - I11.
Génère des expositions de type Loan avec distribution réaliste.
"""
import uuid
from datetime import datetime, timedelta

import pandas as pd
import numpy as np


def generate_loans(config: dict, seed: int) -> pd.DataFrame:
    """
    Génère des prêts (corporate + retail).
    
    Args:
        config: Configuration contenant:
            - n_loans: Nombre de prêts à générer (default: 10000)
            - entities: Liste des entités (default: ['EU', 'US', 'CN'])
            - currencies: Liste des devises (default: ['EUR', 'USD', 'CNY'])
            - retail_ratio: Ratio retail vs corporate (default: 0.4)
        seed: Seed pour reproductibilité
    
    Returns:
        DataFrame avec colonnes du schéma exposures
    """
    np.random.seed(seed)
    
    # Paramètres
    n_loans = config.get('n_loans', 10000)
    entities = config.get('entities', ['EU', 'US', 'CN'])
    currencies = config.get('currencies', ['EUR', 'USD', 'CNY'])
    retail_ratio = config.get('retail_ratio', 0.4)
    
    # Générer les données
    n_retail = int(n_loans * retail_ratio)
    n_corporate = n_loans - n_retail
    
    # IDs
    ids = [str(uuid.uuid4()) for _ in range(n_loans)]
    
    # Product type
    product_types = ['Loan'] * n_loans
    
    # Counterparties
    counterparty_ids = [f'CP_{i:06d}' for i in range(n_loans)]
    
    # Dates
    today = datetime.now().date()
    booking_dates = [today - timedelta(days=int(np.random.exponential(365))) for _ in range(n_loans)]
    maturity_years = np.random.choice([1, 2, 3, 5, 7, 10], size=n_loans, p=[0.1, 0.15, 0.2, 0.25, 0.2, 0.1])
    maturity_dates = [booking_dates[i] + timedelta(days=int(maturity_years[i] * 365)) for i in range(n_loans)]
    
    # Entities & Currencies
    entity_list = np.random.choice(entities, size=n_loans)
    currency_list = np.random.choice(currencies, size=n_loans)
    
    # Notional (log-normal distribution)
    # Corporate: 100k - 50M
    # Retail: 10k - 500k
    notional_corporate = np.random.lognormal(mean=13, sigma=1.5, size=n_corporate)  # ~450k median
    notional_retail = np.random.lognormal(mean=11, sigma=1.0, size=n_retail)  # ~60k median
    notional = np.concatenate([notional_corporate, notional_retail])
    notional = np.clip(notional, 10000, 50000000)
    
    # EAD = Notional (pour loans on-balance sheet)
    ead = notional.copy()
    
    # PD (Probability of Default)
    # Corporate: 0.1% - 10%
    # Retail: 0.5% - 15%
    pd_corporate = np.random.beta(a=1.5, b=50, size=n_corporate) * 0.10  # Median ~1.5%
    pd_retail = np.random.beta(a=2, b=30, size=n_retail) * 0.15  # Median ~3%
    pd_values = np.concatenate([pd_corporate, pd_retail])
    
    # LGD (Loss Given Default)
    # Corporate: 30% - 60%
    # Retail: 40% - 70%
    lgd_corporate = np.random.beta(a=4, b=4, size=n_corporate) * 0.3 + 0.3  # 30-60%
    lgd_retail = np.random.beta(a=4, b=4, size=n_retail) * 0.3 + 0.4  # 40-70%
    lgd = np.concatenate([lgd_corporate, lgd_retail])
    
    # CCF (Credit Conversion Factor) = 1.0 pour loans on-BS
    ccf = np.ones(n_loans)
    
    # MTM = Notional (simplified)
    mtm = notional.copy()
    
    # Desk
    desks = np.random.choice(['Corporate Banking', 'Retail Banking', 'SME'], size=n_loans)
    
    # Is Retail
    is_retail = np.array([False] * n_corporate + [True] * n_retail)
    
    # Exposure Class
    exposure_class = np.where(is_retail, 'Retail', 'Corporate')
    
    # Netting set (N/A pour loans)
    netting_set_id = [None] * n_loans
    
    # Collateral (simplified: 30% des loans ont du collateral)
    has_collateral = np.random.rand(n_loans) < 0.3
    collateral_value = np.where(has_collateral, notional * np.random.uniform(0.5, 0.9, n_loans), 0)
    
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

