"""Entry point for running as a module: python -m abwasser."""

import argparse
import sys
from pathlib import Path

from .orchestrate import run


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Austrian wastewater monitoring visualization",
        prog="python -m abwasser",
    )

    parser.add_argument(
        "-c", "--config",
        type=Path,
        default=None,
        help="Path to configuration file (default: config.yaml)",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    try:
        run(config_path=args.config, verbose=args.verbose)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
