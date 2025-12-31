"""Tests for data processing module."""

import pandas as pd
import pytest

from abwasser import process


def test_parse_dates():
    """Test date parsing."""
    df = pd.DataFrame({
        "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "value": [1, 2, 3],
    })

    result = process.parse_dates(df)

    assert pd.api.types.is_datetime64_any_dtype(result["date"])
    assert result["date"].iloc[0].year == 2024


def test_filter_date_range(sample_regional_data):
    """Test date range filtering."""
    result = process.filter_date_range(sample_regional_data, days=5)

    # Should filter to recent data
    assert len(result) <= len(sample_regional_data)


def test_prepare_regional_data(sample_regional_data):
    """Test regional data preparation."""
    result = process.prepare_regional_data(sample_regional_data, days=365)

    # Should be a DataFrame with date index
    assert isinstance(result.index, pd.DatetimeIndex)


def test_prepare_trend_data(sample_national_data):
    """Test trend data preparation."""
    result = process.prepare_trend_data(sample_national_data, days=365, rolling_window=7)

    # Should have rolling_avg column
    assert "rolling_avg" in result.columns
    # Rolling avg should be calculated
    assert result["rolling_avg"].notna().any()


def test_calculate_statistics(sample_national_data):
    """Test statistics calculation."""
    stats = process.calculate_statistics(sample_national_data)

    assert "min" in stats
    assert "max" in stats
    assert "mean" in stats
    assert stats["min"] <= stats["max"]


def test_normalize_region_names():
    """Test region name normalization."""
    df = pd.DataFrame({
        "region": ["Wien", "Niederösterreich", "Kärnten"],
        "value": [1, 2, 3],
    })

    result = process.normalize_region_names(df)

    assert "Niederoesterreich" in result["region"].values
    assert "Kaernten" in result["region"].values
