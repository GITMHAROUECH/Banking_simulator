"""
Service d'orchestration pour la consolidation IFRS et la réconciliation compta-risque.

Ce service coordonne la consolidation des états financiers et la réconciliation
entre les données comptables et les données de risque.
"""


import pandas as pd

from src.domain.consolidation import (
    consolidate_statements,
    perform_intercompany_eliminations,
    reconcile_ledger_vs_risk,
)


def consolidate_and_reconcile(
    entities_df: pd.DataFrame,
    trial_balance_df: pd.DataFrame,
    fx_rates_df: pd.DataFrame | None = None,
    thresholds: dict[str, float] | None = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Orchestre la consolidation IFRS et la réconciliation compta-risque.

    Args:
        entities_df: Structure de groupe avec colonnes:
            - entity_id, parent_id, ownership_pct, method, currency
        trial_balance_df: Balance générale avec colonnes:
            - entity_id, account, amount, currency, period
        fx_rates_df: Taux de change optionnel avec colonnes:
            - from_ccy, to_ccy, rate, period
        thresholds: Seuils de classification des écarts (optionnel)
            - minor: float (ex: 0.05 = 5%)
            - critical: float (ex: 0.10 = 10%)

    Returns:
        Tuple de 2 DataFrames:
            - consolidated_df: États consolidés avec éliminations
            - variances_df: Écarts de réconciliation classifiés

    Raises:
        ValueError: Si entities_df ou trial_balance_df sont vides
    """
    # Validation
    if entities_df.empty:
        raise ValueError("entities_df ne peut pas être vide")
    if trial_balance_df.empty:
        raise ValueError("trial_balance_df ne peut pas être vide")

    # Validation colonnes entities_df
    required_entities_cols = ['entity_id', 'ownership_pct', 'method', 'currency']
    missing_cols = [col for col in required_entities_cols if col not in entities_df.columns]
    if missing_cols:
        raise ValueError(f"Colonnes manquantes dans entities_df: {missing_cols}")

    # Validation colonnes trial_balance_df
    required_tb_cols = ['entity_id', 'account', 'amount', 'period']
    missing_cols = [col for col in required_tb_cols if col not in trial_balance_df.columns]
    if missing_cols:
        raise ValueError(f"Colonnes manquantes dans trial_balance_df: {missing_cols}")

    # Étape 1: Consolidation IFRS
    consolidated_df = consolidate_statements(
        entities_df=entities_df,
        trial_balance_df=trial_balance_df,
        fx_rates_df=fx_rates_df,
        target_currency='EUR'
    )

    # Étape 2: Éliminations intra-groupe
    consolidated_df = perform_intercompany_eliminations(consolidated_df)

    # Étape 3: Réconciliation compta-risque
    # Pour la réconciliation, on utilise les données consolidées comme "ledger"
    # et on suppose que les données de risque sont dans trial_balance_df
    # (en pratique, il faudrait un risk_df séparé, mais pour I5 on simplifie)

    # Préparer les données pour la réconciliation
    ledger_df = consolidated_df[['entity_id', 'account', 'amount_consolidated', 'period']].copy()
    ledger_df.columns = ['entity_id', 'account', 'amount', 'period']

    # Pour risk_df, on utilise trial_balance_df (simplifié pour I5)
    risk_df = trial_balance_df[['entity_id', 'account', 'amount', 'period']].copy()
    risk_df.columns = ['entity_id', 'risk_bucket', 'amount', 'period']

    # Seuils par défaut si non fournis
    if thresholds is None:
        thresholds = {'minor': 0.05, 'critical': 0.10}

    # Réconciliation
    variances_df = reconcile_ledger_vs_risk(
        ledger_df=ledger_df,
        risk_df=risk_df,
        thresholds=thresholds
    )

    return consolidated_df, variances_df

