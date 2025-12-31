"""Data fetching module for wastewater monitoring."""

import io
import logging
import time
from typing import Any

import pandas as pd
import requests

from .config import Config, DataSourceConfig

logger = logging.getLogger(__name__)

# Request settings
TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2


class FetchError(Exception):
    """Error during data fetching."""


def fetch_csv(
    url: str,
    delimiter: str = ";",
    encoding: str = "utf-8",
    retries: int = MAX_RETRIES,
) -> pd.DataFrame:
    """Fetch CSV from URL and return DataFrame.

    Args:
        url: URL to fetch CSV from
        delimiter: CSV delimiter character
        encoding: Character encoding
        retries: Number of retry attempts

    Returns:
        DataFrame with parsed CSV data

    Raises:
        FetchError: If fetching fails after all retries
    """
    last_error: Exception | None = None

    for attempt in range(retries):
        try:
            logger.info("Fetching %s (attempt %d/%d)", url, attempt + 1, retries)

            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status()

            # Parse CSV from response content
            content = response.content.decode(encoding)
            df = pd.read_csv(
                io.StringIO(content),
                delimiter=delimiter,
                encoding=encoding,
            )

            logger.info("Successfully fetched %d rows from %s", len(df), url)
            return df

        except requests.RequestException as e:
            last_error = e
            logger.warning("Fetch attempt %d failed: %s", attempt + 1, e)

            if attempt < retries - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))

    msg = f"Failed to fetch {url} after {retries} attempts"
    raise FetchError(msg) from last_error


def fetch_data_source(source: DataSourceConfig) -> pd.DataFrame:
    """Fetch data from a configured source.

    Args:
        source: Data source configuration

    Returns:
        DataFrame with fetched data
    """
    return fetch_csv(
        url=source.url,
        delimiter=source.delimiter,
        encoding=source.encoding,
    )


def fetch_regional_data(config: Config) -> pd.DataFrame:
    """Fetch regional (Bundeslaender) data.

    Args:
        config: Application configuration

    Returns:
        DataFrame with regional data
    """
    source = config.data_sources.get("regional")
    if source is None:
        raise FetchError("Regional data source not configured")

    df = fetch_data_source(source)

    # Standardize column names
    if source.date_column in df.columns:
        df = df.rename(columns={source.date_column: "date"})

    if source.group_column and source.group_column in df.columns:
        df = df.rename(columns={source.group_column: "region"})

    if source.value_column and source.value_column in df.columns:
        df = df.rename(columns={source.value_column: "value"})

    return df


def fetch_national_data(config: Config) -> pd.DataFrame:
    """Fetch national monitoring data.

    Args:
        config: Application configuration

    Returns:
        DataFrame with national data
    """
    source = config.data_sources.get("national")
    if source is None:
        raise FetchError("National data source not configured")

    df = fetch_data_source(source)

    # Standardize column names
    if source.date_column in df.columns:
        df = df.rename(columns={source.date_column: "date"})

    if source.value_column:
        # Handle column name that might have special characters
        for col in df.columns:
            if source.value_column in col or "Gesamtvirenfracht" in col:
                df = df.rename(columns={col: "value"})
                break

    return df


def fetch_variants_data(config: Config) -> pd.DataFrame:
    """Fetch variants data.

    Args:
        config: Application configuration

    Returns:
        DataFrame with variants data
    """
    source = config.data_sources.get("variants")
    if source is None:
        raise FetchError("Variants data source not configured")

    return fetch_data_source(source)


def fetch_vienna_data(config: Config) -> dict[str, pd.DataFrame] | None:
    """Fetch Vienna multi-pathogen data from ViennaViz API.

    Args:
        config: Application configuration

    Returns:
        Dictionary of DataFrames by pathogen, or None if not available
    """
    if config.vienna is None:
        logger.warning("Vienna data source not configured")
        return None

    result: dict[str, pd.DataFrame] = {}

    for pathogen, chart_id in config.vienna.charts.items():
        try:
            url = f"{config.vienna.base_url}/{chart_id}/dataSelection?includeBom=1"
            logger.info("Fetching Vienna %s data from %s", pathogen, url)

            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status()

            # Parse CSV - ViennaViz uses semicolon delimiter and comma as decimal
            content = response.content.decode(config.vienna.encoding)
            df = pd.read_csv(
                io.StringIO(content),
                delimiter=config.vienna.delimiter,
                decimal=",",
                thousands=".",
            )

            # Convert to long format with date and value columns
            df_long = _parse_vienna_csv(df, pathogen)
            if df_long is not None and not df_long.empty:
                result[pathogen] = df_long
                logger.info("Fetched Vienna %s: %d rows", pathogen, len(df_long))

        except requests.RequestException as e:
            logger.warning("Failed to fetch Vienna %s data: %s", pathogen, e)
        except Exception as e:
            logger.warning("Error processing Vienna %s data: %s", pathogen, e)

    return result if result else None


def _parse_vienna_csv(df: pd.DataFrame, pathogen: str) -> pd.DataFrame | None:
    """Parse ViennaViz CSV format to standard long format.

    ViennaViz CSVs have format:
    - First column: KW (Kalenderwoche, e.g., "KW 27")
    - Other columns: Season data (e.g., "2023/24", "2024/25", "2025/26")

    Args:
        df: Raw DataFrame from ViennaViz
        pathogen: Name of the pathogen

    Returns:
        DataFrame with columns: date, value, season, pathogen
    """
    if df.empty:
        return None

    # Get the first column name (should be empty or KW identifier)
    kw_col = df.columns[0]

    # Melt the DataFrame to long format
    df_melted = df.melt(
        id_vars=[kw_col],
        var_name="season",
        value_name="value",
    )

    # Rename KW column
    df_melted = df_melted.rename(columns={kw_col: "kw"})

    # Remove empty values
    df_melted = df_melted.dropna(subset=["value"])
    df_melted = df_melted[df_melted["value"] != ""]

    # Convert value to numeric
    df_melted["value"] = pd.to_numeric(df_melted["value"], errors="coerce")
    df_melted = df_melted.dropna(subset=["value"])

    # Add pathogen column
    df_melted["pathogen"] = pathogen

    # Convert KW + Season to approximate date
    df_melted["date"] = df_melted.apply(
        lambda row: _kw_season_to_date(row["kw"], row["season"]),
        axis=1,
    )
    df_melted = df_melted.dropna(subset=["date"])

    # Remove duplicates - keep the most recent season's data for overlapping weeks
    df_melted = df_melted.sort_values(["date", "season"], ascending=[True, False])
    df_melted = df_melted.drop_duplicates(subset=["date", "pathogen"], keep="first")

    # Filter out future dates
    today = pd.Timestamp.now().normalize()
    df_melted = df_melted[df_melted["date"] <= today]

    return df_melted[["date", "value", "season", "pathogen"]]


def _kw_season_to_date(kw_str: str, season: str) -> pd.Timestamp | None:
    """Convert KW string and season to approximate date.

    Args:
        kw_str: Calendar week string (e.g., "KW 27")
        season: Season string (e.g., "2024/25")

    Returns:
        Approximate date (Sunday of that week)
    """
    import re
    from datetime import datetime

    # Extract week number
    match = re.search(r"(\d+)", str(kw_str))
    if not match:
        return None
    week = int(match.group(1))

    # Extract year from season
    match = re.search(r"(\d{4})/(\d{2})", str(season))
    if not match:
        return None

    year_start = int(match.group(1))
    year_end = 2000 + int(match.group(2))

    # Determine which year the week belongs to
    # Weeks 27-52 belong to first year, weeks 1-26 to second year
    if week >= 27:
        year = year_start
    else:
        year = year_end

    try:
        # Get the Sunday of that ISO week
        date = datetime.strptime(f"{year}-W{week:02d}-7", "%G-W%V-%u")
        return pd.Timestamp(date)
    except ValueError:
        return None


def fetch_all(config: Config) -> dict[str, Any]:
    """Fetch all configured data sources.

    Args:
        config: Application configuration

    Returns:
        Dictionary with all fetched data
    """
    data: dict[str, Any] = {}

    # Fetch regional data
    try:
        data["regional"] = fetch_regional_data(config)
        logger.info("Regional data: %d rows", len(data["regional"]))
    except FetchError as e:
        logger.error("Failed to fetch regional data: %s", e)

    # Fetch national data
    try:
        data["national"] = fetch_national_data(config)
        logger.info("National data: %d rows", len(data["national"]))
    except FetchError as e:
        logger.error("Failed to fetch national data: %s", e)

    # Fetch variants data
    try:
        data["variants"] = fetch_variants_data(config)
        logger.info("Variants data: %d rows", len(data["variants"]))
    except FetchError as e:
        logger.error("Failed to fetch variants data: %s", e)

    # Fetch Vienna data
    vienna_data = fetch_vienna_data(config)
    if vienna_data:
        data["vienna"] = vienna_data

    return data
