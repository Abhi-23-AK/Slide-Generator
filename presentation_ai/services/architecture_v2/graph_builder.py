import json
from typing import Dict, Any, List, Optional
from services.llm_client import call_llm

SYSTEM_PROMPT = """You are an expert software architect and systems designer.
Your task is to model a detailed, high-quality architecture diagram as a structured JSON object.
The diagram must represent the selected topology and be highly relevant to the provided slide topic, title, and description.

Return ONLY a valid JSON object matching the schema below. Do not include markdown code block formatting (like ```json), no explanations, just pure JSON.

JSON SCHEMA:
{
  "containers": [
    {
      "id": "unique_container_id",
      "label": "Display Name (e.g. VPC, subnet-1, Pod)",
      "parent": "parent_container_id_or_null"
    }
  ],
  "nodes": [
    {
      "id": "unique_node_id",
      "label": "Display Name (e.g. EC2 Instance, PostgreSQL, OpenAI API)",
      "type": "compute | database | security | network | client | storage",
      "brand": "aws | azure | gcp | kubernetes | openai | claude | gemini | llama | huggingface | langchain | ollama | null",
      "parent": "parent_container_id_or_null"
    }
  ],
  "edges": [
    {
      "source": "source_node_id",
      "target": "target_node_id",
      "label": "Label of connection (e.g. HTTP POST, Sync, SQL Query) or null"
    }
  ]
}

CRITICAL RULES:
1. Ensure all node and edge IDs are unique.
2. Nodes can be inside containers. If a node is inside a container, its 'parent' must match the container's ID.
3. Containers can be nested inside other containers by setting the container's 'parent' to another container's ID.
4. Choose components and labels that are highly technical and specific to the presentation topic. No placeholder terms.
"""

def build_graph(
    topology: str, 
    topic: str, 
    slide_title: str = "", 
    slide_content: str = ""
) -> Dict[str, Any]:
    """
    Builds the graph structure (nodes, edges, containers) for the topology.
    Attempts to call the LLM to get a customized graph, falling back to templates on failure.
    """
    user_prompt = f"""Generate a diagram representing a '{topology}' topology.
Topic: {topic}
Slide Title: {slide_title}
Slide Content: {slide_content}
"""

    try:
        raw_response = call_llm(SYSTEM_PROMPT, user_prompt)
        raw_response = raw_response.strip()
        if raw_response.startswith("```"):
            raw_response = raw_response.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            
        graph = json.loads(raw_response)
        
        # Simple validation of keys
        if "nodes" in graph and isinstance(graph["nodes"], list):
            # Ensure "containers" and "edges" exist
            if "containers" not in graph:
                graph["containers"] = []
            if "edges" not in graph:
                graph["edges"] = []
            print(f"[GRAPH_BUILDER] Successfully built custom graph via LLM (nodes={len(graph['nodes'])}, edges={len(graph['edges'])})")
            return graph
    except Exception as e:
        print(f"[GRAPH_BUILDER] LLM graph builder failed or returned invalid JSON ({e}). Falling back to template.")
        
    return build_fallback_template_graph(topology, topic)


def build_fallback_template_graph(topology: str, topic: str) -> Dict[str, Any]:
    """
    Returns a high-quality static template graph for each topology as a fallback.
    """
    print(f"[GRAPH_BUILDER] Building fallback graph for topology: '{topology}'")
    
    if topology == "cloud":
        return {
            "containers": [
                {"id": "vpc", "label": "Virtual Private Cloud (VPC)", "parent": None},
                {"id": "pub_sub", "label": "Public Subnet", "parent": "vpc"},
                {"id": "priv_sub", "label": "Private Subnet", "parent": "vpc"}
            ],
            "nodes": [
                {"id": "client", "label": "Client / Browser", "type": "client", "brand": None, "parent": None},
                {"id": "lb", "label": "Application Load Balancer", "type": "network", "brand": "aws", "parent": "pub_sub"},
                {"id": "web1", "label": "Web App Instance 1", "type": "compute", "brand": "aws", "parent": "priv_sub"},
                {"id": "web2", "label": "Web App Instance 2", "type": "compute", "brand": "aws", "parent": "priv_sub"},
                {"id": "db", "label": "Aurora PostgreSQL (RDS)", "type": "database", "brand": "aws", "parent": "priv_sub"}
            ],
            "edges": [
                {"source": "client", "target": "lb", "label": "HTTP/2"},
                {"source": "lb", "target": "web1", "label": "Route"},
                {"source": "lb", "target": "web2", "label": "Route"},
                {"source": "web1", "target": "db", "label": "SQL Write"},
                {"source": "web2", "target": "db", "label": "SQL Read"}
            ]
        }
    elif topology == "microservices":
        return {
            "containers": [
                {"id": "ms_env", "label": "Microservices Cluster", "parent": None}
            ],
            "nodes": [
                {"id": "gw", "label": "API Gateway", "type": "network", "brand": "kubernetes", "parent": None},
                {"id": "auth", "label": "Auth Service", "type": "security", "brand": "openai", "parent": "ms_env"},
                {"id": "user", "label": "User Microservice", "type": "compute", "brand": "kubernetes", "parent": "ms_env"},
                {"id": "order", "label": "Order Microservice", "type": "compute", "brand": "kubernetes", "parent": "ms_env"},
                {"id": "db", "label": "Shared Cluster DB", "type": "database", "brand": "gcp", "parent": "ms_env"}
            ],
            "edges": [
                {"source": "gw", "target": "auth", "label": "Validate Token"},
                {"source": "gw", "target": "user", "label": "Route /users"},
                {"source": "gw", "target": "order", "label": "Route /orders"},
                {"source": "user", "target": "db", "label": "JDBC"},
                {"source": "order", "target": "db", "label": "JDBC"}
            ]
        }
    elif topology == "event_driven":
        return {
            "containers": [],
            "nodes": [
                {"id": "p1", "label": "Web Frontend Producer", "type": "client", "brand": None, "parent": None},
                {"id": "p2", "label": "Payment Service Producer", "type": "compute", "brand": None, "parent": None},
                {"id": "broker", "label": "Apache Kafka Message Broker", "type": "network", "brand": "kubernetes", "parent": None},
                {"id": "c1", "label": "Notification Consumer", "type": "compute", "brand": None, "parent": None},
                {"id": "c2", "label": "Analytics Engine Consumer", "type": "compute", "brand": "huggingface", "parent": None}
            ],
            "edges": [
                {"source": "p1", "target": "broker", "label": "Publish Event"},
                {"source": "p2", "target": "broker", "label": "Publish Event"},
                {"source": "broker", "target": "c1", "label": "Subscribe Topic"},
                {"source": "broker", "target": "c2", "label": "Subscribe Topic"}
            ]
        }
    elif topology == "star" or topology == "hub_spoke":
        return {
            "containers": [],
            "nodes": [
                {"id": "hub", "label": "Central Hub Controller", "type": "compute", "brand": "gcp", "parent": None},
                {"id": "spoke1", "label": "Client Service A", "type": "client", "brand": None, "parent": None},
                {"id": "spoke2", "label": "Client Service B", "type": "client", "brand": None, "parent": None},
                {"id": "spoke3", "label": "Client Service C", "type": "client", "brand": None, "parent": None},
                {"id": "spoke4", "label": "Client Service D", "type": "client", "brand": None, "parent": None}
            ],
            "edges": [
                {"source": "spoke1", "target": "hub", "label": "Sync"},
                {"source": "spoke2", "target": "hub", "label": "Sync"},
                {"source": "spoke3", "target": "hub", "label": "Sync"},
                {"source": "spoke4", "target": "hub", "label": "Sync"}
            ]
        }
    elif topology == "ring":
        return {
            "containers": [],
            "nodes": [
                {"id": "n1", "label": "Node Cluster Alpha", "type": "compute", "brand": None, "parent": None},
                {"id": "n2", "label": "Node Cluster Beta", "type": "compute", "brand": None, "parent": None},
                {"id": "n3", "label": "Node Cluster Gamma", "type": "compute", "brand": None, "parent": None},
                {"id": "n4", "label": "Node Cluster Delta", "type": "compute", "brand": None, "parent": None}
            ],
            "edges": [
                {"source": "n1", "target": "n2", "label": "Token Ring"},
                {"source": "n2", "target": "n3", "label": "Token Ring"},
                {"source": "n3", "target": "n4", "label": "Token Ring"},
                {"source": "n4", "target": "n1", "label": "Token Ring"}
            ]
        }
    elif topology == "kubernetes":
        return {
            "containers": [
                {"id": "node", "label": "Kubernetes Worker Node", "parent": None},
                {"id": "pod", "label": "Application Pod Container", "parent": "node"}
            ],
            "nodes": [
                {"id": "ing", "label": "Ingress Controller", "type": "network", "brand": "kubernetes", "parent": None},
                {"id": "svc", "label": "ClusterIP Service", "type": "network", "brand": "kubernetes", "parent": "node"},
                {"id": "app", "label": "Main Web App Pod", "type": "compute", "brand": "kubernetes", "parent": "pod"},
                {"id": "sidecar", "label": "Logging Sidecar Container", "type": "compute", "brand": "kubernetes", "parent": "pod"}
            ],
            "edges": [
                {"source": "ing", "target": "svc", "label": "External HTTP"},
                {"source": "svc", "target": "app", "label": "Internal Routing"},
                {"source": "app", "target": "sidecar", "label": "Shared Vol Logs"}
            ]
        }
    elif topology == "ai_pipeline":
        return {
            "containers": [
                {"id": "stage1", "label": "Preparation", "parent": None},
                {"id": "stage2", "label": "LLM Inference Engine", "parent": None}
            ],
            "nodes": [
                {"id": "data", "label": "Data Source (HuggingFace)", "type": "storage", "brand": "huggingface", "parent": "stage1"},
                {"id": "embed", "label": "Text Embedder (Gemini)", "type": "compute", "brand": "gemini", "parent": "stage1"},
                {"id": "rag", "label": "Vector Database (LangChain)", "type": "database", "brand": "langchain", "parent": "stage1"},
                {"id": "llm", "label": "Claude 3.5 Sonnet API", "type": "compute", "brand": "claude", "parent": "stage2"},
                {"id": "agent", "label": "Self-Correction Loop Agent", "type": "compute", "brand": "langchain", "parent": "stage2"}
            ],
            "edges": [
                {"source": "data", "target": "embed", "label": "Extract"},
                {"source": "embed", "target": "rag", "label": "Vector Insert"},
                {"source": "rag", "target": "llm", "label": "Query Context"},
                {"source": "llm", "target": "agent", "label": "Evaluate Output"},
                {"source": "agent", "target": "llm", "label": "Refine Prompt"}
            ]
        }
    elif topology == "transformer":
        return {
            "containers": [
                {"id": "enc", "label": "Transformer Encoder Block", "parent": None}
            ],
            "nodes": [
                {"id": "input", "label": "Tokenized Input Embeddings", "type": "client", "brand": None, "parent": None},
                {"id": "attn", "label": "Multi-Head Self Attention", "type": "compute", "brand": "huggingface", "parent": "enc"},
                {"id": "norm1", "label": "LayerNorm & Residual Add", "type": "compute", "brand": None, "parent": "enc"},
                {"id": "ffn", "label": "Feed-Forward Neural Net", "type": "compute", "brand": "huggingface", "parent": "enc"},
                {"id": "norm2", "label": "LayerNorm & Residual Add", "type": "compute", "brand": None, "parent": "enc"}
            ],
            "edges": [
                {"source": "input", "target": "attn", "label": "Feed Keys/Query"},
                {"source": "attn", "target": "norm1", "label": "Output Vector"},
                {"source": "norm1", "target": "ffn", "label": "Hidden States"},
                {"source": "ffn", "target": "norm2", "label": "Projection"},
                {"source": "input", "target": "norm1", "label": "Residual Skip"},
                {"source": "norm1", "target": "norm2", "label": "Residual Skip"}
            ]
        }
    elif topology == "cnn":
        return {
            "containers": [],
            "nodes": [
                {"id": "img", "label": "Input Image (224x224x3)", "type": "client", "brand": None, "parent": None},
                {"id": "conv1", "label": "Conv2D Layer (Filters=32)", "type": "compute", "brand": None, "parent": None},
                {"id": "pool1", "label": "MaxPooling2D (Pool=2x2)", "type": "compute", "brand": None, "parent": None},
                {"id": "conv2", "label": "Conv2D Layer (Filters=64)", "type": "compute", "brand": None, "parent": None},
                {"id": "flatten", "label": "Flatten Vector (56x56x64)", "type": "compute", "brand": None, "parent": None},
                {"id": "dense", "label": "Dense Layer (Classes=10)", "type": "compute", "brand": "huggingface", "parent": None}
            ],
            "edges": [
                {"source": "img", "target": "conv1", "label": "5x5 Stride=1"},
                {"source": "conv1", "target": "pool1", "label": "Downsample"},
                {"source": "pool1", "target": "conv2", "label": "3x3 Stride=1"},
                {"source": "conv2", "target": "flatten", "label": "Reshape"},
                {"source": "flatten", "target": "dense", "label": "Softmax Activation"}
            ]
        }
    elif topology == "uml":
        return {
            "containers": [],
            "nodes": [
                {"id": "base", "label": "BaseModel Interface", "type": "storage", "brand": None, "parent": None},
                {"id": "user", "label": "UserClassModel", "type": "storage", "brand": None, "parent": None},
                {"id": "controller", "label": "UserControllerManager", "type": "compute", "brand": None, "parent": None}
            ],
            "edges": [
                {"source": "user", "target": "base", "label": "Inherits / Implements"},
                {"source": "controller", "target": "user", "label": "Instantiates / Manages"}
            ]
        }
    elif topology == "flowchart":
        return {
            "containers": [],
            "nodes": [
                {"id": "start", "label": "Start Execution", "type": "client", "brand": None, "parent": None},
                {"id": "req", "label": "Parse Input Configuration", "type": "compute", "brand": None, "parent": None},
                {"id": "check", "label": "Is Request Token Valid?", "type": "security", "brand": None, "parent": None},
                {"id": "process", "label": "Process & Commit to DB", "type": "compute", "brand": None, "parent": None},
                {"id": "end", "label": "Return Response", "type": "client", "brand": None, "parent": None}
            ],
            "edges": [
                {"source": "start", "target": "req", "label": "Start"},
                {"source": "req", "target": "check", "label": "Verify"},
                {"source": "check", "target": "process", "label": "Yes (Authorized)"},
                {"source": "check", "target": "end", "label": "No (403 Error)"},
                {"source": "process", "target": "end", "label": "Success (200 OK)"}
            ]
        }
    
    # Default fallback: layered
    return {
        "containers": [
            {"id": "lay1", "label": "Presentation Layer", "parent": None},
            {"id": "lay2", "label": "Application Service Layer", "parent": None},
            {"id": "lay3", "label": "Database Storage Layer", "parent": None}
        ],
        "nodes": [
            {"id": "client", "label": "Web Client Interface", "type": "client", "brand": None, "parent": "lay1"},
            {"id": "api", "label": "FastAPI Controller Service", "type": "compute", "brand": None, "parent": "lay2"},
            {"id": "db", "label": "PostgreSQL Store Instance", "type": "database", "brand": None, "parent": "lay3"}
        ],
        "edges": [
            {"source": "client", "target": "api", "label": "HTTP Request"},
            {"source": "api", "target": "db", "label": "SQL Query"}
        ]
    }
