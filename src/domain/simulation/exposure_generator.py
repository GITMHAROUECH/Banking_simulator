"""
Orchestrateur de génération d'expositions - I11.
Génère toutes les expositions pour un run_id en appelant les générateurs individuels.
"""
import uuid

import pandas as pd

from src.domain.simulation.generators.bonds import generate_bonds
from src.domain.simulation.generators.deposits import generate_deposits
from src.domain.simulation.generators.derivatives import generate_derivatives
from src.domain.simulation.generators.equities import generate_equities
from src.domain.simulation.generators.loans import generate_loans
from src.domain.simulation.generators.off_bs import generate_off_bs


def generate_all_exposures(run_id: str, config: dict, seed: int = 42) -> pd.DataFrame:
    """
    Génère toutes les expositions pour un run_id.
    
    Args:
        run_id: Identifiant unique du run
        config: Configuration contenant les paramètres pour chaque générateur
        seed: Seed de base pour reproductibilité
    
    Returns:
        DataFrame avec toutes les expositions (schéma canonique)
    
    Exemple de config:
        {
            'n_loans': 10000,
            'n_bonds': 5000,
            'n_deposits': 15000,
            'n_derivatives': 3000,
            'n_off_bs': 2000,
            'n_equities': 1000,
            'entities': ['EU', 'US', 'CN'],
            'currencies': ['EUR', 'USD', 'CNY'],
            'retail_ratio': 0.4,
            'sovereign_ratio': 0.6,
        }
    """
    dfs = []
    
    # Générer chaque type de produit avec un seed différent
    # (pour éviter corrélation entre produits)
    
    # 1. Loans
    if config.get('n_loans', 0) > 0:
        df_loans = generate_loans(config, seed)
        dfs.append(df_loans)
    
    # 2. Bonds
    if config.get('n_bonds', 0) > 0:
        df_bonds = generate_bonds(config, seed + 1)
        dfs.append(df_bonds)
    
    # 3. Deposits
    if config.get('n_deposits', 0) > 0:
        df_deposits = generate_deposits(config, seed + 2)
        dfs.append(df_deposits)
    
    # 4. Derivatives
    if config.get('n_derivatives', 0) > 0:
        df_derivatives = generate_derivatives(config, seed + 3)
        dfs.append(df_derivatives)
    
    # 5. Off-Balance Sheet
    if config.get('n_off_bs', 0) > 0:
        df_off_bs = generate_off_bs(config, seed + 4)
        dfs.append(df_off_bs)
    
    # 6. Equities
    if config.get('n_equities', 0) > 0:
        df_equities = generate_equities(config, seed + 5)
        dfs.append(df_equities)
    
    # Concaténer tous les DataFrames
    if not dfs:
        # Aucune exposition générée, retourner un DataFrame vide avec le schéma
        return pd.DataFrame(columns=[
            'id', 'run_id', 'product_type', 'counterparty_id', 'booking_date', 'maturity_date',
            'currency', 'notional', 'ead', 'pd', 'lgd', 'ccf', 'maturity_years', 'mtm',
            'desk', 'entity', 'is_retail', 'exposure_class', 'netting_set_id', 'collateral_value'
        ])
    
    df_all = pd.concat(dfs, ignore_index=True)
    
    # Ajouter le run_id
    df_all['run_id'] = run_id
    
    # Réordonner les colonnes
    columns_order = [
        'id', 'run_id', 'product_type', 'counterparty_id', 'booking_date', 'maturity_date',
        'currency', 'notional', 'ead', 'pd', 'lgd', 'ccf', 'maturity_years', 'mtm',
        'desk', 'entity', 'is_retail', 'exposure_class', 'netting_set_id', 'collateral_value'
    ]
    df_all = df_all[columns_order]
    
    return df_all


def get_default_config() -> dict:
    """
    Retourne une configuration par défaut pour la génération d'expositions.
    
    Returns:
        Configuration par défaut
    """
    return {
        'n_loans': 10000,
        'n_bonds': 5000,
        'n_deposits': 15000,
        'n_derivatives': 3000,
        'n_off_bs': 2000,
        'n_equities': 1000,
        'entities': ['EU', 'US', 'CN'],
        'currencies': ['EUR', 'USD', 'CNY'],
        'retail_ratio': 0.4,
        'sovereign_ratio': 0.6,
        'n_netting_sets': 200,
    }

