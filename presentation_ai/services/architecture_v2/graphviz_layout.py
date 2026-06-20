import math
from typing import Dict, Any, List

def layout_graph(graph: Dict[str, Any], topology: str) -> Dict[str, Any]:
    """
    Computes spatial layout coordinates (x, y, width, height) for all nodes and containers
    in the graph based on the chosen topology.
    Returns the graph with coordinate attributes added.
    """
    # Standard dimensions
    node_w = 160
    node_h = 80
    container_padding = 40
    
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    containers = graph.get("containers", [])
    
    # 1. Initialize coordinate dictionaries (absolute coordinates)
    node_coords = {}      # node_id -> {x, y, w, h}
    container_coords = {} # container_id -> {x, y, w, h}
    
    # Define canvas dimensions
    canvas_w = 1654
    canvas_h = 1169
    center_x = canvas_w / 2
    center_y = canvas_h / 2
    
    # 2. Topology-specific layout math
    if topology == "star" or topology == "hub_spoke":
        # Hub in the center, spokes in a circle
        hub_id = None
        spokes = []
        for node in nodes:
            if "hub" in node["id"].lower() or "center" in node["id"].lower() or "controller" in node["id"].lower():
                hub_id = node["id"]
            spokes.append(node["id"])
            
        if hub_id and hub_id in spokes:
            spokes.remove(hub_id)
        elif spokes:
            hub_id = spokes.pop(0) # designate first as hub
            
        # Layout Hub
        if hub_id:
            node_coords[hub_id] = {"x": center_x - 100, "y": center_y - 50, "w": 200, "h": 100}
            
        # Layout Spokes
        num_spokes = len(spokes)
        radius = 280
        for i, spoke_id in enumerate(spokes):
            angle = i * (2 * math.pi / max(1, num_spokes))
            x = center_x + radius * math.cos(angle) - (node_w / 2)
            y = center_y + radius * math.sin(angle) - (node_h / 2)
            node_coords[spoke_id] = {"x": x, "y": y, "w": node_w, "h": node_h}
            
    elif topology == "ring":
        # Arrange all nodes in a circle
        num_nodes = len(nodes)
        radius = 300
        for i, node in enumerate(nodes):
            angle = i * (2 * math.pi / max(1, num_nodes))
            x = center_x + radius * math.cos(angle) - (node_w / 2)
            y = center_y + radius * math.sin(angle) - (node_h / 2)
            node_coords[node["id"]] = {"x": x, "y": y, "w": node_w, "h": node_h}
            
    elif topology == "cloud":
        # Specialized cloud container layout: VPC (outer) -> AZ1, AZ2 (inner) -> Subnets (inner)
        # We lay them out in static panels
        vpc_w = 1200
        vpc_h = 750
        vpc_x = center_x - (vpc_w / 2)
        vpc_y = 150
        
        container_coords["vpc"] = {"x": vpc_x, "y": vpc_y, "w": vpc_w, "h": vpc_h}
        
        # Split VPC into AZ1 (left) and AZ2 (right)
        az_w = 520
        az_h = 620
        container_coords["pub_sub"] = {"x": vpc_x + 60, "y": vpc_y + 80, "w": az_w, "h": az_h}
        container_coords["priv_sub"] = {"x": vpc_x + 620, "y": vpc_y + 80, "w": az_w, "h": az_h}
        
        # Place nodes
        for node in nodes:
            nid = node["id"]
            parent = node.get("parent")
            
            if parent == "pub_sub":
                # ALB / Load balancer in public subnet
                node_coords[nid] = {"x": vpc_x + 60 + (az_w / 2) - (node_w / 2), "y": vpc_y + 160, "w": node_w, "h": node_h}
            elif parent == "priv_sub":
                # Web instances or database
                if "db" in nid or "database" in nid:
                    node_coords[nid] = {"x": vpc_x + 620 + (az_w / 2) - (node_w / 2), "y": vpc_y + 450, "w": node_w, "h": node_h}
                elif "1" in nid:
                    node_coords[nid] = {"x": vpc_x + 620 + 80, "y": vpc_y + 200, "w": node_w, "h": node_h}
                else:
                    node_coords[nid] = {"x": vpc_x + 620 + 280, "y": vpc_y + 200, "w": node_w, "h": node_h}
            else:
                # Client node is outside VPC
                node_coords[nid] = {"x": vpc_x - 220, "y": center_y - (node_h / 2), "w": node_w, "h": node_h}
                
    elif topology == "kubernetes":
        # kubernetes: Node (outer) -> Pod (inner)
        node_w_box = 1000
        node_h_box = 700
        node_x = center_x - 300
        node_y = 200
        
        container_coords["node"] = {"x": node_x, "y": node_y, "w": node_w_box, "h": node_h_box}
        
        pod_w_box = 650
        pod_h_box = 350
        container_coords["pod"] = {"x": node_x + 200, "y": node_y + 250, "w": pod_w_box, "h": pod_h_box}
        
        for node in nodes:
            nid = node["id"]
            parent = node.get("parent")
            
            if parent == "pod":
                if "sidecar" in nid:
                    node_coords[nid] = {"x": node_x + 200 + 360, "y": node_y + 250 + 130, "w": node_w, "h": node_h}
                else:
                    node_coords[nid] = {"x": node_x + 200 + 80, "y": node_y + 250 + 130, "w": node_w, "h": node_h}
            elif parent == "node":
                # Service node
                node_coords[nid] = {"x": node_x + 400, "y": node_y + 80, "w": node_w, "h": node_h}
            else:
                # Ingress (outside node)
                node_coords[nid] = {"x": node_x - 220, "y": node_y + 300, "w": node_w, "h": node_h}
                
    elif topology == "ai_pipeline" or topology == "cnn":
        # Arrange nodes sequentially from left to right in pipeline columns
        # Determine stages/containers or split screen horizontally
        num_nodes = len(nodes)
        spacing = (canvas_w - 200) / max(1, num_nodes)
        
        # Build stage containers if any
        if containers:
            stage1_w = 500
            stage2_w = 600
            container_coords["stage1"] = {"x": 100, "y": 250, "w": stage1_w, "h": 500}
            container_coords["stage2"] = {"x": 750, "y": 250, "w": stage2_w, "h": 500}
            
        for i, node in enumerate(nodes):
            nid = node["id"]
            parent = node.get("parent")
            
            if parent == "stage1":
                if "data" in nid:
                    node_coords[nid] = {"x": 140, "y": 300, "w": node_w, "h": node_h}
                elif "embed" in nid:
                    node_coords[nid] = {"x": 140, "y": 450, "w": node_w, "h": node_h}
                else: # rag
                    node_coords[nid] = {"x": 380, "y": 370, "w": node_w, "h": node_h}
            elif parent == "stage2":
                if "llm" in nid:
                    node_coords[nid] = {"x": 800, "y": 370, "w": node_w, "h": node_h}
                else: # agent
                    node_coords[nid] = {"x": 1100, "y": 370, "w": node_w, "h": node_h}
            else:
                # CNN / generic horizontal pipeline
                x_pos = 100 + i * spacing
                y_pos = center_y - 40
                w = node_w
                h = node_h
                # Add CNN-specific spatial size styles
                if "img" in nid:
                    w, h = 100, 200
                    y_pos = center_y - 100
                elif "conv" in nid:
                    w, h = 120, 160
                    y_pos = center_y - 80
                elif "pool" in nid:
                    w, h = 90, 100
                    y_pos = center_y - 50
                elif "flatten" in nid:
                    w, h = 40, 240
                    y_pos = center_y - 120
                elif "dense" in nid:
                    w, h = 80, 150
                    y_pos = center_y - 75
                node_coords[nid] = {"x": x_pos, "y": y_pos, "w": w, "h": h}
                
    elif topology == "transformer":
        # Stack vertically: bottom to top
        container_coords["enc"] = {"x": center_x - 200, "y": 150, "w": 400, "h": 700}
        
        for node in nodes:
            nid = node["id"]
            parent = node.get("parent")
            
            if parent == "enc":
                if "attn" in nid:
                    node_coords[nid] = {"x": center_x - (node_w / 2), "y": 700, "w": node_w, "h": node_h}
                elif "norm1" in nid:
                    node_coords[nid] = {"x": center_x - (node_w / 2), "y": 550, "w": node_w, "h": node_h}
                elif "ffn" in nid:
                    node_coords[nid] = {"x": center_x - (node_w / 2), "y": 400, "w": node_w, "h": node_h}
                elif "norm2" in nid:
                    node_coords[nid] = {"x": center_x - (node_w / 2), "y": 250, "w": node_w, "h": node_h}
            else:
                # Input embedding at bottom
                node_coords[nid] = {"x": center_x - (node_w / 2), "y": 900, "w": node_w, "h": node_h}
                
    else:
        # Default Rank-based Layered/Hierarchical Layout (Horizontal columns/Vertical stacks)
        # Groups nodes by layer container, or separates them into 3 virtual columns
        layer_ids = [c["id"] for c in containers]
        num_layers = len(layer_ids)
        
        if num_layers > 0:
            layer_w = 400
            layer_h = 750
            spacing_x = (canvas_w - 200 - (num_layers * layer_w)) / max(1, num_layers - 1)
            
            for idx, lid in enumerate(layer_ids):
                lx = 100 + idx * (layer_w + spacing_x)
                ly = 200
                container_coords[lid] = {"x": lx, "y": ly, "w": layer_w, "h": layer_h}
                
                # Place nodes inside layer vertically (or in columns if too many)
                layer_nodes = [n for n in nodes if n.get("parent") == lid]
                num_lnodes = len(layer_nodes)
                
                c_cols = 2 if num_lnodes > 3 else 1
                c_rows = math.ceil(num_lnodes / c_cols)
                col_w = layer_w / c_cols
                row_h = (layer_h - 100) / max(1, c_rows)
                
                for n_idx, node in enumerate(layer_nodes):
                    c_col = n_idx % c_cols
                    c_row = n_idx // c_cols
                    nx = lx + c_col * col_w + (col_w / 2) - (node_w / 2)
                    ny = ly + 80 + c_row * row_h + (row_h / 2) - (node_h / 2)
                    node_coords[node["id"]] = {"x": nx, "y": ny, "w": node_w, "h": node_h}
                    
            # Process remaining nodes that have no parent
            other_nodes = [n for n in nodes if not n.get("parent")]
            for o_idx, node in enumerate(other_nodes):
                node_coords[node["id"]] = {"x": 50, "y": 100 + o_idx * 150, "w": node_w, "h": node_h}
        else:
            # Grid layout if no containers
            num_nodes = len(nodes)
            cols = min(4, math.ceil(math.sqrt(num_nodes)))
            rows = math.ceil(num_nodes / cols)
            grid_w = (canvas_w - 300) / cols
            grid_h = (canvas_h - 300) / rows
            
            for i, node in enumerate(nodes):
                col = i % cols
                row = i // cols
                gx = 150 + col * grid_w + (grid_w / 2) - (node_w / 2)
                gy = 150 + row * grid_h + (grid_h / 2) - (node_h / 2)
                node_coords[node["id"]] = {"x": gx, "y": gy, "w": node_w, "h": node_h}

    # 3. Apply coordinates back to graph objects (ensuring relative coordinates for nested elements!)
    for container in containers:
        cid = container["id"]
        coords = container_coords.get(cid, {"x": 100, "y": 100, "w": 400, "h": 400})
        
        # Check if this container has a parent container, if so make coordinates relative!
        parent = container.get("parent")
        rel_coords = coords.copy()
        if parent and parent in container_coords:
            p_coords = container_coords[parent]
            rel_coords["x"] = coords["x"] - p_coords["x"]
            rel_coords["y"] = coords["y"] - p_coords["y"]
            
        container["layout"] = rel_coords
        
    for node in nodes:
        nid = node["id"]
        coords = node_coords.get(nid, {"x": center_x - (node_w / 2), "y": center_y - (node_h / 2), "w": node_w, "h": node_h})
        
        # Make coordinates relative if nested inside a container!
        parent = node.get("parent")
        rel_coords = coords.copy()
        if parent and parent in container_coords:
            p_coords = container_coords[parent]
            rel_coords["x"] = coords["x"] - p_coords["x"]
            rel_coords["y"] = coords["y"] - p_coords["y"]
            
        node["layout"] = rel_coords

    # Save absolute coordinates inside graph for validator to use (avoids parsing parent relative tree)
    graph["_absolute_coords"] = {
        "nodes": node_coords,
        "containers": container_coords
    }

    return graph
