#!/usr/bin/env python3
"""
Draw.io XML Builder for Architecture V4
======================================
Generates mxGraph XML representing containers, nodes (using native shapes
or base64-encoded image vertices), and orthogonal edges with waypoints.
Fuses Layer 5 shape resolution with Layer 4 visual styling.
"""

import uuid
import re
import textwrap
from typing import Dict, Any, List, Tuple, Optional
import services.architecture_v4.style_engine_v4 as style_engine
from services.architecture_v4.visual_node_resolver import resolve_node_visuals

def xml_escape(text: str) -> str:
    """Escapes XML special characters in string values."""
    if not isinstance(text, str):
        return ""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;")
                .replace("\n", "&#xa;"))

def fix_drawio_data_uris(style: str) -> str:
    """
    Scans a style string for Draw.io embedded base64 SVGs that are missing the ';base64' prefix,
    which causes headless chrome to fail when rendering.
    """
    if not style:
        return ""
    def repl(m):
        prefix = m.group(1)
        content = m.group(2)
        if "<" not in content and "%" not in content:
            return f"data:image/svg+xml;base64,{content}"
        return m.group(0)
    return re.sub(r'(data:image/svg\+xml,)([a-zA-Z0-9+/=]+)', repl, style)

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

def scale_style_string(style: str, scale: float) -> str:
    """Scales numeric attributes in a Draw.io style string by a scale factor."""
    if not style:
        return ""
        
    style_dict = parse_style_string(style)
    
    scalable_keys = {
        "spacing", "spacingTop", "spacingLeft", "spacingBottom", "spacingRight",
        "strokeWidth", "fontSize", "jettySize", "perimeterSpacing", "size",
        "arcSize", "imageWidth", "imageHeight", "shadowOffsetX", "shadowOffsetY",
        "arcWidth", "arcHeight"
    }
    
    for k, v in style_dict.items():
        if k in scalable_keys:
            try:
                num_val = float(v)
                style_dict[k] = str(int(num_val * scale))
            except ValueError:
                pass
        elif k == "dashPattern":
            try:
                nums = [str(int(float(n) * scale)) for n in v.split()]
                style_dict[k] = " ".join(nums)
            except Exception:
                pass
                
    return format_style_dict(style_dict)

def wrap_and_truncate_label(label: str, width: float, font_size: float) -> str:
    """Wraps text at word boundaries and truncates to maximum 3 lines with '...'."""
    char_w = 0.52 * font_size
    max_chars = int(width / char_w)
    if max_chars < 8:
        max_chars = 8
        
    lines = textwrap.wrap(
        label, 
        width=max_chars, 
        break_long_words=True, 
        break_on_hyphens=True
    )
    
    if len(lines) > 3:
        lines = lines[:3]
        if len(lines[2]) > 3:
            lines[2] = lines[2][:-3].strip() + "..."
        else:
            lines[2] = lines[2] + "..."
            
    return "\n".join(lines)

def get_dynamic_font_size(
    label: str,
    node_width: float,
    topology: Optional[str],
    theme: str,
    base_font_size: int
) -> int:
    """Calculates dynamic font size based on node properties and styling contexts."""
    font_size = base_font_size
    if theme == "minimal":
        font_size = max(10, base_font_size - 1)
        
    length = len(label)
    if length > 30:
        font_size -= 2
    elif length > 20:
        font_size -= 1
        
    try:
        node_width_float = float(node_width)
    except (ValueError, TypeError):
        node_width_float = 100.0
    if node_width_float < 100:
        font_size = min(font_size, 10)
    elif node_width_float < 130:
        font_size = min(font_size, 11)
        
    topo = str(topology).lower() if topology else ""
    if topo in ("cnn", "transformer", "rag_pipeline", "ai_pipeline"):
        font_size = min(font_size, 10)
        
    return max(9, font_size)

def get_special_cell_style(kind: str, label: str, theme: str) -> Tuple[str, str, str, str]:
    """Returns style parameters (base_style, fillColor, strokeColor, fontColor) for special cells."""
    fill = "#ffffff"
    stroke = "#333333"
    font = "#000000"
    
    if theme == "ai_dark_neon":
        fill = "#080810"
        stroke = "#ff2a5f"
        font = "#ffffff"
    elif theme == "aws":
        fill = "#f2f3f4"
        stroke = "#ff9900"
        font = "#232f3e"
    elif theme == "azure":
        fill = "#e8f4fd"
        stroke = "#0078d4"
        font = "#003d6b"
    elif theme == "kubernetes":
        fill = "#ffffff"
        stroke = "#326ce5"
        font = "#1d3557"
    elif theme == "drawio_vivid":
        fill = "#f0f4ff"
        stroke = "#4361ee"
        font = "#1b1b2f"
        
    if kind == "note":
        if theme != "ai_dark_neon":
            fill = "#fff9c4"
            stroke = "#fbc02d"
            font = "#3e2723"
        else:
            fill = "#1c1c0a"
            stroke = "#fbc02d"
            font = "#ffffff"
        base_style = "shape=note;whiteSpace=wrap;html=1;size=15;"
    elif kind == "caption":
        base_style = "text;html=1;align=center;verticalAlign=middle;resizable=0;points=[];strokeColor=none;fillColor=none;"
        fill = "none"
        stroke = "none"
    elif kind == "badge":
        base_style = "ellipse;whiteSpace=wrap;html=1;aspect=fixed;"
        if label.isdigit() or len(label) <= 3:
            fill = "#2ec4b6" if theme != "minimal" else "#ffffff"
            stroke = "none"
            font = "#ffffff" if theme != "minimal" else "#111111"
        else:
            fill = stroke
            stroke = "none"
            font = "#ffffff"
    elif kind == "annotation":
        base_style = "shape=callout;whiteSpace=wrap;html=1;size=20;position=0.4;"
    else: # decoration
        base_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=none;strokeColor=none;"
        fill = "none"
        stroke = "none"
        
    return base_style, fill, stroke, font

def build_drawio_xml(graph: Dict[str, Any], scale_factor: float = 1.0, topology: Optional[str] = None, visual_style: str = None) -> str:
    """
    Generates a full Draw.io mxGraph XML document based on the computed
    coordinates and layout in the graph dictionary.
    visual_style is explicitly passed instead of relying on global state.
    """
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    containers = graph.get("containers", [])
    
    # Retrieve topology from graph if not passed explicitly
    if not topology:
        topology = graph.get("topology")
        
    uid = uuid.uuid4().hex[:8]
    active_style = visual_style if visual_style else style_engine.get_current_style()
    
    # Get active theme font and configuration
    font_cfg = style_engine.get_font_settings()
    font_family = font_cfg.get("family", "Inter")
    base_font_size = font_cfg.get("size", 12)
    
    # ── Bounds Calculation ──
    abs_coords = graph.get("_absolute_coords", {})
    abs_nodes = abs_coords.get("nodes", {})
    abs_containers = abs_coords.get("containers", {})
    
    all_x = []
    all_y = []
    
    for _, coords in abs_nodes.items():
        all_x.append(coords["x"])
        all_x.append(coords["x"] + coords["w"])
        all_y.append(coords["y"])
        all_y.append(coords["y"] + coords["h"])
        
    for _, coords in abs_containers.items():
        all_x.append(coords["x"])
        all_x.append(coords["x"] + coords["w"])
        all_y.append(coords["y"])
        all_y.append(coords["y"] + coords["h"])
        
    for edge in edges:
        for pt in edge.get("waypoints", []):
            all_x.append(pt[0])
            all_y.append(pt[1])
            
    content_w = max(all_x) - min(all_x) if all_x else 800
    content_h = max(all_y) - min(all_y) if all_y else 600
    
    padding = 100
    w_needed = content_w + 2 * padding
    h_needed = content_h + 2 * padding
    
    # Strictly target widescreen aspect ratio from registry
    target_ratio = style_engine.get_target_ratio()
    page_w = max(w_needed, h_needed * target_ratio)
    page_w = max(1200.0, page_w)
    page_h = page_w / target_ratio
    
    page_w = int(page_w)
    page_h = int(page_h)
    
    dx = int(page_w * 0.9)
    dy = int(page_h * 0.9)
    
    # Z-Ordering Classification
    # Z-Ordering Classification (Problem 4)
    standard_nodes = [n for n in nodes if str(n.get("type", n.get("kind", "service"))).lower() not in {"note", "caption", "badge", "annotation", "decoration"}]
    
    note_cells = list(graph.get("notes", [])) + list(graph.get("captions", [])) + list(graph.get("badges", [])) + list(graph.get("annotations", []))
    for node in nodes:
        kind = str(node.get("type", node.get("kind", "service"))).lower()
        if kind in {"note", "caption", "badge", "annotation"}:
            if node not in note_cells:
                note_cells.append(node)
                
    decoration_cells = list(graph.get("decorations", []))
    for node in nodes:
        kind = str(node.get("type", node.get("kind", "service"))).lower()
        if kind == "decoration":
            if node not in decoration_cells:
                decoration_cells.append(node)
            
    xml_parts = []
    xml_parts.append('<mxfile host="Electron" version="30.0.4">')
    xml_parts.append(f'  <diagram id="diagram_{uid}" name="Page-1">')
    xml_parts.append(
        f'    <mxGraphModel dx="{dx}" dy="{dy}" grid="1" gridSize="10" guides="1" tooltips="1" '
        f'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{page_w}" pageHeight="{page_h}">'
    )
    xml_parts.append('      <root>')
    xml_parts.append('        <mxCell id="0"/>')
    xml_parts.append('        <mxCell id="1" parent="0"/>')
    
    # ── 1. Render Containers / Groups ──
    for container in containers:
        cid = container["id"]
        label = xml_escape(container["label"])
        layout = container.get("layout", {"x": 100, "y": 100, "w": 400, "h": 400})
        
        cx = int(layout["x"] * scale_factor)
        cy = int(layout["y"] * scale_factor)
        cw = int(layout["w"] * scale_factor)
        ch = int(layout["h"] * scale_factor)
        
        parent_id = container.get("parent") or "1"
        
        # Theme-aware container styles (Problem 2)
        style_str = style_engine.get_container_style(active_style, topology)
        style_dict = parse_style_string(style_str)
        style_dict["is_container"] = "1"
        style_dict["depth"] = str(container.get("depth", 0))
        style_dict["level"] = str(container.get("level", 0))
        style_dict["cluster_id"] = str(container.get("cluster_id", ""))
        style_str = format_style_dict(style_dict)
        
        # Scale & escape
        scaled_style = fix_drawio_data_uris(scale_style_string(style_str, scale_factor))
        escaped_style = xml_escape(scaled_style)
        
        xml_parts.append(
            f'        <mxCell id="{cid}" value="{label}" style="{escaped_style}" vertex="1" parent="{parent_id}">'
            f'          <mxGeometry x="{cx}" y="{cy}" width="{cw}" height="{ch}" as="geometry"/>'
            f'        </mxCell>'
        )
        
    # ── 2. Render Standard Nodes ──
    for node in standard_nodes:
        nid = node["id"]
        raw_label = node["label"]
        layout = node.get("layout", {"x": 200, "y": 200, "w": 160, "h": 80})
        parent_id = node.get("parent") or "1"
        
        resolved = resolve_node_visuals(node)
        category = resolved["category"]
        confidence = resolved.get("confidence", 0.0)
        kind = str(node.get("type", node.get("kind", "service"))).lower()
        
        # Enforce confidence hierarchy inside XML builder
        is_image = False
        is_native = False
        is_cylinder = False
        is_rect = False
        
        if active_style == "minimal":
            if (category == "database" or kind == "database"):
                is_cylinder = True
            else:
                try:
                    confidence_float = float(confidence)
                except (ValueError, TypeError):
                    confidence_float = 0.0
                if confidence_float >= 0.5:
                    is_native = True
                else:
                    is_rect = True
        else:
            try:
                confidence_float = float(confidence)
            except (ValueError, TypeError):
                confidence_float = 0.0
            if confidence_float > 0.8:
                is_image = True
            elif (category == "database" or kind == "database"):
                is_cylinder = True
            elif 0.5 <= confidence_float <= 0.8:
                is_native = True
            elif 0.2 <= confidence_float < 0.5:
                is_cylinder = True
            else:
                is_rect = True
                
        orig_w = layout.get("w", 160)
        orig_h = layout.get("h", 80)
        cx = layout.get("x", 200) + orig_w / 2.0
        cy = layout.get("y", 200) + orig_h / 2.0
        
        font_style = 0 if active_style == "minimal" else 1
        font_size = node.get("font_size_override", get_dynamic_font_size(raw_label, orig_w, topology, active_style, base_font_size))
        label = xml_escape(wrap_and_truncate_label(raw_label, orig_w, font_size))
        
        if is_image:
            # Image Vertex (Brand Logo)
            base_style = resolved["base_style"]
            aspect_ratio = resolved.get("aspect_ratio", 1.0)
            try:
                aspect_ratio_float = float(aspect_ratio)
            except (ValueError, TypeError):
                aspect_ratio_float = 1.0
            base_icon_size = style_engine.get_icon_size(active_style, topology, category) * node.get("image_scale_override", 1.0)
            
            if aspect_ratio_float > 1.0:
                node_w = base_icon_size
                node_h = base_icon_size / aspect_ratio_float
            else:
                node_h = base_icon_size
                node_w = base_icon_size * aspect_ratio
                
            node_x = int((cx - node_w / 2.0) * scale_factor)
            node_y = int((cy - node_h / 2.0) * scale_factor)
            scaled_w = int(node_w * scale_factor)
            scaled_h = int(node_h * scale_factor)
            
            palette = style_engine.get_palette(category)
            font_color = palette.get("font", "#000000")
            
            label_placement = style_engine.get_label_placement(active_style, topology)
            placement_dict = parse_style_string(label_placement)
            
            # Build style using parse/format to ensure no duplicate keys
            style_dict = parse_style_string(base_style)
            style_dict.update(placement_dict)
            
            # Add spacing
            is_right = placement_dict.get("labelPosition") == "right"
            if is_right:
                spacing_left = 12 if active_style == "drawio_vivid" else 8
                style_dict["spacingLeft"] = str(node.get("spacing_left_override", spacing_left))
            else:
                spacing_top = 10 if active_style == "drawio_vivid" else 6
                style_dict["spacingTop"] = str(node.get("spacing_top_override", spacing_top))
                
            # Apply dynamic override keys for top/bottom/left/right spacing
            for s_key in ("spacingTop", "spacingBottom", "spacingLeft", "spacingRight"):
                override_key = s_key.lower().replace("t", "_t").replace("b", "_b").replace("l", "_l").replace("r", "_r") + "_override"
                if node.get(override_key) is not None:
                    style_dict[s_key] = str(node[override_key])
                
            # Dark theme label background
            if active_style == "ai_dark_neon":
                style_dict["labelBackgroundColor"] = "#0c0c16"
                
            # Shadow from style engine
            style_dict.update(style_engine.get_shadow_style(active_style))
            
            # Confidence visual overrides
            style_dict.update(style_engine.get_confidence_style(confidence))
            
            # Core font and alignment properties
            style_dict.update({
                "fontFamily": font_family,
                "fontSize": str(font_size),
                "fontColor": font_color,
                "fontStyle": str(font_style),
                "whiteSpace": "wrap",
                "html": "1"
            })
            
            style_dict["category"] = category
            style_dict["shape_hint"] = node.get("shape_hint", "")
            style_dict["confidence"] = f"{confidence:.2f}"
            node_style = format_style_dict(style_dict)
            
        else:
            # Native shapes, Cylinders, or Rounded Rectangles
            node_w, node_h = style_engine.get_geometry(active_style, topology, raw_label, kind)
            
            node_x = int((cx - node_w / 2.0) * scale_factor)
            node_y = int((cy - node_h / 2.0) * scale_factor)
            scaled_w = int(node_w * scale_factor)
            scaled_h = int(node_h * scale_factor)
            
            node_style_str = style_engine.get_node_theme(active_style, category, confidence)
            style_dict = parse_style_string(node_style_str)
            
            if is_cylinder:
                style_dict.update({
                    "shape": "cylinder3",
                    "boundedLbl": "1",
                    "backgroundOutline": "1",
                    "size": "15"
                })
                if "rounded" in style_dict:
                    del style_dict["rounded"]
            elif is_native:
                style_dict.update(parse_style_string(resolved.get("base_style", "")))
                
            # Make sure active font family, size and wrapping are preserved
            style_dict.update({
                "fontFamily": font_family,
                "fontSize": str(font_size),
                "whiteSpace": "wrap",
                "html": "1"
            })
            
            style_dict["category"] = category
            style_dict["shape_hint"] = node.get("shape_hint", "")
            style_dict["confidence"] = f"{confidence:.2f}"
            node_style = format_style_dict(style_dict)
            
        scaled_node_style = fix_drawio_data_uris(scale_style_string(node_style, scale_factor))
        escaped_node_style = xml_escape(scaled_node_style)
        
        xml_parts.append(
            f'        <mxCell id="{nid}" value="{label}" style="{escaped_node_style}" vertex="1" parent="{parent_id}">'
            f'          <mxGeometry x="{node_x}" y="{node_y}" width="{scaled_w}" height="{scaled_h}" as="geometry"/>'
            f'        </mxCell>'
        )
        
    # ── 3. Render Edges ──
    for i, edge in enumerate(edges):
        if edge.get("style") == "invis":
            continue
            
        eid = f"e_{uid}_{i}"
        source = edge["source"]
        target = edge["target"]
        label = xml_escape(edge.get("label") or "")
        
        edge_style_str = style_engine.get_edge_theme(edge, active_style, font_family)
        scaled_edge_style = scale_style_string(edge_style_str, scale_factor)
        escaped_edge_style = xml_escape(scaled_edge_style)
        
        waypoints = edge.get("waypoints", [])
        if waypoints:
            points_xml = "".join(
                f'<mxPoint x="{int(pt[0] * scale_factor)}" y="{int(pt[1] * scale_factor)}"/>'
                for pt in waypoints
            )
            geom = (
                f'<mxGeometry relative="1" as="geometry">'
                f'  <Array as="points">{points_xml}</Array>'
                f'</mxGeometry>'
            )
        else:
            geom = '<mxGeometry relative="1" as="geometry"/>'
            
        xml_parts.append(
            f'        <mxCell id="{eid}" value="{label}" style="{escaped_edge_style}" edge="1" parent="1" source="{source}" target="{target}">'
            f'          {geom}'
            f'        </mxCell>'
        )
        
    # ── 4. Render Special Note Cells ──
    for node in note_cells:
        nid = node["id"]
        raw_label = node["label"]
        layout = node.get("layout", {"x": 200, "y": 200, "w": 160, "h": 80})
        parent_id = node.get("parent") or "1"
        kind = str(node.get("type", node.get("kind", "note"))).lower()
        
        orig_w = layout.get("w", 120)
        orig_h = layout.get("h", 80)
        
        node_x = int(layout.get("x", 200) * scale_factor)
        node_y = int(layout.get("y", 200) * scale_factor)
        scaled_w = int(orig_w * scale_factor)
        scaled_h = int(orig_h * scale_factor)
        
        base_special_style, fill, stroke, font_color = get_special_cell_style(kind, raw_label, active_style)
        font_size = get_dynamic_font_size(raw_label, orig_w, topology, active_style, base_font_size)
        label = xml_escape(wrap_and_truncate_label(raw_label, orig_w, font_size))
        
        node_style = (
            f"{base_special_style}fillColor={fill};strokeColor={stroke};"
            f"fontFamily={font_family};fontSize={font_size};fontColor={font_color};"
            f"align=center;verticalAlign=middle;whiteSpace=wrap;html=1;"
        )
        
        scaled_node_style = fix_drawio_data_uris(scale_style_string(node_style, scale_factor))
        escaped_node_style = xml_escape(scaled_node_style)
        
        xml_parts.append(
            f'        <mxCell id="{nid}" value="{label}" style="{escaped_node_style}" vertex="1" parent="{parent_id}">'
            f'          <mxGeometry x="{node_x}" y="{node_y}" width="{scaled_w}" height="{scaled_h}" as="geometry"/>'
            f'        </mxCell>'
        )
        
    # ── 5. Render Decoration Cells ──
    for node in decoration_cells:
        nid = node["id"]
        raw_label = node["label"]
        layout = node.get("layout", {"x": 200, "y": 200, "w": 160, "h": 80})
        parent_id = node.get("parent") or "1"
        
        orig_w = layout.get("w", 120)
        orig_h = layout.get("h", 80)
        
        node_x = int(layout.get("x", 200) * scale_factor)
        node_y = int(layout.get("y", 200) * scale_factor)
        scaled_w = int(orig_w * scale_factor)
        scaled_h = int(orig_h * scale_factor)
        
        base_special_style, fill, stroke, font_color = get_special_cell_style("decoration", raw_label, active_style)
        font_size = get_dynamic_font_size(raw_label, orig_w, topology, active_style, base_font_size)
        label = xml_escape(wrap_and_truncate_label(raw_label, orig_w, font_size))
        
        node_style = (
            f"{base_special_style}fillColor={fill};strokeColor={stroke};"
            f"fontFamily={font_family};fontSize={font_size};fontColor={font_color};"
            f"align=center;verticalAlign=middle;whiteSpace=wrap;html=1;"
        )
        
        scaled_node_style = fix_drawio_data_uris(scale_style_string(node_style, scale_factor))
        escaped_node_style = xml_escape(scaled_node_style)
        
        xml_parts.append(
            f'        <mxCell id="{nid}" value="{label}" style="{escaped_node_style}" vertex="1" parent="{parent_id}">'
            f'          <mxGeometry x="{node_x}" y="{node_y}" width="{scaled_w}" height="{scaled_h}" as="geometry"/>'
            f'        </mxCell>'
        )
        
    xml_parts.append('      </root>')
    xml_parts.append('    </mxGraphModel>')
    xml_parts.append('  </diagram>')
    xml_parts.append('</mxfile>')
    
    return "\n".join(xml_parts)
