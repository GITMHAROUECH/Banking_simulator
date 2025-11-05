"""
Tests unitaires pour le module de simulation Monte Carlo.

Objectif de couverture: ≥ 80%
"""

import hashlib

import pandas as pd
import pytest

from src.domain.simulation.monte_carlo import (
    DEFAULT_ENTITIES,
    DEFAULT_PRODUCTS,
    SimulationEngine,
    generate_positions_advanced,
)


class TestGeneratePositionsAdvanced:
    """Tests de la fonction publique generate_positions_advanced()."""

    def test_generate_positions_minimal(self):
        """Test: DataFrame non vide avec toutes les colonnes minimales."""
        df = generate_positions_advanced(num_positions=100, seed=42)

        # Vérifier que le DataFrame n'est pas vide
        assert not df.empty
        assert len(df) == 100

        # Vérifier les colonnes minimales obligatoires
        required_columns = [
            'position_id', 'entity_id', 'product_id', 'exposure_class',
            'currency', 'ead', 'pd', 'lgd', 'maturity', 'stage', 'ecl_provision'
        ]
        for col in required_columns:
            assert col in df.columns, f"Colonne manquante: {col}"

    def test_seed_reproducible(self):
        """Test: Seed identique garantit résultats identiques."""
        df1 = generate_positions_advanced(num_positions=100, seed=42)
        df2 = generate_positions_advanced(num_positions=100, seed=42)

        # Vérifier que les DataFrames sont identiques
        pd.testing.assert_frame_equal(df1, df2)

        # Vérifier avec hash pour plus de robustesse
        hash1 = hashlib.md5(pd.util.hash_pandas_object(df1).values).hexdigest()
        hash2 = hashlib.md5(pd.util.hash_pandas_object(df2).values).hexdigest()
        assert hash1 == hash2

    def test_seed_different_results(self):
        """Test: Seeds différents donnent résultats différents."""
        df1 = generate_positions_advanced(num_positions=100, seed=42)
        df2 = generate_positions_advanced(num_positions=100, seed=123)

        # Les DataFrames ne doivent pas être identiques
        with pytest.raises(AssertionError):
            pd.testing.assert_frame_equal(df1, df2)

    def test_facilities_columns_present_when_applicable(self):
        """Test: Colonnes CCF présentes pour facilities."""
        df = generate_positions_advanced(num_positions=1000, seed=42)

        # Vérifier que les colonnes CCF existent
        assert 'ccf' in df.columns
        assert 'commitment_amount' in df.columns
        assert 'drawn_amount' in df.columns

        # Vérifier que certaines positions ont CCF > 0 (facilities)
        facilities_mask = df['ccf'] > 0
        assert facilities_mask.sum() > 0, "Aucune facility détectée"

        # Pour les facilities, commitment_amount doit être > 0
        facilities_df = df[facilities_mask]
        assert (facilities_df['commitment_amount'] > 0).all()

    def test_config_stress_scenario_baseline(self):
        """Test: Scénario Baseline."""
        config = {'stress_scenario': 'Baseline'}
        df = generate_positions_advanced(num_positions=100, seed=42, config=config)

        assert not df.empty
        assert len(df) == 100

    def test_config_stress_scenario_adverse(self):
        """Test: Scénario Adverse augmente les PD."""
        config_baseline = {'stress_scenario': 'Baseline'}
        config_adverse = {'stress_scenario': 'Adverse'}

        df_baseline = generate_positions_advanced(100, seed=42, config=config_baseline)
        df_adverse = generate_positions_advanced(100, seed=42, config=config_adverse)

        # PD moyen doit être plus élevé en Adverse
        assert df_adverse['pd'].mean() > df_baseline['pd'].mean()

    def test_config_stress_scenario_severely_adverse(self):
        """Test: Scénario Severely Adverse augmente encore plus les PD."""
        config_baseline = {'stress_scenario': 'Baseline'}
        config_severe = {'stress_scenario': 'Severely Adverse'}

        df_baseline = generate_positions_advanced(100, seed=42, config=config_baseline)
        df_severe = generate_positions_advanced(100, seed=42, config=config_severe)

        # PD moyen doit être beaucoup plus élevé
        assert df_severe['pd'].mean() > df_baseline['pd'].mean() * 1.5


class TestSimulationEngine:
    """Tests de la classe SimulationEngine."""

    def test_engine_initialization(self):
        """Test: Initialisation du moteur."""
        engine = SimulationEngine(seed=42)

        assert engine.seed == 42
        assert engine.config is not None
        assert engine.entities == DEFAULT_ENTITIES
        assert engine.products == DEFAULT_PRODUCTS

    def test_engine_with_custom_config(self):
        """Test: Initialisation avec config personnalisée."""
        config = {
            'base_currency': 'USD',
            'stress_scenario': 'Adverse',
            'retail_pd_base': 0.03
        }
        engine = SimulationEngine(seed=42, config=config)

        assert engine.config['base_currency'] == 'USD'
        assert engine.config['stress_scenario'] == 'Adverse'
        assert engine.config['retail_pd_base'] == 0.03

    def test_generate_positions(self):
        """Test: Génération de positions."""
        engine = SimulationEngine(seed=42)
        df = engine.generate_positions(num_positions=50)

        assert not df.empty
        assert len(df) == 50

    def test_generate_single_position(self):
        """Test: Génération d'une position individuelle."""
        engine = SimulationEngine(seed=42)
        position = engine._generate_single_position(0)

        assert isinstance(position, dict)
        assert 'position_id' in position
        assert 'ead' in position
        assert position['position_id'] == 'POS_000001'

    def test_generate_ead_and_ccf_mortgage(self):
        """Test: EAD et CCF pour Mortgages."""
        engine = SimulationEngine(seed=42)
        ead, ccf, commitment, drawn = engine._generate_ead_and_ccf('Retail_Mortgages')

        assert ead > 0
        assert ccf == 0.0  # Pas de CCF pour mortgages
        assert commitment == 0.0
        assert drawn == ead

    def test_generate_ead_and_ccf_facilities(self):
        """Test: EAD et CCF pour Credit Facilities."""
        engine = SimulationEngine(seed=42)
        ead, ccf, commitment, drawn = engine._generate_ead_and_ccf('Credit_Facilities')

        assert ead > 0
        assert ccf > 0  # CCF doit être > 0 pour facilities
        assert commitment > 0
        assert drawn > 0
        assert commitment >= drawn  # Commitment doit être >= drawn

    def test_generate_ead_and_ccf_revolving(self):
        """Test: EAD et CCF pour Revolving Credit Lines."""
        engine = SimulationEngine(seed=42)
        ead, ccf, commitment, drawn = engine._generate_ead_and_ccf('Revolving_Credit_Lines')

        assert ccf >= 0.75  # CCF 75-100% pour revolving
        assert ccf <= 1.0

    def test_generate_pd_retail(self):
        """Test: Génération PD pour Retail."""
        engine = SimulationEngine(seed=42)
        pd = engine._generate_pd('Retail_Mortgages')

        assert pd > 0
        assert pd < 0.20  # PD doit rester raisonnable

    def test_generate_pd_corporate(self):
        """Test: Génération PD pour Corporate."""
        engine = SimulationEngine(seed=42)
        pd = engine._generate_pd('Corporate')

        assert pd > 0
        assert pd < 0.20

    def test_generate_pd_sovereign(self):
        """Test: Génération PD pour Sovereign (très faible)."""
        engine = SimulationEngine(seed=42)
        pd = engine._generate_pd('Sovereign')

        assert pd > 0
        assert pd < 0.01  # PD souverain doit être très faible

    def test_generate_lgd_mortgage(self):
        """Test: Génération LGD pour Mortgages (faible)."""
        engine = SimulationEngine(seed=42)
        lgd = engine._generate_lgd('Retail_Mortgages', 'Retail_Mortgages')

        assert lgd >= 0.20
        assert lgd <= 0.45  # LGD mortgage 20-45%

    def test_generate_lgd_deposit(self):
        """Test: Génération LGD pour Deposits (zéro)."""
        engine = SimulationEngine(seed=42)
        lgd = engine._generate_lgd('Retail_Deposits', 'Retail_Other')

        assert lgd == 0.0  # Dépôts non risqués

    def test_generate_maturity_mortgage(self):
        """Test: Génération maturité pour Mortgages (longue)."""
        engine = SimulationEngine(seed=42)
        maturity = engine._generate_maturity('Retail_Mortgages')

        assert maturity >= 15
        assert maturity <= 30  # 15-30 ans

    def test_generate_maturity_deposit(self):
        """Test: Génération maturité pour Deposits (courte)."""
        engine = SimulationEngine(seed=42)
        maturity = engine._generate_maturity('Retail_Deposits')

        assert maturity >= 0.1
        assert maturity <= 2  # 1 mois - 2 ans

    def test_classify_ifrs9_stage_1(self):
        """Test: Classification IFRS 9 Stage 1 (PD faible)."""
        engine = SimulationEngine(seed=42)
        stage = engine._classify_ifrs9_stage(pd=0.003)

        assert stage == 1

    def test_classify_ifrs9_stage_2(self):
        """Test: Classification IFRS 9 Stage 2 (PD moyenne)."""
        engine = SimulationEngine(seed=42)
        stage = engine._classify_ifrs9_stage(pd=0.015)

        assert stage == 2

    def test_classify_ifrs9_stage_3(self):
        """Test: Classification IFRS 9 Stage 3 (PD élevée)."""
        engine = SimulationEngine(seed=42)
        stage = engine._classify_ifrs9_stage(pd=0.05)

        assert stage == 3

    def test_calculate_ecl_stage_1(self):
        """Test: Calcul ECL pour Stage 1 (12 mois)."""
        engine = SimulationEngine(seed=42)
        ecl = engine._calculate_ecl(ead=100000, pd=0.01, lgd=0.40, maturity=5.0, stage=1)

        expected_ecl = 100000 * 0.01 * 0.40
        assert abs(ecl - expected_ecl) < 1.0  # Tolérance

    def test_calculate_ecl_stage_2(self):
        """Test: Calcul ECL pour Stage 2 (lifetime)."""
        engine = SimulationEngine(seed=42)
        ecl = engine._calculate_ecl(ead=100000, pd=0.02, lgd=0.50, maturity=3.0, stage=2)

        # Lifetime ECL avec min(maturity, 1.0)
        expected_ecl = 100000 * 0.02 * 0.50 * 1.0
        assert abs(ecl - expected_ecl) < 1.0

    def test_calculate_interest_rate_eur(self):
        """Test: Calcul taux d'intérêt EUR."""
        engine = SimulationEngine(seed=42)
        rate = engine._calculate_interest_rate(currency='EUR', pd=0.01)

        # base_rate (0.02) + currency_spread (0.0) + risk_spread (0.01 * 100)
        expected_rate = 0.02 + 0.0 + 1.0
        assert abs(rate - expected_rate) < 0.01

    def test_calculate_interest_rate_usd(self):
        """Test: Calcul taux d'intérêt USD."""
        engine = SimulationEngine(seed=42)
        rate = engine._calculate_interest_rate(currency='USD', pd=0.01)

        # base_rate (0.02) + currency_spread (0.005) + risk_spread (1.0)
        expected_rate = 0.02 + 0.005 + 1.0
        assert abs(rate - expected_rate) < 0.01

    def test_optimize_dtypes(self):
        """Test: Optimisation des dtypes pour réduire la mémoire."""
        engine = SimulationEngine(seed=42)
        df = engine.generate_positions(num_positions=100)

        # Vérifier les types catégoriels
        assert df['entity_id'].dtype.name == 'category'
        assert df['product_id'].dtype.name == 'category'
        assert df['exposure_class'].dtype.name == 'category'
        assert df['currency'].dtype.name == 'category'

        # Vérifier les types numériques optimisés
        assert df['ead'].dtype == 'float32'
        assert df['pd'].dtype == 'float32'
        assert df['lgd'].dtype == 'float32'
        assert df['maturity'].dtype == 'float32'
        assert df['stage'].dtype == 'int8'


class TestDataQuality:
    """Tests de qualité des données générées."""

    def test_no_missing_values(self):
        """Test: Aucune valeur manquante."""
        df = generate_positions_advanced(num_positions=100, seed=42)

        assert df.isnull().sum().sum() == 0

    def test_positive_values(self):
        """Test: Valeurs positives pour EAD, PD, LGD."""
        df = generate_positions_advanced(num_positions=100, seed=42)

        assert (df['ead'] > 0).all()
        assert (df['pd'] > 0).all()
        assert (df['lgd'] >= 0).all()  # LGD peut être 0 pour dépôts
        assert (df['maturity'] > 0).all()

    def test_stage_values(self):
        """Test: Stages IFRS 9 valides (1, 2, 3)."""
        df = generate_positions_advanced(num_positions=100, seed=42)

        assert df['stage'].isin([1, 2, 3]).all()

    def test_position_id_unique(self):
        """Test: position_id unique."""
        df = generate_positions_advanced(num_positions=100, seed=42)

        assert df['position_id'].is_unique

    def test_facilities_logic(self):
        """Test: Logique facilities cohérente."""
        df = generate_positions_advanced(num_positions=1000, seed=42)

        # Pour les facilities (CCF > 0)
        facilities = df[df['ccf'] > 0]

        if len(facilities) > 0:
            # commitment_amount >= drawn_amount
            assert (facilities['commitment_amount'] >= facilities['drawn_amount']).all()

            # EAD = drawn + CCF * (commitment - drawn)
            # Tolérance pour les arrondis float32
            for _, row in facilities.iterrows():
                expected_ead = row['drawn_amount'] + row['ccf'] * (row['commitment_amount'] - row['drawn_amount'])
                assert abs(row['ead'] - expected_ead) < 100  # Tolérance


class TestPerformance:
    """Tests de performance."""

    def test_performance_1000_positions(self):
        """Test: 1000 positions en ≤ 10s."""
        import time

        start = time.time()
        df = generate_positions_advanced(num_positions=1000, seed=42)
        duration = time.time() - start

        assert len(df) == 1000
        assert duration < 10.0, f"Trop lent: {duration:.2f}s (objectif: <10s)"

    @pytest.mark.slow
    def test_performance_10000_positions(self):
        """Test: 10000 positions en ≤ 60s."""
        import time

        start = time.time()
        df = generate_positions_advanced(num_positions=10000, seed=42)
        duration = time.time() - start

        assert len(df) == 10000
        assert duration < 60.0, f"Trop lent: {duration:.2f}s (objectif: <60s)"


class TestMemoryOptimization:
    """Tests d'optimisation mémoire."""

    def test_memory_reduction(self):
        """Test: Réduction mémoire ≥ 15% vs types par défaut."""

        # Générer avec types par défaut (sans optimisation)
        df_default = pd.DataFrame({
            'position_id': [f'POS_{i:06d}' for i in range(1000)],
            'entity_id': ['EU_SUB'] * 1000,
            'ead': [100000.0] * 1000,
            'pd': [0.02] * 1000,
            'lgd': [0.40] * 1000,
            'stage': [1] * 1000
        })

        # Générer avec optimisation
        df_optimized = generate_positions_advanced(num_positions=1000, seed=42)

        # Calculer la mémoire utilisée
        mem_default = df_default.memory_usage(deep=True).sum()
        mem_optimized = df_optimized.memory_usage(deep=True).sum()

        reduction_pct = (1 - mem_optimized / mem_default) * 100

        # Objectif: -20% de mémoire
        # On tolère -15% minimum car les données réelles sont plus variées
        assert reduction_pct >= 15.0, f"Réduction mémoire insuffisante: {reduction_pct:.1f}% (objectif: ≥15%)"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

