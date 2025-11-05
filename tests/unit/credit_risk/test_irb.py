"""
Unit tests for IRB approach RWA calculations.
"""

import pytest
import pandas as pd
import numpy as np
import math
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from src.domain.credit_risk.irb import (
    irb_correlation,
    irb_maturity_adj,
    irb_formula,
    compute_rwa_irb
)


@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        'irb_params': {}
    }


@pytest.fixture
def sample_retail_positions():
    """Sample retail positions DataFrame for testing"""
    return pd.DataFrame({
        'entity_id': ['EU_SUB', 'EU_SUB', 'US_SUB'],
        'product_id': ['RETAIL_MORTGAGE', 'RETAIL_CREDIT_CARDS', 'RETAIL_CONSUMER'],
        'exposure_class': ['retail', 'retail', 'retail'],
        'ead': [500000, 100000, 200000],
        'pd': [0.02, 0.05, 0.03],
        'lgd': [0.40, 0.60, 0.45],
        'is_retail': [True, True, True],
        'stage': [1, 1, 1]
    })


def test_irb_correlation_mortgage(sample_config):
    """Test correlation calculation for mortgages"""
    row = pd.Series({
        'product_id': 'RETAIL_MORTGAGE',
        'pd': 0.02
    })
    
    corr = irb_correlation(row, sample_config)
    assert corr == 0.15


def test_irb_correlation_credit_cards(sample_config):
    """Test correlation calculation for credit cards"""
    row = pd.Series({
        'product_id': 'RETAIL_CREDIT_CARDS',
        'pd': 0.05
    })
    
    corr = irb_correlation(row, sample_config)
    assert corr == 0.04


def test_irb_correlation_other_retail(sample_config):
    """Test correlation calculation for other retail"""
    row = pd.Series({
        'product_id': 'RETAIL_CONSUMER',
        'pd': 0.05
    })
    
    corr = irb_correlation(row, sample_config)
    # R = 0.03 + (PD - 0.03) × 0.16 = 0.03 + (0.05 - 0.03) × 0.16 = 0.03 + 0.0032 = 0.0332
    expected = 0.03 + (0.05 - 0.03) * 0.16
    assert abs(corr - expected) < 0.001


def test_irb_correlation_other_retail_low_pd(sample_config):
    """Test correlation for retail with PD below 0.03"""
    row = pd.Series({
        'product_id': 'RETAIL_CONSUMER',
        'pd': 0.01
    })
    
    corr = irb_correlation(row, sample_config)
    assert corr == 0.03  # Floor at 0.03


def test_irb_maturity_adj_short_term(sample_config):
    """Test maturity adjustment for short-term exposures"""
    row = pd.Series({
        'product_id': 'RETAIL_CREDIT_CARDS',
        'pd': 0.05
    })
    
    ma = irb_maturity_adj(row, sample_config)
    assert ma == 1.0  # No adjustment for maturity <= 1 year


def test_irb_maturity_adj_long_term(sample_config):
    """Test maturity adjustment for long-term exposures"""
    row = pd.Series({
        'product_id': 'RETAIL_MORTGAGE',
        'pd': 0.02
    })
    
    ma = irb_maturity_adj(row, sample_config)
    # Should be > 1.0 for maturity > 1 year
    assert ma > 1.0
    assert ma <= 3.0  # Capped at 3.0


def test_irb_formula_basic():
    """Test basic IRB formula calculation"""
    pd_val = 0.02
    lgd_val = 0.45
    correlation = 0.15
    maturity = 1.0
    
    rwa_density = irb_formula(pd_val, lgd_val, correlation, maturity)
    
    # RWA density should be positive
    assert rwa_density >= 0
    # Should be reasonable (between 0 and 12.5, which is max for 100% risk weight)
    assert rwa_density <= 12.5


def test_irb_formula_with_maturity_adjustment():
    """Test IRB formula with maturity adjustment"""
    pd_val = 0.02
    lgd_val = 0.45
    correlation = 0.15
    maturity = 5.0
    
    rwa_density = irb_formula(pd_val, lgd_val, correlation, maturity)
    
    # With maturity > 1, RWA density should be higher
    rwa_density_no_ma = irb_formula(pd_val, lgd_val, correlation, 1.0)
    
    assert rwa_density > rwa_density_no_ma


def test_irb_formula_high_pd():
    """Test IRB formula with high PD"""
    pd_val = 0.20  # 20% PD
    lgd_val = 0.60
    correlation = 0.15
    maturity = 1.0
    
    rwa_density = irb_formula(pd_val, lgd_val, correlation, maturity)
    
    # Higher PD should result in higher RWA density
    assert rwa_density > 0


def test_irb_formula_extreme_values():
    """Test IRB formula handles extreme values"""
    # Test with very low PD
    rwa_low = irb_formula(0.0001, 0.45, 0.15, 1.0)
    assert rwa_low >= 0
    
    # Test with very high PD (capped at 0.9999)
    rwa_high = irb_formula(0.99, 0.45, 0.15, 1.0)
    assert rwa_high >= 0
    
    # High PD should give higher RWA
    assert rwa_high > rwa_low


def test_irb_formula_error_handling():
    """Test IRB formula error handling"""
    # Invalid inputs should return default 1.0
    result = irb_formula(-1, 0.45, 0.15, 1.0)
    assert result >= 0  # Should handle gracefully


def test_compute_rwa_irb_basic(sample_retail_positions, sample_config):
    """Test basic IRB RWA calculation"""
    result = compute_rwa_irb(sample_retail_positions, sample_config)
    
    assert not result.empty
    assert 'entity_id' in result.columns
    assert 'exposure_class' in result.columns
    assert 'approach' in result.columns
    assert 'ead' in result.columns
    assert 'pd' in result.columns
    assert 'lgd' in result.columns
    assert 'maturity' in result.columns
    assert 'correlation' in result.columns
    assert 'rwa_density' in result.columns
    assert 'rwa_amount' in result.columns
    
    # All approaches should be 'IRB'
    assert (result['approach'] == 'IRB').all()


def test_compute_rwa_irb_calculations(sample_retail_positions, sample_config):
    """Test IRB RWA calculation accuracy"""
    result = compute_rwa_irb(sample_retail_positions, sample_config)
    
    # Check that RWA amounts are calculated correctly
    for _, row in result.iterrows():
        expected_rwa = row['ead'] * row['rwa_density']
        assert abs(row['rwa_amount'] - expected_rwa) < 0.01


def test_compute_rwa_irb_empty_dataframe(sample_config):
    """Test IRB RWA calculation with empty DataFrame"""
    empty_df = pd.DataFrame()
    
    result = compute_rwa_irb(empty_df, sample_config)
    
    assert result.empty
    assert 'entity_id' in result.columns


def test_compute_rwa_irb_total_rwa(sample_retail_positions, sample_config):
    """Test total IRB RWA calculation"""
    result = compute_rwa_irb(sample_retail_positions, sample_config)
    
    total_rwa = result['rwa_amount'].sum()
    
    # Total RWA should be positive
    assert total_rwa > 0
    
    # Should be less than total EAD * 12.5 (max risk weight)
    total_ead = sample_retail_positions['ead'].sum()
    assert total_rwa < total_ead * 12.5


def test_compute_rwa_irb_with_non_retail_filter(sample_config):
    """Test that non-retail positions are filtered correctly"""
    positions = pd.DataFrame({
        'entity_id': ['EU_SUB', 'EU_SUB'],
        'product_id': ['RETAIL_MORTGAGE', 'CORP_LOAN'],
        'exposure_class': ['retail', 'corporates'],
        'ead': [500000, 1000000],
        'pd': [0.02, 0.03],
        'lgd': [0.40, 0.45],
        'is_retail': [True, False],  # Second one is non-retail
        'stage': [1, 1]
    })
    
    result = compute_rwa_irb(positions, sample_config)
    
    # Should only process retail (first position)
    assert len(result) == 1
    assert result.iloc[0]['product_id'] == 'RETAIL_MORTGAGE'


def test_compute_rwa_irb_no_is_retail_column(sample_config):
    """Test IRB RWA calculation when is_retail column is missing"""
    positions = pd.DataFrame({
        'entity_id': ['EU_SUB'],
        'product_id': ['RETAIL_MORTGAGE'],
        'exposure_class': ['retail'],
        'ead': [500000],
        'pd': [0.02],
        'lgd': [0.40],
        'stage': [1]
    })
    
    result = compute_rwa_irb(positions, sample_config)
    
    # Should process all positions when is_retail is missing
    assert len(result) == 1
    assert result.iloc[0]['rwa_amount'] > 0


def test_compute_rwa_irb_default_pd_lgd(sample_config):
    """Test IRB RWA calculation with default PD and LGD"""
    positions = pd.DataFrame({
        'entity_id': ['EU_SUB'],
        'product_id': ['RETAIL_CONSUMER'],
        'exposure_class': ['retail'],
        'ead': [100000],
        'is_retail': [True],
        'stage': [1]
        # No pd or lgd columns
    })
    
    result = compute_rwa_irb(positions, sample_config)
    
    # Should use default values
    assert len(result) == 1
    assert result.iloc[0]['pd'] == 0.025  # Default PD
    assert result.iloc[0]['lgd'] == 0.45  # Default LGD
    assert result.iloc[0]['rwa_amount'] > 0


def test_compute_rwa_irb_maturity_mapping(sample_config):
    """Test that maturity is correctly mapped by product type"""
    positions = pd.DataFrame({
        'entity_id': ['EU_SUB', 'EU_SUB', 'EU_SUB'],
        'product_id': ['RETAIL_MORTGAGE', 'RETAIL_CONSUMER', 'RETAIL_CREDIT_CARDS'],
        'exposure_class': ['retail', 'retail', 'retail'],
        'ead': [500000, 200000, 100000],
        'pd': [0.02, 0.03, 0.05],
        'lgd': [0.40, 0.45, 0.60],
        'is_retail': [True, True, True],
        'stage': [1, 1, 1]
    })
    
    result = compute_rwa_irb(positions, sample_config)
    
    # Check maturity assignments
    mortgage_row = result[result['product_id'] == 'RETAIL_MORTGAGE'].iloc[0]
    assert mortgage_row['maturity'] == 15.0
    
    consumer_row = result[result['product_id'] == 'RETAIL_CONSUMER'].iloc[0]
    assert consumer_row['maturity'] == 3.0
    
    cards_row = result[result['product_id'] == 'RETAIL_CREDIT_CARDS'].iloc[0]
    assert cards_row['maturity'] == 1.0


def test_compute_rwa_irb_correlation_by_product(sample_retail_positions, sample_config):
    """Test that correlation varies by product type"""
    result = compute_rwa_irb(sample_retail_positions, sample_config)
    
    # Mortgage should have correlation 0.15
    mortgage_corr = result[result['product_id'] == 'RETAIL_MORTGAGE'].iloc[0]['correlation']
    assert mortgage_corr == 0.15
    
    # Credit cards should have correlation 0.04
    cards_corr = result[result['product_id'] == 'RETAIL_CREDIT_CARDS'].iloc[0]['correlation']
    assert cards_corr == 0.04
    
    # Consumer should have variable correlation based on PD
    consumer_corr = result[result['product_id'] == 'RETAIL_CONSUMER'].iloc[0]['correlation']
    assert consumer_corr >= 0.03  # Should be at or above floor

