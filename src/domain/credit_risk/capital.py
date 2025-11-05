"""
Domain layer for capital ratio calculations (CRR3).
"""

import logging

logger = logging.getLogger(__name__)


def compute_capital_ratios(
    rwa_total: float,
    capital_base: dict[str, float],
    buffers: dict[str, float]
) -> dict[str, float]:
    """
    Calculate capital ratios according to CRR3 requirements.

    Args:
        rwa_total: Total Risk-Weighted Assets
        capital_base: Dictionary with capital components:
            - 'cet1_capital': Common Equity Tier 1 capital
            - 'tier1_capital': Tier 1 capital (includes CET1 + AT1)
            - 'total_capital': Total capital (includes Tier 1 + Tier 2)
        buffers: Dictionary with regulatory buffers:
            - 'capital_conservation_buffer': Capital conservation buffer (typically 2.5%)
            - 'countercyclical_buffer': Countercyclical buffer (0-2.5%)
            - 'systemic_buffer': Systemic risk buffer (0-3%)

    Returns:
        Dictionary with calculated ratios and requirements:
        {
            'total_rwa': Total RWA,
            'cet1_capital': CET1 capital amount,
            'tier1_capital': Tier 1 capital amount,
            'total_capital': Total capital amount,
            'cet1_ratio': CET1 ratio (%),
            'tier1_ratio': Tier 1 ratio (%),
            'total_capital_ratio': Total capital ratio (%),
            'cet1_requirement': CET1 minimum requirement (%),
            'tier1_requirement': Tier 1 minimum requirement (%),
            'total_requirement': Total capital minimum requirement (%),
            'cet1_surplus': CET1 surplus vs requirement (pp),
            'tier1_surplus': Tier 1 surplus vs requirement (pp),
            'total_surplus': Total capital surplus vs requirement (pp)
        }
    """
    logger.info(f"Computing capital ratios for RWA: {rwa_total:,.0f}")

    if rwa_total <= 0:
        logger.warning("RWA total is zero or negative, returning zero ratios")
        return {
            'total_rwa': 0,
            'cet1_capital': 0,
            'tier1_capital': 0,
            'total_capital': 0,
            'cet1_ratio': 0,
            'tier1_ratio': 0,
            'total_capital_ratio': 0,
            'cet1_requirement': 4.5,
            'tier1_requirement': 6.0,
            'total_requirement': 8.0,
            'cet1_surplus': -4.5,
            'tier1_surplus': -6.0,
            'total_surplus': -8.0
        }

    # Extract capital components
    cet1_capital = capital_base.get('cet1_capital', 0)
    tier1_capital = capital_base.get('tier1_capital', cet1_capital)  # Default to CET1 if not provided
    total_capital = capital_base.get('total_capital', tier1_capital * 1.25)  # Default estimate

    # Calculate capital ratios (as percentages)
    cet1_ratio = (cet1_capital / rwa_total) * 100
    tier1_ratio = (tier1_capital / rwa_total) * 100
    total_capital_ratio = (total_capital / rwa_total) * 100

    # Regulatory minimum requirements (Pillar 1)
    cet1_minimum = 4.5  # 4.5% minimum
    tier1_minimum = 6.0  # 6.0% minimum
    total_minimum = 8.0  # 8.0% minimum

    # Extract buffers (as percentages)
    conservation_buffer = buffers.get('capital_conservation_buffer', 2.5)
    countercyclical_buffer = buffers.get('countercyclical_buffer', 0.0)
    systemic_buffer = buffers.get('systemic_buffer', 0.0)

    # Total buffer requirement (applied to CET1)
    total_buffer = conservation_buffer + countercyclical_buffer + systemic_buffer

    # Total requirements including buffers
    cet1_requirement = cet1_minimum + total_buffer
    tier1_requirement = tier1_minimum + total_buffer
    total_requirement = total_minimum + total_buffer

    # Calculate surplus/deficit vs requirements
    cet1_surplus = cet1_ratio - cet1_requirement
    tier1_surplus = tier1_ratio - tier1_requirement
    total_surplus = total_capital_ratio - total_requirement

    result = {
        'total_rwa': rwa_total,
        'cet1_capital': cet1_capital,
        'tier1_capital': tier1_capital,
        'total_capital': total_capital,
        'cet1_ratio': round(cet1_ratio, 2),
        'tier1_ratio': round(tier1_ratio, 2),
        'total_capital_ratio': round(total_capital_ratio, 2),
        'cet1_requirement': round(cet1_requirement, 2),
        'tier1_requirement': round(tier1_requirement, 2),
        'total_requirement': round(total_requirement, 2),
        'cet1_surplus': round(cet1_surplus, 2),
        'tier1_surplus': round(tier1_surplus, 2),
        'total_surplus': round(total_surplus, 2)
    }

    logger.info(f"Capital ratios computed - CET1: {cet1_ratio:.2f}%, "
                f"Tier1: {tier1_ratio:.2f}%, Total: {total_capital_ratio:.2f}%")

    return result


def compute_leverage_ratio(
    tier1_capital: float,
    total_exposure: float,
    minimum_requirement: float = 3.0
) -> dict[str, float]:
    """
    Calculate leverage ratio according to CRR3.

    Args:
        tier1_capital: Tier 1 capital amount
        total_exposure: Total exposure measure
        minimum_requirement: Minimum leverage ratio requirement (default 3%)

    Returns:
        Dictionary with leverage ratio metrics
    """
    if total_exposure <= 0:
        logger.warning("Total exposure is zero or negative")
        return {
            'tier1_capital': tier1_capital,
            'total_exposure': 0,
            'leverage_ratio': 0,
            'minimum_requirement': minimum_requirement,
            'surplus': -minimum_requirement
        }

    leverage_ratio = (tier1_capital / total_exposure) * 100
    surplus = leverage_ratio - minimum_requirement

    return {
        'tier1_capital': tier1_capital,
        'total_exposure': total_exposure,
        'leverage_ratio': round(leverage_ratio, 2),
        'minimum_requirement': minimum_requirement,
        'surplus': round(surplus, 2)
    }

