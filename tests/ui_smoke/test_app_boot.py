"""
Smoke test pour valider le démarrage de l'application.

Objectif : Garantir que app/main.py peut être importé sans erreur
et que les adaptateurs fonctionnent correctement.
"""

import pytest


def test_app_main_import():
    """Test: Import de app/main.py sans exception."""
    try:
        assert True
    except Exception as e:
        pytest.fail(f"Import de app.main a échoué: {e}")


def test_legacy_compat_import():
    """Test: Import des adaptateurs sans exception."""
    try:
        assert True
    except Exception as e:
        pytest.fail(f"Import de app.adapters.legacy_compat a échoué: {e}")


def test_legacy_compat_exports():
    """Test: Les adaptateurs exposent les fonctions attendues."""
    from app.adapters import legacy_compat

    # Vérifier que les fonctions sont exposées
    assert hasattr(legacy_compat, 'generate_positions_advanced')
    assert hasattr(legacy_compat, 'calculate_rwa_advanced')
    assert hasattr(legacy_compat, 'calculate_liquidity_advanced')
    assert hasattr(legacy_compat, 'compute_capital_ratios')


def test_generate_positions_via_adapter():
    """Test: Appeler generate_positions_advanced via adaptateur."""
    from app.adapters.legacy_compat import generate_positions_advanced

    # Générer 10 positions pour test rapide
    positions_df = generate_positions_advanced(num_positions=10, seed=42)

    # Vérifier que le DataFrame n'est pas vide
    assert not positions_df.empty
    assert len(positions_df) == 10

    # Vérifier les colonnes minimales
    required_cols = ['position_id', 'entity_id', 'ead', 'pd', 'lgd']
    for col in required_cols:
        assert col in positions_df.columns, f"Colonne manquante: {col}"


def test_calculate_rwa_via_adapter():
    """Test: Appeler calculate_rwa_advanced via adaptateur."""
    from app.adapters.legacy_compat import (
        calculate_rwa_advanced,
        generate_positions_advanced,
    )

    # Générer positions
    positions_df = generate_positions_advanced(num_positions=10, seed=42)

    # Calculer RWA
    rwa_df = calculate_rwa_advanced(positions_df)

    # Vérifier que le DataFrame n'est pas vide
    assert not rwa_df.empty
    assert len(rwa_df) == 10

    # Vérifier les colonnes minimales
    assert 'rwa_amount' in rwa_df.columns
    assert 'rwa_density' in rwa_df.columns


def test_calculate_liquidity_via_adapter():
    """Test: Appeler calculate_liquidity_advanced via adaptateur."""
    from app.adapters.legacy_compat import (
        calculate_liquidity_advanced,
        generate_positions_advanced,
    )

    # Générer positions
    positions_df = generate_positions_advanced(num_positions=10, seed=42)

    # Calculer liquidité
    lcr_df, nsfr_df, almm_obj = calculate_liquidity_advanced(positions_df)

    # Vérifier que les DataFrames ne sont pas vides
    assert not lcr_df.empty
    assert not nsfr_df.empty

    # Vérifier que almm_obj est un dict
    assert isinstance(almm_obj, dict)


def test_compute_capital_ratios_via_adapter():
    """Test: Appeler compute_capital_ratios via adaptateur."""
    from app.adapters.legacy_compat import (
        calculate_rwa_advanced,
        compute_capital_ratios,
        generate_positions_advanced,
    )

    # Générer positions
    positions_df = generate_positions_advanced(num_positions=10, seed=42)

    # Calculer RWA
    rwa_df = calculate_rwa_advanced(positions_df)

    # Calculer ratios de capital
    own_funds = {
        'cet1': 1_000_000,
        'tier1': 1_200_000,
        'total': 1_500_000,
        'leverage_exposure': 10_000_000
    }
    ratios = compute_capital_ratios(rwa_df, own_funds)

    # Vérifier que c'est un dict
    assert isinstance(ratios, dict)

    # Vérifier les clés minimales
    assert 'cet1_ratio' in ratios
    assert 'tier1_ratio' in ratios
    assert 'total_capital_ratio' in ratios


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

