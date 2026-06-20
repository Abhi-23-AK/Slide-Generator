import os
import json
import subprocess
from typing import Dict, Any, List
from services.architecture_v3.style_engine import get_node_size_hint

def layout_graph(graph: Dict[str, Any], topology: str, node_size_overrides: Dict[str, Dict[str, float]] = None) -> Dict[str, Any]:
    """
    Computes spatial layout coordinates (x, y, width, height) for all nodes and containers
    in the graph by invoking the Graphviz 'dot' layout command.
    """
    if node_size_overrides is None:
        node_size_overrides = {}
        
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    containers = graph.get("containers", [])
    
    # 1. Resolve rankdir
    horizontal_topologies = {
        "ai_pipeline", "microservices", "event_driven", "transformer", 
        "rag_pipeline", "client_server", "flowchart", "mvc", "hexagonal"
    }
    rankdir = "LR" if topology in horizontal_topologies else "TB"
    
    # 2. Build map of container structure
    container_ids = {c["id"] for c in containers}
    container_to_nodes = {c["id"]: [] for c in containers}
    container_to_containers = {c["id"]: [] for c in containers}
    
    root_containers = []
    root_nodes = []
    
    for c in containers:
        parent = c.get("parent")
        if parent and parent in container_ids:
            container_to_containers[parent].append(c["id"])
        else:
            root_containers.append(c["id"])
            
    for n in nodes:
        parent = n.get("parent")
        if parent and parent in container_ids:
            container_to_nodes[parent].append(n["id"])
        else:
            root_nodes.append(n["id"])
            
    # 3. Generate DOT file
    dot_lines = []
    dot_lines.append("digraph G {")
    dot_lines.append(f'  rankdir="{rankdir}";')
    dot_lines.append("  compound=true;")
    n = len(nodes)
    if n <= 10:
        node_sep = 1.5
        rank_sep = 2.0
    elif n <= 20:
        node_sep = 1.2
        rank_sep = 1.8
    elif n <= 40:
        node_sep = 1.0
        rank_sep = 1.5
    else:
        node_sep = 0.8
        rank_sep = 1.2

    dot_lines.append(f"  nodesep={node_sep};")
    dot_lines.append(f"  ranksep={rank_sep};")
    dot_lines.append('  splines="ortho";')
    dot_lines.append("  newrank=true;")
    dot_lines.append("  node [shape=box, fontname=\"Arial\"];")
    
    def render_container(cid: str) -> List[str]:
        c_lines = []
        c_lines.append(f'  subgraph "cluster_{cid}" {{')
        # find label
        label = next((c["label"] for c in containers if c["id"] == cid), cid)
        c_lines.append(f'    label = "{label}";')
        c_lines.append('    style = "dashed,rounded";')
        c_lines.append('    color = "#4a5568";')
        c_lines.append('    margin = 40;')
        
        # Child nodes
        size_hint = get_node_size_hint()
        for nid in container_to_nodes.get(cid, []):
            override = node_size_overrides.get(nid, {})
            w = override.get("w", size_hint["w"])
            h = override.get("h", size_hint["h"])
            inch_w = w / 72.0
            inch_h = h / 72.0
            c_lines.append(f'    "{nid}" [width={inch_w:.3f}, height={inch_h:.3f}, fixedsize=true];')
            
        # Child containers
        for child_cid in container_to_containers.get(cid, []):
            c_lines.extend(render_container(child_cid))
            
        c_lines.append("  }")
        return c_lines

    # Render root containers
    for cid in root_containers:
        dot_lines.extend(render_container(cid))
        
    # Render root nodes
    size_hint = get_node_size_hint()
    for n in root_nodes:
        nid = n["id"]
        override = node_size_overrides.get(nid, {})
        w = override.get("w", size_hint["w"])
        h = override.get("h", size_hint["h"])
        inch_w = w / 72.0
        inch_h = h / 72.0
        dot_lines.append(f'  "{nid}" [width={inch_w:.3f}, height={inch_h:.3f}, fixedsize=true];')
        
    # Render edges
    for idx, edge in enumerate(edges):
        src = edge["source"]
        tgt = edge["target"]
        dot_lines.append(f'  "{src}" -> "{tgt}";')
        
    dot_lines.append("}")
    dot_source = "\n".join(dot_lines)
    
    # 4. Invoke Graphviz 'dot -Tjson'
    dot_paths = [
        "dot", # On Path
        r"C:\Program Files\Graphviz\bin\dot.exe",
        r"C:\Program Files (x86)\Graphviz\bin\dot.exe",
        r"C:\tools\graphviz\bin\dot.exe",
        r"C:\ProgramData\chocolatey\bin\dot.exe",
        r"C:\scoop\apps\graphviz\current\bin\dot.exe",
    ]
    
    dot_exe = None
    for path in dot_paths:
        if path == "dot":
            try:
                subprocess.run(["dot", "-V"], capture_output=True, check=False)
                dot_exe = "dot"
                break
            except Exception:
                continue
        elif os.path.exists(path):
            dot_exe = path
            break
            
    if not dot_exe:
        raise FileNotFoundError(
            "Graphviz 'dot' executable not found on PATH or common installation locations. "
            "Graphviz layout is required for architecture_v3."
        )
        
    result = subprocess.run(
        [dot_exe, "-Tjson"],
        input=dot_source,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True
    )
    
    dot_json = json.loads(result.stdout)
    
    # 5. Parse absolute coordinates from JSON
    # Bounding box of full graph
    bb_str = dot_json.get("bb", "0,0,1000,1000")
    bb_parts = [float(x) for x in bb_str.split(",")]
    total_h = bb_parts[3]  # ury
    
    node_coords = {}
    container_coords = {}
    
    for obj in dot_json.get("objects", []):
        obj_name = obj.get("name", "")
        # Is it a cluster?
        if obj_name.startswith("cluster_"):
            cid = obj_name[len("cluster_"):]
            c_bb_str = obj.get("bb")
            if c_bb_str:
                parts = [float(x) for x in c_bb_str.split(",")]
                llx, lly, urx, ury = parts
                w = urx - llx
                h = ury - lly
                x = llx
                y = total_h - ury
                container_coords[cid] = {"x": x, "y": y, "w": w, "h": h}
        else:
            # It's a node
            nid = obj_name
            pos_str = obj.get("pos")
            if pos_str:
                cx, cy = [float(x) for x in pos_str.split(",")]
                size_hint = get_node_size_hint()
                override = node_size_overrides.get(nid, {})
                w = override.get("w", size_hint["w"])
                h = override.get("h", size_hint["h"])
                x = cx - w / 2.0
                y = total_h - cy - h / 2.0
                node_coords[nid] = {"x": x, "y": y, "w": w, "h": h}
                
    # 6. Convert absolute to relative coordinates for nested elements
    for c in containers:
        cid = c["id"]
        abs_c = container_coords.get(cid, {"x": 100, "y": 100, "w": 400, "h": 400})
        parent = c.get("parent")
        rel_c = abs_c.copy()
        if parent and parent in container_coords:
            p_abs = container_coords[parent]
            rel_c["x"] = abs_c["x"] - p_abs["x"]
            rel_c["y"] = abs_c["y"] - p_abs["y"]
        c["layout"] = rel_c
        
    size_hint = get_node_size_hint()
    for n in nodes:
        nid = n["id"]
        abs_n = node_coords.get(nid, {"x": 200, "y": 200, "w": size_hint["w"], "h": size_hint["h"]})
        parent = n.get("parent")
        rel_n = abs_n.copy()
        if parent and parent in container_coords:
            p_abs = container_coords[parent]
            rel_n["x"] = abs_n["x"] - p_abs["x"]
            rel_n["y"] = abs_n["y"] - p_abs["y"]
        n["layout"] = rel_n
        
    # Save absolute coordinates for validator
    graph["_absolute_coords"] = {
        "nodes": node_coords,
        "containers": container_coords
    }
    
    return graph
