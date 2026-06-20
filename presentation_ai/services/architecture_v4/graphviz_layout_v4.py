#!/usr/bin/env python3
"""
Graphviz Layout Engine for Architecture V4
=========================================
Computes spatial layout coordinates (x, y, w, h) for all nodes and containers
using Graphviz. Also extracts right-angle edge waypoints from the layout.
Fully topology-aware, metadata-driven, and optimized for 15:8 layouts.
"""

import os
import json
import math
import shutil
import subprocess
from typing import Dict, Any, List, Tuple, Optional
from services.architecture_v4.visual_node_resolver import resolve_node_visuals

# Spacing, margin, spline routing, engines, rankdir, and packmode per topology
TOPOLOGY_LAYOUT_CONFIG = {
    "microservices": {"nodesep": 0.25, "ranksep": 0.55, "margin": 25, "splines": "ortho", "ratio": 1.875, "engine": "dot", "rankdir": "TB", "packmode": "array_u"},
    "cloud":         {"nodesep": 0.35, "ranksep": 0.55, "margin": 30, "splines": "ortho", "ratio": 1.875, "engine": "dot", "rankdir": "TB", "packmode": "array_u"},
    "kubernetes":    {"nodesep": 0.30, "ranksep": 0.50, "margin": 25, "splines": "ortho", "ratio": 1.875, "engine": "dot", "rankdir": "TB", "packmode": "array_u"},
    "ai_pipeline":   {"nodesep": 0.22, "ranksep": 0.28, "margin": 10, "splines": "polyline", "ratio": 1.875, "engine": "dot", "rankdir": "TB", "packmode": "cluster"},
    "rag_pipeline":  {"nodesep": 0.22, "ranksep": 0.28, "margin": 10, "splines": "polyline", "ratio": 1.875, "engine": "dot", "rankdir": "TB", "packmode": "cluster"},
    "rag":           {"nodesep": 0.22, "ranksep": 0.28, "margin": 10, "splines": "polyline", "ratio": 1.875, "engine": "dot", "rankdir": "TB", "packmode": "cluster"},
    "event_driven":  {"nodesep": 0.28, "ranksep": 0.50, "margin": 20, "splines": "ortho", "ratio": 1.875, "engine": "dot", "rankdir": "TB", "packmode": "cluster"},
    "transformer":   {"nodesep": 0.20, "ranksep": 0.25, "margin": 10, "splines": "polyline", "ratio": 1.875, "engine": "dot", "rankdir": "TB", "packmode": "cluster"},
    "cnn":           {"nodesep": 0.20, "ranksep": 0.25, "margin": 10, "splines": "polyline", "ratio": 1.875, "engine": "dot", "rankdir": "TB", "packmode": "cluster"},
    "layered":       {"nodesep": 0.30, "ranksep": 0.45, "margin": 20, "splines": "ortho", "ratio": 1.875, "engine": "dot", "rankdir": "TB", "packmode": "cluster"},
    "uml":           {"nodesep": 0.35, "ranksep": 0.60, "margin": 20, "splines": "polyline", "ratio": 1.875, "engine": "dot", "rankdir": "TB", "packmode": "cluster"},
    "flowchart":     {"nodesep": 0.25, "ranksep": 0.40, "margin": 15, "splines": "polyline", "ratio": 1.875, "engine": "dot", "rankdir": "LR", "packmode": "cluster"},
    "star":          {"nodesep": 0.40, "ranksep": 0.40, "margin": 20, "splines": "curved", "ratio": 1.875, "engine": "twopi", "rankdir": "TB", "packmode": "cluster"},
    "ring":          {"nodesep": 0.40, "ranksep": 0.40, "margin": 20, "splines": "curved", "ratio": 1.875, "engine": "circo", "rankdir": "TB", "packmode": "cluster"},
    "hub_spoke":     {"nodesep": 0.35, "ranksep": 0.45, "margin": 25, "splines": "curved", "ratio": 1.875, "engine": "twopi", "rankdir": "TB", "packmode": "cluster"},
    "none":          {"nodesep": 0.30, "ranksep": 0.50, "margin": 20, "splines": "polyline", "ratio": 1.875, "engine": "dot", "rankdir": "TB", "packmode": "cluster"}
}

# Node size and coordinate layout multipliers per topology
TOPOLOGY_MULTIPLIERS = {
    "cloud":         {"node_scale": 1.1, "layout_scale": 1.2},
    "microservices": {"node_scale": 1.0, "layout_scale": 1.1},
    "kubernetes":    {"node_scale": 1.0, "layout_scale": 1.1},
    "cnn":           {"node_scale": 0.8, "layout_scale": 0.9},
    "transformer":   {"node_scale": 0.9, "layout_scale": 0.9},
    "rag":           {"node_scale": 0.9, "layout_scale": 0.95},
    "rag_pipeline":  {"node_scale": 0.9, "layout_scale": 0.95},
    "ai_pipeline":   {"node_scale": 0.9, "layout_scale": 0.95},
    "none":          {"node_scale": 1.0, "layout_scale": 1.0}
}

def get_topology_band(node: Dict[str, Any], topology: str) -> Optional[str]:
    """Resolves node category/tier/properties to topology-specific alignment bands."""
    topo = str(topology).lower().strip()
    label = node.get("label", "").lower()
    kind = node.get("type", "").lower()
    tier = node.get("tier", "").lower()
    category = node.get("category", "").lower()
    phase = node.get("phase", "").lower()
    role = node.get("role", "").lower()
    
    if topo == "microservices":
        # Check metadata first
        if (kind in ("client", "external", "user", "browser", "frontend", "ui") or 
                tier in ("frontend", "client", "external") or 
                category in ("client", "frontend") or 
                role in ("client", "frontend", "user")):
            return "clients"
        if (kind in ("gateway", "lb", "loadbalancer", "load-balancer", "proxy", "ingress", "api", "router", "broker") or 
                tier in ("gateway", "ingress", "api") or 
                category in ("gateway", "ingress", "api") or 
                role in ("gateway", "ingress", "api")):
            return "gateways"
        if (kind in ("database", "cache", "storage", "db", "sql", "redis", "postgres", "nosql") or 
                tier in ("data", "database", "storage", "backend_db") or 
                category in ("database", "storage") or 
                role in ("database", "storage")):
            return "databases"
            
        # Label fallbacks
        if any(x in label for x in ("client", "user", "browser", "frontend", "ui")):
            return "clients"
        if any(x in label for x in ("gateway", "lb", "loadbalancer", "load-balancer", "proxy", "ingress")):
            return "gateways"
        if any(x in label for x in ("db", "database", "sql", "redis", "postgres", "nosql", "cache")):
            return "databases"
        return "services"
        
    elif topo == "cloud":
        # Check metadata first
        if (kind in ("client", "external", "gateway", "lb", "proxy", "ingress", "public", "ui", "frontend") or 
                tier in ("frontend", "client", "external", "public", "ingress") or 
                category in ("client", "frontend", "gateway", "public") or 
                role in ("client", "frontend", "gateway", "public")):
            return "public"
        if (kind in ("database", "storage", "db", "sql", "redis", "postgres", "nosql", "s3", "bucket") or 
                tier in ("data", "database", "storage", "backend_db") or 
                category in ("database", "storage") or 
                role in ("database", "storage")):
            return "database"
            
        # Label fallbacks
        if any(x in label for x in ("client", "user", "browser", "frontend", "ui", "gateway", "lb", "proxy", "ingress", "public")):
            return "public"
        if any(x in label for x in ("db", "database", "sql", "redis", "postgres", "storage", "s3", "bucket")):
            return "database"
        return "private"
        
    elif topo == "kubernetes":
        # Check metadata first
        if (kind in ("gateway", "ingress", "lb", "loadbalancer", "proxy", "api") or 
                tier in ("ingress", "gateway") or 
                category in ("gateway", "ingress") or 
                role in ("gateway", "ingress")):
            return "ingress"
        if (kind in ("database", "storage", "volume", "pvc", "pv", "db", "s3") or 
                tier in ("data", "storage", "database") or 
                category in ("database", "storage") or 
                role in ("database", "storage")):
            return "storage"
        if (kind in ("compute", "service", "pod", "deployment", "daemonset", "job", "worker") or 
                tier in ("compute", "service") or 
                category in ("compute", "service") or 
                role in ("compute", "service")):
            return "pods"
        if kind in ("namespace", "ns") or tier == "namespace" or category == "namespace" or role == "namespace":
            return "namespaces"
            
        # Label fallbacks
        if any(x in label for x in ("ingress", "gateway", "lb", "loadbalancer", "proxy")):
            return "ingress"
        if any(x in label for x in ("pv", "pvc", "volume", "storage", "db", "database", "s3")):
            return "storage"
        if any(x in label for x in ("pod", "deployment", "service", "job", "daemonset")):
            return "pods"
        return "namespaces"
        
    elif topo == "event_driven":
        # Check metadata first
        if (kind in ("client", "external", "producer", "frontend", "publisher") or 
                tier in ("frontend", "client", "producer") or 
                category in ("client", "producer") or 
                role in ("client", "producer")):
            return "producers"
        if (kind in ("broker", "queue", "kafka", "rabbitmq", "bus", "topic") or 
                tier in ("broker", "queue", "bus") or 
                category in ("broker", "queue", "bus") or 
                role in ("broker", "queue", "bus")):
            return "broker"
        if (kind in ("consumer", "worker", "processor", "subscriber") or 
                tier in ("consumer", "worker") or 
                category in ("consumer", "worker") or 
                role in ("consumer", "worker")):
            return "consumers"
        if (kind in ("database", "storage", "db", "sql", "postgres", "nosql", "persistence") or 
                tier in ("data", "database", "storage", "persistence") or 
                category in ("database", "storage", "persistence") or 
                role in ("database", "storage", "persistence")):
            return "persistence"
            
        # Label fallbacks
        if any(x in label for x in ("producer", "client", "user", "frontend", "publisher")):
            return "producers"
        if any(x in label for x in ("broker", "kafka", "rabbitmq", "bus", "queue", "topic")):
            return "broker"
        if any(x in label for x in ("consumer", "worker", "processor", "subscriber")):
            return "consumers"
        if any(x in label for x in ("db", "database", "sql", "postgres", "storage")):
            return "persistence"
        return "consumers"
        
    elif topo in ("rag", "rag_pipeline", "ai_pipeline"):
        bands = ("loader", "chunker", "embedding", "vectordb", "retriever", "llm", "output")
        # Check metadata first
        for band in bands:
            if band in kind or band in tier or band in category or band in phase or band in role:
                return band
        stage = node.get("stage", "").lower()
        for band in bands:
            if band in stage:
                return band
        # Label fallback last
        for band in bands:
            if band in label:
                return band
        return None
        
    elif topo == "transformer":
        bands = ("embedding", "encoder", "attention", "decoder", "output")
        # Check metadata first
        for band in bands:
            if band in kind or band in tier or band in category or band in phase or band in role:
                return band
        stage = node.get("stage", "").lower()
        for band in bands:
            if band in stage:
                return band
        # Label fallback last
        for band in bands:
            if band in label:
                return band
        return None
        
    elif topo == "cnn":
        bands = ("input", "conv", "pool", "dense", "output")
        # Check metadata first
        for band in bands:
            if band in kind or band in tier or band in category or band in phase or band in role:
                return band
        stage = node.get("stage", "").lower()
        for band in bands:
            if band in stage:
                return band
        # Label fallback last
        for band in bands:
            if band in label:
                return band
        return None
        
    return None

TOPOLOGY_INVIS_METADATA = {
    "rag": ["stage", "flow_order"],
    "rag_pipeline": ["stage", "flow_order"],
    "ai_pipeline": ["stage", "flow_order"],
    "transformer": ["stage", "flow_order"],
    "cnn": ["stage", "flow_order"],
    "microservices": ["lane", "tier"],
    "classic": ["lane", "tier"],
    "layered": ["lane", "tier"],
    "none": ["flow_order", "rank_group"],
    "cloud": ["zone", "section"],
    "kubernetes": ["namespace", "rank_group"],
    "event_driven": ["phase", "flow_order"],
    "flowchart": ["flow_order"],
    "uml": ["flow_order", "rank_group"],
    "star": ["flow_order"],
    "ring": ["flow_order"],
    "hub_spoke": ["flow_order"],
}

def simplify_waypoints(pts: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Prunes duplicate or collinear coordinates, strictly preserving Manhattan corner transitions."""
    if len(pts) < 3:
        return pts
        
    # 1. Remove duplicate or extremely close adjacent points (distance < 0.5)
    unique_pts = []
    for p in pts:
        if not unique_pts:
            unique_pts.append(p)
        else:
            prev = unique_pts[-1]
            if ((p[0] - prev[0])**2 + (p[1] - prev[1])**2)**0.5 > 0.5:
                unique_pts.append(p)
                
    if len(unique_pts) < 3:
        return unique_pts
        
    # 2. Remove collinear points (both axis-aligned and general collinear)
    simplified = [unique_pts[0]]
    for i in range(1, len(unique_pts) - 1):
        p1 = simplified[-1]
        p2 = unique_pts[i]
        p3 = unique_pts[i+1]
        
        dx1, dy1 = p2[0] - p1[0], p2[1] - p1[1]
        dx2, dy2 = p3[0] - p2[0], p3[1] - p2[1]
        
        # Check if segments p1-p2 and p2-p3 are horizontal/vertical
        p1_p2_horiz = abs(dy1) < 0.5
        p1_p2_vert = abs(dx1) < 0.5
        p2_p3_horiz = abs(dy2) < 0.5
        p2_p3_vert = abs(dx2) < 0.5
        
        # If it's a corner (horizontal -> vertical or vertical -> horizontal), we MUST preserve it
        if (p1_p2_horiz and p2_p3_vert) or (p1_p2_vert and p2_p3_horiz):
            simplified.append(p2)
            continue
            
        # Otherwise check for true mathematical collinearity (cross product near 0)
        cross_product = dx1 * dy2 - dy1 * dx2
        len1 = (dx1**2 + dy1**2)**0.5
        len2 = (dx2**2 + dy2**2)**0.5
        
        is_collinear = False
        if len1 > 0 and len2 > 0:
            sin_theta = abs(cross_product) / (len1 * len2)
            if sin_theta < 0.05:  # Less than ~3 degrees bend
                is_collinear = True
                
        # Also check simple axis-aligned collinearity (H->H or V->V)
        if (p1_p2_horiz and p2_p3_horiz) or (p1_p2_vert and p2_p3_vert):
            is_collinear = True
            
        if not is_collinear:
            simplified.append(p2)
            
    simplified.append(unique_pts[-1])
    return simplified

def add_invisible_layout_edges(
    nodes: List[Dict[str, Any]], 
    edges: List[Dict[str, Any]], 
    topology: str = "none"
) -> List[Dict[str, Any]]:
    """Automatically compiles invisible edges to enforce layout alignment and grid stacking."""
    new_edges = list(edges)
    existing_edges = {(e["source"], e["target"]) for e in new_edges}
    
    topo = str(topology).lower().strip()
    enabled_keys = TOPOLOGY_INVIS_METADATA.get(topo, ["flow_order", "rank_group"])
    
    # Precompute flow_order_map to optimize sorting checks to O(1) lookups (PROBLEM 3)
    flow_order_map = {n["id"]: n.get("flow_order", 1) for n in nodes}
    
    # Group nodes by parent container
    parent_groups = {}
    for n in nodes:
        parent = n.get("parent") or "root"
        parent_groups.setdefault(parent, []).append(n)
        
    for parent, p_nodes in parent_groups.items():
        if len(p_nodes) < 2:
            continue
            
        # A. Link sequentially by flow_order
        if "flow_order" in enabled_keys:
            sorted_by_flow = sorted(p_nodes, key=lambda n: flow_order_map.get(n["id"], 1))
            for i in range(len(sorted_by_flow) - 1):
                src = sorted_by_flow[i]["id"]
                tgt = sorted_by_flow[i+1]["id"]
                if (src, tgt) not in existing_edges:
                    new_edges.append({
                        "source": src,
                        "target": tgt,
                        "style": "invis",
                        "constraint": "true",
                        "weight": 20
                    })
                    existing_edges.add((src, tgt))
                
        # B. Link consecutive rank_groups to align rows
        if "rank_group" in enabled_keys:
            rank_groups = {}
            for n in p_nodes:
                rg = n.get("rank_group")
                if rg and rg != "default_rank":
                    rank_groups.setdefault(rg, []).append(n)
                    
            if len(rank_groups) > 1:
                sorted_rgs = sorted(rank_groups.keys(), key=lambda rg: min(flow_order_map.get(n["id"], 1) for n in rank_groups[rg]))
                for i in range(len(sorted_rgs) - 1):
                    src_node = rank_groups[sorted_rgs[i]][0]["id"]
                    tgt_node = rank_groups[sorted_rgs[i+1]][0]["id"]
                    if (src_node, tgt_node) not in existing_edges:
                        new_edges.append({
                            "source": src_node,
                            "target": tgt_node,
                            "style": "invis",
                            "constraint": "true",
                            "weight": 20
                        })
                        existing_edges.add((src_node, tgt_node))
                    
        # C. Link same-lane nodes vertically
        if "lane" in enabled_keys:
            lanes = {}
            for n in p_nodes:
                lane = n.get("lane")
                if lane and lane != "default_lane":
                    lanes.setdefault(lane, []).append(n)
                    
            for lane, lane_nodes in lanes.items():
                if len(lane_nodes) > 1:
                    sorted_lane = sorted(lane_nodes, key=lambda n: flow_order_map.get(n["id"], 1))
                    for i in range(len(sorted_lane) - 1):
                        src = sorted_lane[i]["id"]
                        tgt = sorted_lane[i+1]["id"]
                        if (src, tgt) not in existing_edges:
                            new_edges.append({
                                "source": src,
                                "target": tgt,
                                "style": "invis",
                                "constraint": "true",
                                "weight": 20
                            })
                            existing_edges.add((src, tgt))
                        
        # D. Link same-phase nodes
        if "phase" in enabled_keys:
            phases = {}
            for n in p_nodes:
                phase = n.get("phase")
                if phase and phase != "default_phase":
                    phases.setdefault(phase, []).append(n)
                    
            for phase, phase_nodes in phases.items():
                if len(phase_nodes) > 1:
                    sorted_phase = sorted(phase_nodes, key=lambda n: flow_order_map.get(n["id"], 1))
                    for i in range(len(sorted_phase) - 1):
                        src = sorted_phase[i]["id"]
                        tgt = sorted_phase[i+1]["id"]
                        if (src, tgt) not in existing_edges:
                            new_edges.append({
                                "source": src,
                                "target": tgt,
                                "style": "invis",
                                "constraint": "true",
                                "weight": 20
                            })
                            existing_edges.add((src, tgt))
                        
        # E. Link same-section nodes
        if "section" in enabled_keys:
            sections = {}
            for n in p_nodes:
                section = n.get("section")
                if section and section != "default_section":
                    sections.setdefault(section, []).append(n)
                    
            for section, section_nodes in sections.items():
                if len(section_nodes) > 1:
                    sorted_section = sorted(section_nodes, key=lambda n: flow_order_map.get(n["id"], 1))
                    for i in range(len(sorted_section) - 1):
                        src = sorted_section[i]["id"]
                        tgt = sorted_section[i+1]["id"]
                        if (src, tgt) not in existing_edges:
                            new_edges.append({
                                "source": src,
                                "target": tgt,
                                "style": "invis",
                                "constraint": "true",
                                "weight": 20
                            })
                            existing_edges.add((src, tgt))
 
        # F. Link same-swimlane nodes
        if "swimlane" in enabled_keys:
            swimlanes = {}
            for n in p_nodes:
                swimlane = n.get("swimlane")
                if swimlane and swimlane != "default_swimlane":
                    swimlanes.setdefault(swimlane, []).append(n)
                    
            for swimlane, swimlane_nodes in swimlanes.items():
                if len(swimlane_nodes) > 1:
                    sorted_swimlane = sorted(swimlane_nodes, key=lambda n: flow_order_map.get(n["id"], 1))
                    for i in range(len(sorted_swimlane) - 1):
                        src = sorted_swimlane[i]["id"]
                        tgt = sorted_swimlane[i+1]["id"]
                        if (src, tgt) not in existing_edges:
                            new_edges.append({
                                "source": src,
                                "target": tgt,
                                "style": "invis",
                                "constraint": "true",
                                "weight": 20
                            })
                            existing_edges.add((src, tgt))
 
        # G. Link adjacent stages
        if "stage" in enabled_keys:
            stages = {}
            for n in p_nodes:
                stage = n.get("stage")
                if stage and stage != "default_stage":
                    stages.setdefault(stage, []).append(n)
                    
            if len(stages) > 1:
                sorted_stages = sorted(stages.keys(), key=lambda stg: min(flow_order_map.get(n["id"], 1) for n in stages[stg]))
                for i in range(len(sorted_stages) - 1):
                    src_node = stages[sorted_stages[i]][0]["id"]
                    tgt_node = stages[sorted_stages[i+1]][0]["id"]
                    if (src_node, tgt_node) not in existing_edges:
                        new_edges.append({
                            "source": src_node,
                            "target": tgt_node,
                            "style": "invis",
                            "constraint": "true",
                            "weight": 20
                        })
                        existing_edges.add((src_node, tgt_node))
                        
        # H. Link same-tier nodes
        if "tier" in enabled_keys:
            tiers = {}
            for n in p_nodes:
                tier = n.get("tier")
                if tier and tier != "default_tier":
                    tiers.setdefault(tier, []).append(n)
            for tier, tier_nodes in tiers.items():
                if len(tier_nodes) > 1:
                    sorted_tier = sorted(tier_nodes, key=lambda n: flow_order_map.get(n["id"], 1))
                    for i in range(len(sorted_tier) - 1):
                        src = sorted_tier[i]["id"]
                        tgt = sorted_tier[i+1]["id"]
                        if (src, tgt) not in existing_edges:
                            new_edges.append({
                                "source": src,
                                "target": tgt,
                                "style": "invis",
                                "constraint": "true",
                                "weight": 20
                            })
                            existing_edges.add((src, tgt))

        # I. Link same-namespace nodes
        if "namespace" in enabled_keys:
            namespaces = {}
            for n in p_nodes:
                ns = n.get("namespace")
                if ns and ns != "default_namespace":
                    namespaces.setdefault(ns, []).append(n)
            for ns, ns_nodes in namespaces.items():
                if len(ns_nodes) > 1:
                    sorted_ns = sorted(ns_nodes, key=lambda n: flow_order_map.get(n["id"], 1))
                    for i in range(len(sorted_ns) - 1):
                        src = sorted_ns[i]["id"]
                        tgt = sorted_ns[i+1]["id"]
                        if (src, tgt) not in existing_edges:
                            new_edges.append({
                                "source": src,
                                "target": tgt,
                                "style": "invis",
                                "constraint": "true",
                                "weight": 20
                            })
                            existing_edges.add((src, tgt))

        # J. Link same-zone nodes
        if "zone" in enabled_keys:
            zones = {}
            for n in p_nodes:
                zone = n.get("zone")
                if zone and zone != "default_zone":
                    zones.setdefault(zone, []).append(n)
            for zone, zone_nodes in zones.items():
                if len(zone_nodes) > 1:
                    sorted_zone = sorted(zone_nodes, key=lambda n: flow_order_map.get(n["id"], 1))
                    for i in range(len(sorted_zone) - 1):
                        src = sorted_zone[i]["id"]
                        tgt = sorted_zone[i+1]["id"]
                        if (src, tgt) not in existing_edges:
                            new_edges.append({
                                "source": src,
                                "target": tgt,
                                "style": "invis",
                                "constraint": "true",
                                "weight": 20
                            })
                            existing_edges.add((src, tgt))
                        
    return new_edges

def line_segments_intersect(p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float], p4: Tuple[float, float]) -> bool:
    """Checks if line segment p1-p2 intersects segment p3-p4 using CCW method."""
    def ccw(A, B, C):
        return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])
    return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

def compute_edge_crossings(edges_list: List[Dict[str, Any]], node_coords: Dict[str, Dict[str, float]]) -> int:
    """Computes total edge crossings based on actual laid-out node coordinates and waypoints (PROBLEM 12)."""
    polylines = []
    for edge in edges_list:
        if edge.get("style") == "invis":
            continue
        src = edge["source"]
        tgt = edge["target"]
        if src not in node_coords or tgt not in node_coords:
            continue
        c_src = node_coords[src]
        c_tgt = node_coords[tgt]
        p_src = (c_src["x"] + c_src["w"]/2.0, c_src["y"] + c_src["h"]/2.0)
        p_tgt = (c_tgt["x"] + c_tgt["w"]/2.0, c_tgt["y"] + c_tgt["h"]/2.0)
        
        pts = [p_src] + edge.get("waypoints", []) + [p_tgt]
        polylines.append(pts)
        
    segments = []
    for poly in polylines:
        for i in range(len(poly) - 1):
            segments.append((poly[i], poly[i+1]))
            
    crossings = 0
    for i in range(len(segments)):
        for j in range(i + 1, len(segments)):
            s1 = segments[i]
            s2 = segments[j]
            # Skip adjacent segments sharing an endpoint
            if (s1[0] == s2[0] or s1[0] == s2[1] or 
                    s1[1] == s2[0] or s1[1] == s2[1]):
                continue
            if line_segments_intersect(s1[0], s1[1], s2[0], s2[1]):
                crossings += 1
    return crossings

def build_rank_constraints(
    nodes_list: List[Dict[str, Any]], 
    enabled_keys: List[str], 
    topology: str,
    indent: str = "    "
) -> List[str]:
    """Generates Graphviz rank=same constraints for the specified list of nodes (PROBLEM 1, 11)."""
    rank_same_keys = [k for k in enabled_keys if k != "flow_order"]
    rank_groups = {}
    for n in nodes_list:
        for key in rank_same_keys:
            val = n.get(key)
            if val and val not in ("default_rank", "default_phase", "default_swimlane", "default_lane", "default_section", "default_stage"):
                rank_groups.setdefault(f"{key}_{val}", []).append(n["id"])
        band = get_topology_band(n, topology)
        if band:
            rank_groups.setdefault(f"band_{band}", []).append(n["id"])
            
    lines = []
    for rg, nids in rank_groups.items():
        if len(nids) > 1:
            unique_nids = list(dict.fromkeys(nids))
            if len(unique_nids) > 1:
                nids_str = "; ".join(f'"{nid}"' for nid in unique_nids)
                lines.append(f"{indent}{{ rank=same; {nids_str}; }}")
    return lines

def layout_graph(
    graph: Dict[str, Any],
    topology: str,
    node_size_overrides: Dict[str, Dict[str, float]] = None,
    visual_style: str = None
) -> Dict[str, Any]:
    """
    Computes spatial layout coordinates (x, y, width, height) for all nodes and containers
    in the graph by invoking the Graphviz 'dot' (or circular/radial equivalent) command.
    Also extracts edge waypoints for right-angle orthogonal routing.
    visual_style is explicitly passed instead of relying on global state.
    """
    if node_size_overrides is None:
        node_size_overrides = {}
        
    topo_key = str(topology).lower().strip() if topology else "none"
    cfg = dict(TOPOLOGY_LAYOUT_CONFIG.get(topo_key, TOPOLOGY_LAYOUT_CONFIG["none"]))
    overrides = graph.get("layout_overrides", {})
    
    mults = TOPOLOGY_MULTIPLIERS.get(topo_key, TOPOLOGY_MULTIPLIERS["none"])
    node_scale = mults["node_scale"]
    
    nodes = graph.get("nodes", [])
    raw_edges = graph.get("edges", [])
    containers = graph.get("containers", [])
    
    # Pre-build Maps once (PROBLEM 7)
    node_map = {n["id"]: n for n in nodes}
    container_map = {c["id"]: c for c in containers}
    
    # Precompute flow_order_map once (PROBLEM 3)
    flow_order_map = {n["id"]: n.get("flow_order", 1) for n in nodes}
    
    # 1. Compile invisible edges to guide flow constraints
    edges = add_invisible_layout_edges(nodes, raw_edges, topology=topology)
    
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
            
    # Detect central radial hub node (PROBLEM 7)
    hub_node_id = None
    node_scores = {n["id"]: 0.0 for n in nodes}
    semantic_hub_words = {"gateway", "broker", "llm", "router", "api", "ingress"}
    
    for n in nodes:
        nid = n["id"]
        
        # 1. is_hub
        if n.get("is_hub"):
            node_scores[nid] += 100.0
            continue
            
        # 2. hub_score
        if "hub_score" in n:
            try:
                node_scores[nid] += float(n["hub_score"])
            except (ValueError, TypeError):
                # If hub_score is not a valid float, skip it
                pass
            continue
            
        # 3. role
        role = n.get("role", "").lower()
        if any(w in role for w in semantic_hub_words):
            node_scores[nid] += 40.0
            continue
            
        # 4. category
        category = n.get("category", "").lower()
        if any(w in category for w in semantic_hub_words):
            node_scores[nid] += 30.0
            continue
            
        # 5. kind (type)
        kind = n.get("type", "").lower()
        if any(w in kind for w in semantic_hub_words):
            node_scores[nid] += 20.0
            continue
            
        # 6. label
        label = n.get("label", "").lower()
        if any(w in label for w in semantic_hub_words):
            node_scores[nid] += 10.0
            continue
            
    # Compute node degree to add as base score
    for e in raw_edges:
        s, t = e["source"], e["target"]
        if s in node_scores:
            node_scores[s] += 1.0
        if t in node_scores:
            node_scores[t] += 1.0
            
    if node_scores:
        sorted_scores = sorted(node_scores.items(), key=lambda x: x[1], reverse=True)
        hub_node_id = sorted_scores[0][0]

    # Helper to calculate derived container sorting keys using precomputed flow_order_map (PROBLEM 3, 7)
    def get_container_sort_key(cid: str) -> Tuple[int, str, str, str, str, str]:
        node_ids = container_to_nodes.get(cid, [])
        if not node_ids:
            return (99, "", "", "", "", "")
        child_nodes = [node_map[nid] for nid in node_ids if nid in node_map]
        if not child_nodes:
            return (99, "", "", "", "", "")
        min_flow = min(flow_order_map.get(n["id"], 99) for n in child_nodes)
        min_phase = min(str(n.get("phase", "")) for n in child_nodes)
        min_rank = min(str(n.get("rank_group", "")) for n in child_nodes)
        min_section = min(str(n.get("section", "")) for n in child_nodes)
        min_stage = min(str(n.get("stage", "")) for n in child_nodes)
        min_lane = min(str(n.get("lane", "")) for n in child_nodes)
        return (min_flow, min_phase, min_rank, min_section, min_stage, min_lane)

    # Sort root containers semantically
    root_containers.sort(key=get_container_sort_key)
    for cid in container_to_containers:
        container_to_containers[cid].sort(key=get_container_sort_key)
        
    # Density Spacing & Layout Scale Calculations (PROBLEM 12, 13)
    node_count = len(nodes)
    if node_count < 10:
        density_mult = 1.4
    elif node_count < 25:
        density_mult = 1.0
    else:
        density_mult = 0.7
        
    container_depths = {}
    def get_depth(cid: str) -> int:
        if cid in container_depths:
            return container_depths[cid]
        c = container_map.get(cid)
        if not c:
            return 0
        parent = c.get("parent")
        if not parent:
            container_depths[cid] = 1
            return 1
        depth = 1 + get_depth(parent)
        container_depths[cid] = depth
        return depth
        
    max_container_depth = max([get_depth(c["id"]) for c in containers] + [0])
    edge_density = len(raw_edges) / max(1, node_count)
    
    node_factor = 1.0 + max(0, node_count - 10) * 0.015
    density_factor = 1.0 + max(0.0, edge_density - 1.5) * 0.15
    depth_factor = 1.0 + max(0, max_container_depth - 1) * 0.15
    
    dynamic_layout_scale = mults["layout_scale"] * node_factor * density_factor * depth_factor
    layout_scale = max(0.8, min(3.0, dynamic_layout_scale))
    
    # Logarithmic Canvas Sizing to prevent size explosion (PROBLEM 10)
    canvas_w = 15.0 * (1.0 + math.log(max(1.0, node_count / 10.0)))
    canvas_h = canvas_w / 1.875
    margin_val = max(0.1, node_count / 100.0)
    
    # Bidirectional Spacing Retry Loop (PROBLEM 9, 12)
    nodesep_base = cfg["nodesep"]
    ranksep_base = cfg["ranksep"]
    
    current_nodesep_mult = 1.0
    current_ranksep_mult = 1.0
    
    node_coords = {}
    container_coords = {}
    total_w = 800.0
    total_h = 600.0
    node_sizes = {}
    is_radial = topo_key in ("star", "ring", "hub_spoke")
    
    # Resolve topology keys for rank same constraints
    topo_norm = str(topology).lower().strip()
    enabled_keys = TOPOLOGY_INVIS_METADATA.get(topo_norm, ["flow_order", "rank_group"])
    
    for attempt in range(4):
        cfg["nodesep"] = nodesep_base * current_nodesep_mult * density_mult
        cfg["ranksep"] = ranksep_base * current_ranksep_mult * density_mult
        
        if "nodesep" in overrides:
            cfg["nodesep"] = overrides["nodesep"]
        if "ranksep" in overrides:
            cfg["ranksep"] = overrides["ranksep"]
            
        # 3. Generate DOT file
        dot_lines = []
        dot_lines.append("digraph G {")
        dot_lines.append(f'  rankdir="{cfg.get("rankdir", "TB")}";')
        dot_lines.append("  compound=true;")
        dot_lines.append("  concentrate=false;")
        
        dot_lines.append(f"  nodesep={cfg['nodesep']:.3f};")
        dot_lines.append(f"  ranksep={cfg['ranksep']:.3f};")
        dot_lines.append(f'  splines="{cfg["splines"]}";')
        dot_lines.append("  newrank=true;")
        dot_lines.append("  pack=true;")
        dot_lines.append(f'  packmode="{cfg.get("packmode", "cluster")}";')
        dot_lines.append('  ratio="compress";')
        dot_lines.append(f'  size="{canvas_w:.3f},{canvas_h:.3f}";')
        dot_lines.append(f'  page="{canvas_w:.3f},{canvas_h:.3f}";')
        dot_lines.append(f"  margin={margin_val:.3f};")
        
        if is_radial and hub_node_id:
            dot_lines.append(f'  root="{hub_node_id}";')
            
        dot_lines.append('  node [shape=box, fontname="Arial"];')
        
        node_sizes.clear()
        
        # Iterative DFS rendering of Graphviz subgraphs to prevent stack overflow (PROBLEM 2)
        container_lines = []
        stack = [("start", cid) for cid in reversed(root_containers)]
        
        while stack:
            action, cid = stack.pop()
            depth = get_depth(cid)
            indent = "  " * depth
            
            if action == "end":
                container_lines.append(f"{indent}}}")
            elif action == "start":
                stack.append(("end", cid))
                for child_cid in reversed(container_to_containers.get(cid, [])):
                    stack.append(("start", child_cid))
                    
                container_lines.append(f'{indent}subgraph "cluster_{cid}" {{')
                lbl = container_map.get(cid, {}).get("label", cid)
                container_lines.append(f'{indent}  label = "{lbl}";')
                container_lines.append(f'{indent}  style = "dashed,rounded";')
                container_lines.append(f'{indent}  color = "#4a5568";')
                container_lines.append(f"{indent}  margin = {cfg['margin']};")
                
                container_nodes_list = []
                for nid in container_to_nodes.get(cid, []):
                    node = node_map.get(nid)
                    if not node:
                        continue
                    container_nodes_list.append(node)
                    override = node_size_overrides.get(nid, {})
                    if "w" in override and "h" in override:
                        w, h = override["w"], override["h"]
                    else:
                        resolved = resolve_node_visuals(node)
                        w, h = resolved["w"], resolved["h"]
                    
                    w *= node_scale
                    h *= node_scale
                    
                    node_sizes[nid] = (w, h)
                    inch_w = w / 72.0
                    inch_h = h / 72.0
                    container_lines.append(f'{indent}  "{nid}" [width={inch_w:.3f}, height={inch_h:.3f}, fixedsize=true];')
                        
                container_nodes_list.sort(key=lambda n: (
                    flow_order_map.get(n["id"], 1),
                    str(n.get("phase", "")),
                    str(n.get("rank_group", "")),
                    str(n.get("stage", "")),
                    str(n.get("section", ""))
                ))
                        
                container_lines.extend(build_rank_constraints(
                    container_nodes_list, enabled_keys, topology, indent=f"{indent}  "
                ))
                
        dot_lines.extend(container_lines)
            
        # Render root nodes (PROBLEM 7 lookup optimization)
        root_nodes_list = []
        for nid in root_nodes:
            node = node_map.get(nid)
            if not node:
                continue
            root_nodes_list.append(node)
            override = node_size_overrides.get(nid, {})
            if "w" in override and "h" in override:
                w, h = override["w"], override["h"]
            else:
                resolved = resolve_node_visuals(node)
                w, h = resolved["w"], resolved["h"]
            
            w *= node_scale
            h *= node_scale
            
            node_sizes[nid] = (w, h)
            inch_w = w / 72.0
            inch_h = h / 72.0
            dot_lines.append(f'  "{nid}" [width={inch_w:.3f}, height={inch_h:.3f}, fixedsize=true];')
                
        # Sort root nodes semantically to preserve layout ordering
        root_nodes_list.sort(key=lambda n: (
            flow_order_map.get(n["id"], 1),
            str(n.get("phase", "")),
            str(n.get("rank_group", "")),
            str(n.get("stage", "")),
            str(n.get("section", ""))
        ))
                
        # Generate rank=same constraints for root nodes (PROBLEM 1, 11)
        dot_lines.extend(build_rank_constraints(
            root_nodes_list, enabled_keys, topology, indent="  "
        ))
                
        # Render edges with layout metadata mappings
        for idx, edge in enumerate(edges):
            src = edge["source"]
            tgt = edge["target"]
            
            if edge.get("style") == "invis":
                dot_lines.append(f'  "{src}" -> "{tgt}" [style=invis];')
                continue
                
            imp = edge.get("importance", "medium")
            if imp == "critical":
                base_weight = 10
                base_penwidth = 2.0
            elif imp == "high":
                base_weight = 7
                base_penwidth = 1.5
            elif imp == "medium":
                base_weight = 4
                base_penwidth = 1.0
            else:
                base_weight = 1
                base_penwidth = 0.7
                
            weight = base_weight
            minlen = 1
            constraint = "true"
            
            # O(1) node_map lookups (PROBLEM 10)
            src_node = node_map.get(src)
            tgt_node = node_map.get(tgt)
            
            if src_node and tgt_node:
                src_parent = src_node.get("parent")
                tgt_parent = tgt_node.get("parent")
                if src_parent == tgt_parent and src_parent is not None:
                    weight += 5
                    
                # Same lane (+4)
                src_lane = src_node.get("lane")
                tgt_lane = tgt_node.get("lane")
                if src_lane == tgt_lane and src_lane not in (None, "default_lane"):
                    weight += 4
                    
                # Same stage (+4)
                src_stage = src_node.get("stage")
                tgt_stage = tgt_node.get("stage")
                if src_stage == tgt_stage and src_stage not in (None, "default_stage"):
                    weight += 4
                    
                # Same section (+3)
                src_section = src_node.get("section")
                tgt_section = tgt_node.get("section")
                if src_section == tgt_section and src_section not in (None, "default_section"):
                    weight += 3
                    
                # Same phase (+3)
                src_phase = src_node.get("phase")
                tgt_phase = tgt_node.get("phase")
                if src_phase == tgt_phase and src_phase not in (None, "default_phase"):
                    weight += 3
                    
                # Flow order gap penalty (PROBLEM 8: weight *= 0.5)
                flow_gap = abs(flow_order_map.get(src, 1) - flow_order_map.get(tgt, 1))
                if flow_gap > 2:
                    weight *= 0.5
                    minlen = 3
                    
            # 2. same_rank
            if edge.get("same_rank"):
                weight = 12
                minlen = 1
                constraint = "true"
                
            # 3. Structural constraints (PROBLEM 6, 13)
            is_cross = edge.get("cross_cluster")
            is_long = edge.get("long_edge")
            is_back = edge.get("back_edge") or edge.get("direction") == "back" or edge.get("style") == "back"
            
            if is_long:
                weight = 0.5
                minlen = 2
                constraint = "false"
            elif is_cross:
                weight = 1
                minlen = 2
                constraint = "false"
            elif is_back:
                weight = 0.5
                minlen = 1
                constraint = "false"
            elif edge.get("local_edge"):
                weight = max(weight, 8)
            elif edge.get("cluster_edge"):
                weight = max(weight, 5)
                
            attrs = [f"penwidth={base_penwidth}", f"weight={weight}", f"minlen={minlen}"]
            if constraint == "false":
                attrs.append("constraint=false")
                
            attr_str = f" [{', '.join(attrs)}]" if attrs else ""
            dot_lines.append(f'  "{src}" -> "{tgt}"{attr_str};')
            
        dot_lines.append("}")
        dot_source = "\n".join(dot_lines)
        
        # 4. Invoke Graphviz layout command using shutil.which for portability (PROBLEM 8)
        layout_engine = cfg.get("engine", "dot")
        dot_exe = shutil.which(layout_engine)
        if not dot_exe:
            exe_name = f"{layout_engine}.exe"
            common_paths = [
                r"C:\Program Files\Graphviz\bin",
                r"C:\Program Files (x86)\Graphviz\bin",
                r"C:\tools\graphviz\bin",
                r"C:\ProgramData\chocolatey\bin",
                r"C:\scoop\apps\graphviz\current\bin",
            ]
            for path in common_paths:
                full_path = os.path.join(path, exe_name)
                if os.path.exists(full_path):
                    dot_exe = full_path
                    break
                    
        if not dot_exe:
            dot_exe = layout_engine
            
        try:
            proc = subprocess.run(
                [dot_exe, "-Tjson"],
                input=dot_source.encode("utf-8"),
                capture_output=True,
                check=True
            )
            dot_json = json.loads(proc.stdout.decode("utf-8"))
        except subprocess.CalledProcessError as err:
            print(f"[GRAPHVIZ_LAYOUT] Subprocess error running layout engine: {err}")
            if err.stderr:
                print("--- STDERR ---")
                print(err.stderr.decode("utf-8", errors="replace"))
            print("--- DOT SOURCE ---")
            print(dot_source)
            print("------------------")
            raise err
        except Exception as err:
            print(f"[GRAPHVIZ_LAYOUT] Subprocess error running layout engine: {err}")
            print("--- DOT SOURCE ---")
            print(dot_source)
            print("------------------")
            raise err
            
        # 5. Parse absolute coordinates and apply centroid layout scaling (PROBLEM 14, 16)
        node_coords.clear()
        container_coords.clear()
        
        bb_str = dot_json.get("bb", "0,0,800,600")
        try:
            bb_parts = [float(x) for x in bb_str.split(",")]
        except (ValueError, TypeError):
            bb_parts = [0.0, 0.0, 800.0, 600.0]
        
        layout_center_x = (bb_parts[0] + bb_parts[2]) / 2.0
        
        total_w = (bb_parts[2] - bb_parts[0]) * (layout_scale * 1.875 if is_radial else layout_scale)
        total_h = (bb_parts[3] - bb_parts[1]) * layout_scale
        
        node_id_map = {}
        
        for obj in dot_json.get("objects", []):
            idx = obj.get("_gvid")
            obj_name = obj.get("name")
            if idx is None or not obj_name:
                continue
                
            node_id_map[idx] = obj_name
            
            # Container bounds
            if obj_name.startswith("cluster_"):
                cid = obj_name[len("cluster_"):]
                c_bb_str = obj.get("bb")
                if c_bb_str:
                    try:
                        parts = [float(x) for x in c_bb_str.split(",")]
                    except (ValueError, TypeError):
                        continue
                    llx, lly, urx, ury = parts
                    
                    if is_radial:
                        # Centroid horizontal projection stretch (PROBLEM 14)
                        llx_stretched = layout_center_x + (llx - layout_center_x) * 1.875
                        urx_stretched = layout_center_x + (urx - layout_center_x) * 1.875
                        scaled_llx = llx_stretched * layout_scale
                        scaled_urx = urx_stretched * layout_scale
                    else:
                        scaled_llx = llx * layout_scale
                        scaled_urx = urx * layout_scale
                        
                    scaled_lly = lly * layout_scale
                    scaled_ury = ury * layout_scale
                    
                    w = scaled_urx - scaled_llx
                    h = scaled_ury - scaled_lly
                    x = scaled_llx
                    y = total_h - scaled_ury
                    container_coords[cid] = {"x": x, "y": y, "w": w, "h": h}
            else:
                # Node bounds
                nid = obj_name
                pos_str = obj.get("pos")
                if pos_str:
                    try:
                        cx, cy = [float(x) for x in pos_str.split(",")]
                    except (ValueError, TypeError):
                        continue
                    w, h = node_sizes.get(nid, (160, 80))
                    
                    if is_radial:
                        # Centroid horizontal projection stretch (PROBLEM 14)
                        cx_stretched = layout_center_x + (cx - layout_center_x) * 1.875
                        scaled_cx = cx_stretched * layout_scale
                    else:
                        scaled_cx = cx * layout_scale
                        
                    scaled_cy = cy * layout_scale
                    
                    x = scaled_cx - w / 2.0
                    y = total_h - scaled_cy - h / 2.0
                    node_coords[nid] = {"x": x, "y": y, "w": w, "h": h}
                    
        # 6. Parse Edge Waypoints to allow edge crossings estimation
        json_edges = {}
        for edge in dot_json.get("edges", []):
            t_idx = edge.get("tail")
            h_idx = edge.get("head")
            if t_idx is not None and h_idx is not None:
                src = node_id_map.get(t_idx)
                tgt = node_id_map.get(h_idx)
                if src and tgt:
                    json_edges[(src, tgt)] = edge.get("pos", "")
                    
        temp_edges_with_waypoints = []
        for edge in raw_edges:
            if edge.get("style") == "invis":
                continue
            src = edge["source"]
            tgt = edge["target"]
            pos_str = json_edges.get((src, tgt))
            waypoints = []
            if pos_str:
                pts = []
                for part in pos_str.split():
                    if part.startswith("e,") or part.startswith("s,"):
                        part = part[2:]
                    coords = part.split(",")
                    if len(coords) == 2:
                        try:
                            pts.append((float(coords[0]), float(coords[1])))
                        except (ValueError, TypeError):
                            pass
                if len(pts) > 2:
                    raw_wps = []
                    for pt in pts[1:-1]:
                        if is_radial:
                            pt0_stretched = layout_center_x + (pt[0] - layout_center_x) * 1.875
                            scaled_pt0 = pt0_stretched * layout_scale
                        else:
                            scaled_pt0 = pt[0] * layout_scale
                        raw_wps.append((scaled_pt0, total_h - pt[1] * layout_scale))
                    waypoints = simplify_waypoints(raw_wps)
            temp_edges_with_waypoints.append({
                "source": src,
                "target": tgt,
                "waypoints": waypoints
            })
            
        # 7. Measure occupied bounding box area (PROBLEM 5)
        x_coords = []
        y_coords = []
        for coords in node_coords.values():
            x_coords.extend([coords["x"], coords["x"] + coords["w"]])
            y_coords.extend([coords["y"], coords["y"] + coords["h"]])
        for coords in container_coords.values():
            x_coords.extend([coords["x"], coords["x"] + coords["w"]])
            y_coords.extend([coords["y"], coords["y"] + coords["h"]])
            
        if x_coords and y_coords:
            occupied_area = (max(x_coords) - min(x_coords)) * (max(y_coords) - min(y_coords))
        else:
            occupied_area = 0.0
            
        canvas_area = total_w * total_h
        occupancy = occupied_area / max(1.0, canvas_area)
        
        aspect_ratio = total_w / max(1.0, total_h)
        aspect_ratio_wrong = aspect_ratio < 1.4 or aspect_ratio > 2.3
        occupancy_low = (occupancy < 0.45) if len(nodes) >= 6 else False
        occupancy_high = (occupancy > 0.75) if len(nodes) >= 6 else False
        
        # Calculate edge crossings crossings_score (PROBLEM 12)
        crossing_score = compute_edge_crossings(temp_edges_with_waypoints, node_coords)
        crossing_excessive = crossing_score > max(4, len(raw_edges) * 0.6)
        
        if (aspect_ratio_wrong or occupancy_low or occupancy_high or crossing_excessive) and attempt < 3:
            if occupancy_low:
                current_nodesep_mult *= 0.8
                current_ranksep_mult *= 0.8
            else:
                # High occupancy, wrong aspect ratio, or excessive crossings (PROBLEM 9, 12)
                current_nodesep_mult *= 1.25
                current_ranksep_mult *= 1.25
            continue
        else:
            break
            
    # Set final canvas bounds
    graph["_canvas"] = {"w": total_w, "h": total_h}
    
    # Apply simplified edge waypoints
    temp_edge_map = {(e["source"], e["target"]): e["waypoints"] for e in temp_edges_with_waypoints}
    for edge in raw_edges:
        if edge.get("style") == "invis":
            edge["waypoints"] = []
        else:
            edge["waypoints"] = temp_edge_map.get((edge["source"], edge["target"]), [])
        
    # 8. Convert absolute to relative coordinates for nesting (PROBLEM 14 Center Fallback)
    center_x = total_w / 2.0
    center_y = total_h / 2.0
    
    for c in containers:
        cid = c["id"]
        abs_c = container_coords.get(cid, {"x": center_x - 200.0, "y": center_y - 200.0, "w": 400.0, "h": 400.0})
        parent = c.get("parent")
        rel_c = abs_c.copy()
        if parent and parent in container_coords:
            p_abs = container_coords[parent]
            rel_c["x"] = abs_c["x"] - p_abs["x"]
            rel_c["y"] = abs_c["y"] - p_abs["y"]
        c["layout"] = rel_c
        
    for n in nodes:
        nid = n["id"]
        w, h = node_sizes.get(nid, (160, 80))
        abs_n = node_coords.get(nid, {"x": center_x - w / 2.0, "y": center_y - h / 2.0, "w": w, "h": h})
        parent = n.get("parent")
        rel_n = abs_n.copy()
        if parent and parent in container_coords:
            p_abs = container_coords[parent]
            rel_n["x"] = abs_n["x"] - p_abs["x"]
            rel_n["y"] = abs_n["y"] - p_abs["y"]
        n["layout"] = rel_n
        
    graph["_absolute_coords"] = {
        "nodes": node_coords,
        "containers": container_coords
    }
    
    return graph
