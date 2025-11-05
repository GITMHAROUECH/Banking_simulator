"""
Tests de contrat pour les adaptateurs legacy (I7a).

Vérifie que les signatures publiques I1→I6 n'ont pas changé.
"""
import inspect

import pandas as pd
import pytest

from app.adapters.legacy_compat import (
    calculate_liquidity_advanced,
    calculate_rwa_advanced,
    compute_capital_ratios,
    create_excel_export_advanced,
    generate_positions_advanced,
)


def test_generate_positions_advanced_signature():
    """Test: Signature de generate_positions_advanced préservée."""
    sig = inspect.signature(generate_positions_advanced)
    params = list(sig.parameters.keys())

    assert "num_positions" in params
    assert "seed" in params
    assert "config" in params


def test_generate_positions_advanced_return_type():
    """Test: generate_positions_advanced retourne un DataFrame."""
    result = generate_positions_advanced(num_positions=10, seed=42)
    assert isinstance(result, pd.DataFrame)
    assert not result.empty


def test_calculate_rwa_advanced_signature():
    """Test: Signature de calculate_rwa_advanced préservée."""
    sig = inspect.signature(calculate_rwa_advanced)
    params = list(sig.parameters.keys())

    assert "positions_df" in params


def test_calculate_rwa_advanced_return_type():
    """Test: calculate_rwa_advanced retourne un DataFrame."""
    positions_df = generate_positions_advanced(num_positions=10, seed=42)
    result = calculate_rwa_advanced(positions_df)
    assert isinstance(result, pd.DataFrame)
    assert not result.empty


def test_calculate_liquidity_advanced_signature():
    """Test: Signature de calculate_liquidity_advanced préservée."""
    sig = inspect.signature(calculate_liquidity_advanced)
    params = list(sig.parameters.keys())

    assert "positions_df" in params


def test_calculate_liquidity_advanced_return_type():
    """Test: calculate_liquidity_advanced retourne un tuple de 3 éléments."""
    positions_df = generate_positions_advanced(num_positions=10, seed=42)
    result = calculate_liquidity_advanced(positions_df)

    assert isinstance(result, tuple)
    assert len(result) == 3

    lcr_df, nsfr_df, almm_obj = result
    assert isinstance(lcr_df, pd.DataFrame)
    assert isinstance(nsfr_df, pd.DataFrame)


def test_compute_capital_ratios_signature():
    """Test: Signature de compute_capital_ratios préservée."""
    sig = inspect.signature(compute_capital_ratios)
    params = list(sig.parameters.keys())

    assert "rwa_df" in params
    assert "own_funds" in params


def test_compute_capital_ratios_return_type():
    """Test: compute_capital_ratios retourne un dict."""
    positions_df = generate_positions_advanced(num_positions=10, seed=42)
    rwa_df = calculate_rwa_advanced(positions_df)

    own_funds = {
        "cet1": 1000.0,
        "tier1": 1200.0,
        "total": 1500.0,
        "leverage_exposure": 10000.0,
    }

    result = compute_capital_ratios(rwa_df, own_funds)

    assert isinstance(result, dict)
    assert "cet1_ratio" in result
    assert "tier1_ratio" in result
    assert "total_capital_ratio" in result


def test_create_excel_export_advanced_signature():
    """Test: Signature de create_excel_export_advanced préservée."""
    sig = inspect.signature(create_excel_export_advanced)
    params = list(sig.parameters.keys())

    assert "positions_df" in params
    assert "rwa_df" in params
    assert "lcr_df" in params
    assert "nsfr_df" in params
    assert "capital_ratios" in params


def test_create_excel_export_advanced_return_type():
    """Test: create_excel_export_advanced retourne des bytes."""
    positions_df = generate_positions_advanced(num_positions=10, seed=42)
    rwa_df = calculate_rwa_advanced(positions_df)
    lcr_df, nsfr_df, almm_obj = calculate_liquidity_advanced(positions_df)

    own_funds = {
        "cet1": 1000.0,
        "tier1": 1200.0,
        "total": 1500.0,
        "leverage_exposure": 10000.0,
    }
    capital_ratios = compute_capital_ratios(rwa_df, own_funds)

    result = create_excel_export_advanced(
        positions_df=positions_df,
        rwa_df=rwa_df,
        lcr_df=lcr_df,
        nsfr_df=nsfr_df,
        capital_ratios=capital_ratios,
    )

    assert isinstance(result, bytes)
    assert len(result) > 0


def test_all_adapters_importable():
    """Test: Tous les adaptateurs peuvent être importés."""
    from app.adapters import legacy_compat

    assert hasattr(legacy_compat, "generate_positions_advanced")
    assert hasattr(legacy_compat, "calculate_rwa_advanced")
    assert hasattr(legacy_compat, "calculate_liquidity_advanced")
    assert hasattr(legacy_compat, "compute_capital_ratios")
    assert hasattr(legacy_compat, "create_excel_export_advanced")

