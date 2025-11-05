"""
Tests d'orchestration E2E pour les services.

Ces tests valident l'orchestration complète des services
et la compatibilité avec les adaptateurs legacy.
"""

import pandas as pd
import pytest

from app.adapters.legacy_compat import (
    calculate_liquidity_advanced,
    calculate_rwa_advanced,
    compute_capital_ratios,
    create_excel_export_advanced,
    generate_positions_advanced,
)
from src.services import (
    compute_capital,
    compute_liquidity,
    compute_rwa,
    consolidate_and_reconcile,
    create_excel_export,
    run_simulation,
)


class TestSimulationService:
    """Tests pour simulation_service."""

    def test_run_simulation_minimal(self):
        """Test: Simulation minimale."""
        positions_df, _ = run_simulation(num_positions=100, seed=42)

        assert not positions_df.empty
        assert len(positions_df) == 100

        # Vérifier les colonnes minimales
        required_cols = ['position_id', 'entity_id', 'product_id', 'exposure_class',
                        'currency', 'ead', 'pd', 'lgd', 'maturity', 'stage', 'ecl_provision']
        for col in required_cols:
            assert col in positions_df.columns, f"Colonne manquante: {col}"

    def test_run_simulation_reproducible(self):
        """Test: Reproductibilité avec seed."""
        pos1, _ = run_simulation(num_positions=50, seed=123)
        pos2, _ = run_simulation(num_positions=50, seed=123)

        # Vérifier que les résultats sont identiques
        pd.testing.assert_frame_equal(pos1, pos2)

    def test_run_simulation_invalid_params(self):
        """Test: Validation des paramètres."""
        with pytest.raises(ValueError, match="num_positions doit être > 0"):
            run_simulation(num_positions=0, seed=42)

        with pytest.raises(ValueError, match="seed doit être >= 0"):
            run_simulation(num_positions=100, seed=-1)


class TestRiskService:
    """Tests pour risk_service."""

    def test_compute_rwa_minimal(self):
        """Test: Calcul RWA minimal."""
        # Générer des positions
        positions_df, _ = run_simulation(num_positions=100, seed=42)

        # Calculer RWA
        rwa_df, _ = compute_rwa(positions_df)

        assert not rwa_df.empty
        assert len(rwa_df) == 100

        # Vérifier les colonnes minimales
        required_cols = ['position_id', 'rwa_amount', 'rwa_density', 'approach']
        for col in required_cols:
            assert col in rwa_df.columns, f"Colonne manquante: {col}"

    def test_compute_rwa_invalid_input(self):
        """Test: Validation entrée invalide."""
        with pytest.raises(ValueError, match="ne peut pas être vide"):
            compute_rwa(pd.DataFrame())

        with pytest.raises(ValueError, match="Colonnes manquantes"):
            compute_rwa(pd.DataFrame({'foo': [1, 2, 3]}))

    def test_compute_liquidity_minimal(self):
        """Test: Calcul liquidité minimal."""
        positions_df, _ = run_simulation(num_positions=100, seed=42)

        lcr_df, nsfr_df, almm_obj, _ = compute_liquidity(positions_df)

        assert not lcr_df.empty
        assert not nsfr_df.empty
        assert almm_obj is not None

        # Vérifier les colonnes LCR
        assert 'entity_id' in lcr_df.columns
        assert 'lcr' in lcr_df.columns  # Colonne 'lcr' et non 'lcr_ratio'

        # Vérifier les colonnes NSFR
        assert 'entity_id' in nsfr_df.columns
        assert 'nsfr' in nsfr_df.columns  # Colonne 'nsfr' et non 'nsfr_ratio'

    def test_compute_capital_minimal(self):
        """Test: Calcul capital minimal."""
        positions_df, _ = run_simulation(num_positions=100, seed=42)
        rwa_df, _ = compute_rwa(positions_df)

        own_funds = {
            'cet1': 1_000_000,
            'tier1': 1_200_000,
            'total': 1_500_000,
            'leverage_exposure': 10_000_000
        }

        capital_ratios, _ = compute_capital(rwa_df, own_funds)

        assert isinstance(capital_ratios, dict)

        # Vérifier les clés minimales
        required_keys = ['cet1_ratio', 'tier1_ratio', 'total_capital_ratio', 'leverage_ratio']
        for key in required_keys:
            assert key in capital_ratios, f"Clé manquante: {key}"

        # Vérifier les bornes raisonnables (0-100%)
        for key in required_keys:
            assert 0 <= capital_ratios[key] <= 100, f"{key} hors bornes: {capital_ratios[key]}"

    def test_compute_capital_with_dataframe(self):
        """Test: Calcul capital avec DataFrame own_funds."""
        positions_df, _ = run_simulation(num_positions=100, seed=42)
        rwa_df, _ = compute_rwa(positions_df)

        own_funds_df = pd.DataFrame({
            'entity_id': ['E1', 'E2'],
            'cet1': [500_000, 500_000],
            'tier1': [600_000, 600_000],
            'total': [750_000, 750_000]
        })

        capital_ratios, _ = compute_capital(rwa_df, own_funds_df)

        assert isinstance(capital_ratios, dict)
        assert 'cet1_ratio' in capital_ratios


class TestReportingService:
    """Tests pour reporting_service."""

    def test_create_excel_export_minimal(self):
        """Test: Export Excel minimal."""
        # Générer les données
        positions_df, _ = run_simulation(num_positions=100, seed=42)
        rwa_df, _ = compute_rwa(positions_df)
        lcr_df, nsfr_df, almm_obj, _ = compute_liquidity(positions_df)

        own_funds = {
            'cet1': 1_000_000,
            'tier1': 1_200_000,
            'total': 1_500_000,
            'leverage_exposure': 10_000_000
        }
        capital_ratios, _ = compute_capital(rwa_df, own_funds)

        # Créer l'export
        excel_bytes, _ = create_excel_export(
            positions_df=positions_df,
            rwa_df=rwa_df,
            lcr_df=lcr_df,
            nsfr_df=nsfr_df,
            capital_ratios=capital_ratios
        )

        assert isinstance(excel_bytes, bytes)
        assert len(excel_bytes) > 10_000  # Au moins 10 KB

    def test_create_excel_export_invalid_input(self):
        """Test: Validation entrée invalide."""
        with pytest.raises(ValueError, match="ne peut pas être vide"):
            create_excel_export(
                positions_df=pd.DataFrame(),
                rwa_df=pd.DataFrame(),
                lcr_df=pd.DataFrame(),
                nsfr_df=pd.DataFrame(),
                capital_ratios={}
            )


class TestConsolidationService:
    """Tests pour consolidation_service."""

    def test_consolidate_and_reconcile_minimal(self):
        """Test: Consolidation et réconciliation minimales."""
        entities_df = pd.DataFrame({
            'entity_id': ['PARENT', 'SUB1'],
            'parent_id': [None, 'PARENT'],
            'ownership_pct': [100.0, 80.0],
            'method': ['IG', 'IG'],
            'currency': ['EUR', 'EUR']
        })

        trial_balance_df = pd.DataFrame({
            'entity_id': ['PARENT', 'SUB1'],
            'account': ['70100', '70100'],
            'amount': [1000.0, 500.0],
            'currency': ['EUR', 'EUR'],
            'period': ['2024-12', '2024-12']
        })

        consolidated_df, variances_df = consolidate_and_reconcile(
            entities_df=entities_df,
            trial_balance_df=trial_balance_df
        )

        assert not consolidated_df.empty
        assert not variances_df.empty

        # Vérifier les colonnes consolidation
        assert 'amount_consolidated' in consolidated_df.columns
        assert 'is_eliminated' in consolidated_df.columns

        # Vérifier les colonnes réconciliation
        assert 'severity' in variances_df.columns
        assert 'root_cause_hint' in variances_df.columns

    def test_consolidate_and_reconcile_with_thresholds(self):
        """Test: Consolidation avec seuils personnalisés."""
        entities_df = pd.DataFrame({
            'entity_id': ['PARENT'],
            'parent_id': [None],
            'ownership_pct': [100.0],
            'method': ['IG'],
            'currency': ['EUR']
        })

        trial_balance_df = pd.DataFrame({
            'entity_id': ['PARENT'],
            'account': ['70100'],
            'amount': [1000.0],
            'currency': ['EUR'],
            'period': ['2024-12']
        })

        thresholds = {'minor': 0.03, 'critical': 0.08}

        consolidated_df, variances_df = consolidate_and_reconcile(
            entities_df=entities_df,
            trial_balance_df=trial_balance_df,
            thresholds=thresholds
        )

        assert not consolidated_df.empty
        assert not variances_df.empty


class TestE2EOrchestration:
    """Tests E2E complets."""

    def test_full_pipeline_e2e(self):
        """Test: Pipeline complet Simulation → RWA → Liquidité → Capital → Export."""
        # Étape 1: Simulation
        positions_df, _ = run_simulation(num_positions=800, seed=42)
        assert len(positions_df) == 800

        # Étape 2: RWA
        rwa_df, _ = compute_rwa(positions_df)
        assert len(rwa_df) == 800

        # Étape 3: Liquidité
        lcr_df, nsfr_df, almm_obj, _ = compute_liquidity(positions_df)
        assert not lcr_df.empty
        assert not nsfr_df.empty

        # Étape 4: Capital
        own_funds = {
            'cet1': 1_000_000,
            'tier1': 1_200_000,
            'total': 1_500_000,
            'leverage_exposure': 10_000_000
        }
        capital_ratios, _ = compute_capital(rwa_df, own_funds)
        assert len(capital_ratios) >= 4

        # Étape 5: Export
        excel_bytes, _ = create_excel_export(
            positions_df=positions_df,
            rwa_df=rwa_df,
            lcr_df=lcr_df,
            nsfr_df=nsfr_df,
            capital_ratios=capital_ratios
        )
        assert len(excel_bytes) > 10_000


class TestLegacyAdapters:
    """Tests pour les adaptateurs legacy."""

    def test_legacy_generate_positions(self):
        """Test: Adaptateur generate_positions_advanced."""
        positions_df = generate_positions_advanced(num_positions=50, seed=123)

        assert not positions_df.empty
        assert len(positions_df) == 50

    def test_legacy_calculate_rwa(self):
        """Test: Adaptateur calculate_rwa_advanced."""
        positions_df = generate_positions_advanced(num_positions=50, seed=123)
        rwa_df = calculate_rwa_advanced(positions_df)

        assert not rwa_df.empty
        assert len(rwa_df) == 50

    def test_legacy_calculate_liquidity(self):
        """Test: Adaptateur calculate_liquidity_advanced."""
        positions_df = generate_positions_advanced(num_positions=50, seed=123)
        lcr_df, nsfr_df, almm_obj = calculate_liquidity_advanced(positions_df)

        assert not lcr_df.empty
        assert not nsfr_df.empty

    def test_legacy_compute_capital(self):
        """Test: Adaptateur compute_capital_ratios."""
        positions_df = generate_positions_advanced(num_positions=50, seed=123)
        rwa_df = calculate_rwa_advanced(positions_df)

        own_funds = {
            'cet1': 1_000_000,
            'tier1': 1_200_000,
            'total': 1_500_000,
            'leverage_exposure': 10_000_000
        }
        capital_ratios = compute_capital_ratios(rwa_df, own_funds)

        assert isinstance(capital_ratios, dict)
        assert 'cet1_ratio' in capital_ratios

    def test_legacy_create_excel_export(self):
        """Test: Adaptateur create_excel_export_advanced."""
        positions_df = generate_positions_advanced(num_positions=50, seed=123)
        rwa_df = calculate_rwa_advanced(positions_df)
        lcr_df, nsfr_df, almm_obj = calculate_liquidity_advanced(positions_df)

        own_funds = {
            'cet1': 1_000_000,
            'tier1': 1_200_000,
            'total': 1_500_000,
            'leverage_exposure': 10_000_000
        }
        capital_ratios = compute_capital_ratios(rwa_df, own_funds)

        excel_bytes = create_excel_export_advanced(
            positions_df=positions_df,
            rwa_df=rwa_df,
            lcr_df=lcr_df,
            nsfr_df=nsfr_df,
            capital_ratios=capital_ratios
        )

        assert isinstance(excel_bytes, bytes)
        assert len(excel_bytes) > 10_000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

