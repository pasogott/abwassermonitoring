"""Alpine Editorial Design System for Austrian wastewater monitoring."""

# Color Palette - Sophisticated, non-alarmist medical aesthetic
COLORS = {
    # Viruses - muted, distinguishable, medical-feeling
    "SARS-CoV-2": "#2D5A5A",  # Deep teal - authoritative
    "Influenza": "#B8860B",  # Dark goldenrod - seasonal
    "RSV": "#8B5A6B",  # Dusty mauve - respiratory
    # Severity accents (for trend indicators)
    "rising": "#C73E3A",  # Austrian red - alert
    "stable": "#5C7C5C",  # Sage green - calm
    "falling": "#4A7C8C",  # Steel blue - improving
    # Backgrounds
    "canvas": "#FAF8F5",  # Warm paper white
    "panel": "#F4F1EC",  # Slightly darker for cards
    "grid": "#E8E4DD",  # Subtle grid lines
    # Typography
    "text_primary": "#1C1C1C",  # Near black
    "text_secondary": "#5A5A5A",  # Medium gray
    "text_muted": "#8A8A8A",  # Light gray
}

# Bundesland Identity Colors (accent stripe/element)
BUNDESLAND_ACCENTS = {
    "Wien": "#E31E24",  # Vienna red
    "Niederoesterreich": "#1D428A",  # Classic blue
    "Oberoesterreich": "#2E7D32",  # Forest green
    "Salzburg": "#C62828",  # Salzburg red
    "Tirol": "#1565C0",  # Mountain blue
    "Vorarlberg": "#6A1B9A",  # Alpine purple
    "Kaernten": "#EF6C00",  # Warm orange
    "Steiermark": "#388E3C",  # Styrian green
    "Burgenland": "#D32F2F",  # Burgundy
    "Oesterreich": "#C41E3A",  # National Austrian red
}

# Display names for Bundeslaender (with proper German)
BUNDESLAND_NAMES = {
    "Wien": "Wien",
    "Niederoesterreich": "Niederosterreich",
    "Oberoesterreich": "Oberosterreich",
    "Salzburg": "Salzburg",
    "Tirol": "Tirol",
    "Vorarlberg": "Vorarlberg",
    "Kaernten": "Karnten",
    "Steiermark": "Steiermark",
    "Burgenland": "Burgenland",
    "Oesterreich": "Osterreich",
}

# Typography System
TYPOGRAPHY = {
    # Primary display - elegant, editorial
    "title_family": ["Playfair Display", "Georgia", "serif"],
    "title_weight": 700,
    "title_size": 32,
    # Data labels - precise, technical
    "mono_family": ["JetBrains Mono", "Consolas", "monospace"],
    "mono_size": 28,
    # Body text - clean, governmental
    "body_family": ["Source Sans 3", "Helvetica Neue", "sans-serif"],
    "body_size": 13,
    # Bundesland name
    "bundesland_size": 32,
    "bundesland_weight": 700,
}

# Chart Layout Constants
LAYOUT = {
    # Figure dimensions for 1080x1080 output
    "figure_size": (10.8, 10.8),
    "dpi": 100,
    # Margins (as fraction of figure)
    "margin_top": 0.12,
    "margin_bottom": 0.12,
    "margin_left": 0.10,
    "margin_right": 0.08,
    # Chart styling
    "line_width": 3.0,
    "area_alpha": 0.15,
    "grid_alpha": 0.6,
    "grid_style": "--",
    "grid_linewidth": 0.8,
    # Accent bar
    "accent_bar_width": 0.008,
    "accent_bar_height": 0.06,
    "accent_bar_y": 0.92,
    # Scatter point for latest value
    "scatter_size": 100,
    "scatter_edge_width": 2.5,
}

# Virus display configuration
VIRUS_CONFIG = {
    "SARS-CoV-2": {
        "color": "#2D5A5A",
        "label": "SARS-CoV-2",
        "unit": "Genkopien / EW / Tag (Mio.)",
    },
    "Influenza": {
        "color": "#B8860B",
        "label": "Influenza",
        "unit": "Genkopien / EW / Tag (Mio.)",
    },
    "RSV": {
        "color": "#8B5A6B",
        "label": "RSV",
        "unit": "Genkopien / EW / Tag (Mio.)",
    },
}
