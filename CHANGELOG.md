# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

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
