"""
Réconciliation Compta-Risque - Logique métier pure.

Ce module implémente la réconciliation entre les données comptables (Ledger)
et les données de risque (Risk), avec classification des écarts et identification
des causes probables.
"""


import numpy as np
import pandas as pd


def reconcile_ledger_vs_risk(
    ledger_df: pd.DataFrame,
    risk_df: pd.DataFrame,
    thresholds: dict[str, float],
) -> pd.DataFrame:
    """
    Réconcilie les données comptables vs risque.

    Args:
        ledger_df: Données comptables avec colonnes:
            - entity_id: str
            - account: str
            - amount: float
            - period: str
        risk_df: Données de risque avec colonnes:
            - entity_id: str
            - risk_bucket: str
            - amount: float
            - period: str
        thresholds: Seuils de classification:
            - minor: float (seuil mineur, ex: 0.05 = 5%)
            - critical: float (seuil critique, ex: 0.10 = 10%)

    Returns:
        DataFrame avec colonnes:
            - key: str (clé de réconciliation)
            - ledger_amount: float
            - risk_amount: float
            - delta_abs: float (écart absolu)
            - delta_pct: float (écart relatif en %)
            - severity: str (OK, Minor, Critical)
            - root_cause_hint: str (cause probable)
    """
    # Agréger les données par entité et période
    ledger_agg = ledger_df.groupby(['entity_id', 'period'], observed=True).agg({
        'amount': 'sum'
    }).reset_index()
    ledger_agg.columns = ['entity_id', 'period', 'ledger_amount']

    risk_agg = risk_df.groupby(['entity_id', 'period'], observed=True).agg({
        'amount': 'sum'
    }).reset_index()
    risk_agg.columns = ['entity_id', 'period', 'risk_amount']

    # Joindre les deux sources
    variances_df = ledger_agg.merge(
        risk_agg,
        on=['entity_id', 'period'],
        how='outer',
        suffixes=('_ledger', '_risk')
    )

    # Remplir les valeurs manquantes
    variances_df['ledger_amount'] = variances_df['ledger_amount'].fillna(0.0).astype('float32')
    variances_df['risk_amount'] = variances_df['risk_amount'].fillna(0.0).astype('float32')

    # Calculer les écarts
    variances_df['delta_abs'] = (
        variances_df['ledger_amount'] - variances_df['risk_amount']
    ).astype('float32')

    # Calculer l'écart relatif (en %)
    variances_df['delta_pct'] = np.where(
        variances_df['risk_amount'] != 0,
        (variances_df['delta_abs'] / variances_df['risk_amount'].abs()) * 100,
        np.where(
            variances_df['ledger_amount'] != 0,
            100.0,  # Écart de 100% si risk_amount = 0 mais ledger_amount != 0
            0.0     # Pas d'écart si les deux sont à 0
        )
    ).astype('float32')

    # Créer la clé de réconciliation
    variances_df['key'] = (
        variances_df['entity_id'].astype(str) + '_' +
        variances_df['period'].astype(str)
    )

    # Classifier les écarts
    variances_df = classify_variances(variances_df, thresholds)

    # Identifier les causes probables
    variances_df['root_cause_hint'] = variances_df.apply(
        _identify_root_cause, axis=1
    )

    # Optimisation dtypes
    variances_df['entity_id'] = variances_df['entity_id'].astype('category')
    variances_df['period'] = variances_df['period'].astype('category')
    variances_df['severity'] = variances_df['severity'].astype('category')

    return variances_df


def classify_variances(
    variances_df: pd.DataFrame,
    thresholds: dict[str, float]
) -> pd.DataFrame:
    """
    Classifie les écarts selon les seuils.

    Args:
        variances_df: DataFrame avec colonnes delta_pct
        thresholds: Seuils de classification (minor, critical)

    Returns:
        DataFrame avec colonne severity ajoutée
    """
    df = variances_df.copy()

    minor_threshold = thresholds.get('minor', 0.05) * 100  # Convertir en %
    critical_threshold = thresholds.get('critical', 0.10) * 100

    # Classifier selon les seuils
    df['severity'] = 'OK'
    df.loc[df['delta_pct'].abs() >= minor_threshold, 'severity'] = 'Minor'
    df.loc[df['delta_pct'].abs() >= critical_threshold, 'severity'] = 'Critical'

    return df


def _identify_root_cause(row: pd.Series) -> str:
    """
    Identifie la cause probable de l'écart (heuristique).

    Args:
        row: Ligne du DataFrame de variances

    Returns:
        Cause probable (str)
    """
    ledger = row['ledger_amount']
    risk = row['risk_amount']
    delta_pct = abs(row['delta_pct'])

    # Heuristiques simples
    if ledger == 0 and risk != 0:
        return "Missing ledger data"
    elif risk == 0 and ledger != 0:
        return "Missing risk data"
    elif delta_pct < 5:
        return "Rounding differences"
    elif delta_pct < 10:
        return "Timing differences or mapping issues"
    elif delta_pct < 20:
        return "Scope differences (perimeter mismatch)"
    else:
        return "Significant variance - manual investigation required"


def aggregate_variances_by_entity(variances_df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrège les écarts par entité.

    Args:
        variances_df: DataFrame de variances

    Returns:
        DataFrame agrégé par entité
    """
    agg_df = variances_df.groupby('entity_id', observed=True).agg({
        'ledger_amount': 'sum',
        'risk_amount': 'sum',
        'delta_abs': 'sum',
    }).reset_index()

    # Recalculer delta_pct agrégé
    agg_df['delta_pct'] = np.where(
        agg_df['risk_amount'] != 0,
        (agg_df['delta_abs'] / agg_df['risk_amount'].abs()) * 100,
        0.0
    ).astype('float32')

    return agg_df


def export_variances_summary(variances_df: pd.DataFrame) -> dict[str, int]:
    """
    Exporte un résumé des écarts par sévérité.

    Args:
        variances_df: DataFrame de variances

    Returns:
        Dict avec compteurs par sévérité
    """
    summary = variances_df['severity'].value_counts().to_dict()

    # S'assurer que toutes les sévérités sont présentes
    for severity in ['OK', 'Minor', 'Critical']:
        if severity not in summary:
            summary[severity] = 0

    return summary

