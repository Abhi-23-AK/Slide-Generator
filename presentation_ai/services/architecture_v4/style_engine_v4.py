#!/usr/bin/env python3
"""
Style Presets Engine for Architecture V4
======================================
Provides thread-safe access to visual presets (palette colors, typography,
containers, and edge styles) for the V4 engine.
Acts as the central visual authority for Architecture V4, similar to drawio-skill's philosophy.
"""

import threading
from typing import Dict, Any, Optional, Tuple

# Thread-local storage for active style context
_style_ctx = threading.local()

VALID_STYLES = {
    "classic", "drawio_vivid", "ai_dark_neon", "aws",
    "azure", "gcp", "kubernetes", "minimal"
}

DEFAULT_STYLE = "classic"

# Aspect Ratio Registry (Problem 8)
TARGET_RATIO = 1.875
MIN_RATIO = 1.75
MAX_RATIO = 1.95

# Edge Width Registry (Problem 10)
EDGE_WIDTHS = {
    "critical": 3.5,
    "normal": 2.0,
    "monitoring": 1.5,
    "feedback": 2.0
}

# Icon Size Registry (Problem 4)
ICON_SIZE_BY_STYLE = {
    "drawio_vivid": 110.0,
    "ai_dark_neon": 90.0,
    "aws": 75.0,
    "azure": 75.0,
    "gcp": 75.0,
    "kubernetes": 75.0,
    "classic": 75.0,
    "minimal": 70.0
}

ICON_SIZE_BY_TOPOLOGY = {
    "cnn_pipeline": 0.9,
    "transformer_pipeline": 0.9,
    "microservices": 1.15,
    "cloud": 1.15,
    "rag_pipeline": 1.15,
    "ai_pipeline": 1.15
}

# Label Placement Registry (Problem 5)
LABEL_PLACEMENT_BY_STYLE = {
    "aws": {"labelPosition": "right", "align": "left", "verticalAlign": "middle"},
    "azure": {"labelPosition": "right", "align": "left", "verticalAlign": "middle"},
    "gcp": {"labelPosition": "right", "align": "left", "verticalAlign": "middle"},
    "kubernetes": {"labelPosition": "right", "align": "left", "verticalAlign": "middle"}
}

LABEL_PLACEMENT_BY_TOPOLOGY = {
    "cnn_pipeline": {"verticalLabelPosition": "bottom", "verticalAlign": "top", "align": "center"},
    "transformer_pipeline": {"verticalLabelPosition": "bottom", "verticalAlign": "top", "align": "center"},
    "rag_pipeline": {"verticalLabelPosition": "bottom", "verticalAlign": "top", "align": "center"},
    "ai_pipeline": {"verticalLabelPosition": "bottom", "verticalAlign": "top", "align": "center"}
}

# Shadow Styles Registry (Problem 6)
SHADOW_STYLES = {
    "drawio_vivid": {"shadow": "1"},
    "ai_dark_neon": {"shadow": "1", "shadowColor": "#bd00ff"},
    "aws": {"shadow": "1"},
    "azure": {"shadow": "1"},
    "gcp": {"shadow": "1"},
    "kubernetes": {"shadow": "0"},
    "classic": {"shadow": "0"},
    "minimal": {"shadow": "0"}
}

# Geometry Registry (Problem 7)
GEOMETRY_REGISTRY = {
    "transformer_pipeline": (90.0, 135.0),
    "cnn_pipeline": (90.0, 90.0),
    "microservices": (140.0, 70.0),
    "cloud": (140.0, 70.0),
    "rag_pipeline": (140.0, 70.0),
    "ai_pipeline": (140.0, 70.0)
}

# Typography Registry (Problem 9)
TYPOGRAPHY_REGISTRY = {
    "classic": {
        "fontFamily": "Helvetica",
        "family": "Helvetica",
        "fontSize": 14,
        "size": 14,
        "titleFontSize": 16,
        "titleBold": True,
        "fontWeight": "normal",
        "labelWeight": "normal",
        "titleWeight": "bold",
        "fontStyle": "1"
    },
    "drawio_vivid": {
        "fontFamily": "Outfit, Helvetica",
        "family": "Outfit, Helvetica",
        "fontSize": 14,
        "size": 14,
        "titleFontSize": 16,
        "titleBold": True,
        "fontWeight": "bold",
        "labelWeight": "bold",
        "titleWeight": "bold",
        "fontStyle": "1"
    },
    "ai_dark_neon": {
        "fontFamily": "Inter, Roboto",
        "family": "Inter, Roboto",
        "fontSize": 14,
        "size": 14,
        "titleFontSize": 16,
        "titleBold": True,
        "fontWeight": "bold",
        "labelWeight": "bold",
        "titleWeight": "bold",
        "fontStyle": "1"
    },
    "aws": {
        "fontFamily": "Arial, sans-serif",
        "family": "Arial, sans-serif",
        "fontSize": 14,
        "size": 14,
        "titleFontSize": 16,
        "titleBold": True,
        "fontWeight": "semibold",
        "labelWeight": "semibold",
        "titleWeight": "bold",
        "fontStyle": "1"
    },
    "azure": {
        "fontFamily": "Segoe UI, Arial",
        "family": "Segoe UI, Arial",
        "fontSize": 14,
        "size": 14,
        "titleFontSize": 16,
        "titleBold": True,
        "fontWeight": "semibold",
        "labelWeight": "semibold",
        "titleWeight": "bold",
        "fontStyle": "1"
    },
    "gcp": {
        "fontFamily": "Roboto, Arial",
        "family": "Roboto, Arial",
        "fontSize": 14,
        "size": 14,
        "titleFontSize": 16,
        "titleBold": True,
        "fontWeight": "semibold",
        "labelWeight": "semibold",
        "titleWeight": "bold",
        "fontStyle": "1"
    },
    "kubernetes": {
        "fontFamily": "Helvetica, sans-serif",
        "family": "Helvetica, sans-serif",
        "fontSize": 14,
        "size": 14,
        "titleFontSize": 16,
        "titleBold": True,
        "fontWeight": "semibold",
        "labelWeight": "semibold",
        "titleWeight": "bold",
        "fontStyle": "1"
    },
    "minimal": {
        "fontFamily": "Helvetica, Arial",
        "family": "Helvetica, Arial",
        "fontSize": 12,
        "size": 12,
        "titleFontSize": 14,
        "titleBold": False,
        "fontWeight": "normal",
        "labelWeight": "normal",
        "titleWeight": "normal",
        "fontStyle": "0"
    }
}

# Confidence Styles Registry (Problem 11)
CONFIDENCE_STYLES = {
    "high": {"strokeWidth": "2.5"},
    "medium": {"strokeWidth": "2.0"},
    "low": {"strokeWidth": "1.0"}
}

def set_current_style(style_name: str) -> None:
    """Set the active visual style for the current thread."""
    name = style_name.lower().strip() if style_name else DEFAULT_STYLE
    if name == "aws_icons" or name == "aws":
        name = "aws"
    elif name == "azure_icons" or name == "azure":
        name = "azure"
    elif name == "gcp_icons" or name == "gcp":
        name = "gcp"
    elif name == "k8s_icons" or name == "kubernetes":
        name = "kubernetes"
    elif name == "aiicons" or name == "ai_dark_neon":
        name = "ai_dark_neon"
    elif name == "drawio_skill" or name == "drawio_vivid":
        name = "drawio_vivid"
        
    if name not in VALID_STYLES:
        print(f"[STYLE_ENGINE_V4] Unknown style '{style_name}', falling back to '{DEFAULT_STYLE}'")
        name = DEFAULT_STYLE
    _style_ctx.style = name
    print(f"[STYLE_ENGINE_V4] Active style set to '{name}'")

def get_current_style() -> str:
    """Get the active visual style for the current thread."""
    return getattr(_style_ctx, "style", DEFAULT_STYLE)

# Presets styling database stored as dictionary properties (Problem 12)
STYLE_CONFIGS: Dict[str, Dict[str, Any]] = {
    # ── CLASSIC (Standard pastel/draw.io) ──────────────────
    "classic": {
        "palette": {
            "compute":    {"fill": "#dae8fc", "stroke": "#6c8ebf", "font": "#0f2537"},
            "database":   {"fill": "#d5e8d4", "stroke": "#82b366", "font": "#1b3012"},
            "security":   {"fill": "#f8cecc", "stroke": "#b85450", "font": "#3a1513"},
            "network":    {"fill": "#fff2cc", "stroke": "#d6b656", "font": "#3d3210"},
            "client":     {"fill": "#e1d5e7", "stroke": "#9673a6", "font": "#271233"},
            "storage":    {"fill": "#f5f5f5", "stroke": "#666666", "font": "#1a1a1a"},
            "monitoring": {"fill": "#fff2cc", "stroke": "#d6b656", "font": "#3d3210"},
            "queue":      {"fill": "#dae8fc", "stroke": "#6c8ebf", "font": "#0f2537"},
        },
        "container": {
            "rounded": "1",
            "arcSize": "8",
            "fillColor": "none",
            "strokeColor": "#4a5568",
            "strokeWidth": "2",
            "dashed": "1",
            "verticalAlign": "top",
            "align": "center",
            "fontStyle": "1",
            "fontSize": "16",
            "fontColor": "#2d3748",
            "html": "1",
            "whiteSpace": "wrap"
        },
        "edge": {
            "edgeStyle": "orthogonalEdgeStyle",
            "rounded": "0",
            "orthogonalLoop": "1",
            "jettySize": "auto",
            "html": "1",
            "strokeColor": "#4a5568",
            "strokeWidth": "2",
            "fontSize": "10",
            "fontColor": "#000000",
            "fontStyle": "1"
        }
    },

    # ── DRAWIO VIVID (Vivid colors, dashed containers, sketch-feel) ──────────────────
    "drawio_vivid": {
        "palette": {
            "compute":    {"fill": "#f0f4ff", "stroke": "#4361ee", "font": "#1b1b2f"},
            "database":   {"fill": "#f0fff4", "stroke": "#06d6a0", "font": "#1b1b2f"},
            "security":   {"fill": "#fff0f0", "stroke": "#ef476f", "font": "#1b1b2f"},
            "network":    {"fill": "#fffbf0", "stroke": "#ffd166", "font": "#1b1b2f"},
            "client":     {"fill": "#f5f0ff", "stroke": "#7209b7", "font": "#1b1b2f"},
            "storage":    {"fill": "#f0f4ff", "stroke": "#118ab2", "font": "#1b1b2f"},
            "monitoring": {"fill": "#fff5f0", "stroke": "#e76f51", "font": "#1b1b2f"},
            "queue":      {"fill": "#f0fff8", "stroke": "#2ec4b6", "font": "#1b1b2f"},
        },
        "container": {
            "rounded": "1",
            "arcSize": "14",
            "fillColor": "none",
            "strokeColor": "#4361ee",
            "strokeWidth": "3",
            "dashed": "1",
            "dashPattern": "8 4",
            "shadow": "1",
            "verticalAlign": "top",
            "align": "center",
            "fontStyle": "1",
            "fontSize": "16",
            "fontColor": "#1b1b2f",
            "html": "1",
            "whiteSpace": "wrap"
        },
        "edge": {
            "edgeStyle": "orthogonalEdgeStyle",
            "rounded": "1",
            "orthogonalLoop": "1",
            "jettySize": "auto",
            "html": "1",
            "strokeColor": "#4361ee",
            "strokeWidth": "2",
            "fontSize": "10",
            "fontColor": "#1b1b2f",
            "fontStyle": "1"
        }
    },

    # ── AI DARK NEON (Dark, neon magenta/purple accents, glows) ──────────────────
    "ai_dark_neon": {
        "palette": {
            "compute":    {"fill": "#0f0f1b", "stroke": "#ff2a5f", "font": "#ffffff"},
            "database":   {"fill": "#09122c", "stroke": "#00f0ff", "font": "#ffffff"},
            "security":   {"fill": "#0f0f1b", "stroke": "#bd00ff", "font": "#ffffff"},
            "network":    {"fill": "#09122c", "stroke": "#00f0ff", "font": "#ffffff"},
            "client":     {"fill": "#18002a", "stroke": "#ff2a5f", "font": "#ffffff"},
            "storage":    {"fill": "#09122c", "stroke": "#00f0ff", "font": "#ffffff"},
            "monitoring": {"fill": "#0f0f1b", "stroke": "#bd00ff", "font": "#ffffff"},
            "queue":      {"fill": "#09122c", "stroke": "#bd00ff", "font": "#ffffff"},
        },
        "container": {
            "rounded": "1",
            "arcSize": "12",
            "fillColor": "#080810",
            "strokeColor": "#bd00ff",
            "strokeWidth": "2",
            "dashed": "1",
            "verticalAlign": "top",
            "align": "center",
            "fontStyle": "1",
            "fontSize": "16",
            "fontColor": "#ffffff",
            "html": "1",
            "whiteSpace": "wrap"
        },
        "edge": {
            "edgeStyle": "orthogonalEdgeStyle",
            "rounded": "1",
            "orthogonalLoop": "1",
            "jettySize": "auto",
            "html": "1",
            "strokeColor": "#ff2a5f",
            "strokeWidth": "2.5",
            "fontSize": "10",
            "fontColor": "#ffffff",
            "fontStyle": "1"
        }
    },

    # ── AWS (Official AWS theme) ──────────────────
    "aws": {
        "palette": {
            "compute":    {"fill": "#232f3e", "stroke": "#ff9900", "font": "#ffffff"},
            "database":   {"fill": "#232f3e", "stroke": "#3b48cc", "font": "#ffffff"},
            "security":   {"fill": "#232f3e", "stroke": "#dd344c", "font": "#ffffff"},
            "network":    {"fill": "#232f3e", "stroke": "#8c4fff", "font": "#ffffff"},
            "client":     {"fill": "#232f3e", "stroke": "#067f68", "font": "#ffffff"},
            "storage":    {"fill": "#232f3e", "stroke": "#3b48cc", "font": "#ffffff"},
            "monitoring": {"fill": "#232f3e", "stroke": "#e7157b", "font": "#ffffff"},
            "queue":      {"fill": "#232f3e", "stroke": "#e7157b", "font": "#ffffff"},
        },
        "container": {
            "rounded": "1",
            "arcSize": "8",
            "fillColor": "#f2f3f4",
            "strokeColor": "#ff9900",
            "strokeWidth": "2",
            "dashed": "0",
            "shadow": "1",
            "verticalAlign": "top",
            "align": "center",
            "fontStyle": "1",
            "fontSize": "16",
            "fontColor": "#232f3e",
            "html": "1",
            "whiteSpace": "wrap"
        },
        "edge": {
            "edgeStyle": "orthogonalEdgeStyle",
            "rounded": "0",
            "orthogonalLoop": "1",
            "jettySize": "auto",
            "html": "1",
            "strokeColor": "#ff9900",
            "strokeWidth": "2",
            "fontSize": "10",
            "fontColor": "#232f3e",
            "fontStyle": "1"
        }
    },

    # ── AZURE (Official Azure blue) ──────────────────
    "azure": {
        "palette": {
            "compute":    {"fill": "#0078d4", "stroke": "#005a9e", "font": "#ffffff"},
            "database":   {"fill": "#003d6b", "stroke": "#0078d4", "font": "#ffffff"},
            "security":   {"fill": "#5c2d91", "stroke": "#b4a0ff", "font": "#ffffff"},
            "network":    {"fill": "#0078d4", "stroke": "#50e6ff", "font": "#ffffff"},
            "client":     {"fill": "#005a9e", "stroke": "#50e6ff", "font": "#ffffff"},
            "storage":    {"fill": "#003d6b", "stroke": "#0078d4", "font": "#ffffff"},
            "monitoring": {"fill": "#5c2d91", "stroke": "#b4a0ff", "font": "#ffffff"},
            "queue":      {"fill": "#0078d4", "stroke": "#50e6ff", "font": "#ffffff"},
        },
        "container": {
            "rounded": "1",
            "arcSize": "8",
            "fillColor": "#e8f4fd",
            "strokeColor": "#0078d4",
            "strokeWidth": "2",
            "dashed": "0",
            "shadow": "1",
            "verticalAlign": "top",
            "align": "center",
            "fontStyle": "1",
            "fontSize": "16",
            "fontColor": "#003d6b",
            "html": "1",
            "whiteSpace": "wrap"
        },
        "edge": {
            "edgeStyle": "orthogonalEdgeStyle",
            "rounded": "0",
            "orthogonalLoop": "1",
            "jettySize": "auto",
            "html": "1",
            "strokeColor": "#0078d4",
            "strokeWidth": "2",
            "fontSize": "10",
            "fontColor": "#003d6b",
            "fontStyle": "1"
        }
    },

    # ── GCP (Google Multi-Color) ──────────────────
    "gcp": {
        "palette": {
            "compute":    {"fill": "#4285f4", "stroke": "#1a73e8", "font": "#ffffff"},
            "database":   {"fill": "#34a853", "stroke": "#1e8e3e", "font": "#ffffff"},
            "security":   {"fill": "#ea4335", "stroke": "#c5221f", "font": "#ffffff"},
            "network":    {"fill": "#fbbc04", "stroke": "#f9ab00", "font": "#202124"},
            "client":     {"fill": "#4285f4", "stroke": "#1a73e8", "font": "#ffffff"},
            "storage":    {"fill": "#34a853", "stroke": "#1e8e3e", "font": "#ffffff"},
            "monitoring": {"fill": "#ea4335", "stroke": "#c5221f", "font": "#ffffff"},
            "queue":      {"fill": "#fbbc04", "stroke": "#f9ab00", "font": "#202124"},
        },
        "container": {
            "rounded": "1",
            "arcSize": "8",
            "fillColor": "#f8f9fa",
            "strokeColor": "#4285f4",
            "strokeWidth": "2",
            "dashed": "0",
            "shadow": "1",
            "verticalAlign": "top",
            "align": "center",
            "fontStyle": "1",
            "fontSize": "16",
            "fontColor": "#202124",
            "html": "1",
            "whiteSpace": "wrap"
        },
        "edge": {
            "edgeStyle": "orthogonalEdgeStyle",
            "rounded": "0",
            "orthogonalLoop": "1",
            "jettySize": "auto",
            "html": "1",
            "strokeColor": "#4285f4",
            "strokeWidth": "2",
            "fontSize": "10",
            "fontColor": "#202124",
            "fontStyle": "1"
        }
    },

    # ── KUBERNETES (K8s Navy/Blue) ──────────────────
    "kubernetes": {
        "palette": {
            "compute":    {"fill": "#326ce5", "stroke": "#1d3557", "font": "#ffffff"},
            "database":   {"fill": "#1d3557", "stroke": "#326ce5", "font": "#ffffff"},
            "security":   {"fill": "#1d3557", "stroke": "#e63946", "font": "#ffffff"},
            "network":    {"fill": "#326ce5", "stroke": "#a8dadc", "font": "#ffffff"},
            "client":     {"fill": "#457b9d", "stroke": "#a8dadc", "font": "#ffffff"},
            "storage":    {"fill": "#1d3557", "stroke": "#326ce5", "font": "#ffffff"},
            "monitoring": {"fill": "#1d3557", "stroke": "#e63946", "font": "#ffffff"},
            "queue":      {"fill": "#326ce5", "stroke": "#a8dadc", "font": "#ffffff"},
        },
        "container": {
            "rounded": "1",
            "arcSize": "10",
            "fillColor": "#ffffff",
            "strokeColor": "#326ce5",
            "strokeWidth": "2",
            "dashed": "1",
            "verticalAlign": "top",
            "align": "center",
            "fontStyle": "1",
            "fontSize": "16",
            "fontColor": "#1d3557",
            "html": "1",
            "whiteSpace": "wrap"
        },
        "edge": {
            "edgeStyle": "orthogonalEdgeStyle",
            "rounded": "0",
            "orthogonalLoop": "1",
            "jettySize": "auto",
            "html": "1",
            "strokeColor": "#326ce5",
            "strokeWidth": "2",
            "fontSize": "10",
            "fontColor": "#1d3557",
            "fontStyle": "1"
        }
    },

    # ── MINIMAL (Clean Monochrome) ──────────────────
    "minimal": {
        "palette": {
            "compute":    {"fill": "#ffffff", "stroke": "#333333", "font": "#111111"},
            "database":   {"fill": "#ffffff", "stroke": "#333333", "font": "#111111"},
            "security":   {"fill": "#ffffff", "stroke": "#333333", "font": "#111111"},
            "network":    {"fill": "#ffffff", "stroke": "#333333", "font": "#111111"},
            "client":     {"fill": "#ffffff", "stroke": "#333333", "font": "#111111"},
            "storage":    {"fill": "#ffffff", "stroke": "#333333", "font": "#111111"},
            "monitoring": {"fill": "#ffffff", "stroke": "#333333", "font": "#111111"},
            "queue":      {"fill": "#ffffff", "stroke": "#333333", "font": "#111111"},
        },
        "container": {
            "rounded": "0",
            "fillColor": "none",
            "strokeColor": "#999999",
            "strokeWidth": "1",
            "dashed": "1",
            "verticalAlign": "top",
            "align": "center",
            "fontStyle": "0",
            "fontSize": "14",
            "fontColor": "#444444",
            "html": "1",
            "whiteSpace": "wrap"
        },
        "edge": {
            "edgeStyle": "orthogonalEdgeStyle",
            "rounded": "0",
            "orthogonalLoop": "1",
            "jettySize": "auto",
            "html": "1",
            "strokeColor": "#555555",
            "strokeWidth": "1.5",
            "fontSize": "10",
            "fontColor": "#333333",
            "fontStyle": "0"
        }
    }
}

def parse_style_string(style: str) -> Dict[str, str]:
    """Parses a Draw.io style string into a key-value dictionary."""
    res = {}
    if not style:
        return res
    parts = style.split(";")
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if "=" in p:
            k, v = p.split("=", 1)
            res[k.strip()] = v.strip()
        else:
            res[p.strip()] = ""
    return res

def format_style_dict(style_dict: Dict[str, str]) -> str:
    """Formats a style dictionary back to a Draw.io style string."""
    parts = []
    for k, v in style_dict.items():
        if v != "":
            parts.append(f"{k}={v}")
        else:
            parts.append(k)
    return ";".join(parts) + ";"

def normalize_topology(topology: Optional[str]) -> str:
    """Normalizes topology strings to standard aliases. (Problem 13)"""
    if not topology:
        return ""
    t = str(topology).lower().strip()
    if t in ("rag", "rag_pipeline"):
        return "rag_pipeline"
    if t in ("ai", "ai_pipeline"):
        return "ai_pipeline"
    if t in ("transformer", "transformer_pipeline"):
        return "transformer_pipeline"
    if t in ("cnn", "cnn_pipeline"):
        return "cnn_pipeline"
    return t

# Extended Category Palettes builder (Problem 1)
def _get_expanded_palette(style_name: str) -> Dict[str, Dict[str, str]]:
    cfg = STYLE_CONFIGS.get(style_name, STYLE_CONFIGS[DEFAULT_STYLE])
    base = cfg["palette"]
    
    # Clone base palette
    palette = {k: dict(v) for k, v in base.items()}
    
    if style_name == "classic":
        # Greenish database variants
        palette["vector_db"] = {"fill": "#e2f0d9", "stroke": "#38b000", "font": "#0f3a00"}
        palette["cache"] = {"fill": "#e2f0d9", "stroke": "#70e000", "font": "#0f3a00"}
        palette["storage"] = {"fill": "#f5f5f5", "stroke": "#666666", "font": "#1a1a1a"}
        # Purple/Indigo AI variants
        palette["llm"] = {"fill": "#ebdcf5", "stroke": "#7209b7", "font": "#240046"}
        palette["agent"] = {"fill": "#ffe6cc", "stroke": "#f77f00", "font": "#3d1400"}
        palette["embedding"] = {"fill": "#dae8fc", "stroke": "#4895ef", "font": "#0f2537"}
        palette["retriever"] = {"fill": "#e1d5e7", "stroke": "#9673a6", "font": "#271233"}
        palette["orchestrator"] = {"fill": "#f5f5f5", "stroke": "#7209b7", "font": "#240046"}
        # Neural Network Layer variants
        palette["model"] = {"fill": "#ebdcf5", "stroke": "#9673a6", "font": "#271233"}
        palette["encoder"] = {"fill": "#e1d5e7", "stroke": "#7209b7", "font": "#240046"}
        palette["decoder"] = {"fill": "#e1d5e7", "stroke": "#7209b7", "font": "#240046"}
        palette["conv"] = {"fill": "#f8cecc", "stroke": "#b85450", "font": "#3a1513"}
        palette["pool"] = {"fill": "#f8cecc", "stroke": "#b85450", "font": "#3a1513"}
        palette["dense"] = {"fill": "#f8cecc", "stroke": "#b85450", "font": "#3a1513"}
        # Network/Gateways
        palette["gateway"] = {"fill": "#fff2cc", "stroke": "#f77f00", "font": "#3d1400"}
        palette["api"] = {"fill": "#fff2cc", "stroke": "#d6b656", "font": "#3d3210"}
        palette["proxy"] = {"fill": "#f5f5f5", "stroke": "#d6b656", "font": "#3d3210"}
        # Compute/Containers
        palette["container"] = {"fill": "#dae8fc", "stroke": "#4cc9f0", "font": "#0f2537"}
        palette["worker"] = {"fill": "#dae8fc", "stroke": "#6c8ebf", "font": "#0f2537"}
        palette["backend"] = {"fill": "#dae8fc", "stroke": "#4895ef", "font": "#0f2537"}
        palette["frontend"] = {"fill": "#e1d5e7", "stroke": "#4895ef", "font": "#271233"}
        palette["framework"] = {"fill": "#dae8fc", "stroke": "#6c8ebf", "font": "#0f2537"}
        palette["tool"] = {"fill": "#ffe6cc", "stroke": "#d6b656", "font": "#3d3210"}
        # Queues/Streams
        palette["message_broker"] = {"fill": "#dae8fc", "stroke": "#6c8ebf", "font": "#0f2537"}
        palette["stream"] = {"fill": "#dae8fc", "stroke": "#4cc9f0", "font": "#0f2537"}
        palette["event"] = {"fill": "#dae8fc", "stroke": "#4895ef", "font": "#0f2537"}
        # Monitoring/Analytics
        palette["analytics"] = {"fill": "#fff2cc", "stroke": "#b85450", "font": "#3d3210"}
        palette["logging"] = {"fill": "#fff2cc", "stroke": "#d6b656", "font": "#3d3210"}
        palette["observability"] = {"fill": "#f8cecc", "stroke": "#b85450", "font": "#3a1513"}
        palette["dataset"] = {"fill": "#d5e8d4", "stroke": "#666666", "font": "#1a1a1a"}
        palette["search"] = {"fill": "#fff2cc", "stroke": "#f77f00", "font": "#3d1400"}
        
    elif style_name == "drawio_vivid":
        # Greenish database variants
        palette["vector_db"] = {"fill": "#e6fffa", "stroke": "#00b5ad", "font": "#1b1b2f"}
        palette["cache"] = {"fill": "#f0fff4", "stroke": "#2ec4b6", "font": "#1b1b2f"}
        palette["storage"] = {"fill": "#f0f4ff", "stroke": "#118ab2", "font": "#1b1b2f"}
        # Purple/Indigo AI variants
        palette["llm"] = {"fill": "#faf5ff", "stroke": "#b5179e", "font": "#1b1b2f"}
        palette["agent"] = {"fill": "#fff9db", "stroke": "#f59f00", "font": "#1b1b2f"}
        palette["embedding"] = {"fill": "#f0f4ff", "stroke": "#4895ef", "font": "#1b1b2f"}
        palette["retriever"] = {"fill": "#f5f0ff", "stroke": "#7209b7", "font": "#1b1b2f"}
        palette["orchestrator"] = {"fill": "#faf5ff", "stroke": "#7209b7", "font": "#1b1b2f"}
        # Neural Network Layer variants
        palette["model"] = {"fill": "#faf5ff", "stroke": "#b5179e", "font": "#1b1b2f"}
        palette["encoder"] = {"fill": "#f5f0ff", "stroke": "#7209b7", "font": "#1b1b2f"}
        palette["decoder"] = {"fill": "#f5f0ff", "stroke": "#7209b7", "font": "#1b1b2f"}
        palette["conv"] = {"fill": "#fff5f5", "stroke": "#ff6b6b", "font": "#1b1b2f"}
        palette["pool"] = {"fill": "#fff5f5", "stroke": "#ff6b6b", "font": "#1b1b2f"}
        palette["dense"] = {"fill": "#fff5f5", "stroke": "#ff6b6b", "font": "#1b1b2f"}
        # Network/Gateways
        palette["gateway"] = {"fill": "#fffbf0", "stroke": "#ffd166", "font": "#1b1b2f"}
        palette["api"] = {"fill": "#fffbf0", "stroke": "#fcc419", "font": "#1b1b2f"}
        palette["proxy"] = {"fill": "#f0f4ff", "stroke": "#ffd166", "font": "#1b1b2f"}
        # Compute/Containers
        palette["container"] = {"fill": "#f0f4ff", "stroke": "#4cc9f0", "font": "#1b1b2f"}
        palette["worker"] = {"fill": "#f0f4ff", "stroke": "#4361ee", "font": "#1b1b2f"}
        palette["backend"] = {"fill": "#f0f4ff", "stroke": "#4895ef", "font": "#1b1b2f"}
        palette["frontend"] = {"fill": "#f5f0ff", "stroke": "#7209b7", "font": "#1b1b2f"}
        palette["framework"] = {"fill": "#f0f4ff", "stroke": "#4361ee", "font": "#1b1b2f"}
        palette["tool"] = {"fill": "#fff9db", "stroke": "#ffd166", "font": "#1b1b2f"}
        # Queues/Streams
        palette["message_broker"] = {"fill": "#f0fff8", "stroke": "#2ec4b6", "font": "#1b1b2f"}
        palette["stream"] = {"fill": "#e6fffa", "stroke": "#00b5ad", "font": "#1b1b2f"}
        palette["event"] = {"fill": "#f0fff8", "stroke": "#2ec4b6", "font": "#1b1b2f"}
        # Monitoring/Analytics
        palette["analytics"] = {"fill": "#fff5f0", "stroke": "#e76f51", "font": "#1b1b2f"}
        palette["logging"] = {"fill": "#fffbf0", "stroke": "#e76f51", "font": "#1b1b2f"}
        palette["observability"] = {"fill": "#fff5f0", "stroke": "#e76f51", "font": "#1b1b2f"}
        palette["dataset"] = {"fill": "#f8f9fa", "stroke": "#495057", "font": "#1b1b2f"}
        palette["search"] = {"fill": "#fff9db", "stroke": "#ffd166", "font": "#1b1b2f"}
        
    elif style_name == "ai_dark_neon":
        # Greenish database variants
        palette["vector_db"] = {"fill": "#05161a", "stroke": "#00f0ff", "font": "#ffffff"}
        palette["cache"] = {"fill": "#05161a", "stroke": "#00f0ff", "font": "#ffffff"}
        palette["storage"] = {"fill": "#09122c", "stroke": "#00f0ff", "font": "#ffffff"}
        # Purple/Indigo AI variants
        palette["llm"] = {"fill": "#18002a", "stroke": "#bd00ff", "font": "#ffffff"}
        palette["agent"] = {"fill": "#201000", "stroke": "#ff9900", "font": "#ffffff"}
        palette["embedding"] = {"fill": "#05161a", "stroke": "#bd00ff", "font": "#ffffff"}
        palette["retriever"] = {"fill": "#18002a", "stroke": "#bd00ff", "font": "#ffffff"}
        palette["orchestrator"] = {"fill": "#18002a", "stroke": "#bd00ff", "font": "#ffffff"}
        # Neural Network Layer variants
        palette["model"] = {"fill": "#18002a", "stroke": "#bd00ff", "font": "#ffffff"}
        palette["encoder"] = {"fill": "#18002a", "stroke": "#bd00ff", "font": "#ffffff"}
        palette["decoder"] = {"fill": "#18002a", "stroke": "#bd00ff", "font": "#ffffff"}
        palette["conv"] = {"fill": "#1b0510", "stroke": "#ff2a5f", "font": "#ffffff"}
        palette["pool"] = {"fill": "#1b0510", "stroke": "#ff2a5f", "font": "#ffffff"}
        palette["dense"] = {"fill": "#1b0510", "stroke": "#ff2a5f", "font": "#ffffff"}
        # Network/Gateways
        palette["gateway"] = {"fill": "#09122c", "stroke": "#00f0ff", "font": "#ffffff"}
        palette["api"] = {"fill": "#09122c", "stroke": "#00f0ff", "font": "#ffffff"}
        palette["proxy"] = {"fill": "#09122c", "stroke": "#00f0ff", "font": "#ffffff"}
        # Compute/Containers
        palette["container"] = {"fill": "#0f0f1b", "stroke": "#ff2a5f", "font": "#ffffff"}
        palette["worker"] = {"fill": "#0f0f1b", "stroke": "#ff2a5f", "font": "#ffffff"}
        palette["backend"] = {"fill": "#0f0f1b", "stroke": "#ff2a5f", "font": "#ffffff"}
        palette["frontend"] = {"fill": "#18002a", "stroke": "#ff2a5f", "font": "#ffffff"}
        palette["framework"] = {"fill": "#0f0f1b", "stroke": "#ff2a5f", "font": "#ffffff"}
        palette["tool"] = {"fill": "#201000", "stroke": "#ff9900", "font": "#ffffff"}
        # Queues/Streams
        palette["message_broker"] = {"fill": "#09122c", "stroke": "#bd00ff", "font": "#ffffff"}
        palette["stream"] = {"fill": "#09122c", "stroke": "#bd00ff", "font": "#ffffff"}
        palette["event"] = {"fill": "#09122c", "stroke": "#bd00ff", "font": "#ffffff"}
        # Monitoring/Analytics
        palette["analytics"] = {"fill": "#0f0f1b", "stroke": "#bd00ff", "font": "#ffffff"}
        palette["logging"] = {"fill": "#0f0f1b", "stroke": "#bd00ff", "font": "#ffffff"}
        palette["observability"] = {"fill": "#0f0f1b", "stroke": "#bd00ff", "font": "#ffffff"}
        palette["dataset"] = {"fill": "#09122c", "stroke": "#00f0ff", "font": "#ffffff"}
        palette["search"] = {"fill": "#201000", "stroke": "#ff9900", "font": "#ffffff"}
        
    elif style_name in ("aws", "azure", "gcp", "kubernetes"):
        db_base = base["database"]
        comp_base = base["compute"]
        sec_base = base["security"]
        net_base = base["network"]
        cli_base = base["client"]
        st_base = base["storage"]
        mon_base = base["monitoring"]
        q_base = base["queue"]
        
        # Extended database categories
        palette["vector_db"] = db_base
        palette["cache"] = db_base
        palette["dataset"] = st_base
        # Extended compute categories
        palette["container"] = comp_base
        palette["worker"] = comp_base
        palette["backend"] = comp_base
        palette["frontend"] = cli_base
        palette["framework"] = comp_base
        palette["tool"] = comp_base
        # Extended network categories
        palette["gateway"] = net_base
        palette["api"] = net_base
        palette["proxy"] = net_base
        # Extended queue categories
        palette["message_broker"] = q_base
        palette["stream"] = q_base
        palette["event"] = q_base
        # Extended monitoring categories
        palette["analytics"] = mon_base
        palette["logging"] = mon_base
        palette["observability"] = mon_base
        # Extended AI/ML categories
        palette["llm"] = comp_base
        palette["agent"] = comp_base
        palette["embedding"] = comp_base
        palette["retriever"] = comp_base
        palette["orchestrator"] = comp_base
        palette["model"] = db_base
        palette["encoder"] = comp_base
        palette["decoder"] = comp_base
        palette["conv"] = comp_base
        palette["pool"] = comp_base
        palette["dense"] = comp_base
        palette["search"] = net_base
        
    else: # minimal (monochrome)
        for cat_name in [
            "llm", "vector_db", "framework", "cache", "gateway", "api", "container",
            "analytics", "logging", "observability", "dataset", "embedding", "retriever",
            "agent", "tool", "worker", "frontend", "backend", "proxy", "message_broker",
            "stream", "event", "search", "orchestrator", "model", "encoder", "decoder",
            "conv", "pool", "dense"
        ]:
            palette[cat_name] = {"fill": "#ffffff", "stroke": "#333333", "font": "#111111"}
            
    return palette

def get_palette(category: str, style_name: Optional[str] = None) -> Dict[str, str]:
    """Get the color palette for a node category under the current style. (Problem 1)"""
    style = style_name or get_current_style()
    cat = str(category).lower().strip()
    expanded = _get_expanded_palette(style)
    return expanded.get(cat, expanded.get("storage", {"fill": "#f5f5f5", "stroke": "#666666", "font": "#1a1a1a"}))

def get_font_settings(style_name: Optional[str] = None) -> Dict[str, Any]:
    """Get the font settings under the current style."""
    style = style_name or get_current_style()
    return TYPOGRAPHY_REGISTRY.get(style, TYPOGRAPHY_REGISTRY[DEFAULT_STYLE])

def get_container_style(style_name: Optional[str] = None, topology: Optional[str] = None) -> str:
    """Get the container Draw.io style string under the current style and topology. (Problem 2)"""
    style = style_name or get_current_style()
    cfg = STYLE_CONFIGS.get(style, STYLE_CONFIGS[DEFAULT_STYLE])
    container_dict = dict(cfg["container"])
    
    topo = normalize_topology(topology)
    
    if topo in ("microservices", "cloud"):
        # Cloud: VPC / Subnet groups
        container_dict["strokeWidth"] = "2.5"
        container_dict["arcSize"] = "12"
        container_dict["dashed"] = "0"
        if style == "aws":
            container_dict["fillColor"] = "#f2f3f4"
            container_dict["strokeColor"] = "#ff9900"
        elif style == "azure":
            container_dict["fillColor"] = "#e8f4fd"
            container_dict["strokeColor"] = "#0078d4"
    elif topo == "kubernetes":
        # Kubernetes: Namespaces
        container_dict["dashed"] = "1"
        container_dict["strokeWidth"] = "2"
        container_dict["arcSize"] = "10"
        if style == "kubernetes":
            container_dict["strokeColor"] = "#326ce5"
            container_dict["fillColor"] = "none"
    elif topo == "transformer_pipeline":
        # Transformer: Encoder / Decoder sections
        container_dict["rounded"] = "0"
        container_dict["arcSize"] = "0"
        container_dict["strokeWidth"] = "2"
        container_dict["dashed"] = "0"
    elif topo == "cnn_pipeline":
        # CNN: Layer groups
        container_dict["rounded"] = "1"
        container_dict["arcSize"] = "6"
        container_dict["strokeWidth"] = "1.5"
        container_dict["dashed"] = "1"
    elif topo == "rag_pipeline":
        # RAG: Pipeline stages
        container_dict["dashed"] = "1"
        container_dict["dashPattern"] = "6 3"
        container_dict["arcSize"] = "8"
    elif topo == "event_driven":
        # Event-driven zones
        container_dict["dashed"] = "1"
        container_dict["strokeWidth"] = "2"
        container_dict["fillColor"] = "#fbfbfb" if style != "ai_dark_neon" else "#0a0a12"
        
    return format_style_dict(container_dict)

def get_edge_style(style_name: Optional[str] = None) -> str:
    """Get the base edge Draw.io style string under the current style."""
    style = style_name or get_current_style()
    cfg = STYLE_CONFIGS.get(style, STYLE_CONFIGS[DEFAULT_STYLE])
    return format_style_dict(cfg["edge"])

# ── Unified Visual APIs (Problem 14) ──

def get_node_theme(style_name: Optional[str] = None, category: Optional[str] = None, confidence: float = 1.0) -> str:
    """Returns the complete serialized node style string for a given theme, category, and confidence."""
    style = style_name or get_current_style()
    cat = category or "compute"
    palette = get_palette(cat, style)
    
    font_settings = get_font_settings(style)
    font_family = font_settings.get("fontFamily", "Helvetica")
    font_size = font_settings.get("fontSize", 14)
    font_color = palette.get("font", "#000000")
    font_style = font_settings.get("fontStyle", "1")
    
    # Theme-aware shape overrides
    shape_style = {
        "fillColor": palette.get("fill", "#ffffff"),
        "strokeColor": palette.get("stroke", "#333333"),
        "strokeWidth": "2",
        "rounded": "1",
        "arcSize": "8"
    }
    
    if style == "aws":
        shape_style["strokeColor"] = "#ff9900"
        shape_style["arcSize"] = "8"
    elif style == "azure":
        shape_style["strokeColor"] = "#0078d4"
        shape_style["arcSize"] = "8"
    elif style == "gcp":
        shape_style["strokeColor"] = "#4285f4"
        shape_style["arcSize"] = "8"
    elif style == "kubernetes":
        shape_style["strokeColor"] = "#326ce5"
        shape_style["arcSize"] = "10"
    elif style == "ai_dark_neon":
        shape_style["strokeWidth"] = "2"
        shape_style["arcSize"] = "12"
    elif style == "drawio_vivid":
        shape_style["strokeWidth"] = "3"
        shape_style["arcSize"] = "15"
    elif style == "minimal":
        shape_style["strokeWidth"] = "1"
        shape_style["arcSize"] = "0"
        shape_style["rounded"] = "0"
        
    shadow_cfg = get_shadow_style(style)
    shape_style.update(shadow_cfg)
    
    conf_style = get_confidence_style(confidence)
    shape_style.update(conf_style)
    
    shape_style.update({
        "fontFamily": font_family,
        "fontSize": str(font_size),
        "fontColor": font_color,
        "fontStyle": font_style,
        "align": "center",
        "verticalAlign": "middle",
        "whiteSpace": "wrap",
        "html": "1"
    })
    
    return format_style_dict(shape_style)

def get_edge_theme(edge_metadata: Dict[str, Any], style_name: Optional[str] = None, font_family: Optional[str] = None) -> str:
    """Generates complete edge style properties dynamically based on semantic metadata. (Problem 3)"""
    style = style_name or get_current_style()
    cfg = STYLE_CONFIGS.get(style, STYLE_CONFIGS[DEFAULT_STYLE])
    edge_dict = dict(cfg["edge"])
    
    if font_family:
        edge_dict["fontFamily"] = font_family
        
    stroke_color = edge_dict.get("strokeColor", "#4a5568")
    stroke_width = float(edge_dict.get("strokeWidth", "2"))
    
    is_critical = edge_metadata.get("importance", 1.0) > 1.5 or edge_metadata.get("critical", False)
    is_feedback = edge_metadata.get("back_edge", False) or edge_metadata.get("feedback", False)
    is_monitoring = edge_metadata.get("type") in ("monitoring", "logging", "telemetry", "analytics") or edge_metadata.get("category") == "monitoring"
    is_cross_cluster = edge_metadata.get("cross_cluster", False)
    
    if is_critical:
        stroke_width = EDGE_WIDTHS.get("critical", 3.5)
    elif is_monitoring:
        stroke_width = EDGE_WIDTHS.get("monitoring", 1.5)
    elif is_feedback:
        stroke_width = EDGE_WIDTHS.get("feedback", 2.0)
    else:
        stroke_width = EDGE_WIDTHS.get("normal", 2.0)
        
    edge_dict["strokeWidth"] = str(stroke_width)
    
    if is_cross_cluster:
        stroke_color = get_cross_cluster_color(style)
        
    edge_dict["strokeColor"] = stroke_color
    edge_dict["fontColor"] = stroke_color
    
    if is_feedback:
        edge_dict["dashed"] = "1"
        edge_dict["dashPattern"] = "8 4"
    elif is_monitoring:
        edge_dict["dashed"] = "1"
        edge_dict["dashPattern"] = "1 3"
        
    shadow_cfg = get_shadow_style(style)
    edge_dict.update(shadow_cfg)
    
    if style in ("minimal", "classic", "kubernetes"):
        edge_dict["shadow"] = "0"
        if "shadowColor" in edge_dict:
            del edge_dict["shadowColor"]
            
    return format_style_dict(edge_dict)

def get_geometry(style_name: Optional[str] = None, topology: Optional[str] = None, label: Optional[str] = None, kind: Optional[str] = None) -> Tuple[float, float]:
    """Calculates topology- and theme-aware node dimensions (width, height). (Problem 7)"""
    style = style_name or get_current_style()
    topo = normalize_topology(topology)
    
    orig_w = 160.0
    orig_h = 80.0
    
    label_lower = str(label).lower() if label else ""
    kind_lower = str(kind).lower() if kind else ""
    
    # Check overrides
    if topo == "transformer_pipeline" or "encoder" in label_lower or "decoder" in label_lower or kind_lower in ("encoder", "decoder"):
        return 90.0, 135.0
        
    if topo == "cnn_pipeline" or "cnn" in label_lower or "convolution" in label_lower or kind_lower == "cnn":
        return 90.0, 90.0
        
    if topo == "rag_pipeline" or "retriever" in label_lower or "rag" in label_lower:
        return 120.0, 75.0
        
    if topo in GEOMETRY_REGISTRY:
        return GEOMETRY_REGISTRY[topo]
        
    if style in ("aws", "azure", "gcp", "kubernetes"):
        return 140.0, 70.0
        
    return orig_w, orig_h

def get_icon_size(style_name: Optional[str] = None, topology: Optional[str] = None, category: Optional[str] = None) -> float:
    """Sizes icons combining theme and topology context. (Problem 4)"""
    style = style_name or get_current_style()
    base_size = ICON_SIZE_BY_STYLE.get(style, 75.0)
    
    topo = normalize_topology(topology)
    scale = ICON_SIZE_BY_TOPOLOGY.get(topo, 1.0)
    
    return base_size * scale

def get_shadow_style(style_name: Optional[str] = None) -> Dict[str, str]:
    """Get shadow styles dictionary for specified style. (Problem 6)"""
    style = style_name or get_current_style()
    return SHADOW_STYLES.get(style, {"shadow": "0"})

def get_label_placement(style_name: Optional[str] = None, topology: Optional[str] = None) -> str:
    """Resolves topology- and style-aware label placements. (Problem 5)"""
    style = style_name or get_current_style()
    topo = normalize_topology(topology)
    
    placement = {"verticalLabelPosition": "bottom", "verticalAlign": "top", "align": "center"}
    
    if topo in LABEL_PLACEMENT_BY_TOPOLOGY:
        placement.update(LABEL_PLACEMENT_BY_TOPOLOGY[topo])
    elif style in LABEL_PLACEMENT_BY_STYLE:
        placement.update(LABEL_PLACEMENT_BY_STYLE[style])
        
    return format_style_dict(placement)

def get_confidence_style(confidence: float) -> Dict[str, str]:
    """Exposes style parameters based on confidence level. (Problem 11)"""
    try:
        confidence_float = float(confidence)
    except (ValueError, TypeError):
        confidence_float = 0.0
    if confidence_float > 0.8:
        return CONFIDENCE_STYLES["high"]
    elif confidence_float >= 0.5:
        return CONFIDENCE_STYLES["medium"]
    else:
        return CONFIDENCE_STYLES["low"]

def get_target_ratio() -> float:
    """Returns the widescreen target aspect ratio (15:8). (Problem 8)"""
    return TARGET_RATIO

def get_cross_cluster_color(theme: str) -> str:
    """Get the stroke color for cross-cluster edges under the specified theme."""
    theme_clean = theme.lower().strip() if theme else DEFAULT_STYLE
    if theme_clean in ("aws_icons", "aws"):
        theme_clean = "aws"
    elif theme_clean in ("azure_icons", "azure"):
        theme_clean = "azure"
    elif theme_clean in ("gcp_icons", "gcp"):
        theme_clean = "gcp"
    elif theme_clean in ("k8s_icons", "kubernetes"):
        theme_clean = "kubernetes"
    elif theme_clean in ("aiicons", "ai_dark_neon"):
        theme_clean = "ai_dark_neon"
    elif theme_clean in ("drawio_skill", "drawio_vivid"):
        theme_clean = "drawio_vivid"
        
    if theme_clean == "ai_dark_neon":
        return "#aa1e3f"
    elif theme_clean == "aws":
        return "#ffcc80"
    elif theme_clean == "azure":
        return "#9ec5e8"
    elif theme_clean == "kubernetes":
        return "#9ebbe8"
    elif theme_clean == "gcp":
        return "#fcc934"
    elif theme_clean == "drawio_vivid":
        return "#7b2cbf"
    elif theme_clean == "minimal":
        return "#888888"
    else:
        return "#99a3a4"

if __name__ == "__main__":
    set_current_style("drawio_vivid")
    print(f"Active style: {get_current_style()}")
    print(f"Font settings: {get_font_settings()}")
    print(f"Container style: {get_container_style()}")
    print(f"Compute palette: {get_palette('compute')}")
