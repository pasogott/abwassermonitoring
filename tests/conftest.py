"""Pytest configuration and fixtures."""

import pytest
import pandas as pd
from pathlib import Path


@pytest.fixture
def sample_regional_data() -> pd.DataFrame:
    """Sample regional data for testing."""
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=10, freq="D"),
        "region": ["Wien"] * 10,
        "value": [100.0, 110.0, 105.0, 120.0, 115.0, 130.0, 125.0, 140.0, 135.0, 150.0],
    })


@pytest.fixture
def sample_national_data() -> pd.DataFrame:
    """Sample national data for testing."""
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=30, freq="D"),
        "value": [1000000 + i * 10000 for i in range(30)],
    })


@pytest.fixture
def config_path(tmp_path: Path) -> Path:
    """Create a temporary config file."""
    config_content = """
data_sources:
  regional:
    url: "https://example.com/test.csv"
    delimiter: ";"

output:
  directory: "{output_dir}"
  date_folders: false

visualization:
  width: 800
  height: 600
  dpi: 100

bundeslaender:
  Wien: "#E31A1C"

style:
  background: "#FFFFFF"
  text: "#1A1A1A"
""".format(output_dir=tmp_path / "output")

    config_file = tmp_path / "config.yaml"
    config_file.write_text(config_content)
    return config_file
