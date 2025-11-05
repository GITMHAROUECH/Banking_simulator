"""
Tests unitaires pour le module de réconciliation compta-risque.
"""

import numpy as np
import pandas as pd
import pytest

from src.domain.consolidation.reconciliation import (
    aggregate_variances_by_entity,
    classify_variances,
    export_variances_summary,
    reconcile_ledger_vs_risk,
)


class TestReconcileLedgerVsRisk:
    """Tests pour reconcile_ledger_vs_risk."""

    def test_reco_minimal(self):
        """Test: Réconciliation minimale avec écarts."""
        ledger_df = pd.DataFrame({
            'entity_id': ['E1', 'E2'],
            'account': ['70100', '70100'],
            'amount': [1000.0, 500.0],
            'period': ['2024-12', '2024-12']
        })

        risk_df = pd.DataFrame({
            'entity_id': ['E1', 'E2'],
            'risk_bucket': ['Credit', 'Credit'],
            'amount': [950.0, 500.0],
            'period': ['2024-12', '2024-12']
        })

        thresholds = {'minor': 0.05, 'critical': 0.10}

        result = reconcile_ledger_vs_risk(ledger_df, risk_df, thresholds)

        assert not result.empty
        assert len(result) == 2

        # Vérifier les colonnes attendues
        required_cols = ['key', 'ledger_amount', 'risk_amount', 'delta_abs',
                        'delta_pct', 'severity', 'root_cause_hint']
        for col in required_cols:
            assert col in result.columns, f"Colonne manquante: {col}"

        # Vérifier les calculs
        e1_row = result[result['entity_id'] == 'E1'].iloc[0]
        assert abs(e1_row['ledger_amount'] - 1000.0) < 0.01
        assert abs(e1_row['risk_amount'] - 950.0) < 0.01
        assert abs(e1_row['delta_abs'] - 50.0) < 0.01
        assert abs(e1_row['delta_pct'] - 5.26) < 0.1  # 50/950 * 100

    def test_reco_with_missing_data(self):
        """Test: Réconciliation avec données manquantes."""
        ledger_df = pd.DataFrame({
            'entity_id': ['E1'],
            'account': ['70100'],
            'amount': [1000.0],
            'period': ['2024-12']
        })

        risk_df = pd.DataFrame({
            'entity_id': ['E2'],
            'risk_bucket': ['Credit'],
            'amount': [500.0],
            'period': ['2024-12']
        })

        thresholds = {'minor': 0.05, 'critical': 0.10}

        result = reconcile_ledger_vs_risk(ledger_df, risk_df, thresholds)

        # Vérifier que les deux entités sont présentes
        assert len(result) == 2

        # E1 : ledger présent, risk manquant
        e1_row = result[result['entity_id'] == 'E1'].iloc[0]
        assert abs(e1_row['ledger_amount'] - 1000.0) < 0.01
        assert abs(e1_row['risk_amount'] - 0.0) < 0.01
        assert e1_row['root_cause_hint'] == 'Missing risk data'

        # E2 : risk présent, ledger manquant
        e2_row = result[result['entity_id'] == 'E2'].iloc[0]
        assert abs(e2_row['ledger_amount'] - 0.0) < 0.01
        assert abs(e2_row['risk_amount'] - 500.0) < 0.01
        assert e2_row['root_cause_hint'] == 'Missing ledger data'

    def test_reco_severity_classification(self):
        """Test: Classification des sévérités."""
        ledger_df = pd.DataFrame({
            'entity_id': ['E1', 'E2', 'E3'],
            'account': ['70100', '70100', '70100'],
            'amount': [1000.0, 1000.0, 1000.0],
            'period': ['2024-12', '2024-12', '2024-12']
        })

        risk_df = pd.DataFrame({
            'entity_id': ['E1', 'E2', 'E3'],
            'risk_bucket': ['Credit', 'Credit', 'Credit'],
            'amount': [990.0, 950.0, 800.0],  # Écarts: 1%, 5%, 20%
            'period': ['2024-12', '2024-12', '2024-12']
        })

        thresholds = {'minor': 0.05, 'critical': 0.10}

        result = reconcile_ledger_vs_risk(ledger_df, risk_df, thresholds)

        # E1 : écart 1% → OK
        e1_row = result[result['entity_id'] == 'E1'].iloc[0]
        assert e1_row['severity'] == 'OK'

        # E2 : écart 5% → Minor
        e2_row = result[result['entity_id'] == 'E2'].iloc[0]
        assert e2_row['severity'] == 'Minor'

        # E3 : écart 20% → Critical
        e3_row = result[result['entity_id'] == 'E3'].iloc[0]
        assert e3_row['severity'] == 'Critical'


class TestClassifyVariances:
    """Tests pour classify_variances."""

    def test_thresholds_logic(self):
        """Test: Logique des seuils."""
        variances_df = pd.DataFrame({
            'entity_id': ['E1', 'E2', 'E3', 'E4'],
            'period': ['2024-12'] * 4,
            'delta_pct': [1.0, 5.0, 10.0, 20.0]
        })

        thresholds = {'minor': 0.05, 'critical': 0.10}

        result = classify_variances(variances_df, thresholds)

        assert result.iloc[0]['severity'] == 'OK'      # 1% < 5%
        assert result.iloc[1]['severity'] == 'Minor'   # 5% >= 5%
        assert result.iloc[2]['severity'] == 'Critical' # 10% >= 10%
        assert result.iloc[3]['severity'] == 'Critical' # 20% >= 10%

    def test_thresholds_variation(self):
        """Test: Variation des seuils change la classification."""
        variances_df = pd.DataFrame({
            'entity_id': ['E1'],
            'period': ['2024-12'],
            'delta_pct': [7.0]
        })

        # Seuils stricts
        thresholds_strict = {'minor': 0.03, 'critical': 0.06}
        result_strict = classify_variances(variances_df, thresholds_strict)
        assert result_strict.iloc[0]['severity'] == 'Critical'

        # Seuils larges
        thresholds_loose = {'minor': 0.10, 'critical': 0.20}
        result_loose = classify_variances(variances_df, thresholds_loose)
        assert result_loose.iloc[0]['severity'] == 'OK'


class TestRootCauseHints:
    """Tests pour les hints de cause racine."""

    def test_root_cause_hints(self):
        """Test: Hints renvoyés sur cas typiques."""
        ledger_df = pd.DataFrame({
            'entity_id': ['E1', 'E2', 'E3', 'E4'],
            'account': ['70100'] * 4,
            'amount': [1000.0, 0.0, 1000.0, 1000.0],
            'period': ['2024-12'] * 4
        })

        risk_df = pd.DataFrame({
            'entity_id': ['E1', 'E2', 'E3', 'E4'],
            'risk_bucket': ['Credit'] * 4,
            'amount': [990.0, 500.0, 950.0, 700.0],  # Écarts: 1%, 100%, 5%, 30%
            'period': ['2024-12'] * 4
        })

        thresholds = {'minor': 0.05, 'critical': 0.10}

        result = reconcile_ledger_vs_risk(ledger_df, risk_df, thresholds)

        # E1 : écart faible → rounding
        e1_row = result[result['entity_id'] == 'E1'].iloc[0]
        assert 'Rounding' in e1_row['root_cause_hint']

        # E2 : ledger manquant
        e2_row = result[result['entity_id'] == 'E2'].iloc[0]
        assert 'Missing ledger' in e2_row['root_cause_hint']

        # E3 : écart moyen → timing/mapping
        e3_row = result[result['entity_id'] == 'E3'].iloc[0]
        assert 'Timing' in e3_row['root_cause_hint'] or 'mapping' in e3_row['root_cause_hint']

        # E4 : écart important → investigation
        e4_row = result[result['entity_id'] == 'E4'].iloc[0]
        assert 'investigation' in e4_row['root_cause_hint']


class TestAggregateVariances:
    """Tests pour aggregate_variances_by_entity."""

    def test_aggregation_by_entity(self):
        """Test: Agrégation des écarts par entité."""
        variances_df = pd.DataFrame({
            'entity_id': ['E1', 'E1', 'E2'],
            'period': ['2024-11', '2024-12', '2024-12'],
            'ledger_amount': [1000.0, 500.0, 800.0],
            'risk_amount': [950.0, 480.0, 800.0],
            'delta_abs': [50.0, 20.0, 0.0]
        })

        result = aggregate_variances_by_entity(variances_df)

        assert len(result) == 2

        # E1 : somme de 2 périodes
        e1_row = result[result['entity_id'] == 'E1'].iloc[0]
        assert abs(e1_row['ledger_amount'] - 1500.0) < 0.01
        assert abs(e1_row['risk_amount'] - 1430.0) < 0.01
        assert abs(e1_row['delta_abs'] - 70.0) < 0.01


class TestExportVariancesSummary:
    """Tests pour export_variances_summary."""

    def test_summary_export(self):
        """Test: Export du résumé des écarts."""
        variances_df = pd.DataFrame({
            'entity_id': ['E1', 'E2', 'E3', 'E4'],
            'severity': ['OK', 'OK', 'Minor', 'Critical']
        })

        result = export_variances_summary(variances_df)

        assert isinstance(result, dict)
        assert result['OK'] == 2
        assert result['Minor'] == 1
        assert result['Critical'] == 1


class TestTypesAndColumns:
    """Tests pour les types et colonnes."""

    def test_types_and_columns(self):
        """Test: Vérifier les types de données optimisés."""
        ledger_df = pd.DataFrame({
            'entity_id': ['E1'],
            'account': ['70100'],
            'amount': [1000.0],
            'period': ['2024-12']
        })

        risk_df = pd.DataFrame({
            'entity_id': ['E1'],
            'risk_bucket': ['Credit'],
            'amount': [950.0],
            'period': ['2024-12']
        })

        thresholds = {'minor': 0.05, 'critical': 0.10}

        result = reconcile_ledger_vs_risk(ledger_df, risk_df, thresholds)

        # Vérifier les types optimisés
        assert result['ledger_amount'].dtype == np.float32
        assert result['risk_amount'].dtype == np.float32
        assert result['delta_abs'].dtype == np.float32
        assert result['delta_pct'].dtype == np.float32
        assert result['entity_id'].dtype.name == 'category'
        assert result['period'].dtype.name == 'category'
        assert result['severity'].dtype.name == 'category'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

