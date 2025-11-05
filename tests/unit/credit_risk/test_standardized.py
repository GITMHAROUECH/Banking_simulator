"""
Unit tests for standardized approach RWA calculations.
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from src.domain.credit_risk.standardized import (
    compute_ead,
    risk_weight_for_row,
    compute_rwa_standardized
)


@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        'standard_risk_weights': {
            'corporates': 1.0,
            'institutions': 0.20,
            'retail': 0.75,
            'secured_by_mortgages': 0.35,
            'central_governments': 0.0,
            'exposures_in_default': 1.50,
            'high_risk_categories': 1.50,
            'equity': 1.00
        }
    }


@pytest.fixture
def sample_positions():
    """Sample positions DataFrame for testing"""
    return pd.DataFrame({
        'entity_id': ['EU_SUB', 'EU_SUB', 'US_SUB', 'US_SUB'],
        'product_id': ['CORP_LOAN', 'SME_LOAN', 'MORTGAGE', 'RETAIL_LOAN'],
        'exposure_class': ['corporates', 'corporates', 'secured_by_mortgages', 'retail'],
        'ead': [1000000, 500000, 2000000, 300000],
        'is_retail': [False, False, False, False],
        'stage': [1, 1, 1, 1]
    })


def test_compute_ead_basic():
    """Test basic EAD computation"""
    df = pd.DataFrame({
        'ead': [1000, 2000, 3000]
    })
    
    result = compute_ead(df)
    
    assert 'ead' in result.columns
    assert result['ead'].sum() == 6000
    assert len(result) == 3


def test_compute_ead_with_ccf():
    """Test EAD computation with CCF (Credit Conversion Factor)"""
    df = pd.DataFrame({
        'ead': [1000, 2000],
        'undrawn': [500, 1000],
        'ccf': [0.5, 0.75]
    })
    
    result = compute_ead(df)
    
    # EAD should include undrawn * ccf
    expected_ead_0 = 1000 + (500 * 0.5)  # 1250
    expected_ead_1 = 2000 + (1000 * 0.75)  # 2750
    
    assert result['ead'].iloc[0] == expected_ead_0
    assert result['ead'].iloc[1] == expected_ead_1


def test_compute_ead_missing_column():
    """Test EAD computation raises error when ead column is missing"""
    df = pd.DataFrame({
        'amount': [1000, 2000]
    })
    
    with pytest.raises(ValueError, match="Column 'ead' not found"):
        compute_ead(df)


def test_risk_weight_for_row_corporates(sample_config):
    """Test risk weight calculation for corporate exposures"""
    row = pd.Series({
        'exposure_class': 'corporates',
        'product_id': 'CORP_LOAN'
    })
    
    weight = risk_weight_for_row(row, sample_config)
    assert weight == 1.0


def test_risk_weight_for_row_sme(sample_config):
    """Test risk weight calculation for SME exposures"""
    row = pd.Series({
        'exposure_class': 'corporates',
        'product_id': 'SME_LOAN'
    })
    
    weight = risk_weight_for_row(row, sample_config)
    assert weight == 0.85  # SME reduction


def test_risk_weight_for_row_institutions(sample_config):
    """Test risk weight calculation for institutions"""
    row = pd.Series({
        'exposure_class': 'institutions',
        'product_id': 'BANK_DEPOSIT'
    })
    
    weight = risk_weight_for_row(row, sample_config)
    assert weight == 0.20


def test_risk_weight_for_row_mortgages(sample_config):
    """Test risk weight calculation for mortgages"""
    row = pd.Series({
        'exposure_class': 'secured_by_mortgages',
        'product_id': 'MORTGAGE'
    })
    
    weight = risk_weight_for_row(row, sample_config)
    assert weight == 0.35


def test_risk_weight_for_row_retail(sample_config):
    """Test risk weight calculation for retail"""
    row = pd.Series({
        'exposure_class': 'retail',
        'product_id': 'RETAIL_LOAN'
    })
    
    weight = risk_weight_for_row(row, sample_config)
    assert weight == 0.75


def test_risk_weight_for_row_defaulted(sample_config):
    """Test risk weight calculation for defaulted exposures"""
    row = pd.Series({
        'exposure_class': 'exposures_in_default',
        'product_id': 'DEFAULT_LOAN'
    })
    
    weight = risk_weight_for_row(row, sample_config)
    assert weight == 1.50


def test_risk_weight_for_row_high_risk(sample_config):
    """Test risk weight calculation for high risk exposures"""
    row = pd.Series({
        'exposure_class': 'high_risk_categories',
        'product_id': 'HIGH_RISK'
    })
    
    weight = risk_weight_for_row(row, sample_config)
    assert weight == 1.50


def test_compute_rwa_standardized_basic(sample_positions, sample_config):
    """Test basic RWA calculation using standardized approach"""
    result = compute_rwa_standardized(sample_positions, sample_config)
    
    assert not result.empty
    assert 'entity_id' in result.columns
    assert 'exposure_class' in result.columns
    assert 'approach' in result.columns
    assert 'ead' in result.columns
    assert 'risk_weight' in result.columns
    assert 'rwa_amount' in result.columns
    assert 'rwa_density' in result.columns
    
    # All approaches should be 'Standardised'
    assert (result['approach'] == 'Standardised').all()


def test_compute_rwa_standardized_calculations(sample_positions, sample_config):
    """Test RWA calculation accuracy"""
    result = compute_rwa_standardized(sample_positions, sample_config)
    
    # Check first position (corporates, 1.0 risk weight)
    corp_row = result[result['product_id'] == 'CORP_LOAN'].iloc[0]
    assert corp_row['ead'] == 1000000
    assert corp_row['risk_weight'] == 1.0
    assert corp_row['rwa_amount'] == 1000000
    
    # Check SME position (0.85 risk weight)
    sme_row = result[result['product_id'] == 'SME_LOAN'].iloc[0]
    assert sme_row['ead'] == 500000
    assert sme_row['risk_weight'] == 0.85
    assert sme_row['rwa_amount'] == 425000
    
    # Check mortgage position (0.35 risk weight)
    mort_row = result[result['product_id'] == 'MORTGAGE'].iloc[0]
    assert mort_row['ead'] == 2000000
    assert mort_row['risk_weight'] == 0.35
    assert mort_row['rwa_amount'] == 700000


def test_compute_rwa_standardized_empty_dataframe(sample_config):
    """Test RWA calculation with empty DataFrame"""
    empty_df = pd.DataFrame()
    
    result = compute_rwa_standardized(empty_df, sample_config)
    
    assert result.empty
    assert 'entity_id' in result.columns


def test_compute_rwa_standardized_total_rwa(sample_positions, sample_config):
    """Test total RWA calculation"""
    result = compute_rwa_standardized(sample_positions, sample_config)
    
    total_rwa = result['rwa_amount'].sum()
    
    # Expected: 1000000*1.0 + 500000*0.85 + 2000000*0.35 + 300000*0.75
    # = 1000000 + 425000 + 700000 + 225000 = 2350000
    expected_total = 2350000
    
    assert abs(total_rwa - expected_total) < 1  # Allow for floating point errors


def test_compute_rwa_standardized_with_retail_filter(sample_config):
    """Test that retail positions are filtered correctly"""
    positions = pd.DataFrame({
        'entity_id': ['EU_SUB', 'EU_SUB'],
        'product_id': ['CORP_LOAN', 'RETAIL_LOAN'],
        'exposure_class': ['corporates', 'retail'],
        'ead': [1000000, 500000],
        'is_retail': [False, True],  # Second one is retail
        'stage': [1, 1]
    })
    
    result = compute_rwa_standardized(positions, sample_config)
    
    # Should only process non-retail (first position)
    assert len(result) == 1
    assert result.iloc[0]['product_id'] == 'CORP_LOAN'


def test_compute_rwa_standardized_no_is_retail_column(sample_config):
    """Test RWA calculation when is_retail column is missing"""
    positions = pd.DataFrame({
        'entity_id': ['EU_SUB'],
        'product_id': ['CORP_LOAN'],
        'exposure_class': ['corporates'],
        'ead': [1000000],
        'stage': [1]
    })
    
    result = compute_rwa_standardized(positions, sample_config)
    
    # Should process all positions when is_retail is missing
    assert len(result) == 1
    assert result.iloc[0]['rwa_amount'] == 1000000

