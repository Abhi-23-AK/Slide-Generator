#!/usr/bin/env python3
"""
Component Extractor for Architecture V4
=======================================
Extracts system components (nodes) dynamically from user topics/slide context.
Returns a normalized list of components: name, kind, shape_hint, tier, and layout metadata.
"""

import json
import re
import os
from typing import List, Dict, Any, Optional

try:
    from rapidfuzz import process, fuzz
    _HAS_RAPIDFUZZ = True
except ImportError:
    _HAS_RAPIDFUZZ = False

# Import clean_and_parse_json from relationship_builder
from services.architecture_v4.relationship_builder import clean_and_parse_json

# Centralized Semantic Registry of known technologies
SEMANTIC_REGISTRY = {
    "FRAMEWORKS": {
        "react": "react", "redux": "redux", "nextjs": "nextjs", "angular": "angular", 
        "vue": "vue", "fastapi": "fastapi", "django": "django", "flask": "flask", 
        "spring boot": "springboot", "springboot": "springboot", "spring": "springboot",
        "nodejs": "nodejs", "node.js": "nodejs", "node": "nodejs", "express": "express",
        "next.js": "nextjs", "angularjs": "angular"
    },
    "DATABASES": {
        "postgresql": "postgresql", "postgres": "postgresql", "mongodb": "mongodb", 
        "mongo": "mongodb", "mysql": "mysql", "redis": "redis", "cassandra": "cassandra", 
        "neo4j": "neo4j", "sqlite": "sqlite", "mariadb": "mariadb", "oracle": "oracle",
        "couchbase": "couchbase", "clickhouse": "clickhouse", "duckdb": "duckdb",
        "timescaledb": "timescaledb", "dynamodb": "dynamodb"
    },
    "VECTOR_DATABASES": {
        "pinecone": "pinecone", "milvus": "milvus", "qdrant": "qdrant", 
        "weaviate": "weaviate", "chroma": "chroma", "chromadb": "chroma"
    },
    "AI_MODELS": {
        "openai": "openai", "gpt": "openai", "gpt4": "openai", "gpt-4": "openai",
        "claude": "claude", "anthropic": "claude", "gemini": "gemini", 
        "deepseek": "deepseek", "llama": "llama", "mistral": "mistral", 
        "cohere": "cohere", "qwen": "qwen", "tensorflow": "tensorflow", 
        "pytorch": "pytorch", "onnx": "onnx", "scikit-learn": "scikit-learn", 
        "keras": "keras", "huggingface": "huggingface", "transformers": "transformers"
    },
    "QUEUES": {
        "kafka": "kafka", "rabbitmq": "rabbitmq", "sqs": "sqs", "sns": "sns", 
        "pubsub": "pubsub", "activemq": "activemq", "celery": "celery", "nats": "nats"
    },
    "OBSERVABILITY": {
        "prometheus": "prometheus", "grafana": "grafana", "elk": "elk", 
        "elasticsearch": "elasticsearch", "logstash": "logstash", "kibana": "kibana", 
        "fluentbit": "fluentbit", "fluentd": "fluentd", "datadog": "datadog", 
        "jaeger": "jaeger", "opentelemetry": "opentelemetry", "otel": "opentelemetry"
    },
    "SECURITY": {
        "keycloak": "keycloak", "oauth": "oauth", "jwt": "jwt", "cognito": "cognito", 
        "auth0": "auth0", "vault": "vault", "iam": "iam", "okta": "okta"
    },
    "CLOUD_SERVICES": {
        "aws": "aws", "lambda": "lambda", "s3": "s3", "rds": "rds", "ec2": "ec2", 
        "eks": "eks", "ecs": "ecs", "azure": "azure", "aks": "aks", "gcp": "gcp", 
        "bigquery": "bigquery", "vertex ai": "vertex_ai", "vertexai": "vertex_ai", 
        "cloud run": "cloud_run", "cloudrun": "cloud_run", "s3 bucket": "s3",
        "api gateway": "api_gateway", "apigateway": "api_gateway"
    },
    "DEVOPS": {
        "docker": "docker", "kubernetes": "kubernetes", "k8s": "kubernetes", 
        "pod": "pod", "deployment": "deployment", "ingress": "ingress", 
        "istio": "istio", "nginx": "nginx", "github": "github", "gitlab": "gitlab", 
        "jenkins": "jenkins", "argocd": "argocd", "terraform": "terraform", 
        "ansible": "ansible", "helm": "helm"
    },
    "BROWSER_EXTENSION": {
        "manifest v3": "manifest_v3", "manifestv3": "manifest_v3", 
        "service worker": "service_worker", "serviceworker": "service_worker", 
        "indexeddb": "indexeddb", "chrome extension": "chrome_extension", 
        "content script": "content_script", "popup": "popup", "background page": "background_page"
    }
}

# Centralized Synonym Registry to normalize query variations before entity extraction
SYNONYM_REGISTRY = {
    "postgres db": "postgresql",
    "postgresql db": "postgresql",
    "sql database": "postgresql",
    "relational database": "postgresql",
    "vector store": "pinecone",
    "vector database": "pinecone",
    "embedding db": "openai",
    "rag store": "pinecone",
    "chat model": "openai",
    "api server": "nodejs",
    "backend": "nodejs",
    "frontend": "react",
    "worker": "nodejs",
    "scheduler": "kubernetes",
    "orchestrator": "langchain",
    "agent": "langchain",
    "tool": "langchain",
    "memory": "redis",
    "planner": "langchain",
    "executor": "langchain",
    "controller": "kubernetes",
    "registry": "docker",
    "cache layer": "redis",
    "session store": "redis",
    "knowledge base": "pinecone"
}

# Centralized Flow Order Registry for various topologies
FLOW_ORDER_REGISTRY = {
    "cnn": ["input", "conv", "pool", "dense", "softmax", "output"],
    "transformer": ["input", "embed", "encoder", "attention", "decoder", "output"],
    "rag": ["client", "user", "loader", "parser", "chunker", "embed", "vector", "pinecone", "milvus", "qdrant", "retriev", "llm", "output", "ui"],
    "microservices": ["client", "ui", "frontend", "gateway", "api", "service", "backend", "worker", "queue", "cache", "database", "postgres", "mysql", "monitoring"],
    "event_driven": ["producer", "source", "publisher", "broker", "kafka", "rabbitmq", "pubsub", "queue", "consumer", "subscriber", "worker", "store", "database"],
    "star": ["hub", "center", "spoke", "node", "leaf"],
    "ring": ["node", "link", "station", "terminal"],
    "hub_spoke": ["hub", "center", "spoke", "node", "leaf"],
    "flowchart": ["start", "input", "process", "decision", "step", "output", "end"],
    "uml": ["actor", "interface", "controller", "entity", "class", "package", "database"]
}

# Dynamically construct TECHNOLOGY_SHAPE_HINTS from the registry
TECHNOLOGY_SHAPE_HINTS = {}
for cat, mapping in SEMANTIC_REGISTRY.items():
    for key, val in mapping.items():
        TECHNOLOGY_SHAPE_HINTS[key] = val

ALLOWED_KINDS = {
    "client", "gateway", "service", "cache", "database", "queue", "storage",
    "container", "vector_db", "llm", "monitoring", "logging", "analytics", "external",
    "compute", "security"
}

KIND_SYNONYMS = {
    "db": "database",
    "rds": "database",
    "sql": "database",
    "nosql": "database",
    "redis": "cache",
    "memcached": "cache",
    "broker": "queue",
    "message_broker": "queue",
    "topic": "queue",
    "load_balancer": "gateway",
    "proxy": "gateway",
    "ingress": "gateway",
    "router": "gateway",
    "vector": "vector_db",
    "vectordb": "vector_db",
    "model": "llm",
    "openai": "llm",
    "claude": "llm",
    "gemini": "llm",
    "prometheus": "monitoring",
    "grafana": "analytics",
    "elk": "logging",
    "fluentd": "logging",
    "fluentbit": "logging",
    "user": "client",
    "browser": "client"
}

# Capability-based domain descriptions (no hardcoded technology or component suffix examples to avoid LLM bias)
DOMAIN_GUIDELINES = {
    "AI": (
        "Focus on system capabilities, model execution workflows, analytic components, "
        "persistence/vector storage layers, framework integrations, and view interfaces."
    ),
    "Kubernetes": (
        "Focus on hosting structures, ingress gateways, routing rules, runner pools, "
        "storage attachments, configuration states, and telemetry layers."
    ),
    "Cloud": (
        "Focus on hosting locations, serverless compute scopes, persistence blocks, "
        "relational data backends, load distribution points, network zones, and security groups."
    ),
    "Browser Extensions": (
        "Focus on extension configurations, service runners, view controllers, content "
        "scripts, local cache storages, and external API integrations."
    ),
    "Event-driven": (
        "Focus on event production zones, event routing brokers, event consumption logic, "
        "stream processing pipelines, and message datastores."
    ),
    "CI/CD": (
        "Focus on version storage repositories, automation runners, artifact registries, "
        "operator instances, and deployment target clusters."
    ),
    "Insurance": (
        "Focus on customer portals, intake workflows, underwriting analytics, fraud analysis "
        "layers, database logs, and message dispatchers."
    ),
    "Web": (
        "Focus on client UI layouts, routing gateways, business logic runners, caches, and databases."
    ),
    "Generic": (
        "Focus on view layers, logic processors, messaging brokers, and database stores."
    )
}

def detect_domain(topic: str, slide_title: str, slide_content: str) -> str:
    """Detects the architecture domain of the topic/content using registry matching."""
    text = (topic + " " + slide_title + " " + slide_content).lower()
    
    scores = {
        "AI": 0,
        "Kubernetes": 0,
        "Cloud": 0,
        "Browser Extensions": 0,
        "Event-driven": 0,
        "CI/CD": 0,
        "Insurance": 0,
        "Web": 0
    }
    
    # AI scores
    for key in list(SEMANTIC_REGISTRY["VECTOR_DATABASES"].keys()) + list(SEMANTIC_REGISTRY["AI_MODELS"].keys()):
        if re.search(rf"\b{re.escape(key)}\b", text):
            scores["AI"] += 2
    if any(x in text for x in ["rag", "llm", "embedding", "retrieval", "vector store"]):
        scores["AI"] += 3
        
    # Kubernetes scores
    for key in ["kubernetes", "k8s", "pod", "deployment", "ingress", "istio", "helm", "service mesh"]:
        if re.search(rf"\b{re.escape(key)}\b", text):
            scores["Kubernetes"] += 2
            
    # Cloud scores
    for key in SEMANTIC_REGISTRY["CLOUD_SERVICES"].keys():
        if re.search(rf"\b{re.escape(key)}\b", text):
            scores["Cloud"] += 2
            
    # Browser Extensions scores
    for key in SEMANTIC_REGISTRY["BROWSER_EXTENSION"].keys():
        if re.search(rf"\b{re.escape(key)}\b", text):
            scores["Browser Extensions"] += 3
            
    # Event-driven scores
    for key in SEMANTIC_REGISTRY["QUEUES"].keys():
        if re.search(rf"\b{re.escape(key)}\b", text):
            scores["Event-driven"] += 3
            
    # CI/CD scores
    for key in ["ci/cd", "pipeline", "jenkins", "gitlab", "github actions", "argocd", "deploy"]:
        if re.search(rf"\b{re.escape(key)}\b", text):
            scores["CI/CD"] += 3
            
    # Insurance scores
    for key in ["insurance", "claims", "underwriting", "fraud detection", "policy", "premium"]:
        if re.search(rf"\b{re.escape(key)}\b", text):
            scores["Insurance"] += 4
            
    # Web scores
    for key in SEMANTIC_REGISTRY["FRAMEWORKS"].keys():
        if re.search(rf"\b{re.escape(key)}\b", text):
            scores["Web"] += 2
            
    max_domain, max_score = max(scores.items(), key=lambda x: x[1])
    if max_score > 0:
        return max_domain
    return "Generic"

def extract_entities(text: str) -> List[Dict[str, Any]]:
    """Discovers concrete entities from the semantic registry present in the text."""
    text_lower = text.lower()
    entities = []
    matched_ranges = []
    
    # Sort registry keys by length descending to match longest compound phrases first
    all_keys = []
    for category, mapping in SEMANTIC_REGISTRY.items():
        for key, slug in mapping.items():
            all_keys.append((key, slug, category))
            
    all_keys.sort(key=lambda x: len(x[0]), reverse=True)
    
    for key, slug, category in all_keys:
        pattern = rf"\b{re.escape(key)}\b"
        for match in re.finditer(pattern, text_lower):
            start, end = match.start(), match.end()
            overlap = False
            for s, e in matched_ranges:
                if (start >= s and start < e) or (end > s and end <= e):
                    overlap = True
                    break
            if not overlap:
                matched_ranges.append((start, end))
                kind_map = {
                    "FRAMEWORKS": "service",
                    "DATABASES": "database",
                    "VECTOR_DATABASES": "vector_db",
                    "AI_MODELS": "llm",
                    "QUEUES": "queue",
                    "OBSERVABILITY": "monitoring",
                    "SECURITY": "security",
                    "CLOUD_SERVICES": "compute",
                    "DEVOPS": "container",
                    "BROWSER_EXTENSION": "service"
                }
                
                tier = "backend"
                if category == "FRAMEWORKS" and slug in ["react", "angular", "vue", "nextjs"]:
                    tier = "frontend"
                elif category in ["DATABASES", "VECTOR_DATABASES", "QUEUES"]:
                    tier = "data"
                elif category in ["OBSERVABILITY", "DEVOPS"]:
                    tier = "infra"
                    
                name = key.title()
                if slug in ["aws", "gcp", "rds", "s3", "eks", "aks", "jwt", "elk", "api_gateway"]:
                    name = slug.upper()
                elif slug == "postgresql":
                    name = "PostgreSQL"
                elif slug == "mongodb":
                    name = "MongoDB"
                elif slug == "fastapi":
                    name = "FastAPI"
                elif slug == "nodejs":
                    name = "NodeJS"
                elif slug == "nextjs":
                    name = "NextJS"
                    
                entities.append({
                    "name": name,
                    "kind": kind_map.get(category, "service"),
                    "shape_hint": slug,
                    "tier": tier,
                    "importance": "high"
                })
                
    return entities

def extract_nouns_and_phrases(topic: str, slide_title: str, slide_content: str) -> List[str]:
    """Extracts compound noun phrases dynamically from lowercase text using non-stop-word sequences."""
    stop_words = {
        "the", "and", "or", "of", "a", "an", "in", "to", "for", "with", "by", "on", "at", "from",
        "system", "architecture", "design", "diagram", "management", "processing", "engine", "service",
        "component", "nodes", "edges", "application", "platform", "infrastructure", "using", "with", "as"
    }
    
    full_text = f"{topic} {slide_title} {slide_content}".lower()
    cleaned_text = re.sub(r"[^a-z0-9\s\.-]", " ", full_text)
    
    words = cleaned_text.split()
    phrases = []
    current_phrase = []
    
    for w in words:
        if w in stop_words or w == "-" or w == ".":
            if current_phrase:
                phrases.append(" ".join(current_phrase))
                current_phrase = []
        else:
            current_phrase.append(w)
    if current_phrase:
        phrases.append(" ".join(current_phrase))
        
    seen = set()
    unique_phrases = []
    for p in phrases:
        p_title = p.title()
        p_lower = p_title.lower()
        if p_lower not in seen and len(p_lower.split()) <= 4 and len(p_lower) > 2:
            seen.add(p_lower)
            unique_phrases.append(p_title)
            
    return unique_phrases

def apply_theme_awareness(components: List[Dict[str, Any]], visual_style: str) -> List[Dict[str, Any]]:
    """
    Themes must affect only colors and containers.
    This function returns components untouched, preserving all shape_hints and names.
    """
    return components

def detect_hub_node(components: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Selects the center/hub node semantically rather than using components[0]."""
    if not components:
        return None
    # 1. Look for gateways
    gateways = [c for c in components if c["kind"] == "gateway"]
    if gateways:
        return gateways[0]
    # 2. Look for central services/reasoning engines
    services = [c for c in components if c["kind"] in ["service", "llm", "compute"]]
    if services:
        importance_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        services.sort(key=lambda x: -importance_order.get(x.get("importance", "medium").lower(), 2))
        return services[0]
    # 3. Fallback to highest importance node
    importance_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    sorted_all = sorted(components, key=lambda x: -importance_order.get(x.get("importance", "medium").lower(), 2))
    return sorted_all[0]

def build_dynamic_dependencies(components: List[Dict[str, Any]], topology: str) -> None:
    """Generates service-specific dependencies based on flow_order, tier, and name matching."""
    if not components:
        return
    topo = (topology or "standard").lower().strip()
    
    # Reset depends_on lists
    for c in components:
        c["depends_on"] = []
        
    if topo in ["ai_pipeline", "cnn", "transformer", "flowchart", "pipeline"]:
        # Sequential pipeline flow
        sorted_comps = sorted(components, key=lambda x: x.get("flow_order", 1))
        for i in range(1, len(sorted_comps)):
            sorted_comps[i]["depends_on"] = [sorted_comps[i-1]["name"]]
            
    elif topo in ["hub_spoke", "star"]:
        # Star topology: spokes connect to the dynamic hub
        hub = detect_hub_node(components)
        if hub:
            for c in components:
                if c["name"] != hub["name"]:
                    c["depends_on"] = [hub["name"]]
            
    elif topo == "ring":
        # Circular flow: 0 -> 1 -> 2 -> ... -> N -> 0
        for i in range(len(components)):
            prev_idx = (i - 1) % len(components)
            components[i]["depends_on"] = [components[prev_idx]["name"]]
            
    else:
        # Service-specific microservices / cloud dependency matching
        clients = [c for c in components if c["kind"] == "client"]
        gateways = [c for c in components if c["kind"] == "gateway"]
        services = [c for c in components if c["kind"] in ["service", "compute", "llm"]]
        datas = [c for c in components if c["kind"] in ["database", "vector_db", "cache", "queue", "storage"]]
        
        # Ingress routing
        for g in gateways:
            if clients:
                g["depends_on"] = [c["name"] for c in clients]
                
        # Link services to gateways
        for s in services:
            if gateways:
                s["depends_on"] = [g["name"] for g in gateways]
            elif clients:
                s["depends_on"] = [c["name"] for c in clients]
                
        # Service-specific database / cache connections using prefix matching
        for d in datas:
            d_name = d["name"].lower()
            linked = False
            for s in services:
                s_prefix = s["name"].lower().split()[0]
                if s_prefix in d_name:
                    d["depends_on"].append(s["name"])
                    linked = True
            if not linked and services:
                svc_idx = datas.index(d) % len(services)
                d["depends_on"] = [services[svc_idx]["name"]]

def assign_flow_order(components: List[Dict[str, Any]], topology: str) -> None:
    """Generates sequential flow_order values using topology registries (no scattered keywords)."""
    topo = (topology or "standard").lower().strip()
    order_list = FLOW_ORDER_REGISTRY.get(topo, FLOW_ORDER_REGISTRY["microservices"])
    
    for c in components:
        name_lower = c["name"].lower()
        hint_lower = str(c.get("shape_hint", "")).lower()
        assigned = False
        
        for idx, kw in enumerate(order_list):
            pattern = rf"\b{re.escape(kw)}\b"
            if re.search(pattern, name_lower) or re.search(pattern, hint_lower):
                c["flow_order"] = idx + 1
                assigned = True
                break
        if not assigned:
            kind_order = {
                "client": 1, "gateway": 2, "service": 3, "llm": 3,
                "queue": 4, "cache": 4, "database": 5, "vector_db": 5,
                "storage": 5, "monitoring": 6, "logging": 6, "analytics": 6
            }
            c["flow_order"] = kind_order.get(c["kind"], 3)

def calculate_confidence_importance(c: Dict[str, Any], text: str, topic: str, slide_title: str, domain: str, topology: str) -> str:
    """Calculates importance dynamically based on positioning, frequency, and topology/domain relevance."""
    name_lower = c["name"].lower()
    score = 0
    
    count = text.lower().count(name_lower)
    score += min(3, count)
    
    if name_lower in topic.lower() or name_lower in slide_title.lower():
        score += 3
        
    idx = text.lower().find(name_lower)
    if idx != -1:
        text_len = len(text)
        if idx < (text_len * 0.3):
            score += 2
        elif idx < (text_len * 0.6):
            score += 1
            
    kind = c["kind"]
    if domain == "AI" and kind in ["llm", "vector_db"]:
        score += 2
    elif domain == "Kubernetes" and kind in ["container", "gateway"]:
        score += 2
    elif domain == "Event-driven" and kind == "queue":
        score += 2
        
    if score >= 7:
        return "critical"
    elif score >= 5:
        return "high"
    elif score >= 3:
        return "medium"
    else:
        return "low"

def deduplicate_components(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Removes duplicate components based on name and kind."""
    seen = set()
    unique = []
    for c in components:
        key = (c.get("name", "").lower().strip(), c.get("kind", "").lower().strip())
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique

def post_process_components(
    components: List[Dict[str, Any]], 
    topology: str = None, 
    visual_style: str = None,
    context_text: str = "",
    topic: str = "",
    slide_title: str = ""
) -> List[Dict[str, Any]]:
    """Performs deduplication, flow order, topology and parent hierarchies mapping, and adaptive density clipping."""
    # 1. Deduplicate components
    components = deduplicate_components(components)
    
    domain = detect_domain(topic, slide_title, context_text)
    topo = (topology or "standard").lower().strip()
    
    # 2. Assign flow orders first (so parent container logic can leverage it)
    assign_flow_order(components, topology)
    
    # 3. Map default values, compute importance, and perform shape hint matching
    for c in components:
        c.setdefault("depends_on", [])
        c.setdefault("parent", None)
        c.setdefault("group", "default")
        c.setdefault("zone", "private")
        c.setdefault("namespace", "default")
        c.setdefault("cluster_id", "default_cluster")
        c.setdefault("rank_group", "default_rank")
        c.setdefault("lane", "default_lane")
        c.setdefault("column", "default_col")
        c.setdefault("swimlane", "default_swimlane")
        c.setdefault("section", "default_section")
        c.setdefault("row", 1)
        c.setdefault("phase", "default_phase")
        c.setdefault("stage", "default_stage")
        c.setdefault("layer", "default_layer")
        
        # Calculate dynamic confidence / importance
        imp = calculate_confidence_importance(c, context_text, topic, slide_title, domain, topo)
        c["importance"] = imp
        c["confidence"] = imp
            
        # Shape Hint matching using word boundary search (no substrings)
        label_lower = c["name"].lower()
        shape_hint_lower = str(c.get("shape_hint", "")).lower()
        resolved_shape = c.get("kind", "service")
        
        for tech, hint in TECHNOLOGY_SHAPE_HINTS.items():
            pattern = rf"\b{re.escape(tech)}\b"
            if re.search(pattern, label_lower) or re.search(pattern, shape_hint_lower):
                resolved_shape = hint
                break
        c["shape_hint"] = resolved_shape
        
    # 4. Topology-specific parenting and layout hierarchies (Widescreen 15:8 layout preparation)
    for c in components:
        tier = c["tier"]
        kind = c["kind"]
        flow = c["flow_order"]
        imp = c["importance"]
        
        if topo == "cloud":
            c["group"] = "AWS VPC" if visual_style == "aws" else "Cloud VPC"
            c["zone"] = "public_zone" if tier == "frontend" else "private_zone"
            c["namespace"] = "public-subnet" if tier == "frontend" else "private-subnet"
            c["cluster_id"] = "vpc_cluster"
            c["rank_group"] = f"vpc_subnet_{tier}"
            c["lane"] = "vpc_lane"
            c["column"] = flow
            c["row"] = 1 if imp == "critical" else (2 if imp == "high" else 3)
            c["swimlane"] = f"subnet_{tier}"
            c["section"] = "cloud_region"
            c["phase"] = tier
            c["stage"] = tier
            c["layer"] = tier
            
        elif topo == "kubernetes":
            c["parent"] = "K8s Cluster"
            c["group"] = "Kubernetes Cluster"
            c["namespace"] = "kube-system" if tier == "infra" else "default"
            c["cluster_id"] = "k8s_cluster"
            c["rank_group"] = f"k8s_namespace_{c['namespace']}"
            c["lane"] = f"k8s_lane_{c['namespace']}"
            c["column"] = flow
            c["row"] = 1 if imp == "critical" else 2
            c["swimlane"] = f"namespace_{c['namespace']}"
            c["section"] = "k8s_cluster"
            c["phase"] = "pod_deployment"
            c["stage"] = "kubernetes"
            c["layer"] = "container"
            
        elif topo == "layered":
            c["group"] = "Layered Architecture"
            if tier == "frontend":
                c["parent"] = "Presentation Layer"
                c["section"] = "Presentation Layer"
            elif tier == "backend":
                c["parent"] = "Business Logic Layer"
                c["section"] = "Business Logic Layer"
            elif tier == "data":
                c["parent"] = "Data Access Layer"
                c["section"] = "Data Access Layer"
            c["rank_group"] = c.get("parent", "default_rank")
            c["cluster_id"] = "layered_cluster"
            c["lane"] = f"layered_lane_{tier}"
            c["column"] = flow
            c["row"] = 1 if imp == "critical" else 2
            c["swimlane"] = f"swimlane_{tier}"
            c["phase"] = tier
            c["stage"] = tier
            c["layer"] = tier
            
        elif topo == "microservices":
            c["cluster_id"] = "microservices_cluster"
            if tier == "frontend" or kind == "gateway":
                c["parent"] = "Ingress"
                c["group"] = "Ingress"
            elif tier == "backend":
                c["parent"] = "Service Layer"
                c["group"] = "Service Layer"
            elif tier == "data":
                c["parent"] = "Database Layer"
                c["group"] = "Database Layer"
            c["rank_group"] = c.get("parent", "default_rank")
            c["lane"] = f"{c['parent']}_lane"
            c["column"] = flow
            c["row"] = 1 if imp == "critical" else 2
            c["swimlane"] = f"{c['parent']}_swimlane"
            c["section"] = f"{c['parent']}_section"
            c["phase"] = "microservices"
            c["stage"] = "tier"
            c["layer"] = "service"
            
        elif topo == "event_driven":
            c["cluster_id"] = "event_driven_cluster"
            if kind == "client":
                c["parent"] = "Producer"
                c["group"] = "Producer"
            elif kind == "queue":
                c["parent"] = "Broker"
                c["group"] = "Broker"
            else:
                c["parent"] = "Consumer"
                c["group"] = "Consumer"
            c["rank_group"] = c.get("parent", "default_rank")
            c["lane"] = f"{c['parent']}_lane"
            c["column"] = flow
            c["row"] = 1 if imp == "critical" else 2
            c["swimlane"] = f"{c['parent']}_swimlane"
            c["section"] = f"{c['parent']}_section"
            c["phase"] = "event_driven"
            
        elif topo in ["star", "ring", "hub_spoke"]:
            c["cluster_id"] = f"{topo}_cluster"
            hub = detect_hub_node(components)
            if hub and c["name"] == hub["name"]:
                c["parent"] = "Central Container"
                c["group"] = "Hub Zone"
                c["row"] = 1
            else:
                c["parent"] = "Outer Zones"
                c["group"] = "Spoke Zone"
                c["row"] = 2
            c["rank_group"] = c.get("parent", "default_rank")
            c["lane"] = f"{c['parent']}_lane"
            c["column"] = flow
            c["swimlane"] = f"{c['parent']}_swimlane"
            c["section"] = f"{c['parent']}_section"
            
        elif topo in ["cnn", "transformer", "ai_pipeline", "rag"]:
            c["cluster_id"] = "ai_pipeline_cluster"
            if flow <= 2:
                c["parent"] = "Input"
                c["group"] = "Pipeline Input Phase"
            elif flow <= 4:
                c["parent"] = "Processing"
                c["group"] = "Pipeline Processing Phase"
            else:
                c["parent"] = "Output"
                c["group"] = "Pipeline Output Phase"
            c["rank_group"] = c.get("parent", "default_rank")
            c["lane"] = f"{c['parent']}_lane"
            c["column"] = flow
            c["row"] = 1
            c["swimlane"] = f"{c['parent']}_swimlane"
            c["section"] = f"{c['parent']}_section"
            c["phase"] = c.get("parent", "default_phase")
            
        elif topo == "flowchart":
            c["cluster_id"] = "flowchart_cluster"
            c["parent"] = f"swimlane_{str((flow - 1) // 3 + 1)}"
            c["group"] = c["parent"]
            c["rank_group"] = c["parent"]
            c["lane"] = c["parent"]
            c["column"] = flow
            c["row"] = 1
            c["swimlane"] = c["parent"]
            c["section"] = "flowchart_process"
            
        elif topo == "uml":
            c["cluster_id"] = "uml_cluster"
            c["parent"] = f"package_{tier}"
            c["group"] = c["parent"]
            c["rank_group"] = c["parent"]
            c["lane"] = f"swimlane_{tier}"
            c["column"] = flow
            c["row"] = 1
            c["swimlane"] = f"swimlane_{tier}"
            c["section"] = "uml_class_group"
            c["phase"] = tier
            c["stage"] = tier
            c["layer"] = tier
            
    # 5. Build dynamic dependencies
    build_dynamic_dependencies(components, topology)

    # 6. Apply theme awareness (visual only, no renaming/shapes alterations)
    components = apply_theme_awareness(components, visual_style)
    
    # 7. Dynamic Density Control (Importance, Connectivity, and Topology-Aware Clipping)
    # Define adaptive node limits per topology
    limits = {
        "cnn": 10, "star": 10, "ring": 10, "flowchart": 12, "uml": 12,
        "transformer": 14,
        "microservices": 16, "rag": 16, "ai_pipeline": 16,
        "cloud": 18,
        "kubernetes": 22
    }
    limit = limits.get(topo, 12)
    
    # Sort components dynamically considering importance and critical hubs/databases
    importance_weights = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    def get_sort_score(x):
        score = importance_weights.get(x.get("importance", "medium").lower(), 2) * 10
        # Give boost to critical kinds (databases/vector stores/gateways)
        if x["kind"] in ["gateway", "llm", "vector_db", "database"]:
            score += 5
        # Give boost to central container nodes
        if x.get("parent") == "Central Container" or x.get("parent") == "Ingress":
            score += 3
        return score
        
    components.sort(key=lambda x: -get_sort_score(x))
    
    if len(components) > limit:
        print(f"[COMPONENT_EXTRACTOR] Dynamic density control: Keeping top {limit} of {len(components)} components for topology '{topo}'.")
        components = components[:limit]
        
    return components

def extract_components(
    topic: str,
    slide_title: str,
    slide_content: str,
    topology: str = None,
    visual_style: str = None,
    feedback: str = ""
) -> List[Dict[str, Any]]:
    """
    Calls the LLM to dynamically extract the system components.
    Falls back to a fully dynamic text analysis if the LLM call fails.
    visual_style is explicitly passed instead of relying on global state.
    """
    domain = detect_domain(topic, slide_title, slide_content)
    domain_guideline = DOMAIN_GUIDELINES.get(domain, DOMAIN_GUIDELINES["Generic"])
    full_text = f"{topic} {slide_title} {slide_content}"

    # Normalize query variations using SYNONYM_REGISTRY
    normalized_text = full_text.lower()
    for key, val in SYNONYM_REGISTRY.items():
        pattern = rf"\b{re.escape(key)}\b"
        normalized_text = re.sub(pattern, val, normalized_text)

    system_prompt = (
        "You are an expert systems architect.\n"
        "Your task is to analyze the user topic, slide title, and slide content, and extract "
        "a set of semantic architecture components (nodes) that represent this system's architecture.\n"
        "Do NOT generate generic dummy components (like 'App Replica Node 1..10', 'ELK Log Collector', 'Grafana Dashboard', etc.) "
        "unless they are explicitly requested or implied by the user content.\n"
        "Ensure component names are concrete technologies and brands instead of generic names (e.g., 'React Frontend' instead of 'Client', 'NodeJS API' instead of 'Service', 'MongoDB' instead of 'Database', 'Redis Cache' instead of 'Cache').\n"
        f"Domain Guidance: {domain_guideline}\n\n"
        "Classify each component into one of these allowed kinds: client, gateway, service, cache, database, queue, storage, vector_db, llm, monitoring, logging, analytics, external, security.\n"
        "Assign a tier to each component: frontend, backend, data, infra.\n\n"
        "Return only a JSON object matching this schema:\n"
        "{\n"
        "  \"title\": \"Dynamic System Title\",\n"
        "  \"components\": [\n"
        "    {\n"
        "      \"name\": \"[Concrete Tech Name, e.g. React Frontend, NodeJS API, PostgreSQL DB]\",\n"
        "      \"kind\": \"[One of the allowed kinds]\",\n"
        "      \"shape_hint\": \"[Concrete technology name in lowercase, e.g. react, nodejs, postgres, redis, kafka, lambda, s3, pod, service, ingress, openai, claude, gemini, etc.]\",\n"
        "      \"tier\": \"[frontend/backend/data/infra]\",\n"
        "      \"importance\": \"[critical/high/medium/low]\",\n"
        "      \"depends_on\": [\"List of component names this component depends on/sends data to\"],\n"
        "      \"parent\": \"[Name of parent container or null if top-level]\",\n"
        "      \"group\": \"[Logical group/zone name, or null]\",\n"
        "      \"flow_order\": [Integer representing step order in data flow, e.g. 1, 2, 3],\n"
        "      \"zone\": \"[dmz/public/private/restricted]\",\n"
        "      \"namespace\": \"[Namespace label, or null]\"\n"
        "    }\n"
        "  ]\n"
        "}"
    )

    user_prompt = (
        f"Overall Presentation Topic: {topic}\n"
        f"Slide Title: {slide_title}\n"
        f"Slide Content / Bullet Points:\n{slide_content}\n"
        f"Requested Topology: {topology or 'standard'}\n"
        f"Active Style: {visual_style or 'classic'}"
    )
    if feedback:
        user_prompt += f"\n\nFeedback from previous render failure:\n{feedback}"

    try:
        from services.llm_client import call_llm
        print(f"[COMPONENT_EXTRACTOR] Querying LLM for components on topic: '{topic}' (Domain: {domain})")
        raw_response = call_llm(system_prompt, user_prompt)
        spec = clean_and_parse_json(raw_response)
        
        components = spec.get("components", [])
        if components and isinstance(components, list):
            cleaned = []
            for c in components:
                if isinstance(c, dict) and "name" in c:
                    name = str(c["name"]).strip()
                    kind_raw = str(c.get("kind", "service")).lower().strip()
                    
                    kind = kind_raw
                    label_lower = name.lower()
                    if any(x in label_lower for x in ("cache", "redis", "memcached")):
                        kind = "cache"
                    elif any(x in label_lower for x in ("queue", "kafka", "rabbitmq", "event-bus", "pubsub")):
                        kind = "queue"
                    elif any(x in label_lower for x in ("client", "user", "browser", "mobile", "app-client")):
                        kind = "client"
                    elif any(x in label_lower for x in ("gateway", "load-balancer", "load balancer", "proxy", "nginx", "ingress")):
                        kind = "gateway"
                    elif any(x in label_lower for x in ("s3", "bucket", "storage", "blob", "volume")):
                        kind = "storage"
                    elif any(x in label_lower for x in ("llm", "openai", "gpt", "gemini", "claude", "attention", "transformer", "model")):
                        kind = "llm"
                    elif kind == "compute":
                        kind = "service"
                    elif kind not in ALLOWED_KINDS:
                        kind = KIND_SYNONYMS.get(kind_raw, "service")
                        
                    cleaned.append({
                        "name": name,
                        "kind": kind,
                        "shape_hint": str(c.get("shape_hint", kind)).strip(),
                        "tier": str(c.get("tier", "backend")).strip(),
                        "importance": str(c.get("importance", "medium")).lower().strip(),
                        "depends_on": c.get("depends_on", []),
                        "parent": c.get("parent"),
                        "group": c.get("group"),
                        "flow_order": c.get("flow_order", 1),
                        "zone": c.get("zone"),
                        "namespace": c.get("namespace")
                    })
            if cleaned:
                return post_process_components(cleaned, topology, visual_style, normalized_text, topic, slide_title)
    except Exception as e:
        print(f"[COMPONENT_EXTRACTOR] LLM extraction failed: {e}. Falling back to dynamic registry/noun extraction.")
        
    fallback = get_fallback_components(topic, slide_title, slide_content, topology, visual_style)
    return post_process_components(fallback, topology, visual_style, normalized_text, topic, slide_title)

def get_fallback_components(
    topic: str, 
    slide_title: str, 
    slide_content: str, 
    topology: str = None, 
    visual_style: str = None
) -> List[Dict[str, Any]]:
    """Provides a fully dynamic text-based analysis fallback component set (no generic suffix templates)."""
    full_text = f"{topic} {slide_title} {slide_content}"
    
    # 1. Match registry entities present in the text
    entities = extract_entities(full_text)
    if len(entities) >= 4:
        return entities
        
    # 2. Extract noun phrases dynamically
    nouns = extract_nouns_and_phrases(topic, slide_title, slide_content)
    
    components = []
    if len(nouns) >= 2:
        for idx, noun in enumerate(nouns[:5]):
            if idx == 0:
                kind, tier = "client", "frontend"
            elif idx == 1:
                kind, tier = "service", "backend"
            elif idx == 2:
                kind, tier = "database", "data"
            elif idx == 3:
                kind, tier = "queue", "data"
            else:
                kind, tier = "monitoring", "infra"
                
            components.append({
                "name": noun,
                "kind": kind,
                "shape_hint": kind,
                "tier": tier,
                "importance": "high" if idx < 3 else "medium"
            })
    else:
        # Minimal semantic fallback using clean topic words
        clean_topic = re.sub(r'[^a-zA-Z0-9 ]', '', topic)
        clean_topic = clean_topic.replace("Architecture", "").replace("System", "").strip()
        words = [w.capitalize() for w in clean_topic.split() if len(w) > 2]
        if not words:
            words = ["System", "Data", "Engine"]
            
        for idx, w in enumerate(words[:4]):
            if idx == 0:
                kind, tier = "client", "frontend"
            elif idx == 1:
                kind, tier = "service", "backend"
            elif idx == 2:
                kind, tier = "database", "data"
            else:
                kind, tier = "monitoring", "infra"
                
            components.append({
                "name": w,
                "kind": kind,
                "shape_hint": kind,
                "tier": tier,
                "importance": "high"
            })
            
    return components

if __name__ == "__main__":
    test_comps = extract_components("RAG AI Chatbot", "Retrieval Pipeline", "Loads documents, computes embeddings, saves to Pinecone, prompts Claude.")
    print("Extracted Components:")
    for c in test_comps:
        print(f" - {c['name']} ({c['kind']}) | Hint: {c['shape_hint']} | Parent: {c['parent']} | Cluster: {c['cluster_id']} | Rank: {c['rank_group']} | Row: {c['row']} | Col: {c['column']}")
