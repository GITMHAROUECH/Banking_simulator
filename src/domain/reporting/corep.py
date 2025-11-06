"""
COREP (Common Reporting) - EBA v3.3 compliant calculations.

This module implements full COREP calculations according to EBA ITS on Supervisory Reporting
(Commission Implementing Regulation EU 2021/451, as amended).

Key templates implemented:
- C07: Credit Risk - Standardised Approach - Exposures
- C08: Credit Risk - Risk-Weighted Exposure Amounts (RWEAs)
- C34: Counterparty Credit Risk - SA-CCR

References:
- EBA ITS on Supervisory Reporting v3.3
- CRR3 (Regulation EU 575/2013, as amended)
- Commission Delegated Regulation EU 2022/2453
"""

from typing import Any

import pandas as pd


# ============================================================================
# EBA Exposure Class Mapping (CRR3 Article 112-134)
# ============================================================================

EBA_EXPOSURE_CLASS_MAPPING = {
    # CRR3 Standardized Approach Classes
    "Sovereign": "010",  # Central governments or central banks
    "Regional": "020",  # Regional governments or local authorities
    "PublicSector": "030",  # Public sector entities
    "MDB": "040",  # Multilateral development banks
    "International": "050",  # International organisations
    "Institution": "060",  # Institutions
    "Corporate": "070",  # Corporates
    "Retail": "080",  # Retail exposures
    "RealEstate": "090",  # Secured by mortgages on immovable property
    "Default": "100",  # Exposures in default
    "HighRisk": "110",  # Items associated with particularly high risk
    "CoveredBonds": "120",  # Covered bonds
    "ShortTerm": "130",  # Claims on institutions and corporates (short-term)
    "CIU": "140",  # Collective investment undertakings
    "Equity": "150",  # Equity exposures
    "Other": "160",  # Other items
}

# Risk Weights by Exposure Class (CRR3 Article 112-134)
STANDARD_RISK_WEIGHTS = {
    "Sovereign": 0.0,  # AAA-AA (0%), A-BBB (20%), BB-B (50%), below B (150%)
    "Regional": 0.20,  # Default: 20%
    "PublicSector": 0.20,
    "MDB": 0.0,  # AAA-AA: 0%
    "International": 0.0,
    "Institution": 0.20,  # Default: 20% (depends on credit quality)
    "Corporate": 1.0,  # Unrated: 100%
    "Retail": 0.75,  # 75%
    "RealEstate": 0.35,  # Residential: 35%, Commercial: 100%
    "Default": 1.5,  # 150%
    "HighRisk": 1.5,  # 150%
    "CoveredBonds": 0.10,  # AAA-AA: 10%
    "ShortTerm": 0.20,  # <3 months: 20%
    "CIU": 1.0,  # 100% (or look-through)
    "Equity": 1.0,  # 100% (or 250%/370% for IRB)
    "Other": 1.0,  # 100%
}


# ============================================================================
# COREP C07: Credit Risk - Standardised Approach - Exposures
# ============================================================================


def generate_corep_c07(positions_df: pd.DataFrame, rwa_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate COREP C07 (Credit Risk - Standardised Approach - Exposures).

    Implements EBA ITS C 07.00 - Credit risk: Standardised Approach - Exposures.

    Args:
        positions_df: DataFrame with exposure data (columns: exposure_class, notional, ead, etc.)
        rwa_df: DataFrame with RWA calculations (columns: exposure_class, rwa, risk_weight, etc.)

    Returns:
        DataFrame with COREP C07 structure:
        - EBA_Code: EBA exposure class code (010-160)
        - Exposure_Class: Human-readable exposure class name
        - Original_Exposure: Gross exposure before credit risk mitigation (CRM)
        - Exposure_Value: Exposure value after CRM (= EAD)
        - RWEA: Risk-Weighted Exposure Amount
        - Risk_Weight_Pct: Applicable risk weight (%)
        - Own_Funds_Requirements: Capital requirements (8% of RWEA)

    References:
        - EBA ITS v3.3, Annex III, Part 2, Template C 07.00
        - CRR3 Article 111-134 (Standardised Approach)
    """
    # Validation
    if positions_df.empty:
        return pd.DataFrame(
            columns=[
                "EBA_Code",
                "Exposure_Class",
                "Original_Exposure",
                "Exposure_Value",
                "RWEA",
                "Risk_Weight_Pct",
                "Own_Funds_Requirements",
            ]
        )

    # Determine exposure column (ead or notional)
    exposure_col = "ead" if "ead" in positions_df.columns else "notional"
    if exposure_col not in positions_df.columns:
        raise ValueError("positions_df must contain 'ead' or 'notional' column")

    # Aggregate original exposures by exposure_class
    original_exposure = (
        positions_df.groupby("exposure_class")[exposure_col]
        .sum()
        .reset_index()
        .rename(columns={exposure_col: "Original_Exposure"})
    )

    # Aggregate EAD (after CRM) by exposure_class
    if "ead" in positions_df.columns:
        exposure_value = (
            positions_df.groupby("exposure_class")["ead"]
            .sum()
            .reset_index()
            .rename(columns={"ead": "Exposure_Value"})
        )
    else:
        # If no EAD, assume original exposure = exposure value (no CRM)
        exposure_value = original_exposure.copy()
        exposure_value = exposure_value.rename(
            columns={"Original_Exposure": "Exposure_Value"}
        )

    # Aggregate RWEA by exposure_class
    if not rwa_df.empty and "rwa" in rwa_df.columns:
        rwea = (
            rwa_df.groupby("exposure_class")["rwa"]
            .sum()
            .reset_index()
            .rename(columns={"rwa": "RWEA"})
        )
    else:
        # Fallback: calculate RWEA using standard risk weights
        rwea = exposure_value.copy()
        rwea["RWEA"] = rwea.apply(
            lambda row: row["Exposure_Value"]
            * STANDARD_RISK_WEIGHTS.get(row["exposure_class"], 1.0)
            * 12.5,
            axis=1,
        )

    # Merge all components
    c07_df = original_exposure.merge(exposure_value, on="exposure_class", how="outer")
    c07_df = c07_df.merge(rwea, on="exposure_class", how="outer")

    # Calculate risk weight (% ) = (RWEA / Exposure_Value) / 12.5
    c07_df["Risk_Weight_Pct"] = (
        (c07_df["RWEA"] / (c07_df["Exposure_Value"] * 12.5)) * 100
    ).fillna(0.0)

    # Calculate Own Funds Requirements = 8% of RWEA
    c07_df["Own_Funds_Requirements"] = c07_df["RWEA"] * 0.08

    # Map to EBA codes
    c07_df["EBA_Code"] = c07_df["exposure_class"].map(EBA_EXPOSURE_CLASS_MAPPING)
    c07_df = c07_df.rename(columns={"exposure_class": "Exposure_Class"})

    # Fill NaN with 0
    c07_df = c07_df.fillna(0.0)

    # Sort by EBA_Code
    c07_df = c07_df.sort_values("EBA_Code")

    # Select and order columns
    c07_df = c07_df[
        [
            "EBA_Code",
            "Exposure_Class",
            "Original_Exposure",
            "Exposure_Value",
            "RWEA",
            "Risk_Weight_Pct",
            "Own_Funds_Requirements",
        ]
    ]

    return c07_df


# ============================================================================
# COREP C08: Credit Risk - RWEAs
# ============================================================================


def generate_corep_c08(
    positions_df: pd.DataFrame, rwa_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Generate COREP C08 (Credit Risk - Risk-Weighted Exposure Amounts).

    Implements EBA ITS C 08.00 - Credit risk: Risk-Weighted Exposure Amounts (RWEAs)
    and own funds requirements by approach and exposure class.

    Args:
        positions_df: DataFrame with exposure data
        rwa_df: DataFrame with RWA calculations (must contain: exposure_class, rwa, approach)

    Returns:
        DataFrame with COREP C08 structure:
        - EBA_Code: EBA exposure class code
        - Exposure_Class: Human-readable exposure class
        - Approach: Standardised (STD) or IRB Foundation (FIRBAIRB or Advanced (AIRB)
        - Exposure_Value: Total exposure value
        - RWEA: Risk-Weighted Exposure Amount
        - Capital_Requirements: Own funds requirements (8% of RWEA)
        - Risk_Density_Pct: Risk density (RWEA / Exposure_Value × 100%)

    References:
        - EBA ITS v3.3, Annex III, Part 2, Template C 08.00
        - CRR3 Article 92 (Own funds requirements)
    """
    # Validation
    if rwa_df.empty or "rwa" not in rwa_df.columns:
        return pd.DataFrame(
            columns=[
                "EBA_Code",
                "Exposure_Class",
                "Approach",
                "Exposure_Value",
                "RWEA",
                "Capital_Requirements",
                "Risk_Density_Pct",
            ]
        )

    # Determine approach (STD vs IRB)
    if "approach" in rwa_df.columns:
        approach_col = "approach"
    else:
        # Default: Standardised Approach
        rwa_df = rwa_df.copy()
        rwa_df["approach"] = "STD"
        approach_col = "approach"

    # Aggregate by exposure_class and approach
    groupby_cols = ["exposure_class", approach_col]

    # Aggregate RWEA
    rwea_agg = (
        rwa_df.groupby(groupby_cols)["rwa"].sum().reset_index().rename(columns={"rwa": "RWEA"})
    )

    # Aggregate Exposure Value (EAD if available, otherwise notional)
    if "ead" in rwa_df.columns:
        exposure_value_agg = (
            rwa_df.groupby(groupby_cols)["ead"]
            .sum()
            .reset_index()
            .rename(columns={"ead": "Exposure_Value"})
        )
    elif "notional" in positions_df.columns:
        # Merge with positions_df to get notional
        rwa_with_notional = rwa_df.merge(
            positions_df[["exposure_class", "notional"]], on="exposure_class", how="left"
        )
        exposure_value_agg = (
            rwa_with_notional.groupby(groupby_cols)["notional"]
            .sum()
            .reset_index()
            .rename(columns={"notional": "Exposure_Value"})
        )
    else:
        # Fallback: Exposure_Value = RWEA / 12.5 / avg_risk_weight
        exposure_value_agg = rwea_agg.copy()
        exposure_value_agg["Exposure_Value"] = exposure_value_agg["RWEA"] / 12.5
        exposure_value_agg = exposure_value_agg[groupby_cols + ["Exposure_Value"]]

    # Merge
    c08_df = rwea_agg.merge(exposure_value_agg, on=groupby_cols, how="outer")

    # Calculate Capital Requirements = 8% of RWEA
    c08_df["Capital_Requirements"] = c08_df["RWEA"] * 0.08

    # Calculate Risk Density = (RWEA / Exposure_Value) × 100%
    c08_df["Risk_Density_Pct"] = (
        (c08_df["RWEA"] / c08_df["Exposure_Value"]) * 100
    ).fillna(0.0)

    # Map to EBA codes
    c08_df["EBA_Code"] = c08_df["exposure_class"].map(EBA_EXPOSURE_CLASS_MAPPING)
    c08_df = c08_df.rename(
        columns={"exposure_class": "Exposure_Class", approach_col: "Approach"}
    )

    # Fill NaN with 0
    c08_df = c08_df.fillna(0.0)

    # Sort by EBA_Code and Approach
    c08_df = c08_df.sort_values(["EBA_Code", "Approach"])

    # Select and order columns
    c08_df = c08_df[
        [
            "EBA_Code",
            "Exposure_Class",
            "Approach",
            "Exposure_Value",
            "RWEA",
            "Capital_Requirements",
            "Risk_Density_Pct",
        ]
    ]

    return c08_df


# ============================================================================
# COREP C34: Counterparty Credit Risk - SA-CCR
# ============================================================================


def generate_corep_c34(saccr: dict[str, Any]) -> pd.DataFrame:
    """
    Generate COREP C34 (Counterparty Credit Risk - SA-CCR).

    Implements EBA ITS C 34.00 - Counterparty credit risk (CCR) - SA-CCR method.

    Args:
        saccr: Dict with SA-CCR calculation results:
            - ead_df: DataFrame with EAD per netting set (columns: netting_set, ead_contribution, etc.)
            - rc: Replacement Cost (float)
            - pfe: Potential Future Exposure (float)
            - multiplier: Multiplier (float, 0.7-1.0)
            - alpha: Alpha factor (float, default 1.4 per CRR3)
            - pfe_addons: DataFrame with add-ons by asset class (optional)

    Returns:
        DataFrame with COREP C34 structure:
        - Netting_Set: Netting set identifier
        - Replacement_Cost: RC = max(V - C, 0) per netting set
        - PFE_Addon: Potential Future Exposure add-on
        - Multiplier: Multiplier (0.7-1.0)
        - Alpha: Alpha factor (1.4)
        - EAD: Exposure at Default = Alpha × (RC + PFE × Multiplier)
        - RWEA: Risk-Weighted Exposure Amount (if available)

    References:
        - EBA ITS v3.3, Annex III, Part 2, Template C 34.00
        - CRR3 Article 274-294 (SA-CCR)
    """
    # Validation
    if not saccr or "ead_df" not in saccr or saccr["ead_df"].empty:
        return pd.DataFrame(
            columns=[
                "Netting_Set",
                "Replacement_Cost",
                "PFE_Addon",
                "Multiplier",
                "Alpha",
                "EAD",
                "RWEA",
            ]
        )

    ead_df = saccr["ead_df"]

    # Extract global SA-CCR parameters
    rc_total = saccr.get("rc", 0.0)
    pfe_total = saccr.get("pfe", 0.0)
    multiplier = saccr.get("multiplier", 1.0)
    alpha = saccr.get("alpha", 1.4)

    # Aggregate by netting_set
    if "netting_set" in ead_df.columns:
        netting_set_col = "netting_set"
    elif "netting_set_id" in ead_df.columns:
        netting_set_col = "netting_set_id"
    else:
        # Fallback: create default netting set
        ead_df = ead_df.copy()
        ead_df["netting_set"] = "NS_DEFAULT"
        netting_set_col = "netting_set"

    c34_df = ead_df.groupby(netting_set_col).agg(
        {
            "ead_contribution": "sum",
        }
    ).reset_index()

    c34_df = c34_df.rename(
        columns={
            netting_set_col: "Netting_Set",
            "ead_contribution": "EAD",
        }
    )

    # Calculate RC per netting set (proportional allocation)
    total_ead = c34_df["EAD"].sum()
    if total_ead > 0:
        c34_df["Replacement_Cost"] = (c34_df["EAD"] / total_ead) * rc_total
        c34_df["PFE_Addon"] = (c34_df["EAD"] / total_ead) * pfe_total
    else:
        c34_df["Replacement_Cost"] = 0.0
        c34_df["PFE_Addon"] = 0.0

    # Add global parameters
    c34_df["Multiplier"] = multiplier
    c34_df["Alpha"] = alpha

    # Calculate RWEA if risk_weight available
    if "risk_weight" in ead_df.columns:
        rwea_agg = (
            ead_df.groupby(netting_set_col)
            .apply(lambda g: (g["ead_contribution"] * g.get("risk_weight", 1.0) * 12.5).sum())
            .reset_index(name="RWEA")
        )
        c34_df = c34_df.merge(rwea_agg, left_on="Netting_Set", right_on=netting_set_col, how="left")
        c34_df = c34_df.drop(columns=[netting_set_col])
    else:
        c34_df["RWEA"] = 0.0

    # Fill NaN with 0
    c34_df = c34_df.fillna(0.0)

    # Select and order columns
    c34_df = c34_df[
        [
            "Netting_Set",
            "Replacement_Cost",
            "PFE_Addon",
            "Multiplier",
            "Alpha",
            "EAD",
            "RWEA",
        ]
    ]

    return c34_df
