"""
Reporting domain module - EBA-compliant COREP/FINREP calculations.

This module contains pure business logic for regulatory reporting
conforming to EBA v3.3 specifications.
"""

from src.domain.reporting.corep import (
    generate_corep_c07,
    generate_corep_c08,
    generate_corep_c34,
)
from src.domain.reporting.finrep import (
    generate_finrep_f09,
    generate_finrep_f18,
)

__all__ = [
    "generate_corep_c07",
    "generate_corep_c08",
    "generate_corep_c34",
    "generate_finrep_f09",
    "generate_finrep_f18",
]
