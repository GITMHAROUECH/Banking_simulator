"""
Couche Services - Orchestration de la logique métier.

Expose les services d'orchestration pour la simulation, le risque,
la consolidation et le reporting.
"""

from src.services.consolidation_service import consolidate_and_reconcile
from src.services.pipeline_service import create_pipeline_export, run_full_pipeline
from src.services.reporting_service import create_excel_export
from src.services.risk_service import compute_capital, compute_liquidity, compute_rwa
from src.services.simulation_service import run_simulation

__all__ = [
    # Simulation
    'run_simulation',
    # Risk
    'compute_rwa',
    'compute_liquidity',
    'compute_capital',
    # Consolidation
    'consolidate_and_reconcile',
    # Reporting
    'create_excel_export',
    # Pipeline E2E (I7a)
    'run_full_pipeline',
    # Export Pipeline (I8)
    'create_pipeline_export',
]
