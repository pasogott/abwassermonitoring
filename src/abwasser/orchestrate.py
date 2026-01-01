"""Orchestration module for wastewater monitoring workflow."""

import json
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from . import fetch, visualize
from .config import Config, load_config

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def create_output_directory(config: Config) -> Path:
    """Create timestamped output directory.

    Args:
        config: Application configuration

    Returns:
        Path to the output directory for this run
    """
    base_dir = config.output.directory

    if config.output.date_folders:
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_dir = base_dir / date_str
    else:
        output_dir = base_dir

    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Output directory: %s", output_dir)

    return output_dir


def update_latest_symlink(config: Config, output_dir: Path) -> None:
    """Update the 'latest' symlink to point to the current output directory.

    Args:
        config: Application configuration
        output_dir: Path to the current output directory
    """
    if not config.output.latest_symlink:
        return

    latest_link = config.output.directory / "latest"

    # Remove existing symlink if present
    if latest_link.is_symlink():
        latest_link.unlink()
    elif latest_link.exists():
        logger.warning("'latest' exists but is not a symlink, skipping")
        return

    # Create new symlink (relative path)
    try:
        latest_link.symlink_to(output_dir.name)
        logger.info("Updated 'latest' symlink to %s", output_dir.name)
    except OSError as e:
        logger.warning("Failed to create symlink: %s", e)


def run(config_path: Path | None = None, verbose: bool = False) -> None:
    """Main entry point for the wastewater monitoring workflow.

    Args:
        config_path: Path to configuration file (default: config.yaml)
        verbose: Enable verbose logging
    """
    setup_logging(verbose)
    logger.info("Starting wastewater monitoring workflow")

    # Load configuration
    try:
        config = load_config(config_path)
        logger.info("Loaded configuration from %s", config_path or "config.yaml")
    except FileNotFoundError as e:
        logger.error("Configuration file not found: %s", e)
        raise

    # Create output directory
    output_dir = create_output_directory(config)

    # Fetch Vienna data only
    logger.info("Fetching Vienna data...")
    data = fetch.fetch_all(config)

    if not data:
        logger.error("No data fetched, aborting")
        return

    # Generate Vienna multi-pathogen chart only
    charts = config.visualization.charts
    if charts.get("vienna_pathogens") and charts["vienna_pathogens"].enabled:
        if "vienna" in data and data["vienna"]:
            logger.info("Generating Vienna multi-pathogen chart...")
            try:
                fig = visualize.create_multi_pathogen_chart(
                    data["vienna"],
                    config,
                    charts["vienna_pathogens"],
                )
                out_path = output_dir / "vienna_pathogens.png"
                visualize.save_figure(fig, out_path, config)
            except Exception as e:
                logger.error("Failed to generate Vienna chart: %s", e)

            # Export raw data as JSON for AI analysis
            logger.info("Exporting raw data as JSON...")
            try:
                export_data = export_vienna_data(data["vienna"])
                json_path = output_dir / "vienna_data.json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                logger.info("Exported data to %s", json_path)
            except Exception as e:
                logger.error("Failed to export data: %s", e)
        else:
            logger.error("Vienna multi-pathogen data not available")
            return

    # Update latest symlink
    update_latest_symlink(config, output_dir)

    logger.info("Workflow completed. Output saved to %s", output_dir)


def export_vienna_data(vienna_data: dict[str, pd.DataFrame]) -> dict:
    """Export Vienna pathogen data as structured JSON for AI analysis.

    Args:
        vienna_data: Dictionary of pathogen DataFrames

    Returns:
        Structured data ready for JSON export
    """
    export = {
        "generated_at": datetime.now().isoformat(),
        "period": {},
        "pathogens": {},
    }

    pathogen_map = {
        "sars_cov_2": "SARS-CoV-2",
        "influenza": "Influenza",
        "rsv": "RSV",
    }

    for key, label in pathogen_map.items():
        if key not in vienna_data or vienna_data[key].empty:
            continue

        df = vienna_data[key].copy()
        df = df.sort_values("date")

        # Get last 3 months of data
        date_max = df["date"].max()
        three_months_ago = date_max - pd.DateOffset(months=3)
        df_recent = df[df["date"] >= three_months_ago].copy()

        # Determine value column
        value_col = "rolling_avg" if "rolling_avg" in df.columns else "value"

        # Calculate statistics
        values = df_recent[value_col].dropna()
        current_value = values.iloc[-1] if len(values) > 0 else None
        prev_week_avg = values.iloc[-7:].mean() if len(values) >= 7 else None
        two_weeks_ago_avg = values.iloc[-14:-7].mean() if len(values) >= 14 else None

        # Week-over-week change
        wow_change = None
        if prev_week_avg and two_weeks_ago_avg and two_weeks_ago_avg > 0:
            wow_change = ((prev_week_avg - two_weeks_ago_avg) / two_weeks_ago_avg) * 100

        # Previous year comparison (by calendar week)
        current_year = date_max.year
        df["year"] = df["date"].dt.isocalendar().year
        df["week"] = df["date"].dt.isocalendar().week
        current_week = date_max.isocalendar().week

        prev_year_same_week = df[
            (df["year"] == current_year - 1) & (df["week"] == current_week)
        ]
        prev_year_value = None
        yoy_change = None
        if not prev_year_same_week.empty:
            prev_year_value = prev_year_same_week[value_col].iloc[0]
            if prev_year_value and prev_year_value > 0 and current_value:
                yoy_change = ((current_value - prev_year_value) / prev_year_value) * 100

        # Time series data (last 3 months)
        time_series = []
        for _, row in df_recent.iterrows():
            time_series.append(
                {
                    "date": row["date"].strftime("%Y-%m-%d"),
                    "value": float(row[value_col])
                    if pd.notna(row[value_col])
                    else None,
                }
            )

        wow_pct = round(wow_change, 1) if wow_change else None
        yoy_pct = round(yoy_change, 1) if yoy_change else None
        prev_yr = float(prev_year_value) if prev_year_value else None

        export["pathogens"][label] = {
            "current_value": float(current_value) if current_value else None,
            "current_date": date_max.strftime("%Y-%m-%d"),
            "unit": "Genkopien/Tag",
            "week_over_week_change_percent": wow_pct,
            "year_over_year_change_percent": yoy_pct,
            "previous_year_value": prev_yr,
            "statistics": {
                "min": float(values.min()) if len(values) > 0 else None,
                "max": float(values.max()) if len(values) > 0 else None,
                "mean": float(values.mean()) if len(values) > 0 else None,
            },
            "time_series": time_series,
        }

    # Set period info
    if export["pathogens"]:
        first_pathogen = list(export["pathogens"].values())[0]
        if first_pathogen["time_series"]:
            export["period"] = {
                "start": first_pathogen["time_series"][0]["date"],
                "end": first_pathogen["time_series"][-1]["date"],
            }

    return export
