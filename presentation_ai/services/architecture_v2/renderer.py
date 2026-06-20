from typing import Any, Dict
import json
from services.architecture_v2.topology_detector import detect_topology
from services.architecture_v2.graph_builder import build_graph, build_fallback_template_graph
from services.architecture_v2.graphviz_layout import layout_graph
from services.architecture_v2.validator import validate_layout
from services.architecture_v2.drawio_xml_builder import build_drawio_xml

def generate_architecture_v2(
    architecture_type: str, 
    topic: str, 
    slide_title: str = "", 
    slide_content: str = ""
) -> str:
    """
    Main orchestration function for the architecture_v2 isolated subsystem.
    Handles topology detection, graph building, layout computation, validation with retries, 
    and Draw.io XML translation.
    """
    # 1. Detect topology
    topology = detect_topology(architecture_type, topic)
    print(f"[ARCHITECTURE_V2] Starting diagram generation (type={architecture_type}, resolved_topology={topology})")
    
    if topology == "none":
        return ""
        
    graph = None
    max_attempts = 3
    
    # 2. Render-Validation Loop
    for attempt in range(1, max_attempts + 1):
        print(f"[ARCHITECTURE_V2] Generation attempt {attempt}/{max_attempts}...")
        
        # Build graph structure
        if attempt == 1:
            graph = build_graph(topology, topic, slide_title, slide_content)
        else:
            # Re-build graph with validation errors feedback passed as slide_content
            feedback_str = (
                f"Your previous generated graph had layout issues. Please correct them:\n"
                f"{json.dumps(report.get('errors', []))}\n"
                f"Make sure to specify non-overlapping elements, proper parent containers, and clean paths."
            )
            graph = build_graph(topology, topic, slide_title, feedback_str)
            
        # Compute layout coordinates
        graph = layout_graph(graph, topology)
        
        # Validate layout
        report = validate_layout(graph)
        
        if report["is_valid"]:
            print(f"[ARCHITECTURE_V2] Layout validation PASSED on attempt {attempt}.")
            break
        else:
            print(f"[ARCHITECTURE_V2] Layout validation FAILED on attempt {attempt}. Errors: {report['errors']}")
            
        # Fall back to template on final attempt
        if attempt == max_attempts:
            print("[ARCHITECTURE_V2] Max retry attempts reached. Falling back to pre-designed template graph.")
            graph = build_fallback_template_graph(topology, topic)
            graph = layout_graph(graph, topology)
            
    # 3. Translate to Draw.io XML
    xml = build_drawio_xml(graph)
    print(f"[ARCHITECTURE_V2] Successfully generated Draw.io XML ({len(xml)} characters)")
    
    return xml
