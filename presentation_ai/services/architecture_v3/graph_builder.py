import re
import json
import uuid
from typing import Dict, Any, List

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

def clean_and_parse_json(text: str) -> dict:
    """Safely extracts and parses JSON from LLM output, even with markdown code blocks or outer text."""
    text = text.strip()
    
    # Try finding the first '{' and last '}'
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_str = text[start_idx:end_idx+1]
        try:
            return json.loads(json_str)
        except Exception:
            pass
            
    # Try stripping markdown fences
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        if text.startswith("json"):
            text = text.split("\n", 1)[1].strip()
            
    # Try direct parse
    return json.loads(text)

def extract_architecture_spec(topic: str, topology: str) -> dict:
    """
    Calls the LLM to extract domain-specific components and relationships for a topic.
    Returns a dict with 'title', 'components', and 'relationships'.
    """
    try:
        from services.llm_client import call_llm
        print(f"[GRAPH_BUILDER_V3] Querying LLM for topic: '{topic}' (topology: {topology})")
        
        system_prompt = (
            "You are an expert systems architect.\n"
            f"Analyze the topic: {topic}\n"
            "Identify the technology domain:\n"
            "- If cloud/AWS/GCP/Azure: generate cloud infrastructure components\n"
            "- If kubernetes/k8s: generate k8s cluster components\n"
            "- If ML/AI/LLM: generate ML pipeline components\n"
            "- If microservices: generate service mesh components\n"
            "- If database/data: generate data pipeline components\n"
            "- If network/security: generate network topology components\n\n"
            "Your task is to extract core architecture components and their relationships for the given topic "
            "and architectural style (topology).\n"
            "You must return ONLY a valid JSON object. Do NOT include markdown code blocks, backticks, "
            "XML, SVG, Draw.io syntax, or coordinates. Keep the JSON clean and raw. Do NOT generate containers or styles.\n\n"
            "JSON SCHEMA:\n"
            "{\n"
            "  \"title\": \"System Architecture for [Topic]\",\n"
            "  \"components\": [\n"
            "    {\n"
            "      \"name\": \"[Exact technology name, e.g. 'PostgreSQL', 'Redis', 'Nginx', never generic names like 'Service1']\",\n"
            "      \"kind\": \"[One of: compute, database, gateway, queue, storage, security, external]\",\n"
            "      \"shape_hint\": \"[draw.io shape keyword, e.g. 'database', 'load balancer', 'cache', 'api gateway', 'lambda', 's3', 'pod', 'service', 'ingress', 'deployment', 'namespace', 'model', 'training', 'inference', 'vector db', 'embedding']\",\n"
            "      \"tier\": \"[which layer it belongs to: frontend/backend/data/infra]\"\n"
            "    }\n"
            "  ],\n"
            "  \"relationships\": [\n"
            "    {\n"
            "      \"source\": \"[Source component name matching exactly one of the component names]\",\n"
            "      \"target\": \"[Target component name matching exactly one of the component names]\",\n"
            "      \"label\": \"[Action/interaction label, e.g. queries, sends events, HTTP request]\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )
        
        user_prompt = f"Topic: {topic}\nArchitecture Style / Topology: {topology}"
        
        raw_response = call_llm(system_prompt, user_prompt)
        spec = clean_and_parse_json(raw_response)
        
        if isinstance(spec, dict) and "components" in spec:
            components = []
            for c in spec.get("components", []):
                if isinstance(c, dict) and "name" in c and "kind" in c:
                    name = str(c["name"]).strip()
                    kind_raw = str(c["kind"]).lower().strip()
                    
                    # Normalize kind based on component name keywords first
                    kind = kind_raw
                    label_lower = name.lower()
                    
                    if any(x in label_lower for x in ("cache", "redis", "memcached")):
                        kind = "cache"
                    elif any(x in label_lower for x in ("queue", "kafka", "rabbitmq", "event-bus", "event bus", "pubsub")):
                        kind = "queue"
                    elif any(x in label_lower for x in ("client", "user", "browser", "mobile", "app-client", "desktop-client")):
                        kind = "client"
                    elif any(x in label_lower for x in ("gateway", "load-balancer", "load balancer", "proxy", "nginx", "ingress", "route53", "route-53")):
                        kind = "gateway"
                    elif any(x in label_lower for x in ("s3", "bucket", "storage", "blob", "volume")):
                        kind = "storage"
                    elif any(x in label_lower for x in ("llm", "openai", "gpt", "gemini", "claude", "attention", "transformer", "model")):
                        kind = "llm"
                    elif kind == "compute":
                        kind = "service"
                    elif kind not in ALLOWED_KINDS:
                        kind = KIND_SYNONYMS.get(kind_raw, "service")
                        
                    components.append({
                        "name": name,
                        "kind": kind,
                        "shape_hint": str(c.get("shape_hint", "")).strip(),
                        "tier": str(c.get("tier", "")).strip()
                    })
                    
            relationships = []
            for r in spec.get("relationships", []):
                if isinstance(r, dict) and "source" in r and "target" in r:
                    relationships.append({
                        "source": str(r["source"]).strip(),
                        "target": str(r["target"]).strip(),
                        "label": str(r.get("label", "Request")).strip()
                    })
                    
            return {
                "title": spec.get("title", f"{topic} Architecture"),
                "components": components,
                "relationships": relationships
            }
    except Exception as e:
        print(f"[GRAPH_BUILDER_V3] LLM spec extraction failed: {e}. Falling back to rule-based fallback spec.")
        
    return _build_fallback_spec(topic, topology)

def _build_fallback_spec(topic: str, topology: str) -> dict:
    """
    Provides a basic fallback spec that will be enriched by individual topology builders.
    """
    return {
        "title": f"{topic} Architecture",
        "components": [],
        "relationships": []
    }

def get_base_name(spec: dict) -> str:
    """Extracts a clean noun phrase prefix from the system title/topic."""
    base_name = spec.get("title", "System")
    for word in ["System Architecture for", "System Architecture", "Architecture", "System", "Platform", "Engine", "Service", "App", "Application", "Framework", "Schema"]:
        base_name = re.sub(rf'\b{word}\b', '', base_name, flags=re.IGNORECASE)
    base_name = base_name.strip()
    return base_name if base_name else "System"

def clean_node_id(name: str) -> str:
    """Generates a safe alphanumeric XML ID from a component label."""
    nid = name.replace(" ", "_").replace("-", "_").lower()
    nid = re.sub(r'[^a-zA-Z0-9_]', '', nid)
    if not nid:
        nid = f"node_{uuid.uuid4().hex[:6]}"
    return nid

def get_components_of_kinds(spec: dict, kinds: list, base_name: str, default_name_suffix: str, default_kind: str, min_count: int = 1) -> list:
    """
    Filters the parsed LLM components list for specific kinds.
    Injects dynamic topic-prefixed defaults if fewer than min_count exist.
    """
    results = []
    for c in spec.get("components", []):
        if c.get("kind") in kinds:
            results.append(c)
            
    if len(results) < min_count:
        for i in range(len(results), min_count):
            suffix = f" {default_name_suffix}" if i == 0 else f" {default_name_suffix} {i+1}"
            results.append({
                "name": f"{base_name}{suffix}",
                "kind": default_kind
            })
    return results

def _get_skeleton_containers(topology: str) -> List[Dict[str, Any]]:
    """Defines container structures for the 12 topology skeletons."""
    t_key = topology.lower().strip()
    
    if t_key == "microservices":
        return [
            {"id": "cluster", "label": "Kubernetes Cluster", "parent": None},
            {"id": "ingress", "label": "Ingress Gateway Layer", "parent": "cluster"},
            {"id": "services", "label": "Core Services Tier", "parent": "cluster"},
            {"id": "db_tier", "label": "Database & Queue Tier", "parent": "cluster"},
            {"id": "observability", "label": "Monitoring Stack", "parent": "cluster"}
        ]
    elif t_key == "cloud":
        return [
            {"id": "region", "label": "Region (Cloud Infrastructure)", "parent": None},
            {"id": "vpc", "label": "VPC (Virtual Private Cloud)", "parent": "region"},
            {"id": "public_subnet", "label": "Public Subnet (DMZ)", "parent": "vpc"},
            {"id": "private_subnet", "label": "Private Subnet (App Tier)", "parent": "vpc"},
            {"id": "db_subnet", "label": "Database Subnet (Data Tier)", "parent": "vpc"}
        ]
    elif t_key == "kubernetes":
        return [
            {"id": "cluster", "label": "K8s Cluster Node Group", "parent": None},
            {"id": "control_plane", "label": "K8s Control Plane Services", "parent": "cluster"},
            {"id": "worker_node", "label": "K8s Worker Node Group", "parent": "cluster"},
            {"id": "pods_tier", "label": "Active Pod Containers", "parent": "worker_node"}
        ]
    elif t_key == "ai_pipeline":
        return [
            {"id": "pipeline", "label": "AI Application Platform", "parent": None},
            {"id": "ingestion", "label": "Data Ingestion & Loaders", "parent": "pipeline"},
            {"id": "processing", "label": "Prompt & Orchestration Engine", "parent": "pipeline"},
            {"id": "model_tier", "label": "LLM & Vector Model Tier", "parent": "pipeline"}
        ]
    elif t_key == "rag_pipeline":
        return [
            {"id": "rag_platform", "label": "RAG Architecture Platform", "parent": None},
            {"id": "data_ingest", "label": "Data Ingestion Tier", "parent": "rag_platform"},
            {"id": "orchestration", "label": "Orchestration & Retrieval Layer", "parent": "rag_platform"},
            {"id": "models", "label": "Foundation Models & Vector Store", "parent": "rag_platform"}
        ]
    elif t_key == "event_driven":
        return [
            {"id": "event_mesh", "label": "Event-Driven System Architecture", "parent": None},
            {"id": "producers", "label": "Event Producers Layer", "parent": "event_mesh"},
            {"id": "brokers", "label": "Event Broker & Queue Tier", "parent": "event_mesh"},
            {"id": "consumers", "label": "Event Consumers / Service Tier", "parent": "event_mesh"}
        ]
    elif t_key == "transformer":
        return [
            {"id": "transformer_block", "label": "Transformer Model Architecture", "parent": None},
            {"id": "encoder", "label": "Encoder Blocks Stack", "parent": "transformer_block"},
            {"id": "decoder", "label": "Decoder Blocks Stack", "parent": "transformer_block"},
            {"id": "output_tier", "label": "Linear & Softmax Projection", "parent": "transformer_block"}
        ]
    elif t_key == "cnn":
        return [
            {"id": "neural_net", "label": "CNN Model Architecture", "parent": None},
            {"id": "features", "label": "Feature Extraction Layers", "parent": "neural_net"},
            {"id": "classifier", "label": "Dense Classification Head", "parent": "neural_net"}
        ]
    elif t_key == "mvc":
        return [
            {"id": "mvc_app", "label": "Model-View-Controller Framework", "parent": None},
            {"id": "controller_layer", "label": "Controller & Routers", "parent": "mvc_app"},
            {"id": "view_layer", "label": "View & Template UI Renderers", "parent": "mvc_app"},
            {"id": "model_layer", "label": "Model Entities & ORM", "parent": "mvc_app"}
        ]
    elif t_key == "hexagonal":
        return [
            {"id": "hexagon", "label": "Hexagonal Domain Core Architecture", "parent": None},
            {"id": "driving_adapters", "label": "Driving Inbound Adapters", "parent": "hexagon"},
            {"id": "domain_core", "label": "Pure Domain Business Logic", "parent": "hexagon"},
            {"id": "driven_adapters", "label": "Driven Outbound Adapters", "parent": "hexagon"}
        ]
    elif t_key == "client_server":
        return [
            {"id": "app_system", "label": "Client-Server System", "parent": None},
            {"id": "client_side", "label": "Client Applications Layer", "parent": "app_system"},
            {"id": "server_side", "label": "Server Application Layer", "parent": "app_system"},
            {"id": "storage_side", "label": "Data & Persistence Tier", "parent": "app_system"}
        ]
    
    # Default fallback to layered
    return [
        {"id": "app_layered", "label": "Layered Architecture", "parent": None},
        {"id": "presentation_layer", "label": "Presentation Layer", "parent": "app_layered"},
        {"id": "business_layer", "label": "Business Logic Layer", "parent": "app_layered"},
        {"id": "data_layer", "label": "Data Access Layer", "parent": "app_layered"}
    ]

# Skeleton mapping configuration dictionary to resolve container ID for a given kind
TOPOLOGY_KIND_MAP = {
    "microservices": {
        "client": "ingress", "gateway": "ingress", "external": "ingress",
        "service": "services", "container": "services", "llm": "services",
        "database": "db_tier", "cache": "db_tier", "queue": "db_tier", "storage": "db_tier", "vector_db": "db_tier",
        "monitoring": "observability", "logging": "observability", "analytics": "observability"
    },
    "cloud": {
        "client": "public_subnet", "gateway": "public_subnet", "external": "public_subnet",
        "service": "private_subnet", "container": "private_subnet", "llm": "private_subnet",
        "database": "db_subnet", "cache": "db_subnet", "queue": "db_subnet", "storage": "db_subnet", "vector_db": "db_subnet",
        "monitoring": "private_subnet", "logging": "private_subnet", "analytics": "private_subnet"
    },
    "kubernetes": {
        "client": "worker_node", "gateway": "control_plane", "external": "control_plane",
        "service": "pods_tier", "container": "pods_tier", "llm": "pods_tier",
        "database": "pods_tier", "cache": "pods_tier", "queue": "pods_tier", "storage": "pods_tier", "vector_db": "pods_tier",
        "monitoring": "control_plane", "logging": "control_plane", "analytics": "control_plane"
    },
    "ai_pipeline": {
        "client": "ingestion", "gateway": "ingestion", "external": "ingestion",
        "service": "processing", "container": "processing", "llm": "model_tier",
        "database": "model_tier", "cache": "processing", "queue": "processing", "storage": "ingestion", "vector_db": "model_tier",
        "monitoring": "processing", "logging": "processing", "analytics": "processing"
    },
    "rag_pipeline": {
        "client": "data_ingest", "gateway": "data_ingest", "external": "data_ingest",
        "service": "orchestration", "container": "orchestration", "llm": "models",
        "database": "models", "cache": "orchestration", "queue": "orchestration", "storage": "data_ingest", "vector_db": "models",
        "monitoring": "orchestration", "logging": "orchestration", "analytics": "orchestration"
    },
    "event_driven": {
        "client": "producers", "gateway": "producers", "external": "producers",
        "service": "consumers", "container": "consumers", "llm": "consumers",
        "database": "consumers", "cache": "consumers", "queue": "brokers", "storage": "consumers", "vector_db": "consumers",
        "monitoring": "consumers", "logging": "consumers", "analytics": "consumers"
    },
    "transformer": {
        "client": "output_tier", "gateway": "output_tier", "external": "output_tier",
        "service": "decoder", "container": "decoder", "llm": "decoder",
        "database": "encoder", "cache": "encoder", "queue": "encoder", "storage": "encoder", "vector_db": "encoder",
        "monitoring": "output_tier", "logging": "output_tier", "analytics": "output_tier"
    },
    "cnn": {
        "client": "classifier", "gateway": "features", "external": "features",
        "service": "features", "container": "features", "llm": "classifier",
        "database": "classifier", "cache": "features", "queue": "features", "storage": "features", "vector_db": "features",
        "monitoring": "classifier", "logging": "classifier", "analytics": "classifier"
    },
    "mvc": {
        "client": "view_layer", "gateway": "controller_layer", "external": "view_layer",
        "service": "controller_layer", "container": "controller_layer", "llm": "model_layer",
        "database": "model_layer", "cache": "model_layer", "queue": "model_layer", "storage": "model_layer", "vector_db": "model_layer",
        "monitoring": "controller_layer", "logging": "controller_layer", "analytics": "controller_layer"
    },
    "hexagonal": {
        "client": "driving_adapters", "gateway": "driving_adapters", "external": "driving_adapters",
        "service": "domain_core", "container": "domain_core", "llm": "domain_core",
        "database": "driven_adapters", "cache": "driven_adapters", "queue": "driven_adapters", "storage": "driven_adapters", "vector_db": "driven_adapters",
        "monitoring": "driven_adapters", "logging": "driven_adapters", "analytics": "driven_adapters"
    },
    "client_server": {
        "client": "client_side", "gateway": "server_side", "external": "client_side",
        "service": "server_side", "container": "server_side", "llm": "server_side",
        "database": "storage_side", "cache": "storage_side", "queue": "storage_side", "storage": "storage_side", "vector_db": "storage_side",
        "monitoring": "server_side", "logging": "server_side", "analytics": "server_side"
    },
    "layered": {
        "client": "presentation_layer", "gateway": "presentation_layer", "external": "presentation_layer",
        "service": "business_layer", "container": "business_layer", "llm": "business_layer",
        "database": "data_layer", "cache": "data_layer", "queue": "data_layer", "storage": "data_layer", "vector_db": "data_layer",
        "monitoring": "business_layer", "logging": "business_layer", "analytics": "business_layer"
    }
}

# ==========================================
# TOPOLOGY BUILDERS
# ==========================================

def build_cloud_graph(spec: dict) -> dict:
    """Builds a classic Cloud layer diagram: Load Balancers -> Private Compute Instances -> DB / Storages subnets."""
    base_name = get_base_name(spec)
    containers = _get_skeleton_containers("cloud")
    
    clients = get_components_of_kinds(spec, ["client", "external"], base_name, "Web App User", "client", 1)
    gateways = get_components_of_kinds(spec, ["gateway"], base_name, "Elastic Load Balancer", "gateway", 1)
    services = get_components_of_kinds(spec, ["service", "container", "llm"], base_name, "Application Service", "service", 2)
    databases = get_components_of_kinds(spec, ["database", "vector_db"], base_name, "RDS Core Database", "database", 1)
    caches = get_components_of_kinds(spec, ["cache"], base_name, "ElastiCache Redis", "cache", 1)
    storages = get_components_of_kinds(spec, ["storage"], base_name, "S3 Cloud Storage", "storage", 1)
    
    nodes = []
    edges = []
    
    def add_nodes(comp_list, default_type):
        ids = []
        for c in comp_list:
            nid = clean_node_id(c["name"])
            nodes.append({
                "id": nid,
                "label": c["name"],
                "type": c.get("kind", default_type),
                "brand": None,
                "parent": None
            })
            ids.append(nid)
        return ids
        
    client_ids = add_nodes(clients, "client")
    gateway_ids = add_nodes(gateways, "gateway")
    service_ids = add_nodes(services, "service")
    db_ids = add_nodes(databases, "database")
    cache_ids = add_nodes(caches, "cache")
    storage_ids = add_nodes(storages, "storage")
    
    # Edges: Clients -> Gateways -> Compute -> DB/Storage subnets
    for cid in client_ids:
        for gid in gateway_ids:
            edges.append({"source": cid, "target": gid, "label": "HTTPS Connect"})
            
    for gid in gateway_ids:
        for sid in service_ids:
            edges.append({"source": gid, "target": sid, "label": "Forward Traffic"})
            
    for sid in service_ids:
        if db_ids: edges.append({"source": sid, "target": db_ids[0], "label": "SQL query"})
        if cache_ids: edges.append({"source": sid, "target": cache_ids[0], "label": "Check cache"})
        if storage_ids: edges.append({"source": sid, "target": storage_ids[0], "label": "Fetch files"})
        
    return {
        "containers": containers,
        "nodes": nodes,
        "edges": edges
    }

def build_microservice_graph(spec: dict) -> dict:
    """Builds a microservices topology: Gateway fan-out to distinct Services, pointing to backing Databases / Queues."""
    base_name = get_base_name(spec)
    containers = _get_skeleton_containers("microservices")
    
    clients = get_components_of_kinds(spec, ["client", "external"], base_name, "Web App Interface", "client", 1)
    gateways = get_components_of_kinds(spec, ["gateway"], base_name, "Kong API Gateway", "gateway", 1)
    services = get_components_of_kinds(spec, ["service", "container", "llm"], base_name, "Microservice Pod", "service", 3)
    databases = get_components_of_kinds(spec, ["database", "vector_db"], base_name, "PostgreSQL Database", "database", 1)
    caches = get_components_of_kinds(spec, ["cache"], base_name, "Redis Session Cache", "cache", 1)
    queues = get_components_of_kinds(spec, ["queue"], base_name, "Kafka Event Bus", "queue", 1)
    
    nodes = []
    edges = []
    
    def add_nodes(comp_list, default_type):
        ids = []
        for c in comp_list:
            nid = clean_node_id(c["name"])
            nodes.append({
                "id": nid,
                "label": c["name"],
                "type": c.get("kind", default_type),
                "brand": None,
                "parent": None
            })
            ids.append(nid)
        return ids
        
    client_ids = add_nodes(clients, "client")
    gateway_ids = add_nodes(gateways, "gateway")
    service_ids = add_nodes(services, "service")
    db_ids = add_nodes(databases, "database")
    cache_ids = add_nodes(caches, "cache")
    queue_ids = add_nodes(queues, "queue")
    
    # Client -> Gateway
    for cid in client_ids:
        for gid in gateway_ids:
            edges.append({"source": cid, "target": gid, "label": "HTTPS Connect"})
            
    # Gateway -> Microservices (fan-out)
    for gid in gateway_ids:
        for sid in service_ids:
            edges.append({"source": gid, "target": sid, "label": "Route Request"})
            
    # Services -> DBs / Caches / Queues
    if len(service_ids) >= 3:
        edges.append({"source": service_ids[0], "target": db_ids[0], "label": "SQL queries"})
        edges.append({"source": service_ids[1], "target": cache_ids[0], "label": "Check cache"})
        edges.append({"source": service_ids[2], "target": queue_ids[0], "label": "Publish event"})
        edges.append({"source": queue_ids[0], "target": service_ids[0], "label": "Consume event"})
    else:
        for sid in service_ids:
            if db_ids: edges.append({"source": sid, "target": db_ids[0], "label": "Query"})
            if cache_ids: edges.append({"source": sid, "target": cache_ids[0], "label": "Read cache"})
            if queue_ids: edges.append({"source": sid, "target": queue_ids[0], "label": "Broadcast"})
            
    return {
        "containers": containers,
        "nodes": nodes,
        "edges": edges
    }

def build_kubernetes_graph(spec: dict) -> dict:
    """Builds a Kubernetes cluster node layout: Ingress Controller -> Pod Services -> Active Pod Containers -> Storage."""
    base_name = get_base_name(spec)
    containers = _get_skeleton_containers("kubernetes")
    
    clients = get_components_of_kinds(spec, ["client", "external"], base_name, "External User Client", "client", 1)
    gateways = get_components_of_kinds(spec, ["gateway"], base_name, "Nginx Ingress controller", "gateway", 1)
    services = get_components_of_kinds(spec, ["service", "container"], base_name, "Replica Service Pod", "service", 3)
    storages = get_components_of_kinds(spec, ["storage", "database", "vector_db"], base_name, "Persistent Volume Claim", "storage", 2)
    
    nodes = []
    edges = []
    
    def add_nodes(comp_list, default_type):
        ids = []
        for c in comp_list:
            nid = clean_node_id(c["name"])
            nodes.append({
                "id": nid,
                "label": c["name"],
                "type": c.get("kind", default_type),
                "brand": None,
                "parent": None
            })
            ids.append(nid)
        return ids
        
    client_ids = add_nodes(clients, "client")
    gateway_ids = add_nodes(gateways, "gateway")
    service_ids = add_nodes(services, "service")
    storage_ids = add_nodes(storages, "storage")
    
    for cid in client_ids:
        for gid in gateway_ids:
            edges.append({"source": cid, "target": gid, "label": "HTTPS Connect"})
            
    for gid in gateway_ids:
        for sid in service_ids:
            edges.append({"source": gid, "target": sid, "label": "Service routing"})
            
    for sid in service_ids:
        for stid in storage_ids:
            edges.append({"source": sid, "target": stid, "label": "Mount volume"})
            
    return {
        "containers": containers,
        "nodes": nodes,
        "edges": edges
    }

def build_ai_pipeline_graph(spec: dict) -> dict:
    """Builds an AI pipeline: Document Loader -> Text Chunker -> Embedding Model -> Vector DB -> Retriever -> LLM."""
    base_name = get_base_name(spec)
    containers = _get_skeleton_containers("ai_pipeline")
    
    clients = get_components_of_kinds(spec, ["client", "external"], base_name, "Web User Client", "client", 1)
    gateways = get_components_of_kinds(spec, ["gateway"], base_name, "Ingestion API gateway", "gateway", 1)
    loaders = get_components_of_kinds(spec, ["service"], base_name, "Document loader daemon", "service", 1)
    chunkers = get_components_of_kinds(spec, ["service"], base_name, "Text chunking service", "service", 1)
    embeddings = get_components_of_kinds(spec, ["llm"], base_name, "Embedding generator model", "llm", 1)
    vector_dbs = get_components_of_kinds(spec, ["vector_db"], base_name, "Vector database (Pinecone)", "vector_db", 1)
    retrievers = get_components_of_kinds(spec, ["service"], base_name, "retriever service", "service", 1)
    llms = get_components_of_kinds(spec, ["llm"], base_name, "LLM foundation model", "llm", 1)
    outputs = get_components_of_kinds(spec, ["client"], base_name, "Output Response UI", "client", 1)
    
    nodes = []
    edges = []
    
    def add_nodes(comp_list, default_type):
        ids = []
        for c in comp_list:
            nid = clean_node_id(c["name"])
            nodes.append({
                "id": nid,
                "label": c["name"],
                "type": c.get("kind", default_type),
                "brand": None,
                "parent": None
            })
            ids.append(nid)
        return ids
        
    client_ids = add_nodes(clients, "client")
    gateway_ids = add_nodes(gateways, "gateway")
    loader_ids = add_nodes(loaders, "service")
    chunker_ids = add_nodes(chunkers, "service")
    emb_ids = add_nodes(embeddings, "llm")
    vdb_ids = add_nodes(vector_dbs, "vector_db")
    ret_ids = add_nodes(retrievers, "service")
    llm_ids = add_nodes(llms, "llm")
    out_ids = add_nodes(outputs, "client")
    
    # Linear Ingestion flow:
    edges.append({"source": loader_ids[0], "target": chunker_ids[0], "label": "Stream text"})
    edges.append({"source": chunker_ids[0], "target": emb_ids[0], "label": "Embed"})
    edges.append({"source": emb_ids[0], "target": vdb_ids[0], "label": "Upsert"})
    
    # Query / Search Retrieval flow:
    edges.append({"source": client_ids[0], "target": gateway_ids[0], "label": "Query prompt"})
    edges.append({"source": gateway_ids[0], "target": ret_ids[0], "label": "Invoke"})
    edges.append({"source": ret_ids[0], "target": vdb_ids[0], "label": "Search index"})
    edges.append({"source": ret_ids[0], "target": llm_ids[0], "label": "Inject context"})
    edges.append({"source": llm_ids[0], "target": out_ids[0], "label": "Deliver response"})
    
    return {
        "containers": containers,
        "nodes": nodes,
        "edges": edges
    }

def build_rag_pipeline_graph(spec: dict) -> dict:
    """Builds a RAG orchestration platform similar to AI Pipeline but with RAG-specific containers."""
    base_name = get_base_name(spec)
    containers = _get_skeleton_containers("rag_pipeline")
    
    clients = get_components_of_kinds(spec, ["client", "external"], base_name, "Chatbot User Interface", "client", 1)
    gateways = get_components_of_kinds(spec, ["gateway"], base_name, "Application Ingress Router", "gateway", 1)
    loaders = get_components_of_kinds(spec, ["service"], base_name, "Document Loader service", "service", 1)
    chunkers = get_components_of_kinds(spec, ["service"], base_name, "Text Splitting Chunker", "service", 1)
    embeddings = get_components_of_kinds(spec, ["llm"], base_name, "Embedding API Model", "llm", 1)
    vector_dbs = get_components_of_kinds(spec, ["vector_db"], base_name, "Vector database (Pinecone)", "vector_db", 1)
    retrievers = get_components_of_kinds(spec, ["service"], base_name, "retrieval Context Engine", "service", 1)
    llms = get_components_of_kinds(spec, ["llm"], base_name, "LLM Chat Generator Model", "llm", 1)
    outputs = get_components_of_kinds(spec, ["client"], base_name, "Formatted Agent Response", "client", 1)
    
    nodes = []
    edges = []
    
    def add_nodes(comp_list, default_type):
        ids = []
        for c in comp_list:
            nid = clean_node_id(c["name"])
            nodes.append({
                "id": nid,
                "label": c["name"],
                "type": c.get("kind", default_type),
                "brand": None,
                "parent": None
            })
            ids.append(nid)
        return ids
        
    client_ids = add_nodes(clients, "client")
    gateway_ids = add_nodes(gateways, "gateway")
    loader_ids = add_nodes(loaders, "service")
    chunker_ids = add_nodes(chunkers, "service")
    emb_ids = add_nodes(embeddings, "llm")
    vdb_ids = add_nodes(vector_dbs, "vector_db")
    ret_ids = add_nodes(retrievers, "service")
    llm_ids = add_nodes(llms, "llm")
    out_ids = add_nodes(outputs, "client")
    
    edges.append({"source": loader_ids[0], "target": chunker_ids[0], "label": "Load data"})
    edges.append({"source": chunker_ids[0], "target": emb_ids[0], "label": "Embed"})
    edges.append({"source": emb_ids[0], "target": vdb_ids[0], "label": "Store"})
    
    edges.append({"source": client_ids[0], "target": gateway_ids[0], "label": "Interact"})
    edges.append({"source": gateway_ids[0], "target": ret_ids[0], "label": "Route query"})
    edges.append({"source": ret_ids[0], "target": vdb_ids[0], "label": "Similarity query"})
    edges.append({"source": ret_ids[0], "target": llm_ids[0], "label": "Pass prompt"})
    edges.append({"source": llm_ids[0], "target": out_ids[0], "label": "Show chat"})
    
    return {
        "containers": containers,
        "nodes": nodes,
        "edges": edges
    }

def build_event_driven_graph(spec: dict) -> dict:
    """Builds an Event-Driven flow: Producers -> Ingress -> Brokers (queues) -> Consumers -> Persistence."""
    base_name = get_base_name(spec)
    containers = _get_skeleton_containers("event_driven")
    
    clients = get_components_of_kinds(spec, ["client", "external"], base_name, "Telemetry Agent Producer", "client", 2)
    gateways = get_components_of_kinds(spec, ["gateway"], base_name, "Ingress broker API Gateway", "gateway", 1)
    queues = get_components_of_kinds(spec, ["queue"], base_name, "Kafka Event Topic", "queue", 2)
    services = get_components_of_kinds(spec, ["service", "container"], base_name, "Consumer worker Daemon", "service", 2)
    databases = get_components_of_kinds(spec, ["database"], base_name, "TimescaleDB Time-series DB", "database", 1)
    
    nodes = []
    edges = []
    
    def add_nodes(comp_list, default_type):
        ids = []
        for c in comp_list:
            nid = clean_node_id(c["name"])
            nodes.append({
                "id": nid,
                "label": c["name"],
                "type": c.get("kind", default_type),
                "brand": None,
                "parent": None
            })
            ids.append(nid)
        return ids
        
    client_ids = add_nodes(clients, "client")
    gateway_ids = add_nodes(gateways, "gateway")
    queue_ids = add_nodes(queues, "queue")
    service_ids = add_nodes(services, "service")
    db_ids = add_nodes(databases, "database")
    
    for cid in client_ids:
        for gid in gateway_ids:
            edges.append({"source": cid, "target": gid, "label": "Publish"})
            
    for gid in gateway_ids:
        for qid in queue_ids:
            edges.append({"source": gid, "target": qid, "label": "Route event"})
            
    if len(queue_ids) >= 2 and len(service_ids) >= 2:
        edges.append({"source": queue_ids[0], "target": service_ids[0], "label": "Consume"})
        edges.append({"source": queue_ids[1], "target": service_ids[1], "label": "Consume"})
    else:
        for qid in queue_ids:
            for sid in service_ids:
                edges.append({"source": qid, "target": sid, "label": "Consume"})
                
    for sid in service_ids:
        for dbid in db_ids:
            edges.append({"source": sid, "target": dbid, "label": "Commit records"})
            
    return {
        "containers": containers,
        "nodes": nodes,
        "edges": edges
    }

def build_transformer_graph(spec: dict) -> dict:
    """Builds a sequential Transformer model pipeline: Tokenizer -> Embeddings -> Attention block -> linear projections."""
    base_name = get_base_name(spec)
    containers = _get_skeleton_containers("transformer")
    
    tokenizers = get_components_of_kinds(spec, ["client"], base_name, "Input Tokenizer", "client", 1)
    embeddings = get_components_of_kinds(spec, ["storage"], base_name, "Positional Embedding weights", "storage", 1)
    attns = get_components_of_kinds(spec, ["service"], base_name, "Multi-Head Attention blocks", "service", 1)
    ffns = get_components_of_kinds(spec, ["service"], base_name, "Feed-Forward subnet", "service", 1)
    norms = get_components_of_kinds(spec, ["service"], base_name, "Layer Normalizer", "service", 1)
    linears = get_components_of_kinds(spec, ["service"], base_name, "Linear Projection Head", "service", 1)
    softmaxes = get_components_of_kinds(spec, ["client"], base_name, "Softmax Output Probabilities", "client", 1)
    
    nodes = []
    edges = []
    
    def add_nodes(comp_list, default_type):
        ids = []
        for c in comp_list:
            nid = clean_node_id(c["name"])
            nodes.append({
                "id": nid,
                "label": c["name"],
                "type": c.get("kind", default_type),
                "brand": None,
                "parent": None
            })
            ids.append(nid)
        return ids
        
    tok_ids = add_nodes(tokenizers, "client")
    emb_ids = add_nodes(embeddings, "storage")
    attn_ids = add_nodes(attns, "service")
    ffn_ids = add_nodes(ffns, "service")
    norm_ids = add_nodes(norms, "service")
    lin_ids = add_nodes(linears, "service")
    soft_ids = add_nodes(softmaxes, "client")
    
    edges.append({"source": tok_ids[0], "target": emb_ids[0], "label": "Tokenize"})
    edges.append({"source": emb_ids[0], "target": attn_ids[0], "label": "Attention weights"})
    edges.append({"source": attn_ids[0], "target": ffn_ids[0], "label": "Feed Forward"})
    edges.append({"source": ffn_ids[0], "target": norm_ids[0], "label": "Normalize"})
    edges.append({"source": norm_ids[0], "target": lin_ids[0], "label": "Project"})
    edges.append({"source": lin_ids[0], "target": soft_ids[0], "label": "Softmax classify"})
    
    return {
        "containers": containers,
        "nodes": nodes,
        "edges": edges
    }

def build_cnn_graph(spec: dict) -> dict:
    """Builds a sequential CNN classifier layers sequence: Input Image -> Conv2D -> MaxPooling -> Flatten -> Softmax."""
    base_name = get_base_name(spec)
    containers = _get_skeleton_containers("cnn")
    
    inputs = get_components_of_kinds(spec, ["storage"], base_name, "Raw Input Image Matrix", "storage", 1)
    conv1s = get_components_of_kinds(spec, ["service"], base_name, "Conv2D Layer (Filters)", "service", 1)
    pool1s = get_components_of_kinds(spec, ["service"], base_name, "MaxPooling Downsampling Layer", "service", 1)
    conv2s = get_components_of_kinds(spec, ["service"], base_name, "Conv2D Layer 2 (Deep features)", "service", 1)
    flattens = get_components_of_kinds(spec, ["service"], base_name, "Flatten Reshaping Layer", "service", 1)
    denses = get_components_of_kinds(spec, ["service"], base_name, "Dense fully-connected layer", "service", 1)
    outputs = get_components_of_kinds(spec, ["client"], base_name, "Softmax Prediction classifier", "client", 1)
    
    nodes = []
    edges = []
    
    def add_nodes(comp_list, default_type):
        ids = []
        for c in comp_list:
            nid = clean_node_id(c["name"])
            nodes.append({
                "id": nid,
                "label": c["name"],
                "type": c.get("kind", default_type),
                "brand": None,
                "parent": None
            })
            ids.append(nid)
        return ids
        
    in_ids = add_nodes(inputs, "storage")
    c1_ids = add_nodes(conv1s, "service")
    p1_ids = add_nodes(pool1s, "service")
    c2_ids = add_nodes(conv2s, "service")
    flat_ids = add_nodes(flattens, "service")
    dense_ids = add_nodes(denses, "service")
    out_ids = add_nodes(outputs, "client")
    
    edges.append({"source": in_ids[0], "target": c1_ids[0], "label": "Convolve"})
    edges.append({"source": c1_ids[0], "target": p1_ids[0], "label": "Max Pool"})
    edges.append({"source": p1_ids[0], "target": c2_ids[0], "label": "Deep Convolve"})
    edges.append({"source": c2_ids[0], "target": flat_ids[0], "label": "Flatten"})
    edges.append({"source": flat_ids[0], "target": dense_ids[0], "label": "Connect"})
    edges.append({"source": dense_ids[0], "target": out_ids[0], "label": "Predict probabilities"})
    
    return {
        "containers": containers,
        "nodes": nodes,
        "edges": edges
    }

def build_mvc_graph(spec: dict) -> dict:
    """Builds a classic MVC structure: Browser View -> Ingress Controller -> DB Models -> DB Storage."""
    base_name = get_base_name(spec)
    containers = _get_skeleton_containers("mvc")
    
    views = get_components_of_kinds(spec, ["client"], base_name, "Web Browser View Client", "client", 1)
    routers = get_components_of_kinds(spec, ["gateway"], base_name, "HTTP request URL Router", "gateway", 1)
    controllers = get_components_of_kinds(spec, ["service"], base_name, "App Controller module", "service", 1)
    view_renders = get_components_of_kinds(spec, ["service"], base_name, "View Template UI renderer", "service", 1)
    models = get_components_of_kinds(spec, ["service"], base_name, "Model ORM Database layer", "service", 1)
    databases = get_components_of_kinds(spec, ["database"], base_name, "Relational Core Database", "database", 1)
    
    nodes = []
    edges = []
    
    def add_nodes(comp_list, default_type):
        ids = []
        for c in comp_list:
            nid = clean_node_id(c["name"])
            nodes.append({
                "id": nid,
                "label": c["name"],
                "type": c.get("kind", default_type),
                "brand": None,
                "parent": None
            })
            ids.append(nid)
        return ids
        
    v_ids = add_nodes(views, "client")
    r_ids = add_nodes(routers, "gateway")
    c_ids = add_nodes(controllers, "service")
    vr_ids = add_nodes(view_renders, "service")
    m_ids = add_nodes(models, "service")
    db_ids = add_nodes(databases, "database")
    
    edges.append({"source": v_ids[0], "target": r_ids[0], "label": "HTTP request"})
    edges.append({"source": r_ids[0], "target": c_ids[0], "label": "Forward"})
    edges.append({"source": c_ids[0], "target": m_ids[0], "label": "Call ORM"})
    edges.append({"source": m_ids[0], "target": db_ids[0], "label": "SQL queries"})
    edges.append({"source": c_ids[0], "target": vr_ids[0], "label": "Pass model payload"})
    edges.append({"source": vr_ids[0], "target": v_ids[0], "label": "HTML output response"})
    
    return {
        "containers": containers,
        "nodes": nodes,
        "edges": edges
    }

def build_hexagonal_graph(spec: dict) -> dict:
    """Builds a Ports & Adapters Hexagonal flow: REST/CLI driving adapters -> Domain Core -> Driven adapters."""
    base_name = get_base_name(spec)
    containers = _get_skeleton_containers("hexagonal")
    
    rest_adapters = get_components_of_kinds(spec, ["client"], base_name, "REST HTTP Driving Adapter", "client", 1)
    cli_adapters = get_components_of_kinds(spec, ["client"], base_name, "CLI Command shell Adapter", "client", 1)
    in_ports = get_components_of_kinds(spec, ["gateway"], base_name, "Inbound Driver Port", "gateway", 1)
    domain_cores = get_components_of_kinds(spec, ["service"], base_name, "Pure Domain Business logic core", "service", 1)
    out_ports = get_components_of_kinds(spec, ["gateway"], base_name, "Outbound Driven Port", "gateway", 1)
    db_adapters = get_components_of_kinds(spec, ["database"], base_name, "Database Adapter repository", "database", 1)
    
    nodes = []
    edges = []
    
    def add_nodes(comp_list, default_type):
        ids = []
        for c in comp_list:
            nid = clean_node_id(c["name"])
            nodes.append({
                "id": nid,
                "label": c["name"],
                "type": c.get("kind", default_type),
                "brand": None,
                "parent": None
            })
            ids.append(nid)
        return ids
        
    ra_ids = add_nodes(rest_adapters, "client")
    ca_ids = add_nodes(cli_adapters, "client")
    ip_ids = add_nodes(in_ports, "gateway")
    dc_ids = add_nodes(domain_cores, "service")
    op_ids = add_nodes(out_ports, "gateway")
    da_ids = add_nodes(db_adapters, "database")
    
    edges.append({"source": ra_ids[0], "target": ip_ids[0], "label": "Translate REST API"})
    edges.append({"source": ca_ids[0], "target": ip_ids[0], "label": "Translate CLI command"})
    edges.append({"source": ip_ids[0], "target": dc_ids[0], "label": "Invoke Core"})
    edges.append({"source": dc_ids[0], "target": op_ids[0], "label": "Trigger Port"})
    edges.append({"source": op_ids[0], "target": da_ids[0], "label": "SQL persist"})
    
    return {
        "containers": containers,
        "nodes": nodes,
        "edges": edges
    }

def build_client_server_graph(spec: dict) -> dict:
    """Builds a classic Client-Server layout: Mobile / Desktop apps -> Socket listener Gateway -> server daemon -> DB."""
    base_name = get_base_name(spec)
    containers = _get_skeleton_containers("client_server")
    
    clients = get_components_of_kinds(spec, ["client"], base_name, "Desktop App Client", "client", 1)
    mobiles = get_components_of_kinds(spec, ["client"], base_name, "Mobile App Client", "client", 1)
    gateways = get_components_of_kinds(spec, ["gateway"], base_name, "TCP Socket Gateway listener", "gateway", 1)
    servers = get_components_of_kinds(spec, ["service"], base_name, "Core System Daemon Server", "service", 1)
    databases = get_components_of_kinds(spec, ["database"], base_name, "Relational Storage Database", "database", 1)
    storages = get_components_of_kinds(spec, ["storage"], base_name, "Shared Local storage folder", "storage", 1)
    
    nodes = []
    edges = []
    
    def add_nodes(comp_list, default_type):
        ids = []
        for c in comp_list:
            nid = clean_node_id(c["name"])
            nodes.append({
                "id": nid,
                "label": c["name"],
                "type": c.get("kind", default_type),
                "brand": None,
                "parent": None
            })
            ids.append(nid)
        return ids
        
    cl_ids = add_nodes(clients, "client")
    mb_ids = add_nodes(mobiles, "client")
    gw_ids = add_nodes(gateways, "gateway")
    sv_ids = add_nodes(servers, "service")
    db_ids = add_nodes(databases, "database")
    st_ids = add_nodes(storages, "storage")
    
    edges.append({"source": cl_ids[0], "target": gw_ids[0], "label": "Establish socket"})
    edges.append({"source": mb_ids[0], "target": gw_ids[0], "label": "Establish socket"})
    edges.append({"source": gw_ids[0], "target": sv_ids[0], "label": "Redirect"})
    edges.append({"source": sv_ids[0], "target": db_ids[0], "label": "SQL commands"})
    edges.append({"source": sv_ids[0], "target": st_ids[0], "label": "Mount assets"})
    
    return {
        "containers": containers,
        "nodes": nodes,
        "edges": edges
    }

def build_layered_graph(spec: dict) -> dict:
    """Builds a classic 3-tier Layered Diagram: UI Client -> Server Router Gateway -> Logic Service -> Data Layer DAO -> DB."""
    base_name = get_base_name(spec)
    containers = _get_skeleton_containers("layered")
    
    uis = get_components_of_kinds(spec, ["client"], base_name, "Presentation Layer UI", "client", 1)
    gateways = get_components_of_kinds(spec, ["gateway"], base_name, "Web Gateway Server Controller", "gateway", 1)
    services = get_components_of_kinds(spec, ["service"], base_name, "Business Logic Service tier", "service", 1)
    daos = get_components_of_kinds(spec, ["service"], base_name, "Data Access Object (DAO)", "service", 1)
    databases = get_components_of_kinds(spec, ["database"], base_name, "Relational Database Engine", "database", 1)
    
    nodes = []
    edges = []
    
    def add_nodes(comp_list, default_type):
        ids = []
        for c in comp_list:
            nid = clean_node_id(c["name"])
            nodes.append({
                "id": nid,
                "label": c["name"],
                "type": c.get("kind", default_type),
                "brand": None,
                "parent": None
            })
            ids.append(nid)
        return ids
        
    ui_ids = add_nodes(uis, "client")
    gw_ids = add_nodes(gateways, "gateway")
    sv_ids = add_nodes(services, "service")
    dao_ids = add_nodes(daos, "service")
    db_ids = add_nodes(databases, "database")
    
    edges.append({"source": ui_ids[0], "target": gw_ids[0], "label": "HTTPS Connect"})
    edges.append({"source": gw_ids[0], "target": sv_ids[0], "label": "Route Request"})
    edges.append({"source": sv_ids[0], "target": dao_ids[0], "label": "Execute Logic"})
    edges.append({"source": dao_ids[0], "target": db_ids[0], "label": "SQL execute"})
    
    return {
        "containers": containers,
        "nodes": nodes,
        "edges": edges
    }

# ==========================================
# SELF HEALING ENGINE
# ==========================================

def self_heal_graph(graph: dict, topology: str) -> dict:
    """Self-heals the graph to meet structural constraints and complexity requirements."""
    containers = graph.setdefault("containers", [])
    nodes = graph.setdefault("nodes", [])
    edges = graph.setdefault("edges", [])
    
    t_key = topology.lower().strip()
    if t_key not in TOPOLOGY_KIND_MAP:
        t_key = "layered"
        
    # Ensure containers exist
    if not containers:
        containers[:] = _get_skeleton_containers(t_key)
        
    default_container_id = containers[-1]["id"] if containers else "default_container"
    if not containers:
        containers.append({"id": "default_container", "label": "System Core", "parent": None})
        
    def get_parent_for_kind(kind: str) -> str:
        k = kind.lower().strip()
        topo_map = TOPOLOGY_KIND_MAP.get(t_key, TOPOLOGY_KIND_MAP["layered"])
        return topo_map.get(k, default_container_id)

    # 1. Clean nodes and ensure valid attributes
    node_ids = set()
    cleaned_nodes = []
    
    for node in nodes:
        if "label" not in node or not node["label"]:
            continue
            
        label = str(node["label"]).strip()
        
        if "id" not in node or not node["id"]:
            node["id"] = re.sub(r'[^a-zA-Z0-9_]', '', label.replace(" ", "_").lower())
            
        nid = node["id"]
        if not nid:
            nid = f"node_{uuid.uuid4().hex[:6]}"
            node["id"] = nid
            
        # Avoid duplicate nodes
        if nid in node_ids:
            continue
            
        node_ids.add(nid)
        
        # Validate node type/kind
        ntype = str(node.get("type", "service")).lower().strip()
        if ntype not in ALLOWED_KINDS:
            ntype = KIND_SYNONYMS.get(ntype, "service")
        node["type"] = ntype
        
        # Assign container parent
        node["parent"] = get_parent_for_kind(ntype)
        cleaned_nodes.append(node)
        
    nodes[:] = cleaned_nodes

    # 2. Enrich graph to at least 20 nodes
    # First: add standard observability/monitoring stack if missing
    obs_nodes = [
        {"id": "prometheus", "label": "Prometheus Collector", "type": "monitoring", "brand": None},
        {"id": "grafana", "label": "Grafana Dashboard", "type": "analytics", "brand": None},
        {"id": "elk", "label": "ELK Log Collector", "type": "logging", "brand": None},
        {"id": "log_agent", "label": "Fluentbit Log Agent", "type": "logging", "brand": None}
    ]
    
    for obs in obs_nodes:
        if len(nodes) >= 20:
            break
        if obs["id"] not in node_ids:
            obs["parent"] = get_parent_for_kind(obs["type"])
            nodes.append(obs)
            node_ids.add(obs["id"])
            
            # Connect them logically to existing nodes
            service_nodes = [n["id"] for n in nodes if n["type"] == "service" and n["id"] != obs["id"]]
            if service_nodes:
                target_service = service_nodes[0]
                if obs["id"] in ["prometheus", "log_agent"]:
                    edges.append({"source": target_service, "target": obs["id"], "label": "Scrape" if obs["id"] == "prometheus" else "Log"})
                elif obs["id"] == "grafana":
                    edges.append({"source": obs["id"], "target": "prometheus", "label": "Query"})
                elif obs["id"] == "elk":
                    edges.append({"source": "log_agent", "target": obs["id"], "label": "Aggregate"})

    # Second: add replica service nodes if still < 20
    db_nodes = [n["id"] for n in nodes if n["type"] in ["database", "vector_db", "storage"]]
    gateway_nodes = [n["id"] for n in nodes if n["type"] == "gateway"]
    
    counter = 1
    while len(nodes) < 20:
        replica_id = f"replica_service_{counter}"
        replica_label = f"App Replica Node {counter}"
        replica_node = {
            "id": replica_id,
            "label": replica_label,
            "type": "service",
            "brand": None,
            "parent": get_parent_for_kind("service")
        }
        nodes.append(replica_node)
        node_ids.add(replica_id)
        
        # Connect replicas to gateways and databases to avoid isolation
        if gateway_nodes:
            edges.append({"source": gateway_nodes[0], "target": replica_id, "label": "Load Balance"})
        if db_nodes:
            edges.append({"source": replica_id, "target": db_nodes[0], "label": "Connect DB"})
            
        counter += 1

    # 3. Truncate nodes to exactly 50 if > 50
    if len(nodes) > 50:
        nodes[:] = nodes[:50]
        node_ids = {n["id"] for n in nodes}

    # 4. Clean edges: remove edges pointing to non-existent nodes
    edges[:] = [e for e in edges if e.get("source") in node_ids and e.get("target") in node_ids]

    # 5. Ensure every node has at least one connection (degree >= 1)
    connected_nodes = {e["source"] for e in edges} | {e["target"] for e in edges}
    
    gateways = [n["id"] for n in nodes if n["type"] == "gateway"]
    services = [n["id"] for n in nodes if n["type"] in ["service", "container", "llm"]]
    databases = [n["id"] for n in nodes if n["type"] in ["database", "vector_db", "cache", "storage", "queue"]]
    
    for node in nodes:
        nid = node["id"]
        ntype = node["type"]
        if nid not in connected_nodes:
            # Connect based on node type
            if ntype in ["client", "external"]:
                target = gateways[0] if gateways else (services[0] if services else None)
                if target:
                    edges.append({"source": nid, "target": target, "label": "HTTPS"})
            elif ntype == "gateway":
                target = services[0] if services else None
                if target:
                    edges.append({"source": nid, "target": target, "label": "Route"})
            elif ntype in ["database", "vector_db", "cache", "storage"]:
                source = services[0] if services else None
                if source:
                    edges.append({"source": source, "target": nid, "label": "Query/Store" if ntype != "cache" else "Read Cache"})
            elif ntype == "queue":
                if len(services) >= 2:
                    edges.append({"source": services[0], "target": nid, "label": "Publish"})
                    edges.append({"source": nid, "target": services[1], "label": "Consume"})
                elif services:
                    edges.append({"source": services[0], "target": nid, "label": "Publish"})
            elif ntype in ["monitoring", "logging", "analytics"]:
                source = services[0] if services else None
                if source:
                    edges.append({"source": source, "target": nid, "label": "Telemetry"})
            else:  # service / container / llm
                if gateways:
                    edges.append({"source": gateways[0], "target": nid, "label": "Forward"})
                if databases:
                    edges.append({"source": nid, "target": databases[0], "label": "Query DB"})
                if not gateways and not databases:
                    other_nodes = [n["id"] for n in nodes if n["id"] != nid]
                    if other_nodes:
                        edges.append({"source": other_nodes[0], "target": nid, "label": "Connect"})
                        
            connected_nodes.add(nid)

    # 6. Enforce Edge Count (10 <= E <= 30) using Greedy Selection
    selected_edges = []
    covered_nodes = set()
    all_edges = list(edges)

    # Pass A: Connect pairs where BOTH source and target are completely uncovered
    for e in all_edges:
        s, t = e["source"], e["target"]
        if s not in covered_nodes and t not in covered_nodes:
            selected_edges.append(e)
            covered_nodes.add(s)
            covered_nodes.add(t)

    # Pass B: Connect edges where at least ONE side is uncovered
    for e in all_edges:
        s, t = e["source"], e["target"]
        if s not in covered_nodes or t not in covered_nodes:
            selected_edges.append(e)
            covered_nodes.add(s)
            covered_nodes.add(t)

    # Pass C: Any remaining node that isn't covered (should be empty since we ensured degree >= 1)
    for n in nodes:
        nid = n["id"]
        if nid not in covered_nodes:
            for e in all_edges:
                if e["source"] == nid or e["target"] == nid:
                    selected_edges.append(e)
                    covered_nodes.add(e["source"])
                    covered_nodes.add(e["target"])
                    break

    # Pass D: Enforce minimum of 10 edges
    if len(selected_edges) < 10:
        used_edges = { (e["source"], e["target"]) for e in selected_edges }
        for e in all_edges:
            if len(selected_edges) >= 10:
                break
            key = (e["source"], e["target"])
            if key not in used_edges:
                selected_edges.append(e)
                used_edges.add(key)
                
        if len(selected_edges) < 10 and services and databases:
            for s in services:
                for db in databases:
                    if len(selected_edges) >= 10:
                        break
                    key = (s, db)
                    if key not in used_edges:
                        selected_edges.append({"source": s, "target": db, "label": "Query"})
                        used_edges.add(key)

    # Pass E: Enforce maximum of 30 edges
    if len(selected_edges) > 30:
        selected_edges[:] = selected_edges[:30]

    edges[:] = selected_edges
    return graph

# ==========================================
# GRAPH ORCHESTRATOR
# ==========================================

def build_graph(
    topology: str, 
    topic: str, 
    slide_title: str = "", 
    slide_content: str = ""
) -> Dict[str, Any]:
    """
    Builds the graph structure (nodes, edges, containers) for the selected topology.
    Topic determines nodes dynamically via LLM extraction, while topology determines the structure.
    """
    print(f"[GRAPH_BUILDER_V3] Building graph for topic: '{topic}' (topology: {topology})")
    
    # 1. Spec Extraction (LLM -> Fallback)
    spec = extract_architecture_spec(topic, topology)
    
    # 2. Route to style-specific graph builder to differentiate layout structure
    t_key = topology.lower().strip()
    
    if t_key == "microservices":
        graph = build_microservice_graph(spec)
    elif t_key == "cloud":
        graph = build_cloud_graph(spec)
    elif t_key == "kubernetes":
        graph = build_kubernetes_graph(spec)
    elif t_key == "ai_pipeline":
        graph = build_ai_pipeline_graph(spec)
    elif t_key == "rag_pipeline":
        graph = build_rag_pipeline_graph(spec)
    elif t_key == "event_driven":
        graph = build_event_driven_graph(spec)
    elif t_key == "transformer":
        graph = build_transformer_graph(spec)
    elif t_key == "cnn":
        graph = build_cnn_graph(spec)
    elif t_key == "mvc":
        graph = build_mvc_graph(spec)
    elif t_key == "hexagonal":
        graph = build_hexagonal_graph(spec)
    elif t_key == "client_server":
        graph = build_client_server_graph(spec)
    else:
        graph = build_layered_graph(spec)
        
    # 3. Self-Healing & Enrichment
    graph = self_heal_graph(graph, topology)
    
    # 4. Post-processing to map shape_hint and tier from spec
    spec_components = spec.get("components", [])
    spec_map = {c["name"].lower().strip(): c for c in spec_components if "name" in c}
    
    for node in graph.get("nodes", []):
        label_lower = node["label"].lower().strip()
        matched_spec = None
        if label_lower in spec_map:
            matched_spec = spec_map[label_lower]
        else:
            for name_key, c in spec_map.items():
                if name_key in label_lower or label_lower in name_key:
                    matched_spec = c
                    break
                    
        if matched_spec:
            node["shape_hint"] = matched_spec.get("shape_hint")
            node["tier"] = matched_spec.get("tier")
            if "kind" in matched_spec:
                node["type"] = matched_spec["kind"]
        else:
            t = node.get("type", "service")
            node["shape_hint"] = t
            node["tier"] = "infra"
            
    return graph
