"""
Adaptateurs de compatibilité ascendante.

Ce module expose les signatures historiques attendues par l'UI,
en déléguant aux Services (I5) qui orchestrent le Domain (I1-I4).

Objectif : Préserver les imports existants dans les pages UI
sans modification, tout en utilisant la nouvelle architecture.

Note I6: Les services retournent maintenant des tuples (résultat, cache_hit).
Les adaptateurs extraient le résultat pour préserver la compatibilité.
"""

from typing import Any

import pandas as pd

# Imports depuis Services (I5)
from src.services import (
    compute_capital,
    compute_liquidity,
    compute_rwa,
    create_excel_export,
    run_simulation,
)


def generate_positions_advanced(
    num_positions: int,
    seed: int,
    config: dict[str, object] | None = None
) -> pd.DataFrame:
    """
    Génère des positions bancaires via simulation Monte Carlo.

    Signature historique préservée, délègue au service.
    """
    positions_df, _ = run_simulation(
        num_positions=num_positions,
        seed=seed,
        config=config,
        include_derivatives=False  # Par défaut, pas de dérivés
    )
    return positions_df


def calculate_rwa_advanced(positions_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule les RWA pour un portefeuille de positions.

    Signature historique préservée, délègue au service.
    """
    rwa_df, _ = compute_rwa(positions_df)
    return rwa_df


def calculate_liquidity_advanced(
    positions_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, Any]:
    """
    Calcule les métriques de liquidité (LCR, NSFR, ALMM).

    Signature historique préservée, délègue au service.
    """
    lcr_df, nsfr_df, almm_obj, _ = compute_liquidity(positions_df)
    return lcr_df, nsfr_df, almm_obj


def compute_capital_ratios(
    rwa_df: pd.DataFrame,
    own_funds: dict[str, float] | pd.DataFrame
) -> dict[str, float]:
    """
    Calcule les ratios de capital.

    Signature historique préservée, délègue au service.
    """
    capital_ratios, _ = compute_capital(rwa_df, own_funds)
    return capital_ratios


def create_excel_export_advanced(
    positions_df: pd.DataFrame,
    rwa_df: pd.DataFrame,
    lcr_df: pd.DataFrame,
    nsfr_df: pd.DataFrame,
    capital_ratios: dict[str, float]
) -> bytes:
    """
    Crée un export Excel multi-onglets.

    Signature historique préservée, délègue au service.
    """
    excel_bytes, _ = create_excel_export(
        positions_df=positions_df,
        rwa_df=rwa_df,
        lcr_df=lcr_df,
        nsfr_df=nsfr_df,
        capital_ratios=capital_ratios
    )
    return excel_bytes




# ============================================================================
# SA-CCR Adapters (I7b)
# ============================================================================

from src.services.risk_service import compute_saccr_ead, compute_saccr_rwa


def calculate_saccr_ead_advanced(
    trades_df: pd.DataFrame,
    collateral_df: pd.DataFrame | None = None,
    params: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """
    Calcule l'EAD selon SA-CCR pour un portefeuille de dérivés.

    Signature historique préservée, délègue au service.
    """
    ead_df, _ = compute_saccr_ead(trades_df, collateral_df, params)
    return ead_df


def calculate_saccr_rwa_advanced(
    trades_df: pd.DataFrame,
    collateral_df: pd.DataFrame | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Calcule les RWA selon SA-CCR pour un portefeuille de dérivés.

    Signature historique préservée, délègue au service.
    """
    rwa_dict, _ = compute_saccr_rwa(trades_df, collateral_df, params)
    return rwa_dict




# ============================================================================
# CVA Adapters (I7c)
# ============================================================================

from src.services.risk_service import (
    compute_counterparty_risk,
    compute_cva_capital,
    compute_cva_pricing,
)


def calculate_cva_capital_advanced(
    ead_df: pd.DataFrame, params: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Calcule le capital CVA selon l'approche BA-CVA.

    Signature historique préservée, délègue au service.
    """
    result, _ = compute_cva_capital(ead_df, params)
    return result


def calculate_cva_pricing_advanced(
    trades_df: pd.DataFrame, params: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Calcule le CVA pricing selon une approche simplifiée v1.

    Signature historique préservée, délègue au service.
    """
    result, _ = compute_cva_pricing(trades_df, params)
    return result


def calculate_counterparty_risk_advanced(
    trades_df: pd.DataFrame,
    collateral_df: pd.DataFrame | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Agrégateur de risque de contrepartie : SA-CCR + CVA.

    Signature historique préservée, délègue au service.
    """
    result, _ = compute_counterparty_risk(trades_df, collateral_df, params)
    return result





# ============================================================================
# Adaptateurs I8 - Export avancé
# ============================================================================


def create_export_advanced(
    outputs: dict[str, Any],
    *,
    format: str = "xlsx",
    compress: bool = False,
    include_corep_stubs: bool = True,
) -> bytes:
    """
    Crée un export multi-formats avec stubs COREP/LE/LCR (I8).

    Args:
        outputs: Dict avec clés positions, rwa, liquidity, ratios, saccr, metadata
        format: Format d'export ("xlsx", "parquet", "csv", "json")
        compress: Si True, compresse le résultat
        include_corep_stubs: Si True, inclut les stubs COREP/LE/LCR

    Returns:
        bytes: Contenu du fichier exporté
    """
    from src.services.reporting_service import create_export

    return create_export(
        outputs,
        format=format,  # type: ignore
        compress=compress,
        include_corep_stubs=include_corep_stubs,
    )


def create_pipeline_export_advanced(
    num_positions: int,
    seed: int,
    own_funds: dict[str, float],
    config: dict[str, object] | None = None,
    *,
    format: str = "xlsx",
    compress: bool = False,
    include_corep_stubs: bool = True,
) -> bytes:
    """
    Exécute le pipeline complet et génère un export multi-formats (I8).

    Args:
        num_positions: Nombre de positions à générer
        seed: Graine aléatoire
        own_funds: Fonds propres (cet1, tier1, total, leverage_exposure)
        config: Configuration optionnelle
        format: Format d'export ("xlsx", "parquet", "csv", "json")
        compress: Si True, compresse le résultat
        include_corep_stubs: Si True, inclut les stubs COREP/LE/LCR

    Returns:
        bytes: Contenu du fichier exporté
    """
    from src.services.pipeline_service import create_pipeline_export

    return create_pipeline_export(
        num_positions=num_positions,
        seed=seed,
        own_funds=own_funds,
        config=config,
        format=format,
        compress=compress,
        include_corep_stubs=include_corep_stubs,
    )





# ============================================================================
# Adaptateurs I8b - Listing artifacts et configurations
# ============================================================================


def list_artifacts_advanced(limit: int = 50) -> pd.DataFrame:
    """
    Liste les artifacts persistés (I8b).

    Args:
        limit: Nombre maximum d'artifacts à retourner

    Returns:
        DataFrame avec colonnes: artifact_id, params_hash, name, mime_type, size_bytes, created_at
    """
    from src.services.persistence_service import list_artifacts

    return list_artifacts(limit=limit)


def list_configurations_advanced(limit: int = 50) -> pd.DataFrame:
    """
    Liste les configurations persistées (I8b).

    Args:
        limit: Nombre maximum de configurations à retourner

    Returns:
        DataFrame avec colonnes: config_id, params_hash, name, num_positions, seed, created_at
    """
    from src.services.persistence_service import list_configurations

    return list_configurations(limit=limit)




# ============================================================================
# I11: Imports pour run_id pipeline
# ============================================================================

from app.adapters.i11_adapters import (
    compute_capital_ratios_from_run_advanced,
    compute_lcr_from_run_advanced,
    compute_rwa_from_run_advanced,
    compute_saccr_from_run_advanced,
    create_corep_finrep_stubs_advanced,
    generate_exposures_advanced,
    load_exposures_advanced,
    reconcile_ledger_vs_risk_advanced,
)




# ============================================================================
# I12: Adaptateurs IFRS 9 ECL
# ============================================================================

def compute_ecl_advanced_wrapper(
    run_id: str,
    scenario_id: str,
    *,
    horizon_months: int = 12,
    discount_rate: float = 5.0,
    use_cache: bool = True,
) -> tuple[dict, bool]:
    """
    Wrapper UI pour compute_ecl_advanced.
    
    Returns:
        (result, cache_hit)
    """
    from src.services.ifrs9_service import compute_ecl_advanced
    
    return compute_ecl_advanced(
        run_id=run_id,
        scenario_id=scenario_id,
        horizon_months=horizon_months,
        discount_rate=discount_rate,
        use_cache=use_cache,
    )


def create_scenario_overlay_advanced(
    scenario_id: str,
    name: str,
    description: str = '',
    pd_shift: float = 0.0,
    sicr_threshold_abs: float = 1.0,
    horizon_months: int = 12,
    discount_rate_value: float = 5.0,
) -> str:
    """
    Wrapper UI pour create_scenario_overlay.
    
    Returns:
        scenario_id
    """
    from src.services.ifrs9_service import create_scenario_overlay
    
    return create_scenario_overlay(
        scenario_id=scenario_id,
        name=name,
        description=description,
        pd_shift=pd_shift,
        sicr_threshold_abs=sicr_threshold_abs,
        horizon_months=horizon_months,
        discount_rate_value=discount_rate_value,
    )


def list_scenario_overlays_advanced():
    """
    Wrapper UI pour list_scenario_overlays.
    
    Returns:
        DataFrame
    """
    from src.services.ifrs9_service import list_scenario_overlays
    
    return list_scenario_overlays()


def create_finrep_from_run_advanced(
    run_id: str,
    scenario_id: str,
) -> dict:
    """
    Wrapper UI pour create_finrep_from_run.
    
    Returns:
        Dict avec finrep_f09, finrep_f18
    """
    from src.services.reporting_service import create_finrep_from_run
    
    return create_finrep_from_run(run_id, scenario_id)

