import re
from typing import Dict, Any

from services.architecture_v3.style_engine import (
    get_current_style,
    get_palette,
    get_container_style,
    should_use_image_shapes,
)

# Color themes (modern, professional, high-quality aesthetics)
THEMES = {
    "compute": {
        "fill": "#dae8fc",
        "stroke": "#6c8ebf",
        "font": "#0f2537"
    },
    "database": {
        "fill": "#d5e8d4",
        "stroke": "#82b366",
        "font": "#1b3012"
    },
    "security": {
        "fill": "#f8cecc",
        "stroke": "#b85450",
        "font": "#3a1513"
    },
    "network": {
        "fill": "#fff2cc",
        "stroke": "#d6b656",
        "font": "#3d3210"
    },
    "client": {
        "fill": "#e1d5e7",
        "stroke": "#9673a6",
        "font": "#271233"
    },
    "storage": {
        "fill": "#f5f5f5",
        "stroke": "#666666",
        "font": "#1a1a1a"
    },
    "container": {
        "fill": "none",
        "stroke": "#7f8c8d",
        "font": "#2c3e50"
    }
}

SHAPE_PATTERNS = {
    # Database
    r'\b(db|database|postgres|mysql|oracle|sqlite|mongodb|dynamodb|rds|redis|cache|datastore|warehouse|pinecone)\b': "database",
    # Network/Routing
    r'\b(lb|load-balancer|gateway|dns|router|route|nginx|proxy|ingress|egress|vpc|subnet|firewall|waf|vpn|api-gateway|ingress-controller|route53|cloudfront|cdn)\b': "network",
    # Compute
    r'\b(server|compute|instance|ec2|vm|virtual-machine|lambda|function|pod|docker|kubernetes|k8s|worker|microservice|service|api|app|frontend|backend|fastapi|chunker|retriever|prompt-builder|llm|guardrails|memory|loader|document-loader)\b': "compute",
    # Client
    r'\b(client|user|browser|mobile|phone|app-client|consumer|producer)\b': "client",
    # Security
    r'\b(auth|cognito|iam|oauth|key|token|encryption|ssl|tls|kms|vault|guardrails)\b': "security",
    # Monitoring
    r'\b(prometheus|grafana|elk|monitor|logging|alert|metric|dashboard|kibana|logstash|jaeger|zipkin|datadog)\b': "monitoring",
    # Queue / Messaging
    r'\b(kafka|rabbitmq|sqs|sns|queue|message|event-bus|event-hub|pub-sub|stream|nats)\b': "queue",
}

def _classify_node(node_lower: str) -> str:
    """Classify a node into a category based on keyword matching."""
    for pattern, cat in SHAPE_PATTERNS.items():
        if re.search(pattern, node_lower):
            return cat
    return "storage"  # default


def resolve_shape_style(node_name: str, node_type: str = "node") -> Dict[str, Any]:
    """
    Resolves the Draw.io shape and style parameters for a node or container.
    All containers are set with rounded=1.
    
    Now style-aware: queries the current visual style from style_engine
    to return different palettes, shapes, and effects.
    """
    style_name = get_current_style()
    node_lower = node_name.lower()
    
    # 1. Container/Layer styling
    if node_type == "container":
        container_style = get_container_style()
        return {
            "shape": "rectangle",
            "style": container_style,
            "category": "container"
        }
        
    # 2. Determine category based on keyword matching
    category = _classify_node(node_lower)
    
    # 3. Get palette from style engine (style-aware colors)
    theme = get_palette(category)
    fill_color = theme["fill"]
    stroke_color = theme["stroke"]
    font_color = theme["font"]
    
    # 4. Determine shape type and extra style (style-dependent)
    shape = "rectangle"
    extra_style = ""
    
    if style_name == "minimal":
        # Clean, no rounded corners, thin stroke
        shape = "rectangle"
        if category == "database":
            shape = "cylinder"
            extra_style = "rounded=0;glass=0;whiteSpace=wrap;html=1;"
        else:
            extra_style = "rounded=0;whiteSpace=wrap;html=1;"
        style = (
            f"{extra_style}fillColor={fill_color};strokeColor={stroke_color};"
            f"fontColor={font_color};strokeWidth=1;fontStyle=0;align=center;verticalAlign=middle;"
        )
        
    elif style_name == "drawio_skill":
        # Large rounded boxes, thick stroke, shadow effect
        shape = "rectangle"
        if category == "database":
            shape = "cylinder"
            extra_style = "rounded=0;glass=0;whiteSpace=wrap;html=1;shadow=1;"
        else:
            extra_style = "rounded=1;arcSize=14;whiteSpace=wrap;html=1;shadow=1;"
        style = (
            f"{extra_style}fillColor={fill_color};strokeColor={stroke_color};"
            f"fontColor={font_color};strokeWidth=3;fontStyle=1;fontSize=13;align=center;verticalAlign=middle;"
        )
        
    elif style_name in ("aws_icons", "azure_icons", "gcp_icons", "k8s_icons"):
        # Dark/branded boxes, thick stroke, strong contrast
        shape = "rectangle"
        if category == "database":
            shape = "cylinder"
            extra_style = "rounded=0;glass=0;whiteSpace=wrap;html=1;"
        else:
            extra_style = "rounded=1;arcSize=10;whiteSpace=wrap;html=1;"
        style = (
            f"{extra_style}fillColor={fill_color};strokeColor={stroke_color};"
            f"fontColor={font_color};strokeWidth=2;fontStyle=1;align=center;verticalAlign=middle;"
        )
        
    elif style_name == "aiicons":
        # Dark themed, neon accents
        shape = "rectangle"
        if category == "database":
            shape = "cylinder"
            extra_style = "rounded=0;glass=1;whiteSpace=wrap;html=1;"
        else:
            extra_style = "rounded=1;arcSize=12;whiteSpace=wrap;html=1;glass=1;"
        style = (
            f"{extra_style}fillColor={fill_color};strokeColor={stroke_color};"
            f"fontColor={font_color};strokeWidth=2;fontStyle=1;align=center;verticalAlign=middle;"
        )
        
    else:
        # Classic (default) — original behavior
        if category == "database":
            shape = "cylinder"
            extra_style = "rounded=0;glass=0;whiteSpace=wrap;html=1;"
        elif category == "network" and "cloud" in node_lower:
            shape = "cloud"
            extra_style = "whiteSpace=wrap;html=1;"
        elif "firewall" in node_lower or "waf" in node_lower:
            shape = "double-bordered"
            extra_style = "shape=doubleBoundary;whiteSpace=wrap;html=1;"
        else:
            shape = "rectangle"
            extra_style = "rounded=1;arcSize=10;whiteSpace=wrap;html=1;"
        style = (
            f"{extra_style}fillColor={fill_color};strokeColor={stroke_color};"
            f"fontColor={font_color};strokeWidth=2;fontStyle=1;align=center;verticalAlign=middle;"
        )
    
    return {
        "shape": shape,
        "style": style,
        "category": category
    }
