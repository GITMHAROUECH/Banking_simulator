"""
Module de calcul SA-CCR (Standardized Approach for Counterparty Credit Risk).

Implémente le calcul de l'EAD (Exposure At Default) pour les dérivés
selon la méthode SA-CCR (CRR3, Article 274).

Références:
- CRR3 Article 274 (SA-CCR)
- Basel III: SA-CCR framework
"""

from typing import Any

import numpy as np
import pandas as pd


# Supervisory factors par classe d'actifs (CRR3 Annexe IV)
SUPERVISORY_FACTORS = {
    "IR": {  # Interest Rate
        "0-1Y": 0.0005,
        "1-5Y": 0.0005,
        ">5Y": 0.0015,
    },
    "FX": 0.04,  # Foreign Exchange
    "Equity": 0.32,  # Actions
    "Commodity": 0.18,  # Matières premières
    "Credit": {  # Crédit
        "IG": 0.0038,  # Investment Grade
        "HY": 0.054,  # High Yield
    },
}

# Alpha (facteur multiplicateur)
ALPHA = 1.4


def compute_replacement_cost(
    trades_df: pd.DataFrame, collateral_df: pd.DataFrame | None = None
) -> float:
    """
    Calcule le Replacement Cost (RC).

    RC = max(V - C, 0)
    où V = somme des MTM positifs par netting set
        C = collateral reçu

    Args:
        trades_df: DataFrame des trades avec colonnes:
            - netting_set: Identifiant du netting set
            - mtm: Mark-to-Market (positif = créance, négatif = dette)
        collateral_df: DataFrame du collatéral (optionnel) avec colonnes:
            - netting_set: Identifiant du netting set
            - collateral_amount: Montant du collatéral

    Returns:
        Replacement Cost (RC)
    """
    # Grouper par netting set et sommer les MTM
    mtm_by_ns = trades_df.groupby("netting_set")["mtm"].sum()

    # Prendre uniquement les MTM positifs (créances)
    v = mtm_by_ns[mtm_by_ns > 0].sum()

    # Collateral reçu
    c = 0.0
    if collateral_df is not None and not collateral_df.empty:
        c = collateral_df["collateral_amount"].sum()

    # RC = max(V - C, 0)
    rc = max(v - c, 0.0)

    return rc


def compute_pfe_addon_ir(trades_df: pd.DataFrame) -> float:
    """
    Calcule l'add-on PFE (Potential Future Exposure) pour Interest Rate.

    PFE_IR = SF_IR × Notional × Maturity_Factor

    Args:
        trades_df: DataFrame des trades IR avec colonnes:
            - notional: Notionnel
            - maturity_bucket: Bucket de maturité ("0-1Y", "1-5Y", ">5Y")

    Returns:
        Add-on PFE pour IR
    """
    if trades_df.empty:
        return 0.0

    # Appliquer les supervisory factors par bucket
    def apply_sf(row: pd.Series) -> float:
        bucket = row["maturity_bucket"]
        sf = SUPERVISORY_FACTORS["IR"].get(bucket, 0.0005)
        return sf * row["notional"]

    pfe = trades_df.apply(apply_sf, axis=1).sum()

    return pfe


def compute_pfe_addon_fx(trades_df: pd.DataFrame) -> float:
    """
    Calcule l'add-on PFE pour Foreign Exchange.

    PFE_FX = SF_FX × Notional

    Args:
        trades_df: DataFrame des trades FX avec colonnes:
            - notional: Notionnel

    Returns:
        Add-on PFE pour FX
    """
    if trades_df.empty:
        return 0.0

    sf = SUPERVISORY_FACTORS["FX"]
    pfe = (trades_df["notional"] * sf).sum()

    return pfe


def compute_pfe_addon_equity(trades_df: pd.DataFrame) -> float:
    """
    Calcule l'add-on PFE pour Equity.

    PFE_Equity = SF_Equity × Notional

    Args:
        trades_df: DataFrame des trades Equity avec colonnes:
            - notional: Notionnel

    Returns:
        Add-on PFE pour Equity
    """
    if trades_df.empty:
        return 0.0

    sf = SUPERVISORY_FACTORS["Equity"]
    pfe = (trades_df["notional"] * sf).sum()

    return pfe


def compute_pfe_addon_commodity(trades_df: pd.DataFrame) -> float:
    """
    Calcule l'add-on PFE pour Commodity.

    PFE_Commodity = SF_Commodity × Notional

    Args:
        trades_df: DataFrame des trades Commodity avec colonnes:
            - notional: Notionnel

    Returns:
        Add-on PFE pour Commodity
    """
    if trades_df.empty:
        return 0.0

    sf = SUPERVISORY_FACTORS["Commodity"]
    pfe = (trades_df["notional"] * sf).sum()

    return pfe


def compute_pfe_addon_credit(trades_df: pd.DataFrame) -> float:
    """
    Calcule l'add-on PFE pour Credit.

    PFE_Credit = SF_Credit × Notional

    Args:
        trades_df: DataFrame des trades Credit avec colonnes:
            - notional: Notionnel
            - rating: Rating ("IG" ou "HY")

    Returns:
        Add-on PFE pour Credit
    """
    if trades_df.empty:
        return 0.0

    # Appliquer les supervisory factors par rating
    def apply_sf(row: pd.Series) -> float:
        rating = row.get("rating", "HY")  # Défaut: High Yield
        sf = SUPERVISORY_FACTORS["Credit"].get(rating, 0.054)
        return sf * row["notional"]

    pfe = trades_df.apply(apply_sf, axis=1).sum()

    return pfe


def compute_pfe_addon(trades_df: pd.DataFrame) -> dict[str, float]:
    """
    Calcule les add-ons PFE par classe d'actifs.

    Args:
        trades_df: DataFrame des trades avec colonnes:
            - asset_class: Classe d'actifs ("IR", "FX", "Equity", "Commodity", "Credit")
            - notional: Notionnel
            - maturity_bucket: Bucket de maturité (pour IR)
            - rating: Rating (pour Credit)

    Returns:
        Dict des add-ons PFE par classe d'actifs
    """
    addons = {
        "IR": 0.0,
        "FX": 0.0,
        "Equity": 0.0,
        "Commodity": 0.0,
        "Credit": 0.0,
        "Total": 0.0,
    }

    # Grouper par classe d'actifs
    for asset_class, group in trades_df.groupby("asset_class"):
        if asset_class == "IR":
            addons["IR"] = compute_pfe_addon_ir(group)
        elif asset_class == "FX":
            addons["FX"] = compute_pfe_addon_fx(group)
        elif asset_class == "Equity":
            addons["Equity"] = compute_pfe_addon_equity(group)
        elif asset_class == "Commodity":
            addons["Commodity"] = compute_pfe_addon_commodity(group)
        elif asset_class == "Credit":
            addons["Credit"] = compute_pfe_addon_credit(group)

    # Total
    addons["Total"] = sum(
        addons[k] for k in ["IR", "FX", "Equity", "Commodity", "Credit"]
    )

    return addons


def compute_multiplier(
    trades_df: pd.DataFrame, pfe_addon_total: float, collateral_df: pd.DataFrame | None = None
) -> float:
    """
    Calcule le multiplier (NICA/CMV).

    multiplier = min(1, floor + (1 - floor) × exp(V / (2 × (1 - floor) × AddOn)))

    où floor = 0.05
        V = somme des MTM nets par netting set

    Args:
        trades_df: DataFrame des trades
        pfe_addon_total: Total des add-ons PFE
        collateral_df: DataFrame du collatéral (optionnel)

    Returns:
        Multiplier
    """
    floor = 0.05

    # V = somme des MTM nets
    v = trades_df["mtm"].sum()

    # Si V <= 0 ou AddOn = 0, multiplier = 1
    if v <= 0 or pfe_addon_total == 0:
        return 1.0

    # Formule du multiplier
    exp_term = np.exp(v / (2 * (1 - floor) * pfe_addon_total))
    multiplier = min(1.0, floor + (1 - floor) * exp_term)

    return multiplier


def compute_saccr_ead_detailed(
    trades_df: pd.DataFrame,
    collateral_df: pd.DataFrame | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Calcule l'EAD selon SA-CCR avec détails.

    EAD = Alpha × (RC + PFE)
    où PFE = multiplier × AddOn

    Args:
        trades_df: DataFrame des trades avec colonnes:
            - trade_id: Identifiant du trade
            - netting_set: Identifiant du netting set
            - asset_class: Classe d'actifs
            - notional: Notionnel
            - maturity_bucket: Bucket de maturité (pour IR)
            - rating: Rating (pour Credit)
            - mtm: Mark-to-Market
        collateral_df: DataFrame du collatéral (optionnel)
        params: Paramètres optionnels (alpha, supervisory factors override)

    Returns:
        Dict avec:
            - ead: EAD total
            - rc: Replacement Cost
            - pfe: Potential Future Exposure
            - pfe_addons: Dict des add-ons par classe
            - multiplier: Multiplier
            - alpha: Alpha utilisé
    """
    # Validation
    required_cols = [
        "trade_id",
        "netting_set",
        "asset_class",
        "notional",
        "mtm",
    ]
    missing_cols = [col for col in required_cols if col not in trades_df.columns]
    if missing_cols:
        raise ValueError(f"Colonnes manquantes dans trades_df: {missing_cols}")

    # Paramètres
    alpha = params.get("alpha", ALPHA) if params else ALPHA

    # 1. Replacement Cost (RC)
    rc = compute_replacement_cost(trades_df, collateral_df)

    # 2. PFE Add-ons par classe
    pfe_addons = compute_pfe_addon(trades_df)

    # 3. Multiplier
    multiplier = compute_multiplier(trades_df, pfe_addons["Total"], collateral_df)

    # 4. PFE
    pfe = multiplier * pfe_addons["Total"]

    # 5. EAD
    ead = alpha * (rc + pfe)

    return {
        "ead": ead,
        "rc": rc,
        "pfe": pfe,
        "pfe_addons": pfe_addons,
        "multiplier": multiplier,
        "alpha": alpha,
    }





# ============================================================================
# BA-CVA (Basic Approach for CVA Capital) - I7c
# ============================================================================


def compute_cva_capital_ba(
    ead_df: pd.DataFrame, params: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Calcule le capital CVA selon l'approche BA-CVA (Basic Approach).

    Formule simplifiée (CRR3 Article 384) :
    K_CVA = 2.33 × sqrt(Σ_i (w_i × M_i × EAD_i)²)

    où :
    - w_i = poids de la contrepartie (proxy rating/spread bucket)
    - M_i = maturité effective (en années)
    - EAD_i = Exposure At Default de la contrepartie

    Args:
        ead_df: DataFrame avec colonnes:
            - counterparty: Identifiant de la contrepartie
            - ead: Exposure At Default
            - maturity: Maturité effective (optionnel, défaut: 1 an)
            - weight: Poids (optionnel, défaut: 1.0)
        params: Paramètres optionnels:
            - default_maturity: Maturité par défaut (défaut: 1.0)
            - default_weight: Poids par défaut (défaut: 1.0)

    Returns:
        Dict avec:
            - k_cva: Capital CVA total
            - by_counterparty: DataFrame avec détails par contrepartie
    """
    # Validation
    if ead_df.empty:
        raise ValueError("ead_df ne peut pas être vide")

    if "counterparty" not in ead_df.columns or "ead" not in ead_df.columns:
        raise ValueError("ead_df doit contenir les colonnes 'counterparty' et 'ead'")

    # Paramètres
    default_maturity = params.get("default_maturity", 1.0) if params else 1.0
    default_weight = params.get("default_weight", 1.0) if params else 1.0

    # Copier le DataFrame pour ne pas modifier l'original
    df = ead_df.copy()

    # Ajouter maturity et weight si absents
    if "maturity" not in df.columns:
        df["maturity"] = default_maturity

    if "weight" not in df.columns:
        df["weight"] = default_weight

    # Calculer le terme (w_i × M_i × EAD_i)
    df["term"] = df["weight"] * df["maturity"] * df["ead"]

    # Calculer K_CVA = 2.33 × sqrt(Σ (term_i)²)
    sum_squared_terms = (df["term"] ** 2).sum()
    k_cva = 2.33 * np.sqrt(sum_squared_terms)

    # Préparer le DataFrame par contrepartie
    by_counterparty = df[["counterparty", "ead", "maturity", "weight", "term"]].copy()

    return {"k_cva": k_cva, "by_counterparty": by_counterparty}


# ============================================================================
# CVA Pricing v1 (Simplified) - I7c
# ============================================================================


def compute_cva_pricing_v1(
    trades_df: pd.DataFrame, params: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Calcule le CVA pricing selon une approche simplifiée v1.

    Formule :
    CVA ≈ (1 - R) × Σ_t DF(t) × ΔPD(t) × EE(t)

    où :
    - R = Recovery Rate (taux de recouvrement)
    - DF(t) = Discount Factor au temps t
    - ΔPD(t) = Probabilité de défaut incrémentale sur [t-1, t]
    - EE(t) = Expected Exposure au temps t (proxy depuis EAD SA-CCR)

    Simplifications v1 :
    - EE(t) constant = EAD (profil plat)
    - ΔPD(t) via hazard rate constant (λ = spread / LGD)
    - DF(t) = exp(-r × t) avec r = taux sans risque

    Args:
        trades_df: DataFrame avec colonnes:
            - counterparty: Identifiant de la contrepartie
            - ead: Exposure At Default (proxy pour EE)
            - spread: Spread de crédit (en bps, optionnel)
            - maturity: Maturité (en années, optionnel)
        params: Paramètres optionnels:
            - recovery_rate: Taux de recouvrement (défaut: 0.4)
            - risk_free_rate: Taux sans risque (défaut: 0.02)
            - default_spread: Spread par défaut (défaut: 100 bps)
            - default_maturity: Maturité par défaut (défaut: 1.0 an)
            - time_steps: Nombre de pas de temps (défaut: 10)

    Returns:
        Dict avec:
            - cva: CVA total
            - by_bucket: DataFrame avec détails par bucket de temps
    """
    # Validation
    if trades_df.empty:
        raise ValueError("trades_df ne peut pas être vide")

    if "counterparty" not in trades_df.columns or "ead" not in trades_df.columns:
        raise ValueError("trades_df doit contenir les colonnes 'counterparty' et 'ead'")

    # Paramètres
    recovery_rate = params.get("recovery_rate", 0.4) if params else 0.4
    risk_free_rate = params.get("risk_free_rate", 0.02) if params else 0.02
    default_spread = params.get("default_spread", 100) if params else 100  # bps
    default_maturity = params.get("default_maturity", 1.0) if params else 1.0
    time_steps = params.get("time_steps", 10) if params else 10

    # Copier le DataFrame
    df = trades_df.copy()

    # Ajouter spread et maturity si absents
    if "spread" not in df.columns:
        df["spread"] = default_spread

    if "maturity" not in df.columns:
        df["maturity"] = default_maturity

    # Calculer le CVA par contrepartie
    cva_total = 0.0
    buckets = []

    # Grouper par contrepartie
    for counterparty, group in df.groupby("counterparty"):
        ead = group["ead"].sum()
        spread_bps = group["spread"].mean()
        maturity = group["maturity"].mean()

        # Spread en décimal
        spread = spread_bps / 10000.0

        # Hazard rate λ = spread / (1 - R)
        lgd = 1 - recovery_rate
        hazard_rate = spread / lgd if lgd > 0 else 0.0

        # Discrétisation temporelle
        dt = maturity / time_steps

        for i in range(1, time_steps + 1):
            t = i * dt
            t_prev = (i - 1) * dt

            # Discount Factor DF(t) = exp(-r × t)
            df_t = np.exp(-risk_free_rate * t)

            # Probabilité de survie S(t) = exp(-λ × t)
            survival_t = np.exp(-hazard_rate * t)
            survival_t_prev = np.exp(-hazard_rate * t_prev)

            # Probabilité de défaut incrémentale ΔPD(t) = S(t-1) - S(t)
            delta_pd = survival_t_prev - survival_t

            # Expected Exposure EE(t) ≈ EAD (profil plat v1)
            ee_t = ead

            # CVA bucket = (1 - R) × DF(t) × ΔPD(t) × EE(t)
            cva_bucket = lgd * df_t * delta_pd * ee_t

            cva_total += cva_bucket

            buckets.append(
                {
                    "counterparty": counterparty,
                    "time": t,
                    "df": df_t,
                    "delta_pd": delta_pd,
                    "ee": ee_t,
                    "cva_contribution": cva_bucket,
                }
            )

    # Créer le DataFrame par bucket
    by_bucket = pd.DataFrame(buckets)

    return {"cva": cva_total, "by_bucket": by_bucket}

