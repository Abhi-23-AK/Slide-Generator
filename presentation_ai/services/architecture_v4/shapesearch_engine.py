#!/usr/bin/env python3
"""
Shape Search Engine for Architecture V4
======================================
Loads the official Draw.io shape index database and dynamically searches
for matching vector shapes using tag-matching, Soundex phonetic matching,
semantic synonym/alias translation, RapidFuzz token sorting similarity,
and theme-aware library prioritization.
"""

import gzip
import json
import os
import re
import pickle
from typing import List, Dict, Any, Tuple, Set, Optional

# Path to the shape index database and cache
INDEX_PATH = os.path.join(os.path.dirname(__file__), "data", "shape-index.json")
INDEX_PATH_GZ = os.path.join(os.path.dirname(__file__), "data", "shape-index.json.gz")
CACHE_PICKLE_PATH = os.path.join(os.path.dirname(__file__), "cache", "shape-cache.pkl")

# Soundex mapping configurations
_SOUNDEX_MAP = "01230120022455012603010202"   # A..Z digit codes
_TRAIL = re.compile(r"\.*\d*$")               # strip trailing digits/dots before soundex

# In-memory caches for shape list and inverted indexes
_SHAPES_CACHE = None
_TAG_MAP = None
_TITLE_MAP = None
_STYLE_MAP = None
_CATEGORY_MAP = None
_LIBRARY_MAP = None

# Fuzzy match fallbacks if rapidfuzz is not installed
try:
    from rapidfuzz import fuzz
except ImportError:
    class fuzz:
        @staticmethod
        def ratio(s1: str, s2: str) -> float:
            s1, s2 = s1.lower(), s2.lower()
            if not s1 or not s2:
                return 0.0
            common = set(s1) & set(s2)
            return (2.0 * len(common)) / (len(s1) + len(s2)) * 100.0
        
        @staticmethod
        def token_sort_ratio(s1: str, s2: str) -> float:
            w1 = sorted(s1.lower().split())
            w2 = sorted(s2.lower().split())
            return fuzz.ratio(" ".join(w1), " ".join(w2))

# ─── SEMANTIC & SYNONYM REGISTRIES ───
SEMANTIC_ALIASES = {
    "postgres db": "postgresql",
    "sql db": "postgresql",
    "vector db": "pinecone",
    "vector store": "pinecone",
    "cache": "redis",
    "session cache": "redis",
    "queue": "kafka",
    "message broker": "kafka",
    "gateway": "nginx",
    "api gateway": "nginx",
    "container orchestration": "kubernetes",
    "lambda function": "aws lambda"
}

SYNONYM_REGISTRY = {
    "api server": "fastapi",
    "cache layer": "redis",
    "session store": "redis",
    "embedding store": "pinecone",
    "event bus": "kafka",
    "sql database": "postgresql"
}

TECH_REGISTRY = {
    # Frameworks
    "react": "react", "nextjs": "nextjs", "vue": "vue", "angular": "angular", 
    "fastapi": "fastapi", "spring": "spring", "node": "node",
    # Databases
    "redis": "redis", "mongodb": "mongodb", "postgresql": "postgresql", "mysql": "mysql",
    # Vector DBs
    "pinecone": "pinecone", "milvus": "milvus", "qdrant": "qdrant", "weaviate": "weaviate",
    # Queues
    "kafka": "kafka", "rabbitmq": "rabbitmq",
    # AI Models
    "openai": "openai", "claude": "anthropic", "gemini": "google", "deepseek": "deepseek", 
    "llama": "meta", "mistral": "mistral",
    # Cloud
    "aws": "aws", "azure": "azure", "gcp": "gcp",
    # Containers
    "docker": "docker", "kubernetes": "kubernetes",
    # Observability
    "prometheus": "prometheus", "grafana": "grafana", "elk": "elasticsearch", "jaeger": "jaeger"
}

OFFICIAL_LIBRARY_PRIORITIES = {
    "aws": 10,
    "azure": 9,
    "gcp": 8,
    "kubernetes": 7,
    "cisco": 6,
    "elastic": 5,
    "database": 4,
    "general": 1
}

def soundex(name: str) -> str:
    """Computes the 4-character Soundex code for a given word."""
    if not name:
        return ""
    s = [name[0].upper()]
    si = 1
    for ch in name[1:]:
        c = ord(ch.upper()) - 65
        if 0 <= c <= 25 and _SOUNDEX_MAP[c] != "0":
            code = _SOUNDEX_MAP[c]
            if code != s[si - 1]:
                s.append(code)
                si += 1
                if si > 3:
                    break
    s += ["0"] * (4 - len(s))
    return "".join(s[:4])

def split_compound(token: str) -> List[str]:
    """Splits camelCase, PascalCase, snake_case, kebab-case, and numeric/alphanumeric transitions."""
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", token)
    spaced = re.sub(r"([A-Z])([A-Z][a-z])", r"\1 \2", spaced)
    spaced = re.sub(r"([a-zA-Z])(\d)", r"\1 \2", spaced)
    spaced = re.sub(r"(\d)([a-zA-Z])", r"\1 \2", spaced)
    spaced = re.sub(r"[_\-+/.(),;:]", " ", spaced)
    
    return [p.lower() for p in spaced.split() if len(p) >= 2 or p.isdigit()]

def build_indexes(shapes: List[Dict[str, Any]]) -> Tuple[Dict[str, Set[int]], Dict[str, Set[int]], Dict[str, Set[int]], Dict[str, Set[int]], Dict[str, Set[int]]]:
    """Builds multi-field inverted mapping indices for efficient retrieval."""
    tag_map = {}
    title_map = {}
    style_map = {}
    category_map = {}
    library_map = {}
    
    for i, shape in enumerate(shapes):
        # ─── Dynamic Metadata Inference ───
        tags = shape.get("tags", "")
        title = shape.get("title", "")
        style = shape.get("style", "")
        
        tags_lower = tags.lower()
        title_lower = title.lower()
        style_lower = style.lower()
        
        # 1. Infer Library
        library = shape.get("library", "")
        if not library:
            if any(x in tags_lower or x in title_lower or x in style_lower for x in ("aws3", "aws4", "aws", "amazon")):
                library = "aws"
            elif any(x in tags_lower or x in title_lower or x in style_lower for x in ("azure",)):
                library = "azure"
            elif any(x in tags_lower or x in title_lower or x in style_lower for x in ("gcp2", "gcp", "google")):
                library = "gcp"
            elif any(x in tags_lower or x in title_lower or x in style_lower for x in ("kubernetes", "k8s")):
                library = "kubernetes"
            elif any(x in tags_lower or x in title_lower or x in style_lower for x in ("cisco",)):
                library = "cisco"
            elif any(x in tags_lower or x in title_lower or x in style_lower for x in ("elastic",)):
                library = "elastic"
            elif any(x in tags_lower or x in title_lower or x in style_lower for x in ("db", "database", "sql", "nosql")):
                library = "database"
            else:
                library = "general"
            shape["library"] = library

        # 2. Infer Category
        category = shape.get("category", "")
        if not category:
            if any(x in tags_lower or x in title_lower for x in ("gateway", "loadbalancer", "load-balancer", "lb", "proxy", "ingress", "route", "dns", "network")):
                category = "network"
            elif any(x in tags_lower or x in title_lower for x in ("db", "database", "postgres", "sql", "oracle", "warehouse", "vector", "pinecone", "redis", "cache", "memcached")):
                category = "database"
            elif any(x in tags_lower or x in title_lower for x in ("queue", "kafka", "rabbitmq", "bus", "broker")):
                category = "queue"
            elif any(x in tags_lower or x in title_lower for x in ("auth", "cognito", "iam", "security", "vault")):
                category = "security"
            elif any(x in tags_lower or x in title_lower for x in ("monitor", "prometheus", "grafana", "log")):
                category = "monitoring"
            elif any(x in tags_lower or x in title_lower for x in ("client", "user", "browser", "app", "mobile", "admin", "dashboard")):
                category = "client"
            elif any(x in tags_lower or x in title_lower for x in ("s3", "bucket", "storage", "blob", "volume")):
                category = "storage"
            else:
                category = "compute"
            shape["category"] = category
            
        # Tags index
        if tags:
            for token in re.sub(r"[/,()_\-+]", " ", tags_lower).split():
                if len(token) >= 2 or token.isdigit():
                    tag_map.setdefault(token, set()).add(i)
                    sx = soundex(_TRAIL.sub("", token))
                    if sx and sx != token:
                        tag_map.setdefault(sx, set()).add(i)
                        
        # Title index
        if title:
            for token in re.sub(r"[/,()_\-+]", " ", title_lower).split():
                if len(token) >= 2 or token.isdigit():
                    title_map.setdefault(token, set()).add(i)
                    
        # Style index
        if style:
            for p in re.sub(r"[=;]", " ", style_lower).split():
                style_map.setdefault(p, set()).add(i)
                
        # Category index
        if library:
            library_map.setdefault(library.lower(), set()).add(i)
        if category:
            category_map.setdefault(category.lower(), set()).add(i)
            
    return tag_map, title_map, style_map, category_map, library_map

def normalize_query(query: str) -> str:
    """Normalizes the input query by stripping plurals, vendor brands, synonyms, and punctuation."""
    q = query.lower().strip()
    
    # 1. Apply Synonym Registry
    for syn, replacement in SYNONYM_REGISTRY.items():
        q = re.sub(rf"\b{re.escape(syn)}\b", replacement, q)
        
    # 2. Apply Semantic Aliases
    for alias, replacement in SEMANTIC_ALIASES.items():
        q = re.sub(rf"\b{re.escape(alias)}\b", replacement, q)
        
    # 3. Strip vendor prefixes
    for vendor in ("aws", "amazon", "azure", "gcp", "google cloud", "google"):
        if q != vendor:
            q = re.sub(rf"\b{re.escape(vendor)}\b", "", q)
            
    # 4. Strip plurals
    words = []
    for w in q.split():
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            words.append(w[:-1])
        else:
            words.append(w)
    q = " ".join(words)
    
    # 5. Clean punctuation
    q = re.sub(r"[_\-+/.(),;:]", " ", q)
    q = re.sub(r"\s+", " ", q).strip()
    
    return q

def _load_database():
    """Loads shape library index database using persistent disk caching."""
    global _SHAPES_CACHE, _TAG_MAP, _TITLE_MAP, _STYLE_MAP, _CATEGORY_MAP, _LIBRARY_MAP
    if _SHAPES_CACHE is not None:
        return
        
    # Load from persistent cache if available
    if os.path.exists(CACHE_PICKLE_PATH):
        try:
            with open(CACHE_PICKLE_PATH, "rb") as f:
                cached = pickle.load(f)
                _SHAPES_CACHE = cached["shapes"]
                _TAG_MAP = cached["tag_map"]
                _TITLE_MAP = cached["title_map"]
                _STYLE_MAP = cached["style_map"]
                _CATEGORY_MAP = cached["category_map"]
                _LIBRARY_MAP = cached["library_map"]
                return
        except Exception as cache_err:
            print(f"[SHAPE_SEARCH_ENGINE] Pickle cache load failed: {cache_err}. Rebuilding...")
            
    # Load raw file (supports both compressed and uncompressed shapes index)
    shapes_data = None
    if os.path.exists(INDEX_PATH_GZ):
        with gzip.open(INDEX_PATH_GZ, "rt", encoding="utf-8") as f:
            shapes_data = json.load(f)
    elif os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            shapes_data = json.load(f)
    else:
        # Check parent data directory fallback
        fallback_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "architecture_v3", "data")
        f_gz = os.path.join(fallback_dir, "shape-index.json.gz")
        if os.path.exists(f_gz):
            with gzip.open(f_gz, "rt", encoding="utf-8") as f:
                shapes_data = json.load(f)
                
    if shapes_data is None:
        raise FileNotFoundError(f"Draw.io shape index database not found at: {INDEX_PATH_GZ}")
        
    _SHAPES_CACHE = shapes_data
    _TAG_MAP, _TITLE_MAP, _STYLE_MAP, _CATEGORY_MAP, _LIBRARY_MAP = build_indexes(_SHAPES_CACHE)
    
    # Save cache to disk
    try:
        os.makedirs(os.path.dirname(CACHE_PICKLE_PATH), exist_ok=True)
        with open(CACHE_PICKLE_PATH, "wb") as f:
            pickle.dump({
                "shapes": _SHAPES_CACHE,
                "tag_map": _TAG_MAP,
                "title_map": _TITLE_MAP,
                "style_map": _STYLE_MAP,
                "category_map": _CATEGORY_MAP,
                "library_map": _LIBRARY_MAP
            }, f)
    except Exception as cache_save_err:
        print(f"[SHAPE_SEARCH_ENGINE] Failed to save pickle cache: {cache_save_err}")

def get_shape_score(
    shape: Dict[str, Any],
    idx: int,
    query_terms: List[str],
    norm_query: str,
    theme: Optional[str] = None
) -> float:
    """Calculates weighted similarity score incorporating tag, title, fuzzy logic, soundex, and theme."""
    title = shape.get("title", "").lower()
    tags = shape.get("tags", "").lower()
    library = shape.get("library", "").lower()
    category = shape.get("category", "").lower()
    
    score = 0.0
    
    # 1. Exact match hit on title (+10)
    if title == norm_query:
        score += 10.0
        
    # 2. Title word matches (+8 per matched word)
    title_words = set(re.sub(r"[^a-z0-9]", " ", title).split())
    for t in query_terms:
        if t in title_words:
            score += 8.0
        # Title substring similarity (rapidfuzz ratio fallback) (+6)
        ratio = fuzz.ratio(t, title)
        if ratio > 80:
            score += 6.0 * (ratio / 100.0)
            
    # 3. Tag hits (+7 per matched tag)
    tag_words = set(re.sub(r"[^a-z0-9]", " ", tags).split())
    for t in query_terms:
        if t in tag_words:
            score += 7.0
            
    # 4. Token sorting ratio similarity (+5)
    token_overlap = fuzz.token_sort_ratio(norm_query, title)
    if token_overlap > 50:
        score += 5.0 * (token_overlap / 100.0)
        
    # 5. Soundex phonetic matches (+2)
    for t in query_terms:
        sx_t = soundex(_TRAIL.sub("", t))
        for tw in title_words | tag_words:
            sx_tw = soundex(_TRAIL.sub("", tw))
            if sx_t and sx_t == sx_tw:
                score += 2.0
                break
                
    # 6. Library Quality Tie-breakers
    lib_priority = 0
    for official_lib, prio in OFFICIAL_LIBRARY_PRIORITIES.items():
        if official_lib in library:
            lib_priority = max(lib_priority, prio)
            break
    score += lib_priority * 0.5
    
    # 7. Theme-aware prioritization (+15)
    if theme:
        t_clean = theme.lower().strip()
        if t_clean in ("aws", "amazon") and "aws" in library:
            score += 15.0
        elif t_clean == "azure" and "azure" in library:
            score += 15.0
        elif t_clean in ("gcp", "google") and "gcp" in library:
            score += 15.0
        elif t_clean in ("kubernetes", "k8s") and "kubernetes" in library:
            score += 15.0
        elif t_clean in ("aiicons", "ai_dark_neon") and ("ai" in library or "cloud" in library):
            score += 5.0
            
    # 8. Same Category / Technology Registry Reward (+4)
    for tech, vendor in TECH_REGISTRY.items():
        if tech in norm_query:
            if vendor in library or vendor in tags or vendor in category:
                score += 4.0
                
    return score

def search_shapes(query: str, limit: int = 5, theme: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search the official Draw.io shapes database semantically.
    Matches using tag/title intersections, RapidFuzz token sorting, Soundex, and active theme.
    
    Returns a list of dicts:
      [{"style": str, "w": float, "h": float, "title": str, "category": str, "library": str,
        "tags": str, "aspect_ratio": float, "confidence": float, "priority": int}, ...]
    """
    if not query:
        return []
        
    try:
        _load_database()
    except Exception as e:
        print(f"[SHAPE_SEARCH_ENGINE] Failed to load database: {e}")
        return []
        
    norm_query = normalize_query(query)
    
    # Extract terms
    terms = []
    seen_terms = set()
    for raw in norm_query.split():
        subs = split_compound(raw) or ([raw] if len(raw) >= 2 else [])
        for t in subs:
            if t not in seen_terms:
                seen_terms.add(t)
                terms.append(t)
                
    if not terms:
        return []
        
    # Retrieve candidates using inverted index intersections
    candidates = set()
    for t in terms:
        candidates.update(_TAG_MAP.get(t, set()))
        candidates.update(_TITLE_MAP.get(t, set()))
        
        sx = soundex(_TRAIL.sub("", t))
        if sx and sx != t:
            candidates.update(_TAG_MAP.get(sx, set()))
            
    # Score candidates
    scores = {}
    for idx in candidates:
        s = get_shape_score(_SHAPES_CACHE[idx], idx, terms, norm_query, theme)
        if s > 0:
            scores[idx] = s
            
    # Rank candidates
    ranked = sorted(scores.keys(), key=lambda i: (-scores[i], _SHAPES_CACHE[i].get("title", "").lower(), i))
    
    results = []
    for idx in ranked[:limit]:
        shape = _SHAPES_CACHE[idx]
        w = float(shape.get("w", 120))
        h = float(shape.get("h", 60))
        aspect_ratio = w / h if h > 0 else 1.0
        
        # Map theoretical maximum to compute 0.0 - 1.0 confidence score
        raw_score = scores[idx]
        confidence = min(1.0, max(0.0, raw_score / 35.0))
        
        # Priority mapping
        lib_priority = 0
        library_name = shape.get("library", "").lower()
        for official_lib, prio in OFFICIAL_LIBRARY_PRIORITIES.items():
            if official_lib in library_name:
                lib_priority = prio
                break
                
        results.append({
            "style": shape["style"],
            "w": w,
            "h": h,
            "title": shape.get("title", ""),
            "category": shape.get("category", ""),
            "library": shape.get("library", ""),
            "tags": shape.get("tags", ""),
            "aspect_ratio": aspect_ratio,
            "confidence": confidence,
            "priority": lib_priority
        })
        
    return results

def search_multiple_shapes(queries: List[str], limit: int = 5, theme: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Batch search Draw.io shapes for multiple queries, minimizing index loading overhead."""
    try:
        _load_database()
    except Exception as e:
        print(f"[SHAPE_SEARCH_ENGINE] Failed to load database: {e}")
        return {q: [] for q in queries}
        
    results = {}
    for q in queries:
        results[q] = search_shapes(q, limit=limit, theme=theme)
    return results

if __name__ == "__main__":
    import sys
    test_query = "aws lambda" if len(sys.argv) < 2 else sys.argv[1]
    print(f"Semantic Search for: {test_query}")
    res = search_shapes(test_query, limit=5, theme="aws")
    for r in res:
        print(f"- {r['title']} [Lib: {r['library']}] (Conf: {r['confidence']:.2f}, Aspect: {r['aspect_ratio']:.2f})")
        print(f"  Style: {r['style'][:90]}...")
