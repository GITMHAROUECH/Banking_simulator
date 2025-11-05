"""
Service d'orchestration Pipeline E2E (I7a).

Ce service coordonne l'exécution complète du pipeline :
Simulation → RWA → Liquidité → Capital → Export Excel.
"""

from typing import Any

from src.services.reporting_service import create_excel_export
from src.services.risk_service import compute_capital, compute_liquidity, compute_rwa
from src.services.simulation_service import run_simulation


def run_full_pipeline(
    num_positions: int,
    seed: int,
    own_funds: dict[str, float],
    config: dict[str, object] | None = None,
    use_cache: bool = True,
) -> dict[str, Any]:
    """
    Exécute le pipeline complet E2E.

    Args:
        num_positions: Nombre de positions à générer
        seed: Graine aléatoire pour reproductibilité
        own_funds: Fonds propres (cet1, tier1, total, leverage_exposure)
        config: Configuration optionnelle
        use_cache: Si True, utilise le cache params_hash (défaut: True)

    Returns:
        Dict avec clés:
            - positions_df: DataFrame des positions
            - rwa_df: DataFrame des RWA
            - lcr_df: DataFrame LCR
            - nsfr_df: DataFrame NSFR
            - almm_obj: Objet ALMM
            - capital_ratios: Dict des ratios de capital
            - excel_bytes: Bytes du fichier Excel
            - cache_hits: Dict des cache hits par étape

    Raises:
        ValueError: Si paramètres invalides
    """
    # Validation des paramètres
    if num_positions <= 0:
        raise ValueError(f"num_positions doit être > 0, reçu: {num_positions}")
    if seed < 0:
        raise ValueError(f"seed doit être >= 0, reçu: {seed}")

    required_keys = ["cet1", "tier1", "total", "leverage_exposure"]
    missing_keys = [k for k in required_keys if k not in own_funds]
    if missing_keys:
        raise ValueError(f"Clés manquantes dans own_funds: {missing_keys}")

    # Initialiser le tracker de cache hits
    cache_hits: dict[str, bool] = {}

    # Étape 1 : Simulation Monte Carlo
    positions_df, cache_hit_sim = run_simulation(
        num_positions=num_positions, seed=seed, config=config, use_cache=use_cache
    )
    cache_hits["simulation"] = cache_hit_sim

    # Étape 2 : Calcul RWA
    rwa_df, cache_hit_rwa = compute_rwa(positions_df, use_cache=use_cache)
    cache_hits["rwa"] = cache_hit_rwa

    # Étape 3 : Calcul Liquidité (LCR, NSFR, ALMM)
    lcr_df, nsfr_df, almm_obj, cache_hit_liq = compute_liquidity(
        positions_df, use_cache=use_cache
    )
    cache_hits["liquidity"] = cache_hit_liq

    # Étape 4 : Calcul Capital
    capital_ratios, cache_hit_cap = compute_capital(
        rwa_df, own_funds, use_cache=use_cache
    )
    cache_hits["capital"] = cache_hit_cap

    # Étape 5 : Export Excel
    excel_bytes, cache_hit_exp = create_excel_export(
        positions_df=positions_df,
        rwa_df=rwa_df,
        lcr_df=lcr_df,
        nsfr_df=nsfr_df,
        capital_ratios=capital_ratios,
        use_cache=use_cache,
    )
    cache_hits["export"] = cache_hit_exp

    # Retourner tous les résultats
    return {
        "positions_df": positions_df,
        "rwa_df": rwa_df,
        "lcr_df": lcr_df,
        "nsfr_df": nsfr_df,
        "almm_obj": almm_obj,
        "capital_ratios": capital_ratios,
        "excel_bytes": excel_bytes,
        "cache_hits": cache_hits,
    }




def create_pipeline_export(
    num_positions: int,
    seed: int,
    own_funds: dict[str, float],
    config: dict[str, object] | None = None,
    *,
    format: str = "xlsx",
    compress: bool = False,
    include_corep_stubs: bool = True,
    use_cache: bool = True,
) -> bytes:
    """
    Exécute le pipeline complet et génère un export multi-formats (I8).

    Args:
        num_positions: Nombre de positions à générer
        seed: Graine aléatoire pour reproductibilité
        own_funds: Fonds propres (cet1, tier1, total, leverage_exposure)
        config: Configuration optionnelle
        format: Format d'export ("xlsx", "parquet", "csv", "json")
        compress: Si True, compresse le résultat
        include_corep_stubs: Si True, inclut les stubs COREP/LE/LCR
        use_cache: Si True, utilise le cache params_hash (défaut: True)

    Returns:
        bytes: Contenu du fichier exporté

    Raises:
        ValueError: Si paramètres invalides
    """
    from src.services.reporting_service import create_export

    # Exécuter le pipeline complet
    results = run_full_pipeline(
        num_positions=num_positions,
        seed=seed,
        own_funds=own_funds,
        config=config,
        use_cache=use_cache,
    )

    # Préparer les outputs pour create_export
    outputs = {
        "positions": results["positions_df"],
        "rwa": results["rwa_df"],
        "liquidity": {
            "lcr": results["lcr_df"],
            "nsfr": results["nsfr_df"],
        },
        "ratios": results["capital_ratios"],
        "metadata": {
            "num_positions": num_positions,
            "seed": seed,
            "own_funds": own_funds,
            "cache_hits": results["cache_hits"],
            "version": "0.8.0",
        },
    }

    # Générer l'export
    return create_export(
        outputs,
        format=format,  # type: ignore
        compress=compress,
        include_corep_stubs=include_corep_stubs,
    )

