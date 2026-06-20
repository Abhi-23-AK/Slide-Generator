from typing import Dict, Any, List, Tuple
from services.architecture_v3.logo_resolver import resolve_logo

def ccw(A: Tuple[float, float], B: Tuple[float, float], C: Tuple[float, float]) -> bool:
    """Checks if points A, B, C are in counter-clockwise order."""
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

def line_intersects(A: Tuple[float, float], B: Tuple[float, float], C: Tuple[float, float], D: Tuple[float, float]) -> bool:
    """Checks if line segment AB intersects segment CD."""
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

def validate_layout(graph: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates nodes, containers, and edges geometrically.
    Returns:
      {
        "is_valid": bool,
        "errors": List[str],
        "warnings": List[str],
        "clipped_nodes": List[str] # node IDs that need width expansion
      }
    """
    errors = []
    warnings = []
    clipped_nodes = []
    
    abs_coords = graph.get("_absolute_coords", {})
    node_coords = abs_coords.get("nodes", {})
    container_coords = abs_coords.get("containers", {})
    
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    containers = graph.get("containers", [])
    
    # 1. Node Overlap Check
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            n1 = nodes[i]
            n2 = nodes[j]
            c1 = node_coords.get(n1["id"])
            c2 = node_coords.get(n2["id"])
            
            if c1 and c2:
                # Check bounding box intersection
                x_overlap = not (c1["x"] + c1["w"] <= c2["x"] or c2["x"] + c2["w"] <= c1["x"])
                y_overlap = not (c1["y"] + c1["h"] <= c2["y"] or c2["y"] + c2["h"] <= c1["y"])
                
                if x_overlap and y_overlap:
                    errors.append(f"Node overlap: '{n1['label']}' intersects '{n2['label']}'.")
                    
    # 2. Sibling Container Overlap Check
    for i in range(len(containers)):
        for j in range(i + 1, len(containers)):
            c1_info = containers[i]
            c2_info = containers[j]
            
            # Only check if they are siblings or not nested
            p1 = c1_info.get("parent")
            p2 = c2_info.get("parent")
            
            c1 = container_coords.get(c1_info["id"])
            c2 = container_coords.get(c2_info["id"])
            
            if c1 and c2:
                # Bounding box intersection check
                x_overlap = not (c1["x"] + c1["w"] <= c2["x"] or c2["x"] + c2["w"] <= c1["x"])
                y_overlap = not (c1["y"] + c1["h"] <= c2["y"] or c2["y"] + c2["h"] <= c1["y"])
                
                if x_overlap and y_overlap:
                    # Ignore if one is parent of the other (nested)
                    is_nested = (c1_info["id"] == p2) or (c2_info["id"] == p1)
                    if not is_nested:
                        errors.append(f"Container overlap: '{c1_info['label']}' intersects '{c2_info['label']}'.")
                        
    # 3. Text Label Clipping Check
    for node in nodes:
        nid = node["id"]
        c = node_coords.get(nid)
        if c:
            label_len = len(node["label"])
            available_width = c["w"]
            
            # Check if there is a logo (indents text)
            logo_url = resolve_logo(node["label"], brand=node.get("brand"))
            if logo_url:
                available_width -= 44
                
            required_width = label_len * 7.5
            if required_width > available_width:
                warnings.append(f"Clipped label: '{node['label']}' needs width {required_width:.1f}px (available {available_width:.1f}px)")
                clipped_nodes.append(nid)
                
    # 4. Crossing Edges Check
    edge_segments = []
    for edge in edges:
        src_id = edge["source"]
        tgt_id = edge["target"]
        
        c_src = node_coords.get(src_id)
        c_tgt = node_coords.get(tgt_id)
        
        if c_src and c_tgt:
            # Segment connects center points
            p_src = (c_src["x"] + c_src["w"]/2.0, c_src["y"] + c_src["h"]/2.0)
            p_tgt = (c_tgt["x"] + c_tgt["w"]/2.0, c_tgt["y"] + c_tgt["h"]/2.0)
            edge_segments.append((p_src, p_tgt, edge))
            
    for i in range(len(edge_segments)):
        for j in range(i + 1, len(edge_segments)):
            seg1 = edge_segments[i]
            seg2 = edge_segments[j]
            
            # Skip if they share an endpoint
            if (seg1[2]["source"] in (seg2[2]["source"], seg2[2]["target"]) or
                seg1[2]["target"] in (seg2[2]["source"], seg2[2]["target"])):
                continue
                
            if line_intersects(seg1[0], seg1[1], seg2[0], seg2[1]):
                warnings.append(
                    f"Crossing edges: Connection '{seg1[2].get('label') or 'unnamed'}' "
                    f"crosses with '{seg2[2].get('label') or 'unnamed'}'."
                )
                
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "clipped_nodes": clipped_nodes
    }
