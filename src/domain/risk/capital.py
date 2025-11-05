"""
Module de calcul des ratios de capital.

Ce module implémente le calcul des ratios de capital selon CRR/CRD IV:
- CET1 Ratio
- Tier 1 Ratio
- Total Capital Ratio
- Leverage Ratio

Optimisations:
- Calculs simples et déterministes
- Performance: ≤ 0.2s
"""


import pandas as pd


def compute_capital_ratios(
    rwa_df: pd.DataFrame,
    own_funds: dict | pd.DataFrame | None = None
) -> dict[str, float]:
    """
    Calcule les ratios de capital réglementaires.

    Args:
        rwa_df: DataFrame avec colonne 'rwa_amount'
        own_funds: Fonds propres (dict ou DataFrame)
            Si None, utilise des valeurs simulées (12% CET1)

            Format dict attendu:
            {
                'cet1_capital': float,
                'tier1_capital': float,
                'total_capital': float,
                'total_assets': float  # Pour leverage ratio
            }

    Returns:
        Dict avec clés:
        - cet1_ratio (float): Ratio CET1 (%)
        - tier1_ratio (float): Ratio Tier 1 (%)
        - total_capital_ratio (float): Ratio Total Capital (%)
        - leverage_ratio (float): Leverage Ratio (%)

        Valeurs additionnelles:
        - total_rwa (float): Total RWA
        - cet1_capital, tier1_capital, total_capital

    Performance:
        - ≤ 0.2s
    """
    # Validation
    if 'rwa_amount' not in rwa_df.columns:
        raise KeyError("Colonne 'rwa_amount' manquante dans rwa_df")

    # Calculer le total RWA
    total_rwa = float(rwa_df['rwa_amount'].sum())

    # Gérer les fonds propres
    if own_funds is None:
        # Simuler des fonds propres (12% CET1, 13.5% Tier1, 15% Total)
        cet1_capital = total_rwa * 0.12
        tier1_capital = total_rwa * 0.135
        total_capital = total_rwa * 0.15
        total_assets = total_rwa * 10  # Approximation pour leverage ratio

    elif isinstance(own_funds, dict):
        cet1_capital = own_funds.get('cet1_capital', total_rwa * 0.12)
        tier1_capital = own_funds.get('tier1_capital', total_rwa * 0.135)
        total_capital = own_funds.get('total_capital', total_rwa * 0.15)
        total_assets = own_funds.get('total_assets', total_rwa * 10)

    elif isinstance(own_funds, pd.DataFrame):
        # Si DataFrame, prendre la première ligne
        if len(own_funds) > 0:
            cet1_capital = float(own_funds.iloc[0].get('cet1_capital', total_rwa * 0.12))
            tier1_capital = float(own_funds.iloc[0].get('tier1_capital', total_rwa * 0.135))
            total_capital = float(own_funds.iloc[0].get('total_capital', total_rwa * 0.15))
            total_assets = float(own_funds.iloc[0].get('total_assets', total_rwa * 10))
        else:
            cet1_capital = total_rwa * 0.12
            tier1_capital = total_rwa * 0.135
            total_capital = total_rwa * 0.15
            total_assets = total_rwa * 10

    else:
        raise TypeError(f"own_funds doit être dict, DataFrame ou None, reçu: {type(own_funds)}")

    # Calculer les ratios
    cet1_ratio = (cet1_capital / total_rwa * 100) if total_rwa > 0 else 0.0
    tier1_ratio = (tier1_capital / total_rwa * 100) if total_rwa > 0 else 0.0
    total_capital_ratio = (total_capital / total_rwa * 100) if total_rwa > 0 else 0.0

    # Leverage Ratio = Tier 1 Capital / Total Assets
    leverage_ratio = (tier1_capital / total_assets * 100) if total_assets > 0 else 0.0

    return {
        'cet1_ratio': round(cet1_ratio, 2),
        'tier1_ratio': round(tier1_ratio, 2),
        'total_capital_ratio': round(total_capital_ratio, 2),
        'leverage_ratio': round(leverage_ratio, 2),
        'total_rwa': round(total_rwa, 2),
        'cet1_capital': round(cet1_capital, 2),
        'tier1_capital': round(tier1_capital, 2),
        'total_capital': round(total_capital, 2)
    }

