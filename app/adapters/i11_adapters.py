"""
Adaptateurs I11 pour l'UI - Exposition des fonctions run_id.
Dépile les tuples (result, cache_hit) pour l'UI.
"""
from typing import Any

import pandas as pd

from src.services.exposure_service import generate_exposures, load_exposures, list_runs
from src.services.reconciliation_service import (
    get_reconciliation_summary,
    reconcile_ledger_vs_risk,
)
from src.services.reporting_service import create_corep_finrep_stubs
from src.services.risk_service import (
    compute_capital_ratios_from_run,
    compute_lcr_from_run,
    compute_rwa_from_run,
    compute_saccr_from_run,
)


# ============================================================================
# Adaptateurs pour génération d'exposures
# ============================================================================

def generate_exposures_advanced(
    run_id: str,
    config: dict | None = None,
    seed: int = 42,
    use_cache: bool = True,
) -> tuple[pd.DataFrame, bool]:
    """
    Génère les exposures pour un run_id (UI adapter).
    
    Returns:
        (DataFrame, cache_hit)
    """
    return generate_exposures(run_id, config, seed, use_cache)


def load_exposures_advanced(run_id: str) -> pd.DataFrame:
    """
    Charge les exposures pour un run_id (UI adapter).

    Returns:
        DataFrame
    """
    return load_exposures(run_id)


def list_runs_advanced(limit: int = 50) -> pd.DataFrame:
    """
    Liste les runs de simulation disponibles (UI adapter).

    Args:
        limit: Nombre maximum de runs à retourner

    Returns:
        DataFrame avec colonnes: run_id, run_date, status, total_exposures, total_notional
    """
    return list_runs(limit)


# ============================================================================
# Adaptateurs pour calculs de risque
# ============================================================================

def compute_rwa_from_run_advanced(
    run_id: str,
    params: dict | None = None,
    use_cache: bool = True,
) -> tuple[dict, bool]:
    """
    Calcule RWA à partir d'un run_id (UI adapter).
    
    Returns:
        (dict résultats, cache_hit)
    """
    return compute_rwa_from_run(run_id, params, use_cache)


def compute_saccr_from_run_advanced(
    run_id: str,
    params: dict | None = None,
    use_cache: bool = True,
) -> tuple[dict, bool]:
    """
    Calcule SA-CCR à partir d'un run_id (UI adapter).
    
    Returns:
        (dict résultats, cache_hit)
    """
    return compute_saccr_from_run(run_id, params, use_cache)


def compute_lcr_from_run_advanced(
    run_id: str,
    params: dict | None = None,
    use_cache: bool = True,
) -> tuple[dict, bool]:
    """
    Calcule LCR à partir d'un run_id (UI adapter).
    
    Returns:
        (dict résultats, cache_hit)
    """
    return compute_lcr_from_run(run_id, params, use_cache)


def compute_capital_ratios_from_run_advanced(
    run_id: str,
    params: dict | None = None,
    use_cache: bool = True,
) -> tuple[dict, bool]:
    """
    Calcule les ratios de capital à partir d'un run_id (UI adapter).
    
    Returns:
        (dict résultats, cache_hit)
    """
    return compute_capital_ratios_from_run(run_id, params, use_cache)


# ============================================================================
# Adaptateurs pour réconciliation
# ============================================================================

def reconcile_ledger_vs_risk_advanced(run_id: str) -> dict:
    """
    Réconcilie ledger vs risk pour un run_id (UI adapter).
    
    Returns:
        Dict avec 'summary' et 'details'
    """
    df_details = reconcile_ledger_vs_risk(run_id)
    summary = get_reconciliation_summary(run_id)
    
    return {
        'summary': summary,
        'details': df_details,
    }


# ============================================================================
# Adaptateurs pour reporting
# ============================================================================

def create_corep_finrep_stubs_advanced(run_id: str) -> dict[str, pd.DataFrame]:
    """
    Pré-remplit COREP/FINREP pour un run_id (UI adapter).
    
    Returns:
        Dict avec clés: corep_c34, corep_c07, corep_c08, corep_leverage, corep_lcr, finrep_f01, finrep_f18
    """
    return create_corep_finrep_stubs(run_id)

