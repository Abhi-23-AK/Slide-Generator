import uuid
import re
from typing import Dict, Any

SHAPE_LIBRARY = {
    # Cloud/AWS topics
    "load balancer": "shape=mxgraph.aws4.traditional_server",
    "database": "shape=mxgraph.aws4.rds",
    "cache": "shape=mxgraph.aws4.elasticache",
    "api gateway": "shape=mxgraph.aws4.api_gateway",
    "lambda": "shape=mxgraph.aws4.lambda",
    "s3": "shape=mxgraph.aws4.s3",

    # Kubernetes topics
    "pod": "shape=mxgraph.kubernetes.pod",
    "service": "shape=mxgraph.kubernetes.svc",
    "ingress": "shape=mxgraph.kubernetes.ing",
    "deployment": "shape=mxgraph.kubernetes.deploy",
    "namespace": "shape=mxgraph.kubernetes.ns",

    # AI/ML topics
    "model": "shape=mxgraph.flowchart.stored_data",
    "training": "shape=mxgraph.flowchart.process",
    "inference": "shape=mxgraph.flowchart.decision",
    "vector db": "shape=mxgraph.flowchart.database",
    "embedding": "shape=mxgraph.flowchart.internal_storage",
    
    # Generic fallbacks
    "service/api": "rounded=1",
    "database/store": "shape=mxgraph.flowchart.database",
    "queue/broker": "shape=parallelogram",
    "user/client": "shape=mxgraph.flowchart.start_2",
    "gateway/proxy": "shape=hexagon",
    "container/zone": "shape=swimlane",
}

SEMANTIC_COLORS = {
    "compute":   {"fill": "#dae8fc", "stroke": "#6c8ebf"},  # blue
    "database":  {"fill": "#d5e8d4", "stroke": "#82b366"},  # green
    "security":  {"fill": "#f8cecc", "stroke": "#b85450"},  # red
    "gateway":   {"fill": "#fff2cc", "stroke": "#d6b656"},  # yellow
    "queue":     {"fill": "#e1d5e7", "stroke": "#9673a6"},  # purple
    "storage":   {"fill": "#dae8fc", "stroke": "#6c8ebf"},  # blue
    "external":  {"fill": "#f5f5f5", "stroke": "#666666"},  # grey
}

def xml_escape(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;")
                .replace("\n", "&#xa;"))

def get_semantic_color(node_type: str) -> Dict[str, str]:
    t = node_type.lower().strip() if node_type else "service"
    if t in ["service", "container", "llm", "compute"]:
        return SEMANTIC_COLORS["compute"]
    elif t in ["database", "vector_db", "cache"]:
        return SEMANTIC_COLORS["database"]
    elif t in ["security"]:
        return SEMANTIC_COLORS["security"]
    elif t in ["gateway"]:
        return SEMANTIC_COLORS["gateway"]
    elif t in ["queue"]:
        return SEMANTIC_COLORS["queue"]
    elif t in ["storage"]:
        return SEMANTIC_COLORS["storage"]
    elif t in ["external", "client", "monitoring", "logging", "analytics"]:
        return SEMANTIC_COLORS["external"]
    else:
        return SEMANTIC_COLORS["compute"]

def resolve_node_shape_style(label: str, node_type: str, shape_hint: str = None) -> str:
    # Check shape_hint first
    hint = shape_hint.lower().strip() if shape_hint else ""
    if hint in SHAPE_LIBRARY:
        return SHAPE_LIBRARY[hint]
    
    # Check if any keyword in shape_library matches label
    label_lower = label.lower()
    for kw, shape_str in SHAPE_LIBRARY.items():
        if kw in label_lower:
            return shape_str
            
    # Check keyword matches in node_type
    type_lower = node_type.lower().strip() if node_type else ""
    for kw, shape_str in SHAPE_LIBRARY.items():
        if kw in type_lower:
            return shape_str

    # Category fallback
    if type_lower in ["service", "api", "compute", "llm"]:
        return SHAPE_LIBRARY["service/api"]
    elif type_lower in ["database", "store", "cache", "vector_db"]:
        return SHAPE_LIBRARY["database/store"]
    elif type_lower in ["queue", "broker"]:
        return SHAPE_LIBRARY["queue/broker"]
    elif type_lower in ["user", "client"]:
        return SHAPE_LIBRARY["user/client"]
    elif type_lower in ["gateway", "proxy"]:
        return SHAPE_LIBRARY["gateway/proxy"]
    elif type_lower in ["container", "zone"]:
        return SHAPE_LIBRARY["container/zone"]
    else:
        return SHAPE_LIBRARY["service/api"]

def get_edge_style(style_name: str) -> str:
    stroke_color = "#4a5568"
    if style_name == "drawio_skill":
        stroke_color = "#4361ee"
    elif style_name == "aiicons":
        stroke_color = "#e94560"
    elif style_name == "aws_icons":
        stroke_color = "#ff9900"
    elif style_name == "azure_icons":
        stroke_color = "#0078d4"
    elif style_name == "gcp_icons":
        stroke_color = "#4285f4"
    elif style_name == "k8s_icons":
        stroke_color = "#326ce5"

    return (
        f"edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;"
        f"strokeColor={stroke_color};strokeWidth=2;fontSize=10;fontColor=#000000;fontStyle=1;"
    )

def scale_style_string(style: str, factor: float) -> str:
    if not style:
        return ""
    parts = style.split(';')
    new_parts = []
    for part in parts:
        if not part:
            continue
        if '=' in part:
            k, v = part.split('=', 1)
            # Keys to scale:
            if k in {
                "fontSize", "strokeWidth", "spacing", "spacingTop", 
                "spacingLeft", "spacingRight", "spacingBottom", 
                "imageWidth", "imageHeight", "jettySize"
            }:
                try:
                    val = float(v)
                    new_val = int(val * factor) if val.is_integer() or k == "fontSize" else val * factor
                    new_parts.append(f"{k}={new_val}")
                except ValueError:
                    new_parts.append(part)
            elif k == "dashPattern":
                try:
                    nums = [str(int(float(n) * factor)) for n in v.split()]
                    new_parts.append(f"{k}={' '.join(nums)}")
                except Exception:
                    new_parts.append(part)
            else:
                new_parts.append(part)
        else:
            new_parts.append(part)
    return ";".join(new_parts) + ";"

def get_style_category(node_type: str, label: str) -> str:
    t = node_type.lower().strip() if node_type else "service"
    label_lower = label.lower()
    
    # Check label keywords first for more precise classification
    if any(x in label_lower for x in ("gateway", "loadbalancer", "load-balancer", "lb", "proxy", "ingress", "route", "dns")):
        return "network"
    if any(x in label_lower for x in ("db", "database", "postgres", "sql", "oracle", "warehouse")):
        return "database"
    if any(x in label_lower for x in ("cache", "redis", "memcached")):
        return "database"
    if any(x in label_lower for x in ("queue", "kafka", "rabbitmq", "bus", "broker")):
        return "queue"
    if any(x in label_lower for x in ("auth", "cognito", "iam", "security", "vault")):
        return "security"
    if any(x in label_lower for x in ("monitor", "prometheus", "grafana", "log")):
        return "monitoring"
    if any(x in label_lower for x in ("client", "user", "browser", "app", "mobile", "admin", "dashboard")):
        return "client"
        
    # Fallback to node_type mapping
    if t in ["service", "compute", "llm", "container"]:
        return "compute"
    elif t in ["database", "vector_db", "cache"]:
        return "database"
    elif t in ["security", "auth"]:
        return "security"
    elif t in ["gateway", "network", "dns", "cdn"]:
        return "network"
    elif t in ["queue", "broker"]:
        return "queue"
    elif t in ["storage", "bucket"]:
        return "storage"
    elif t in ["client", "user", "external"]:
        return "client"
    elif t in ["monitoring", "logging", "analytics"]:
        return "monitoring"
    else:
        return "compute"

def build_drawio_xml(graph: Dict[str, Any]) -> str:
    """
    Translates nodes, containers, and edges into a complete, valid Draw.io XML string
    wrapped in <mxfile><diagram><mxGraphModel>...</mxGraphModel></diagram></mxfile> tags.
    """
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    containers = graph.get("containers", [])
    
    uid = uuid.uuid4().hex[:10]
    scale_factor = 2.0
    
    xml_parts = []
    xml_parts.append('<mxfile host="Electron" version="30.0.4">')
    xml_parts.append(f'  <diagram id="page_{uid}" name="Page-1">')
    xml_parts.append('    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" pageWidth="1654" pageHeight="1169">')
    xml_parts.append('      <root>')
    xml_parts.append('        <mxCell id="0"/>')
    xml_parts.append('        <mxCell id="1" parent="0"/>')
    
    # 1. Add Containers/Groups (Fix 5: style-aware transparent fill, dashed/solid border, bold black 16pt font)
    from services.architecture_v3.style_engine import get_container_style
    for container in containers:
        cid = container["id"]
        label = xml_escape(container["label"])
        layout = container.get("layout", {"x": 100, "y": 100, "w": 400, "h": 400})
        
        # Scale coordinates
        cx = int(layout["x"] * scale_factor)
        cy = int(layout["y"] * scale_factor)
        cw = int(layout["w"] * scale_factor)
        ch = int(layout["h"] * scale_factor)
        
        parent_id = container.get("parent") or "1"
        
        # Fetch styled container from style engine
        base_container_style = get_container_style()
        # Enforce bold black 16pt font and html wrapping
        container_style = base_container_style
        if "fontSize" not in container_style:
            container_style += "fontSize=16;"
        else:
            container_style = re.sub(r'fontSize=\d+', 'fontSize=16', container_style)
        if "fontStyle" not in container_style:
            container_style += "fontStyle=1;"
        else:
            container_style = re.sub(r'fontStyle=\d+', 'fontStyle=1', container_style)
        if "fontColor" not in container_style:
            container_style += "fontColor=#000000;"
        container_style += "html=1;whiteSpace=wrap;"
        
        scaled_style = scale_style_string(container_style, scale_factor)
        style = xml_escape(scaled_style)
        
        xml_parts.append(
            f'        <mxCell id="{cid}" value="{label}" style="{style}" vertex="1" parent="{parent_id}">'
            f'          <mxGeometry x="{cx}" y="{cy}" width="{cw}" height="{ch}" as="geometry"/>'
            f'        </mxCell>'
        )
        
    # 2. Add Nodes (Fix 1: dynamic shapes, Fix 2: 14pt bold black labels, auto wrapping/expansion, Fix 5: semantic colors)
    from services.architecture_v3.style_engine import get_current_style, should_use_image_shapes, get_palette
    from services.architecture_v3.logo_resolver import resolve_logo
    style_name = get_current_style()
    
    for node in nodes:
        nid = node["id"]
        label = xml_escape(node["label"])
        layout = node.get("layout", {"x": 200, "y": 200, "w": 160, "h": 80})
        parent_id = node.get("parent") or "1"
        
        # Resolve category and style engine palette colors
        node_type = node.get("type", "service")
        cat = get_style_category(node_type, node["label"])
        theme = get_palette(cat)
        fill = theme["fill"]
        stroke = theme["stroke"]
        font_color = theme.get("font", "#000000")
        
        # Base font size: 14pt BEFORE scaling
        node_font_size = 14
        
        # Check if we should render as a high-fidelity image shape/logo
        logo_url = resolve_logo(node["label"], brand=node.get("brand"), kind=node_type)
        use_image = should_use_image_shapes() and (logo_url is not None)
        
        orig_w = layout.get("w", 160)
        lh = layout.get("h", 80)
        
        if use_image:
            # Sizes for different styles
            sizes = {
                "drawio_skill": 120,
                "aiicons": 96,
                "aws_icons": 90,
                "azure_icons": 90,
                "gcp_icons": 90,
                "k8s_icons": 90,
                "classic": 90
            }
            size = sizes.get(style_name, 90)
            
            # Center the square icon over computed layout positions
            cx = layout.get("x", 200) + orig_w / 2.0
            cy = layout.get("y", 200) + lh / 2.0
            
            node_w = int(size * scale_factor)
            node_h = int(size * scale_factor)
            node_x = int((cx - size / 2.0) * scale_factor)
            node_y = int((cy - size / 2.0) * scale_factor)
            
            escaped_url = xml_escape(logo_url)
            style = (
                f"shape=image;image={escaped_url};"
                f"verticalLabelPosition=bottom;verticalAlign=top;aspect=fixed;imageAspect=0;spacingTop={int(6 * scale_factor)};html=1;whiteSpace=wrap;"
                f"fontColor={font_color};fontSize={node_font_size};fontStyle=1;align=center;"
            )
            scaled_style = scale_style_string(style, scale_factor)
            escaped_style = xml_escape(scaled_style)
        else:
            # Fallback to standard shape/style styling
            shape_hint = node.get("shape_hint")
            shape_str = resolve_node_shape_style(node["label"], node_type, shape_hint)
            
            lw = orig_w
            extra_style = ""
            
            # Long label logic: >15 characters gets auto wrapping, html=1, and width expanded
            if len(node["label"]) > 15:
                lw = max(120, len(node["label"]) * 8)
                extra_style = "whiteSpace=wrap;html=1;"
                
            # Re-center geometry mathematically before scaling to keep layout aligned
            lx = layout.get("x", 200) - (lw - orig_w) / 2.0
            ly = layout.get("y", 200)
            
            # Scale coordinates
            node_x = int(lx * scale_factor)
            node_y = int(ly * scale_factor)
            node_w = int(lw * scale_factor)
            node_h = int(lh * scale_factor)
            
            # Construct node style
            style = (
                f"{shape_str};fillColor={fill};strokeColor={stroke};strokeWidth=2;"
                f"fontColor={font_color};fontSize={node_font_size};fontStyle=1;"
                f"align=center;verticalAlign=middle;{extra_style}"
            )
            
            scaled_style = scale_style_string(style, scale_factor)
            escaped_style = xml_escape(scaled_style)
        
        xml_parts.append(
            f'        <mxCell id="{nid}" value="{label}" style="{escaped_style}" vertex="1" parent="{parent_id}">'
            f'          <mxGeometry x="{node_x}" y="{node_y}" width="{node_w}" height="{node_h}" as="geometry"/>'
            f'        </mxCell>'
        )
        
    # 3. Add Edges/Connections
    edge_style = get_edge_style(style_name)
    scaled_edge_style = scale_style_string(edge_style, scale_factor)
    for i, edge in enumerate(edges):
        eid = f"e_{uid}_{i}"
        source = edge["source"]
        target = edge["target"]
        label = xml_escape(edge.get("label") or "")
        
        xml_parts.append(
            f'        <mxCell id="{eid}" value="{label}" style="{scaled_edge_style}" edge="1" parent="1" source="{source}" target="{target}">'
            f'          <mxGeometry relative="1" as="geometry"/>'
            f'        </mxCell>'
        )
        
    # 4. Aspect Ratio Padding
    try:
        abs_coords = graph.get("_absolute_coords", {})
        abs_nodes = abs_coords.get("nodes", {})
        abs_containers = abs_coords.get("containers", {})
        
        all_x = []
        all_y = []
        
        for nid, coords in abs_nodes.items():
            all_x.append(coords["x"])
            all_x.append(coords["x"] + coords["w"])
            all_y.append(coords["y"])
            all_y.append(coords["y"] + coords["h"])
            
        for cid, coords in abs_containers.items():
            all_x.append(coords["x"])
            all_x.append(coords["x"] + coords["w"])
            all_y.append(coords["y"])
            all_y.append(coords["y"] + coords["h"])
            
        if all_x and all_y:
            min_x = min(all_x)
            max_x = max(all_x)
            min_y = min(all_y)
            max_y = max(all_y)
            
            w = max_x - min_x
            h = max_y - min_y
            
            if w > 0 and h > 0:
                target_ratio = 1.90
                current_ratio = w / h
                
                if current_ratio < target_ratio:
                    target_w = h * target_ratio
                    pad_w = target_w - w
                    
                    dummy_lx = int((min_x - pad_w / 2) * scale_factor)
                    dummy_ly = int((min_y + h / 2) * scale_factor)
                    dummy_rx = int((max_x + pad_w / 2) * scale_factor)
                    dummy_ry = int((min_y + h / 2) * scale_factor)
                    
                    xml_parts.append(
                        f'        <mxCell id="dummy_left" value="" style="fillColor=none;strokeColor=none;selectable=0;" vertex="1" parent="1">'
                        f'          <mxGeometry x="{dummy_lx}" y="{dummy_ly}" width="1" height="1" as="geometry"/>'
                        f'        </mxCell>'
                    )
                    xml_parts.append(
                        f'        <mxCell id="dummy_right" value="" style="fillColor=none;strokeColor=none;selectable=0;" vertex="1" parent="1">'
                        f'          <mxGeometry x="{dummy_rx}" y="{dummy_ry}" width="1" height="1" as="geometry"/>'
                        f'        </mxCell>'
                    )
                else:
                    target_h = w / target_ratio
                    pad_h = target_h - h
                    
                    dummy_tx = int((min_x + w / 2) * scale_factor)
                    dummy_ty = int((min_y - pad_h / 2) * scale_factor)
                    dummy_bx = int((min_x + w / 2) * scale_factor)
                    dummy_by = int((max_y + pad_h / 2) * scale_factor)
                    
                    xml_parts.append(
                        f'        <mxCell id="dummy_top" value="" style="fillColor=none;strokeColor=none;selectable=0;" vertex="1" parent="1">'
                        f'          <mxGeometry x="{dummy_tx}" y="{dummy_ty}" width="1" height="1" as="geometry"/>'
                        f'        </mxCell>'
                    )
                    xml_parts.append(
                        f'        <mxCell id="dummy_bottom" value="" style="fillColor=none;strokeColor=none;selectable=0;" vertex="1" parent="1">'
                        f'          <mxGeometry x="{dummy_bx}" y="{dummy_by}" width="1" height="1" as="geometry"/>'
                        f'        </mxCell>'
                    )
    except Exception as e:
        print(f"[drawio_xml_builder] Error computing aspect ratio padding: {e}")

    xml_parts.append('      </root>')
    xml_parts.append('    </mxGraphModel>')
    xml_parts.append('  </diagram>')
    xml_parts.append('</mxfile>')
    
    return "\n".join(xml_parts)
