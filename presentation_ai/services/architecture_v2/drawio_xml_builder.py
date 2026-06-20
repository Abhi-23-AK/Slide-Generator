from typing import Dict, Any
from services.architecture_v2.logo_resolver import resolve_logo
from services.architecture_v2.shape_resolver import resolve_shape_style

def xml_escape(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;")
                .replace("\n", "&#xa;"))

def build_drawio_xml(graph: Dict[str, Any]) -> str:
    """
    Translates the graph nodes, containers, and edges into a complete mxGraphModel XML string.
    Resolves shapes, colors, and logos.
    """
    from services.architecture_v2.shape_resolver import resolve_shape_style
    
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    containers = graph.get("containers", [])
    
    xml_parts = []
    xml_parts.append('<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" pageWidth="1654" pageHeight="1169">')
    xml_parts.append('  <root>')
    xml_parts.append('    <mxCell id="0"/>')
    xml_parts.append('    <mxCell id="1" parent="0"/>')
    
    # 1. Add Containers/Groups
    for container in containers:
        cid = container["id"]
        label = xml_escape(container["label"])
        layout = container.get("layout", {"x": 100, "y": 100, "w": 400, "h": 400})
        
        parent_id = container.get("parent") or "1"
        style_info = resolve_shape_style(container["label"], node_type="container")
        style = xml_escape(style_info["style"])
        
        xml_parts.append(
            f'    <mxCell id="{cid}" value="{label}" style="{style}" vertex="1" parent="{parent_id}">'
            f'      <mxGeometry x="{layout["x"]}" y="{layout["y"]}" width="{layout["w"]}" height="{layout["h"]}" as="geometry"/>'
            f'    </mxCell>'
        )
        
    # 2. Add Nodes
    for node in nodes:
        nid = node["id"]
        label = xml_escape(node["label"])
        layout = node.get("layout", {"x": 200, "y": 200, "w": 160, "h": 80})
        parent_id = node.get("parent") or "1"
        
        # Resolve styling
        style_info = resolve_shape_style(node["label"], node_type="node")
        style = style_info["style"]
        
        # Resolve logo
        logo_url = resolve_logo(node["label"], brand=node.get("brand"))
        if logo_url:
            # Inject logo styling (left-aligned icon, indented text)
            escaped_url = xml_escape(logo_url)
            style += f"image={escaped_url};imageWidth=28;imageHeight=28;imageAlign=left;spacingLeft=44;align=left;"
            
        escaped_style = xml_escape(style)
        
        xml_parts.append(
            f'    <mxCell id="{nid}" value="{label}" style="{escaped_style}" vertex="1" parent="{parent_id}">'
            f'      <mxGeometry x="{layout["x"]}" y="{layout["y"]}" width="{layout["w"]}" height="{layout["h"]}" as="geometry"/>'
            f'    </mxCell>'
        )
        
    # 3. Add Edges/Connections
    for i, edge in enumerate(edges):
        eid = f"e{i}"
        source = edge["source"]
        target = edge["target"]
        label = xml_escape(edge.get("label") or "")
        
        # Premium curved edge style
        style = (
            "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;"
            "strokeColor=#4a5568;strokeWidth=2;fontSize=10;fontColor=#2d3748;"
        )
        
        xml_parts.append(
            f'    <mxCell id="{eid}" value="{label}" style="{style}" edge="1" parent="1" source="{source}" target="{target}">'
            f'      <mxGeometry relative="1" as="geometry"/>'
            f'    </mxCell>'
        )
        
    xml_parts.append('  </root>')
    xml_parts.append('</mxGraphModel>')
    
    return "\n".join(xml_parts)
