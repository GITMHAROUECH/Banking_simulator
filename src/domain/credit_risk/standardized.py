"""
Domain layer for standardized approach RWA calculations (CRR3).
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def compute_ead(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Exposure at Default (EAD) for standardized approach.

    Args:
        df: DataFrame with positions containing 'ead' column

    Returns:
        DataFrame with computed EAD values
    """
    result = df.copy()

    # EAD is already computed in the positions DataFrame
    # This function ensures the column exists and handles any adjustments
    if 'ead' not in result.columns:
        raise ValueError("Column 'ead' not found in positions DataFrame")

    # Handle missing values
    result['ead'] = result['ead'].fillna(0)

    # Apply CCF (Credit Conversion Factor) to off-balance sheet items if needed
    if 'undrawn' in result.columns and 'ccf' in result.columns:
        result['ead'] = result['ead'] + (result['undrawn'].fillna(0) * result['ccf'].fillna(0))

    return result


def risk_weight_for_row(row: pd.Series, config: dict) -> float:
    """
    Determine the risk weight for a single position based on exposure class.

    Args:
        row: Series representing a single position
        config: Configuration dictionary with standard_risk_weights

    Returns:
        Risk weight as a float (e.g., 1.0 for 100%)
    """
    exposure_class = row.get('exposure_class', 'corporates')
    product_id = row.get('product_id', '')

    # Get base risk weights from config
    standard_risk_weights = config.get('standard_risk_weights', {})
    base_weight = standard_risk_weights.get(exposure_class, 1.0)

    # Apply specific adjustments based on exposure class
    if exposure_class == 'corporates':
        # SME reduction: 85% risk weight
        if 'SME' in product_id:
            return 0.85
        return base_weight

    elif exposure_class == 'institutions':
        # Standard weight for institutions (20%)
        return 0.20

    elif exposure_class == 'secured_by_mortgages':
        # Residential mortgages: 35% risk weight
        if 'MORTGAGE' in product_id:
            return 0.35
        return base_weight

    elif exposure_class == 'retail':
        # Retail exposures: 75% risk weight
        return 0.75

    elif exposure_class == 'central_governments':
        # Sovereign exposures: 0% for high-quality, 100% otherwise
        return 0.0 if row.get('rating', '') in ['AAA', 'AA'] else 1.0

    elif exposure_class == 'exposures_in_default':
        # Defaulted exposures: 150% risk weight
        return 1.50

    elif exposure_class == 'high_risk_categories':
        # High risk: 150% risk weight
        return 1.50

    elif exposure_class == 'equity':
        # Equity exposures: 100% to 250% depending on type
        return 2.50 if 'SPECULATIVE' in product_id else 1.00

    else:
        # Default risk weight
        return base_weight


def compute_rwa_standardized(positions: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Compute Risk-Weighted Assets (RWA) using the standardized approach.

    Args:
        positions: DataFrame with bank positions
        config: Configuration dictionary with risk parameters

    Returns:
        DataFrame with columns:
        ['entity_id', 'exposure_class', 'approach', 'ead', 'risk_weight', 'rwa_amount', 'rwa_density']
    """
    logger.info("Computing RWA using standardized approach")

    if positions.empty:
        logger.warning("Empty positions DataFrame provided")
        return pd.DataFrame(columns=[
            'entity_id', 'product_id', 'exposure_class', 'approach',
            'ead', 'risk_weight', 'rwa_amount', 'rwa_density', 'stage'
        ])

    # Compute EAD
    positions_with_ead = compute_ead(positions)

    # Filter non-retail positions (standardized approach)
    if 'is_retail' in positions_with_ead.columns:
        non_retail = positions_with_ead[~positions_with_ead['is_retail']].copy()
    else:
        # If is_retail column doesn't exist, treat all as non-retail for standardized
        non_retail = positions_with_ead.copy()

    if non_retail.empty:
        logger.info("No non-retail positions found for standardized approach")
        return pd.DataFrame(columns=[
            'entity_id', 'product_id', 'exposure_class', 'approach',
            'ead', 'risk_weight', 'rwa_amount', 'rwa_density', 'stage'
        ])

    results = []

    for _, row in non_retail.iterrows():
        ead = row['ead']

        # Get risk weight for this position
        risk_weight = risk_weight_for_row(row, config)

        # Calculate RWA
        rwa_amount = ead * risk_weight

        # Calculate RWA density (as percentage)
        rwa_density = risk_weight

        results.append({
            'entity_id': row.get('entity_id', 'UNKNOWN'),
            'product_id': row.get('product_id', 'UNKNOWN'),
            'exposure_class': row.get('exposure_class', 'corporates'),
            'approach': 'Standardised',
            'ead': ead,
            'risk_weight': risk_weight,
            'rwa_amount': rwa_amount,
            'rwa_density': rwa_density,
            'stage': row.get('stage', 1)
        })

    result_df = pd.DataFrame(results)

    logger.info(f"Standardized RWA computed for {len(result_df)} positions. "
                f"Total RWA: {result_df['rwa_amount'].sum():,.0f}")

    return result_df

