"""
FINREP (Financial Reporting) - EBA v3.3 compliant calculations.

This module implements FINREP calculations according to EBA ITS on Financial Reporting
(Commission Implementing Regulation EU 2021/451, Annex V).

Key templates implemented:
- F09: Impairment and Provisions (IFRS 9 ECL)
- F18: Loans and Advances by Product and by Counterparty Sector

References:
- EBA ITS on Supervisory Reporting v3.3, Annex V (FINREP)
- IFRS 9 Financial Instruments
- CRR3 (for exposure class definitions)
"""

from typing import Optional

import pandas as pd


# ============================================================================
# FINREP Staging Mapping (IFRS 9)
# ============================================================================

IFRS9_STAGE_MAPPING = {
    "S1": "Performing",  # Stage 1: No SICR, 12-month ECL
    "S2": "Underperforming",  # Stage 2: SICR, lifetime ECL
    "S3": "Non-performing",  # Stage 3: Default, lifetime ECL
}


# ============================================================================
# FINREP F09: Impairment and Provisions (IFRS 9 ECL)
# ============================================================================


def generate_finrep_f09(
    ecl_results_df: pd.DataFrame,
    positions_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Generate FINREP F09 (Impairment and Provisions under IFRS 9).

    Implements EBA ITS F 09.00 - Impairment and provisions, including breakdown
    by IFRS 9 stages (Stage 1/2/3) and exposure classes.

    Args:
        ecl_results_df: DataFrame with ECL calculation results (from ecl_results table).
            Required columns:
            - stage: IFRS 9 stage (S1/S2/S3)
            - ead: Exposure at Default (gross carrying amount)
            - ecl_amount: Expected Credit Loss amount
            - exposure_id: Link to exposure (for joining with positions_df)
        positions_df: Optional DataFrame with additional exposure info (exposure_class, entity, currency)

    Returns:
        DataFrame with FINREP F09 structure:
        - Exposure_Class: Exposure class (Corporate, Retail, Sovereign, etc.)
        - Stage: IFRS 9 stage (Performing, Underperforming, Non-performing)
        - Gross_Carrying_Amount: Gross carrying amount before impairment (= EAD)
        - Accumulated_Impairment: Accumulated impairment (= cumulative ECL)
        - Net_Carrying_Amount: Net carrying amount (Gross - Impairment)
        - ECL_Coverage_Ratio_Pct: Coverage ratio (Impairment / Gross × 100%)

    References:
        - EBA ITS v3.3, Annex V, Template F 09.00
        - IFRS 9 Financial Instruments (ECL impairment model)
    """
    # Validation
    if ecl_results_df.empty:
        return pd.DataFrame(
            columns=[
                "Exposure_Class",
                "Stage",
                "Gross_Carrying_Amount",
                "Accumulated_Impairment",
                "Net_Carrying_Amount",
                "ECL_Coverage_Ratio_Pct",
            ]
        )

    # Required columns check
    required_cols = ["stage", "ead", "ecl_amount"]
    for col in required_cols:
        if col not in ecl_results_df.columns:
            raise ValueError(f"ecl_results_df must contain '{col}' column")

    # Merge with positions_df to get exposure_class (if provided)
    if positions_df is not None and not positions_df.empty:
        if "exposure_id" in ecl_results_df.columns and "id" in positions_df.columns:
            # Join on exposure_id
            ecl_with_class = ecl_results_df.merge(
                positions_df[["id", "exposure_class"]],
                left_on="exposure_id",
                right_on="id",
                how="left",
            )
        elif "exposure_class" in ecl_results_df.columns:
            ecl_with_class = ecl_results_df.copy()
        else:
            # Fallback: no exposure_class available
            ecl_with_class = ecl_results_df.copy()
            ecl_with_class["exposure_class"] = "Other"
    else:
        if "exposure_class" in ecl_results_df.columns:
            ecl_with_class = ecl_results_df.copy()
        else:
            ecl_with_class = ecl_results_df.copy()
            ecl_with_class["exposure_class"] = "Other"

    # Map IFRS 9 stages to FINREP labels
    ecl_with_class["Stage"] = ecl_with_class["stage"].map(IFRS9_STAGE_MAPPING)

    # Aggregate by exposure_class and Stage
    groupby_cols = ["exposure_class", "Stage"]

    f09_agg = (
        ecl_with_class.groupby(groupby_cols)
        .agg(
            {
                "ead": "sum",  # Gross Carrying Amount
                "ecl_amount": "sum",  # Accumulated Impairment
            }
        )
        .reset_index()
    )

    f09_agg = f09_agg.rename(
        columns={
            "exposure_class": "Exposure_Class",
            "ead": "Gross_Carrying_Amount",
            "ecl_amount": "Accumulated_Impairment",
        }
    )

    # Calculate Net Carrying Amount = Gross - Impairment
    f09_agg["Net_Carrying_Amount"] = (
        f09_agg["Gross_Carrying_Amount"] - f09_agg["Accumulated_Impairment"]
    )

    # Calculate ECL Coverage Ratio = (Impairment / Gross) × 100%
    f09_agg["ECL_Coverage_Ratio_Pct"] = (
        (f09_agg["Accumulated_Impairment"] / f09_agg["Gross_Carrying_Amount"]) * 100
    ).fillna(0.0)

    # Fill NaN with 0
    f09_agg = f09_agg.fillna(0.0)

    # Sort by Exposure_Class and Stage
    stage_order = {"Performing": 1, "Underperforming": 2, "Non-performing": 3}
    f09_agg["Stage_Order"] = f09_agg["Stage"].map(stage_order)
    f09_agg = f09_agg.sort_values(["Exposure_Class", "Stage_Order"])
    f09_agg = f09_agg.drop(columns=["Stage_Order"])

    # Select and order columns
    f09_agg = f09_agg[
        [
            "Exposure_Class",
            "Stage",
            "Gross_Carrying_Amount",
            "Accumulated_Impairment",
            "Net_Carrying_Amount",
            "ECL_Coverage_Ratio_Pct",
        ]
    ]

    return f09_agg


# ============================================================================
# FINREP F18: Loans and Advances
# ============================================================================


def generate_finrep_f18(positions_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate FINREP F18 (Loans and Advances).

    Implements EBA ITS F 18.00 - Loans and advances by product and counterparty sector,
    including breakdown by maturity buckets and collateral type.

    Args:
        positions_df: DataFrame with loan exposure data.
            Required columns:
            - product_type: Must be "Loan" (filters only loans)
            - exposure_class: Exposure class (Corporate, Retail, Sovereign, etc.)
            - notional or ead: Loan amount
            - maturity_years: Residual maturity in years (for maturity buckets)
            Optional columns:
            - entity: Legal entity
            - currency: Currency (EUR, USD, etc.)
            - collateral_value: Collateral value (for collateral type classification)

    Returns:
        DataFrame with FINREP F18 structure:
        - Exposure_Class: Exposure class
        - Maturity_Bucket: Maturity bucket (<1y, 1-5y, >5y)
        - Total_Loans: Total loan amount
        - Secured_Loans: Loans with collateral (if collateral_value > 0)
        - Unsecured_Loans: Loans without collateral

    References:
        - EBA ITS v3.3, Annex V, Template F 18.00
        - FINREP Part 2 (Asset breakdown)
    """
    # Validation
    if positions_df.empty:
        return pd.DataFrame(
            columns=[
                "Exposure_Class",
                "Maturity_Bucket",
                "Total_Loans",
                "Secured_Loans",
                "Unsecured_Loans",
            ]
        )

    # Filter only loans
    if "product_type" in positions_df.columns:
        loans_df = positions_df[positions_df["product_type"] == "Loan"].copy()
    else:
        # Assume all positions are loans if product_type not available
        loans_df = positions_df.copy()

    if loans_df.empty:
        return pd.DataFrame(
            columns=[
                "Exposure_Class",
                "Maturity_Bucket",
                "Total_Loans",
                "Secured_Loans",
                "Unsecured_Loans",
            ]
        )

    # Determine loan amount column
    if "ead" in loans_df.columns:
        loan_amount_col = "ead"
    elif "notional" in loans_df.columns:
        loan_amount_col = "notional"
    else:
        raise ValueError("positions_df must contain 'ead' or 'notional' column")

    # Create maturity buckets
    if "maturity_years" in loans_df.columns:
        loans_df["Maturity_Bucket"] = loans_df["maturity_years"].apply(
            _classify_maturity_bucket
        )
    else:
        # Default: Unknown maturity
        loans_df["Maturity_Bucket"] = "Unknown"

    # Classify secured vs unsecured loans
    if "collateral_value" in loans_df.columns:
        loans_df["Secured_Amount"] = loans_df.apply(
            lambda row: row[loan_amount_col]
            if row["collateral_value"] > 0
            else 0.0,
            axis=1,
        )
        loans_df["Unsecured_Amount"] = loans_df.apply(
            lambda row: 0.0 if row["collateral_value"] > 0 else row[loan_amount_col],
            axis=1,
        )
    else:
        # Default: all unsecured
        loans_df["Secured_Amount"] = 0.0
        loans_df["Unsecured_Amount"] = loans_df[loan_amount_col]

    # Aggregate by exposure_class and Maturity_Bucket
    groupby_cols = ["exposure_class", "Maturity_Bucket"]

    f18_agg = (
        loans_df.groupby(groupby_cols)
        .agg(
            {
                loan_amount_col: "sum",
                "Secured_Amount": "sum",
                "Unsecured_Amount": "sum",
            }
        )
        .reset_index()
    )

    f18_agg = f18_agg.rename(
        columns={
            "exposure_class": "Exposure_Class",
            loan_amount_col: "Total_Loans",
            "Secured_Amount": "Secured_Loans",
            "Unsecured_Amount": "Unsecured_Loans",
        }
    )

    # Fill NaN with 0
    f18_agg = f18_agg.fillna(0.0)

    # Sort by Exposure_Class and Maturity_Bucket
    maturity_order = {"<1y": 1, "1-5y": 2, ">5y": 3, "Unknown": 4}
    f18_agg["Maturity_Order"] = f18_agg["Maturity_Bucket"].map(maturity_order)
    f18_agg = f18_agg.sort_values(["Exposure_Class", "Maturity_Order"])
    f18_agg = f18_agg.drop(columns=["Maturity_Order"])

    # Select and order columns
    f18_agg = f18_agg[
        [
            "Exposure_Class",
            "Maturity_Bucket",
            "Total_Loans",
            "Secured_Loans",
            "Unsecured_Loans",
        ]
    ]

    return f18_agg


# ============================================================================
# Helper Functions
# ============================================================================


def _classify_maturity_bucket(maturity_years: float) -> str:
    """
    Classify residual maturity into buckets.

    Args:
        maturity_years: Residual maturity in years

    Returns:
        Maturity bucket: "<1y", "1-5y", ">5y", or "Unknown"
    """
    if pd.isna(maturity_years):
        return "Unknown"
    elif maturity_years < 1.0:
        return "<1y"
    elif 1.0 <= maturity_years <= 5.0:
        return "1-5y"
    else:
        return ">5y"
