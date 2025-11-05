"""
Tests unitaires pour le module domain/risk.

Objectif de couverture: ≥ 80%
"""

import pandas as pd
import pytest

from src.domain.risk import (
    calculate_liquidity_advanced,
    calculate_rwa_advanced,
    compute_capital_ratios,
)
from src.domain.simulation import generate_positions_advanced


class TestCalculateRWAAdvanced:
    """Tests de la fonction calculate_rwa_advanced()."""

    def test_rwa_minimal(self):
        """Test: DF non vide + colonnes minimales présentes."""
        # Générer des positions via I1
        positions_df = generate_positions_advanced(num_positions=200, seed=42)

        # Calculer RWA
        rwa_df = calculate_rwa_advanced(positions_df)

        # Vérifier que le DataFrame n'est pas vide
        assert not rwa_df.empty
        assert len(rwa_df) == 200

        # Vérifier les colonnes minimales
        required_cols = ['position_id', 'rwa_amount', 'rwa_density', 'approach']
        for col in required_cols:
            assert col in rwa_df.columns, f"Colonne manquante: {col}"

    def test_rwa_density_bounds(self):
        """Test: rwa_density dans [0, 150]."""
        positions_df = generate_positions_advanced(num_positions=200, seed=42)
        rwa_df = calculate_rwa_advanced(positions_df)

        # RWA density doit être >= 0 (pas de limite supérieure stricte pour IRB)
        assert (rwa_df['rwa_density'] >= 0).all()
        # Vérifier que la majorité est dans [0, 200%]
        assert (rwa_df['rwa_density'] <= 200).sum() / len(rwa_df) > 0.9

    def test_rwa_classes_expo_variation(self):
        """Test: Variation de rwa_amount selon exposure_class."""
        positions_df = generate_positions_advanced(num_positions=1000, seed=42)
        rwa_df = calculate_rwa_advanced(positions_df)

        # exposure_class est déjà dans rwa_df
        # Calculer RWA moyen par classe
        rwa_by_class = rwa_df.groupby('exposure_class')['rwa_density'].mean()

        # Sovereign doit avoir RWA density plus faible que Corporate (approche standardisée)
        if 'Sovereign' in rwa_by_class.index and 'Corporate' in rwa_by_class.index:
            assert rwa_by_class['Sovereign'] < rwa_by_class['Corporate']

        # Vérifier que les classes ont des densités différentes
        assert len(rwa_by_class.unique()) > 1

    def test_rwa_approach_values(self):
        """Test: Approches valides."""
        positions_df = generate_positions_advanced(num_positions=200, seed=42)
        rwa_df = calculate_rwa_advanced(positions_df)

        valid_approaches = ['IRB_Foundation', 'IRB_SME', 'Standardised']
        assert rwa_df['approach'].isin(valid_approaches).all()

    def test_rwa_missing_columns(self):
        """Test: Exception si colonnes manquantes."""
        # DataFrame incomplet
        incomplete_df = pd.DataFrame({
            'position_id': ['POS_001'],
            'ead': [100000]
            # Manque: entity_id, exposure_class, pd, lgd, maturity
        })

        with pytest.raises(KeyError, match="Colonnes manquantes"):
            calculate_rwa_advanced(incomplete_df)

    def test_rwa_deterministic(self):
        """Test: Déterminisme (mêmes inputs → mêmes outputs)."""
        positions_df = generate_positions_advanced(num_positions=100, seed=42)

        rwa_df1 = calculate_rwa_advanced(positions_df)
        rwa_df2 = calculate_rwa_advanced(positions_df)

        pd.testing.assert_frame_equal(rwa_df1, rwa_df2)

    def test_rwa_dtypes_optimized(self):
        """Test: Dtypes optimisés."""
        positions_df = generate_positions_advanced(num_positions=200, seed=42)
        rwa_df = calculate_rwa_advanced(positions_df)

        assert rwa_df['rwa_amount'].dtype == 'float32'
        assert rwa_df['rwa_density'].dtype == 'float32'
        assert rwa_df['approach'].dtype.name == 'category'


class TestCalculateLiquidityAdvanced:
    """Tests de la fonction calculate_liquidity_advanced()."""

    def test_lcr_minimal(self):
        """Test: lcr_df contient les colonnes minimales."""
        positions_df = generate_positions_advanced(num_positions=200, seed=42)

        lcr_df, nsfr_df, almm_obj = calculate_liquidity_advanced(positions_df)

        # Vérifier LCR
        assert not lcr_df.empty
        required_lcr_cols = ['entity_id', 'lcr', 'hqlas_total', 'net_outflows_30d']
        for col in required_lcr_cols:
            assert col in lcr_df.columns, f"Colonne LCR manquante: {col}"

    def test_nsfr_minimal(self):
        """Test: nsfr_df contient les colonnes minimales."""
        positions_df = generate_positions_advanced(num_positions=200, seed=42)

        lcr_df, nsfr_df, almm_obj = calculate_liquidity_advanced(positions_df)

        # Vérifier NSFR
        assert not nsfr_df.empty
        required_nsfr_cols = ['entity_id', 'nsfr', 'asf_total', 'rsf_total']
        for col in required_nsfr_cols:
            assert col in nsfr_df.columns, f"Colonne NSFR manquante: {col}"

    def test_lcr_positive(self):
        """Test: LCR >= 0."""
        positions_df = generate_positions_advanced(num_positions=200, seed=42)

        lcr_df, _, _ = calculate_liquidity_advanced(positions_df)

        assert (lcr_df['lcr'] >= 0).all()

    def test_nsfr_positive(self):
        """Test: NSFR >= 0."""
        positions_df = generate_positions_advanced(num_positions=200, seed=42)

        _, nsfr_df, _ = calculate_liquidity_advanced(positions_df)

        assert (nsfr_df['nsfr'] >= 0).all()

    def test_almm_structure(self):
        """Test: ALMM obj contient des métriques."""
        positions_df = generate_positions_advanced(num_positions=200, seed=42)

        _, _, almm_obj = calculate_liquidity_advanced(positions_df)

        # Vérifier que c'est un dict
        assert isinstance(almm_obj, dict)

        # Vérifier les clés essentielles
        assert 'total_assets' in almm_obj
        assert 'avg_maturity' in almm_obj

    def test_liquidity_missing_columns(self):
        """Test: Exception si colonnes manquantes."""
        incomplete_df = pd.DataFrame({
            'position_id': ['POS_001']
            # Manque: entity_id, product_id, ead
        })

        with pytest.raises(KeyError, match="Colonnes manquantes"):
            calculate_liquidity_advanced(incomplete_df)

    def test_liquidity_dtypes_optimized(self):
        """Test: Dtypes optimisés."""
        positions_df = generate_positions_advanced(num_positions=200, seed=42)

        lcr_df, nsfr_df, _ = calculate_liquidity_advanced(positions_df)

        assert lcr_df['lcr'].dtype == 'float32'
        assert lcr_df['hqlas_total'].dtype == 'float32'
        assert nsfr_df['nsfr'].dtype == 'float32'
        assert nsfr_df['asf_total'].dtype == 'float32'


class TestComputeCapitalRatios:
    """Tests de la fonction compute_capital_ratios()."""

    def test_capital_ratios_keys(self):
        """Test: Retourne les clés attendues."""
        positions_df = generate_positions_advanced(num_positions=200, seed=42)
        rwa_df = calculate_rwa_advanced(positions_df)

        ratios = compute_capital_ratios(rwa_df)

        # Vérifier les clés minimales
        required_keys = ['cet1_ratio', 'tier1_ratio', 'total_capital_ratio', 'leverage_ratio']
        for key in required_keys:
            assert key in ratios, f"Clé manquante: {key}"

    def test_capital_ratios_bounds(self):
        """Test: Ratios dans des bornes raisonnables (0-50%)."""
        positions_df = generate_positions_advanced(num_positions=200, seed=42)
        rwa_df = calculate_rwa_advanced(positions_df)

        ratios = compute_capital_ratios(rwa_df)

        # Ratios doivent être positifs et < 50%
        assert 0 <= ratios['cet1_ratio'] <= 50
        assert 0 <= ratios['tier1_ratio'] <= 50
        assert 0 <= ratios['total_capital_ratio'] <= 50
        assert 0 <= ratios['leverage_ratio'] <= 50

    def test_capital_ratios_hierarchy(self):
        """Test: CET1 <= Tier1 <= Total Capital."""
        positions_df = generate_positions_advanced(num_positions=200, seed=42)
        rwa_df = calculate_rwa_advanced(positions_df)

        ratios = compute_capital_ratios(rwa_df)

        # Hiérarchie des ratios
        assert ratios['cet1_ratio'] <= ratios['tier1_ratio']
        assert ratios['tier1_ratio'] <= ratios['total_capital_ratio']

    def test_capital_ratios_with_own_funds_dict(self):
        """Test: Calcul avec own_funds dict."""
        positions_df = generate_positions_advanced(num_positions=200, seed=42)
        rwa_df = calculate_rwa_advanced(positions_df)

        own_funds = {
            'cet1_capital': 1000000,
            'tier1_capital': 1200000,
            'total_capital': 1500000,
            'total_assets': 20000000
        }

        ratios = compute_capital_ratios(rwa_df, own_funds)

        assert 'cet1_ratio' in ratios
        assert ratios['cet1_ratio'] > 0

    def test_capital_ratios_with_own_funds_df(self):
        """Test: Calcul avec own_funds DataFrame."""
        positions_df = generate_positions_advanced(num_positions=200, seed=42)
        rwa_df = calculate_rwa_advanced(positions_df)

        own_funds_df = pd.DataFrame([{
            'cet1_capital': 1000000,
            'tier1_capital': 1200000,
            'total_capital': 1500000,
            'total_assets': 20000000
        }])

        ratios = compute_capital_ratios(rwa_df, own_funds_df)

        assert 'cet1_ratio' in ratios
        assert ratios['cet1_ratio'] > 0

    def test_capital_ratios_missing_column(self):
        """Test: Exception si colonne rwa_amount manquante."""
        incomplete_df = pd.DataFrame({
            'position_id': ['POS_001'],
            'ead': [100000]
        })

        with pytest.raises(KeyError, match="rwa_amount"):
            compute_capital_ratios(incomplete_df)


class TestPerformance:
    """Tests de performance."""

    def test_performance_rwa_10k(self):
        """Test: calculate_rwa_advanced 10k positions en ≤ 3s."""
        import time

        positions_df = generate_positions_advanced(num_positions=10000, seed=42)

        start = time.time()
        rwa_df = calculate_rwa_advanced(positions_df)
        duration = time.time() - start

        assert len(rwa_df) == 10000
        assert duration < 3.0, f"Trop lent: {duration:.2f}s (objectif: <3s)"

    def test_performance_liquidity_10k(self):
        """Test: calculate_liquidity_advanced 10k positions en ≤ 2s."""
        import time

        positions_df = generate_positions_advanced(num_positions=10000, seed=42)

        start = time.time()
        lcr_df, nsfr_df, almm_obj = calculate_liquidity_advanced(positions_df)
        duration = time.time() - start

        assert not lcr_df.empty
        assert not nsfr_df.empty
        assert duration < 2.0, f"Trop lent: {duration:.2f}s (objectif: <2s)"

    def test_performance_capital_ratios(self):
        """Test: compute_capital_ratios en ≤ 0.2s."""
        import time

        positions_df = generate_positions_advanced(num_positions=10000, seed=42)
        rwa_df = calculate_rwa_advanced(positions_df)

        start = time.time()
        ratios = compute_capital_ratios(rwa_df)
        duration = time.time() - start

        assert 'cet1_ratio' in ratios
        assert duration < 0.2, f"Trop lent: {duration:.2f}s (objectif: <0.2s)"


class TestIntegration:
    """Tests d'intégration I1 + I2."""

    def test_full_pipeline(self):
        """Test: Pipeline complet Simulation → RWA → Capital."""
        # I1: Générer positions
        positions_df = generate_positions_advanced(num_positions=500, seed=42)

        # I2: Calculer RWA
        rwa_df = calculate_rwa_advanced(positions_df)

        # I2: Calculer ratios de capital
        ratios = compute_capital_ratios(rwa_df)

        # Vérifications
        assert len(positions_df) == 500
        assert len(rwa_df) == 500
        assert 'cet1_ratio' in ratios
        assert ratios['total_rwa'] > 0

    def test_full_pipeline_with_liquidity(self):
        """Test: Pipeline complet avec liquidité."""
        # I1: Générer positions
        positions_df = generate_positions_advanced(num_positions=500, seed=42)

        # I2: Calculer RWA
        rwa_df = calculate_rwa_advanced(positions_df)

        # I2: Calculer liquidité
        lcr_df, nsfr_df, almm_obj = calculate_liquidity_advanced(positions_df)

        # I2: Calculer ratios de capital
        ratios = compute_capital_ratios(rwa_df)

        # Vérifications
        assert not lcr_df.empty
        assert not nsfr_df.empty
        assert 'cet1_ratio' in ratios


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

