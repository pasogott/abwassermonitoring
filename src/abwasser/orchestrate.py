"""Orchestration module for wastewater monitoring workflow."""

import logging
from datetime import datetime
from pathlib import Path

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
        else:
            logger.error("Vienna multi-pathogen data not available")
            return

    # Update latest symlink
    update_latest_symlink(config, output_dir)

    logger.info("Workflow completed. Output saved to %s", output_dir)
