"""
Unit tests for capital ratio calculations.
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from src.domain.credit_risk.capital import (
    compute_capital_ratios,
    compute_leverage_ratio
)


@pytest.fixture
def sample_capital_base():
    """Sample capital base for testing"""
    return {
        'cet1_capital': 1000000,
        'tier1_capital': 1000000,
        'total_capital': 1250000
    }


@pytest.fixture
def sample_buffers():
    """Sample regulatory buffers for testing"""
    return {
        'capital_conservation_buffer': 2.5,
        'countercyclical_buffer': 0.0,
        'systemic_buffer': 0.0
    }


def test_compute_capital_ratios_basic(sample_capital_base, sample_buffers):
    """Test basic capital ratio calculation"""
    rwa_total = 10000000
    
    result = compute_capital_ratios(rwa_total, sample_capital_base, sample_buffers)
    
    assert 'total_rwa' in result
    assert 'cet1_capital' in result
    assert 'tier1_capital' in result
    assert 'total_capital' in result
    assert 'cet1_ratio' in result
    assert 'tier1_ratio' in result
    assert 'total_capital_ratio' in result
    assert 'cet1_requirement' in result
    assert 'tier1_requirement' in result
    assert 'total_requirement' in result
    assert 'cet1_surplus' in result
    assert 'tier1_surplus' in result
    assert 'total_surplus' in result


def test_compute_capital_ratios_calculations(sample_capital_base, sample_buffers):
    """Test capital ratio calculation accuracy"""
    rwa_total = 10000000
    
    result = compute_capital_ratios(rwa_total, sample_capital_base, sample_buffers)
    
    # CET1 ratio = 1,000,000 / 10,000,000 * 100 = 10%
    assert result['cet1_ratio'] == 10.0
    
    # Tier 1 ratio = 1,000,000 / 10,000,000 * 100 = 10%
    assert result['tier1_ratio'] == 10.0
    
    # Total capital ratio = 1,250,000 / 10,000,000 * 100 = 12.5%
    assert result['total_capital_ratio'] == 12.5


def test_compute_capital_ratios_requirements(sample_capital_base, sample_buffers):
    """Test capital requirement calculations"""
    rwa_total = 10000000
    
    result = compute_capital_ratios(rwa_total, sample_capital_base, sample_buffers)
    
    # CET1 requirement = 4.5% + 2.5% (conservation buffer) = 7.0%
    assert result['cet1_requirement'] == 7.0
    
    # Tier 1 requirement = 6.0% + 2.5% = 8.5%
    assert result['tier1_requirement'] == 8.5
    
    # Total requirement = 8.0% + 2.5% = 10.5%
    assert result['total_requirement'] == 10.5


def test_compute_capital_ratios_surplus(sample_capital_base, sample_buffers):
    """Test capital surplus calculations"""
    rwa_total = 10000000
    
    result = compute_capital_ratios(rwa_total, sample_capital_base, sample_buffers)
    
    # CET1 surplus = 10.0% - 7.0% = 3.0%
    assert result['cet1_surplus'] == 3.0
    
    # Tier 1 surplus = 10.0% - 8.5% = 1.5%
    assert result['tier1_surplus'] == 1.5
    
    # Total surplus = 12.5% - 10.5% = 2.0%
    assert result['total_surplus'] == 2.0


def test_compute_capital_ratios_with_countercyclical_buffer(sample_capital_base):
    """Test capital ratios with countercyclical buffer"""
    rwa_total = 10000000
    buffers = {
        'capital_conservation_buffer': 2.5,
        'countercyclical_buffer': 1.0,  # Add 1% countercyclical
        'systemic_buffer': 0.0
    }
    
    result = compute_capital_ratios(rwa_total, sample_capital_base, buffers)
    
    # CET1 requirement = 4.5% + 2.5% + 1.0% = 8.0%
    assert result['cet1_requirement'] == 8.0
    
    # CET1 surplus = 10.0% - 8.0% = 2.0%
    assert result['cet1_surplus'] == 2.0


def test_compute_capital_ratios_with_systemic_buffer(sample_capital_base):
    """Test capital ratios with systemic buffer"""
    rwa_total = 10000000
    buffers = {
        'capital_conservation_buffer': 2.5,
        'countercyclical_buffer': 0.0,
        'systemic_buffer': 1.5  # Add 1.5% systemic buffer
    }
    
    result = compute_capital_ratios(rwa_total, sample_capital_base, buffers)
    
    # CET1 requirement = 4.5% + 2.5% + 1.5% = 8.5%
    assert result['cet1_requirement'] == 8.5
    
    # CET1 surplus = 10.0% - 8.5% = 1.5%
    assert result['cet1_surplus'] == 1.5


def test_compute_capital_ratios_zero_rwa():
    """Test capital ratios with zero RWA"""
    rwa_total = 0
    capital_base = {'cet1_capital': 1000000, 'tier1_capital': 1000000, 'total_capital': 1250000}
    buffers = {'capital_conservation_buffer': 2.5, 'countercyclical_buffer': 0.0, 'systemic_buffer': 0.0}
    
    result = compute_capital_ratios(rwa_total, capital_base, buffers)
    
    # All ratios should be 0
    assert result['cet1_ratio'] == 0
    assert result['tier1_ratio'] == 0
    assert result['total_capital_ratio'] == 0
    
    # Surplus should be negative (equal to requirement)
    assert result['cet1_surplus'] < 0
    assert result['tier1_surplus'] < 0
    assert result['total_surplus'] < 0


def test_compute_capital_ratios_negative_rwa():
    """Test capital ratios with negative RWA"""
    rwa_total = -1000000
    capital_base = {'cet1_capital': 1000000, 'tier1_capital': 1000000, 'total_capital': 1250000}
    buffers = {'capital_conservation_buffer': 2.5, 'countercyclical_buffer': 0.0, 'systemic_buffer': 0.0}
    
    result = compute_capital_ratios(rwa_total, capital_base, buffers)
    
    # Should handle gracefully
    assert result['cet1_ratio'] == 0


def test_compute_capital_ratios_default_tier1():
    """Test capital ratios with default tier1 capital"""
    rwa_total = 10000000
    capital_base = {'cet1_capital': 1000000}  # Only CET1 provided
    buffers = {'capital_conservation_buffer': 2.5, 'countercyclical_buffer': 0.0, 'systemic_buffer': 0.0}
    
    result = compute_capital_ratios(rwa_total, capital_base, buffers)
    
    # Tier 1 should default to CET1
    assert result['tier1_capital'] == 1000000
    assert result['tier1_ratio'] == 10.0


def test_compute_capital_ratios_default_total_capital():
    """Test capital ratios with default total capital"""
    rwa_total = 10000000
    capital_base = {'cet1_capital': 1000000, 'tier1_capital': 1000000}  # No total_capital
    buffers = {'capital_conservation_buffer': 2.5, 'countercyclical_buffer': 0.0, 'systemic_buffer': 0.0}
    
    result = compute_capital_ratios(rwa_total, capital_base, buffers)
    
    # Total capital should be estimated as tier1 * 1.25
    assert result['total_capital'] == 1250000
    assert result['total_capital_ratio'] == 12.5


def test_compute_capital_ratios_low_capital():
    """Test capital ratios with insufficient capital"""
    rwa_total = 10000000
    capital_base = {
        'cet1_capital': 500000,  # Only 5% CET1
        'tier1_capital': 500000,
        'total_capital': 600000
    }
    buffers = {'capital_conservation_buffer': 2.5, 'countercyclical_buffer': 0.0, 'systemic_buffer': 0.0}
    
    result = compute_capital_ratios(rwa_total, capital_base, buffers)
    
    # CET1 ratio = 5%
    assert result['cet1_ratio'] == 5.0
    
    # CET1 surplus should be negative (5% - 7% = -2%)
    assert result['cet1_surplus'] == -2.0


def test_compute_leverage_ratio_basic():
    """Test basic leverage ratio calculation"""
    tier1_capital = 1000000
    total_exposure = 20000000
    
    result = compute_leverage_ratio(tier1_capital, total_exposure)
    
    assert 'tier1_capital' in result
    assert 'total_exposure' in result
    assert 'leverage_ratio' in result
    assert 'minimum_requirement' in result
    assert 'surplus' in result


def test_compute_leverage_ratio_calculations():
    """Test leverage ratio calculation accuracy"""
    tier1_capital = 1000000
    total_exposure = 20000000
    
    result = compute_leverage_ratio(tier1_capital, total_exposure)
    
    # Leverage ratio = 1,000,000 / 20,000,000 * 100 = 5%
    assert result['leverage_ratio'] == 5.0
    
    # Surplus = 5% - 3% = 2%
    assert result['surplus'] == 2.0


def test_compute_leverage_ratio_custom_minimum():
    """Test leverage ratio with custom minimum requirement"""
    tier1_capital = 1000000
    total_exposure = 20000000
    minimum_requirement = 4.0
    
    result = compute_leverage_ratio(tier1_capital, total_exposure, minimum_requirement)
    
    assert result['minimum_requirement'] == 4.0
    # Surplus = 5% - 4% = 1%
    assert result['surplus'] == 1.0


def test_compute_leverage_ratio_zero_exposure():
    """Test leverage ratio with zero exposure"""
    tier1_capital = 1000000
    total_exposure = 0
    
    result = compute_leverage_ratio(tier1_capital, total_exposure)
    
    # Should handle gracefully
    assert result['leverage_ratio'] == 0
    assert result['surplus'] < 0  # Negative surplus


def test_compute_leverage_ratio_negative_exposure():
    """Test leverage ratio with negative exposure"""
    tier1_capital = 1000000
    total_exposure = -1000000
    
    result = compute_leverage_ratio(tier1_capital, total_exposure)
    
    # Should handle gracefully
    assert result['leverage_ratio'] == 0


def test_compute_leverage_ratio_below_minimum():
    """Test leverage ratio below minimum requirement"""
    tier1_capital = 500000
    total_exposure = 20000000
    
    result = compute_leverage_ratio(tier1_capital, total_exposure)
    
    # Leverage ratio = 500,000 / 20,000,000 * 100 = 2.5%
    assert result['leverage_ratio'] == 2.5
    
    # Surplus = 2.5% - 3% = -0.5%
    assert result['surplus'] == -0.5


def test_compute_leverage_ratio_high_capital():
    """Test leverage ratio with high capital"""
    tier1_capital = 2000000
    total_exposure = 20000000
    
    result = compute_leverage_ratio(tier1_capital, total_exposure)
    
    # Leverage ratio = 2,000,000 / 20,000,000 * 100 = 10%
    assert result['leverage_ratio'] == 10.0
    
    # Surplus = 10% - 3% = 7%
    assert result['surplus'] == 7.0


def test_compute_capital_ratios_rounding():
    """Test that capital ratios are properly rounded"""
    rwa_total = 10000000
    capital_base = {
        'cet1_capital': 1234567,
        'tier1_capital': 1234567,
        'total_capital': 1543209
    }
    buffers = {'capital_conservation_buffer': 2.5, 'countercyclical_buffer': 0.0, 'systemic_buffer': 0.0}
    
    result = compute_capital_ratios(rwa_total, capital_base, buffers)
    
    # Check that values are rounded to 2 decimal places
    assert isinstance(result['cet1_ratio'], float)
    assert len(str(result['cet1_ratio']).split('.')[-1]) <= 2 or result['cet1_ratio'] == int(result['cet1_ratio'])

