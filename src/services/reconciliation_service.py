"""
Service de réconciliation ledger vs risk - I11.
Compare les agrégats comptables (bilan) avec les agrégats risques.
"""
import pandas as pd

from src.services.exposure_service import load_exposures, snapshot_balance_sheet
from src.services.risk_service import compute_rwa_from_run


def reconcile_ledger_vs_risk(run_id: str) -> pd.DataFrame:
    """
    Réconcilie le bilan (ledger) vs les agrégats risques.
    
    Args:
        run_id: Identifiant du run
    
    Returns:
        DataFrame avec colonnes:
            - category: Catégorie (Loan, Bond, etc.)
            - entity: Entité
            - currency: Devise
            - ledger_amount: Montant bilan
            - risk_ead: EAD risque
            - difference: Écart
            - difference_pct: Écart en %
    """
    # 1. Charger le bilan
    df_assets, df_liabilities = snapshot_balance_sheet(run_id)
    
    # 2. Charger les exposures
    df_exp = load_exposures(run_id)
    
    # 3. Agréger les exposures par catégorie/entity/currency
    df_risk = df_exp.groupby(['product_type', 'entity', 'currency']).agg({
        'ead': 'sum',
        'notional': 'sum',
    }).reset_index()
    
    df_risk.rename(columns={'product_type': 'category'}, inplace=True)
    
    # 4. Merger bilan et risque
    df_merged = df_assets.merge(
        df_risk,
        on=['category', 'entity', 'currency'],
        how='outer',
        suffixes=('_ledger', '_risk')
    )
    
    # 5. Calculer les écarts
    # Après le merge, les colonnes peuvent avoir des suffixes
    if 'amount' in df_merged.columns:
        df_merged['ledger_amount'] = df_merged['amount'].fillna(0)
    elif 'amount_ledger' in df_merged.columns:
        df_merged['ledger_amount'] = df_merged['amount_ledger'].fillna(0)
    else:
        df_merged['ledger_amount'] = 0
    
    if 'ead' in df_merged.columns:
        df_merged['risk_ead'] = df_merged['ead'].fillna(0)
    elif 'ead_risk' in df_merged.columns:
        df_merged['risk_ead'] = df_merged['ead_risk'].fillna(0)
    else:
        df_merged['risk_ead'] = 0
    df_merged['difference'] = df_merged['ledger_amount'] - df_merged['risk_ead']
    df_merged['difference_pct'] = (
        df_merged['difference'] / df_merged['ledger_amount'] * 100
    ).fillna(0)
    
    # 6. Sélectionner les colonnes
    df_result = df_merged[[
        'category', 'entity', 'currency',
        'ledger_amount', 'risk_ead', 'difference', 'difference_pct'
    ]]
    
    # 7. Trier par écart absolu décroissant
    df_result['abs_difference'] = df_result['difference'].abs()
    df_result = df_result.sort_values('abs_difference', ascending=False).drop('abs_difference', axis=1)
    
    return df_result


def reconcile_rwa_vs_exposures(run_id: str) -> pd.DataFrame:
    """
    Réconcilie les RWA calculés vs les exposures.
    
    Args:
        run_id: Identifiant du run
    
    Returns:
        DataFrame avec colonnes:
            - exposure_class: Classe d'exposition
            - total_ead: EAD total
            - total_rwa: RWA total
            - rwa_density: Densité RWA (%)
    """
    # 1. Charger les exposures
    df_exp = load_exposures(run_id)
    
    # 2. Calculer RWA
    rwa_result, _ = compute_rwa_from_run(run_id)
    
    # 3. Agréger par exposure_class
    df_agg = df_exp.groupby('exposure_class').agg({
        'ead': 'sum',
    }).reset_index()
    
    # 4. Ajouter RWA depuis le résultat
    rwa_by_class = rwa_result.get('by_exposure_class', {})
    df_agg['total_rwa'] = df_agg['exposure_class'].map(rwa_by_class).fillna(0)
    
    # 5. Calculer densité
    df_agg['rwa_density'] = (df_agg['total_rwa'] / df_agg['ead'] * 100).fillna(0)
    
    # 6. Renommer colonnes
    df_agg.rename(columns={'ead': 'total_ead'}, inplace=True)
    
    return df_agg


def get_reconciliation_summary(run_id: str) -> dict:
    """
    Retourne un résumé de réconciliation pour un run_id.
    
    Args:
        run_id: Identifiant du run
    
    Returns:
        Dict avec:
            - total_ledger: Total bilan
            - total_risk_ead: Total EAD risque
            - total_difference: Écart total
            - max_difference_category: Catégorie avec le plus grand écart
            - reconciliation_status: 'OK' ou 'ISSUES'
    """
    df_recon = reconcile_ledger_vs_risk(run_id)
    
    total_ledger = float(df_recon['ledger_amount'].sum())
    total_risk_ead = float(df_recon['risk_ead'].sum())
    total_difference = float(df_recon['difference'].sum())
    
    # Trouver la catégorie avec le plus grand écart absolu
    max_diff_row = df_recon.loc[df_recon['difference'].abs().idxmax()]
    max_difference_category = {
        'category': max_diff_row['category'],
        'entity': max_diff_row['entity'],
        'difference': float(max_diff_row['difference']),
        'difference_pct': float(max_diff_row['difference_pct']),
    }
    
    # Statut (OK si écart < 1%)
    reconciliation_status = 'OK' if abs(total_difference / total_ledger * 100) < 1 else 'ISSUES'
    
    return {
        'run_id': run_id,
        'total_ledger': total_ledger,
        'total_risk_ead': total_risk_ead,
        'total_difference': total_difference,
        'difference_pct': (total_difference / total_ledger * 100) if total_ledger > 0 else 0,
        'max_difference_category': max_difference_category,
        'reconciliation_status': reconciliation_status,
    }

