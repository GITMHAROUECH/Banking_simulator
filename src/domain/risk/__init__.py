"""
Module de calcul des risques (Credit, Liquidity, Capital).

Ce module expose les fonctions publiques pour le calcul des RWA,
des ratios de liquidité (LCR/NSFR) et des ratios de capital.
"""

from .capital import compute_capital_ratios
from .credit_risk import calculate_rwa_advanced
from .liquidity import calculate_liquidity_advanced

__all__ = [
    'calculate_rwa_advanced',
    'calculate_liquidity_advanced',
    'compute_capital_ratios'
]
