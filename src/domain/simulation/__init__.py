"""
Module de simulation Monte Carlo.

Ce module expose la fonction publique generate_positions_advanced()
pour générer des portefeuilles de positions bancaires.
"""

from .monte_carlo import SimulationEngine, generate_positions_advanced

__all__ = ['generate_positions_advanced', 'SimulationEngine']
