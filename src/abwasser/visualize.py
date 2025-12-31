"""Visualization module with Alpine Editorial design system."""

import logging
from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.patches import Rectangle

from .config import ChartConfig, Config
from .design import (
    BUNDESLAND_ACCENTS,
    BUNDESLAND_NAMES,
    COLORS,
    LAYOUT,
    TYPOGRAPHY,
    VIRUS_CONFIG,
)

logger = logging.getLogger(__name__)


def add_year_annotations(ax: plt.Axes, date_min: pd.Timestamp, date_max: pd.Timestamp) -> None:
    """Add year labels in background and dashed lines between years.

    Args:
        ax: Matplotlib axes
        date_min: Start date
        date_max: End date
    """
    years_in_range = range(date_min.year, date_max.year + 1)
    for year in years_in_range:
        year_start = pd.Timestamp(year=year, month=1, day=1)
        year_end = pd.Timestamp(year=year, month=12, day=31)
        # Clip to data range
        vis_start = max(year_start, date_min)
        vis_end = min(year_end, date_max)
        if vis_start < vis_end:
            mid_point = vis_start + (vis_end - vis_start) / 2
            ax.text(
                mid_point,
                0.5,
                str(year),
                transform=ax.get_xaxis_transform(),
                ha="center",
                va="center",
                fontsize=48,
                fontweight=300,
                color="#E0E0E0",
                zorder=0,
            )

        # Add dashed vertical line at year boundary (Jan 1)
        if year_start > date_min and year_start <= date_max:
            ax.axvline(
                x=year_start,
                color="#CCCCCC",
                linestyle="--",
                linewidth=1.5,
                zorder=1,
            )


def apply_editorial_style() -> None:
    """Apply the Alpine Editorial style globally."""
    plt.rcParams.update({
        # Canvas
        "figure.facecolor": COLORS["canvas"],
        "axes.facecolor": COLORS["panel"],
        "savefig.facecolor": COLORS["canvas"],

        # Typography
        "font.family": TYPOGRAPHY["body_family"],
        "font.size": 12,
        "axes.titlesize": 16,
        "axes.titleweight": 600,
        "axes.labelsize": 12,
        "axes.labelcolor": COLORS["text_secondary"],

        # Grid
        "axes.grid": True,
        "grid.color": COLORS["grid"],
        "grid.alpha": LAYOUT["grid_alpha"],
        "grid.linestyle": LAYOUT["grid_style"],
        "grid.linewidth": LAYOUT["grid_linewidth"],

        # Spines
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": True,
        "axes.spines.bottom": True,
        "axes.linewidth": 1.2,
        "axes.edgecolor": COLORS["grid"],

        # Ticks
        "xtick.color": COLORS["text_muted"],
        "ytick.color": COLORS["text_muted"],
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,

        # Legend
        "legend.frameon": False,
        "legend.fontsize": 11,
    })


def create_figure_with_margins() -> tuple[plt.Figure, plt.Axes]:
    """Create a figure with Alpine Editorial margins."""
    fig = plt.figure(
        figsize=LAYOUT["figure_size"],
        dpi=LAYOUT["dpi"],
        facecolor=COLORS["canvas"],
    )

    ax = fig.add_axes([
        LAYOUT["margin_left"],
        LAYOUT["margin_bottom"],
        1 - LAYOUT["margin_left"] - LAYOUT["margin_right"],
        1 - LAYOUT["margin_top"] - LAYOUT["margin_bottom"],
    ])

    ax.set_facecolor(COLORS["panel"])
    return fig, ax


def add_accent_bar(fig: plt.Figure, color: str) -> None:
    """Add the Bundesland identity accent bar."""
    accent_bar = Rectangle(
        (0, LAYOUT["accent_bar_y"]),
        LAYOUT["accent_bar_width"],
        LAYOUT["accent_bar_height"],
        transform=fig.transFigure,
        color=color,
        clip_on=False,
    )
    fig.add_artist(accent_bar)


def add_header(
    fig: plt.Figure,
    title: str,
    subtitle: str,
    current_value: float | None = None,
    value_color: str = COLORS["text_primary"],
) -> None:
    """Add header with title, subtitle, and optional current value."""
    # Main title
    fig.text(
        0.03, 0.95,
        title.upper(),
        fontsize=TYPOGRAPHY["title_size"],
        fontweight=TYPOGRAPHY["title_weight"],
        color=COLORS["text_primary"],
        fontfamily=TYPOGRAPHY["title_family"],
    )

    # Subtitle
    fig.text(
        0.03, 0.905,
        subtitle,
        fontsize=TYPOGRAPHY["body_size"],
        color=COLORS["text_secondary"],
    )

    # Current value (right-aligned)
    if current_value is not None:
        fig.text(
            0.97, 0.91,
            f"{current_value:.1f}",
            fontsize=TYPOGRAPHY["mono_size"],
            fontweight=700,
            color=value_color,
            ha="right",
            fontfamily=TYPOGRAPHY["mono_family"],
        )


def add_footer(
    fig: plt.Figure,
    trend_pct: float | None = None,
    date_str: str | None = None,
) -> None:
    """Add footer with trend indicator and data source."""
    # Trend indicator
    if trend_pct is not None:
        if trend_pct > 5:
            trend_color = COLORS["rising"]
            trend_arrow = "^"
        elif trend_pct < -5:
            trend_color = COLORS["falling"]
            trend_arrow = "v"
        else:
            trend_color = COLORS["stable"]
            trend_arrow = "-"

        trend_text = f"{trend_arrow} {abs(trend_pct):.0f}% vs. Vorwoche"

        fig.text(
            0.03, 0.04,
            trend_text,
            fontsize=14,
            fontweight=600,
            color=trend_color,
        )

    # Date and source
    if date_str is None:
        date_str = datetime.now().strftime("%d.%m.%Y")

    fig.text(
        0.97, 0.04,
        f"Stand: {date_str}  |  AGES Abwassermonitoring",
        fontsize=10,
        color=COLORS["text_muted"],
        ha="right",
    )


def save_figure(fig: plt.Figure, path: Path, config: Config | None = None) -> None:
    """Save figure with optimized settings."""
    fig.savefig(
        path,
        dpi=LAYOUT["dpi"],
        bbox_inches="tight",
        pad_inches=0.1,
        facecolor=COLORS["canvas"],
        edgecolor="none",
    )
    plt.close(fig)
    logger.info("Saved figure to %s", path)


def create_bundesland_chart(
    data: pd.DataFrame,
    bundesland: str,
    config: Config,
    virus: str = "SARS-CoV-2",
    date_range_days: int = 90,
) -> plt.Figure:
    """Create a publication-quality chart for a single Bundesland.

    Features:
    - Colored accent bar for Bundesland identity
    - Elegant typography hierarchy
    - Trend indicator with directional coloring
    - Subtle area fill under line
    - Clean grid with dashed lines
    """
    apply_editorial_style()
    fig, ax = create_figure_with_margins()

    # Get colors
    virus_color = VIRUS_CONFIG.get(virus, {}).get("color", COLORS["text_primary"])
    accent_color = BUNDESLAND_ACCENTS.get(bundesland, COLORS["text_muted"])
    display_name = BUNDESLAND_NAMES.get(bundesland, bundesland)

    # Prepare data
    if data.empty:
        ax.text(
            0.5, 0.5, "Keine Daten verfugbar",
            ha="center", va="center",
            fontsize=16, color=COLORS["text_muted"],
            transform=ax.transAxes,
        )
        add_accent_bar(fig, accent_color)
        add_header(fig, display_name, f"{virus}  |  Keine Daten")
        return fig

    dates = data.index if hasattr(data, "index") else range(len(data))
    values = data.values.flatten() if hasattr(data, "values") else data

    # Area fill
    ax.fill_between(
        dates, values,
        alpha=LAYOUT["area_alpha"],
        color=virus_color,
        linewidth=0,
    )

    # Main line
    ax.plot(
        dates, values,
        color=virus_color,
        linewidth=LAYOUT["line_width"],
        solid_capstyle="round",
        solid_joinstyle="round",
    )

    # Latest value dot
    ax.scatter(
        [dates[-1]], [values[-1]],
        color=virus_color,
        s=LAYOUT["scatter_size"],
        zorder=5,
        edgecolors="white",
        linewidths=LAYOUT["scatter_edge_width"],
    )

    # Y-axis starts at 0
    ax.set_ylim(bottom=0)

    # Format y-axis label
    unit = VIRUS_CONFIG.get(virus, {}).get("unit", "Genkopien / EW / Tag (Mio.)")
    ax.set_ylabel(unit, fontsize=11, color=COLORS["text_secondary"])

    # Date formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0, interval=2))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # Calculate trend (last week vs previous week)
    trend_pct = None
    if len(values) >= 14:
        last_week = values[-7:].mean()
        prev_week = values[-14:-7].mean()
        if prev_week > 0:
            trend_pct = ((last_week - prev_week) / prev_week) * 100

    # Add visual elements
    add_accent_bar(fig, accent_color)

    subtitle = f"{virus}  |  Letzte {date_range_days} Tage"
    current_value = float(values[-1]) if len(values) > 0 else None
    add_header(fig, display_name, subtitle, current_value, virus_color)

    latest_date = None
    if hasattr(dates, "__getitem__") and len(dates) > 0:
        try:
            latest_date = pd.Timestamp(dates[-1]).strftime("%d.%m.%Y")
        except (TypeError, ValueError):
            latest_date = None

    add_footer(fig, trend_pct, latest_date)

    return fig


def create_regional_chart(
    data: pd.DataFrame,
    config: Config,
    chart_config: ChartConfig,
) -> plt.Figure:
    """Create stacked area chart comparing all Bundeslaender."""
    apply_editorial_style()
    fig, ax = create_figure_with_margins()

    if data.empty:
        ax.text(
            0.5, 0.5, "Keine Daten verfugbar",
            ha="center", va="center",
            fontsize=16, color=COLORS["text_muted"],
            transform=ax.transAxes,
        )
        add_header(fig, "Osterreich", "SARS-CoV-2 nach Bundesland")
        return fig

    # Limit to max 2 years back
    date_max = data.index.max()
    two_years_ago = date_max - pd.DateOffset(years=2)
    data = data[data.index >= two_years_ago]

    # Get regions (exclude national aggregate)
    regions = [
        col for col in data.columns
        if col not in ["Oesterreich", "Osterreich"]
        and col in BUNDESLAND_ACCENTS
    ]

    if not regions:
        regions = [col for col in data.columns if col in BUNDESLAND_ACCENTS]

    plot_data = data[[r for r in regions if r in data.columns]]

    if plot_data.empty:
        ax.text(
            0.5, 0.5, "Keine Daten verfugbar",
            ha="center", va="center",
            fontsize=16, color=COLORS["text_muted"],
            transform=ax.transAxes,
        )
        return fig

    # Colors for stacked area
    region_colors = [
        BUNDESLAND_ACCENTS.get(col, "#999999") for col in plot_data.columns
    ]

    # Create stacked area chart
    ax.stackplot(
        plot_data.index,
        [plot_data[col].fillna(0) for col in plot_data.columns],
        labels=[BUNDESLAND_NAMES.get(col, col) for col in plot_data.columns],
        colors=region_colors,
        alpha=0.85,
    )

    # Add line-end labels for each region at the last data point
    cumsum = 0
    last_idx = plot_data.index[-1]
    for i, col in enumerate(plot_data.columns):
        last_val = plot_data[col].fillna(0).iloc[-1]
        y_pos = cumsum + last_val / 2  # Position at center of that region's slice
        cumsum += last_val

        # Only show label if the slice is large enough
        if last_val > plot_data.sum(axis=1).iloc[-1] * 0.03:
            ax.annotate(
                BUNDESLAND_NAMES.get(col, col)[:3],  # Abbreviated name
                xy=(last_idx, y_pos),
                xytext=(5, 0),
                textcoords="offset points",
                fontsize=8,
                color=region_colors[i],
                fontweight=600,
                va="center",
            )

    # Y-axis
    ax.set_ylim(bottom=0)
    ax.set_ylabel(
        "Genkopien / EW / Tag (Mio.)", fontsize=11, color=COLORS["text_secondary"]
    )

    # Add year annotations
    add_year_annotations(ax, plot_data.index.min(), plot_data.index.max())

    # Date formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0, interval=2))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # Legend (keep for reference but smaller)
    ax.legend(
        loc="upper left",
        bbox_to_anchor=(0, 1),
        fontsize=8,
        frameon=False,
        ncol=3,
    )

    # Header
    add_accent_bar(fig, COLORS["rising"])
    subtitle = "SARS-CoV-2  |  Letzte 2 Jahre"
    add_header(fig, "Osterreich", subtitle)

    # Footer
    latest_date = None
    if len(plot_data) > 0:
        try:
            latest_date = pd.Timestamp(plot_data.index[-1]).strftime("%d.%m.%Y")
        except (TypeError, ValueError):
            pass
    add_footer(fig, date_str=latest_date)

    plt.tight_layout(rect=[0, 0.05, 0.85, 0.88])
    return fig


def create_trend_chart(
    data: pd.DataFrame,
    config: Config,
    chart_config: ChartConfig,
) -> plt.Figure:
    """Create line chart with national trend."""
    apply_editorial_style()
    fig, ax = create_figure_with_margins()

    if data.empty:
        ax.text(
            0.5, 0.5, "Keine Daten verfugbar",
            ha="center", va="center",
            fontsize=16, color=COLORS["text_muted"],
            transform=ax.transAxes,
        )
        add_header(fig, "Nationaler Trend", "SARS-CoV-2 Virenlast")
        return fig

    # Limit to max 2 years back
    date_max = data["date"].max()
    two_years_ago = date_max - pd.DateOffset(years=2)
    data = data[data["date"] >= two_years_ago].copy()

    if data.empty:
        ax.text(
            0.5, 0.5, "Keine Daten verfugbar",
            ha="center", va="center",
            fontsize=16, color=COLORS["text_muted"],
            transform=ax.transAxes,
        )
        add_header(fig, "Nationaler Trend", "SARS-CoV-2 Virenlast")
        return fig

    virus_color = VIRUS_CONFIG["SARS-CoV-2"]["color"]

    # Plot raw values as light line
    if "value" in data.columns:
        ax.plot(
            data["date"],
            data["value"],
            color=virus_color,
            alpha=0.25,
            linewidth=1.5,
        )

    # Plot rolling average as main line
    if "rolling_avg" in data.columns:
        ax.plot(
            data["date"],
            data["rolling_avg"],
            color=virus_color,
            linewidth=LAYOUT["line_width"],
            solid_capstyle="round",
        )

        # Fill under curve
        ax.fill_between(
            data["date"],
            data["rolling_avg"],
            alpha=LAYOUT["area_alpha"],
            color=virus_color,
        )

        # Latest value dot
        latest = data.dropna(subset=["rolling_avg"]).iloc[-1]
        ax.scatter(
            [latest["date"]], [latest["rolling_avg"]],
            color=virus_color,
            s=LAYOUT["scatter_size"],
            zorder=5,
            edgecolors="white",
            linewidths=LAYOUT["scatter_edge_width"],
        )

        current_value = float(latest["rolling_avg"])
    else:
        current_value = None

    # Y-axis starts at 0
    ax.set_ylim(bottom=0)
    ax.set_ylabel(
        "Virenfracht (Mio. Genkopien/Tag)",
        fontsize=11,
        color=COLORS["text_secondary"],
    )

    # Add year annotations
    add_year_annotations(ax, data["date"].min(), data["date"].max())

    # Date formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # Calculate trend
    trend_pct = None
    if "rolling_avg" in data.columns and len(data) >= 14:
        values = data["rolling_avg"].dropna().values
        if len(values) >= 14:
            last_week = values[-7:].mean()
            prev_week = values[-14:-7].mean()
            if prev_week > 0:
                trend_pct = ((last_week - prev_week) / prev_week) * 100

    # Visual elements
    add_accent_bar(fig, COLORS["rising"])
    subtitle = f"SARS-CoV-2  |  {chart_config.rolling_window}-Tage-Durchschnitt  |  Letzte 2 Jahre"
    add_header(fig, "Nationaler Trend", subtitle, current_value, virus_color)

    latest_date = None
    if "date" in data.columns and len(data) > 0:
        try:
            latest_date = pd.Timestamp(data["date"].iloc[-1]).strftime("%d.%m.%Y")
        except (TypeError, ValueError):
            pass
    add_footer(fig, trend_pct, latest_date)

    return fig


def create_heatmap_chart(
    data: pd.DataFrame,
    config: Config,
    chart_config: ChartConfig,
) -> plt.Figure:
    """Create calendar heatmap."""
    apply_editorial_style()
    fig, ax = create_figure_with_margins()

    if data.empty:
        ax.text(
            0.5, 0.5, "Keine Daten verfugbar",
            ha="center", va="center",
            fontsize=16, color=COLORS["text_muted"],
            transform=ax.transAxes,
        )
        add_header(fig, "Aktivitat", "Letzte 52 Wochen")
        return fig

    # German weekday labels
    weekday_labels = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

    # Custom colormap using design colors
    cmap = sns.light_palette(VIRUS_CONFIG["SARS-CoV-2"]["color"], as_cmap=True)

    # Generate week labels (show every 4th week)
    week_labels = []
    for i, col in enumerate(data.columns):
        if i % 4 == 0:
            # Extract week number from column if possible, otherwise use index
            week_labels.append(f"KW{(i % 52) + 1}")
        else:
            week_labels.append("")

    # Create heatmap with week labels and better spacing
    sns.heatmap(
        data,
        ax=ax,
        cmap=cmap,
        cbar_kws={"label": "Virenlast", "shrink": 0.5},
        xticklabels=week_labels,
        yticklabels=weekday_labels,
        linewidths=0.5,
        linecolor=COLORS["canvas"],
        square=True,
    )

    ax.set_xlabel("", fontsize=11, color=COLORS["text_secondary"])
    ax.set_ylabel("", fontsize=11)
    ax.tick_params(axis="x", labelsize=8, rotation=45)
    ax.tick_params(axis="y", labelsize=10)

    # Visual elements
    add_accent_bar(fig, VIRUS_CONFIG["SARS-CoV-2"]["color"])
    add_header(fig, "Aktivitat", f"SARS-CoV-2  |  Letzte {chart_config.weeks} Wochen")
    add_footer(fig)

    return fig


def create_multi_pathogen_chart(
    data: dict[str, pd.DataFrame],
    config: Config,
    chart_config: ChartConfig,
) -> plt.Figure:
    """Create vertical stack of 3 pathogen charts."""
    apply_editorial_style()

    # 3 rows, 1 column layout for better readability
    fig, axes = plt.subplots(
        3, 1,
        figsize=(12, 14),  # Wider and taller for better label spacing
        dpi=LAYOUT["dpi"],
        facecolor=COLORS["canvas"],
    )

    # Map of possible keys to labels and colors
    # 3 pathogens from ViennaViz: sars_cov_2, influenza, rsv
    pathogen_config = [
        {
            "keys": ["SARS-CoV-2", "sars_cov_2", "sars-cov-2"],
            "label": "SARS-CoV-2",
            "color_key": "SARS-CoV-2",
        },
        {
            "keys": ["Influenza", "influenza", "Influenza_A", "influenza_a"],
            "label": "Influenza",
            "color_key": "Influenza",
        },
        {
            "keys": ["RSV", "rsv"],
            "label": "RSV",
            "color_key": "RSV",
        },
    ]

    for i, pcfg in enumerate(pathogen_config):
        ax = axes[i]
        ax.set_facecolor(COLORS["panel"])

        virus_config = VIRUS_CONFIG.get(pcfg["color_key"], VIRUS_CONFIG["SARS-CoV-2"])
        color = virus_config["color"]

        # Find matching key in data
        df = None
        for key in pcfg["keys"]:
            if key in data and not data[key].empty:
                df = data[key]
                break

        label = pcfg["label"]
        if df is None:
            ax.text(
                0.5, 0.5, f"{label}\n(keine Daten)",
                ha="center", va="center",
                fontsize=12, color=COLORS["text_muted"],
                transform=ax.transAxes,
            )
            ax.set_xticks([])
            ax.set_yticks([])
            continue

        if "rolling_avg" in df.columns:
            ax.plot(df["date"], df["rolling_avg"], color=color, linewidth=2.5)
            ax.fill_between(
                df["date"], df["rolling_avg"],
                alpha=LAYOUT["area_alpha"], color=color,
            )
        elif "value" in df.columns:
            ax.plot(df["date"], df["value"], color=color, linewidth=2.5)
            ax.fill_between(
                df["date"], df["value"],
                alpha=LAYOUT["area_alpha"], color=color,
            )

        # Title on left side
        ax.set_ylabel(label, fontsize=14, fontweight=600, color=COLORS["text_primary"])

        # Custom x-axis labels with season spans below
        dates = df["date"].sort_values()
        if len(dates) > 0:
            date_max = dates.max()
            # Limit to max 2 years back
            two_years_ago = date_max - pd.DateOffset(years=2)
            date_min = max(dates.min(), two_years_ago)
            # Filter data to this range
            df = df[df["date"] >= date_min].copy()
            dates = df["date"].sort_values()

            # Update plot limits
            ax.set_xlim(date_min, date_max)

            # Custom x-axis labels: sparse labels, always include last date
            all_ticks = pd.date_range(
                start=date_min,
                end=date_max,
                freq="MS",  # Month start
            ).tolist()

            # Always include the last date
            last_date = date_max

            # Keep every 2nd month, but ensure we don't have too many
            if len(all_ticks) > 8:
                selected_ticks = all_ticks[::3]  # Every 3rd month
            elif len(all_ticks) > 5:
                selected_ticks = all_ticks[::2]  # Every 2nd month
            else:
                selected_ticks = all_ticks

            # Always add last date as final tick
            selected_ticks.append(last_date)

            ax.set_xticks(selected_ticks)
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))

            # Add season span annotations below x-axis (only for bottom chart)
            if i == len(pathogen_config) - 1:
                # Define season boundaries
                def get_season_info(month: int) -> tuple[str, str]:
                    """Return season name and color."""
                    if month in [12, 1, 2]:
                        return "Winter", "#4A90A4"
                    elif month in [3, 4, 5]:
                        return "Fruhling", "#7CB342"
                    elif month in [6, 7, 8]:
                        return "Sommer", "#FFB300"
                    else:
                        return "Herbst", "#D84315"

                # Find season transitions in the date range
                season_spans = []
                current_date = date_min.replace(day=1)
                while current_date <= date_max:
                    season_name, season_color = get_season_info(current_date.month)
                    # Find end of this season
                    if current_date.month in [12, 1, 2]:
                        if current_date.month == 12:
                            end_date = pd.Timestamp(
                                year=current_date.year + 1, month=3, day=1
                            )
                        else:
                            end_date = pd.Timestamp(year=current_date.year, month=3, day=1)
                    elif current_date.month in [3, 4, 5]:
                        end_date = pd.Timestamp(year=current_date.year, month=6, day=1)
                    elif current_date.month in [6, 7, 8]:
                        end_date = pd.Timestamp(year=current_date.year, month=9, day=1)
                    else:
                        end_date = pd.Timestamp(year=current_date.year, month=12, day=1)

                    # Clip to data range
                    span_start = max(current_date, date_min)
                    span_end = min(end_date, date_max)

                    if span_start < span_end:
                        season_spans.append({
                            "start": span_start,
                            "end": span_end,
                            "name": season_name,
                            "color": season_color,
                        })

                    current_date = end_date

                # Draw season annotations below x-axis
                y_pos = -0.18  # Position below axis
                for span in season_spans:
                    mid_point = span["start"] + (span["end"] - span["start"]) / 2
                    # Convert to axis coordinates
                    ax.annotate(
                        f'<-- {span["name"]} -->',
                        xy=(mid_point, 0),
                        xytext=(mid_point, y_pos),
                        textcoords=("data", "axes fraction"),
                        ha="center",
                        va="top",
                        fontsize=9,
                        fontweight=500,
                        color=span["color"],
                        annotation_clip=False,
                    )

        # Add year labels in background and dashed lines between years
        if len(dates) > 0:
            # Find year boundaries within date range
            years_in_range = sorted(set(dates.dt.year))
            for year in years_in_range:
                year_start = pd.Timestamp(year=year, month=1, day=1)
                year_end = pd.Timestamp(year=year, month=12, day=31)
                # Clip to data range
                vis_start = max(year_start, date_min)
                vis_end = min(year_end, date_max)
                if vis_start < vis_end:
                    mid_point = vis_start + (vis_end - vis_start) / 2
                    ax.text(
                        mid_point,
                        0.5,
                        str(year),
                        transform=ax.get_xaxis_transform(),
                        ha="center",
                        va="center",
                        fontsize=48,
                        fontweight=300,
                        color="#E0E0E0",
                        zorder=0,
                    )

                # Add dashed vertical line at year boundary (Jan 1)
                if year_start > date_min and year_start <= date_max:
                    ax.axvline(
                        x=year_start,
                        color="#CCCCCC",
                        linestyle="--",
                        linewidth=1.5,
                        zorder=1,
                    )

        plt.setp(ax.xaxis.get_majorticklabels(), rotation=0, ha="center", fontsize=10)
        ax.tick_params(axis="y", labelsize=10)
        ax.grid(True, alpha=0.4, linestyle="--", color=COLORS["grid"])
        ax.set_ylim(bottom=0)

        # Remove top and right spines
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(COLORS["grid"])
        ax.spines["bottom"].set_color(COLORS["grid"])

    # Main title
    fig.suptitle(
        "WIEN: RESPIRATORISCHE VIREN",
        fontsize=TYPOGRAPHY["title_size"],
        fontweight=TYPOGRAPHY["title_weight"],
        color=COLORS["text_primary"],
        y=0.97,
        fontfamily=TYPOGRAPHY["title_family"],
    )

    # Add data timestamp footer
    # Find latest date from all pathogens
    latest_dates = []
    for pcfg in pathogen_config:
        for key in pcfg["keys"]:
            if key in data and not data[key].empty:
                latest_dates.append(data[key]["date"].max())
                break
    if latest_dates:
        latest_date = max(latest_dates)
        date_str = latest_date.strftime("%d.%m.%Y")
        fig.text(
            0.98, 0.01,
            f"Stand: {date_str}  |  Quelle: Stadt Wien",
            ha="right",
            va="bottom",
            fontsize=9,
            color=COLORS["text_muted"],
        )

    plt.tight_layout(rect=[0, 0.03, 1, 0.94])
    return fig


def create_summary_chart(
    regional_data: pd.DataFrame,
    trend_data: pd.DataFrame,
    config: Config,
) -> plt.Figure:
    """Create summary chart with key metrics."""
    apply_editorial_style()

    fig = plt.figure(
        figsize=LAYOUT["figure_size"],
        dpi=LAYOUT["dpi"],
        facecolor=COLORS["canvas"],
    )

    gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.3)

    # Top: Regional comparison (spans 2 columns)
    ax1 = fig.add_subplot(gs[0, :])
    ax1.set_facecolor(COLORS["panel"])

    if not regional_data.empty:
        recent = regional_data.tail(30)

        for col in recent.columns:
            if col in BUNDESLAND_ACCENTS:
                ax1.plot(
                    recent.index,
                    recent[col],
                    label=BUNDESLAND_NAMES.get(col, col),
                    color=BUNDESLAND_ACCENTS[col],
                    linewidth=2,
                )

        ax1.set_title(
            "Bundeslander (letzte 30 Tage)",
            fontsize=14, fontweight=600, color=COLORS["text_primary"],
        )
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
        ax1.legend(
            loc="center left", bbox_to_anchor=(1.02, 0.5),
            fontsize=9, frameon=False,
        )
        ax1.grid(True, alpha=0.4, linestyle="--", color=COLORS["grid"])
        ax1.spines["top"].set_visible(False)
        ax1.spines["right"].set_visible(False)

    # Bottom left: Current values
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.set_facecolor(COLORS["panel"])

    if not regional_data.empty:
        latest = regional_data.iloc[-1].dropna().sort_values(ascending=True)

        colors = [BUNDESLAND_ACCENTS.get(r, "#999999") for r in latest.index]
        y_labels = [BUNDESLAND_NAMES.get(r, r) for r in latest.index]
        bars = ax2.barh(y_labels, latest.values, color=colors)

        ax2.set_title(
            "Aktuelle Werte",
            fontsize=14, fontweight=600, color=COLORS["text_primary"],
        )
        ax2.tick_params(axis="both", labelsize=9)
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(False)

        for bar, val in zip(bars, latest.values):
            x_pos = val + 0.5
            y_pos = bar.get_y() + bar.get_height() / 2
            ax2.text(x_pos, y_pos, f"{val:.1f}", va="center", fontsize=9)

    # Bottom right: Trend sparkline
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.set_facecolor(COLORS["panel"])

    if not trend_data.empty and "rolling_avg" in trend_data.columns:
        virus_color = VIRUS_CONFIG["SARS-CoV-2"]["color"]

        ax3.plot(
            trend_data["date"], trend_data["rolling_avg"],
            color=virus_color, linewidth=2.5,
        )
        ax3.fill_between(
            trend_data["date"], trend_data["rolling_avg"],
            alpha=LAYOUT["area_alpha"], color=virus_color,
        )
        ax3.set_title(
            "Nationaler Trend (180 Tage)",
            fontsize=14, fontweight=600, color=COLORS["text_primary"],
        )
        ax3.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
        ax3.tick_params(axis="both", labelsize=9)
        ax3.set_ylim(bottom=0)
        ax3.grid(True, alpha=0.4, linestyle="--", color=COLORS["grid"])
        ax3.spines["top"].set_visible(False)
        ax3.spines["right"].set_visible(False)

    # Main title
    fig.suptitle(
        "SARS-COV-2 ABWASSERMONITORING",
        fontsize=TYPOGRAPHY["title_size"],
        fontweight=TYPOGRAPHY["title_weight"],
        color=COLORS["text_primary"],
        y=0.98,
        fontfamily=TYPOGRAPHY["title_family"],
    )

    # Footer
    fig.text(
        0.5, 0.01,
        f"Stand: {datetime.now().strftime('%d.%m.%Y')}  |  AGES Abwassermonitoring",
        fontsize=10, color=COLORS["text_muted"], ha="center",
    )

    plt.tight_layout(rect=[0, 0.03, 0.88, 0.94])
    return fig
