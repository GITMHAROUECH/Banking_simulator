"""
Tests pour le calcul CVA Pricing v1 - I7c.
"""
import pandas as pd
import pytest

from src.services.risk_service import compute_cva_pricing


def test_cva_pricing_basic():
    """Test: Calcul CVA pricing basique."""
    trades_df = pd.DataFrame(
        {
            "counterparty": ["CP1", "CP2"],
            "ead": [1000000, 500000],
        }
    )

    result, cache_hit = compute_cva_pricing(trades_df, use_cache=False)

    assert not cache_hit
    assert "cva" in result
    assert "by_bucket" in result
    assert result["cva"] > 0
    assert len(result["by_bucket"]) > 0


def test_cva_pricing_lgd_sensitivity():
    """Test: Vérifier que ↑LGD ⇒ ↑CVA."""
    trades_df = pd.DataFrame(
        {
            "counterparty": ["CP1"],
            "ead": [1000000],
        }
    )

    # Cas 1 : Recovery rate élevé (LGD faible)
    params1 = {"recovery_rate": 0.8}  # LGD = 0.2
    result1, _ = compute_cva_pricing(trades_df, params=params1, use_cache=False)
    cva1 = result1["cva"]

    # Cas 2 : Recovery rate faible (LGD élevé)
    params2 = {"recovery_rate": 0.2}  # LGD = 0.8
    result2, _ = compute_cva_pricing(trades_df, params=params2, use_cache=False)
    cva2 = result2["cva"]

    # Vérifier la sensibilité
    assert cva2 > cva1, "CVA devrait augmenter avec LGD"


def test_cva_pricing_horizon_sensitivity():
    """Test: Vérifier que ↑horizon ⇒ ↑CVA."""
    trades_df = pd.DataFrame(
        {
            "counterparty": ["CP1"],
            "ead": [1000000],
        }
    )

    # Cas 1 : Maturité courte
    params1 = {"default_maturity": 0.5}
    result1, _ = compute_cva_pricing(trades_df, params=params1, use_cache=False)
    cva1 = result1["cva"]

    # Cas 2 : Maturité longue
    params2 = {"default_maturity": 2.0}
    result2, _ = compute_cva_pricing(trades_df, params=params2, use_cache=False)
    cva2 = result2["cva"]

    # Vérifier la sensibilité
    assert cva2 > cva1, "CVA devrait augmenter avec la maturité"


def test_cva_pricing_spread_sensitivity():
    """Test: Vérifier que ↑spread ⇒ ↑CVA."""
    # Cas 1 : Spread faible
    trades_df1 = pd.DataFrame(
        {
            "counterparty": ["CP1"],
            "ead": [1000000],
            "spread": [50],  # 50 bps
        }
    )

    result1, _ = compute_cva_pricing(trades_df1, use_cache=False)
    cva1 = result1["cva"]

    # Cas 2 : Spread élevé
    trades_df2 = pd.DataFrame(
        {
            "counterparty": ["CP1"],
            "ead": [1000000],
            "spread": [500],  # 500 bps
        }
    )

    result2, _ = compute_cva_pricing(trades_df2, use_cache=False)
    cva2 = result2["cva"]

    # Vérifier la sensibilité
    assert cva2 > cva1, "CVA devrait augmenter avec le spread"


def test_cva_pricing_multiple_counterparties():
    """Test: Calcul CVA pricing avec plusieurs contreparties."""
    trades_df = pd.DataFrame(
        {
            "counterparty": ["CP1", "CP2", "CP3"],
            "ead": [1000000, 500000, 750000],
            "spread": [100, 200, 150],
            "maturity": [1.0, 2.0, 1.5],
        }
    )

    result, _ = compute_cva_pricing(trades_df, use_cache=False)

    assert result["cva"] > 0
    assert len(result["by_bucket"]) > 0

    # Vérifier que les 3 contreparties sont présentes
    counterparties = result["by_bucket"]["counterparty"].unique()
    assert len(counterparties) == 3


def test_cva_pricing_cache_hit():
    """Test: Vérifier que le cache fonctionne."""
    import uuid

    unique_id = str(uuid.uuid4())[:8]

    trades_df = pd.DataFrame(
        {
            "counterparty": [f"CP_PRICING_CACHE_{unique_id}"],
            "ead": [1000000],
        }
    )

    # 1er calcul : cache miss
    result1, cache_hit1 = compute_cva_pricing(trades_df, use_cache=True)
    assert not cache_hit1

    # 2ème calcul : cache hit
    result2, cache_hit2 = compute_cva_pricing(trades_df, use_cache=True)
    assert cache_hit2

    # Vérifier que les résultats sont identiques
    assert result1["cva"] == result2["cva"]


def test_cva_pricing_empty_trades():
    """Test: Validation trades vide."""
    trades_df = pd.DataFrame()

    with pytest.raises(ValueError, match="trades_df ne peut pas être vide"):
        compute_cva_pricing(trades_df)


def test_cva_pricing_missing_columns():
    """Test: Validation colonnes manquantes."""
    trades_df = pd.DataFrame({"counterparty": ["CP1"]})

    with pytest.raises(ValueError, match="Colonnes manquantes"):
        compute_cva_pricing(trades_df)

