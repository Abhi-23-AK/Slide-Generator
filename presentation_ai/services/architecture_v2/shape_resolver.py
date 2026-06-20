import re
from typing import Dict, Any

# Standard color palettes (harmonious and sleek)
THEMES = {
    "compute": {
        "fill": "#dae8fc",
        "stroke": "#6c8ebf",
        "font": "#000000"
    },
    "database": {
        "fill": "#d5e8d4",
        "stroke": "#82b366",
        "font": "#000000"
    },
    "security": {
        "fill": "#f8cecc",
        "stroke": "#b85450",
        "font": "#000000"
    },
    "network": {
        "fill": "#fff2cc",
        "stroke": "#d6b656",
        "font": "#000000"
    },
    "client": {
        "fill": "#e1d5e7",
        "stroke": "#9673a6",
        "font": "#000000"
    },
    "storage": {
        "fill": "#f5f5f5",
        "stroke": "#666666",
        "font": "#000000"
    },
    "container": {
        "fill": "none",
        "stroke": "#999999",
        "font": "#333333"
    }
}

SHAPE_PATTERNS = {
    # Database
    r'\b(db|database|postgres|mysql|oracle|sqlite|mongodb|dynamodb|rds|redis|cache|datastore|warehouse)\b': "database",
    # Network/Routing
    r'\b(lb|load-balancer|gateway|dns|router|route|nginx|proxy|ingress|egress|vpc|subnet|firewall|waf|vpn)\b': "network",
    # Compute
    r'\b(server|compute|instance|ec2|vm|virtual-machine|lambda|function|pod|docker|kubernetes|k8s|worker|microservice|service|api|app|frontend|backend)\b': "compute",
    # Client
    r'\b(client|user|browser|mobile|phone|app-client|consumer|producer)\b': "client",
    # Security
    r'\b(auth|cognito|iam|oauth|key|token|encryption|ssl|tls|kms|vault)\b': "security",
}

def resolve_shape_style(node_name: str, node_type: str = "node") -> Dict[str, Any]:
    """
    Resolves the Draw.io shape and style parameters for a node or container.
    Returns a dict containing:
    - shape: Draw.io shape name (e.g. mxgraph.aws3.ec2, cylinder, cloud)
    - style: full Draw.io style string
    - category: string category (compute, database, etc.)
    """
    node_lower = node_name.lower()
    
    # 1. Container/Layer styling
    if node_type == "container":
        style = (
            "rounded=1;fillColor=none;strokeColor=#999999;strokeWidth=2;"
            "dashed=1;verticalAlign=top;align=center;fontStyle=1;fontSize=12;"
        )
        return {
            "shape": "rectangle",
            "style": style,
            "category": "container"
        }
        
    # 2. Determine category based on keyword matching
    category = "storage"  # default
    for pattern, cat in SHAPE_PATTERNS.items():
        if re.search(pattern, node_lower):
            category = cat
            break
            
    theme = THEMES[category]
    fill_color = theme["fill"]
    stroke_color = theme["stroke"]
    font_color = theme["font"]
    
    # 3. Determine shape type
    shape = "rectangle"  # default
    extra_style = ""
    
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
        # Standard rounded box for compute / clients
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
