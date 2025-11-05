"""
Tests pour le calcul SA-CCR RWA (I7b).
"""
import pandas as pd
import pytest

from src.services.risk_service import compute_saccr_rwa


def test_saccr_rwa_basic():
    """Test: Calcul RWA basique."""
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

    rwa_result, cache_hit = compute_saccr_rwa(trades_df, use_cache=False)

    assert not cache_hit
    assert "ead" in rwa_result
    assert "rwa" in rwa_result
    assert "rc" in rwa_result
    assert "pfe" in rwa_result
    assert "pfe_addons" in rwa_result
    assert "multiplier" in rwa_result
    assert "alpha" in rwa_result
    assert "k" in rwa_result

    # Vérifier les valeurs
    assert rwa_result["ead"] > 0
    assert rwa_result["rwa"] > 0
    assert rwa_result["k"] == 1.0  # 100%


def test_saccr_rwa_pfe_addons():
    """Test: Vérifier les add-ons PFE par classe."""
    trades_df = pd.DataFrame(
        {
            "trade_id": ["T001", "T002", "T003"],
            "netting_set": ["NS01", "NS01", "NS01"],
            "asset_class": ["IR", "FX", "Equity"],
            "notional": [1000000, 500000, 750000],
            "maturity_bucket": ["1-5Y", "1-5Y", "1-5Y"],
            "rating": ["IG", "IG", "IG"],
            "mtm": [10000, -5000, 2000],
        }
    )

    rwa_result, _ = compute_saccr_rwa(trades_df, use_cache=False)

    pfe_addons = rwa_result["pfe_addons"]

    assert "IR" in pfe_addons
    assert "FX" in pfe_addons
    assert "Equity" in pfe_addons
    assert "Total" in pfe_addons

    # Vérifier que Total = somme des add-ons
    total_expected = pfe_addons["IR"] + pfe_addons["FX"] + pfe_addons["Equity"]
    assert abs(pfe_addons["Total"] - total_expected) < 0.01


def test_saccr_rwa_with_custom_alpha():
    """Test: Calcul RWA avec alpha personnalisé."""
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

    params = {"alpha": 2.0}

    rwa_result, _ = compute_saccr_rwa(trades_df, params=params, use_cache=False)

    assert rwa_result["alpha"] == 2.0


def test_saccr_rwa_cache_hit():
    """Test: Vérifier que le cache fonctionne."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    
    trades_df = pd.DataFrame(
        {
            "trade_id": [f"T_RWA_CACHE_{unique_id}"],
            "netting_set": [f"NS_RWA_CACHE_{unique_id}"],
            "asset_class": ["IR"],
            "notional": [1000000],
            "maturity_bucket": ["1-5Y"],
            "rating": ["IG"],
            "mtm": [10000],
        }
    )

    # 1er calcul : cache miss
    rwa_result1, cache_hit1 = compute_saccr_rwa(trades_df, use_cache=True)
    assert not cache_hit1

    # 2ème calcul : cache hit
    rwa_result2, cache_hit2 = compute_saccr_rwa(trades_df, use_cache=True)
    assert cache_hit2

    # Vérifier que les résultats sont identiques
    assert rwa_result1["ead"] == rwa_result2["ead"]
    assert rwa_result1["rwa"] == rwa_result2["rwa"]


def test_saccr_rwa_empty_trades():
    """Test: Validation trades vide."""
    trades_df = pd.DataFrame()

    with pytest.raises(ValueError, match="trades_df ne peut pas être vide"):
        compute_saccr_rwa(trades_df)


def test_saccr_rwa_ead_rwa_relationship():
    """Test: Vérifier que RWA = EAD × K."""
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

    rwa_result, _ = compute_saccr_rwa(trades_df, use_cache=False)

    # RWA = EAD × K
    expected_rwa = rwa_result["ead"] * rwa_result["k"]
    assert abs(rwa_result["rwa"] - expected_rwa) < 0.01


def test_saccr_rwa_large_portfolio():
    """Test: Performance sur grand portefeuille (20k trades)."""
    import numpy as np

    np.random.seed(42)

    num_trades = 20000
    trades_df = pd.DataFrame(
        {
            "trade_id": [f"T{i:05d}" for i in range(num_trades)],
            "netting_set": [f"NS{np.random.randint(1, 101):03d}" for _ in range(num_trades)],
            "asset_class": np.random.choice(
                ["IR", "FX", "Equity", "Commodity", "Credit"], num_trades
            ),
            "notional": np.random.uniform(100000, 10000000, num_trades),
            "maturity_bucket": np.random.choice(["0-1Y", "1-5Y", ">5Y"], num_trades),
            "rating": np.random.choice(["IG", "HY"], num_trades),
            "mtm": np.random.uniform(-100000, 100000, num_trades),
        }
    )

    import time

    start = time.time()
    rwa_result, _ = compute_saccr_rwa(trades_df, use_cache=False)
    elapsed = time.time() - start

    # Vérifier performance : < 3s pour 20k trades
    assert elapsed < 3.0, f"Calcul trop lent : {elapsed:.2f}s"
    assert rwa_result["ead"] > 0
    assert rwa_result["rwa"] > 0

