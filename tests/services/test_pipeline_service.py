"""
Tests pour le service pipeline E2E (I7a).
"""
import pytest

from src.services import run_full_pipeline


def test_pipeline_keys():
    """Test: Le pipeline retourne toutes les clés attendues."""
    own_funds = {
        "cet1": 1000.0,
        "tier1": 1200.0,
        "total": 1500.0,
        "leverage_exposure": 10000.0,
    }

    results = run_full_pipeline(
        num_positions=100, seed=42, own_funds=own_funds, use_cache=False
    )

    # Vérifier les clés
    expected_keys = {
        "positions_df",
        "rwa_df",
        "lcr_df",
        "nsfr_df",
        "almm_obj",
        "capital_ratios",
        "excel_bytes",
        "cache_hits",
    }

    assert set(results.keys()) == expected_keys


def test_pipeline_cache_hits():
    """Test: Le pipeline retourne les cache_hits pour chaque étape."""
    own_funds = {
        "cet1": 1000.0,
        "tier1": 1200.0,
        "total": 1500.0,
        "leverage_exposure": 10000.0,
    }

    results = run_full_pipeline(
        num_positions=100, seed=42, own_funds=own_funds, use_cache=False
    )

    cache_hits = results["cache_hits"]

    # Vérifier les clés cache_hits
    expected_cache_keys = {"simulation", "rwa", "liquidity", "capital", "export"}
    assert set(cache_hits.keys()) == expected_cache_keys

    # Toutes les valeurs doivent être des booléens
    for key, value in cache_hits.items():
        assert isinstance(value, bool), f"cache_hits[{key}] doit être un bool"


def test_pipeline_second_run_hits_cache():
    """Test: Un 2ème run avec les mêmes paramètres hit le cache."""
    own_funds = {
        "cet1": 1000.0,
        "tier1": 1200.0,
        "total": 1500.0,
        "leverage_exposure": 10000.0,
    }

    # 1er run : cache miss
    results1 = run_full_pipeline(
        num_positions=100, seed=123, own_funds=own_funds, use_cache=True
    )

    cache_hits1 = results1["cache_hits"]

    # 2ème run : cache hit
    results2 = run_full_pipeline(
        num_positions=100, seed=123, own_funds=own_funds, use_cache=True
    )

    cache_hits2 = results2["cache_hits"]

    # Au moins une étape doit avoir un cache hit au 2ème run
    # (simulation devrait être en cache)
    assert cache_hits2["simulation"] is True, "Simulation devrait être en cache au 2ème run"


def test_pipeline_invalid_num_positions():
    """Test: Validation num_positions."""
    own_funds = {
        "cet1": 1000.0,
        "tier1": 1200.0,
        "total": 1500.0,
        "leverage_exposure": 10000.0,
    }

    with pytest.raises(ValueError, match="num_positions doit être > 0"):
        run_full_pipeline(num_positions=0, seed=42, own_funds=own_funds)


def test_pipeline_invalid_seed():
    """Test: Validation seed."""
    own_funds = {
        "cet1": 1000.0,
        "tier1": 1200.0,
        "total": 1500.0,
        "leverage_exposure": 10000.0,
    }

    with pytest.raises(ValueError, match="seed doit être >= 0"):
        run_full_pipeline(num_positions=100, seed=-1, own_funds=own_funds)


def test_pipeline_missing_own_funds_keys():
    """Test: Validation own_funds."""
    own_funds = {
        "cet1": 1000.0,
        # Manque tier1, total, leverage_exposure
    }

    with pytest.raises(ValueError, match="Clés manquantes dans own_funds"):
        run_full_pipeline(num_positions=100, seed=42, own_funds=own_funds)


def test_pipeline_dataframes_not_empty():
    """Test: Les DataFrames retournés ne sont pas vides."""
    own_funds = {
        "cet1": 1000.0,
        "tier1": 1200.0,
        "total": 1500.0,
        "leverage_exposure": 10000.0,
    }

    results = run_full_pipeline(
        num_positions=100, seed=42, own_funds=own_funds, use_cache=False
    )

    assert not results["positions_df"].empty
    assert not results["rwa_df"].empty
    assert not results["lcr_df"].empty
    assert not results["nsfr_df"].empty


def test_pipeline_excel_bytes_not_empty():
    """Test: L'export Excel n'est pas vide."""
    own_funds = {
        "cet1": 1000.0,
        "tier1": 1200.0,
        "total": 1500.0,
        "leverage_exposure": 10000.0,
    }

    results = run_full_pipeline(
        num_positions=100, seed=42, own_funds=own_funds, use_cache=False
    )

    assert len(results["excel_bytes"]) > 0
    assert isinstance(results["excel_bytes"], bytes)

