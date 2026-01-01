"""Visualization module for Vienna pathogen chart."""

import logging
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from .config import ChartConfig, Config
from .design import COLORS, LAYOUT, TYPOGRAPHY, VIRUS_CONFIG

logger = logging.getLogger(__name__)


def apply_editorial_style() -> None:
    """Apply the Alpine Editorial style globally."""
    plt.rcParams.update(
        {
            "figure.facecolor": COLORS["canvas"],
            "axes.facecolor": COLORS["panel"],
            "savefig.facecolor": COLORS["canvas"],
            "font.family": TYPOGRAPHY["body_family"],
            "font.size": 12,
            "axes.titlesize": 16,
            "axes.titleweight": 600,
            "axes.labelsize": 12,
            "axes.labelcolor": COLORS["text_secondary"],
            "axes.grid": True,
            "grid.color": COLORS["grid"],
            "grid.alpha": LAYOUT["grid_alpha"],
            "grid.linestyle": LAYOUT["grid_style"],
            "grid.linewidth": LAYOUT["grid_linewidth"],
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": True,
            "axes.spines.bottom": True,
            "axes.linewidth": 1.2,
            "axes.edgecolor": COLORS["grid"],
            "xtick.color": COLORS["text_muted"],
            "ytick.color": COLORS["text_muted"],
            "xtick.labelsize": 11,
            "ytick.labelsize": 11,
            "legend.frameon": False,
            "legend.fontsize": 11,
        }
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


def create_multi_pathogen_chart(
    data: dict[str, pd.DataFrame],
    config: Config,
    chart_config: ChartConfig,
) -> plt.Figure:
    """Create vertical stack of 3 pathogen charts with year-over-year comparison.

    Shows last 3 months with previous year aligned by calendar week.
    """
    apply_editorial_style()

    fig, axes = plt.subplots(
        3,
        1,
        figsize=(12, 14),
        dpi=LAYOUT["dpi"],
        facecolor=COLORS["canvas"],
    )

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
        df_full = None
        for key in pcfg["keys"]:
            if key in data and not data[key].empty:
                df_full = data[key].copy()
                break

        label = pcfg["label"]
        if df_full is None:
            ax.text(
                0.5,
                0.5,
                f"{label}\n(keine Daten)",
                ha="center",
                va="center",
                fontsize=12,
                color=COLORS["text_muted"],
                transform=ax.transAxes,
            )
            ax.set_xticks([])
            ax.set_yticks([])
            continue

        # Add ISO calendar week info
        df_full["year"] = df_full["date"].dt.isocalendar().year
        df_full["week"] = df_full["date"].dt.isocalendar().week

        # Define current period (last 3 months)
        dates_all = df_full["date"].sort_values()
        date_max = dates_all.max()
        three_months_ago = date_max - pd.DateOffset(months=3)
        date_min = max(dates_all.min(), three_months_ago)

        # Current year data
        df_current = df_full[df_full["date"] >= date_min].copy()
        current_year = date_max.year

        # Get calendar weeks in current period
        current_weeks = set(df_current["week"].tolist())

        # Previous year data: match by calendar week
        prev_year = current_year - 1
        df_prev_raw = df_full[df_full["year"] == prev_year].copy()

        # Filter to only weeks that exist in current period
        df_prev = df_prev_raw[df_prev_raw["week"].isin(current_weeks)].copy()

        # Create mapping: for each prev year date, find corresponding current year date
        # by matching calendar week
        if not df_prev.empty:
            week_to_current_date = dict(zip(df_current["week"], df_current["date"]))
            df_prev["date_mapped"] = df_prev["week"].map(week_to_current_date)
            df_prev = df_prev.dropna(subset=["date_mapped"])
            df_prev["date"] = df_prev["date_mapped"]

        # Determine which column to plot
        value_col = "rolling_avg" if "rolling_avg" in df_full.columns else "value"

        # Plot previous year first (background, faded)
        if not df_prev.empty:
            df_prev_sorted = df_prev.sort_values("date")
            ax.plot(
                df_prev_sorted["date"],
                df_prev_sorted[value_col],
                color="#999999",
                linewidth=1.5,
                linestyle="--",
                alpha=0.6,
            )

        # Plot current year (foreground, prominent)
        if not df_current.empty:
            df_current_sorted = df_current.sort_values("date")
            ax.plot(
                df_current_sorted["date"],
                df_current_sorted[value_col],
                color=color,
                linewidth=2.5,
            )
            ax.fill_between(
                df_current_sorted["date"],
                df_current_sorted[value_col],
                alpha=LAYOUT["area_alpha"],
                color=color,
            )
            # Dot at latest value
            last_date = df_current_sorted["date"].max()
            mask = df_current_sorted["date"] == last_date
            last_value = df_current_sorted.loc[mask, value_col].iloc[0]
            ax.scatter(
                [last_date],
                [last_value],
                color=color,
                s=60,
                zorder=5,
                edgecolors="white",
                linewidths=2,
            )

        # Y-axis label
        ax.set_ylabel(label, fontsize=14, fontweight=600, color=COLORS["text_primary"])

        # X-axis: use actual data points as ticks
        dates = df_current["date"].sort_values()
        if len(dates) > 0:
            # Add padding so dots aren't clipped
            padding = pd.Timedelta(days=3)
            ax.set_xlim(date_min - padding, date_max + padding)

            # Use actual data dates as ticks (every 2nd week)
            tick_dates = dates.tolist()[::2]
            # Always include last date
            if dates.iloc[-1] not in tick_dates:
                tick_dates.append(dates.iloc[-1])
            ax.set_xticks(tick_dates)
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))

        plt.setp(ax.xaxis.get_majorticklabels(), rotation=0, ha="center", fontsize=10)
        ax.tick_params(axis="y", labelsize=10)
        ax.grid(True, alpha=0.4, linestyle="--", color=COLORS["grid"])
        ax.set_ylim(bottom=0)

        # Spine styling
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(COLORS["grid"])
        ax.spines["bottom"].set_color(COLORS["grid"])

    # Title
    fig.suptitle(
        "WIEN: RESPIRATORISCHE VIREN",
        fontsize=TYPOGRAPHY["title_size"],
        fontweight=TYPOGRAPHY["title_weight"],
        color=COLORS["text_primary"],
        y=0.97,
        fontfamily=TYPOGRAPHY["title_family"],
    )

    # Shared legend below title
    from matplotlib.lines import Line2D

    legend_elements = [
        Line2D([0], [0], color="#444444", linewidth=2.5, label="2025"),
        Line2D([0], [0], color="#999999", linewidth=1.5, linestyle="--", label="2024"),
    ]
    fig.legend(
        handles=legend_elements,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.94),
        ncol=2,
        fontsize=11,
        frameon=False,
    )

    # Footer with date
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
            0.98,
            0.01,
            f"Stand: {date_str}  |  Quelle: Stadt Wien",
            ha="right",
            va="bottom",
            fontsize=9,
            color=COLORS["text_muted"],
        )

    plt.tight_layout(rect=[0, 0.03, 1, 0.94])
    return fig
