#!/usr/bin/env python3
"""
Orchestrator Renderer for Architecture V4
=========================================
Main entry point for generating semantic-driven Architecture V4 diagrams.
Invokes dynamic component extraction, relationship builder, groups elements
into logical layer containers, runs aspect-ratio grid optimization,
computes Graphviz dot layout, and builds final Draw.io XML.
"""

import re
import uuid
import math
import copy
import json
import hashlib
import threading
from typing import Dict, Any, List, Tuple, Optional

import services.architecture_v4.style_engine_v4 as style_engine
from services.architecture_v4.component_extractor import extract_components
from services.architecture_v4.relationship_builder import build_relationships
from services.architecture_v4.aspect_ratio_optimizer import optimize_aspect_ratio
from services.architecture_v4.graphviz_layout_v4 import layout_graph
from services.architecture_v4.drawio_xml_builder_v4 import build_drawio_xml
from services.architecture_v4.container_builder import build_semantic_containers
from services.architecture_v4.topology_validator import validate_topology_layout

# Simple Thread-safe LRU Cache (Problem 14)
class SimpleLRUCache:
    def __init__(self, maxsize: int = 64):
        self.maxsize = maxsize
        self.cache = {}
        self.keys = []
        self.lock = threading.Lock()
        
    def get(self, key: Any) -> Optional[Any]:
        with self.lock:
            if key in self.cache:
                self.keys.remove(key)
                self.keys.append(key)
                return copy.deepcopy(self.cache[key])
            return None
            
    def set(self, key: Any, value: Any) -> None:
        with self.lock:
            if key in self.cache:
                self.keys.remove(key)
            elif len(self.cache) >= self.maxsize:
                oldest = self.keys.pop(0)
                if oldest in self.cache:
                    del self.cache[oldest]
            self.cache[key] = copy.deepcopy(value)
            self.keys.append(key)

# Global caches
_COMPONENTS_CACHE = SimpleLRUCache(32)
_RELATIONSHIPS_CACHE = SimpleLRUCache(32)
_LAYOUTS_CACHE = SimpleLRUCache(32)

def clean_node_id(name: str) -> str:
    """Generates a safe alphanumeric XML ID from a component label."""
    nid = name.replace(" ", "_").replace("-", "_").lower()
    nid = re.sub(r'[^a-zA-Z0-9_]', '', nid)
    if not nid:
        nid = f"node_{uuid.uuid4().hex[:6]}"
    return nid

def get_sha256_hash(data: str) -> str:
    """Computes SHA-256 hex digest for cache keys (Problem 6)."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def resolve_node_name(query_name: str, node_name_to_id: Dict[str, str]) -> Optional[str]:
    """
    Fuzzy node name resolver (Problem 4 / Problem 2 update) that maps queried names
    to node IDs using exact matching, token overlap, and RapidFuzz scoring.
    No substring logic is used to prevent incorrect connections.
    """
    query_clean = query_name.lower().strip()
    if not query_clean:
        return None
        
    # 1. Exact Match
    if query_clean in node_name_to_id:
        return node_name_to_id[query_clean]
        
    # 2. Word Token Overlap Match (Identical word set)
    query_words = set(re.findall(r'\w+', query_clean))
    if query_words:
        for name_key, nid in node_name_to_id.items():
            key_words = set(re.findall(r'\w+', name_key))
            if query_words == key_words:
                return nid
                
    # 3. RapidFuzz Token Match
    try:
        from rapidfuzz import process, fuzz
        choices = list(node_name_to_id.keys())
        best_match = process.extractOne(query_clean, choices, scorer=fuzz.token_sort_ratio)
        if best_match and best_match[1] >= 80.0:
            return node_name_to_id[best_match[0]]
    except Exception:
        pass
        
    return None

def get_layout_aspect_ratio(graph: Dict[str, Any]) -> float:
    """Computes the aspect ratio of the calculated layout bounding box (Problem 11)."""
    abs_coords = graph.get("_absolute_coords", {})
    node_coords = abs_coords.get("nodes", {})
    if not node_coords:
        return style_engine.TARGET_RATIO
    min_x = min(c["x"] for c in node_coords.values())
    max_x = max(c["x"] + c["w"] for c in node_coords.values())
    min_y = min(c["y"] for c in node_coords.values())
    max_y = max(c["y"] + c["h"] for c in node_coords.values())
    w = max_x - min_x
    h = max_y - min_y
    return w / h if h > 0 else style_engine.TARGET_RATIO

def compute_layout_metrics(graph: Dict[str, Any]) -> Dict[str, float]:
    """Computes and returns detailed layout coordinates quality metrics (Problem 8)."""
    abs_coords = graph.get("_absolute_coords", {})
    node_coords = abs_coords.get("nodes", {})
    edges = graph.get("edges", [])
    
    if not node_coords:
        return {
            "density": 0.0,
            "edge_crossings": 0.0,
            "aspect_ratio_score": 0.0,
            "whitespace_ratio": 1.0
        }
        
    min_x = min(c["x"] for c in node_coords.values())
    max_x = max(c["x"] + c["w"] for c in node_coords.values())
    min_y = min(c["y"] for c in node_coords.values())
    max_y = max(c["y"] + c["h"] for c in node_coords.values())
    
    canvas_w = max_x - min_x
    canvas_h = max_y - min_y
    canvas_area = canvas_w * canvas_h
    
    total_node_area = sum(c["w"] * c["h"] for c in node_coords.values())
    density = total_node_area / canvas_area if canvas_area > 0 else 0.0
    
    ar = canvas_w / canvas_h if canvas_h > 0 else style_engine.TARGET_RATIO
    ar_score = abs(ar - style_engine.TARGET_RATIO)
    
    # Calculate edge crossings
    crossings = 0
    from services.architecture_v3.validator import line_intersects
    edge_segments = []
    for edge in edges:
        src_id = edge["source"]
        tgt_id = edge["target"]
        c_src = node_coords.get(src_id)
        c_tgt = node_coords.get(tgt_id)
        if c_src and c_tgt:
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
                crossings += 1
                
    return {
        "density": density,
        "edge_crossings": float(crossings),
        "aspect_ratio_score": ar_score,
        "whitespace_ratio": 1.0 - density
    }

def adapt_node_size(
    node: Dict[str, Any],
    current_size: Dict[str, float],
    topology: str,
    attempt: int,
    visual_style: str
) -> Dict[str, float]:
    """
    Intelligently resizes a node to resolve layout/text-clipping issues
    while respecting its topology, geometry constraints, and aspect ratio (Problem 6 & 15).
    Includes image-aware scaling to preserve original branding ratios (Problem 9).
    """
    w = current_size.get("w", 140.0)
    h = current_size.get("h", 70.0)
    
    # Check if this node renders as an image (Problem 9)
    try:
        confidence = float(node.get("confidence", 0.0))
    except (ValueError, TypeError):
        confidence = 0.0
    use_image = confidence > 0.8 and visual_style != "minimal"
    
    if use_image:
        # Scale both dimensions to preserve aspect ratio
        scale_factor = 1.1 + (0.1 * attempt)
        return {"w": w * scale_factor, "h": h * scale_factor}
        
    shape = node.get("shape_hint", "").lower()
    topo = str(topology).lower().strip()
    
    # Square scaling (CNN/icon nodes)
    if shape in ("circle", "ellipse", "square") or "cnn" in topo:
        new_w = w + 20.0 * attempt
        new_h = new_w
    # Tall scaling (Transformer blocks)
    elif "transformer" in topo or shape == "tall":
        new_w = w + 20.0 * attempt
        new_h = new_w * 1.5
    # Wide/standard scaling (microservices/cloud blocks)
    else:
        new_w = w + 30.0 * attempt
        new_h = h + 10.0 * attempt
        
    return {"w": new_w, "h": new_h}

def generate_architecture_v4(
    architecture_type: str,
    visual_style: str,
    topic: str,
    slide_title: str = "",
    slide_content: str = "",
    feedback: str = ""
) -> str:
    """
    Main orchestration function for the semantic-driven architecture_v4 subsystem.
    visual_style is explicitly passed instead of relying on global state.
    """
    print(f"[ARCHITECTURE_V4] Starting semantic-driven diagram generation")
    print(f"[ARCHITECTURE_V4] Topology={architecture_type}")
    print(f"[ARCHITECTURE_V4] Visual Style={visual_style}")
    print(f"[ARCHITECTURE_V4] Topic='{topic}'")
    
    active_style = visual_style
    
    # 1. Fetch / Extract system components dynamically
    print(f"[ARCHITECTURE_V4] Stage 1: Extract components - Topology={architecture_type}, Visual Style={visual_style}")
    comp_cache_key = (topic, slide_title, slide_content, architecture_type, visual_style)
    components = None if feedback else _COMPONENTS_CACHE.get(comp_cache_key)
    if not components:
        components = extract_components(
            topic,
            slide_title,
            slide_content,
            topology=architecture_type,
            visual_style=visual_style,
            feedback=feedback
        )
        if components:
            _COMPONENTS_CACHE.set(comp_cache_key, components)
            
    if not components:
        print("[ARCHITECTURE_V4] No components extracted. Aborting.")
        return ""
        
    # 2. Fetch / Infer semantic relationships dynamically
    print(f"[ARCHITECTURE_V4] Stage 2: Build relationships - Topology={architecture_type}, Visual Style={visual_style}")
    rel_cache_key = (topic, architecture_type, visual_style, get_sha256_hash(json.dumps(components, sort_keys=True)))
    relationships = None if feedback else _RELATIONSHIPS_CACHE.get(rel_cache_key)
    if not relationships:
        relationships = build_relationships(components, topic, topology=architecture_type, visual_style=visual_style)
        if relationships:
            _RELATIONSHIPS_CACHE.set(rel_cache_key, relationships)
            
    # 3. Dynamic Container Layering (Problem 1 & 13)
    print(f"[ARCHITECTURE_V4] Stage 3: Build semantic containers - Topology={architecture_type}, Visual Style={visual_style}")
    containers, mapped_nodes = build_semantic_containers(components, architecture_type, visual_style=visual_style)
    
    # Build nodes list and preserve all metadata fields (Problem 3 & 8 & 9)
    nodes = []
    for mn in mapped_nodes:
        name = mn["name"]
        nid = clean_node_id(name)
        kind = mn["kind"]
        tier = mn["tier"].lower().strip()
        
        # Get defaults from style_engine (Problem 7)
        default_w, default_h = style_engine.get_geometry(
            style_name=visual_style,
            topology=architecture_type,
            label=name,
            kind=kind
        )
        
        node_obj = {
            "id": nid,
            "label": name,
            "type": kind,
            "shape_hint": mn.get("shape_hint", kind),
            "tier": tier,
            "parent": mn["parent"],
            "topic": topic,
            "w": default_w,
            "h": default_h
        }
        
        # Copy extensive layout and semantics metadata (Problem 7 is_hub/hub_score copied)
        for field in (
            "flow_order", "phase", "stage", "section", "rank_group", "lane",
            "swimlane", "cluster_id", "importance", "namespace", "zone",
            "tier", "group", "depends_on", "confidence", "shape_hint",
            "category", "semantic_type", "hub_score", "is_hub", "kind"
        ):
            if field in mn:
                node_obj[field] = mn[field]
                
        # Support notes, captions, badges, annotations (Problem 10)
        kind_lower = str(mn.get("type", mn.get("kind", "service"))).lower()
        if kind_lower in ("note", "caption", "badge", "annotation"):
            node_obj["type"] = kind_lower
            
        nodes.append(node_obj)
        
    # Re-map relationship source/target names to node IDs using fuzzy resolver (Problem 4 / 2)
    edges = []
    node_name_to_id = {n["label"].lower().strip(): n["id"] for n in nodes}
    
    for r in relationships:
        src_name = r["source"]
        tgt_name = r["target"]
        
        src_id = resolve_node_name(src_name, node_name_to_id)
        tgt_id = resolve_node_name(tgt_name, node_name_to_id)
        
        if src_id and tgt_id:
            edge_obj = {
                "source": src_id,
                "target": tgt_id,
                "label": r.get("label", "")
            }
            # Copy all edge relationship metadata (Problem 5 & 3)
            for key in (
                "importance", "same_rank", "cross_cluster", "back_edge", 
                "local_edge", "long_edge", "cluster_edge", "feedback",
                "critical", "category", "type", "phase", "stage", "section",
                "lane", "cluster_id", "weight", "confidence", "edge_confidence", "relationship_confidence"
            ):
                if key in r:
                    edge_obj[key] = r[key]
            
            # Ensure normalized edge confidence is set
            edge_obj["confidence"] = r.get("confidence", r.get("edge_confidence", r.get("relationship_confidence", 1.0)))
            edges.append(edge_obj)
            
    # Assemble raw graph structure (Problem 4 separate collections)
    graph = {
        "containers": containers,
        "nodes": nodes,
        "edges": edges,
        "notes": [n for n in nodes if n.get("type") == "note"],
        "captions": [n for n in nodes if n.get("type") == "caption"],
        "badges": [n for n in nodes if n.get("type") == "badge"],
        "annotations": [n for n in nodes if n.get("type") == "annotation"],
        "decorations": [n for n in nodes if n.get("type") == "decoration"],
        "layout_overrides": {},
        "metrics": {}
    }
    
    # Node size overrides dictionary for self-correction feedback loop
    node_size_overrides = {}
    
    max_attempts = 4
    # 5. Graphviz Layout & Validation Loop with Spacing Retries (Problem 12 & 15)
    for attempt in range(1, max_attempts + 1):
        print(f"[ARCHITECTURE_V4] Layout rendering attempt {attempt}/{max_attempts} - Topology={architecture_type}, Visual Style={visual_style}")

        # Compute layout via Graphviz (Layer 7)
        # Check cache first for layout coords (Problem 6 & 10 hash keys with visual_style)
        graph_str = json.dumps(graph, sort_keys=True)
        overrides_str = json.dumps(node_size_overrides, sort_keys=True)
        layout_cache_key = f"{architecture_type}_{visual_style}_{get_sha256_hash(graph_str)}_{get_sha256_hash(overrides_str)}"
        
        cached_graph = None if feedback else _LAYOUTS_CACHE.get(layout_cache_key)
        if cached_graph:
            graph = cached_graph
        else:
            try:
                graph = layout_graph(graph, architecture_type, node_size_overrides, visual_style=visual_style)
                _LAYOUTS_CACHE.set(layout_cache_key, graph)
            except Exception as layout_err:
                print(f"[ARCHITECTURE_V4] Graphviz layout call failed: {layout_err}")
                raise layout_err
                
        # Aspect Ratio Optimization Post-Layout Check (Problem 11 & Problem 1 update)
        # Re-compute aspect ratio after every retry and clear previous invisible edges first
        ar = get_layout_aspect_ratio(graph)
        print(f"[ARCHITECTURE_V4] Layout aspect ratio is {ar:.3f} (target {style_engine.TARGET_RATIO})")
        if ar < style_engine.MIN_RATIO or ar > style_engine.MAX_RATIO:
            print("[ARCHITECTURE_V4] Aspect ratio out of bounds. Applying optimization grid edges...")
            # Remove previous invis edges to avoid duplicates
            graph["edges"] = [e for e in graph.get("edges", []) if e.get("style") != "invis"]
            graph = optimize_aspect_ratio(graph, visual_style=visual_style)
            # Re-run layout with the new invisible edges
            try:
                graph = layout_graph(graph, architecture_type, node_size_overrides, visual_style=visual_style)
            except Exception as layout_err:
                print(f"[ARCHITECTURE_V4] Re-layout after aspect ratio optimization failed: {layout_err}")
                
        # Compute and store quality metrics (Problem 8)
        graph["metrics"] = compute_layout_metrics(graph)
        print(f"[ARCHITECTURE_V4] Layout metrics: {graph['metrics']}")
        
        # Validate layout using topology-specific validation rules (Problem 12)
        report = validate_topology_layout(graph, architecture_type)
        print(f"[ARCHITECTURE_V4] Validation report (attempt {attempt}): is_valid={report['is_valid']}, clipped={report['clipped_nodes']}")
        
        if not report["is_valid"] or report["clipped_nodes"]:
            if attempt < max_attempts:
                # Retry Spacing Scaling (Problem 15)
                overrides = graph.setdefault("layout_overrides", {})
                if any("Node overlap" in err for err in report.get("errors", [])):
                    overrides["nodesep"] = overrides.get("nodesep", 0.3) + 0.1
                    print(f"[ARCHITECTURE_V4] Overlaps detected. Increasing nodesep override to {overrides['nodesep']:.2f}")
                if any("Container overlap" in err for err in report.get("errors", [])):
                    overrides["ranksep"] = overrides.get("ranksep", 0.5) + 0.15
                    print(f"[ARCHITECTURE_V4] Container overlaps detected. Increasing ranksep override to {overrides['ranksep']:.2f}")
                    
                # Intelligent size adaptation for text clipping (Problem 6 & 15 & 5 & 9)
                if report["clipped_nodes"]:
                    print(f"[ARCHITECTURE_V4] Feedback loop: text clipping detected on {report['clipped_nodes']}. Adapting node sizes & style overrides...")
                    for nid in report["clipped_nodes"]:
                        node_obj = next((n for n in nodes if n["id"] == nid), None)
                        if node_obj:
                            current_w = node_size_overrides.get(nid, {}).get("w", node_obj["w"])
                            current_h = node_size_overrides.get(nid, {}).get("h", node_obj["h"])
                            
                            # Adapt size intelligently based on topology, shape hint, and image-awareness (Problem 9)
                            node_size_overrides[nid] = adapt_node_size(
                                node_obj,
                                {"w": current_w, "h": current_h},
                                architecture_type,
                                attempt,
                                visual_style=visual_style
                            )
                            
                            # Adapt font size (Problem 5: shrink slightly on clipping)
                            font_size_override = node_obj.get("font_size_override", 14)
                            node_obj["font_size_override"] = max(9, font_size_override - 1)
                            
                            # Adapt image scale
                            image_scale_override = node_obj.get("image_scale_override", 1.0)
                            node_obj["image_scale_override"] = max(0.6, image_scale_override - 0.1)
                            
                            # Adapt spacings
                            node_obj["spacing_top_override"] = max(2, node_obj.get("spacing_top_override", 6) - 1)
                            node_obj["spacing_bottom_override"] = max(2, node_obj.get("spacing_bottom_override", 6) - 1)
                continue
            else:
                if not report["is_valid"]:
                    print(f"[ARCHITECTURE_V4] Layout validation issues found: {report['errors']}")
                break
        else:
            break
            
    # 6. Generate final Draw.io XML (Layer 6)
    print(f"[ARCHITECTURE_V4] Stage 6: Build Draw.io XML - Topology={architecture_type}, Visual Style={visual_style}")
    xml = build_drawio_xml(graph, visual_style=visual_style)
    print(f"[ARCHITECTURE_V4] Successfully generated Draw.io XML ({len(xml)} characters)")
    return xml
