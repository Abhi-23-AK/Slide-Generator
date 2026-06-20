#!/usr/bin/env python3
"""
Relationship Builder for Architecture V4
=======================================
Infers semantic relationships (edges) between extracted components using LLM.
Returns a list of relationships: source, target, label, and layout metadata.
"""

import json
import re
from typing import List, Dict, Any, Tuple, Set
from services.llm_client import call_llm

try:
    from rapidfuzz import process, fuzz
    _HAS_RAPIDFUZZ = True
except ImportError:
    _HAS_RAPIDFUZZ = False

def clean_and_parse_json(text: str) -> dict:
    """Safely extracts and parses JSON from LLM output."""
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
            
    try:
        return json.loads(text)
    except Exception:
        return {}

def detect_hub_node(components: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Detects the primary hub component in the architecture based on semantic centrality."""
    if not components:
        return None
    scores = []
    
    # Pre-calculate dependency frequencies to determine centrality
    dependency_inbound = {}
    dependency_outbound = {}
    for c in components:
        name = c["name"].lower().strip()
        dependency_outbound[name] = set(str(d).lower().strip() for d in c.get("depends_on", []))
        for d in c.get("depends_on", []):
            d_clean = str(d).lower().strip()
            dependency_inbound.setdefault(d_clean, set()).add(name)
            
    for c in components:
        score = 0.0
        kind = c.get("kind", "").lower()
        name = c["name"].lower().strip()
        importance = c.get("importance", "medium").lower()
        
        # Kind weight
        if kind == "gateway":
            score += 10.0
        elif kind == "llm":
            score += 8.0
        elif kind == "queue":
            score += 6.0
        elif kind == "service":
            score += 3.0
            
        # Importance weight
        if importance == "critical":
            score += 5.0
        elif importance == "high":
            score += 3.0
            
        # Centrality (inbound and outbound degree)
        in_degree = len(dependency_inbound.get(name, []))
        out_degree = len(dependency_outbound.get(name, []))
        score += in_degree * 2.0  # highly depended-upon nodes are hubs
        score += out_degree * 1.0  # nodes that orchestrate/call many others
        
        # Shared dependencies / clustering
        if c.get("parent") or c.get("cluster_id"):
            score += 1.0
            
        scores.append((c, score))
        
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[0][0]

def find_semantic_matches(service: Dict[str, Any], components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Finds backing datastores/queues/caches semantically matched to a service."""
    # Candidates are databases, caches, queues, vector_dbs, and storage
    candidates = [c for c in components if c["kind"] in ("database", "cache", "queue", "vector_db", "storage")]
    if not candidates:
        return []
        
    service_name = service["name"].lower()
    
    stop_words = {"service", "api", "app", "server", "microservice", "controller", "handler", "layer", "logic", "core", "client"}
    service_words = [w for w in re.split(r'\W+', service_name) if w and w not in stop_words]
    
    matches = []
    
    for cand in candidates:
        cand_name = cand["name"].lower()
        cand_words = [w for w in re.split(r'\W+', cand_name) if w and w not in stop_words and w not in ("db", "database", "cache", "queue", "store", "broker", "vector")]
        
        # Word overlap check
        shared_words = set(service_words).intersection(set(cand_words))
        if shared_words:
            matches.append((cand, 2.0 + len(shared_words)))
            continue
            
        # RapidFuzz match
        if _HAS_RAPIDFUZZ:
            ratio = fuzz.token_set_ratio(service_name, cand_name)
            if ratio > 75:
                matches.append((cand, ratio / 50.0))
                continue
                
        # Kind compatibility heuristics
        if "auth" in service_name and cand["kind"] in ("database", "cache") and ("auth" in cand_name or "user" in cand_name or "session" in cand_name):
            matches.append((cand, 1.5))
        elif any(x in service_name for x in ("embedding", "vector", "search", "rag")) and cand["kind"] == "vector_db":
            matches.append((cand, 1.8))
        elif any(x in service_name for x in ("notification", "event", "publish", "msg", "alert")) and cand["kind"] == "queue":
            matches.append((cand, 1.8))
            
    # Sort matches by score desc
    matches.sort(key=lambda x: x[1], reverse=True)
    
    matched_nodes = [m[0] for m in matches]
    if matched_nodes:
        return matched_nodes
        
    # Subnet or parenting group local fallback
    local_candidates = [c for c in candidates if c.get("parent") == service.get("parent") or c.get("group") == service.get("group")]
    if local_candidates:
        return [local_candidates[0]]
        
    # Database default sorted by importance
    candidates.sort(key=lambda c: ("critical", "high", "medium", "low").index(c.get("importance", "medium")))
    return [candidates[0]]

def get_semantic_label(source: Dict[str, Any], target: Dict[str, Any], topology: str) -> str:
    """Generates context-aware, semantic labels for edges."""
    s_kind = source.get("kind", "").lower()
    t_kind = target.get("kind", "").lower()
    s_name = source["name"].lower()
    t_name = target["name"].lower()
    
    if topology == "rag":
        if "loader" in s_name or "parser" in s_name:
            return "Load Documents"
        if "chunk" in s_name:
            return "Chunk Text"
        if "embed" in s_name and t_kind == "vector_db":
            return "Store Embeddings"
        if t_kind == "vector_db":
            return "Query Vector DB"
        if t_kind == "llm":
            return "Retrieve Context"
            
    if t_kind == "llm":
        return "Run Inference"
    if t_kind == "vector_db":
        return "Store Embeddings"
        
    if t_kind == "database":
        if "auth" in s_name or "user" in s_name or "claim" in s_name:
            return "Authenticate"
        if "order" in s_name or "pay" in s_name:
            return "Store Order"
        return "Persist Claims" if "policy" in s_name or "claim" in s_name else "Query DB"
    if t_kind == "cache":
        return "Read Cache"
    if t_kind == "queue":
        return "Publish Event"
    if s_kind == "queue":
        return "Consume Event"
    if t_kind == "storage":
        return "Write Logs" if "log" in s_name else "Persist Data"
        
    if s_kind == "client" and t_kind == "gateway":
        return "HTTPS Request"
    if s_kind == "gateway" and t_kind == "service":
        return "Route Request"
        
    if t_kind in ("monitoring", "logging", "analytics"):
        if t_kind == "logging":
            return "Write Logs"
        if t_kind == "monitoring":
            return "Publish Metrics"
        return "Send Telemetry"
        
    return "Connects"

def build_dependency_edges(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Builds edges specified in components' depends_on metadata (source depends on target -> source -> target)."""
    edges = []
    comp_by_name = {c["name"].lower().strip(): c for c in components}
    for c in components:
        deps = c.get("depends_on", [])
        if isinstance(deps, list):
            for dep_name in deps:
                dep_name_clean = str(dep_name).lower().strip()
                tgt = None
                if dep_name_clean in comp_by_name:
                    tgt = comp_by_name[dep_name_clean]
                else:
                    for name, comp in comp_by_name.items():
                        if dep_name_clean in name or name in dep_name_clean:
                            tgt = comp
                            break
                if tgt:
                    edges.append({
                        "source": c["name"],
                        "target": tgt["name"],
                        "label": get_semantic_label(c, tgt, "dependency")
                    })
    return edges

# Programmatic topology-specific builders

def build_microservices_relationships(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    edges = build_dependency_edges(components)
    
    gateways = [c for c in components if c["kind"] == "gateway"]
    clients = [c for c in components if c["kind"] in ("client", "external")]
    services = [c for c in components if c["kind"] == "service"]
    llms = [c for c in components if c["kind"] == "llm"]
    observability = [c for c in components if c["kind"] in ("monitoring", "logging", "analytics")]
    
    gws = gateways if gateways else (clients if clients else [])
    if gws and (services or llms):
        for gw in gws:
            targets = [s for s in services + llms if s.get("flow_order", 2) <= gw.get("flow_order", 1) + 1]
            if not targets:
                targets = [s for s in services + llms if s.get("importance") in ("critical", "high")]
            if not targets:
                targets = services + llms
                
            for t in targets:
                edges.append({
                    "source": gw["name"],
                    "target": t["name"],
                    "label": get_semantic_label(gw, t, "microservices")
                })
                
    for s in services + llms:
        matched = find_semantic_matches(s, components)
        for m in matched:
            edges.append({
                "source": s["name"],
                "target": m["name"],
                "label": get_semantic_label(s, m, "microservices")
            })
            
    if observability and (services or llms):
        obs_targets = [s for s in services + llms if s.get("importance") in ("critical", "high")]
        if not obs_targets and (services or llms):
            obs_targets = [(services + llms)[0]]
            
        for obs in observability:
            for s in obs_targets:
                edges.append({
                    "source": s["name"],
                    "target": obs["name"],
                    "label": get_semantic_label(s, obs, "microservices")
                })
                
    return edges

def build_cloud_relationships(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    edges = build_dependency_edges(components)
    
    clients = [c for c in components if c["kind"] in ("client", "external")]
    gateways = [c for c in components if c["kind"] == "gateway"]
    compute = [c for c in components if c["kind"] in ("service", "container", "llm")]
    security = [c for c in components if c["kind"] == "security"]
    
    if clients and gateways:
        for cl in clients:
            for gw in gateways:
                edges.append({"source": cl["name"], "target": gw["name"], "label": "HTTPS Request"})
    elif clients and compute:
        for cl in clients:
            for cp in compute:
                if cp.get("importance") in ("critical", "high"):
                    edges.append({"source": cl["name"], "target": cp["name"], "label": "Request"})
                    
    if gateways and compute:
        for gw in gateways:
            for cp in compute:
                if cp.get("namespace") == "private-subnet" or cp.get("zone") == "private_zone" or cp.get("importance") in ("critical", "high"):
                    edges.append({"source": gw["name"], "target": cp["name"], "label": "Forward Traffic"})
                    
    for cp in compute:
        matched = find_semantic_matches(cp, components)
        for m in matched:
            edges.append({
                "source": cp["name"],
                "target": m["name"],
                "label": get_semantic_label(cp, m, "cloud")
            })
        for sec in security:
            edges.append({
                "source": cp["name"],
                "target": sec["name"],
                "label": "Authenticate"
            })
            
    return edges

def build_kubernetes_relationships(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    edges = build_dependency_edges(components)
    
    ingress = [c for c in components if c["kind"] == "gateway" or "ingress" in c["name"].lower()]
    pods = [c for c in components if c["kind"] in ("service", "container", "llm") and c not in ingress]
    security = [c for c in components if c["kind"] == "security"]
    
    frontend_pods = [p for p in pods if p.get("tier") == "frontend" or p.get("flow_order", 2) <= 2]
    backend_pods = [p for p in pods if p not in frontend_pods]
    
    if ingress and frontend_pods:
        for ing in ingress:
            for fp in frontend_pods:
                if fp.get("namespace") == ing.get("namespace"):
                    edges.append({"source": ing["name"], "target": fp["name"], "label": "Route Traffic"})
    elif ingress and pods:
        min_flow = min(p.get("flow_order", 2) for p in pods)
        for ing in ingress:
            for p in pods:
                if p.get("flow_order", 2) == min_flow:
                    edges.append({"source": ing["name"], "target": p["name"], "label": "Route Traffic"})
                    
    if frontend_pods and backend_pods:
        for fp in frontend_pods:
            for bp in backend_pods:
                if fp.get("namespace") == bp.get("namespace"):
                    edges.append({"source": fp["name"], "target": bp["name"], "label": "API Call"})
                    
    active_pods = backend_pods if backend_pods else pods
    for pod in active_pods:
        matched = find_semantic_matches(pod, components)
        for m in matched:
            edges.append({
                "source": pod["name"],
                "target": m["name"],
                "label": get_semantic_label(pod, m, "kubernetes")
            })
        for sec in security:
            edges.append({
                "source": pod["name"],
                "target": sec["name"],
                "label": "Access Secrets"
            })
            
    return edges

def build_event_relationships(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    edges = build_dependency_edges(components)
    
    producers = [c for c in components if "producer" in c["name"].lower() or c.get("flow_order", 1) < 3]
    brokers = [c for c in components if c["kind"] == "queue"]
    consumers = [c for c in components if "consumer" in c["name"].lower() or "worker" in c["name"].lower() or c.get("flow_order", 1) > 4]
    
    if not brokers:
        return build_microservices_relationships(components)
        
    for prod in producers:
        if prod in brokers:
            continue
        for broker in brokers:
            edges.append({
                "source": prod["name"],
                "target": broker["name"],
                "label": "Publish Event"
            })
            
    for consumer in consumers:
        if consumer in brokers or consumer in producers:
            continue
        for broker in brokers:
            edges.append({
                "source": broker["name"],
                "target": consumer["name"],
                "label": "Consume Event"
            })
            
    for consumer in consumers:
        if consumer in brokers:
            continue
        matched = find_semantic_matches(consumer, components)
        for m in matched:
            edges.append({
                "source": consumer["name"],
                "target": m["name"],
                "label": get_semantic_label(consumer, m, "event_driven")
            })
            
    return edges

def build_transformer_relationships(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    edges = build_dependency_edges(components)
    
    def get_phase_order(c):
        p = str(c.get("phase", "")).lower()
        if "tokenizer" in p or "token" in p: return 0
        if "input" in p or "embed" in p: return 1
        if "encoder" in p: return 2
        if "decoder" in p: return 3
        if "output" in p or "softmax" in p: return 4
        return 5
        
    def get_stage_order(c):
        s = str(c.get("stage", "")).lower()
        name = c["name"].lower()
        if "token" in s or "token" in name: return 0
        if "embed" in s or "embed" in name: return 1
        if "position" in s or "position" in name: return 2
        if "attention" in s or "attention" in name or "mha" in name: return 3
        if "norm" in s or "norm" in name or "add" in name: return 4
        if "feed" in s or "ffn" in name or "forward" in name: return 5
        if "linear" in s or "linear" in name or "proj" in name: return 6
        if "softmax" in s or "softmax" in name: return 7
        return 8

    sorted_comps = sorted(components, key=lambda c: (get_phase_order(c), get_stage_order(c), c.get("flow_order", 1)))
    
    for i in range(len(sorted_comps) - 1):
        src = sorted_comps[i]
        tgt = sorted_comps[i+1]
        edges.append({
            "source": src["name"],
            "target": tgt["name"],
            "label": "Forward Pass"
        })
        
    encoders = [c for c in components if get_phase_order(c) == 2]
    decoders = [c for c in components if get_phase_order(c) == 3]
    
    if encoders and decoders:
        src = encoders[-1]
        tgt_candidates = [d for d in decoders if "attention" in d["name"].lower() or get_stage_order(d) == 3]
        tgt = tgt_candidates[0] if tgt_candidates else decoders[0]
        
        edges.append({
            "source": src["name"],
            "target": tgt["name"],
            "label": "Key/Value Vector"
        })
        
    return edges

def build_cnn_relationships(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    edges = build_dependency_edges(components)
    
    inputs = [c for c in components if c.get("phase") == "input" or "input" in c["name"].lower()]
    convs = [c for c in components if "conv" in c["name"].lower() or c.get("stage") == "conv"]
    pools = [c for c in components if "pool" in c["name"].lower() or c.get("stage") == "pool"]
    denses = [c for c in components if "dense" in c["name"].lower() or "fc" in c["name"].lower() or "fully" in c["name"].lower()]
    outputs = [c for c in components if c.get("phase") == "output" or "output" in c["name"].lower()]
    
    layers = []
    if inputs: layers.append(inputs)
    if convs: layers.append(convs)
    if pools: layers.append(pools)
    if denses: layers.append(denses)
    if outputs: layers.append(outputs)
    
    for i in range(len(layers) - 1):
        src_layer = layers[i]
        tgt_layer = layers[i+1]
        for src in src_layer:
            edges.append({
                "source": src["name"],
                "target": tgt_layer[0]["name"],
                "label": "Feature Maps" if "conv" in src["name"].lower() else "Forward Pass"
            })
            
    if not edges:
        sorted_comps = sorted(components, key=lambda c: c.get("flow_order", 1))
        for i in range(len(sorted_comps) - 1):
            edges.append({
                "source": sorted_comps[i]["name"],
                "target": sorted_comps[i+1]["name"],
                "label": "Forward Pass"
            })
            
    return edges

def build_ring_relationships(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    edges = build_dependency_edges(components)
    sorted_comps = sorted(components, key=lambda c: (c.get("flow_order", 1), c["name"]))
    n = len(sorted_comps)
    if n > 1:
        for i in range(n):
            edges.append({
                "source": sorted_comps[i]["name"],
                "target": sorted_comps[(i + 1) % n]["name"],
                "label": "Ring Forward"
            })
    return edges

def build_star_relationships(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    edges = build_dependency_edges(components)
    hub = detect_hub_node(components)
    if hub:
        for c in components:
            if c["name"] != hub["name"]:
                if c["kind"] in ("client", "external"):
                    edges.append({
                        "source": c["name"],
                        "target": hub["name"],
                        "label": "Invoke"
                    })
                else:
                    edges.append({
                        "source": hub["name"],
                        "target": c["name"],
                        "label": "Route Request"
                    })
    return edges

def build_hub_spoke_relationships(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    edges = build_dependency_edges(components)
    hub = detect_hub_node(components)
    if hub:
        groups = {}
        for c in components:
            if c["name"] == hub["name"]:
                continue
            grp = c.get("group") or c.get("parent") or "spokes"
            groups.setdefault(grp, []).append(c)
            
        for grp, members in groups.items():
            members.sort(key=lambda x: ("critical", "high", "medium", "low").index(x.get("importance", "medium")))
            rep = members[0]
            edges.append({
                "source": hub["name"],
                "target": rep["name"],
                "label": "Call Cluster"
            })
            for m in members[1:]:
                edges.append({
                    "source": rep["name"],
                    "target": m["name"],
                    "label": "Local Flow"
                })
    return edges

def build_flowchart_relationships(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    edges = build_dependency_edges(components)
    sorted_comps = sorted(components, key=lambda c: c.get("flow_order", 1))
    
    for i in range(len(sorted_comps) - 1):
        src = sorted_comps[i]
        tgt = sorted_comps[i+1]
        
        t_stage = str(tgt.get("stage", "")).lower()
        t_phase = str(tgt.get("phase", "")).lower()
        t_section = str(tgt.get("section", "")).lower()
        
        lbl = "Next Step"
        if "decision" in src["kind"] or "?" in src["name"]:
            if "no" in (t_stage, t_phase, t_section):
                lbl = "No"
            elif "yes" in (t_stage, t_phase, t_section):
                lbl = "Yes"
            elif "retry" in (t_stage, t_phase, t_section):
                lbl = "Retry"
            else:
                tgt_name = tgt["name"].lower()
                if any(x in tgt_name for x in ("fail", "error", "reject", "invalid", "abort")):
                    lbl = "No"
                elif any(x in tgt_name for x in ("retry", "repeat", "loop")):
                    lbl = "Retry"
                else:
                    lbl = "Yes"
        else:
            if "fail" in (t_stage, t_phase, t_section):
                lbl = "Failure"
            elif "success" in (t_stage, t_phase, t_section) or "ok" in (t_stage, t_phase, t_section):
                lbl = "Success"
            else:
                tgt_name = tgt["name"].lower()
                if any(x in tgt_name for x in ("fail", "error", "reject", "invalid")):
                    lbl = "Failure"
                elif any(x in tgt_name for x in ("success", "ok", "valid", "complete")):
                    lbl = "Success"
                    
        edges.append({
            "source": src["name"],
            "target": tgt["name"],
            "label": lbl
        })
        
    return edges

def build_uml_relationships(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    edges = []
    
    parent_index = {}
    group_index = {}
    dependency_index = {}
    comp_by_name = {c["name"].lower().strip(): c for c in components}
    
    for c in components:
        name_clean = c["name"].lower().strip()
        
        parent = c.get("parent")
        if parent:
            parent_index.setdefault(parent.lower().strip(), []).append(c)
            
        group = c.get("group")
        if group:
            group_index.setdefault(group.lower().strip(), []).append(c)
            
        for dep in c.get("depends_on", []):
            dep_clean = str(dep).lower().strip()
            dependency_index.setdefault(dep_clean, []).append(c)
            
    for c in components:
        name_clean = c["name"].lower().strip()
        
        if "impl" in name_clean:
            base_candidate = name_clean.replace("impl", "").strip()
            if base_candidate in comp_by_name:
                edges.append({"source": c["name"], "target": comp_by_name[base_candidate]["name"], "label": "Inheritance"})
        for d in c.get("depends_on", []):
            d_clean = str(d).lower().strip()
            if "interface" in d_clean or "base" in d_clean:
                if d_clean in comp_by_name:
                    edges.append({"source": c["name"], "target": comp_by_name[d_clean]["name"], "label": "Inheritance"})
                    
        parent = c.get("parent")
        if parent and parent.lower().strip() in comp_by_name:
            edges.append({"source": c["name"], "target": comp_by_name[parent.lower().strip()]["name"], "label": "Composition"})
            
        group = c.get("group")
        if group:
            group_clean = group.lower().strip()
            group_members = group_index.get(group_clean, [])
            for m in group_members:
                if m["name"] != c["name"] and c.get("flow_order", 1) < m.get("flow_order", 1):
                    edges.append({"source": c["name"], "target": m["name"], "label": "Aggregation"})
                    
        for dep in c.get("depends_on", []):
            dep_clean = str(dep).lower().strip()
            if dep_clean in comp_by_name:
                edges.append({"source": c["name"], "target": comp_by_name[dep_clean]["name"], "label": "Association"})
                
    if not edges:
        for i in range(len(components) - 1):
            edges.append({
                "source": components[i]["name"],
                "target": components[i+1]["name"],
                "label": "Association"
            })
            
    return edges

def build_ai_pipeline_relationships(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    edges = build_dependency_edges(components)
    
    def get_pipeline_stage_index(c) -> int:
        stage = str(c.get("stage", "")).lower()
        phase = str(c.get("phase", "")).lower()
        section = str(c.get("section", "")).lower()
        name = c["name"].lower()
        
        if "load" in stage or "load" in phase or "load" in name: return 0
        if "parse" in stage or "parse" in phase or "parse" in name: return 1
        if "chunk" in stage or "chunk" in phase or "chunk" in name: return 2
        if "embed" in stage or "embed" in phase or "embed" in name: return 3
        if "vector" in stage or "vector" in phase or "vector" in name or c.get("kind") == "vector_db": return 4
        if "retriev" in stage or "retriev" in phase or "retriev" in name: return 5
        if "llm" in stage or "llm" in phase or "llm" in name or c.get("kind") == "llm": return 6
        if "response" in stage or "output" in phase or "response" in name or c.get("kind") == "client": return 7
        return 8

    sorted_comps = sorted(components, key=lambda c: (get_pipeline_stage_index(c), c.get("flow_order", 1)))
    
    for i in range(len(sorted_comps) - 1):
        src = sorted_comps[i]
        tgt = sorted_comps[i+1]
        lbl = get_semantic_label(src, tgt, "rag")
        edges.append({
            "source": src["name"],
            "target": tgt["name"],
            "label": lbl
        })
        
    return edges

def build_layered_relationships(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    edges = build_dependency_edges(components)
    
    frontend = [c for c in components if c.get("tier") == "frontend"]
    backend = [c for c in components if c.get("tier") == "backend"]
    data = [c for c in components if c.get("tier") == "data"]
    infra = [c for c in components if c.get("tier") == "infra"]
    
    if frontend and backend:
        for f in frontend:
            targets = [b for b in backend if b.get("importance") in ("critical", "high")]
            if not targets:
                targets = backend
            for t in targets:
                edges.append({"source": f["name"], "target": t["name"], "label": "HTTPS API Request"})
                
    if backend and data:
        for b in backend:
            matched = find_semantic_matches(b, components)
            for m in matched:
                edges.append({"source": b["name"], "target": m["name"], "label": get_semantic_label(b, m, "layered")})
                
    if infra:
        for inf in infra:
            targets = [c for c in frontend + backend if c.get("importance") in ("critical", "high")]
            for t in targets:
                edges.append({"source": t["name"], "target": inf["name"], "label": "Publish Telemetry"})
                
    return edges

def build_none_relationships(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    edges = build_dependency_edges(components)
    
    candidates = []
    for i, c1 in enumerate(components):
        for j, c2 in enumerate(components):
            if i == j:
                continue
            if c1.get("flow_order", 1) < c2.get("flow_order", 1):
                candidates.append({
                    "source": c1["name"],
                    "target": c2["name"],
                    "label": get_semantic_label(c1, c2, "none")
                })
                
    for c in candidates:
        classify_and_enrich_edge(c, components, "none")
        c["_score"] = score_edge(c, components, "none")
        
    candidates.sort(key=lambda x: x["_score"], reverse=True)
    
    max_extra = int(1.5 * len(components))
    added = 0
    connected_pairs = set((e["source"].lower(), e["target"].lower()) for e in edges)
    
    for cand in candidates:
        key = (cand["source"].lower(), cand["target"].lower())
        if key not in connected_pairs:
            edges.append(cand)
            connected_pairs.add(key)
            added += 1
            if added >= max_extra:
                break
                
    return edges

TOPOLOGY_RELATIONSHIP_REGISTRY = {
    "microservices": build_microservices_relationships,
    "cloud": build_cloud_relationships,
    "kubernetes": build_kubernetes_relationships,
    "event_driven": build_event_relationships,
    "ring": build_ring_relationships,
    "star": build_star_relationships,
    "hub_spoke": build_hub_spoke_relationships,
    "cnn": build_cnn_relationships,
    "transformer": build_transformer_relationships,
    "flowchart": build_flowchart_relationships,
    "uml": build_uml_relationships,
    "ai_pipeline": build_ai_pipeline_relationships,
    "rag": build_ai_pipeline_relationships,
    "layered": build_layered_relationships,
    "none": build_none_relationships
}

def score_edge(edge: Dict[str, Any], components: List[Dict[str, Any]], topology: str) -> float:
    """Computes a numeric layout suitability score for an edge, optimizing for 15:8."""
    src_name = edge["source"]
    tgt_name = edge["target"]
    
    comp_by_name = {c["name"]: c for c in components}
    src_comp = comp_by_name.get(src_name)
    tgt_comp = comp_by_name.get(tgt_name)
    
    if not src_comp or not tgt_comp:
        return 0.0
        
    s_flow = src_comp.get("flow_order", 1)
    t_flow = tgt_comp.get("flow_order", 1)
    s_parent = src_comp.get("parent")
    t_parent = tgt_comp.get("parent")
    s_group = src_comp.get("group")
    t_group = tgt_comp.get("group")
    s_cluster = src_comp.get("cluster_id")
    t_cluster = tgt_comp.get("cluster_id")
    s_rank_grp = src_comp.get("rank_group")
    t_rank_grp = tgt_comp.get("rank_group")
    s_lane = src_comp.get("lane")
    t_lane = tgt_comp.get("lane")
    s_swimlane = src_comp.get("swimlane")
    t_swimlane = tgt_comp.get("swimlane")
    s_phase = src_comp.get("phase")
    t_phase = tgt_comp.get("phase")
    s_section = src_comp.get("section")
    t_section = tgt_comp.get("section")
    s_stage = src_comp.get("stage")
    t_stage = tgt_comp.get("stage")
    
    score = 0.0
    
    edge_imp = edge.get("importance", "medium")
    if edge_imp == "critical":
        score += 10.0
    elif edge_imp == "high":
        score += 7.0
    elif edge_imp == "medium":
        score += 4.0
    else:
        score += 1.0
        
    if tgt_name in src_comp.get("depends_on", []):
        score += 10.0
        
    if s_parent and s_parent == t_parent:
        score += 5.0
    if s_group and s_group == t_group:
        score += 4.0
    if s_cluster and s_cluster == t_cluster:
        score += 4.0
    if s_phase and s_phase == t_phase:
        score += 3.0
    if s_section and s_section == t_section:
        score += 3.0
    if s_stage and s_stage == t_stage:
        score += 3.0
        
    if edge.get("same_rank"):
        score += 4.0
    if s_rank_grp and s_rank_grp == t_rank_grp:
        score += 3.0
    if s_lane and s_lane == t_lane:
        score += 2.0
    if s_swimlane and s_swimlane == t_swimlane:
        score += 2.0
    if edge.get("local_edge"):
        score += 3.0
    if edge.get("cluster_edge"):
        score += 2.0
        
    if edge.get("cross_cluster"):
        score -= 4.0
    if edge.get("long_edge"):
        score -= 5.0
    if edge.get("back_edge"):
        score -= 8.0
        
    flow_diff = abs(t_flow - s_flow)
    if flow_diff <= 1:
        score += 3.0
    elif flow_diff > 2:
        score -= (flow_diff - 2) * 2.0
        
    return score

def classify_and_enrich_edge(edge: Dict[str, Any], components: List[Dict[str, Any]], topology: str) -> Dict[str, Any]:
    """Classifies edge importance and layout hints for compact widescreen layouts."""
    src_name = edge["source"]
    tgt_name = edge["target"]
    
    comp_by_name = {c["name"]: c for c in components}
    src_comp = comp_by_name.get(src_name)
    tgt_comp = comp_by_name.get(tgt_name)
    
    if not src_comp or not tgt_comp:
        edge.setdefault("importance", "medium")
        edge.setdefault("same_rank", False)
        edge.setdefault("cross_cluster", False)
        edge.setdefault("back_edge", False)
        edge.setdefault("local_edge", True)
        edge.setdefault("long_edge", False)
        edge.setdefault("cluster_edge", False)
        return edge
        
    s_flow = src_comp.get("flow_order", 1)
    t_flow = tgt_comp.get("flow_order", 1)
    s_tier = src_comp.get("tier", "backend")
    t_tier = tgt_comp.get("tier", "backend")
    s_parent = src_comp.get("parent")
    t_parent = tgt_comp.get("parent")
    s_group = src_comp.get("group")
    t_group = tgt_comp.get("group")
    s_cluster = src_comp.get("cluster_id")
    t_cluster = tgt_comp.get("cluster_id")
    
    back_edge = t_flow < s_flow
    local_edge = (s_parent == t_parent) or (s_group == t_group) or (s_cluster == t_cluster)
    cross_cluster = not local_edge
    same_rank = (s_tier == t_tier) or (s_flow == t_flow)
    long_edge = abs(t_flow - s_flow) > 2 and cross_cluster
    cluster_edge = (s_parent != t_parent) and (s_parent is not None or t_parent is not None)
    
    s_imp = src_comp.get("importance", "medium")
    t_imp = tgt_comp.get("importance", "medium")
    
    edge_imp = "medium"
    if tgt_comp.get("kind") in ("monitoring", "logging", "analytics"):
        edge_imp = "low"
    elif src_name in tgt_comp.get("depends_on", []) or tgt_name in src_comp.get("depends_on", []):
        edge_imp = "critical"
    elif s_imp == "critical" and t_imp == "critical":
        edge_imp = "critical"
    elif s_imp in ("critical", "high") and t_imp in ("critical", "high"):
        edge_imp = "high"
    elif s_imp == "low" or t_imp == "low":
        edge_imp = "low"
        
    edge["importance"] = edge_imp
    edge["same_rank"] = same_rank
    edge["cross_cluster"] = cross_cluster
    edge["back_edge"] = back_edge
    edge["local_edge"] = local_edge
    edge["long_edge"] = long_edge
    edge["cluster_edge"] = cluster_edge
    
    return edge

def prune_and_control_edges(
    edges: List[Dict[str, Any]], 
    components: List[Dict[str, Any]], 
    topology: str
) -> List[Dict[str, Any]]:
    """Enforces degree limits, cycle policies, and clips edge density to 10-30 edges."""
    seen = set()
    deduped = []
    for e in edges:
        key = (e["source"].lower().strip(), e["target"].lower().strip())
        if key not in seen and key[0] != key[1]:
            seen.add(key)
            deduped.append(e)
            
    for e in deduped:
        classify_and_enrich_edge(e, components, topology)
        
    acyclic_topologies = {"cnn", "transformer", "rag", "ai_pipeline", "layered"}
    if topology in acyclic_topologies:
        deduped = [e for e in deduped if not e.get("back_edge", False)]
        
    for e in deduped:
        e["_score"] = score_edge(e, components, topology)
        
    deduped.sort(key=lambda x: x["_score"], reverse=True)
    
    comp_by_name = {c["name"].lower().strip(): c for c in components}
    
    default_max_out = 3
    default_max_in = 3
    
    if topology == "ring":
        default_max_out, default_max_in = 1, 1
    elif topology in ("cnn", "transformer"):
        default_max_out, default_max_in = 2, 2
    elif topology == "star":
        default_max_out, default_max_in = 1, 1
        
    hub = detect_hub_node(components)
    hub_name_clean = hub["name"].lower().strip() if hub else None
    
    out_degree = {c["name"].lower().strip(): [] for c in components}
    in_degree = {c["name"].lower().strip(): [] for c in components}
    
    allowed_edges = []
    
    for e in deduped:
        s_name = e["source"].lower().strip()
        t_name = e["target"].lower().strip()
        
        src_comp = comp_by_name.get(s_name)
        tgt_comp = comp_by_name.get(t_name)
        if not src_comp or not tgt_comp:
            continue
            
        s_kind = src_comp.get("kind", "").lower()
        t_kind = tgt_comp.get("kind", "").lower()
        
        is_src_hub = hub_name_clean and hub_name_clean == s_name
        is_tgt_hub = hub_name_clean and hub_name_clean == t_name
        
        src_limit = len(components) if (is_src_hub or s_kind == "gateway") else default_max_out
        tgt_limit = len(components) if (is_tgt_hub or t_kind in ("database", "vector_db", "cache", "queue")) else default_max_in
        
        if len(out_degree[s_name]) < src_limit and len(in_degree[t_name]) < tgt_limit:
            out_degree[s_name].append(e)
            in_degree[t_name].append(e)
            allowed_edges.append(e)
            
    if len(allowed_edges) > 30:
        connected_nodes = set()
        pruned_list = []
        for e in allowed_edges:
            s = e["source"].lower().strip()
            t = e["target"].lower().strip()
            if len(pruned_list) < 30 or s not in connected_nodes or t not in connected_nodes:
                pruned_list.append(e)
                connected_nodes.add(s)
                connected_nodes.add(t)
        allowed_edges = pruned_list[:30]
        
    return allowed_edges

def build_relationships(components: List[Dict[str, Any]], topic: str, topology: str = None, visual_style: str = None) -> List[Dict[str, Any]]:
    """
    Calls the LLM to infer the relationships between the components.
    Falls back to a topology-specific relationship builder if the LLM call fails.
    visual_style is explicitly passed instead of relying on global state.
    """
    topology = str(topology).lower().strip() if topology else "none"

    if topology not in TOPOLOGY_RELATIONSHIP_REGISTRY:
        topology = "none"
        
    component_names = [c["name"] for c in components]
    component_details = []
    
    for c in components:
        component_details.append({
            "name": c["name"],
            "kind": c["kind"],
            "tier": c.get("tier", "backend"),
            "importance": c.get("importance", "medium"),
            "depends_on": c.get("depends_on", []),
            "flow_order": c.get("flow_order", 1),
            "parent": c.get("parent"),
            "group": c.get("group"),
            "cluster_id": c.get("cluster_id"),
            "rank_group": c.get("rank_group"),
            "lane": c.get("lane"),
            "section": c.get("section"),
            "zone": c.get("zone"),
            "namespace": c.get("namespace"),
            "swimlane": c.get("swimlane"),
            "phase": c.get("phase"),
            "stage": c.get("stage")
        })

    system_prompt = (
        "You are an expert systems architect.\n"
        "Your task is to define logical/architectural connections and data flows (relationships) "
        "between the given list of system components.\n\n"
        "GUIDELINES FOR CONNECTING COMPONENTS:\n"
        "- Connect components logically following the requested topology rules.\n"
        "- Use the components' `depends_on` metadata where specified.\n"
        "- Use the components' `flow_order` to determine connection direction (lower flow_order -> higher flow_order).\n"
        "- Keep connections local within the same `parent`, `group`, or `cluster_id` where appropriate to avoid layout clutter.\n"
        "- Use layout metadata fields (like `rank_group`, `cluster_id`, `lane`, `swimlane`, `phase`, `section`, `stage`) to keep connections localized, enabling clean, compact 15:8 widescreen layouts and minimizing long cross-cluster lines.\n"
        "- Do not connect everything; prune unnecessary links to keep the diagram clean.\n"
        "- Every source and target MUST exactly match one of the component names provided in the list.\n\n"
        "TOPOLOGY CONNECTION RULES:\n"
        "- RAG / AI Pipeline: Loader -> Chunker -> Embedder -> VectorDB -> Retriever -> LLM -> UI. No cycles.\n"
        "- CNN: Input -> Conv -> Pool -> Dense -> Output. Strict pipeline. No cycles.\n"
        "- Transformer: Embedding -> Encoder -> Attention -> Decoder -> Output. Strict pipeline. No cycles.\n"
        "- Event Driven: Producer -> Broker -> Consumer. Consumers query databases.\n"
        "- Star: Central Hub connects to Outer Spokes.\n"
        "- Ring: Connect in a circular loop: 0 -> 1 -> 2 -> ... -> N -> 0.\n"
        "- Hub-Spoke: Hub connects to outer clusters/groups.\n"
        "- Flowchart: Sequential flow, decision nodes branching into multiple targets.\n"
        "- UML: Associations, Compositions, and Inheritance lines.\n"
        "- Cloud: Public subnet -> Private subnet -> Database/restricted subnet.\n"
        "- Microservices: Gateway/Load Balancer -> Microservices -> Databases/Caches/Queues.\n"
        "- Kubernetes: Ingress -> Pods -> Volumes/Secrets/ConfigMaps.\n"
        "- Layered: Presentation -> Business Logic -> Data Access layers.\n\n"
        "Return only a JSON object matching this schema:\n"
        "{\n"
        "  \"relationships\": [\n"
        "    {\n"
        "      \"source\": \"[Exact Component Name from list]\",\n"
        "      \"target\": \"[Exact Component Name from list]\",\n"
        "      \"label\": \"[Action label, e.g. Authenticate, Persist claims, Store embeddings, Query vector store, Publish event, Consume event, Route request]\"\n"
        "    }\n"
        "  ]\n"
        "}"
    )

    user_prompt = (
        f"Topic: {topic}\n"
        f"Topology: {topology}\n"
        f"Components List with Metadata: {json.dumps(component_details, indent=2)}"
    )

    try:
        print(f"[RELATIONSHIP_BUILDER] Querying LLM to infer relationships for: {topic} (Topology: {topology})")
        raw_response = call_llm(system_prompt, user_prompt)
        spec = clean_and_parse_json(raw_response)
        
        relationships = spec.get("relationships", [])
        if relationships and isinstance(relationships, list):
            cleaned = []
            for r in relationships:
                if isinstance(r, dict) and "source" in r and "target" in r:
                    src = str(r["source"]).strip()
                    tgt = str(r["target"]).strip()
                    if src in component_names and tgt in component_names:
                        cleaned.append({
                            "source": src,
                            "target": tgt,
                            "label": str(r.get("label", "Request")).strip()
                        })
            if cleaned:
                return prune_and_control_edges(cleaned, components, topology)
    except Exception as e:
        print(f"[RELATIONSHIP_BUILDER] LLM relationship inference failed: {e}. Falling back to topology-specific rules.")

    print(f"[RELATIONSHIP_BUILDER] Executing fallback builder for topology: {topology}")
    fallback_builder = TOPOLOGY_RELATIONSHIP_REGISTRY.get(topology, build_none_relationships)
    fallback_edges = fallback_builder(components)
    return prune_and_control_edges(fallback_edges, components, topology)
