import re
from typing import Optional

# Mapping of brand names to their official/standard logo URLs (high-quality PNGs or SVGs)
LOGO_URLS = {
    "aws": "https://img.icons8.com/color/144/amazon-web-services.png",
    "azure": "https://img.icons8.com/color/144/azure-1.png",
    "gcp": "https://img.icons8.com/color/144/google-cloud.png",
    "kubernetes": "https://img.icons8.com/color/144/kubernetes.png",
    
    # AI Brands
    "openai": "https://img.icons8.com/external-tal-revivo-color-tal-revivo/144/external-openai-an-artificial-intelligence-research-laboratory-logo-color-tal-revivo.png",
    "claude": "https://upload.wikimedia.org/wikipedia/commons/e/e4/Claude_AI_logo.svg",
    "gemini": "https://upload.wikimedia.org/wikipedia/commons/e/ec/Google_Gemini_logo.svg",
    "llama": "https://img.icons8.com/color/144/meta-platforms.png",
    "huggingface": "https://img.icons8.com/color/144/hugging-face.png",
    "langchain": "https://raw.githubusercontent.com/langchain-ai/langchain/master/docs/static/img/langchain_logo.png",
    "ollama": "https://github.com/ollama/ollama/raw/main/docs/assets/ollama.png"
}

# Sub-services mapping to standard cloud category logos (AWS/Azure/GCP)
SERVICE_LOGOS = {
    # AWS Services
    r'\b(ec2|virtual-machine|vm|instance)\b': "https://img.icons8.com/color/144/amazon-web-services.png",
    r'\b(s3|bucket|storage|blob|blob-storage)\b': "https://img.icons8.com/color/144/amazon-web-services.png",
    r'\b(lambda|serverless|function|functions)\b': "https://img.icons8.com/color/144/amazon-web-services.png",
    r'\b(rds|dynamodb|aurora|database|db|postgres|mysql)\b': "https://img.icons8.com/color/144/amazon-web-services.png",
    
    # AI/ML Services
    r'\b(gpt|chatgpt|llm|generator|openai)\b': LOGO_URLS["openai"],
    r'\b(claude|anthropic)\b': LOGO_URLS["claude"],
    r'\b(gemini|google-gemini)\b': LOGO_URLS["gemini"],
    r'\b(llama|llama2|llama3|meta)\b': LOGO_URLS["llama"],
    r'\b(huggingface|transformers|transformer)\b': LOGO_URLS["huggingface"],
    r'\b(langchain|chain|agent|agents)\b': LOGO_URLS["langchain"],
    r'\b(ollama|local-llm)\b': LOGO_URLS["ollama"],
}

def resolve_logo(node_name: str, brand: Optional[str] = None) -> Optional[str]:
    """
    Resolves the brand logo URL based on the node name or explicit brand selection.
    Returns the logo URL if found, otherwise None.
    """
    node_lower = node_name.lower()
    
    # 1. Explicit brand matching
    if brand:
        brand_key = brand.lower().strip()
        if brand_key in LOGO_URLS:
            return LOGO_URLS[brand_key]
            
    # 2. Check node name directly for explicit brand match
    for brand_name, url in LOGO_URLS.items():
        if brand_name in node_lower:
            return url
            
    # 3. Fuzzy match sub-services or generic service keywords
    for pattern, url in SERVICE_LOGOS.items():
        if re.search(pattern, node_lower):
            return url
            
    return None
