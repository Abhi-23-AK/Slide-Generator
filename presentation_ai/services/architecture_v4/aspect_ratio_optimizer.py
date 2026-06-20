#!/usr/bin/env python3
"""
Aspect Ratio Optimizer for Architecture V4
==========================================
Enforces 15:8 (1.875) aspect ratio by wrapping container nodes into grid rows
using invisible layout-directing Graphviz edges.
"""

import math
from typing import Dict, Any, List

def optimize_aspect_ratio(graph: Dict[str, Any], visual_style: str = None) -> Dict[str, Any]:
    """
    Analyzes the nodes in each container (and root nodes) and adds invisible
    edges to lay them out in a balanced grid matching widescreen slide proportions.
    visual_style is explicitly passed instead of relying on global state.
    """
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    containers = graph.get("containers", [])
    
    # 1. Identify all container IDs (plus None for root level)
    container_ids = [c["id"] for c in containers] + [None]
    
    invisible_edges = []
    
    for cid in container_ids:
        # Get nodes belonging directly to this container
        c_nodes = [n for n in nodes if n.get("parent") == cid]
        N = len(c_nodes)
        
        if N <= 3:
            # For 3 or fewer nodes, let them align in a single row naturally
            continue
            
        # Determine number of columns (C) and rows (R)
        # We want a layout close to 15:8. Since individual nodes are wide (2:1),
        # C x R grid of 2:1 nodes has aspect ratio ~ (C/R) * 2.0.
        # To make (C/R) * 2.0 close to 1.875, C/R should be close to 0.9375 (C roughly equals R).
        C = int(math.ceil(math.sqrt(N)))
        
        # Sort nodes deterministically by ID or label to keep layout stable
        c_nodes = sorted(c_nodes, key=lambda n: n.get("id", ""))
        
        # Arrange nodes in a grid: grid[r][c]
        grid = []
        for i in range(0, N, C):
            grid.append(c_nodes[i:i+C])
            
        # Add vertical invisible edges: grid[r][c] -> grid[r+1][c]
        R = len(grid)
        for r in range(R - 1):
            for c in range(len(grid[r])):
                if c < len(grid[r+1]):
                    src = grid[r][c]["id"]
                    tgt = grid[r+1][c]["id"]
                    invisible_edges.append({
                        "source": src,
                        "target": tgt,
                        "label": "",
                        "style": "invis"  # Mark as invisible
                    })
                    
    # Add invisible edges to the graph's edge list
    if invisible_edges:
        print(f"[ASPECT_RATIO_OPTIMIZER] Injected {len(invisible_edges)} invisible layout-constraining edges.")
        edges.extend(invisible_edges)
        
    return graph
