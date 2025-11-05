"""
Domain layer for IRB (Internal Ratings-Based) approach RWA calculations (CRR3).
"""

import logging
import math

import pandas as pd
from scipy.stats import norm

logger = logging.getLogger(__name__)


def irb_correlation(row: pd.Series, config: dict) -> float:
    """
    Calculate IRB correlation based on product type and PD.

    Args:
        row: Series representing a single position
        config: Configuration dictionary

    Returns:
        Correlation value as float
    """
    product_id = row.get('product_id', '')
    pd_val = row.get('pd', 0.025)

    # Retail secured by mortgages
    if 'MORTGAGE' in product_id:
        return 0.15

    # Retail revolving (credit cards)
    elif 'CREDIT_CARDS' in product_id or 'CREDIT_CARD' in product_id:
        return 0.04

    # Other retail exposures
    elif 'RETAIL' in product_id:
        # R = 0.03 × (1 - exp(-35 × PD)) / (1 - exp(-35)) + 0.16 × [1 - (1 - exp(-35 × PD)) / (1 - exp(-35))]
        # Simplified: R = 0.03 + (PD - 0.03) × 0.16 if PD > 0.03 else 0.03
        return 0.03 + (pd_val - 0.03) * 0.16 if pd_val > 0.03 else 0.03

    # Corporate exposures (if IRB is applied)
    else:
        # R = 0.12 × (1 + exp(-50 × PD)) / (1 - exp(-50)) + 0.24 × [1 - (1 + exp(-50 × PD)) / (1 - exp(-50))]
        # Simplified approximation
        return 0.12 + 0.12 * (1 - math.exp(-50 * pd_val))


def irb_maturity_adj(row: pd.Series, config: dict) -> float:
    """
    Calculate maturity adjustment for IRB formula.

    Args:
        row: Series representing a single position
        config: Configuration dictionary

    Returns:
        Maturity adjustment factor
    """
    product_id = row.get('product_id', '')
    pd_val = row.get('pd', 0.025)

    # Determine effective maturity
    maturity_mapping = {
        'RETAIL_MORTGAGE': 15.0,
        'RETAIL_CONSUMER': 3.0,
        'RETAIL_CREDIT_CARDS': 1.0,
        'RETAIL_CREDIT_CARD': 1.0,
    }

    maturity = maturity_mapping.get(product_id, 2.5)  # Default 2.5 years

    # For retail exposures with maturity <= 1 year, no maturity adjustment
    if maturity <= 1.0:
        return 1.0

    # Maturity adjustment formula for non-retail or long-term retail
    # b = (0.11852 - 0.05478 × ln(PD))²
    # MA = (1 + (M - 2.5) × b) / (1 - 1.5 × b)

    try:
        b = (0.11852 - 0.05478 * math.log(max(0.0001, pd_val))) ** 2
        maturity_adjustment = (1 + (maturity - 2.5) * b) / (1 - 1.5 * b)
        return max(0.5, min(3.0, maturity_adjustment))  # Cap between 0.5 and 3.0
    except (ValueError, ZeroDivisionError):
        logger.warning(f"Error calculating maturity adjustment for PD={pd_val}, using 1.0")
        return 1.0


def irb_formula(pd_val: float, lgd_val: float, correlation: float, maturity: float) -> float:
    """
    Calculate RWA density using IRB foundation formula.

    Formula:
    K = LGD × N[(1-R)^(-0.5) × G(PD) + (R/(1-R))^0.5 × G(0.999)] - PD × LGD
    RWA_density = K × 12.5 × MA

    Args:
        pd_val: Probability of Default
        lgd_val: Loss Given Default
        correlation: Asset correlation
        maturity: Effective maturity in years

    Returns:
        RWA density (multiplier for EAD)
    """
    try:
        # Constrain input values to valid ranges
        pd_val = max(0.0001, min(0.9999, pd_val))
        lgd_val = max(0.01, min(0.99, lgd_val))
        correlation = max(0.01, min(0.99, correlation))
        maturity = max(1.0, min(7.0, maturity))

        # Calculate inverse normal distribution values
        g_pd = norm.ppf(pd_val)
        g_999 = norm.ppf(0.999)

        # Calculate correlation components
        sqrt_r = math.sqrt(correlation)
        sqrt_1_minus_r = math.sqrt(1 - correlation)

        # Calculate N[...] term
        n_arg = (g_pd / sqrt_1_minus_r) + (sqrt_r / sqrt_1_minus_r) * g_999
        n_value = norm.cdf(n_arg)

        # Calculate capital requirement K
        k = lgd_val * n_value - pd_val * lgd_val
        k = max(0, k)  # K cannot be negative

        # Apply maturity adjustment for non-retail exposures
        if maturity > 1.0:
            b = (0.11852 - 0.05478 * math.log(pd_val)) ** 2
            maturity_adjustment = (1 + (maturity - 2.5) * b) / (1 - 1.5 * b)
            k *= maturity_adjustment

        # Convert to RWA density (K × 12.5, where 12.5 = 1/0.08)
        rwa_density = k * 12.5

        return max(0, rwa_density)

    except Exception as e:
        logger.warning(f"Error in IRB formula calculation: {e}, returning default 1.0")
        return 1.0  # 100% risk weight as fallback


def compute_rwa_irb(positions: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Compute Risk-Weighted Assets (RWA) using the IRB approach.

    Args:
        positions: DataFrame with bank positions
        config: Configuration dictionary with IRB parameters

    Returns:
        DataFrame with columns:
        ['entity_id', 'exposure_class', 'approach', 'ead', 'pd', 'lgd', 'maturity',
         'correlation', 'risk_weight', 'rwa_amount', 'rwa_density']
    """
    logger.info("Computing RWA using IRB approach")

    if positions.empty:
        logger.warning("Empty positions DataFrame provided")
        return pd.DataFrame(columns=[
            'entity_id', 'product_id', 'exposure_class', 'approach', 'ead',
            'pd', 'lgd', 'maturity', 'correlation', 'rwa_density', 'rwa_amount', 'stage'
        ])

    # Filter retail positions (IRB approach typically for retail)
    if 'is_retail' in positions.columns:
        retail = positions[positions['is_retail']].copy()
    else:
        # If is_retail column doesn't exist, assume all positions can use IRB
        retail = positions.copy()

    if retail.empty:
        logger.info("No retail positions found for IRB approach")
        return pd.DataFrame(columns=[
            'entity_id', 'product_id', 'exposure_class', 'approach', 'ead',
            'pd', 'lgd', 'maturity', 'correlation', 'rwa_density', 'rwa_amount', 'stage'
        ])

    results = []

    for _, row in retail.iterrows():
        ead = row.get('ead', 0)
        pd_val = row.get('pd', 0.025)  # Default 2.5% PD
        lgd_val = row.get('lgd', 0.45)  # Default 45% LGD

        # Calculate correlation
        correlation = irb_correlation(row, config)

        # Get maturity
        product_id = row.get('product_id', '')
        maturity_mapping = {
            'RETAIL_MORTGAGE': 15.0,
            'RETAIL_CONSUMER': 3.0,
            'RETAIL_CREDIT_CARDS': 1.0,
            'RETAIL_CREDIT_CARD': 1.0,
        }
        maturity = maturity_mapping.get(product_id, 2.5)

        # Calculate RWA density using IRB formula
        rwa_density = irb_formula(pd_val, lgd_val, correlation, maturity)

        # Calculate RWA amount
        rwa_amount = ead * rwa_density

        results.append({
            'entity_id': row.get('entity_id', 'UNKNOWN'),
            'product_id': row.get('product_id', 'UNKNOWN'),
            'exposure_class': row.get('exposure_class', 'retail'),
            'approach': 'IRB',
            'ead': ead,
            'pd': pd_val,
            'lgd': lgd_val,
            'maturity': maturity,
            'correlation': correlation,
            'rwa_density': rwa_density,
            'rwa_amount': rwa_amount,
            'stage': row.get('stage', 1)
        })

    result_df = pd.DataFrame(results)

    logger.info(f"IRB RWA computed for {len(result_df)} positions. "
                f"Total RWA: {result_df['rwa_amount'].sum():,.0f}")

    return result_df

