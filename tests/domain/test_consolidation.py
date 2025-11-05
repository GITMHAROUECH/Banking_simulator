"""
Tests unitaires pour le module de consolidation IFRS.
"""

import numpy as np
import pandas as pd
import pytest

from src.domain.consolidation.ifrs_conso import (
    build_group_structure,
    compute_minority_interest,
    consolidate_statements,
    perform_intercompany_eliminations,
)


class TestBuildGroupStructure:
    """Tests pour build_group_structure."""

    def test_minimal_structure(self):
        """Test: Structure minimale avec parent et subsidiaire."""
        entities_df = pd.DataFrame({
            'entity_id': ['PARENT', 'SUB1'],
            'parent_id': [None, 'PARENT'],
            'ownership_pct': [100.0, 80.0],
            'method': ['IG', 'IG'],
            'currency': ['EUR', 'EUR']
        })

        result = build_group_structure(entities_df)

        assert not result.empty
        assert len(result) == 2
        assert 'level' in result.columns
        assert 'path' in result.columns
        assert 'is_consolidated' in result.columns

        # Vérifier les niveaux
        parent_row = result[result['entity_id'] == 'PARENT'].iloc[0]
        assert parent_row['level'] == 0
        assert parent_row['is_consolidated']

        sub_row = result[result['entity_id'] == 'SUB1'].iloc[0]
        assert sub_row['level'] == 1
        assert sub_row['is_consolidated']

    def test_multiple_methods(self):
        """Test: Structure avec différentes méthodes (IG, IP, ME)."""
        entities_df = pd.DataFrame({
            'entity_id': ['PARENT', 'SUB_IG', 'SUB_IP', 'SUB_ME'],
            'parent_id': [None, 'PARENT', 'PARENT', 'PARENT'],
            'ownership_pct': [100.0, 80.0, 40.0, 15.0],
            'method': ['IG', 'IG', 'IP', 'ME'],
            'currency': ['EUR', 'EUR', 'EUR', 'EUR']
        })

        result = build_group_structure(entities_df)

        # Vérifier is_consolidated
        assert result[result['entity_id'] == 'SUB_IG']['is_consolidated'].iloc[0]
        assert result[result['entity_id'] == 'SUB_IP']['is_consolidated'].iloc[0]
        assert not result[result['entity_id'] == 'SUB_ME']['is_consolidated'].iloc[0]


class TestConsolidateStatements:
    """Tests pour consolidate_statements."""

    def test_consolidation_minimal(self):
        """Test: Consolidation minimale avec 2 entités."""
        entities_df = pd.DataFrame({
            'entity_id': ['PARENT', 'SUB1'],
            'parent_id': [None, 'PARENT'],
            'ownership_pct': [100.0, 80.0],
            'method': ['IG', 'IG'],
            'currency': ['EUR', 'EUR']
        })

        trial_balance_df = pd.DataFrame({
            'entity_id': ['PARENT', 'PARENT', 'SUB1', 'SUB1'],
            'account': ['70100', '60100', '70100', '60100'],
            'amount': [1000.0, -500.0, 500.0, -200.0],
            'currency': ['EUR', 'EUR', 'EUR', 'EUR'],
            'period': ['2024-12', '2024-12', '2024-12', '2024-12']
        })

        result = consolidate_statements(
            entities_df,
            trial_balance_df,
            fx_rates_df=None,
            target_currency='EUR'
        )

        assert not result.empty
        assert len(result) == 4
        assert 'amount_consolidated' in result.columns
        assert 'minority_share' in result.columns
        assert 'is_eliminated' in result.columns

        # Vérifier les colonnes attendues
        required_cols = ['entity_id', 'account', 'amount', 'currency', 'period',
                        'level', 'method', 'is_eliminated', 'minority_share']
        for col in required_cols:
            assert col in result.columns, f"Colonne manquante: {col}"

    def test_consolidation_with_ip(self):
        """Test: Consolidation avec intégration proportionnelle."""
        entities_df = pd.DataFrame({
            'entity_id': ['PARENT', 'SUB_IP'],
            'parent_id': [None, 'PARENT'],
            'ownership_pct': [100.0, 40.0],
            'method': ['IG', 'IP'],
            'currency': ['EUR', 'EUR']
        })

        trial_balance_df = pd.DataFrame({
            'entity_id': ['SUB_IP'],
            'account': ['70100'],
            'amount': [1000.0],
            'currency': ['EUR'],
            'period': ['2024-12']
        })

        result = consolidate_statements(
            entities_df,
            trial_balance_df,
            fx_rates_df=None,
            target_currency='EUR'
        )

        # Vérifier que l'intégration proportionnelle est appliquée (40%)
        sub_row = result[result['entity_id'] == 'SUB_IP'].iloc[0]
        assert abs(sub_row['amount_consolidated'] - 400.0) < 0.01

    def test_consolidation_with_fx(self):
        """Test: Consolidation avec conversion devise."""
        entities_df = pd.DataFrame({
            'entity_id': ['PARENT', 'SUB_USD'],
            'parent_id': [None, 'PARENT'],
            'ownership_pct': [100.0, 100.0],
            'method': ['IG', 'IG'],
            'currency': ['EUR', 'USD']
        })

        trial_balance_df = pd.DataFrame({
            'entity_id': ['PARENT', 'SUB_USD'],
            'account': ['70100', '70100'],
            'amount': [1000.0, 1000.0],
            'currency': ['EUR', 'USD'],
            'period': ['2024-12', '2024-12']
        })

        fx_rates_df = pd.DataFrame({
            'from_ccy': ['USD'],
            'to_ccy': ['EUR'],
            'rate': [0.9],
            'period': ['2024-12']
        })

        result = consolidate_statements(
            entities_df,
            trial_balance_df,
            fx_rates_df=fx_rates_df,
            target_currency='EUR'
        )

        # Vérifier la conversion USD -> EUR
        sub_row = result[result['entity_id'] == 'SUB_USD'].iloc[0]
        assert abs(sub_row['amount_consolidated'] - 900.0) < 0.01

    def test_minority_interest_calculation(self):
        """Test: Calcul des intérêts minoritaires."""
        entities_df = pd.DataFrame({
            'entity_id': ['PARENT', 'SUB1'],
            'parent_id': [None, 'PARENT'],
            'ownership_pct': [100.0, 70.0],  # 30% minoritaires
            'method': ['IG', 'IG'],
            'currency': ['EUR', 'EUR']
        })

        trial_balance_df = pd.DataFrame({
            'entity_id': ['SUB1'],
            'account': ['70100'],
            'amount': [1000.0],
            'currency': ['EUR'],
            'period': ['2024-12']
        })

        result = consolidate_statements(
            entities_df,
            trial_balance_df,
            fx_rates_df=None,
            target_currency='EUR'
        )

        # Vérifier les intérêts minoritaires (30% de 1000)
        sub_row = result[result['entity_id'] == 'SUB1'].iloc[0]
        assert abs(sub_row['minority_share'] - 300.0) < 0.01


class TestPerformIntercompanyEliminations:
    """Tests pour perform_intercompany_eliminations."""

    def test_eliminations_basic(self):
        """Test: Éliminations intra-groupe basiques."""
        conso_df = pd.DataFrame({
            'entity_id': ['PARENT', 'SUB1', 'PARENT', 'SUB1'],
            'account': ['70100', '60100', '41100', '40100'],  # Ventes, Achats, Clients, Fournisseurs
            'amount_consolidated': [1000.0, -500.0, 200.0, -200.0],
            'currency': ['EUR', 'EUR', 'EUR', 'EUR'],
            'period': ['2024-12', '2024-12', '2024-12', '2024-12'],
            'level': [0, 1, 0, 1],
            'method': ['IG', 'IG', 'IG', 'IG'],
            'is_eliminated': [False, False, False, False],
            'minority_share': [0.0, 0.0, 0.0, 0.0]
        })

        result = perform_intercompany_eliminations(conso_df)

        # Vérifier que les comptes intra-groupe sont marqués comme éliminés
        assert result[result['account'] == '70100']['is_eliminated'].iloc[0]
        assert result[result['account'] == '60100']['is_eliminated'].iloc[0]
        assert result[result['account'] == '41100']['is_eliminated'].iloc[0]
        assert result[result['account'] == '40100']['is_eliminated'].iloc[0]

        # Vérifier que les montants sont mis à 0
        assert result[result['account'] == '70100']['amount_consolidated'].iloc[0] == 0.0


class TestComputeMinorityInterest:
    """Tests pour compute_minority_interest."""

    def test_minority_interest_aggregation(self):
        """Test: Agrégation des intérêts minoritaires."""
        conso_df = pd.DataFrame({
            'entity_id': ['SUB1', 'SUB1', 'SUB2'],
            'minority_share': [100.0, 50.0, 200.0]
        })

        result = compute_minority_interest(conso_df)

        assert not result.empty
        assert 'total_minority_interest' in result.columns

        # Vérifier l'agrégation
        sub1_row = result[result['entity_id'] == 'SUB1'].iloc[0]
        assert abs(sub1_row['total_minority_interest'] - 150.0) < 0.01

        sub2_row = result[result['entity_id'] == 'SUB2'].iloc[0]
        assert abs(sub2_row['total_minority_interest'] - 200.0) < 0.01


class TestTypesAndColumns:
    """Tests pour les types et colonnes."""

    def test_consolidation_types(self):
        """Test: Vérifier les types de données optimisés."""
        entities_df = pd.DataFrame({
            'entity_id': ['PARENT', 'SUB1'],
            'parent_id': [None, 'PARENT'],
            'ownership_pct': [100.0, 80.0],
            'method': ['IG', 'IG'],
            'currency': ['EUR', 'EUR']
        })

        trial_balance_df = pd.DataFrame({
            'entity_id': ['PARENT'],
            'account': ['70100'],
            'amount': [1000.0],
            'currency': ['EUR'],
            'period': ['2024-12']
        })

        result = consolidate_statements(
            entities_df,
            trial_balance_df,
            fx_rates_df=None,
            target_currency='EUR'
        )

        # Vérifier les types optimisés
        assert result['amount_consolidated'].dtype == np.float32
        assert result['minority_share'].dtype == np.float32
        assert result['account'].dtype.name == 'category'
        assert result['period'].dtype.name == 'category'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

