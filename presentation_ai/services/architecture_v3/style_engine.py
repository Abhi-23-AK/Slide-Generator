"""
Style Engine — Thread-local visual style context for Architecture V3.

This module provides a thread-safe mechanism to set/get the active visual style.
shape_resolver.py and logo_resolver.py query the current style to emit different
colors, shapes, and icon strategies — without modifying the rendering pipeline.

Supported styles:
  classic       — Rounded pastel boxes (the original default)
  aiicons       — Colorful AI-themed with brand logos emphasized
  aws_icons     — AWS orange/dark palette with service icons
  azure_icons   — Azure blue palette with service icons
  gcp_icons     — GCP multi-color palette with service icons
  k8s_icons     — Kubernetes blue/navy palette with cluster icons
  drawio_skill  — Large icons, dashed rounded containers, bright vivid colors
  minimal       — Monochrome, no logos, clean lines
"""

import threading
from typing import Dict, Any, Optional

# ─────────────────────────────────────────
# Thread-local storage
# ─────────────────────────────────────────
_style_ctx = threading.local()

VALID_STYLES = {
    "classic", "aiicons", "aws_icons", "azure_icons",
    "gcp_icons", "k8s_icons", "drawio_skill", "minimal"
}

DEFAULT_STYLE = "classic"


def set_current_style(style_name: str) -> None:
    """Set the active visual style for the current thread."""
    name = style_name.lower().strip() if style_name else DEFAULT_STYLE
    if name not in VALID_STYLES:
        print(f"[STYLE_ENGINE] Unknown style '{name}', falling back to '{DEFAULT_STYLE}'")
        name = DEFAULT_STYLE
    _style_ctx.style = name
    print(f"[STYLE_ENGINE] Active style set to '{name}'")


def get_current_style() -> str:
    """Get the active visual style for the current thread."""
    return getattr(_style_ctx, "style", DEFAULT_STYLE)


# ─────────────────────────────────────────
# Style palettes
# ─────────────────────────────────────────

# Each style defines palettes for node categories and containers.
# Categories: compute, database, security, network, client, storage, monitoring, queue

STYLE_PALETTES: Dict[str, Dict[str, Dict[str, str]]] = {
    # ── Classic (default pastel) ────────────────────────
    "classic": {
        "compute":    {"fill": "#dae8fc", "stroke": "#6c8ebf", "font": "#0f2537"},
        "database":   {"fill": "#d5e8d4", "stroke": "#82b366", "font": "#1b3012"},
        "security":   {"fill": "#f8cecc", "stroke": "#b85450", "font": "#3a1513"},
        "network":    {"fill": "#fff2cc", "stroke": "#d6b656", "font": "#3d3210"},
        "client":     {"fill": "#e1d5e7", "stroke": "#9673a6", "font": "#271233"},
        "storage":    {"fill": "#f5f5f5", "stroke": "#666666", "font": "#1a1a1a"},
        "monitoring": {"fill": "#fff2cc", "stroke": "#d6b656", "font": "#3d3210"},
        "queue":      {"fill": "#dae8fc", "stroke": "#6c8ebf", "font": "#0f2537"},
    },

    # ── AI Icons (vibrant AI palette) ──────────────────
    "aiicons": {
        "compute":    {"fill": "#1a1a2e", "stroke": "#e94560", "font": "#eaeaea"},
        "database":   {"fill": "#16213e", "stroke": "#0f3460", "font": "#e94560"},
        "security":   {"fill": "#1a1a2e", "stroke": "#533483", "font": "#e94560"},
        "network":    {"fill": "#0f3460", "stroke": "#e94560", "font": "#eaeaea"},
        "client":     {"fill": "#533483", "stroke": "#e94560", "font": "#eaeaea"},
        "storage":    {"fill": "#16213e", "stroke": "#0f3460", "font": "#eaeaea"},
        "monitoring": {"fill": "#1a1a2e", "stroke": "#e94560", "font": "#eaeaea"},
        "queue":      {"fill": "#0f3460", "stroke": "#533483", "font": "#eaeaea"},
    },

    # ── AWS Icons (AWS orange / dark) ──────────────────
    "aws_icons": {
        "compute":    {"fill": "#232f3e", "stroke": "#ff9900", "font": "#ffffff"},
        "database":   {"fill": "#232f3e", "stroke": "#3b48cc", "font": "#ffffff"},
        "security":   {"fill": "#232f3e", "stroke": "#dd344c", "font": "#ffffff"},
        "network":    {"fill": "#232f3e", "stroke": "#8c4fff", "font": "#ffffff"},
        "client":     {"fill": "#232f3e", "stroke": "#067f68", "font": "#ffffff"},
        "storage":    {"fill": "#232f3e", "stroke": "#3b48cc", "font": "#ffffff"},
        "monitoring": {"fill": "#232f3e", "stroke": "#e7157b", "font": "#ffffff"},
        "queue":      {"fill": "#232f3e", "stroke": "#e7157b", "font": "#ffffff"},
    },

    # ── Azure Icons (Azure blue) ───────────────────────
    "azure_icons": {
        "compute":    {"fill": "#0078d4", "stroke": "#005a9e", "font": "#ffffff"},
        "database":   {"fill": "#003d6b", "stroke": "#0078d4", "font": "#ffffff"},
        "security":   {"fill": "#5c2d91", "stroke": "#b4a0ff", "font": "#ffffff"},
        "network":    {"fill": "#0078d4", "stroke": "#50e6ff", "font": "#ffffff"},
        "client":     {"fill": "#005a9e", "stroke": "#50e6ff", "font": "#ffffff"},
        "storage":    {"fill": "#003d6b", "stroke": "#0078d4", "font": "#ffffff"},
        "monitoring": {"fill": "#5c2d91", "stroke": "#b4a0ff", "font": "#ffffff"},
        "queue":      {"fill": "#0078d4", "stroke": "#50e6ff", "font": "#ffffff"},
    },

    # ── GCP Icons (Google multi-color) ─────────────────
    "gcp_icons": {
        "compute":    {"fill": "#4285f4", "stroke": "#1a73e8", "font": "#ffffff"},
        "database":   {"fill": "#34a853", "stroke": "#1e8e3e", "font": "#ffffff"},
        "security":   {"fill": "#ea4335", "stroke": "#c5221f", "font": "#ffffff"},
        "network":    {"fill": "#fbbc04", "stroke": "#f9ab00", "font": "#202124"},
        "client":     {"fill": "#4285f4", "stroke": "#1a73e8", "font": "#ffffff"},
        "storage":    {"fill": "#34a853", "stroke": "#1e8e3e", "font": "#ffffff"},
        "monitoring": {"fill": "#ea4335", "stroke": "#c5221f", "font": "#ffffff"},
        "queue":      {"fill": "#fbbc04", "stroke": "#f9ab00", "font": "#202124"},
    },

    # ── K8s Icons (Kubernetes navy) ────────────────────
    "k8s_icons": {
        "compute":    {"fill": "#326ce5", "stroke": "#ffffff", "font": "#ffffff"},
        "database":   {"fill": "#1d3557", "stroke": "#326ce5", "font": "#ffffff"},
        "security":   {"fill": "#1d3557", "stroke": "#e63946", "font": "#ffffff"},
        "network":    {"fill": "#326ce5", "stroke": "#a8dadc", "font": "#ffffff"},
        "client":     {"fill": "#457b9d", "stroke": "#a8dadc", "font": "#ffffff"},
        "storage":    {"fill": "#1d3557", "stroke": "#326ce5", "font": "#ffffff"},
        "monitoring": {"fill": "#1d3557", "stroke": "#e63946", "font": "#ffffff"},
        "queue":      {"fill": "#326ce5", "stroke": "#a8dadc", "font": "#ffffff"},
    },

    # ── DrawIO Skill (vivid, large icons, dashed) ──────
    "drawio_skill": {
        "compute":    {"fill": "#f0f4ff", "stroke": "#4361ee", "font": "#1b1b2f"},
        "database":   {"fill": "#f0fff4", "stroke": "#06d6a0", "font": "#1b1b2f"},
        "security":   {"fill": "#fff0f0", "stroke": "#ef476f", "font": "#1b1b2f"},
        "network":    {"fill": "#fffbf0", "stroke": "#ffd166", "font": "#1b1b2f"},
        "client":     {"fill": "#f5f0ff", "stroke": "#7209b7", "font": "#1b1b2f"},
        "storage":    {"fill": "#f0f4ff", "stroke": "#118ab2", "font": "#1b1b2f"},
        "monitoring": {"fill": "#fff5f0", "stroke": "#e76f51", "font": "#1b1b2f"},
        "queue":      {"fill": "#f0fff8", "stroke": "#2ec4b6", "font": "#1b1b2f"},
    },

    # ── Minimal (monochrome) ──────────────────────────
    "minimal": {
        "compute":    {"fill": "#ffffff", "stroke": "#333333", "font": "#111111"},
        "database":   {"fill": "#f9f9f9", "stroke": "#555555", "font": "#111111"},
        "security":   {"fill": "#ffffff", "stroke": "#333333", "font": "#111111"},
        "network":    {"fill": "#f9f9f9", "stroke": "#555555", "font": "#111111"},
        "client":     {"fill": "#ffffff", "stroke": "#333333", "font": "#111111"},
        "storage":    {"fill": "#f9f9f9", "stroke": "#555555", "font": "#111111"},
        "monitoring": {"fill": "#ffffff", "stroke": "#333333", "font": "#111111"},
        "queue":      {"fill": "#f9f9f9", "stroke": "#555555", "font": "#111111"},
    },
}


# ─────────────────────────────────────────
# Container style overrides per visual style
# ─────────────────────────────────────────

CONTAINER_STYLES: Dict[str, str] = {
    "classic": (
        "rounded=1;arcSize=8;fillColor=none;strokeColor=#4a5568;strokeWidth=2;"
        "dashed=1;verticalAlign=top;align=center;fontStyle=1;fontSize=12;fontColor=#2d3748;"
    ),
    "aiicons": (
        "rounded=1;arcSize=12;fillColor=#1a1a2e;strokeColor=#e94560;strokeWidth=2;"
        "dashed=1;opacity=30;verticalAlign=top;align=center;fontStyle=1;fontSize=13;fontColor=#e94560;"
    ),
    "aws_icons": (
        "rounded=1;arcSize=8;fillColor=#f2f3f4;strokeColor=#ff9900;strokeWidth=2;"
        "dashed=0;shadow=1;verticalAlign=top;align=center;fontStyle=1;fontSize=12;fontColor=#232f3e;"
    ),
    "azure_icons": (
        "rounded=1;arcSize=8;fillColor=#e8f4fd;strokeColor=#0078d4;strokeWidth=2;"
        "dashed=0;shadow=1;verticalAlign=top;align=center;fontStyle=1;fontSize=12;fontColor=#003d6b;"
    ),
    "gcp_icons": (
        "rounded=1;arcSize=8;fillColor=#f8f9fa;strokeColor=#4285f4;strokeWidth=2;"
        "dashed=0;shadow=1;verticalAlign=top;align=center;fontStyle=1;fontSize=12;fontColor=#202124;"
    ),
    "k8s_icons": (
        "rounded=1;arcSize=10;fillColor=#ffffff;strokeColor=#326ce5;strokeWidth=2;"
        "dashed=1;verticalAlign=top;align=center;fontStyle=1;fontSize=12;fontColor=#1d3557;"
    ),
    "drawio_skill": (
        "rounded=1;arcSize=14;fillColor=none;strokeColor=#4361ee;strokeWidth=3;"
        "dashed=1;dashPattern=8 4;shadow=1;verticalAlign=top;align=center;fontStyle=1;fontSize=14;fontColor=#1b1b2f;"
    ),
    "minimal": (
        "rounded=0;fillColor=none;strokeColor=#999999;strokeWidth=1;"
        "dashed=1;verticalAlign=top;align=center;fontStyle=0;fontSize=11;fontColor=#444444;"
    ),
}


def get_palette(category: str) -> Dict[str, str]:
    """Get the color palette for a node category under the current style."""
    style = get_current_style()
    palette = STYLE_PALETTES.get(style, STYLE_PALETTES["classic"])
    return palette.get(category, palette.get("storage", {"fill": "#f5f5f5", "stroke": "#666666", "font": "#1a1a1a"}))


def get_container_style() -> str:
    """Get the container Draw.io style string under the current style."""
    style = get_current_style()
    return CONTAINER_STYLES.get(style, CONTAINER_STYLES["classic"])


def should_use_image_shapes() -> bool:
    """Returns True if the current style prefers image-based node rendering."""
    return get_current_style() in {"aiicons", "aws_icons", "azure_icons", "gcp_icons", "k8s_icons", "drawio_skill"}


def should_suppress_logos() -> bool:
    """Returns True if the current style should hide logos (monochrome, minimal)."""
    return get_current_style() == "minimal"


def get_node_size_hint() -> Dict[str, int]:
    """Returns preferred node dimensions for the current style."""
    style = get_current_style()
    if style == "drawio_skill":
        return {"w": 180, "h": 100}  # larger for big icons
    elif style == "minimal":
        return {"w": 140, "h": 60}
    return {"w": 160, "h": 80}
