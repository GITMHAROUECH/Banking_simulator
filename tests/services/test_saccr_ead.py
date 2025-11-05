"""
Tests pour le calcul SA-CCR EAD (I7b).
"""
import pandas as pd
import pytest

from src.services.risk_service import compute_saccr_ead


def test_saccr_ead_ir_basic():
    """Test: Calcul EAD pour trades IR."""
    trades_df = pd.DataFrame(
        {
            "trade_id": ["T001", "T002"],
            "netting_set": ["NS01", "NS01"],
            "asset_class": ["IR", "IR"],
            "notional": [1000000, 500000],
            "maturity_bucket": ["1-5Y", ">5Y"],
            "rating": ["IG", "IG"],
            "mtm": [10000, -5000],
        }
    )

    ead_df, cache_hit = compute_saccr_ead(trades_df, use_cache=False)

    assert not cache_hit
    assert len(ead_df) == 2
    assert "ead_contribution" in ead_df.columns
    assert ead_df["ead_contribution"].sum() > 0


def test_saccr_ead_fx_basic():
    """Test: Calcul EAD pour trades FX."""
    trades_df = pd.DataFrame(
        {
            "trade_id": ["T001", "T002"],
            "netting_set": ["NS01", "NS01"],
            "asset_class": ["FX", "FX"],
            "notional": [1000000, 500000],
            "maturity_bucket": ["1-5Y", "1-5Y"],
            "rating": ["IG", "IG"],
            "mtm": [10000, -5000],
        }
    )

    ead_df, cache_hit = compute_saccr_ead(trades_df, use_cache=False)

    assert not cache_hit
    assert len(ead_df) == 2
    assert ead_df["ead_contribution"].sum() > 0


def test_saccr_ead_equity_basic():
    """Test: Calcul EAD pour trades Equity."""
    trades_df = pd.DataFrame(
        {
            "trade_id": ["T001"],
            "netting_set": ["NS01"],
            "asset_class": ["Equity"],
            "notional": [1000000],
            "maturity_bucket": ["1-5Y"],
            "rating": ["IG"],
            "mtm": [10000],
        }
    )

    ead_df, cache_hit = compute_saccr_ead(trades_df, use_cache=False)

    assert not cache_hit
    assert len(ead_df) == 1
    assert ead_df["ead_contribution"].sum() > 0


def test_saccr_ead_commodity_basic():
    """Test: Calcul EAD pour trades Commodity."""
    trades_df = pd.DataFrame(
        {
            "trade_id": ["T001"],
            "netting_set": ["NS01"],
            "asset_class": ["Commodity"],
            "notional": [1000000],
            "maturity_bucket": ["1-5Y"],
            "rating": ["IG"],
            "mtm": [10000],
        }
    )

    ead_df, cache_hit = compute_saccr_ead(trades_df, use_cache=False)

    assert not cache_hit
    assert len(ead_df) == 1
    assert ead_df["ead_contribution"].sum() > 0


def test_saccr_ead_credit_basic():
    """Test: Calcul EAD pour trades Credit."""
    trades_df = pd.DataFrame(
        {
            "trade_id": ["T001", "T002"],
            "netting_set": ["NS01", "NS01"],
            "asset_class": ["Credit", "Credit"],
            "notional": [1000000, 500000],
            "maturity_bucket": ["1-5Y", "1-5Y"],
            "rating": ["IG", "HY"],
            "mtm": [10000, -5000],
        }
    )

    ead_df, cache_hit = compute_saccr_ead(trades_df, use_cache=False)

    assert not cache_hit
    assert len(ead_df) == 2
    assert ead_df["ead_contribution"].sum() > 0


def test_saccr_ead_multiple_netting_sets():
    """Test: Calcul EAD avec plusieurs netting sets."""
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

    ead_df, cache_hit = compute_saccr_ead(trades_df, use_cache=False)

    assert not cache_hit
    assert len(ead_df) == 3
    assert ead_df["netting_set"].nunique() == 2


def test_saccr_ead_with_collateral():
    """Test: Calcul EAD avec collatéral."""
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

    collateral_df = pd.DataFrame(
        {"netting_set": ["NS01"], "collateral_amount": [5000]}
    )

    ead_df, cache_hit = compute_saccr_ead(
        trades_df, collateral_df=collateral_df, use_cache=False
    )

    assert not cache_hit
    assert len(ead_df) == 2


def test_saccr_ead_cache_hit():
    """Test: Vérifier que le cache fonctionne."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    
    trades_df = pd.DataFrame(
        {
            "trade_id": [f"T_CACHE_{unique_id}"],
            "netting_set": [f"NS_CACHE_{unique_id}"],
            "asset_class": ["IR"],
            "notional": [1000000],
            "maturity_bucket": ["1-5Y"],
            "rating": ["IG"],
            "mtm": [10000],
        }
    )

    # 1er calcul : cache miss
    ead_df1, cache_hit1 = compute_saccr_ead(trades_df, use_cache=True)
    assert not cache_hit1

    # 2ème calcul : cache hit
    ead_df2, cache_hit2 = compute_saccr_ead(trades_df, use_cache=True)
    assert cache_hit2

    # Vérifier que les résultats sont identiques
    pd.testing.assert_frame_equal(ead_df1, ead_df2)


def test_saccr_ead_empty_trades():
    """Test: Validation trades vide."""
    trades_df = pd.DataFrame()

    with pytest.raises(ValueError, match="trades_df ne peut pas être vide"):
        compute_saccr_ead(trades_df)


def test_saccr_ead_missing_columns():
    """Test: Validation colonnes manquantes."""
    trades_df = pd.DataFrame({"trade_id": ["T001"], "notional": [1000000]})

    with pytest.raises(ValueError, match="Colonnes manquantes"):
        compute_saccr_ead(trades_df)

