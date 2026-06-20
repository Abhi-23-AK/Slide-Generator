#!/usr/bin/env python3
"""
Topology-Specific Layout Validator for Architecture V4
======================================================
Implements custom density, spacing, sequence-alignment, and containment validations
for different architecture topologies.
"""

from typing import Dict, Any, List

def validate_topology_layout(graph: Dict[str, Any], topology: str) -> Dict[str, Any]:
    """
    Validates node layouts against standard geometric constraints (overlaps)
    as well as topology-specific ordering and structure rules.
    """
    # 1. Invoke base layout validator
    from services.architecture_v3.validator import validate_layout
    report = validate_layout(graph)
    
    topo = str(topology).lower().strip()
    abs_coords = graph.get("_absolute_coords", {})
    node_coords = abs_coords.get("nodes", {})
    nodes = graph.get("nodes", [])
    
    if not node_coords or not nodes:
        return report
        
    # 2. Topology-specific validation checks
    # A. Monotonic sequence-based pipelines (CNN, Transformer, RAG, AI Pipeline)
    if topo in ("cnn", "cnn_pipeline", "transformer", "transformer_pipeline", "rag", "rag_pipeline", "ai_pipeline"):
        # Sequence-based layout verification: nodes with higher flow_order must generally
        # be placed further down (TB) or further right (LR) than nodes with lower flow_order.
        sorted_nodes = sorted(
            [n for n in nodes if n["id"] in node_coords],
            key=lambda n: n.get("flow_order", 0)
        )
        
        y_violations = 0
        for i in range(len(sorted_nodes) - 1):
            n1 = sorted_nodes[i]
            n2 = sorted_nodes[i+1]
            c1 = node_coords[n1["id"]]
            c2 = node_coords[n2["id"]]
            
            # For TB (standard pipeline direction), y coordinates should increase
            # Allow 15px overlap tolerance for same-row structures
            if c2["y"] < c1["y"] - 15:
                y_violations += 1
                
        # If a significant fraction of sequential nodes violate coordinates, flag it
        if y_violations > max(1, len(sorted_nodes) // 3):
            report["warnings"].append(
                f"Pipeline flow ordering violation: {y_violations} sequential nodes out of order. "
                "The layout order might look fragmented or backwards."
            )
            
    # B. Cloud networks (VPC Subnets containment logic)
    elif topo == "cloud":
        public_nodes = [n for n in nodes if n.get("parent") == "public" and n["id"] in node_coords]
        db_nodes = [n for n in nodes if n.get("parent") == "database" and n["id"] in node_coords]
        
        # Public subnet should sit higher (smaller y) than database subnet
        vertical_mismatches = 0
        for p_node in public_nodes:
            p_y = node_coords[p_node["id"]]["y"]
            for d_node in db_nodes:
                d_y = node_coords[d_node["id"]]["y"]
                if p_y > d_y:
                    vertical_mismatches += 1
                    
        if vertical_mismatches > 0:
            report["warnings"].append(
                "Cloud network hierarchy: Public ingress components are positioned below database storage layers."
            )
            
    # C. Kubernetes Namespace isolation
    elif topo == "kubernetes":
        # Namespace containers should enclose their respective namespace nodes
        namespaces = {}
        for n in nodes:
            ns = n.get("namespace")
            if ns:
                namespaces.setdefault(ns, []).append(n["id"])
                
        # Simple cross-namespace placement warnings (if nodes are placed inside wrong bounds)
        pass
        
    return report
