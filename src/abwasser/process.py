"""Data processing module for wastewater monitoring."""

import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def parse_dates(df: pd.DataFrame, date_column: str = "date") -> pd.DataFrame:
    """Parse date column to datetime.

    Args:
        df: Input DataFrame
        date_column: Name of the date column

    Returns:
        DataFrame with parsed dates
    """
    df = df.copy()

    if date_column in df.columns:
        df[date_column] = pd.to_datetime(df[date_column], format="%Y-%m-%d")

    return df


def filter_date_range(
    df: pd.DataFrame,
    days: int,
    date_column: str = "date",
) -> pd.DataFrame:
    """Filter DataFrame to last N days.

    Args:
        df: Input DataFrame
        days: Number of days to include
        date_column: Name of the date column

    Returns:
        Filtered DataFrame
    """
    if date_column not in df.columns:
        return df

    cutoff = datetime.now() - timedelta(days=days)
    return df[df[date_column] >= cutoff].copy()


def prepare_regional_data(
    df: pd.DataFrame,
    days: int = 90,
) -> pd.DataFrame:
    """Prepare regional data for stacked area chart.

    Pivots data so that each region becomes a column.

    Args:
        df: Input DataFrame with columns: date, region, value
        days: Number of days to include

    Returns:
        DataFrame with date index and region columns
    """
    df = parse_dates(df)
    df = filter_date_range(df, days)

    if df.empty:
        logger.warning("No data after filtering")
        return df

    # Convert value column to numeric
    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # Pivot: rows=dates, columns=regions
    pivot = df.pivot_table(
        index="date",
        columns="region",
        values="value",
        aggfunc="mean",
    )

    # Sort by date
    pivot = pivot.sort_index()

    # Forward fill small gaps
    pivot = pivot.ffill(limit=3)

    logger.info(
        "Prepared regional data: %d dates, %d regions", len(pivot), len(pivot.columns)
    )
    return pivot


def prepare_trend_data(
    df: pd.DataFrame,
    days: int = 180,
    rolling_window: int = 7,
) -> pd.DataFrame:
    """Prepare national trend data with rolling average.

    Args:
        df: Input DataFrame with columns: date, value
        days: Number of days to include
        rolling_window: Window size for rolling average

    Returns:
        DataFrame with date, value, and rolling_avg columns
    """
    df = parse_dates(df)
    df = filter_date_range(df, days)

    if df.empty:
        logger.warning("No data after filtering")
        return df

    # Convert value column to numeric
    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # Sort by date
    df = df.sort_values("date")

    # Calculate rolling average
    df["rolling_avg"] = df["value"].rolling(window=rolling_window, min_periods=1).mean()

    logger.info("Prepared trend data: %d rows", len(df))
    return df


def prepare_heatmap_data(
    df: pd.DataFrame,
    weeks: int = 52,
) -> pd.DataFrame:
    """Prepare data for GitHub-style calendar heatmap.

    Args:
        df: Input DataFrame with columns: date, value
        weeks: Number of weeks to include

    Returns:
        DataFrame with week and weekday indices for heatmap
    """
    df = parse_dates(df)

    if df.empty:
        logger.warning("No data for heatmap")
        return df

    # Convert value column to numeric
    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # Filter to last N weeks
    days = weeks * 7
    df = filter_date_range(df, days)

    if df.empty:
        return df

    # Aggregate by date if multiple values per day
    df = df.groupby("date").agg({"value": "mean"}).reset_index()

    # Add week and weekday columns
    df["weekday"] = df["date"].dt.weekday  # 0=Monday, 6=Sunday
    df["week"] = df["date"].dt.isocalendar().week
    df["year"] = df["date"].dt.year

    # Create unique week identifier for proper ordering
    df["week_id"] = (df["year"] - df["year"].min()) * 53 + df["week"]

    # Pivot for heatmap: rows=weekday, columns=week
    pivot = df.pivot_table(
        index="weekday",
        columns="week_id",
        values="value",
        aggfunc="mean",
    )

    logger.info(
        "Prepared heatmap data: %d weekdays x %d weeks", len(pivot), len(pivot.columns)
    )
    return pivot


def get_latest_data(
    df: pd.DataFrame,
    date_column: str = "date",
) -> pd.DataFrame:
    """Get the most recent data point(s).

    Args:
        df: Input DataFrame
        date_column: Name of the date column

    Returns:
        DataFrame with only the latest date's data
    """
    df = parse_dates(df)

    if df.empty or date_column not in df.columns:
        return df

    latest_date = df[date_column].max()
    return df[df[date_column] == latest_date].copy()


def calculate_statistics(df: pd.DataFrame) -> dict:
    """Calculate summary statistics for the data.

    Args:
        df: Input DataFrame with value column

    Returns:
        Dictionary with statistics
    """
    if "value" not in df.columns:
        return {}

    values = pd.to_numeric(df["value"], errors="coerce").dropna()

    if values.empty:
        return {}

    return {
        "min": float(values.min()),
        "max": float(values.max()),
        "mean": float(values.mean()),
        "median": float(values.median()),
        "std": float(values.std()),
        "latest": float(values.iloc[-1]) if len(values) > 0 else None,
    }


def normalize_region_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize Austrian region names.

    Handles variations in spelling and encoding.

    Args:
        df: Input DataFrame with region column

    Returns:
        DataFrame with normalized region names
    """
    if "region" not in df.columns:
        return df

    df = df.copy()

    # Mapping of variations to standard names
    # Includes UTF-8 encoding issues and proper German names
    name_map = {
        # Proper German names
        "Niederösterreich": "Niederoesterreich",
        "Oberösterreich": "Oberoesterreich",
        "Kärnten": "Kaernten",
        "Österreich": "Oesterreich",
        # Encoding issues (mojibake from latin-1 read as utf-8)
        "NiederÃ¶sterreich": "Niederoesterreich",
        "OberÃ¶sterreich": "Oberoesterreich",
        "KÃ¤rnten": "Kaernten",
        "Ãsterreich": "Oesterreich",
    }

    df["region"] = df["region"].replace(name_map)
    return df


def interpolate_missing(
    df: pd.DataFrame,
    method: str = "linear",
    limit: int = 3,
) -> pd.DataFrame:
    """Interpolate missing values in the DataFrame.

    Args:
        df: Input DataFrame
        method: Interpolation method
        limit: Maximum number of consecutive NaNs to fill

    Returns:
        DataFrame with interpolated values
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    for col in numeric_cols:
        df[col] = df[col].interpolate(method=method, limit=limit)

    return df
