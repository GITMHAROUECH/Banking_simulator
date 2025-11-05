"""
Tests pour l'agrégateur de risque de contrepartie - I7c.
"""
import pandas as pd
import pytest

from src.services.risk_service import compute_counterparty_risk


def test_counterparty_risk_basic():
    """Test: Calcul risque contrepartie basique."""
    trades_df = pd.DataFrame(
        {
            "trade_id": ["T001", "T002"],
            "netting_set": ["NS01", "NS01"],
            "asset_class": ["IR", "FX"],
            "notional": [1000000, 500000],
            "maturity_bucket": ["1-5Y", "1-5Y"],
            "rating": ["IG", "IG"],
            "mtm": [10000, -5000],
        }
    )

    result, cache_hit = compute_counterparty_risk(trades_df, use_cache=False)

    assert not cache_hit
    assert "saccr" in result
    assert "cva_capital" in result
    assert "cva_pricing" in result

    # Vérifier SA-CCR
    assert "ead_df" in result["saccr"]
    assert "rc" in result["saccr"]
    assert "pfe" in result["saccr"]
    assert "rwa" in result["saccr"]

    # Vérifier CVA Capital
    assert "k_cva" in result["cva_capital"]
    assert "by_counterparty" in result["cva_capital"]

    # CVA Pricing désactivé par défaut
    assert result["cva_pricing"] is None


def test_counterparty_risk_with_cva_pricing():
    """Test: Calcul risque contrepartie avec CVA pricing activé."""
    trades_df = pd.DataFrame(
        {
            "trade_id": ["T001", "T002"],
            "netting_set": ["NS01", "NS01"],
            "asset_class": ["IR", "FX"],
            "notional": [1000000, 500000],
            "maturity_bucket": ["1-5Y", "1-5Y"],
            "rating": ["IG", "IG"],
            "mtm": [10000, -5000],
        }
    )

    params = {"enable_cva_pricing": True}

    result, _ = compute_counterparty_risk(trades_df, params=params, use_cache=False)

    # CVA Pricing activé
    assert result["cva_pricing"] is not None
    assert "cva" in result["cva_pricing"]
    assert "by_bucket" in result["cva_pricing"]


def test_counterparty_risk_all_keys():
    """Test: Vérifier que toutes les clés sont présentes."""
    trades_df = pd.DataFrame(
        {
            "trade_id": ["T001"],
            "netting_set": ["NS01"],
            "asset_class": ["IR"],
            "notional": [1000000],
            "maturity_bucket": ["1-5Y"],
            "rating": ["IG"],
            "mtm": [10000],
        }
    )

    result, _ = compute_counterparty_risk(trades_df, use_cache=False)

    # Vérifier toutes les clés SA-CCR
    saccr_keys = ["ead_df", "rc", "pfe", "pfe_addons", "multiplier", "alpha", "rwa", "k"]
    for key in saccr_keys:
        assert key in result["saccr"], f"Clé manquante: {key}"

    # Vérifier toutes les clés CVA Capital
    cva_capital_keys = ["k_cva", "by_counterparty"]
    for key in cva_capital_keys:
        assert key in result["cva_capital"], f"Clé manquante: {key}"


def test_counterparty_risk_cache_hit():
    """Test: Vérifier que le cache fonctionne (2ᵉ run → cache_hit=True)."""
    import uuid

    unique_id = str(uuid.uuid4())[:8]

    trades_df = pd.DataFrame(
        {
            "trade_id": [f"T_AGG_CACHE_{unique_id}"],
            "netting_set": [f"NS_AGG_CACHE_{unique_id}"],
            "asset_class": ["IR"],
            "notional": [1000000],
            "maturity_bucket": ["1-5Y"],
            "rating": ["IG"],
            "mtm": [10000],
        }
    )

    # 1er calcul : cache miss
    result1, cache_hit1 = compute_counterparty_risk(trades_df, use_cache=True)
    assert not cache_hit1

    # 2ème calcul : cache hit
    result2, cache_hit2 = compute_counterparty_risk(trades_df, use_cache=True)
    assert cache_hit2

    # Vérifier que les résultats sont identiques
    assert result1["saccr"]["rwa"] == result2["saccr"]["rwa"]
    assert result1["cva_capital"]["k_cva"] == result2["cva_capital"]["k_cva"]


def test_counterparty_risk_multiple_netting_sets():
    """Test: Calcul risque contrepartie avec plusieurs netting sets."""
    trades_df = pd.DataFrame(
        {
            "trade_id": ["T001", "T002", "T003"],
            "netting_set": ["NS01", "NS01", "NS02"],
            "asset_class": ["IR", "FX", "Equity"],
            "notional": [1000000, 500000, 750000],
            "maturity_bucket": ["1-5Y", "1-5Y", "1-5Y"],
            "rating": ["IG", "IG", "IG"],
            "mtm": [10000, -5000, 2000],
        }
    )

    result, _ = compute_counterparty_risk(trades_df, use_cache=False)

    # Vérifier que les 2 netting sets sont présents dans CVA Capital
    counterparties = result["cva_capital"]["by_counterparty"]["counterparty"].unique()
    assert len(counterparties) == 2


def test_counterparty_risk_empty_trades():
    """Test: Validation trades vide."""
    trades_df = pd.DataFrame()

    with pytest.raises(ValueError, match="trades_df ne peut pas être vide"):
        compute_counterparty_risk(trades_df)


def test_counterparty_risk_missing_columns():
    """Test: Validation colonnes manquantes."""
    trades_df = pd.DataFrame({"trade_id": ["T001"], "notional": [1000000]})

    with pytest.raises(ValueError, match="Colonnes manquantes"):
        compute_counterparty_risk(trades_df)

