import os
import re
import urllib.parse
import requests
from typing import Optional

from services.architecture_v3.style_engine import get_current_style, should_suppress_logos

# Mapping of brand names to their standard remote logo URLs (high-quality PNG or SVG)
LOGO_REMOTE_URLS = {
    # ── AI / LLM ──────────────────────────────────────
    "openai": "https://cdn.jsdelivr.net/gh/gilbarbara/logos@master/logos/openai-icon.svg",
    "claude": "https://cdn.jsdelivr.net/gh/gilbarbara/logos@master/logos/claude.svg",
    "gemini": "https://cdn.jsdelivr.net/gh/gilbarbara/logos@master/logos/google-gemini.svg",
    "mistral": "https://cdn.jsdelivr.net/gh/gilbarbara/logos@master/logos/mistral-ai-icon.svg",
    "deepseek": "https://www.vectorlogo.zone/logos/deepseek/deepseek-icon.svg",
    "ollama": "https://cdn.jsdelivr.net/gh/gilbarbara/logos@master/logos/ollama.svg",
    "cohere": "https://cdn.jsdelivr.net/gh/gilbarbara/logos@master/logos/cohere-icon.svg",
    "huggingface": "https://cdn.jsdelivr.net/gh/gilbarbara/logos@master/logos/hugging-face-icon.svg",

    # ── AI Frameworks ─────────────────────────────────
    "langchain": "https://raw.githubusercontent.com/langchain-ai/langchain/master/docs/static/img/langchain_logo.png",
    "llamaindex": "https://www.vectorlogo.zone/logos/llamaindex/llamaindex-icon.svg",

    # ── Vector / Data Stores ──────────────────────────
    "pinecone": "https://cdn.jsdelivr.net/gh/gilbarbara/logos@master/logos/pinecone.svg",
    "redis": "https://www.vectorlogo.zone/logos/redis/redis-icon.svg",
    "postgresql": "https://www.vectorlogo.zone/logos/postgresql/postgresql-icon.svg",
    "mongodb": "https://www.vectorlogo.zone/logos/mongodb/mongodb-icon.svg",
    "dynamodb": "https://cdn.jsdelivr.net/gh/gilbarbara/logos@master/logos/aws-dynamodb.svg",
    "elasticsearch": "https://www.vectorlogo.zone/logos/elastic/elastic-icon.svg",
    "mysql": "https://www.vectorlogo.zone/logos/mysql/mysql-icon.svg",
    "mariadb": "https://www.vectorlogo.zone/logos/mariadb/mariadb-icon.svg",
    "sqlite": "https://www.vectorlogo.zone/logos/sqlite/sqlite-icon.svg",
    "cassandra": "https://www.vectorlogo.zone/logos/apache_cassandra/apache_cassandra-icon.svg",
    "snowflake": "https://www.vectorlogo.zone/logos/snowflake/snowflake-icon.svg",
    "memcached": "https://www.vectorlogo.zone/logos/memcached/memcached-icon.svg",
    "etcd": "https://www.vectorlogo.zone/logos/etcd/etcd-icon.svg",

    # ── Infrastructure / Containers / CI-CD ───────────
    "docker": "https://www.vectorlogo.zone/logos/docker/docker-icon.svg",
    "kubernetes": "https://www.vectorlogo.zone/logos/kubernetes/kubernetes-icon.svg",
    "nginx": "https://www.vectorlogo.zone/logos/nginx/nginx-icon.svg",
    "kafka": "https://www.vectorlogo.zone/logos/apache_kafka/apache_kafka-icon.svg",
    "rabbitmq": "https://www.vectorlogo.zone/logos/rabbitmq/rabbitmq-icon.svg",
    "activemq": "https://www.vectorlogo.zone/logos/apache_activemq/apache_activemq-icon.svg",
    "jenkins": "https://www.vectorlogo.zone/logos/jenkins/jenkins-icon.svg",
    "github": "https://www.vectorlogo.zone/logos/github/github-icon.svg",
    "gitlab": "https://www.vectorlogo.zone/logos/gitlab/gitlab-icon.svg",
    "argocd": "https://www.vectorlogo.zone/logos/argoproj/argoproj-icon.svg",
    "terraform": "https://www.vectorlogo.zone/logos/terraform/terraform-icon.svg",

    # ── Gateway / Proxy / Service Mesh ─────────────────
    "kong": "https://www.vectorlogo.zone/logos/kong/kong-icon.svg",
    "envoy": "https://www.vectorlogo.zone/logos/envoyproxy/envoyproxy-icon.svg",
    "traefik": "https://www.vectorlogo.zone/logos/traefik/traefik-icon.svg",
    "haproxy": "https://www.vectorlogo.zone/logos/haproxy/haproxy-icon.svg",
    "istio": "https://www.vectorlogo.zone/logos/istio/istio-icon.svg",
    "linkerd": "https://www.vectorlogo.zone/logos/linkerd/linkerd-icon.svg",

    # ── Cloud Providers ───────────────────────────────
    "aws": "https://www.vectorlogo.zone/logos/amazon_aws/amazon_aws-icon.svg",
    "azure": "https://www.vectorlogo.zone/logos/microsoft_azure/microsoft_azure-icon.svg",
    "gcp": "https://www.vectorlogo.zone/logos/google_cloud/google_cloud-icon.svg",

    # ── AWS Services ──────────────────────────────────
    "route53": "https://cdn.jsdelivr.net/gh/gilbarbara/logos@master/logos/aws-route53.svg",
    "cloudfront": "https://cdn.jsdelivr.net/gh/gilbarbara/logos@master/logos/aws-cloudfront.svg",
    "lambda": "https://cdn.jsdelivr.net/gh/gilbarbara/logos@master/logos/aws-lambda.svg",
    "api_gateway": "https://cdn.jsdelivr.net/gh/gilbarbara/logos@master/logos/aws-api-gateway.svg",
    "cognito": "https://cdn.jsdelivr.net/gh/gilbarbara/logos@master/logos/aws-cognito.svg",
    "rds": "https://cdn.jsdelivr.net/gh/gilbarbara/logos@master/logos/aws-rds.svg",
    "s3": "https://cdn.jsdelivr.net/gh/gilbarbara/logos@master/logos/aws-s3.svg",

    # ── Monitoring / Observability ────────────────────
    "prometheus": "https://www.vectorlogo.zone/logos/prometheusio/prometheusio-icon.svg",
    "grafana": "https://www.vectorlogo.zone/logos/grafana/grafana-icon.svg",
    "elk": "https://www.vectorlogo.zone/logos/elastic/elastic-icon.svg",
    "kibana": "https://www.vectorlogo.zone/logos/elasticco_kibana/elasticco_kibana-icon.svg",
    "logstash": "https://www.vectorlogo.zone/logos/elasticco_logstash/elasticco_logstash-icon.svg",
    "fluentbit": "https://www.vectorlogo.zone/logos/fluentbit/fluentbit-icon.svg",
    "fluentd": "https://www.vectorlogo.zone/logos/fluentd/fluentd-icon.svg",
    "jaeger": "https://www.vectorlogo.zone/logos/jaegertracing/jaegertracing-icon.svg",

    # ── Generic Roles / Integration Logos ─────────────
    "stripe": "https://www.vectorlogo.zone/logos/stripe/stripe-icon.svg",
    "auth0": "https://www.vectorlogo.zone/logos/auth0/auth0-icon.svg",
    "jwt": "https://www.vectorlogo.zone/logos/jwt/jwt-icon.svg",
    "sendgrid": "https://www.vectorlogo.zone/logos/sendgrid/sendgrid-icon.svg",
    "chrome": "https://cdn.jsdelivr.net/gh/gilbarbara/logos@master/logos/chrome.svg",
    "android": "https://cdn.jsdelivr.net/gh/gilbarbara/logos@master/logos/android-icon.svg",
    "apple": "https://cdn.jsdelivr.net/gh/gilbarbara/logos@master/logos/apple.svg",
    "shopify": "https://www.vectorlogo.zone/logos/shopify/shopify-icon.svg",
    "gravatar": "https://www.vectorlogo.zone/logos/gravatar/gravatar-icon.svg",
    "twilio": "https://www.vectorlogo.zone/logos/twilio/twilio-icon.svg",

    # ── Programming / Frameworks ──────────────────────
    "python": "https://www.vectorlogo.zone/logos/python/python-icon.svg",
    "nodejs": "https://www.vectorlogo.zone/logos/nodejs/nodejs-icon.svg",
    "react": "https://www.vectorlogo.zone/logos/reactjs/reactjs-icon.svg",
    "fastapi": "https://cdn.jsdelivr.net/gh/gilbarbara/logos@master/logos/fastapi-icon.svg",
    "tensorflow": "https://www.vectorlogo.zone/logos/tensorflow/tensorflow-icon.svg",
    "pytorch": "https://www.vectorlogo.zone/logos/pytorch/pytorch-icon.svg",
    "django": "https://www.vectorlogo.zone/logos/djangoproject/djangoproject-icon.svg",
    "flask": "https://www.vectorlogo.zone/logos/pocoo_flask/pocoo_flask-icon.svg",
    "spring": "https://www.vectorlogo.zone/logos/springio/springio-icon.svg",
    "golang": "https://www.vectorlogo.zone/logos/golang/golang-icon.svg",
    "rust": "https://www.vectorlogo.zone/logos/rust-lang/rust-lang-icon.svg",
    "java": "https://www.vectorlogo.zone/logos/java/java-icon.svg",
    "dotnet": "https://www.vectorlogo.zone/logos/microsoft_net/microsoft_net-icon.svg",
}

# Fuzzy matching of terms in node labels to standard brands
BRAND_PATTERNS = {
    # Generic Roles & Integrations
    r'\b(stripe|payment|payments|billing|checkout|pay)\b': "stripe",
    r'\b(auth0|login|keycloak)\b': "auth0",
    r'\b(jwt|token|jwt-auth|auth-service|auth)\b': "jwt",
    r'\b(sendgrid|email|mail|notification|mailer|notifications)\b': "sendgrid",
    r'\b(browser|web|chrome|frontend-client|webapp|web-client|web-interface)\b': "chrome",
    r'\b(android|mobile|mobile-app|phone|mobile-client)\b': "android",
    r'\b(apple|ios|macos)\b': "apple",
    r'\b(shopify|shop|catalog|store|cart|order|orders|product|products|checkout-service)\b': "shopify",
    r'\b(user|profile|customer|member|client|users)\b': "gravatar",
    r'\b(twilio|sms|text-message)\b': "twilio",

    # AI / LLM
    r'\b(openai|chatgpt|gpt)\b': "openai",
    r'\b(claude|anthropic)\b': "claude",
    r'\b(gemini|google-gemini)\b': "gemini",
    r'\b(mistral)\b': "mistral",
    r'\b(deepseek)\b': "deepseek",
    r'\b(ollama)\b': "ollama",
    r'\b(cohere)\b': "cohere",
    r'\b(huggingface|hugging-face|hf-hub)\b': "huggingface",

    # AI Frameworks
    r'\b(langchain|agent|agents)\b': "langchain",
    r'\b(llamaindex|llama-index)\b': "llamaindex",

    # Vector / Data stores
    r'\b(pinecone|vector-store|vector-db)\b': "pinecone",
    r'\b(redis|cache|keyvalue)\b': "redis",
    r'\b(postgres|postgresql|sql-db)\b': "postgresql",
    r'\b(mongodb|mongo|document-db)\b': "mongodb",
    r'\b(dynamodb|dynamo)\b': "dynamodb",
    r'\b(elasticsearch|elastic-search|elastic)\b': "elasticsearch",
    r'\b(mysql)\b': "mysql",
    r'\b(mariadb)\b': "mariadb",
    r'\b(sqlite)\b': "sqlite",
    r'\b(cassandra)\b': "cassandra",
    r'\b(snowflake)\b': "snowflake",
    r'\b(memcached)\b': "memcached",
    r'\b(etcd)\b': "etcd",

    # Infrastructure / CI-CD
    r'\b(docker|containerize)\b': "docker",
    r'\b(kubernetes|k8s|pod|deployments|ingress)\b': "kubernetes",
    r'\b(nginx|ingress-nginx|reverse-proxy)\b': "nginx",
    r'\b(kafka|event-bus|event-hub)\b': "kafka",
    r'\b(rabbitmq)\b': "rabbitmq",
    r'\b(activemq)\b': "activemq",
    r'\b(jenkins)\b': "jenkins",
    r'\b(github)\b': "github",
    r'\b(gitlab)\b': "gitlab",
    r'\b(argocd|argo-cd|argo)\b': "argocd",
    r'\b(terraform)\b': "terraform",

    # Gateways / Proxies / Service Meshes
    r'\b(kong)\b': "kong",
    r'\b(envoy|envoyproxy)\b': "envoy",
    r'\b(traefik)\b': "traefik",
    r'\b(haproxy)\b': "haproxy",
    r'\b(istio)\b': "istio",
    r'\b(linkerd)\b': "linkerd",

    # Cloud
    r'\b(aws|amazon)\b': "aws",
    r'\b(azure|microsoft)\b': "azure",
    r'\b(gcp|google-cloud|google)\b': "gcp",

    # AWS services (dns is removed from brand patterns to be style-fallback dependent)
    r'\b(route53|route-53)\b': "route53",
    r'\b(cloudfront|cdn)\b': "cloudfront",
    r'\b(lambda|serverless)\b': "lambda",
    r'\b(api-gateway|apigateway)\b': "api_gateway",
    r'\b(cognito|user-pool)\b': "cognito",
    r'\b(rds|relational-db)\b': "rds",
    r'\b(s3|object-storage|bucket)\b': "s3",

    # Monitoring
    r'\b(prometheus|prom)\b': "prometheus",
    r'\b(grafana|dashboard)\b': "grafana",
    r'\b(elk|elastic-stack)\b': "elk",
    r'\b(kibana)\b': "kibana",
    r'\b(logstash)\b': "logstash",
    r'\b(fluentbit|fluent-bit)\b': "fluentbit",
    r'\b(fluentd)\b': "fluentd",
    r'\b(jaeger)\b': "jaeger",

    # Programming (note nodejs matches exactly, avoiding generic node mapping)
    r'\b(python)\b': "python",
    r'\b(nodejs)\b': "nodejs",
    r'\b(react|reactjs)\b': "react",
    r'\b(fastapi)\b': "fastapi",
    r'\b(tensorflow|tf)\b': "tensorflow",
    r'\b(pytorch|torch)\b': "pytorch",
    r'\b(django)\b': "django",
    r'\b(flask)\b': "flask",
    r'\b(spring|springboot)\b': "spring",
    r'\b(golang|go)\b': "golang",
    r'\b(rust)\b': "rust",
    r'\b(java)\b': "java",
    r'\b(dotnet|\.net)\b': "dotnet",
}

# Kind to default brand mapping
KIND_BRAND_MAPPING = {
    "database": "postgresql",
    "cache": "redis",
    "queue": "kafka",
    "gateway": "nginx",
    "container": "docker",
    "llm": "openai",
    "vector_db": "pinecone",
    "monitoring": "prometheus",
    "analytics": "grafana",
    "logging": "elk",
    "orchestrator": "kubernetes",
    "cdn": "cloudfront",
    "dns": "route53",
    "auth": "cognito",
    "storage": "s3",
    "serverless": "lambda",
}

def get_logo_cache_dir() -> str:
    """Returns the absolute path to the local logo cache directory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.join(current_dir, "assets", "logos")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

def get_style_brand_fallback(style_name: str, kind: Optional[str], category: str) -> Optional[str]:
    """
    Returns a fallback brand logo based on node kind, category, and visual style.
    """
    kind_lower = kind.lower().strip() if kind else ""
    
    if style_name == "aws_icons":
        # Specific mappings first
        if kind_lower == "database": return "rds"
        if kind_lower == "storage": return "s3"
        if kind_lower == "compute": return "lambda"
        if kind_lower == "gateway": return "api_gateway"
        if kind_lower == "security": return "cognito"
        if kind_lower == "serverless": return "lambda"
        if kind_lower == "auth": return "cognito"
        if kind_lower == "cdn": return "cloudfront"
        if kind_lower == "dns": return "route53"
        
        # Category-based fallbacks
        aws_cat = {
            "compute": "lambda",
            "database": "rds",
            "security": "cognito",
            "network": "api_gateway",
            "client": "react",
            "storage": "s3",
            "monitoring": "prometheus",
            "queue": "dynamodb",
        }
        return aws_cat.get(category, "aws")

    elif style_name == "aiicons":
        if kind_lower == "llm": return "openai"
        if kind_lower == "vector_db": return "pinecone"
        if kind_lower == "framework": return "langchain"
        if kind_lower == "dataset": return "huggingface"
        
        ai_cat = {
            "compute": "openai",
            "database": "pinecone",
            "security": "openai",
            "network": "langchain",
            "client": "react",
            "storage": "pinecone",
            "monitoring": "huggingface",
            "queue": "cohere",
        }
        return ai_cat.get(category, "openai")

    elif style_name == "k8s_icons":
        if kind_lower == "gateway": return "nginx"
        if kind_lower == "queue": return "kafka"
        if kind_lower == "database": return "postgresql"
        if kind_lower == "container": return "kubernetes"
        if kind_lower == "orchestrator": return "kubernetes"
        
        k8s_cat = {
            "compute": "kubernetes",
            "database": "postgresql",
            "security": "kubernetes",
            "network": "nginx",
            "client": "react",
            "storage": "kubernetes",
            "monitoring": "prometheus",
            "queue": "kafka",
        }
        return k8s_cat.get(category, "kubernetes")

    elif style_name == "drawio_skill":
        # Prefer open-source icons: Python, Redis, Kafka, PostgreSQL, Docker, Kubernetes
        if kind_lower == "database": return "postgresql"
        if kind_lower == "cache": return "redis"
        if kind_lower == "queue": return "kafka"
        if kind_lower == "container": return "docker"
        if kind_lower == "orchestrator": return "kubernetes"
        if kind_lower == "compute": return "python"
        
        skill_cat = {
            "compute": "python",
            "database": "postgresql",
            "security": "cognito",
            "network": "nginx",
            "client": "react",
            "storage": "s3",
            "monitoring": "prometheus",
            "queue": "kafka",
        }
        return skill_cat.get(category, "python")

    elif style_name in ("azure_icons", "gcp_icons"):
        provider = "azure" if style_name == "azure_icons" else "gcp"
        return provider

    # Classic/Default style brand fallback
    defaults = {
        "compute": "python",
        "database": "postgresql",
        "security": "cognito",
        "network": "nginx",
        "client": "react",
        "storage": "s3",
        "monitoring": "prometheus",
        "queue": "kafka",
    }
    return defaults.get(category, "python")

def resolve_logo(node_name: str, brand: Optional[str] = None, kind: Optional[str] = None) -> Optional[str]:
    """
    Resolves the brand logo URL based on the node name, explicit brand selection, or component kind.
    If the logo is not yet cached locally, it downloads it.
    Returns a local file:/// URI if cached/downloaded successfully, otherwise the remote URL.
    
    Style-aware: If the current style is 'minimal', logos are suppressed.
    """
    # Style check — suppress logos for minimal style
    if should_suppress_logos():
        return None
    
    node_lower = node_name.lower()
    resolved_brand = None
    
    # 1. Check explicit brand
    if brand:
        brand_key = brand.lower().strip()
        if brand_key in LOGO_REMOTE_URLS:
            resolved_brand = brand_key
            
    # 2. Check exact matches in node name
    if not resolved_brand:
        for b_name in LOGO_REMOTE_URLS.keys():
            if b_name in node_lower:
                resolved_brand = b_name
                break
                
    # 3. Fuzzy match patterns in node name
    if not resolved_brand:
        for pattern, b_name in BRAND_PATTERNS.items():
            if re.search(pattern, node_lower):
                resolved_brand = b_name
                break
                
    # 4. Check component kind mapping
    if not resolved_brand and kind:
        kind_key = kind.lower().strip()
        if kind_key in KIND_BRAND_MAPPING:
            resolved_brand = KIND_BRAND_MAPPING[kind_key]
            
    # 5. Visual style specific category/kind default fallback hierarchy
    if not resolved_brand:
        from services.architecture_v3.shape_resolver import _classify_node
        category = _classify_node(node_lower)
        style_name = get_current_style()
        resolved_brand = get_style_brand_fallback(style_name, kind, category)
        
    if not resolved_brand:
        return None
        
    return LOGO_REMOTE_URLS[resolved_brand]
