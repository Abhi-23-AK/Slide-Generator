"""
Layout Definitions Registry
============================
Defines the 8 canonical slide layouts with their zone specifications,
capacity limits, and content-type affinities used by the scoring engine.
"""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass(frozen=True)
class LayoutZone:
    """A named region within a layout template."""
    name: str
    max_words: int
    max_lines: int
    accepts: tuple  # ("text", "bullets", "image", "chart", "diagram", "icon", "metric")


@dataclass(frozen=True)
class LayoutDefinition:
    """Static definition of a layout template."""
    id: str
    name: str
    zones: tuple  # tuple of LayoutZone
    best_for: tuple  # content type tags this layout excels at
    capacity_words: int  # total word budget across all zones
    column_count: int
    description: str = ""


# ─── Layout Zone Presets ──────────────────────────────────────────────

# 1-Column: Hero image top, headline + body below
ONE_COLUMN = LayoutDefinition(
    id="1-column",
    name="One Column",
    zones=(
        LayoutZone("hero_image", max_words=0, max_lines=0, accepts=("image",)),
        LayoutZone("headline", max_words=12, max_lines=2, accepts=("text",)),
        LayoutZone("body", max_words=90, max_lines=8, accepts=("text", "bullets")),
    ),
    best_for=("opener", "conclusion", "quote", "content", "abstract"),
    capacity_words=102,
    column_count=1,
    description="Hero image top, headline + body below. Best for openers, conclusions, quotes.",
)

# 2-Column: Left text/bullets, right image or chart
TWO_COLUMN = LayoutDefinition(
    id="2-column",
    name="Two Column",
    zones=(
        LayoutZone("left_column", max_words=80, max_lines=8, accepts=("text", "bullets")),
        LayoutZone("right_column", max_words=56, max_lines=7, accepts=("image", "chart", "text", "bullets")),
    ),
    best_for=("content", "solution", "problem", "tech_stack", "comparison"),
    capacity_words=136,
    column_count=2,
    description="Left: text/bullets. Right: image or chart. Best for content + visual pairs.",
)

# 3-Column: Equal columns with icon + heading + short text
THREE_COLUMN = LayoutDefinition(
    id="3-column",
    name="Three Column",
    zones=(
        LayoutZone("col_1", max_words=42, max_lines=5, accepts=("icon", "text", "bullets")),
        LayoutZone("col_2", max_words=42, max_lines=5, accepts=("icon", "text", "bullets")),
        LayoutZone("col_3", max_words=42, max_lines=5, accepts=("icon", "text", "bullets")),
    ),
    best_for=("comparison", "content", "abstract", "solution"),
    capacity_words=126,
    column_count=3,
    description="Equal columns with icon + heading + short text. Best for feature comparisons.",
)

# 4-Grid: 2×2 metric cards or icon boxes
FOUR_GRID = LayoutDefinition(
    id="4-grid",
    name="Four Grid",
    zones=(
        LayoutZone("cell_tl", max_words=25, max_lines=3, accepts=("metric", "icon", "text")),
        LayoutZone("cell_tr", max_words=25, max_lines=3, accepts=("metric", "icon", "text")),
        LayoutZone("cell_bl", max_words=25, max_lines=3, accepts=("metric", "icon", "text")),
        LayoutZone("cell_br", max_words=25, max_lines=3, accepts=("metric", "icon", "text")),
    ),
    best_for=("data", "kpi", "comparison"),
    capacity_words=100,
    column_count=4,
    description="2×2 metric cards or icon boxes. Best for KPI dashboards, 4-element frameworks.",
)

# Hero: Full-bleed background image, large centered title
HERO = LayoutDefinition(
    id="hero",
    name="Hero",
    zones=(
        LayoutZone("background_image", max_words=0, max_lines=0, accepts=("image",)),
        LayoutZone("title", max_words=15, max_lines=2, accepts=("text",)),
    ),
    best_for=("title", "opener", "quote", "conclusion"),
    capacity_words=15,
    column_count=1,
    description="Full-bleed background image, large centered title. Best for section dividers.",
)

# Dashboard: Top stat row, middle chart, bottom table or insight
DASHBOARD = LayoutDefinition(
    id="dashboard",
    name="Dashboard",
    zones=(
        LayoutZone("stat_row", max_words=30, max_lines=2, accepts=("metric", "text")),
        LayoutZone("chart_area", max_words=10, max_lines=1, accepts=("chart", "image")),
        LayoutZone("insight_area", max_words=40, max_lines=4, accepts=("text", "bullets")),
    ),
    best_for=("data", "kpi", "content"),
    capacity_words=80,
    column_count=1,
    description="Top: stat row. Middle: chart. Bottom: table or insight. Best for analytics.",
)

# Architecture: Large diagram canvas with surrounding labels
ARCHITECTURE = LayoutDefinition(
    id="architecture",
    name="Architecture",
    zones=(
        LayoutZone("diagram_canvas", max_words=0, max_lines=0, accepts=("diagram", "image")),
        LayoutZone("labels", max_words=60, max_lines=8, accepts=("text", "bullets")),
    ),
    best_for=("architecture", "diagram", "process", "tech_stack"),
    capacity_words=60,
    column_count=1,
    description="Large diagram canvas with surrounding labels. Best for system diagrams.",
)

# Timeline: Horizontal or vertical swimlane with dated events
TIMELINE = LayoutDefinition(
    id="timeline",
    name="Timeline",
    zones=(
        LayoutZone("events", max_words=50, max_lines=10, accepts=("text", "bullets")),
    ),
    best_for=("timeline", "process", "content"),
    capacity_words=50,
    column_count=1,
    description="Horizontal swimlane with dated events. Best for roadmaps, history slides.",
)


# ─── Registry ─────────────────────────────────────────────────────────

ALL_LAYOUTS: tuple = (
    ONE_COLUMN,
    TWO_COLUMN,
    THREE_COLUMN,
    FOUR_GRID,
    HERO,
    DASHBOARD,
    ARCHITECTURE,
    TIMELINE,
)

LAYOUT_MAP: Dict[str, LayoutDefinition] = {layout.id: layout for layout in ALL_LAYOUTS}


def get_layout(layout_id: str) -> LayoutDefinition:
    """Look up a layout by ID, defaulting to 1-column."""
    return LAYOUT_MAP.get(layout_id, ONE_COLUMN)


def get_all_layout_ids() -> List[str]:
    """Return all available layout IDs."""
    return [layout.id for layout in ALL_LAYOUTS]


def get_layout_summaries() -> List[dict]:
    """Return a list of layout summaries suitable for API responses."""
    return [
        {
            "id": layout.id,
            "name": layout.name,
            "description": layout.description,
            "capacity_words": layout.capacity_words,
            "column_count": layout.column_count,
            "best_for": list(layout.best_for),
            "zones": [
                {
                    "name": zone.name,
                    "max_words": zone.max_words,
                    "max_lines": zone.max_lines,
                    "accepts": list(zone.accepts),
                }
                for zone in layout.zones
            ],
        }
        for layout in ALL_LAYOUTS
    ]
