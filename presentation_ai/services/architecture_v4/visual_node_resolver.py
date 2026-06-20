#!/usr/bin/env python3
"""
Visual Node Resolver for Architecture V4
=======================================
Implements the Layer 5 node resolving logic and Layer 8 theme mapping.
Implements the exact priority hierarchy:
1. Lobe-icons / Simple-icons Supplement / Local Cache (via get_ai_icon)
2. Theme fallback brand
3. ShapeSearchEngine (Draw.io native cloud library search)
4. Database cylinder fallback
5. Rounded rectangle fallback
"""

import re
from typing import Dict, Any, Optional
from services.architecture_v4.shapesearch_engine import search_shapes
from services.architecture_v4.ai_icon_engine import get_ai_icon
import services.architecture_v4.style_engine_v4 as style_engine

# Theme mappings for shapesearch queries
THEME_MAPPINGS = {
    "aws": {
        "database": "RDS",
        "compute": "Lambda",
        "service": "Lambda",
        "gateway": "API Gateway",
        "storage": "S3",
        "security": "Cognito",
        "queue": "SQS"
    },
    "azure": {
        "database": "SQL Database",
        "compute": "Functions",
        "service": "Functions",
        "storage": "Blob Storage",
        "gateway": "API Management",
        "queue": "Service Bus"
    },
    "gcp": {
        "database": "Cloud SQL",
        "compute": "Cloud Functions",
        "service": "Cloud Functions",
        "storage": "Cloud Storage",
        "gateway": "API Gateway",
        "queue": "PubSub"
    },
    "kubernetes": {
        "network": "Ingress",
        "gateway": "Ingress",
        "compute": "Pod",
        "service": "Pod",
        "queue": "Kafka",
        "database": "PostgreSQL",
        "storage": "Persistent Volume"
    }
}

def clean_brand_query(name: str) -> str:
    """Extracts a clean brand query by stripping common suffixes/prefixes."""
    n = name.lower()
    for word in ["db", "database", "service", "app", "ui", "client", "controller", "instance", "broker", "queue", "topic", "cluster"]:
        n = re.sub(rf'\b{word}\b', '', n)
    return n.strip()

def get_node_category(label: str, node_type: str) -> str:
    """Classifies a node into a semantic category for styling/palette mapping."""
    label_lower = label.lower()
    type_lower = node_type.lower() if node_type else ""
    
    # 1. AI/ML specific categories
    if any(x in label_lower or x in type_lower for x in ("llm", "large language", "gpt", "gemini", "claude", "llama", "openai")):
        return "llm"
    if any(x in label_lower or x in type_lower for x in ("vector db", "vector database", "pinecone", "chroma", "weaviate", "milvus")):
        return "vector_db"
    if any(x in label_lower or x in type_lower for x in ("embedding", "embedder")):
        return "embedding"
    if any(x in label_lower or x in type_lower for x in ("retriever", "retrieval")):
        return "retriever"
    if any(x in label_lower or x in type_lower for x in ("agent", "bot", "assistant")):
        return "agent"
    if any(x in label_lower or x in type_lower for x in ("orchestrator", "langchain", "llamaindex", "flow")):
        return "orchestrator"
    
    # 2. Database & Cache
    if any(x in label_lower or x in type_lower for x in ("cache", "redis", "memcached")):
        return "cache"
    if any(x in label_lower or x in type_lower for x in ("postgres", "sql", "oracle", "mysql", "database", "db")):
        return "database"
    if any(x in label_lower or x in type_lower for x in ("s3", "bucket", "storage", "blob", "volume", "dataset")):
        return "storage"
        
    # 3. Queue & Event-driven
    if any(x in label_lower or x in type_lower for x in ("kafka", "rabbitmq", "pubsub", "broker", "queue")):
        return "message_broker"
    if any(x in label_lower or x in type_lower for x in ("stream", "kinesis", "event hub")):
        return "stream"
    if "event" in label_lower or "event" in type_lower:
        return "event"
        
    # 4. Networking & Gateways
    if any(x in label_lower or x in type_lower for x in ("gateway", "loadbalancer", "load-balancer", "lb", "proxy", "ingress", "route", "dns")):
        return "gateway"
    if "api" in label_lower or "api" in type_lower:
        return "api"
        
    # 5. Client & Frontend
    if any(x in label_lower or x in type_lower for x in ("client", "user", "browser", "app", "mobile", "frontend", "ui", "dashboard")):
        return "frontend"
        
    # 6. Monitoring & Observability
    if any(x in label_lower or x in type_lower for x in ("prometheus", "grafana", "observability", "telemetry", "tracing")):
        return "observability"
    if "log" in label_lower or "log" in type_lower:
        return "logging"
    if "monitor" in label_lower or "analytics" in label_lower:
        return "monitoring"
        
    # 7. Compute & Containers
    if any(x in label_lower or x in type_lower for x in ("kubernetes", "k8s", "container", "pod", "docker")):
        return "container"
    if "worker" in label_lower or "worker" in type_lower:
        return "worker"
    if "backend" in label_lower or "service" in label_lower or "backend" in type_lower or "compute" in type_lower:
        return "backend"
        
    # 8. Neural Network Layers
    if "encoder" in label_lower or "encoder" in type_lower:
        return "encoder"
    if "decoder" in label_lower or "decoder" in type_lower:
        return "decoder"
    if "conv" in label_lower or "convolution" in label_lower:
        return "conv"
    if "pool" in label_lower or "pooling" in label_lower:
        return "pool"
    if "dense" in label_lower or "dense" in type_lower:
        return "dense"
    if "model" in label_lower or "model" in type_lower:
        return "model"
        
    return "compute"

def resolve_ai_icon_helper(label: str, kind: str, shape_hint: str, topic: str, visual_style: str) -> Optional[Dict[str, Any]]:
    """Helper to resolve brand logos from Lobe Icons, Simple Icons, and Local Cache."""
    icon_res = None

    # 1.1 Complete Label
    if label and len(label.strip()) > 2:
        icon_res = get_ai_icon(label, kind=kind, visual_style=visual_style, topic=topic)

    # 1.2 Cleaned Label
    if not icon_res:
        cleaned_label = clean_brand_query(label)
        if cleaned_label and cleaned_label.strip() != label.strip() and len(cleaned_label.strip()) > 2:
            icon_res = get_ai_icon(cleaned_label, kind=kind, visual_style=visual_style, topic=topic)

    # 1.3 Shape Hint
    if not icon_res and shape_hint and len(shape_hint.strip()) > 2:
        icon_res = get_ai_icon(shape_hint, kind=kind, visual_style=visual_style, topic=topic)

    # 1.4 Semantic Aliases (checking if any alias key is a phrase inside the label/cleaned label)
    if not icon_res:
        from services.architecture_v4.ai_icon_engine import SEMANTIC_ALIASES
        # Match longest key first
        sorted_keys = sorted(SEMANTIC_ALIASES.keys(), key=len, reverse=True)
        for key in sorted_keys:
            # Check using word boundary regex to avoid partial word matches
            pattern = rf"\b{re.escape(key)}\b"
            if re.search(pattern, label.lower()) or re.search(pattern, clean_brand_query(label).lower()):
                alias_val = SEMANTIC_ALIASES[key]
                icon_res = get_ai_icon(alias_val, kind=kind, visual_style=visual_style, topic=topic)
                if icon_res:
                    break

    # 1.5 Individual tokenized words
    if not icon_res:
        cleaned = clean_brand_query(label)
        words = [w.strip() for w in re.split(r'[^a-zA-Z0-9]', cleaned) if w]
        for w in words:
            if len(w) > 2:
                icon_res = get_ai_icon(w, kind=kind, visual_style=visual_style, topic=topic)
                if icon_res:
                    break

    # 1.6 Kind/Type query fallback
    if not icon_res and kind and len(kind.strip()) > 2:
        icon_res = get_ai_icon(kind, kind=kind, visual_style=visual_style, topic=topic)

    # ── Theme Fallback ──
    if not icon_res and visual_style:
        from services.architecture_v4.ai_icon_engine import get_theme_brand_fallback
        fallback_brand = get_theme_brand_fallback(kind or label, visual_style)
        if fallback_brand:
            icon_res = get_ai_icon(fallback_brand, kind=kind, visual_style=visual_style, topic=topic)

    return icon_res

def resolve_node_visuals(node: Dict[str, Any], visual_style: str = None) -> Dict[str, Any]:
    """
    Confidence-Based Priority Pipeline:
    1. ShapeSearchEngine: Search Draw.io shapes using query and active theme.
       - If confidence > 0.75: Use Draw.io shape.
       - If confidence between 0.5 and 0.75: Fallback to get_ai_icon() (Lobe/Simple icons).
       - If confidence < 0.5: Skip get_ai_icon and fallback to database cylinder / generic shape.
    visual_style is explicitly passed instead of relying on global state.
    """
    label = node.get("label", node.get("id", ""))
    kind = node.get("type", node.get("kind", "service"))
    shape_hint = node.get("shape_hint", "")
    topic = node.get("topic", "")

    active_style = visual_style if visual_style else style_engine.get_current_style()
    category = get_node_category(label, kind)
    
    # 1. Formulate Queries for Shape Search
    queries = []
    if active_style in ["aws", "azure", "gcp", "kubernetes"]:
        theme_prefix = "aws" if active_style == "aws" else active_style
        mapped_term = THEME_MAPPINGS.get(active_style, {}).get(kind)
        
        if mapped_term:
            queries.append(f"{theme_prefix} {mapped_term}")
        if shape_hint:
            queries.append(f"{theme_prefix} {shape_hint}")
        queries.append(f"{theme_prefix} {label}")
    else:
        label_lower = label.lower()
        if "aws" in label_lower or "amazon" in label_lower:
            queries.append(label)
        elif "k8s" in label_lower or "kubernetes" in label_lower:
            queries.append(label)
        elif "azure" in label_lower:
            queries.append(label)
        elif "gcp" in label_lower or "google" in label_lower:
            queries.append(label)
            
        if shape_hint:
            queries.append(shape_hint)
        queries.append(label)
        
    # 2. Run Shape Search to Find Best Candidate
    best_shape = None
    for q in queries:
        search_res = search_shapes(q, limit=1, theme=active_style)
        if search_res:
            best_shape = search_res[0]
            break
            
    node_confidence = node.get("confidence")
    if node_confidence is not None:
        try:
            confidence = float(node_confidence)
        except (ValueError, TypeError):
            confidence = 0.0
    else:
        confidence = best_shape["confidence"] if best_shape else 0.0
    
    # 3. Shape Confidence Pipeline Routing (Problem 19)
    
    # A. Confidence > 0.8: Image Vertex (Brand Logo)
    try:
        confidence_float = float(confidence)
    except (ValueError, TypeError):
        confidence_float = 0.0
    if confidence_float > 0.8:
        icon_res = resolve_ai_icon_helper(label, kind, shape_hint, topic, active_style)
        if icon_res:
            try:
                icon_w = float(icon_res["w"])
                icon_h = float(icon_res["h"])
            except (ValueError, TypeError):
                icon_w = 120.0
                icon_h = 80.0
            return {
                "base_style": icon_res["style"],
                "w": icon_w,
                "h": icon_h,
                "use_image": True,
                "category": category,
                "aspect_ratio": icon_w / icon_h if icon_h > 0 else 1.0,
                "confidence": confidence
            }
        # Fallback to Native Shape if AI icon resolution fails
        if best_shape:
            confidence = 0.7  # Demote to native shape range
            
    # B. Confidence 0.5 - 0.8: Native Draw.io Shape
    if best_shape and 0.5 <= confidence_float <= 0.8:
        try:
            sw = float(best_shape.get("w", 120))
            sh = float(best_shape.get("h", 60))
        except (ValueError, TypeError):
            sw = 120.0
            sh = 60.0
        
        style_sizes = {
            "drawio_vivid": 120,
            "ai_dark_neon": 96,
            "aws": 80,
            "kubernetes": 80
        }
        try:
            max_dim = float(style_sizes.get(active_style, 100.0))
        except (ValueError, TypeError):
            max_dim = 100.0
        scale = max_dim / max(sw, sh)
        return {
            "base_style": best_shape["style"],
            "w": sw * scale,
            "h": sh * scale,
            "use_image": False,
            "category": category,
            "aspect_ratio": sw / sh if sh > 0 else 1.0,
            "confidence": confidence
        }
        
    # C. Confidence 0.2 - 0.5: Cylinder Shape
    try:
        confidence_float = float(confidence)
    except (ValueError, TypeError):
        confidence_float = 0.0
    if 0.2 <= confidence_float < 0.5 or (category == "database" or kind == "database"):
        style_sizes = {
            "drawio_vivid": 120,
            "ai_dark_neon": 96,
            "aws": 80,
            "kubernetes": 80
        }
        try:
            max_dim = float(style_sizes.get(active_style, 100.0))
        except (ValueError, TypeError):
            max_dim = 100.0
        # Keep Cylinder dimensions: width ~0.9 * max_dim, height ~1.1 * max_dim
        cw = max_dim * 0.9
        ch = max_dim * 1.1
        return {
            "base_style": "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;",
            "w": cw,
            "h": ch,
            "use_image": False,
            "category": category,
            "aspect_ratio": cw / ch,
            "confidence": confidence
        }
        
    # D. Confidence < 0.2: Rounded Rectangle (Generic)
    style_sizes = {
        "drawio_vivid": 120,
        "ai_dark_neon": 96,
        "aws": 80,
        "kubernetes": 80
    }
    try:
        max_dim = float(style_sizes.get(active_style, 100.0))
    except (ValueError, TypeError):
        max_dim = 100.0
    rw = max_dim * 1.8
    rh = max_dim * 0.9
    return {
        "base_style": "rounded=1;whiteSpace=wrap;html=1;",
        "w": rw,
        "h": rh,
        "use_image": False,
        "category": category,
        "aspect_ratio": rw / rh,
        "confidence": confidence
    }

if __name__ == "__main__":
    style_engine.set_current_style("aws")
    node_test = {"label": "Process Engine", "type": "compute"}
    print(f"AWS: {resolve_node_visuals(node_test)}")
