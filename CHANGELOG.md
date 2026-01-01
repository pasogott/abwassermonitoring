# Changelog

All notable changes to this project will be documented in this file.

## 0.2.0 - 2026-01-01

### Changed

* Simplified output to Vienna-only 3-month trend chart with year-over-year comparison
* Previous year shown as faded dashed line using calendar week alignment
* Shared legend below chart title showing current and previous year
* Endpoint dots on current values for visual clarity

### Added

* GitHub Action for weekly automated runs (Monday 03:00 CET)
* Webhook integration with n8n for messaging automation
* JSON data export with statistics, week-over-week, and year-over-year changes
* Public URLs for chart and data via `data/latest.png` and `data/latest.json`
* n8n AI prompts documentation for personalized summaries
* uv caching in CI for faster builds

### Removed

* Regional comparison charts
* National trend charts
* Calendar heatmap visualization
* Season labels and year annotations
* Docker support files

## 0.1.0 - 2025-12-31

### Added

* Initial implementation of Austrian wastewater monitoring visualization tool
* Multi-source data fetching from abwassermonitoring.at (national/regional SARS-CoV-2 data) and ViennaViz API (multi-pathogen data)
* Vienna multi-pathogen charts displaying SARS-CoV-2, Influenza, and RSV in vertical layout
* Regional comparison stacked area chart for all Bundeslaender
* National trend chart with 7-day rolling average
* Calendar heatmap visualization showing 52 weeks of activity
* Year annotations with large background numbers and dashed separators between years
* Season labels (`<-- Winter -->`, `<-- Sommer -->`, etc.) below x-axis on Vienna charts
* Automatic 2-year data window limit for all time-series charts
* Data timestamp footer showing "Stand" date and source
* Docker support with `Dockerfile`, `docker-compose.yml`, and `Makefile`
* YAML-based configuration for data sources, visualization settings, and styling
* Alpine Editorial design system with consistent typography and color scheme
