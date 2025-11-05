"""
Module de consolidation IFRS et réconciliation compta-risque.

Expose les fonctions publiques pour la consolidation et la réconciliation.
"""

from src.domain.consolidation.ifrs_conso import (
    build_group_structure,
    compute_minority_interest,
    consolidate_statements,
    perform_intercompany_eliminations,
)
from src.domain.consolidation.reconciliation import (
    aggregate_variances_by_entity,
    classify_variances,
    export_variances_summary,
    reconcile_ledger_vs_risk,
)

__all__ = [
    # IFRS Consolidation
    'build_group_structure',
    'consolidate_statements',
    'perform_intercompany_eliminations',
    'compute_minority_interest',
    # Reconciliation
    'reconcile_ledger_vs_risk',
    'classify_variances',
    'aggregate_variances_by_entity',
    'export_variances_summary',
]
