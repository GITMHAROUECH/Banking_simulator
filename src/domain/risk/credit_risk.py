"""
Module de calcul du risque de crédit (RWA) selon CRR3.

Ce module implémente les approches Standardisée et IRB Foundation
pour le calcul des Risk-Weighted Assets (RWA).

Optimisations:
- Vectorisation NumPy/Pandas pour performance
- Dtypes optimisés (float32, category)
- Déterminisme garanti
"""


import numpy as np
import pandas as pd


def calculate_rwa_advanced(positions_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule les RWA (Risk-Weighted Assets) selon CRR3.

    Cette fonction implémente:
    - Approche IRB Foundation pour Retail, Corporate, SME
    - Approche Standardisée pour Sovereign, Bank, autres
    - Support des dérivés (SA-CCR stub pour I2)

    Args:
        positions_df: DataFrame avec colonnes minimales:
            - position_id (str): Identifiant unique
            - entity_id (str): Entité bancaire
            - exposure_class (str): Classe d'exposition CRR3
            - ead (float): Exposure At Default
            - pd (float): Probability of Default
            - lgd (float): Loss Given Default
            - maturity (float): Maturité en années

    Returns:
        DataFrame avec colonnes minimales:
        - position_id (str): Identifiant unique
        - rwa_amount (float32): Montant RWA
        - rwa_density (float32): Densité RWA (%)
        - approach (str): Approche utilisée

        Colonnes additionnelles:
        - entity_id, exposure_class, ead, pd, lgd, maturity

    Performance:
        - 10,000 positions: ≤ 3s

    Raises:
        KeyError: Si colonnes minimales manquantes
    """
    # Validation des colonnes requises
    required_cols = ['position_id', 'entity_id', 'exposure_class', 'ead', 'pd', 'lgd', 'maturity']
    missing_cols = set(required_cols) - set(positions_df.columns)
    if missing_cols:
        raise KeyError(f"Colonnes manquantes: {missing_cols}")

    # Copie pour éviter les modifications du DF original
    df = positions_df[required_cols].copy()

    # Initialiser les colonnes de résultat
    df['rwa_amount'] = 0.0
    df['approach'] = 'Unknown'
    df['risk_weight'] = 0.0

    # === Approche IRB Foundation pour Retail ===
    retail_mask = df['exposure_class'].isin(['Retail_Mortgages', 'Retail_Other'])
    if retail_mask.any():
        df.loc[retail_mask, 'rwa_amount'] = _calculate_rwa_irb_retail(
            df.loc[retail_mask, 'exposure_class'].values,  # type: ignore[arg-type]
            df.loc[retail_mask, 'ead'].values,  # type: ignore[arg-type]
            df.loc[retail_mask, 'pd'].values,  # type: ignore[arg-type]
            df.loc[retail_mask, 'lgd'].values,  # type: ignore[arg-type]
            df.loc[retail_mask, 'maturity'].values  # type: ignore[arg-type]
        )
        df.loc[retail_mask, 'approach'] = 'IRB_Foundation'

    # === Approche IRB Foundation pour Corporate ===
    corporate_mask = df['exposure_class'] == 'Corporate'
    if corporate_mask.any():
        df.loc[corporate_mask, 'rwa_amount'] = _calculate_rwa_irb_corporate(
            df.loc[corporate_mask, 'ead'].values,  # type: ignore[arg-type]
            df.loc[corporate_mask, 'pd'].values,  # type: ignore[arg-type]
            df.loc[corporate_mask, 'lgd'].values,  # type: ignore[arg-type]
            df.loc[corporate_mask, 'maturity'].values  # type: ignore[arg-type]
        )
        df.loc[corporate_mask, 'approach'] = 'IRB_Foundation'

    # === Approche IRB SME (avec réduction 23.81%) ===
    sme_mask = df['exposure_class'] == 'SME'
    if sme_mask.any():
        df.loc[sme_mask, 'rwa_amount'] = _calculate_rwa_irb_sme(
            df.loc[sme_mask, 'ead'].values,  # type: ignore[arg-type]
            df.loc[sme_mask, 'pd'].values,  # type: ignore[arg-type]
            df.loc[sme_mask, 'lgd'].values,  # type: ignore[arg-type]
            df.loc[sme_mask, 'maturity'].values  # type: ignore[arg-type]
        )
        df.loc[sme_mask, 'approach'] = 'IRB_SME'

    # === Approche Standardisée pour Sovereign ===
    sovereign_mask = df['exposure_class'] == 'Sovereign'
    if sovereign_mask.any():
        rwa, rw = _calculate_rwa_standardised_sovereign(
            df.loc[sovereign_mask, 'ead'].values,  # type: ignore[arg-type]
            df.loc[sovereign_mask, 'pd'].values  # type: ignore[arg-type]
        )
        df.loc[sovereign_mask, 'rwa_amount'] = rwa
        df.loc[sovereign_mask, 'risk_weight'] = rw
        df.loc[sovereign_mask, 'approach'] = 'Standardised'

    # === Approche Standardisée pour Bank ===
    bank_mask = df['exposure_class'] == 'Bank'
    if bank_mask.any():
        rwa, rw = _calculate_rwa_standardised_bank(
            df.loc[bank_mask, 'ead'].values,  # type: ignore[arg-type]
            df.loc[bank_mask, 'pd'].values  # type: ignore[arg-type]
        )
        df.loc[bank_mask, 'rwa_amount'] = rwa
        df.loc[bank_mask, 'risk_weight'] = rw
        df.loc[bank_mask, 'approach'] = 'Standardised'

    # === Autres expositions (100% RW par défaut) ===
    other_mask = ~(retail_mask | corporate_mask | sme_mask | sovereign_mask | bank_mask)
    if other_mask.any():
        df.loc[other_mask, 'rwa_amount'] = df.loc[other_mask, 'ead'] * 1.0
        df.loc[other_mask, 'risk_weight'] = 1.0
        df.loc[other_mask, 'approach'] = 'Standardised'

    # Calculer la densité RWA (%)
    df['rwa_density'] = np.where(
        df['ead'] > 0,
        (df['rwa_amount'] / df['ead']) * 100,
        0.0
    )

    # Optimiser les dtypes
    df['rwa_amount'] = df['rwa_amount'].astype('float32')
    df['rwa_density'] = df['rwa_density'].astype('float32')
    df['risk_weight'] = df['risk_weight'].astype('float32')
    df['approach'] = df['approach'].astype('category')

    return df


def _calculate_rwa_irb_retail(
    exposure_classes: np.ndarray,
    ead: np.ndarray,
    pd: np.ndarray,
    lgd: np.ndarray,
    maturity: np.ndarray
) -> np.ndarray:
    """
    Calcule RWA pour Retail selon IRB Foundation.

    Formule CRR3:
    - Corrélation: 0.15 (Mortgages), 0.04 (Other)
    - K = max(0, LGD * N((1-R)^-0.5 * G(PD) + (R/(1-R))^0.5 * G(0.999)) - PD * LGD) * MA
    - RWA = K * 12.5 * EAD
    """
    # Corrélation selon la classe
    correlation = np.where(
        exposure_classes == 'Retail_Mortgages',
        0.15,
        0.04
    )

    # Constantes
    z_score = 3.09  # Approximation G(0.999)

    # Calcul vectorisé du facteur de risque
    sqrt_corr = np.sqrt(correlation)
    sqrt_pd_variance = np.sqrt(pd * (1 - pd))

    risk_factor = lgd * (pd + sqrt_corr * z_score * sqrt_pd_variance)

    # Ajustement maturité (si > 1 an)
    maturity_adjustment = np.where(
        maturity > 1,
        np.clip((1 + (maturity - 2.5) * 0.11) / (1 + 1.5 * 0.11), 1.0, 5.0),
        1.0
    )

    # Capital requis K
    k = np.maximum(0, risk_factor - pd * lgd) * maturity_adjustment

    # RWA = K * 12.5 * EAD
    rwa = k * 12.5 * ead

    return rwa


def _calculate_rwa_irb_corporate(
    ead: np.ndarray,
    pd: np.ndarray,
    lgd: np.ndarray,
    maturity: np.ndarray
) -> np.ndarray:
    """
    Calcule RWA pour Corporate selon IRB Foundation.

    Formule CRR3 avec ajustement taille entreprise et maturité.
    """
    # Corrélation selon la taille (approximation)
    firm_size_factor = np.clip((ead / 1_000_000 - 5) / 45, 0, 1)

    exp_50pd = np.exp(-50 * pd)
    base_corr = 0.12 * (1 - exp_50pd) / (1 - np.exp(-50)) + \
                0.24 * (1 - (1 - exp_50pd) / (1 - np.exp(-50)))

    correlation = np.clip(base_corr - 0.04 * (1 - firm_size_factor), 0.12, 0.24)

    # Calcul du facteur de risque
    z_score = 3.09
    sqrt_corr = np.sqrt(correlation)
    sqrt_pd_variance = np.sqrt(pd * (1 - pd))

    risk_factor = lgd * (pd + sqrt_corr * z_score * sqrt_pd_variance)

    # Ajustement maturité (formule corporate complexe)
    b_factor = (0.11852 - 0.05478 * np.log(pd)) ** 2
    maturity_adjustment = np.where(
        maturity > 1,
        np.clip((1 + (maturity - 2.5) * b_factor) / (1 + 1.5 * b_factor), 1.0, 5.0),
        1.0
    )

    # Capital requis K
    k = np.maximum(0, risk_factor - pd * lgd) * maturity_adjustment

    # RWA = K * 12.5 * EAD
    rwa = k * 12.5 * ead

    return rwa


def _calculate_rwa_irb_sme(
    ead: np.ndarray,
    pd: np.ndarray,
    lgd: np.ndarray,
    maturity: np.ndarray
) -> np.ndarray:
    """
    Calcule RWA pour SME selon IRB avec réduction de 23.81%.

    Utilise la formule corporate puis applique la réduction SME.
    """
    # Corrélation SME (sans ajustement taille)
    exp_50pd = np.exp(-50 * pd)
    correlation = 0.12 * (1 - exp_50pd) / (1 - np.exp(-50)) + \
                  0.24 * (1 - (1 - exp_50pd) / (1 - np.exp(-50)))

    # Calcul du facteur de risque
    z_score = 3.09
    sqrt_corr = np.sqrt(correlation)
    sqrt_pd_variance = np.sqrt(pd * (1 - pd))

    risk_factor = lgd * (pd + sqrt_corr * z_score * sqrt_pd_variance)

    # Capital requis K (sans ajustement maturité pour SME)
    k = np.maximum(0, risk_factor - pd * lgd)

    # RWA = K * 12.5 * EAD * 0.7619 (réduction 23.81%)
    rwa = k * 12.5 * ead * 0.7619

    return rwa


def _calculate_rwa_standardised_sovereign(
    ead: np.ndarray,
    pd: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """
    Calcule RWA pour Sovereign selon approche standardisée.

    Pondérations selon la notation (approximée via PD):
    - PD ≤ 0.001: 0% (AAA à AA-)
    - PD ≤ 0.005: 20% (A+ à A-)
    - PD ≤ 0.01: 50% (BBB+ à BBB-)
    - PD ≤ 0.03: 100% (BB+ à B-)
    - PD > 0.03: 150% (< B-)

    Returns:
        Tuple (rwa, risk_weight)
    """
    risk_weight = np.select(
        [
            pd <= 0.001,
            pd <= 0.005,
            pd <= 0.01,
            pd <= 0.03
        ],
        [0.0, 0.20, 0.50, 1.00],
        default=1.50
    )

    rwa = ead * risk_weight

    return rwa, risk_weight


def _calculate_rwa_standardised_bank(
    ead: np.ndarray,
    pd: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """
    Calcule RWA pour Bank selon approche standardisée.

    Pondérations selon la notation (approximée via PD):
    - PD ≤ 0.002: 20%
    - PD ≤ 0.01: 50%
    - PD ≤ 0.02: 100%
    - PD > 0.02: 150%

    Returns:
        Tuple (rwa, risk_weight)
    """
    risk_weight = np.select(
        [
            pd <= 0.002,
            pd <= 0.01,
            pd <= 0.02
        ],
        [0.20, 0.50, 1.00],
        default=1.50
    )

    rwa = ead * risk_weight

    return rwa, risk_weight

