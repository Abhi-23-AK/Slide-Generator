#!/usr/bin/env python3
"""
Semantic Container Builder for Architecture V4
===============================================
Generates container hierarchies and parent assignments dynamically from node metadata
and topologies, removing hardcoded universal assumptions.
"""

import re
from typing import List, Dict, Any, Tuple

# Normalize topology name helper
def normalize_topology_name(topology: str) -> str:
    t = str(topology).lower().strip()
    if t in ("rag", "rag_pipeline"):
        return "rag_pipeline"
    if t in ("ai", "ai_pipeline"):
        return "ai_pipeline"
    if t in ("transformer", "transformer_pipeline"):
        return "transformer"
    if t in ("cnn", "cnn_pipeline"):
        return "cnn"
    if t in ("classic", "layered", "uml", "flowchart", "star", "ring", "hub_spoke", "none"):
        return "microservices"
    return t

def clean_node_id(name: str) -> str:
    """Generates a safe alphanumeric XML ID from a label."""
    nid = name.replace(" ", "_").replace("-", "_").lower()
    nid = re.sub(r'[^a-zA-Z0-9_]', '', nid)
    return nid

# Standard containers configuration per topology
TOPOLOGY_CONTAINERS = {
    "microservices": [
        {"id": "clients", "label": "Clients & External Interfaces"},
        {"id": "gateways", "label": "API Gateways & Ingress Layer"},
        {"id": "services", "label": "Microservices Layer"},
        {"id": "databases", "label": "Data Storage & Caching"}
    ],
    "cloud": [
        {"id": "public", "label": "Public Subnet (DMZ)"},
        {"id": "private", "label": "Private Application Subnet"},
        {"id": "database", "label": "Database & Storage Subnet"}
    ],
    "kubernetes": [
        {"id": "ingress", "label": "Ingress Controller & Load Balancer"},
        {"id": "pods", "label": "K8s Pods & Core Services"},
        {"id": "storage", "label": "Persistent Volume Claims (PVC)"},
        {"id": "namespaces", "label": "K8s Namespaces"}
    ],
    "event_driven": [
        {"id": "producers", "label": "Event Producers & Clients"},
        {"id": "broker", "label": "Message Broker & Event Bus"},
        {"id": "consumers", "label": "Event Consumers & Workers"},
        {"id": "persistence", "label": "Persistence & Audit Logs"}
    ],
    "rag_pipeline": [
        {"id": "loader", "label": "Data Loading & Ingestion"},
        {"id": "chunker", "label": "Text Chunking & Preprocessing"},
        {"id": "embedding", "label": "Embedding Generator"},
        {"id": "vectordb", "label": "Vector Database"},
        {"id": "retriever", "label": "Information Retrieval Context"},
        {"id": "llm", "label": "LLM & Reasoning Engine"},
        {"id": "output", "label": "Output UI & Presentation"}
    ],
    "ai_pipeline": [
        {"id": "loader", "label": "Data Ingest"},
        {"id": "chunker", "label": "Preprocessing"},
        {"id": "embedding", "label": "Embeddings"},
        {"id": "vectordb", "label": "Vector Index"},
        {"id": "retriever", "label": "Retriever"},
        {"id": "llm", "label": "LLM Reasoning"},
        {"id": "output", "label": "Output Processing"}
    ],
    "transformer": [
        {"id": "embedding", "label": "Input Embedding Layer"},
        {"id": "encoder", "label": "Transformer Encoder Block"},
        {"id": "attention", "label": "Multi-Head Self-Attention"},
        {"id": "decoder", "label": "Transformer Decoder Block"},
        {"id": "output", "label": "Linear Projection & Softmax"}
    ],
    "cnn": [
        {"id": "input", "label": "Input Image Layer"},
        {"id": "conv", "label": "Convolutional Feature Extraction"},
        {"id": "pool", "label": "Pooling & Downsampling"},
        {"id": "dense", "label": "Fully Connected Layers"},
        {"id": "output", "label": "Class Output & Softmax"}
    ]
}

def build_semantic_containers(
    components: List[Dict[str, Any]],
    topology: str,
    visual_style: str = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Dynamically generates the appropriate containers list and assigns parent container
    relations to each component node based on metadata, flow attributes, or topology defaults.
    visual_style is explicitly passed instead of relying on global state.
    """
    containers = []
    used_container_ids = set()
    
    topo = normalize_topology_name(topology)
    std_containers = TOPOLOGY_CONTAINERS.get(topo, TOPOLOGY_CONTAINERS["microservices"])
    std_container_map = {c["id"]: c for c in std_containers}
    
    nodes = []
    
    for c in components:
        # Clone component dict to avoid mutations upstream
        node_obj = dict(c)
        parent = None
        
        # Priority 1: cluster_id
        cluster_id = node_obj.get("cluster_id")
        if cluster_id:
            parent = f"cluster_{clean_node_id(cluster_id)}"
            if parent not in used_container_ids:
                containers.append({
                    "id": parent,
                    "label": f"{cluster_id} Group",
                    "parent": None
                })
                used_container_ids.add(parent)
                
        # Priority 2: namespace
        if not parent:
            namespace = node_obj.get("namespace")
            if namespace:
                parent = f"namespace_{clean_node_id(namespace)}"
                if parent not in used_container_ids:
                    containers.append({
                        "id": parent,
                        "label": f"Namespace: {namespace}",
                        "parent": None
                    })
                    used_container_ids.add(parent)
                    
        # Priority 3: zone
        if not parent:
            zone = node_obj.get("zone")
            if zone:
                parent = f"zone_{clean_node_id(zone)}"
                if parent not in used_container_ids:
                    containers.append({
                        "id": parent,
                        "label": f"Zone: {zone}",
                        "parent": None
                    })
                    used_container_ids.add(parent)

        # Priority 4: swimlane / lane
        if not parent:
            lane = node_obj.get("lane") or node_obj.get("swimlane")
            if lane and lane != "default_lane" and lane != "default_swimlane":
                parent = f"lane_{clean_node_id(lane)}"
                if parent not in used_container_ids:
                    containers.append({
                        "id": parent,
                        "label": f"{lane} Lane",
                        "parent": None
                    })
                    used_container_ids.add(parent)

        # Priority 5: stage / phase / section
        if not parent:
            section = node_obj.get("section") or node_obj.get("phase") or node_obj.get("stage")
            if section and section not in ("default_section", "default_phase", "default_stage"):
                parent = f"section_{clean_node_id(section)}"
                if parent not in used_container_ids:
                    containers.append({
                        "id": parent,
                        "label": f"{section.replace('_', ' ').title()}",
                        "parent": None
                    })
                    used_container_ids.add(parent)
                    
        # Priority 6: Topology-based fallback
        if not parent:
            from services.architecture_v4.graphviz_layout_v4 import get_topology_band
            band = get_topology_band(node_obj, topology)
            if band:
                parent = band
                if parent not in used_container_ids:
                    label = std_container_map.get(parent, {}).get("label", parent.replace("_", " ").title())
                    containers.append({
                        "id": parent,
                        "label": label,
                        "parent": None
                    })
                    used_container_ids.add(parent)
            else:
                # Absolute fallback
                parent = "services"
                if parent not in used_container_ids:
                    label = std_container_map.get(parent, {}).get("label", "Application Services")
                    containers.append({
                        "id": parent,
                        "label": label,
                        "parent": None
                    })
                    used_container_ids.add(parent)
                    
        node_obj["parent"] = parent
        nodes.append(node_obj)
        
    return containers, nodes
