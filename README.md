# Vienna Wastewater Pathogen Monitor

Automated weekly visualization of respiratory virus levels in Vienna's wastewater, with year-over-year comparison.

![Vienna Pathogens Chart](output/latest/vienna_pathogens.png)

## What it does

- Fetches wastewater monitoring data from Stadt Wien Open Data
- Generates a 3-month trend chart for SARS-CoV-2, Influenza, and RSV
- Compares current levels with the same calendar week last year
- Exports structured JSON data for AI analysis
- Sends results to n8n webhook every Monday

## Output

| File | Description |
|------|-------------|
| `vienna_pathogens.png` | Chart with current year (solid) vs previous year (dashed) |
| `vienna_data.json` | Structured data with statistics and time series |

### JSON Structure

```json
{
  "generated_at": "2025-12-23T02:00:00",
  "period": { "start": "2025-09-21", "end": "2025-12-21" },
  "pathogens": {
    "SARS-CoV-2": {
      "current_value": 264222602195925.88,
      "current_date": "2025-12-21",
      "week_over_week_change_percent": -28.6,
      "year_over_year_change_percent": 31.3,
      "previous_year_value": 201225368827786.0,
      "statistics": { "min": ..., "max": ..., "mean": ... },
      "time_series": [{ "date": "...", "value": ... }, ...]
    },
    "Influenza": { ... },
    "RSV": { ... }
  }
}
```

## Installation

```bash
# Clone repository
git clone https://github.com/pasogott/abwassermonitoring.git
cd abwassermonitoring

# Install dependencies (requires uv)
uv sync

# Run manually
uv run python -m abwasser
```

## GitHub Actions

The workflow runs automatically every Monday at 03:00 CET.

### Setup

1. Go to **Settings > Secrets and variables > Actions**
2. Add secret: `N8N_WEBHOOK_URL` with your n8n webhook URL

### Manual Trigger

**Actions > Weekly Vienna Pathogen Report > Run workflow**

### Webhook Payload

The webhook receives a JSON POST with:

```json
{
  "image": "<base64 encoded PNG>",
  "filename": "vienna_pathogens.png",
  "generated_at": "2025-12-23T02:00:00Z",
  "data": { /* full JSON data structure */ }
}
```

#### n8n: Decode Image

```javascript
// Code Node
const imageBuffer = Buffer.from($json.image, 'base64');
return {
  binary: {
    data: {
      data: $json.image,
      mimeType: 'image/png',
      fileName: $json.filename
    }
  },
  json: $json.data
};
```

## AI Summary Generation

The JSON data is structured for AI analysis. See **[docs/n8n-ai-prompts.md](docs/n8n-ai-prompts.md)** for ready-to-use prompts that generate friendly weekly summaries.

Example workflow:
1. Webhook receives data from GitHub Actions
2. AI Agent analyzes trends and changes
3. Sends personalized message with chart to Telegram/Signal

## Data Sources

- [Stadt Wien Open Data - Abwassermonitoring](https://www.data.gv.at/katalog/dataset/stadt-wien_abwassermonitoringwien)

## License

MIT
