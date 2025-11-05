"""
Tests pour les stubs COREP/LE/LCR (I8).
"""
import pandas as pd

from src.services.reporting_service import _generate_corep_stubs


def test_generate_corep_c34_stub():
    """Test: Stub COREP C34 (SA-CCR)."""
    saccr = {
        "ead_df": pd.DataFrame(
            {
                "netting_set": ["NS01", "NS01", "NS02"],
                "ead_contribution": [100000, 50000, 75000],
            }
        ),
        "rc": 10000.0,
        "pfe": 50000.0,
        "multiplier": 0.95,
        "alpha": 1.4,
    }

    stubs = _generate_corep_stubs(
        positions_df=pd.DataFrame(),
        rwa_df=pd.DataFrame(),
        liquidity={},
        ratios={},
        saccr=saccr,
    )

    # Vérifier que le stub C34 est généré
    assert "COREP C34" in stubs
    c34_df = stubs["COREP C34"]

    # Vérifier les colonnes
    assert "Counterparty" in c34_df.columns
    assert "EAD" in c34_df.columns
    assert "RC" in c34_df.columns
    assert "PFE" in c34_df.columns
    assert "Multiplier" in c34_df.columns
    assert "Alpha" in c34_df.columns

    # Vérifier les valeurs agrégées
    assert len(c34_df) == 2  # 2 netting sets
    assert c34_df["EAD"].sum() == 225000  # 150000 + 75000


def test_generate_corep_c07_stub():
    """Test: Stub COREP C07 (Crédit - Expositions)."""
    positions_df = pd.DataFrame(
        {
            "exposure_class": ["Corporate", "Retail", "Sovereign"],
            "exposure": [1000000, 500000, 750000],
        }
    )

    stubs = _generate_corep_stubs(
        positions_df=positions_df,
        rwa_df=pd.DataFrame(),
        liquidity={},
        ratios={},
        saccr={},
    )

    # Vérifier que le stub C07 est généré
    assert "COREP C07" in stubs
    c07_df = stubs["COREP C07"]

    # Vérifier les colonnes
    assert "Exposure Class" in c07_df.columns
    assert "Total Exposure" in c07_df.columns

    # Vérifier les valeurs
    assert len(c07_df) == 3
    assert c07_df["Total Exposure"].sum() == 2250000


def test_generate_corep_c08_stub():
    """Test: Stub COREP C08 (Crédit - RWA)."""
    rwa_df = pd.DataFrame(
        {
            "exposure_class": ["Corporate", "Retail", "Sovereign"],
            "rwa": [800000, 375000, 0],
        }
    )

    stubs = _generate_corep_stubs(
        positions_df=pd.DataFrame(),
        rwa_df=rwa_df,
        liquidity={},
        ratios={},
        saccr={},
    )

    # Vérifier que le stub C08 est généré
    assert "COREP C08" in stubs
    c08_df = stubs["COREP C08"]

    # Vérifier les colonnes
    assert "Exposure Class" in c08_df.columns
    assert "Total RWA" in c08_df.columns

    # Vérifier les valeurs
    assert len(c08_df) == 3
    assert c08_df["Total RWA"].sum() == 1175000


def test_generate_leverage_stub():
    """Test: Stub Leverage Ratio."""
    positions_df = pd.DataFrame(
        {
            "exposure_class": ["Corporate", "Retail", "Sovereign"],
            "exposure": [1000000, 500000, 750000],
        }
    )

    ratios = {
        "tier1": 1200000,
        "leverage_ratio": 0.05,
    }

    stubs = _generate_corep_stubs(
        positions_df=positions_df,
        rwa_df=pd.DataFrame(),
        liquidity={},
        ratios=ratios,
        saccr={},
    )

    # Vérifier que le stub Leverage est généré
    assert "Leverage" in stubs
    leverage_df = stubs["Leverage"]

    # Vérifier les colonnes
    assert "Metric" in leverage_df.columns
    assert "Value" in leverage_df.columns

    # Vérifier les valeurs
    assert len(leverage_df) == 3
    assert "Total Exposure" in leverage_df["Metric"].values
    assert "Leverage Ratio" in leverage_df["Metric"].values


def test_generate_lcr_stub():
    """Test: Stub LCR."""
    lcr_df = pd.DataFrame(
        {
            "category": ["HQLA Level 1", "HQLA Level 2A", "Net Outflows"],
            "amount": [1000000, 500000, 800000],
        }
    )

    stubs = _generate_corep_stubs(
        positions_df=pd.DataFrame(),
        rwa_df=pd.DataFrame(),
        liquidity={"lcr": lcr_df},
        ratios={},
        saccr={},
    )

    # Vérifier que le stub LCR est généré
    assert "LCR" in stubs
    lcr_stub_df = stubs["LCR"]

    # Vérifier les colonnes
    assert "Category" in lcr_stub_df.columns
    assert "Amount" in lcr_stub_df.columns

    # Vérifier les valeurs
    assert len(lcr_stub_df) == 3
    assert lcr_stub_df["Amount"].sum() == 2300000


def test_generate_all_stubs():
    """Test: Génération de tous les stubs."""
    positions_df = pd.DataFrame(
        {
            "exposure_class": ["Corporate", "Retail"],
            "exposure": [1000000, 500000],
        }
    )

    rwa_df = pd.DataFrame(
        {
            "exposure_class": ["Corporate", "Retail"],
            "rwa": [800000, 375000],
        }
    )

    lcr_df = pd.DataFrame(
        {
            "category": ["HQLA Level 1", "Net Outflows"],
            "amount": [1000000, 800000],
        }
    )

    ratios = {
        "tier1": 1200000,
        "leverage_ratio": 0.05,
    }

    saccr = {
        "ead_df": pd.DataFrame(
            {
                "netting_set": ["NS01"],
                "ead_contribution": [100000],
            }
        ),
        "rc": 10000.0,
        "pfe": 50000.0,
        "multiplier": 0.95,
        "alpha": 1.4,
    }

    stubs = _generate_corep_stubs(
        positions_df=positions_df,
        rwa_df=rwa_df,
        liquidity={"lcr": lcr_df},
        ratios=ratios,
        saccr=saccr,
    )

    # Vérifier que tous les stubs sont générés
    assert "COREP C34" in stubs
    assert "COREP C07" in stubs
    assert "COREP C08" in stubs
    assert "Leverage" in stubs
    assert "LCR" in stubs


def test_corep_stubs_coherence():
    """Test: Cohérence des stubs COREP (totaux ≥ 0, ratios ∈ [0, 1.5])."""
    positions_df = pd.DataFrame(
        {
            "exposure_class": ["Corporate"],
            "exposure": [1000000],
        }
    )

    rwa_df = pd.DataFrame(
        {
            "exposure_class": ["Corporate"],
            "rwa": [800000],
        }
    )

    ratios = {
        "tier1": 1200000,
        "leverage_ratio": 0.05,
    }

    stubs = _generate_corep_stubs(
        positions_df=positions_df,
        rwa_df=rwa_df,
        liquidity={},
        ratios=ratios,
        saccr={},
    )

    # Vérifier C07 : Total Exposure ≥ 0
    c07_df = stubs["COREP C07"]
    assert (c07_df["Total Exposure"] >= 0).all()

    # Vérifier C08 : Total RWA ≥ 0
    c08_df = stubs["COREP C08"]
    assert (c08_df["Total RWA"] >= 0).all()

    # Vérifier Leverage : Leverage Ratio ∈ [0, 1.5]
    leverage_df = stubs["Leverage"]
    leverage_ratio_row = leverage_df[leverage_df["Metric"] == "Leverage Ratio"]
    if not leverage_ratio_row.empty:
        leverage_ratio = leverage_ratio_row["Value"].iloc[0]
        assert 0 <= leverage_ratio <= 1.5

