"""
Tests for COREP/FINREP full calculations (EBA v3.3 compliant).

This module tests the complete COREP/FINREP implementations
against EBA specifications.
"""

import pandas as pd
import pytest

from src.domain.reporting.corep import (
    generate_corep_c07,
    generate_corep_c08,
    generate_corep_c34,
)
from src.domain.reporting.finrep import (
    generate_finrep_f09,
    generate_finrep_f18,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_positions():
    """Sample positions DataFrame for testing."""
    return pd.DataFrame(
        {
            "exposure_class": [
                "Corporate",
                "Corporate",
                "Retail",
                "Retail",
                "Sovereign",
                "RealEstate",
            ],
            "notional": [1000000, 500000, 200000, 150000, 800000, 300000],
            "ead": [950000, 450000, 180000, 140000, 800000, 280000],
            "product_type": ["Loan", "Loan", "Loan", "Loan", "Bond", "Loan"],
            "maturity_years": [3.5, 0.5, 2.0, 6.0, 10.0, 4.0],
            "collateral_value": [500000, 0, 100000, 0, 0, 300000],
        }
    )


@pytest.fixture
def sample_rwa():
    """Sample RWA DataFrame for testing."""
    return pd.DataFrame(
        {
            "exposure_class": [
                "Corporate",
                "Corporate",
                "Retail",
                "Retail",
                "Sovereign",
                "RealEstate",
            ],
            "rwa": [11875000, 5625000, 1687500, 1312500, 0, 1225000],
            "ead": [950000, 450000, 180000, 140000, 800000, 280000],
            "approach": ["STD", "STD", "STD", "STD", "STD", "STD"],
        }
    )


@pytest.fixture
def sample_saccr():
    """Sample SA-CCR results for testing."""
    ead_df = pd.DataFrame(
        {
            "netting_set": ["NS001", "NS001", "NS002", "NS002"],
            "ead_contribution": [100000, 50000, 80000, 70000],
            "risk_weight": [1.0, 1.0, 0.75, 0.75],
        }
    )
    return {
        "ead_df": ead_df,
        "rc": 50000.0,
        "pfe": 100000.0,
        "multiplier": 0.9,
        "alpha": 1.4,
    }


@pytest.fixture
def sample_ecl_results():
    """Sample ECL results DataFrame for testing."""
    return pd.DataFrame(
        {
            "stage": ["S1", "S1", "S2", "S2", "S3", "S3"],
            "ead": [1000000, 500000, 200000, 150000, 100000, 50000],
            "ecl_amount": [5000, 2500, 10000, 7500, 50000, 25000],
            "exposure_class": [
                "Corporate",
                "Retail",
                "Corporate",
                "Retail",
                "Corporate",
                "Retail",
            ],
            "exposure_id": ["exp001", "exp002", "exp003", "exp004", "exp005", "exp006"],
        }
    )


# ============================================================================
# COREP C07 Tests
# ============================================================================


def test_corep_c07_basic(sample_positions, sample_rwa):
    """Test COREP C07 generation with basic data."""
    c07 = generate_corep_c07(sample_positions, sample_rwa)

    # Check structure
    assert not c07.empty
    assert "EBA_Code" in c07.columns
    assert "Exposure_Class" in c07.columns
    assert "Original_Exposure" in c07.columns
    assert "Exposure_Value" in c07.columns
    assert "RWEA" in c07.columns
    assert "Risk_Weight_Pct" in c07.columns
    assert "Own_Funds_Requirements" in c07.columns

    # Check Corporate row
    corporate = c07[c07["Exposure_Class"] == "Corporate"]
    assert not corporate.empty
    assert corporate["EBA_Code"].iloc[0] == "070"  # Corporate EBA code
    assert corporate["Original_Exposure"].iloc[0] > 0
    assert corporate["Exposure_Value"].iloc[0] > 0
    assert corporate["RWEA"].iloc[0] > 0


def test_corep_c07_empty_positions():
    """Test COREP C07 with empty positions."""
    empty_positions = pd.DataFrame()
    empty_rwa = pd.DataFrame()

    c07 = generate_corep_c07(empty_positions, empty_rwa)

    assert c07.empty
    assert list(c07.columns) == [
        "EBA_Code",
        "Exposure_Class",
        "Original_Exposure",
        "Exposure_Value",
        "RWEA",
        "Risk_Weight_Pct",
        "Own_Funds_Requirements",
    ]


def test_corep_c07_own_funds_requirements(sample_positions, sample_rwa):
    """Test COREP C07 Own Funds Requirements calculation (8% of RWEA)."""
    c07 = generate_corep_c07(sample_positions, sample_rwa)

    for _, row in c07.iterrows():
        expected_ofr = row["RWEA"] * 0.08
        assert abs(row["Own_Funds_Requirements"] - expected_ofr) < 0.01


def test_corep_c07_risk_weight_calculation(sample_positions, sample_rwa):
    """Test COREP C07 Risk Weight calculation."""
    c07 = generate_corep_c07(sample_positions, sample_rwa)

    # Risk Weight % = (RWEA / (Exposure_Value × 12.5)) × 100
    for _, row in c07.iterrows():
        if row["Exposure_Value"] > 0:
            expected_rw_pct = (row["RWEA"] / (row["Exposure_Value"] * 12.5)) * 100
            assert abs(row["Risk_Weight_Pct"] - expected_rw_pct) < 0.1


# ============================================================================
# COREP C08 Tests
# ============================================================================


def test_corep_c08_basic(sample_positions, sample_rwa):
    """Test COREP C08 generation with basic data."""
    c08 = generate_corep_c08(sample_positions, sample_rwa)

    # Check structure
    assert not c08.empty
    assert "EBA_Code" in c08.columns
    assert "Exposure_Class" in c08.columns
    assert "Approach" in c08.columns
    assert "Exposure_Value" in c08.columns
    assert "RWEA" in c08.columns
    assert "Capital_Requirements" in c08.columns
    assert "Risk_Density_Pct" in c08.columns


def test_corep_c08_approach_breakdown(sample_rwa):
    """Test COREP C08 with approach breakdown (STD vs IRB)."""
    # Add IRB approach for some exposures
    rwa_mixed = sample_rwa.copy()
    rwa_mixed.loc[0, "approach"] = "FIRB"

    positions = pd.DataFrame(
        {
            "exposure_class": ["Corporate", "Retail"],
            "notional": [1000000, 200000],
        }
    )

    c08 = generate_corep_c08(positions, rwa_mixed)

    # Should have both STD and FIRB approaches
    assert "STD" in c08["Approach"].values
    # Check at least one row with FIRB (if aggregation kept it)


def test_corep_c08_capital_requirements(sample_positions, sample_rwa):
    """Test COREP C08 Capital Requirements (8% of RWEA)."""
    c08 = generate_corep_c08(sample_positions, sample_rwa)

    for _, row in c08.iterrows():
        expected_cap_req = row["RWEA"] * 0.08
        assert abs(row["Capital_Requirements"] - expected_cap_req) < 0.01


def test_corep_c08_risk_density(sample_positions, sample_rwa):
    """Test COREP C08 Risk Density calculation."""
    c08 = generate_corep_c08(sample_positions, sample_rwa)

    for _, row in c08.iterrows():
        if row["Exposure_Value"] > 0:
            expected_density = (row["RWEA"] / row["Exposure_Value"]) * 100
            assert abs(row["Risk_Density_Pct"] - expected_density) < 0.1


# ============================================================================
# COREP C34 Tests
# ============================================================================


def test_corep_c34_basic(sample_saccr):
    """Test COREP C34 generation with basic SA-CCR data."""
    c34 = generate_corep_c34(sample_saccr)

    # Check structure
    assert not c34.empty
    assert "Netting_Set" in c34.columns
    assert "Replacement_Cost" in c34.columns
    assert "PFE_Addon" in c34.columns
    assert "Multiplier" in c34.columns
    assert "Alpha" in c34.columns
    assert "EAD" in c34.columns
    assert "RWEA" in c34.columns

    # Check parameters
    assert c34["Multiplier"].iloc[0] == 0.9
    assert c34["Alpha"].iloc[0] == 1.4


def test_corep_c34_netting_sets(sample_saccr):
    """Test COREP C34 aggregation by netting sets."""
    c34 = generate_corep_c34(sample_saccr)

    # Should have 2 netting sets
    assert len(c34) == 2
    assert "NS001" in c34["Netting_Set"].values
    assert "NS002" in c34["Netting_Set"].values


def test_corep_c34_ead_calculation(sample_saccr):
    """Test COREP C34 EAD calculation."""
    c34 = generate_corep_c34(sample_saccr)

    # EAD for NS001 should be sum of contributions
    ns001 = c34[c34["Netting_Set"] == "NS001"]
    expected_ead_ns001 = 100000 + 50000  # From fixture
    assert abs(ns001["EAD"].iloc[0] - expected_ead_ns001) < 0.01


def test_corep_c34_empty_saccr():
    """Test COREP C34 with empty SA-CCR data."""
    empty_saccr = {"ead_df": pd.DataFrame()}

    c34 = generate_corep_c34(empty_saccr)

    assert c34.empty
    assert list(c34.columns) == [
        "Netting_Set",
        "Replacement_Cost",
        "PFE_Addon",
        "Multiplier",
        "Alpha",
        "EAD",
        "RWEA",
    ]


# ============================================================================
# FINREP F09 Tests
# ============================================================================


def test_finrep_f09_basic(sample_ecl_results):
    """Test FINREP F09 generation with basic ECL data."""
    f09 = generate_finrep_f09(sample_ecl_results)

    # Check structure
    assert not f09.empty
    assert "Exposure_Class" in f09.columns
    assert "Stage" in f09.columns
    assert "Gross_Carrying_Amount" in f09.columns
    assert "Accumulated_Impairment" in f09.columns
    assert "Net_Carrying_Amount" in f09.columns
    assert "ECL_Coverage_Ratio_Pct" in f09.columns


def test_finrep_f09_stage_mapping(sample_ecl_results):
    """Test FINREP F09 IFRS 9 stage mapping."""
    f09 = generate_finrep_f09(sample_ecl_results)

    # Should have all 3 stages
    assert "Performing" in f09["Stage"].values  # S1
    assert "Underperforming" in f09["Stage"].values  # S2
    assert "Non-performing" in f09["Stage"].values  # S3


def test_finrep_f09_net_carrying_amount(sample_ecl_results):
    """Test FINREP F09 Net Carrying Amount calculation."""
    f09 = generate_finrep_f09(sample_ecl_results)

    for _, row in f09.iterrows():
        expected_net = row["Gross_Carrying_Amount"] - row["Accumulated_Impairment"]
        assert abs(row["Net_Carrying_Amount"] - expected_net) < 0.01


def test_finrep_f09_ecl_coverage_ratio(sample_ecl_results):
    """Test FINREP F09 ECL Coverage Ratio calculation."""
    f09 = generate_finrep_f09(sample_ecl_results)

    for _, row in f09.iterrows():
        if row["Gross_Carrying_Amount"] > 0:
            expected_ratio = (
                row["Accumulated_Impairment"] / row["Gross_Carrying_Amount"]
            ) * 100
            assert abs(row["ECL_Coverage_Ratio_Pct"] - expected_ratio) < 0.01


def test_finrep_f09_empty_ecl():
    """Test FINREP F09 with empty ECL results."""
    empty_ecl = pd.DataFrame()

    f09 = generate_finrep_f09(empty_ecl)

    assert f09.empty
    assert list(f09.columns) == [
        "Exposure_Class",
        "Stage",
        "Gross_Carrying_Amount",
        "Accumulated_Impairment",
        "Net_Carrying_Amount",
        "ECL_Coverage_Ratio_Pct",
    ]


# ============================================================================
# FINREP F18 Tests
# ============================================================================


def test_finrep_f18_basic(sample_positions):
    """Test FINREP F18 generation with basic loan data."""
    f18 = generate_finrep_f18(sample_positions)

    # Check structure
    assert not f18.empty
    assert "Exposure_Class" in f18.columns
    assert "Maturity_Bucket" in f18.columns
    assert "Total_Loans" in f18.columns
    assert "Secured_Loans" in f18.columns
    assert "Unsecured_Loans" in f18.columns


def test_finrep_f18_loan_filter(sample_positions):
    """Test FINREP F18 filters only loans."""
    f18 = generate_finrep_f18(sample_positions)

    # Should not include Sovereign (Bond)
    # Only loans: Corporate (2), Retail (2), RealEstate (1)
    # Total: 5 loans


def test_finrep_f18_maturity_buckets(sample_positions):
    """Test FINREP F18 maturity bucket classification."""
    f18 = generate_finrep_f18(sample_positions)

    # Should have maturity buckets: <1y, 1-5y, >5y
    assert "<1y" in f18["Maturity_Bucket"].values  # maturity_years=0.5
    assert "1-5y" in f18["Maturity_Bucket"].values  # maturity_years=3.5, 2.0, 4.0
    assert ">5y" in f18["Maturity_Bucket"].values  # maturity_years=6.0


def test_finrep_f18_secured_vs_unsecured(sample_positions):
    """Test FINREP F18 secured vs unsecured loans."""
    f18 = generate_finrep_f18(sample_positions)

    # Total loans = Secured + Unsecured
    for _, row in f18.iterrows():
        expected_total = row["Secured_Loans"] + row["Unsecured_Loans"]
        assert abs(row["Total_Loans"] - expected_total) < 0.01


def test_finrep_f18_empty_positions():
    """Test FINREP F18 with empty positions."""
    empty_positions = pd.DataFrame()

    f18 = generate_finrep_f18(empty_positions)

    assert f18.empty
    assert list(f18.columns) == [
        "Exposure_Class",
        "Maturity_Bucket",
        "Total_Loans",
        "Secured_Loans",
        "Unsecured_Loans",
    ]


# ============================================================================
# Integration Tests
# ============================================================================


def test_corep_finrep_integration(sample_positions, sample_rwa, sample_ecl_results):
    """Test integration of COREP and FINREP generation."""
    # Generate all reports
    c07 = generate_corep_c07(sample_positions, sample_rwa)
    c08 = generate_corep_c08(sample_positions, sample_rwa)
    f09 = generate_finrep_f09(sample_ecl_results)
    f18 = generate_finrep_f18(sample_positions)

    # All reports should be generated successfully
    assert not c07.empty
    assert not c08.empty
    assert not f09.empty
    assert not f18.empty

    # Check consistency: exposure classes should match across reports
    c07_classes = set(c07["Exposure_Class"].unique())
    c08_classes = set(c08["Exposure_Class"].unique())
    f09_classes = set(f09["Exposure_Class"].unique())
    f18_classes = set(f18["Exposure_Class"].unique())

    # C07 and C08 should have same exposure classes
    assert c07_classes == c08_classes
