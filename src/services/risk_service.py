"""
Service d'orchestration pour les calculs de risque.

Ce service coordonne les calculs de RWA, liquidité (LCR/NSFR/ALMM)
et ratios de capital.
"""

from typing import Any

import pandas as pd

from src.domain.risk import calculate_liquidity_advanced as domain_calculate_liquidity
from src.domain.risk import calculate_rwa_advanced as domain_calculate_rwa
from src.domain.risk import compute_capital_ratios as domain_compute_capital
from src.services.persistence_service import (
    compute_params_hash,
    load_dataframe,
    load_dict,
    save_dataframe,
    save_dict,
)


def compute_rwa(
    positions_df: pd.DataFrame,
    use_cache: bool = True
) -> tuple[pd.DataFrame, bool]:
    """
    Calcule les RWA (Risk-Weighted Assets) pour un portefeuille de positions.

    Args:
        positions_df: DataFrame avec colonnes minimales:
            - position_id, exposure_class, ead, pd, lgd, maturity
        use_cache: Si True, utilise le cache params_hash (défaut: True)

    Returns:
        Tuple (DataFrame, cache_hit):
            - DataFrame avec colonnes minimales:
                position_id, rwa_amount, rwa_density, approach
            - cache_hit: True si chargé depuis le cache, False si calculé

    Raises:
        ValueError: Si positions_df est vide ou manque des colonnes requises
    """
    # Validation
    if positions_df.empty:
        raise ValueError("positions_df ne peut pas être vide")

    required_cols = ['position_id', 'exposure_class', 'ead']
    missing_cols = [col for col in required_cols if col not in positions_df.columns]
    if missing_cols:
        raise ValueError(f"Colonnes manquantes dans positions_df: {missing_cols}")

    # Calculer le hash des paramètres pour le cache (I6)
    # On hash les position_ids pour identifier le portefeuille
    params = {
        "position_ids": sorted(positions_df['position_id'].tolist()),
        "num_positions": len(positions_df),
    }
    params_hash = compute_params_hash(params)

    # Tenter de charger depuis le cache (I6)
    if use_cache:
        cached_df = load_dataframe("rwa", params_hash)
        if cached_df is not None:
            return (cached_df, True)  # Cache hit

    # Calcul RWA via le domain
    rwa_df = domain_calculate_rwa(positions_df)

    # Sauvegarder dans le cache (I6)
    if use_cache:
        save_dataframe("rwa", params_hash, rwa_df)

    return (rwa_df, False)  # Cache miss


def compute_liquidity(
    positions_df: pd.DataFrame,
    use_cache: bool = True
) -> tuple[pd.DataFrame, pd.DataFrame, Any, bool]:
    """
    Calcule les métriques de liquidité (LCR, NSFR, ALMM).

    Args:
        positions_df: DataFrame avec colonnes minimales:
            - position_id, entity_id, product_id, maturity, currency
        use_cache: Si True, utilise le cache params_hash (défaut: True)

    Returns:
        Tuple de 4 éléments:
            - lcr_df: DataFrame avec métriques LCR par entité
            - nsfr_df: DataFrame avec métriques NSFR par entité
            - almm_obj: Objet ALMM (dict ou DataFrame)
            - cache_hit: True si chargé depuis le cache, False si calculé

    Raises:
        ValueError: Si positions_df est vide ou manque des colonnes requises
    """
    # Validation
    if positions_df.empty:
        raise ValueError("positions_df ne peut pas être vide")

    required_cols = ['position_id', 'entity_id', 'maturity']
    missing_cols = [col for col in required_cols if col not in positions_df.columns]
    if missing_cols:
        raise ValueError(f"Colonnes manquantes dans positions_df: {missing_cols}")

    # Calculer le hash des paramètres pour le cache (I6)
    params = {
        "position_ids": sorted(positions_df['position_id'].tolist()),
        "num_positions": len(positions_df),
    }
    params_hash = compute_params_hash(params)

    # Tenter de charger depuis le cache (I6)
    if use_cache:
        cached_lcr = load_dataframe("lcr", params_hash)
        cached_nsfr = load_dataframe("nsfr", params_hash)
        cached_almm = load_dict("almm", params_hash)

        if cached_lcr is not None and cached_nsfr is not None and cached_almm is not None:
            return (cached_lcr, cached_nsfr, cached_almm, True)  # Cache hit

    # Calcul liquidité via le domain
    lcr_df, nsfr_df, almm_obj = domain_calculate_liquidity(positions_df)

    # Sauvegarder dans le cache (I6)
    if use_cache:
        save_dataframe("lcr", params_hash, lcr_df)
        save_dataframe("nsfr", params_hash, nsfr_df)
        # Convertir almm_obj en dict si nécessaire
        if isinstance(almm_obj, pd.DataFrame):
            almm_dict = almm_obj.to_dict(orient='records')
        else:
            almm_dict = almm_obj
        save_dict("almm", params_hash, almm_dict)

    return (lcr_df, nsfr_df, almm_obj, False)  # Cache miss


def compute_capital(
    rwa_df: pd.DataFrame,
    own_funds: dict[str, float] | pd.DataFrame,
    use_cache: bool = True
) -> tuple[dict[str, float], bool]:
    """
    Calcule les ratios de capital (CET1, Tier 1, Total, Leverage).

    Args:
        rwa_df: DataFrame avec colonnes minimales:
            - rwa_amount
        own_funds: Fonds propres, soit:
            - dict avec clés: cet1, tier1, total, leverage_exposure
            - DataFrame avec colonnes: entity_id, cet1, tier1, total
        use_cache: Si True, utilise le cache params_hash (défaut: True)

    Returns:
        Tuple (dict, cache_hit):
            - Dict avec clés:
                cet1_ratio, tier1_ratio, total_capital_ratio, leverage_ratio
            - cache_hit: True si chargé depuis le cache, False si calculé

    Raises:
        ValueError: Si rwa_df est vide ou own_funds invalide
    """
    # Validation
    if rwa_df.empty:
        raise ValueError("rwa_df ne peut pas être vide")

    if 'rwa_amount' not in rwa_df.columns:
        raise ValueError("Colonne 'rwa_amount' manquante dans rwa_df")

    # Validation own_funds
    if isinstance(own_funds, dict):
        required_keys = ['cet1', 'tier1', 'total', 'leverage_exposure']
        missing_keys = [k for k in required_keys if k not in own_funds]
        if missing_keys:
            raise ValueError(f"Clés manquantes dans own_funds: {missing_keys}")
    elif isinstance(own_funds, pd.DataFrame):
        if own_funds.empty:
            raise ValueError("own_funds DataFrame ne peut pas être vide")
        required_cols = ['cet1', 'tier1', 'total']
        missing_cols = [col for col in required_cols if col not in own_funds.columns]
        if missing_cols:
            raise ValueError(f"Colonnes manquantes dans own_funds: {missing_cols}")
    else:
        raise ValueError("own_funds doit être un dict ou un DataFrame")

    # Calculer le hash des paramètres pour le cache (I6)
    params: dict[str, object] = {
        "total_rwa": float(rwa_df['rwa_amount'].sum()),
        "own_funds": own_funds if isinstance(own_funds, dict) else own_funds.to_dict(orient='records'),
    }
    params_hash = compute_params_hash(params)

    # Tenter de charger depuis le cache (I6)
    if use_cache:
        cached_ratios = load_dict("ratios", params_hash)
        if cached_ratios is not None:
            # Cast pour mypy (assume que les valeurs sont des floats)
            typed_ratios: dict[str, float] = dict(cached_ratios.items())  # type: ignore[misc]
            return (typed_ratios, True)  # Cache hit

    # Calcul capital via le domain
    capital_ratios = domain_compute_capital(rwa_df, own_funds)

    # Sauvegarder dans le cache (I6)
    if use_cache:
        ratios_dict: dict[str, object] = dict(capital_ratios.items())
        save_dict("ratios", params_hash, ratios_dict)

    return (capital_ratios, False)  # Cache miss




# ============================================================================
# SA-CCR (Standardized Approach for Counterparty Credit Risk) - I7b
# ============================================================================

from src.domain.risk.counterparty import compute_saccr_ead_detailed


def compute_saccr_ead(
    trades_df: pd.DataFrame,
    collateral_df: pd.DataFrame | None = None,
    params: dict[str, Any] | None = None,
    use_cache: bool = True,
) -> tuple[pd.DataFrame, bool]:
    """
    Calcule l'EAD selon SA-CCR pour un portefeuille de dérivés.

    Args:
        trades_df: DataFrame des trades avec colonnes:
            - trade_id: Identifiant du trade
            - netting_set: Identifiant du netting set
            - asset_class: Classe d'actifs ("IR", "FX", "Equity", "Commodity", "Credit")
            - notional: Notionnel
            - maturity_bucket: Bucket de maturité (pour IR: "0-1Y", "1-5Y", ">5Y")
            - rating: Rating (pour Credit: "IG" ou "HY")
            - mtm: Mark-to-Market
        collateral_df: DataFrame du collatéral (optionnel) avec colonnes:
            - netting_set: Identifiant du netting set
            - collateral_amount: Montant du collatéral
        params: Paramètres optionnels (alpha, supervisory factors override)
        use_cache: Si True, utilise le cache params_hash (défaut: True)

    Returns:
        Tuple (DataFrame, cache_hit):
            - DataFrame avec une ligne par trade et colonnes:
                trade_id, netting_set, asset_class, ead_contribution
            - cache_hit: True si chargé depuis le cache, False si calculé

    Raises:
        ValueError: Si trades_df est vide ou manque des colonnes requises
    """
    # Validation
    if trades_df.empty:
        raise ValueError("trades_df ne peut pas être vide")

    required_cols = ["trade_id", "netting_set", "asset_class", "notional", "mtm"]
    missing_cols = [col for col in required_cols if col not in trades_df.columns]
    if missing_cols:
        raise ValueError(f"Colonnes manquantes dans trades_df: {missing_cols}")

    # Calculer le hash des paramètres pour le cache (I6)
    params_dict: dict[str, object] = {
        "trade_ids": trades_df["trade_id"].tolist(),
        "params": params if params else {},
        "collateral": collateral_df.to_dict(orient="records")
        if collateral_df is not None
        else None,
    }
    params_hash = compute_params_hash(params_dict)

    # Tenter de charger depuis le cache (I6)
    if use_cache:
        cached_df = load_dataframe("saccr_ead", params_hash)
        if cached_df is not None:
            return (cached_df, True)  # Cache hit

    # Calcul SA-CCR via le domain
    result = compute_saccr_ead_detailed(trades_df, collateral_df, params)

    # Créer un DataFrame de résultats par trade
    # Simplification: EAD total réparti proportionnellement au notionnel
    total_notional = trades_df["notional"].sum()
    trades_df_result = trades_df[["trade_id", "netting_set", "asset_class", "notional"]].copy()
    trades_df_result["ead_contribution"] = (
        trades_df_result["notional"] / total_notional * result["ead"]
    )

    # Sauvegarder dans le cache (I6)
    if use_cache:
        save_dataframe("saccr_ead", params_hash, trades_df_result)

    return (trades_df_result, False)  # Cache miss


def compute_saccr_rwa(
    trades_df: pd.DataFrame,
    collateral_df: pd.DataFrame | None = None,
    params: dict[str, Any] | None = None,
    use_cache: bool = True,
) -> tuple[dict[str, Any], bool]:
    """
    Calcule les RWA selon SA-CCR pour un portefeuille de dérivés.

    Args:
        trades_df: DataFrame des trades (voir compute_saccr_ead)
        collateral_df: DataFrame du collatéral (optionnel)
        params: Paramètres optionnels
        use_cache: Si True, utilise le cache params_hash (défaut: True)

    Returns:
        Tuple (dict, cache_hit):
            - Dict avec clés:
                - ead: EAD total
                - rwa: RWA total (EAD × 100% pour contrepartie)
                - rc: Replacement Cost
                - pfe: Potential Future Exposure
                - pfe_addons: Dict des add-ons par classe
                - multiplier: Multiplier
                - alpha: Alpha utilisé
                - k: Facteur de pondération (100% pour contrepartie)
            - cache_hit: True si chargé depuis le cache, False si calculé

    Raises:
        ValueError: Si trades_df est vide ou manque des colonnes requises
    """
    # Validation
    if trades_df.empty:
        raise ValueError("trades_df ne peut pas être vide")

    # Calculer le hash des paramètres pour le cache (I6)
    params_dict: dict[str, object] = {
        "trade_ids": trades_df["trade_id"].tolist(),
        "params": params if params else {},
        "collateral": collateral_df.to_dict(orient="records")
        if collateral_df is not None
        else None,
    }
    params_hash = compute_params_hash(params_dict)

    # Tenter de charger depuis le cache (I6)
    if use_cache:
        cached_dict = load_dict("saccr_rwa", params_hash)
        if cached_dict is not None:
            # Cast pour mypy
            typed_dict: dict[str, Any] = {k: v for k, v in cached_dict.items()}  # type: ignore[misc]
            return (typed_dict, True)  # Cache hit

    # Calcul SA-CCR via le domain
    result = compute_saccr_ead_detailed(trades_df, collateral_df, params)

    # RWA = EAD × 100% (pondération standard pour contrepartie)
    k = 1.0  # 100%
    rwa = result["ead"] * k

    # Ajouter RWA et k au résultat
    result["rwa"] = rwa
    result["k"] = k

    # Sauvegarder dans le cache (I6)
    if use_cache:
        result_dict: dict[str, object] = {k: v for k, v in result.items()}
        save_dict("saccr_rwa", params_hash, result_dict)

    return (result, False)  # Cache miss




# ============================================================================
# CVA (Credit Valuation Adjustment) - I7c
# ============================================================================

from src.domain.risk.counterparty import compute_cva_capital_ba, compute_cva_pricing_v1


def compute_cva_capital(
    ead_df: pd.DataFrame, params: dict[str, Any] | None = None, use_cache: bool = True
) -> tuple[dict[str, Any], bool]:
    """
    Calcule le capital CVA selon l'approche BA-CVA.

    Args:
        ead_df: DataFrame avec colonnes:
            - counterparty: Identifiant de la contrepartie
            - ead: Exposure At Default
            - maturity: Maturité effective (optionnel)
            - weight: Poids (optionnel)
        params: Paramètres optionnels (default_maturity, default_weight)
        use_cache: Si True, utilise le cache params_hash (défaut: True)

    Returns:
        Tuple (dict, cache_hit):
            - Dict avec clés:
                - k_cva: Capital CVA total
                - by_counterparty: DataFrame avec détails par contrepartie
            - cache_hit: True si chargé depuis le cache, False si calculé
    """
    # Validation
    if ead_df.empty:
        raise ValueError("ead_df ne peut pas être vide")

    required_cols = ["counterparty", "ead"]
    missing_cols = [col for col in required_cols if col not in ead_df.columns]
    if missing_cols:
        raise ValueError(f"Colonnes manquantes dans ead_df: {missing_cols}")

    # Calculer le hash des paramètres pour le cache (I6)
    params_dict: dict[str, object] = {
        "counterparties": ead_df["counterparty"].tolist(),
        "eads": ead_df["ead"].tolist(),
        "params": params if params else {},
    }
    params_hash = compute_params_hash(params_dict)

    # Tenter de charger depuis le cache (I6)
    if use_cache:
        cached_dict = load_dict("cva_capital", params_hash)
        if cached_dict is not None:
            # Reconstruire le DataFrame by_counterparty
            result = {
                "k_cva": cached_dict["k_cva"],
                "by_counterparty": pd.DataFrame(cached_dict["by_counterparty"]),  # type: ignore[arg-type]
            }
            return (result, True)  # Cache hit

    # Calcul BA-CVA via le domain
    result = compute_cva_capital_ba(ead_df, params)

    # Sauvegarder dans le cache (I6)
    if use_cache:
        cache_dict: dict[str, object] = {
            "k_cva": result["k_cva"],
            "by_counterparty": result["by_counterparty"].to_dict(orient="records"),
        }
        save_dict("cva_capital", params_hash, cache_dict)

    return (result, False)  # Cache miss


def compute_cva_pricing(
    trades_df: pd.DataFrame, params: dict[str, Any] | None = None, use_cache: bool = True
) -> tuple[dict[str, Any], bool]:
    """
    Calcule le CVA pricing selon une approche simplifiée v1.

    Args:
        trades_df: DataFrame avec colonnes:
            - counterparty: Identifiant de la contrepartie
            - ead: Exposure At Default (proxy pour EE)
            - spread: Spread de crédit (en bps, optionnel)
            - maturity: Maturité (en années, optionnel)
        params: Paramètres optionnels (recovery_rate, risk_free_rate, etc.)
        use_cache: Si True, utilise le cache params_hash (défaut: True)

    Returns:
        Tuple (dict, cache_hit):
            - Dict avec clés:
                - cva: CVA total
                - by_bucket: DataFrame avec détails par bucket de temps
            - cache_hit: True si chargé depuis le cache, False si calculé
    """
    # Validation
    if trades_df.empty:
        raise ValueError("trades_df ne peut pas être vide")

    required_cols = ["counterparty", "ead"]
    missing_cols = [col for col in required_cols if col not in trades_df.columns]
    if missing_cols:
        raise ValueError(f"Colonnes manquantes dans trades_df: {missing_cols}")

    # Calculer le hash des paramètres pour le cache (I6)
    params_dict: dict[str, object] = {
        "counterparties": trades_df["counterparty"].tolist(),
        "eads": trades_df["ead"].tolist(),
        "params": params if params else {},
    }
    params_hash = compute_params_hash(params_dict)

    # Tenter de charger depuis le cache (I6)
    if use_cache:
        cached_dict = load_dict("cva_pricing", params_hash)
        if cached_dict is not None:
            # Reconstruire le DataFrame by_bucket
            result = {
                "cva": cached_dict["cva"],
                "by_bucket": pd.DataFrame(cached_dict["by_bucket"]),  # type: ignore[arg-type]
            }
            return (result, True)  # Cache hit

    # Calcul CVA pricing via le domain
    result = compute_cva_pricing_v1(trades_df, params)

    # Sauvegarder dans le cache (I6)
    if use_cache:
        cache_dict: dict[str, object] = {
            "cva": result["cva"],
            "by_bucket": result["by_bucket"].to_dict(orient="records"),
        }
        save_dict("cva_pricing", params_hash, cache_dict)

    return (result, False)  # Cache miss


def compute_counterparty_risk(
    trades_df: pd.DataFrame,
    collateral_df: pd.DataFrame | None = None,
    params: dict[str, Any] | None = None,
    use_cache: bool = True,
) -> tuple[dict[str, Any], bool]:
    """
    Agrégateur de risque de contrepartie : SA-CCR + CVA (capital + pricing v1).

    Args:
        trades_df: DataFrame des trades (voir compute_saccr_ead)
        collateral_df: DataFrame du collatéral (optionnel)
        params: Paramètres optionnels:
            - alpha: Alpha pour SA-CCR (défaut: 1.4)
            - enable_cva_pricing: Activer CVA pricing (défaut: False)
            - cva_params: Paramètres CVA (recovery_rate, risk_free_rate, etc.)
        use_cache: Si True, utilise le cache params_hash (défaut: True)

    Returns:
        Tuple (dict, cache_hit):
            - Dict avec clés:
                - saccr: Dict SA-CCR (ead_df, rc, pfe, pfe_addons, multiplier, alpha, rwa, k)
                - cva_capital: Dict CVA capital (k_cva, by_counterparty)
                - cva_pricing: Dict CVA pricing (cva, by_bucket) ou None si désactivé
                - cache_hit: bool (True si tout chargé depuis cache)
            - cache_hit: True si chargé depuis le cache, False si calculé
    """
    # Validation
    if trades_df.empty:
        raise ValueError("trades_df ne peut pas être vide")

    # Calculer le hash des paramètres pour le cache (I6)
    params_dict: dict[str, object] = {
        "trade_ids": trades_df["trade_id"].tolist(),
        "params": params if params else {},
        "collateral": collateral_df.to_dict(orient="records")
        if collateral_df is not None
        else None,
    }
    params_hash = compute_params_hash(params_dict)

    # Tenter de charger depuis le cache (I6)
    if use_cache:
        cached_dict = load_dict("counterparty_risk", params_hash)
        if cached_dict is not None:
            # Reconstruire les DataFrames
            result = {
                "saccr": {
                    "ead_df": pd.DataFrame(cached_dict["saccr"]["ead_df"]),  # type: ignore[index]
                    "rc": cached_dict["saccr"]["rc"],  # type: ignore[index]
                    "pfe": cached_dict["saccr"]["pfe"],  # type: ignore[index]
                    "pfe_addons": cached_dict["saccr"]["pfe_addons"],  # type: ignore[index]
                    "multiplier": cached_dict["saccr"]["multiplier"],  # type: ignore[index]
                    "alpha": cached_dict["saccr"]["alpha"],  # type: ignore[index]
                    "rwa": cached_dict["saccr"]["rwa"],  # type: ignore[index]
                    "k": cached_dict["saccr"]["k"],  # type: ignore[index]
                },
                "cva_capital": {
                    "k_cva": cached_dict["cva_capital"]["k_cva"],  # type: ignore[index]
                    "by_counterparty": pd.DataFrame(
                        cached_dict["cva_capital"]["by_counterparty"]  # type: ignore[index]
                    ),
                },
                "cva_pricing": (
                    {
                        "cva": cached_dict["cva_pricing"]["cva"],  # type: ignore[index]
                        "by_bucket": pd.DataFrame(cached_dict["cva_pricing"]["by_bucket"]),  # type: ignore[index]
                    }
                    if cached_dict.get("cva_pricing") is not None
                    else None
                ),
            }
            return (result, True)  # Cache hit

    # Paramètres
    enable_cva_pricing = params.get("enable_cva_pricing", False) if params else False
    cva_params = params.get("cva_params", {}) if params else {}

    # 1. Calcul SA-CCR (EAD + RWA)
    ead_df, _ = compute_saccr_ead(trades_df, collateral_df, params, use_cache=False)
    rwa_result, _ = compute_saccr_rwa(trades_df, collateral_df, params, use_cache=False)

    # 2. Préparer le DataFrame pour CVA capital
    # Grouper par contrepartie (netting_set comme proxy)
    ead_by_counterparty = (
        ead_df.groupby("netting_set")
        .agg({"ead_contribution": "sum"})
        .reset_index()
        .rename(columns={"netting_set": "counterparty", "ead_contribution": "ead"})
    )

    # 3. Calcul CVA capital
    cva_capital_result, _ = compute_cva_capital(
        ead_by_counterparty, cva_params, use_cache=False
    )

    # 4. Calcul CVA pricing (si activé)
    cva_pricing_result = None
    if enable_cva_pricing:
        # Préparer le DataFrame pour CVA pricing
        trades_for_pricing = ead_by_counterparty.copy()
        cva_pricing_result, _ = compute_cva_pricing(
            trades_for_pricing, cva_params, use_cache=False
        )

    # 5. Agréger les résultats
    result = {
        "saccr": {
            "ead_df": ead_df,
            "rc": rwa_result["rc"],
            "pfe": rwa_result["pfe"],
            "pfe_addons": rwa_result["pfe_addons"],
            "multiplier": rwa_result["multiplier"],
            "alpha": rwa_result["alpha"],
            "rwa": rwa_result["rwa"],
            "k": rwa_result["k"],
        },
        "cva_capital": cva_capital_result,
        "cva_pricing": cva_pricing_result,
    }

    # Sauvegarder dans le cache (I6)
    if use_cache:
        cache_dict: dict[str, object] = {
            "saccr": {
                "ead_df": result["saccr"]["ead_df"].to_dict(orient="records"),
                "rc": result["saccr"]["rc"],
                "pfe": result["saccr"]["pfe"],
                "pfe_addons": result["saccr"]["pfe_addons"],
                "multiplier": result["saccr"]["multiplier"],
                "alpha": result["saccr"]["alpha"],
                "rwa": result["saccr"]["rwa"],
                "k": result["saccr"]["k"],
            },
            "cva_capital": {
                "k_cva": result["cva_capital"]["k_cva"],
                "by_counterparty": result["cva_capital"]["by_counterparty"].to_dict(
                    orient="records"
                ),
            },
            "cva_pricing": (
                {
                    "cva": result["cva_pricing"]["cva"],
                    "by_bucket": result["cva_pricing"]["by_bucket"].to_dict(
                        orient="records"
                    ),
                }
                if result["cva_pricing"] is not None
                else None
            ),
        }
        save_dict("counterparty_risk", params_hash, cache_dict)

    return (result, False)  # Cache miss




# ============================================================================
# I11: Fonctions run_id pour consommer exposures
# ============================================================================

def compute_rwa_from_run(
    run_id: str,
    params: dict | None = None,
    use_cache: bool = True,
) -> tuple[dict, bool]:
    """
    Calcule RWA à partir d'un run_id (I11).
    
    Args:
        run_id: Identifiant du run
        params: Paramètres additionnels (filtres, etc.)
        use_cache: Si True, utilise le cache
    
    Returns:
        (dict résultats RWA, cache_hit)
    """
    from src.services.exposure_service import load_exposures
    
    # Charger les exposures
    df_exp = load_exposures(run_id)
    
    # Filtrer les actifs à risque (exclure deposits)
    df_risk = df_exp[~df_exp['product_type'].isin(['Deposit'])].copy()
    
    # Transformer en format positions_df pour compute_rwa
    # Mapper les colonnes du schéma exposures vers le format legacy
    positions_df = df_risk.rename(columns={
        'id': 'position_id',
        'maturity_years': 'maturity',  # maturity_years → maturity
        'entity': 'entity_id',         # entity → entity_id
    })
    
    # Calculer RWA
    df_rwa, cache_hit = compute_rwa(positions_df, use_cache=use_cache)
    
    # Agréger les résultats
    result = {
        'run_id': run_id,
        'total_ead': float(df_risk['ead'].sum()),
        'total_rwa': float(df_rwa['rwa_amount'].sum()),
        'rwa_density': float(df_rwa['rwa_amount'].sum() / df_risk['ead'].sum()) if df_risk['ead'].sum() > 0 else 0,
        'by_exposure_class': df_rwa.groupby('exposure_class')['rwa_amount'].sum().to_dict(),
        'by_product_type': df_risk.merge(df_rwa, left_on='id', right_on='position_id').groupby('product_type')['rwa_amount'].sum().to_dict(),
    }
    
    return (result, cache_hit)


def compute_saccr_from_run(
    run_id: str,
    params: dict | None = None,
    use_cache: bool = True,
) -> tuple[dict, bool]:
    """
    Calcule SA-CCR à partir d'un run_id (I11).
    
    Args:
        run_id: Identifiant du run
        params: Paramètres additionnels
        use_cache: Si True, utilise le cache
    
    Returns:
        (dict résultats SA-CCR, cache_hit)
    """
    from src.services.exposure_service import load_exposures
    
    # Charger les exposures
    df_exp = load_exposures(run_id)
    
    # Filtrer les dérivés
    df_deriv = df_exp[df_exp['product_type'] == 'Derivative'].copy()
    
    if len(df_deriv) == 0:
        return ({'run_id': run_id, 'total_ead': 0, 'rc': 0, 'pfe': 0}, False)
    
    # Transformer en format trades_df pour compute_saccr_ead
    # Mapper les colonnes du schéma exposures vers le format SA-CCR
    trades_df = df_deriv.rename(columns={
        'id': 'trade_id',
        'netting_set_id': 'netting_set',  # netting_set_id → netting_set
    })
    
    # Ajouter asset_class si manquante (dérivé de product_type)
    if 'asset_class' not in trades_df.columns:
        trades_df['asset_class'] = 'IR'  # Interest Rate par défaut
    
    # Ajouter maturity_bucket si manquante (calculé depuis maturity_years)
    if 'maturity_bucket' not in trades_df.columns and 'maturity_years' in trades_df.columns:
        import pandas as pd
        trades_df['maturity_bucket'] = pd.cut(
            trades_df['maturity_years'],
            bins=[0, 1, 5, float('inf')],
            labels=['<1Y', '1-5Y', '>5Y']
        )
    
    # Calculer SA-CCR EAD
    result_dict, cache_hit = compute_saccr_ead(trades_df, collateral_df=None, params=params, use_cache=use_cache)
    
    # Ajouter run_id
    result_dict['run_id'] = run_id
    
    return (result_dict, cache_hit)


def compute_lcr_from_run(
    run_id: str,
    params: dict | None = None,
    use_cache: bool = True,
) -> tuple[dict, bool]:
    """
    Calcule LCR à partir d'un run_id (I11).
    
    Args:
        run_id: Identifiant du run
        params: Paramètres additionnels
        use_cache: Si True, utilise le cache
    
    Returns:
        (dict résultats LCR, cache_hit)
    """
    from src.services.exposure_service import load_exposures
    
    # Charger les exposures
    df_exp = load_exposures(run_id)
    
    # Identifier HQLA (bonds sovereign/corporate de haute qualité)
    df_hqla = df_exp[
        (df_exp['product_type'] == 'Bond') &
        (df_exp['exposure_class'].isin(['Sovereign', 'Corporate']))
    ].copy()
    
    # Identifier cash outflows (deposits à court terme)
    df_outflows = df_exp[
        (df_exp['product_type'] == 'Deposit') &
        (df_exp['maturity_years'] <= 0.25)  # < 3 mois
    ].copy()
    
    # Calculer LCR simplifié
    hqla = float(df_hqla['notional'].sum())
    net_cash_outflows = float(df_outflows['notional'].sum()) * 0.25  # Assume 25% outflow rate
    
    lcr_ratio = (hqla / net_cash_outflows * 100) if net_cash_outflows > 0 else 0
    
    result = {
        'run_id': run_id,
        'hqla': hqla,
        'net_cash_outflows': net_cash_outflows,
        'lcr_ratio': lcr_ratio,
        'compliant': lcr_ratio >= 100,
    }
    
    return (result, False)  # Pas de cache pour LCR simplifié


def compute_capital_ratios_from_run(
    run_id: str,
    params: dict | None = None,
    use_cache: bool = True,
) -> tuple[dict, bool]:
    """
    Calcule les ratios de capital à partir d'un run_id (I11).
    
    Args:
        run_id: Identifiant du run
        params: Paramètres contenant:
            - cet1_capital: Capital CET1
            - tier1_capital: Capital Tier 1
            - total_capital: Capital total
        use_cache: Si True, utilise le cache
    
    Returns:
        (dict ratios de capital, cache_hit)
    """
    # Calculer RWA d'abord
    rwa_result, _ = compute_rwa_from_run(run_id, params, use_cache)
    
    # Paramètres de capital (à fournir ou utiliser defaults)
    if params is None:
        params = {}
    
    cet1_capital = params.get('cet1_capital', 1200)  # Default: 1.2B
    tier1_capital = params.get('tier1_capital', 1500)  # Default: 1.5B
    total_capital = params.get('total_capital', 2000)  # Default: 2B
    
    total_rwa = rwa_result['total_rwa']
    
    # Calculer ratios
    cet1_ratio = (cet1_capital / total_rwa * 100) if total_rwa > 0 else 0
    tier1_ratio = (tier1_capital / total_rwa * 100) if total_rwa > 0 else 0
    total_ratio = (total_capital / total_rwa * 100) if total_rwa > 0 else 0
    
    # Leverage ratio (Tier1 / Total Exposure)
    from src.services.exposure_service import load_exposures
    df_exp = load_exposures(run_id)
    total_exposure = float(df_exp['ead'].sum())
    leverage_ratio = (tier1_capital / total_exposure * 100) if total_exposure > 0 else 0
    
    result = {
        'run_id': run_id,
        'cet1_capital': cet1_capital,
        'tier1_capital': tier1_capital,
        'total_capital': total_capital,
        'total_rwa': total_rwa,
        'total_exposure': total_exposure,
        'cet1_ratio': cet1_ratio,
        'tier1_ratio': tier1_ratio,
        'total_ratio': total_ratio,
        'leverage_ratio': leverage_ratio,
        'cet1_compliant': cet1_ratio >= 4.5,
        'tier1_compliant': tier1_ratio >= 6.0,
        'total_compliant': total_ratio >= 8.0,
        'leverage_compliant': leverage_ratio >= 3.0,
    }
    
    return (result, False)  # Pas de cache pour ratios (dépend de capital externe)

