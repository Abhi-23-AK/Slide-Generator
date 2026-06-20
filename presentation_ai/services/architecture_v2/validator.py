from typing import Dict, Any, List

def ccw(A, B, C):
    """Checks if points A, B, C are in counter-clockwise order."""
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

def line_intersects(A, B, C, D):
    """Checks if line segment AB intersects segment CD."""
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

def validate_layout(graph: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates node layouts and edges for geometric issues:
    - Node overlaps
    - Crossing edges
    - Clipped text labels
    - Duplicate/stacked connectors
    Returns a report: {"is_valid": bool, "errors": List[str]}
    """
    errors = []
    
    warnings = []
    
    # We retrieve the absolute coordinates calculated during graphviz_layout.py
    abs_coords = graph.get("_absolute_coords", {})
    node_coords = abs_coords.get("nodes", {})
    container_coords = abs_coords.get("containers", {})
    
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    
    # 1. Check Node Overlaps
    # Bounding box collision detection
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            n1 = nodes[i]
            n2 = nodes[j]
            c1 = node_coords.get(n1["id"])
            c2 = node_coords.get(n2["id"])
            
            if c1 and c2:
                # Check intersection of rectangles
                x_overlap = not (c1["x"] + c1["w"] <= c2["x"] or c2["x"] + c2["w"] <= c1["x"])
                y_overlap = not (c1["y"] + c1["h"] <= c2["y"] or c2["y"] + c2["h"] <= c1["y"])
                
                if x_overlap and y_overlap:
                    errors.append(f"Overlap detected: Node '{n1['label']}' overlaps with Node '{n2['label']}'.")
                    
    # 2. Check Clipped Text
    for node in nodes:
        c = node_coords.get(node["id"])
        if c:
            label_len = len(node["label"])
            # Indented logo text has less width
            logo_url = node.get("brand") or ""
            available_width = c["w"]
            if logo_url:
                available_width -= 44  # spacingLeft
                
            # Heuristic: average character width is 7.5 pixels at 12 Pt
            required_width = label_len * 7.5
            if required_width > available_width:
                warnings.append(f"Clipped text warning: Node label '{node['label']}' is too long for node width ({c['w']}px).")

    # 3. Check Crossing Edges
    # Represent each edge as a segment between node centers
    edge_segments = []
    for edge in edges:
        source_id = edge["source"]
        target_id = edge["target"]
        
        c_src = node_coords.get(source_id)
        c_tgt = node_coords.get(target_id)
        
        if c_src and c_tgt:
            p_src = (c_src["x"] + c_src["w"]/2, c_src["y"] + c_src["h"]/2)
            p_tgt = (c_tgt["x"] + c_tgt["w"]/2, c_tgt["y"] + c_tgt["h"]/2)
            edge_segments.append((p_src, p_tgt, edge))
            
    for i in range(len(edge_segments)):
        for j in range(i + 1, len(edge_segments)):
            seg1 = edge_segments[i]
            seg2 = edge_segments[j]
            
            # Skip if they share a common endpoint (node connection)
            if (seg1[2]["source"] in (seg2[2]["source"], seg2[2]["target"]) or
                seg1[2]["target"] in (seg2[2]["source"], seg2[2]["target"])):
                continue
                
            if line_intersects(seg1[0], seg1[1], seg2[0], seg2[1]):
                errors.append(
                    f"Crossing edges: Connection '{seg1[2].get('label') or 'unnamed'}' "
                    f"crosses with '{seg2[2].get('label') or 'unnamed'}'."
                )
                
    # 4. Check Stacked/Duplicate Connectors
    seen_connections = set()
    for edge in edges:
        pair = tuple(sorted([edge["source"], edge["target"]]))
        if pair in seen_connections:
            warnings.append(f"Stacked connectors warning: Multiple connections exist between '{edge['source']}' and '{edge['target']}'.")
        seen_connections.add(pair)
        
    if warnings:
        print(f"[VALIDATOR] Warnings detected: {warnings}")
        
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }
