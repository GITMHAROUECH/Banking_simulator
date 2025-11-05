"""
Tests pour le calcul CVA Capital (BA-CVA) - I7c.
"""
import pandas as pd
import pytest

from src.services.risk_service import compute_cva_capital


def test_cva_capital_basic():
    """Test: Calcul CVA capital basique."""
    ead_df = pd.DataFrame(
        {
            "counterparty": ["CP1", "CP2"],
            "ead": [1000000, 500000],
            "maturity": [1.0, 2.0],
            "weight": [1.0, 1.0],
        }
    )

    result, cache_hit = compute_cva_capital(ead_df, use_cache=False)

    assert not cache_hit
    assert "k_cva" in result
    assert "by_counterparty" in result
    assert result["k_cva"] > 0
    assert len(result["by_counterparty"]) == 2


def test_cva_capital_monotonicity():
    """Test: Vérifier que ↑EAD ⇒ ↑K_CVA."""
    # Cas 1 : EAD faible
    ead_df1 = pd.DataFrame(
        {
            "counterparty": ["CP1"],
            "ead": [100000],
        }
    )

    result1, _ = compute_cva_capital(ead_df1, use_cache=False)
    k_cva1 = result1["k_cva"]

    # Cas 2 : EAD élevé
    ead_df2 = pd.DataFrame(
        {
            "counterparty": ["CP1"],
            "ead": [1000000],
        }
    )

    result2, _ = compute_cva_capital(ead_df2, use_cache=False)
    k_cva2 = result2["k_cva"]

    # Vérifier la monotonicité
    assert k_cva2 > k_cva1, "K_CVA devrait augmenter avec EAD"


def test_cva_capital_multiple_counterparties():
    """Test: Calcul CVA capital avec plusieurs contreparties."""
    ead_df = pd.DataFrame(
        {
            "counterparty": ["CP1", "CP2", "CP3"],
            "ead": [1000000, 500000, 750000],
            "maturity": [1.0, 2.0, 1.5],
            "weight": [1.0, 1.2, 0.8],
        }
    )

    result, _ = compute_cva_capital(ead_df, use_cache=False)

    assert result["k_cva"] > 0
    assert len(result["by_counterparty"]) == 3

    # Vérifier que le terme est calculé correctement
    by_cp = result["by_counterparty"]
    assert "term" in by_cp.columns
    assert (by_cp["term"] == by_cp["weight"] * by_cp["maturity"] * by_cp["ead"]).all()


def test_cva_capital_default_params():
    """Test: Vérifier les paramètres par défaut."""
    ead_df = pd.DataFrame(
        {
            "counterparty": ["CP1"],
            "ead": [1000000],
        }
    )

    result, _ = compute_cva_capital(ead_df, use_cache=False)

    # Vérifier que maturity et weight par défaut sont appliqués
    by_cp = result["by_counterparty"]
    assert by_cp["maturity"].iloc[0] == 1.0  # Défaut
    assert by_cp["weight"].iloc[0] == 1.0  # Défaut


def test_cva_capital_custom_params():
    """Test: Vérifier les paramètres personnalisés."""
    ead_df = pd.DataFrame(
        {
            "counterparty": ["CP1"],
            "ead": [1000000],
        }
    )

    params = {"default_maturity": 2.0, "default_weight": 1.5}

    result, _ = compute_cva_capital(ead_df, params=params, use_cache=False)

    # Vérifier que les paramètres personnalisés sont appliqués
    by_cp = result["by_counterparty"]
    assert by_cp["maturity"].iloc[0] == 2.0
    assert by_cp["weight"].iloc[0] == 1.5


def test_cva_capital_cache_hit():
    """Test: Vérifier que le cache fonctionne."""
    import uuid

    unique_id = str(uuid.uuid4())[:8]

    ead_df = pd.DataFrame(
        {
            "counterparty": [f"CP_CACHE_{unique_id}"],
            "ead": [1000000],
        }
    )

    # 1er calcul : cache miss
    result1, cache_hit1 = compute_cva_capital(ead_df, use_cache=True)
    assert not cache_hit1

    # 2ème calcul : cache hit
    result2, cache_hit2 = compute_cva_capital(ead_df, use_cache=True)
    assert cache_hit2

    # Vérifier que les résultats sont identiques
    assert result1["k_cva"] == result2["k_cva"]


def test_cva_capital_empty_ead():
    """Test: Validation EAD vide."""
    ead_df = pd.DataFrame()

    with pytest.raises(ValueError, match="ead_df ne peut pas être vide"):
        compute_cva_capital(ead_df)


def test_cva_capital_missing_columns():
    """Test: Validation colonnes manquantes."""
    ead_df = pd.DataFrame({"counterparty": ["CP1"]})

    with pytest.raises(ValueError, match="Colonnes manquantes"):
        compute_cva_capital(ead_df)

