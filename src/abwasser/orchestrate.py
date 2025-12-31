"""Orchestration module for wastewater monitoring workflow."""

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from . import fetch, process, visualize
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

    # Fetch all data
    logger.info("Fetching data from sources...")
    data = fetch.fetch_all(config)

    if not data:
        logger.error("No data fetched, aborting")
        return

    # Process and generate charts
    charts = config.visualization.charts

    # Regional comparison chart
    if charts.get("regional") and charts["regional"].enabled:
        if "regional" in data:
            logger.info("Generating regional comparison chart...")
            try:
                regional_processed = process.prepare_regional_data(
                    data["regional"],
                    days=charts["regional"].time_range_days,
                )
                fig = visualize.create_regional_chart(
                    regional_processed,
                    config,
                    charts["regional"],
                )
                out_path = output_dir / "regional_comparison.png"
                visualize.save_figure(fig, out_path, config)
            except Exception as e:
                logger.error("Failed to generate regional chart: %s", e)
        else:
            logger.warning("No regional data available")

    # National trend chart
    if charts.get("trend") and charts["trend"].enabled:
        if "national" in data:
            logger.info("Generating national trend chart...")
            try:
                trend_processed = process.prepare_trend_data(
                    data["national"],
                    days=charts["trend"].time_range_days,
                    rolling_window=charts["trend"].rolling_window,
                )
                fig = visualize.create_trend_chart(
                    trend_processed,
                    config,
                    charts["trend"],
                )
                out_path = output_dir / "national_trend.png"
                visualize.save_figure(fig, out_path, config)
            except Exception as e:
                logger.error("Failed to generate trend chart: %s", e)
        else:
            logger.warning("No national data available")

    # Heatmap calendar
    if charts.get("heatmap") and charts["heatmap"].enabled:
        if "regional" in data:
            logger.info("Generating heatmap calendar...")
            try:
                # Use national aggregate for heatmap
                regions = ["Oesterreich", "Oesterreich"]
                national_df = data["regional"][
                    data["regional"]["region"].isin(regions)
                ]
                if national_df.empty:
                    # Fallback: aggregate all regions
                    national_df = (
                        data["regional"]
                        .groupby("date")
                        .agg({"value": "mean"})
                        .reset_index()
                    )

                heatmap_processed = process.prepare_heatmap_data(
                    national_df,
                    weeks=charts["heatmap"].weeks,
                )
                fig = visualize.create_heatmap_chart(
                    heatmap_processed,
                    config,
                    charts["heatmap"],
                )
                out_path = output_dir / "heatmap_calendar.png"
                visualize.save_figure(fig, out_path, config)
            except Exception as e:
                logger.error("Failed to generate heatmap: %s", e)

    # Vienna multi-pathogen chart
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
        else:
            logger.info("Vienna multi-pathogen data not available yet")

    # Individual Bundesland charts
    if "regional" in data:
        logger.info("Generating individual Bundesland charts...")

        # Create subdirectory for Bundesland charts
        bundesland_dir = output_dir / "bundeslaender"
        bundesland_dir.mkdir(exist_ok=True)

        # Normalize region names in the data
        regional_df = process.normalize_region_names(data["regional"])
        regions = regional_df["region"].unique()

        # List of Bundeslaender to generate charts for (excluding national aggregate)
        bundeslaender = [
            "Wien",
            "Niederoesterreich",
            "Oberoesterreich",
            "Salzburg",
            "Tirol",
            "Vorarlberg",
            "Kaernten",
            "Steiermark",
            "Burgenland",
        ]

        for bundesland in bundeslaender:
            if bundesland not in regions:
                logger.warning("No data for %s", bundesland)
                continue

            try:
                # Filter data for this Bundesland
                bl_data = regional_df[regional_df["region"] == bundesland].copy()

                if bl_data.empty:
                    logger.warning("Empty data for %s", bundesland)
                    continue

                # Prepare data: parse dates and set as index
                bl_data = process.parse_dates(bl_data)
                bl_data = bl_data.sort_values("date")

                # Filter to time range
                chart_cfg = charts.get("regional", {})
                if hasattr(chart_cfg, "time_range_days"):
                    time_range = chart_cfg.time_range_days
                else:
                    time_range = 90
                bl_data = process.filter_date_range(bl_data, days=time_range)

                # Convert to numeric and set index
                bl_data["value"] = pd.to_numeric(bl_data["value"], errors="coerce")
                bl_series = bl_data.set_index("date")["value"]

                # Generate chart
                fig = visualize.create_bundesland_chart(
                    bl_series,
                    bundesland,
                    config,
                    virus="SARS-CoV-2",
                    date_range_days=time_range,
                )

                # Save with lowercase filename
                filename = f"{bundesland.lower()}.png"
                out_path = bundesland_dir / filename
                visualize.save_figure(fig, out_path, config)

                logger.info("Generated chart for %s", bundesland)

            except Exception as e:
                logger.error("Failed to generate chart for %s: %s", bundesland, e)

        logger.info("Bundesland charts saved to %s", bundesland_dir)

    # Summary chart (always generate if we have data)
    if "regional" in data or "national" in data:
        logger.info("Generating summary chart...")
        try:
            regional_processed = pd.DataFrame()
            trend_processed = pd.DataFrame()

            if "regional" in data:
                regional_processed = process.prepare_regional_data(
                    data["regional"], days=90
                )

            if "national" in data:
                trend_processed = process.prepare_trend_data(
                    data["national"], days=180
                )

            fig = visualize.create_summary_chart(
                regional_processed,
                trend_processed,
                config,
            )
            visualize.save_figure(fig, output_dir / "summary.png", config)
        except Exception as e:
            logger.error("Failed to generate summary chart: %s", e)

    # Update latest symlink
    update_latest_symlink(config, output_dir)

    logger.info("Workflow completed. Output saved to %s", output_dir)
