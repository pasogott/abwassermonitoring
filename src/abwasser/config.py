"""Configuration management for wastewater monitoring."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class DataSourceConfig:
    """Configuration for a single data source."""

    url: str = ""
    delimiter: str = ";"
    date_column: str = "Datum"
    value_column: str | None = None
    group_column: str | None = None
    encoding: str = "utf-8"


@dataclass
class ViennaDataConfig:
    """Configuration for Vienna ViennaViz data source."""

    base_url: str = "https://stp.wien.gv.at/viennaviz/anonymous/chart"
    delimiter: str = ";"
    encoding: str = "utf-8"
    charts: dict[str, str] = field(default_factory=dict)


@dataclass
class ChartConfig:
    """Configuration for a chart type."""

    enabled: bool = True
    time_range_days: int = 90
    title: str = ""
    subtitle: str = ""
    chart_type: str = "line"
    rolling_window: int = 7
    weeks: int = 52
    colormap: str = "YlOrRd"


@dataclass
class VisualizationConfig:
    """Visualization settings."""

    width: int = 1080
    height: int = 1080
    dpi: int = 150
    font_family: str = "DejaVu Sans"
    charts: dict[str, ChartConfig] = field(default_factory=dict)


@dataclass
class StyleConfig:
    """Style settings."""

    background: str = "#FFFFFF"
    text: str = "#1A1A1A"
    grid: str = "#E5E5E5"
    title_size: int = 24
    label_size: int = 14
    tick_size: int = 12


@dataclass
class OutputConfig:
    """Output settings."""

    directory: Path = field(default_factory=lambda: Path("./output"))
    date_folders: bool = True
    latest_symlink: bool = True


@dataclass
class Config:
    """Main configuration container."""

    data_sources: dict[str, DataSourceConfig]
    vienna: ViennaDataConfig | None
    output: OutputConfig
    visualization: VisualizationConfig
    style: StyleConfig
    bundeslaender: dict[str, str]
    pathogens: dict[str, str]

    @classmethod
    def from_yaml(cls, path: Path) -> "Config":
        """Load configuration from YAML file."""
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "Config":
        """Create Config from dictionary."""
        # Parse data sources
        data_sources = {}
        for name, source_data in data.get("data_sources", {}).items():
            if isinstance(source_data, dict) and "url" in source_data:
                data_sources[name] = DataSourceConfig(
                    url=source_data["url"],
                    delimiter=source_data.get("delimiter", ";"),
                    date_column=source_data.get("date_column", "Datum"),
                    value_column=source_data.get("value_column"),
                    group_column=source_data.get("group_column"),
                    encoding=source_data.get("encoding", "utf-8"),
                )

        # Parse Vienna config
        vienna_data = data.get("data_sources", {}).get("vienna", {})
        vienna = None
        if vienna_data and "base_url" in vienna_data:
            vienna = ViennaDataConfig(
                base_url=vienna_data.get("base_url", ""),
                delimiter=vienna_data.get("delimiter", ";"),
                encoding=vienna_data.get("encoding", "utf-8"),
                charts=vienna_data.get("charts", {}),
            )

        # Parse output config
        output_data = data.get("output", {})
        output = OutputConfig(
            directory=Path(output_data.get("directory", "./output")),
            date_folders=output_data.get("date_folders", True),
            latest_symlink=output_data.get("latest_symlink", True),
        )

        # Parse visualization config
        viz_data = data.get("visualization", {})
        charts = {}
        for name, chart_data in viz_data.get("charts", {}).items():
            charts[name] = ChartConfig(
                enabled=chart_data.get("enabled", True),
                time_range_days=chart_data.get("time_range_days", 90),
                title=chart_data.get("title", ""),
                subtitle=chart_data.get("subtitle", ""),
                chart_type=chart_data.get("chart_type", "line"),
                rolling_window=chart_data.get("rolling_window", 7),
                weeks=chart_data.get("weeks", 52),
                colormap=chart_data.get("colormap", "YlOrRd"),
            )

        visualization = VisualizationConfig(
            width=viz_data.get("width", 1080),
            height=viz_data.get("height", 1080),
            dpi=viz_data.get("dpi", 150),
            font_family=viz_data.get("font_family", "DejaVu Sans"),
            charts=charts,
        )

        # Parse style config
        style_data = data.get("style", {})
        style = StyleConfig(
            background=style_data.get("background", "#FFFFFF"),
            text=style_data.get("text", "#1A1A1A"),
            grid=style_data.get("grid", "#E5E5E5"),
            title_size=style_data.get("title_size", 24),
            label_size=style_data.get("label_size", 14),
            tick_size=style_data.get("tick_size", 12),
        )

        return cls(
            data_sources=data_sources,
            vienna=vienna,
            output=output,
            visualization=visualization,
            style=style,
            bundeslaender=data.get("bundeslaender", {}),
            pathogens=data.get("pathogens", {}),
        )


def load_config(path: Path | None = None) -> Config:
    """Load configuration from file or use defaults."""
    if path is None:
        path = Path("config.yaml")

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    return Config.from_yaml(path)
