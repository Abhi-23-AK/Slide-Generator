from typing import Dict, Any
from services.architecture_v3.topology_detector import detect_topology
from services.architecture_v3.graph_builder import build_graph
from services.architecture_v3.graphviz_layout import layout_graph
from services.architecture_v3.validator import validate_layout
from services.architecture_v3.drawio_xml_builder import build_drawio_xml

def generate_architecture_v3(
    architecture_type: str, 
    topic: str, 
    slide_title: str = "", 
    slide_content: str = ""
) -> str:
    """
    Main orchestration function for the architecture_v3 subsystem.
    Computes graph layout using Graphviz, performs self-correction, and returns Draw.io XML.
    """
    # 1. Detect topology
    topology = detect_topology(architecture_type, topic)
    print(f"[ARCHITECTURE_V3] Starting diagram generation (type={architecture_type}, resolved_topology={topology})")
    
    if topology == "none":
        return ""
        
    # 2. Build graph structure
    graph = build_graph(topology, topic, slide_title, slide_content)
    
    # Node size overrides dictionary for self-correction feedback loop
    node_size_overrides = {}
    
    max_attempts = 3
    # 3. Layout - Validation - Self-correction loop
    for attempt in range(1, max_attempts + 1):
        print(f"[ARCHITECTURE_V3] Layout rendering attempt {attempt}/{max_attempts}...")
        
        # Compute layout via Graphviz
        try:
            graph = layout_graph(graph, topology, node_size_overrides)
        except Exception as layout_err:
            print(f"[ARCHITECTURE_V3] Graphviz layout call failed: {layout_err}")
            raise layout_err
            
        # Validate layout
        report = validate_layout(graph)
        print(f"[ARCHITECTURE_V3] Validation report (attempt {attempt}): is_valid={report['is_valid']}, clipped={report['clipped_nodes']}")
        
        # If text clipping is detected, expand node widths and retry layout
        if report["clipped_nodes"] and attempt < max_attempts:
            print(f"[ARCHITECTURE_V3] Feedback loop: text clipping detected on {report['clipped_nodes']}. Enlarging nodes and recalculating layout...")
            for nid in report["clipped_nodes"]:
                # Increase width by 40px
                current_w = node_size_overrides.get(nid, {}).get("w", 160)
                node_size_overrides[nid] = {"w": current_w + 40, "h": 80}
            continue
        else:
            # Overlaps or crossings (we print warning but proceed, since Graphviz dot rarely has overlaps)
            if not report["is_valid"]:
                print(f"[ARCHITECTURE_V3] Layout validation issues found: {report['errors']}")
            break
            
    # 4. Generate Draw.io XML
    xml = build_drawio_xml(graph)
    print(f"[ARCHITECTURE_V3] Successfully generated Draw.io XML ({len(xml)} characters)")
    return xml
