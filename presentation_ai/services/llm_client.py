import os
import time
import re
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_ENV = os.getenv("MODEL", "openai/gpt-oss-120b:free")
if "gemini-2.5" in MODEL_ENV or "flash" in MODEL_ENV or "gpt-4" in MODEL_ENV or "claude" in MODEL_ENV:
    MODEL = "openai/gpt-oss-120b:free"
else:
    MODEL = MODEL_ENV

MAX_RETRIES = 2
RETRY_WAIT_SECONDS = 2  # Base wait time, doubles each retry

# Reliable list of fallback models on OpenRouter (all free)
FALLBACK_MODELS = [
    "openai/gpt-oss-120b:free",          # ✅ WORKS — 120B params
    "qwen/qwen3-coder:free",             # ✅ Works when not rate limited
    "liquid/lfm-2.5-1.2b-instruct:free", # ✅ Last resort fallback
]


def extract_topic_and_slide_count(user_prompt: str) -> tuple:
    topic = "Offline Topic"
    slide_count = 6
    
    # Regex to find Topic
    topic_match = re.search(r"Topic:\s*(.*)", user_prompt, re.IGNORECASE)
    if topic_match:
        topic = topic_match.group(1).strip()
    else:
        # Try finding subject
        topic_match2 = re.search(r"slide deck structure for:\s*(.*)", user_prompt, re.IGNORECASE)
        if topic_match2:
            topic = topic_match2.group(1).split('\n')[0].strip()
            
    # Regex to find slide count
    count_match = re.search(r"Number of slides:\s*(\d+)", user_prompt, re.IGNORECASE)
    if count_match:
        slide_count = int(count_match.group(1))
    else:
        count_match2 = re.search(r"EXACTLY\s*(\d+)\s*slides", user_prompt, re.IGNORECASE)
        if count_match2:
            slide_count = int(count_match2.group(1))
            
    return topic, slide_count


def generate_mock_text_for_role(role: str, orig_text: str, topic: str) -> str:
    if not orig_text:
        return f"{role.capitalize()} for {topic}"
        
    word_count = len(orig_text.split())
    if word_count <= 3:
        if "step" in orig_text.lower():
            return orig_text
        return f"{topic} Overview" if "title" in role.lower() else orig_text
        
    if "title" in role or "heading" in role or "subtitle" in role:
        words = f"Understanding the Core Principles and Frameworks of {topic} System".split()
        return " ".join(words[:word_count])
        
    sentence = f"In this section, we analyze the main requirements of {topic} to establish baseline efficiency and operational excellence across all development phases."
    words = sentence.split()
    if len(words) > word_count:
        return " ".join(words[:word_count]) + "."
    else:
        return sentence


def generate_offline_json_outline(topic: str, slide_count: int) -> str:
    slides = []
    
    # Title slide
    slides.append({
        "slide_type": "title",
        "title": topic,
        "heading": "Presentation Overview",
        "lead_sentence": f"An in-depth exploration of {topic} generated completely in offline mode due to connectivity limitations.",
        "bullets": [
            "This presentation was generated locally using our robust offline fallback outline engine.",
            "Contains a fully structured template tailorable to your specific presentation requirements.",
            "All slides adhere strictly to the visual layouts and word count rules of Slide Generator."
        ],
        "visual_type": "image",
        "image_keyword": topic + " concept",
        "speaker_notes": "Welcome to the presentation."
    })
    
    num_content_slides = max(1, slide_count - 2)
    for i in range(1, num_content_slides + 1):
        if i % 4 == 1:
            # Overview / Column layout
            slides.append({
                "slide_type": "three_column",
                "title": f"Key Pillars of {topic}",
                "heading": "Strategic Overview",
                "lead_sentence": "We identify three fundamental dimensions that characterize our strategic approach to the topic today.",
                "bullets": [
                    "First dimension covers structural optimization and baseline efficiency improvements across systems.",
                    "Second dimension centers around user-centric service delivery and feature-rich iterations.",
                    "Third dimension integrates robust security standards and long-term sustainability metrics."
                ],
                "visual_type": "icon",
                "icon_keywords": ["settings", "users", "shield"],
                "grid_items": [
                    {"title": "System Baseline", "description": "Analyzing structural components and baseline efficiency for operational excellence."},
                    {"title": "User Engagement", "description": "Fostering engagement through modern interfaces and interactive client design."},
                    {"title": "Security Shield", "description": "Ensuring data integrity and robust security policies for all operations."}
                ],
                "speaker_notes": "This slide outlines our three key pillars."
            })
        elif i % 4 == 2:
            # Process lifecycle
            slides.append({
                "slide_type": "process",
                "title": f"Implementation Lifecycle",
                "heading": "Process Flow",
                "lead_sentence": "The execution roadmap follows four sequential phases designed to minimize risk and maximize output.",
                "bullets": [
                    "Phase one focuses on initial discovery, requirements gathering, and design analysis.",
                    "Phase two comprises iterative prototyping, code reviews, and initial feature building.",
                    "Phase three encompasses integration testing, client validation, and security auditing.",
                    "Phase four wraps up with deployment pipelines, performance monitoring, and support."
                ],
                "visual_type": "process",
                "visual_items": ["Discovery", "Prototyping", "Testing", "Deployment"],
                "process_steps": [
                    {"title": "Discovery Phase", "description": "Gathering user needs and analyzing technical system constraints."},
                    {"title": "Prototyping Phase", "description": "Developing initial wireframes and core database models iteratively."},
                    {"title": "Testing Phase", "description": "Running comprehensive unit tests and user acceptance trials."},
                    {"title": "Deployment Phase", "description": "Rolling out services safely with blue-green deployment strategies."}
                ],
                "speaker_notes": "Here is the implementation roadmap."
            })
        elif i % 4 == 3:
            # Metrics / Dashboard
            slides.append({
                "slide_type": "dashboard",
                "title": "Performance Indicators",
                "heading": "Data & Insight",
                "lead_sentence": "Key metrics demonstrate positive growth trends and operational improvements across the board.",
                "bullets": [
                    "System throughput increased significantly during the last evaluation cycle under stress testing.",
                    "User satisfaction scores rose to record levels following the visual interface redesign.",
                    "Resource utilization was optimized, resulting in lower infrastructure overhead costs.",
                    "Error rates dropped below the target threshold, ensuring robust system reliability."
                ],
                "visual_type": "dashboard",
                "dashboard_metrics": [
                    {"label": "Throughput Boost", "value": "+45%"},
                    {"label": "User Satisfaction", "value": "98%"},
                    {"label": "Cost Savings", "value": "$12k/mo"},
                    {"label": "Error Rate", "value": "<0.1%"}
                ],
                "dashboard_insight": "Optimizations delivered high performance and significant cost reductions simultaneously.",
                "speaker_notes": "We are tracking positive indicators."
            })
        else:
            # Comparison
            slides.append({
                "slide_type": "comparison",
                "title": "Traditional vs. Modern Approach",
                "heading": "Comparative Analysis",
                "lead_sentence": "Comparing the legacy system with our modern visual architecture highlights massive efficiency gains.",
                "bullets": [
                    "Legacy systems suffered from manual configuration overhead and high deployment failure rates.",
                    "Our modern approach utilizes automated CI/CD pipelines and infrastructure as code.",
                    "Scalability is now dynamic, adapting in real-time to load spikes automatically.",
                    "Maintenance costs are minimized through decoupled serverless microservices."
                ],
                "visual_type": "comparison",
                "comparison_left_title": "Legacy System",
                "comparison_right_title": "Modern Platform",
                "comparison_items": [
                    {"feature": "Deployments", "left": "Manual & Risks", "right": "Automated & Safe"},
                    {"feature": "Scaling", "left": "Fixed Capacity", "right": "Elastic Auto-scaling"},
                    {"feature": "Architecture", "left": "Monolithic", "right": "Microservices"}
                ],
                "speaker_notes": "This comparison contrasts legacy bottlenecks with modern capabilities."
            })
            
    # Conclusion slide
    slides.append({
        "slide_type": "conclusion",
        "title": "Conclusion & Next Steps",
        "heading": "Summary",
        "lead_sentence": f"In conclusion, {topic} presents a significant opportunity for innovation, growth, and efficiency.",
        "bullets": [
            "Implementing the proposed roadmap will secure a solid foundation for future growth.",
            "Immediate priorities include setting up development environments and testing pipelines.",
            "Stakeholders will be kept informed with bi-weekly progress reports and visual demos.",
            "We are confident in our execution strategy and look forward to getting started."
        ],
        "visual_type": "icon",
        "icon_keywords": ["check-circle"],
        "speaker_notes": "Thank you for your time."
    })
    
    # Adjust slide count
    if len(slides) > slide_count:
        slides = [slides[0]] + slides[1:slide_count-1] + [slides[-1]]
    elif len(slides) < slide_count:
        while len(slides) < slide_count:
            last_content = slides[-2].copy()
            last_content["title"] = last_content["title"] + " (Cont.)"
            slides.insert(len(slides)-1, last_content)
    slides = slides[:slide_count]
    
    return json.dumps({"title": topic, "slides": slides}, indent=4)


def generate_offline_architecture_spec(topic: str, topology: str) -> str:
    topo = topology.lower().strip()
    components = []
    relationships = []
    
    if topo == "kubernetes":
        components = [
            {"name": "External Ingress Gateway", "kind": "gateway"},
            {"name": "Kube-API Server", "kind": "gateway"},
            {"name": "Authentication Pod", "kind": "service"},
            {"name": "Core Application Pod", "kind": "service"},
            {"name": "etcd Cluster", "kind": "database"},
            {"name": "Redis Cache Pod", "kind": "cache"},
            {"name": "Persistent Volume Storage", "kind": "storage"}
        ]
        relationships = [
            {"source": "External Ingress Gateway", "target": "Core Application Pod", "label": "routes traffic"},
            {"source": "Core Application Pod", "target": "Authentication Pod", "label": "authenticates"},
            {"source": "Core Application Pod", "target": "Redis Cache Pod", "label": "caches"},
            {"source": "Core Application Pod", "target": "Persistent Volume Storage", "label": "mounts"},
            {"source": "Kube-API Server", "target": "etcd Cluster", "label": "persists state"}
        ]
    elif topo in ["ai_pipeline", "rag_pipeline"]:
        components = [
            {"name": "User Query Interface", "kind": "client"},
            {"name": "FastAPI API Gateway", "kind": "gateway"},
            {"name": "Document Loader & Chunker", "kind": "service"},
            {"name": "RAG Embedding Generator", "kind": "service"},
            {"name": "Pinecone Vector Store", "kind": "vector_db"},
            {"name": "Claude LLM Orchestrator", "kind": "llm"},
            {"name": "SQL History DB", "kind": "database"}
        ]
        relationships = [
            {"source": "User Query Interface", "target": "FastAPI API Gateway", "label": "queries"},
            {"source": "FastAPI API Gateway", "target": "Document Loader & Chunker", "label": "triggers ingest"},
            {"source": "Document Loader & Chunker", "target": "RAG Embedding Generator", "label": "vectorizes"},
            {"source": "RAG Embedding Generator", "target": "Pinecone Vector Store", "label": "stores embeddings"},
            {"source": "FastAPI API Gateway", "target": "Claude LLM Orchestrator", "label": "invokes generation"},
            {"source": "Claude LLM Orchestrator", "target": "Pinecone Vector Store", "label": "retrieves context"},
            {"source": "Claude LLM Orchestrator", "target": "SQL History DB", "label": "logs conversation"}
        ]
    elif topo == "event_driven":
        components = [
            {"name": "Event Producer client", "kind": "client"},
            {"name": "Nginx Event Gateway", "kind": "gateway"},
            {"name": "Apache Kafka Broker", "kind": "queue"},
            {"name": "Processing Microservice", "kind": "service"},
            {"name": "Notification Engine", "kind": "service"},
            {"name": "Timescale DB Storage", "kind": "database"}
        ]
        relationships = [
            {"source": "Event Producer client", "target": "Nginx Event Gateway", "label": "sends HTTP events"},
            {"source": "Nginx Event Gateway", "target": "Apache Kafka Broker", "label": "publishes events"},
            {"source": "Processing Microservice", "target": "Apache Kafka Broker", "label": "subscribes"},
            {"source": "Notification Engine", "target": "Apache Kafka Broker", "label": "subscribes"},
            {"source": "Processing Microservice", "target": "Timescale DB Storage", "label": "persists events"}
        ]
    else:
        # Standard default (microservices/cloud/etc.)
        components = [
            {"name": f"{topic} Web App Client", "kind": "client"},
            {"name": f"{topic} API Gateway", "kind": "gateway"},
            {"name": f"{topic} Core Service", "kind": "service"},
            {"name": f"{topic} Auth Service", "kind": "service"},
            {"name": f"{topic} Database", "kind": "database"},
            {"name": f"{topic} Cache Store", "kind": "cache"}
        ]
        relationships = [
            {"source": f"{topic} Web App Client", "target": f"{topic} API Gateway", "label": "HTTP Request"},
            {"source": f"{topic} API Gateway", "target": f"{topic} Core Service", "label": "routes"},
            {"source": f"{topic} API Gateway", "target": f"{topic} Auth Service", "label": "authenticates"},
            {"source": f"{topic} Core Service", "target": f"{topic} Database", "label": "queries"},
            {"source": f"{topic} Core Service", "target": f"{topic} Cache Store", "label": "checks cache"}
        ]
        
    spec = {
        "title": f"System Architecture for {topic}",
        "components": components,
        "relationships": relationships
    }
    return json.dumps(spec, indent=2)


def generate_offline_fallback(system_prompt: str, user_prompt: str) -> str:
    print("[LLM FALLBACK] Triggering offline mock fallback generator...")
    
    # Check if this is an architecture spec extraction request
    if "components" in system_prompt and "relationships" in system_prompt:
        topic, topology = "Offline Topic", "cloud"
        topic_match = re.search(r"Topic:\s*(.*)", user_prompt, re.IGNORECASE)
        if topic_match:
            topic = topic_match.group(1).strip()
        topo_match = re.search(r"Topology:\s*(.*)", user_prompt, re.IGNORECASE)
        if topo_match:
            topology = topo_match.group(1).strip()
        return generate_offline_architecture_spec(topic, topology)

    # Check if Draw.io XML is expected
    if "mxfile" in user_prompt or "mxGraphModel" in user_prompt or "xml" in user_prompt.lower():
        return """<mxfile host="Electron" version="30.0.4">
  <diagram id="page_offline" name="Page-1">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" pageWidth="1654" pageHeight="1169">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="n1" value="Offline Mode: Architecture Visuals" style="rounded=1;fillColor=#f8f9fa;strokeColor=#333333;fontColor=#000000;fontSize=14;fontStyle=1;align=center;" vertex="1" parent="1">
          <mxGeometry x="600" y="450" width="300" height="150" as="geometry"/>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""

    # Check if V2 Slide Planner request
    if "deck_title" in user_prompt or "slides_layout_info" in user_prompt or "zones" in user_prompt:
        topic = "Offline Topic"
        topic_match = re.search(r'presentation about:\s*"(.*?)"', user_prompt, re.IGNORECASE)
        if topic_match:
            topic = topic_match.group(1).strip()
            
        # Parse layout info
        layout_info = None
        json_start = user_prompt.find("[\n  {")
        if json_start == -1:
            json_start = user_prompt.find("[\n{")
        if json_start == -1:
            json_start = user_prompt.find("[")
            
        if json_start != -1:
            bracket_count = 0
            json_end = -1
            for idx in range(json_start, len(user_prompt)):
                char = user_prompt[idx]
                if char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        json_end = idx + 1
                        break
            if json_end != -1:
                try:
                    layout_info = json.loads(user_prompt[json_start:json_end])
                except Exception as e:
                    print(f"[LLM FALLBACK] Failed to parse extracted layout JSON: {e}")
                    
        if layout_info:
            slides = []
            for slide_layout in layout_info:
                slide_idx = slide_layout.get("slide_index", 1)
                zones = slide_layout.get("zones", [])
                image_roles = slide_layout.get("image_roles", [])
                
                slide_data = {"slide_index": slide_idx}
                for zone in zones:
                    role = zone.get("role")
                    orig_text = zone.get("original_text", "")
                    slide_data[role] = generate_mock_text_for_role(role, orig_text, topic)
                    
                for img_role in image_roles:
                    slide_data[f"{img_role}_keyword"] = f"{topic} professional stock photo"
                    
                slides.append(slide_data)
                
            deck = {
                "deck_title": topic,
                "slides": slides
            }
            return json.dumps(deck, indent=2)
            
    # Default to V1 outline fallback
    topic, slide_count = extract_topic_and_slide_count(user_prompt)
    return generate_offline_json_outline(topic, slide_count)


def call_llm(system_prompt: str, user_prompt: str, max_tokens: int = 2500) -> str:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not set. Please set it in the .env file.")

    models_to_try = [MODEL]
    for fm in FALLBACK_MODELS:
        if fm not in models_to_try:
            models_to_try.append(fm)

    last_error = None

    for model_name in models_to_try:
        print(f"[LLM] Trying model: {model_name}")
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user",   "content": user_prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": max_tokens
                    },
                    timeout=60
                )

                # Handle rate limiting with retry
                if response.status_code == 429:
                    wait_time = RETRY_WAIT_SECONDS * (2 ** (attempt - 1))
                    print(f"[LLM] {model_name} rate limited (429). Retry {attempt}/{MAX_RETRIES}, waiting {wait_time}s...")
                    if attempt < MAX_RETRIES:
                        time.sleep(wait_time)
                        continue
                    else:
                        raise requests.exceptions.HTTPError(f"Rate limit exhausted for {model_name}", response=response)

                # Handle other bad statuses
                if not response.ok:
                    print(f"[LLM] Model {model_name} returned error status {response.status_code}: {response.text}")
                    response.raise_for_status()

                data = response.json()

                # Handle OpenRouter error responses that return 200 but contain an error key
                if "error" in data:
                    error_msg = data["error"].get("message", str(data["error"]))
                    raise ValueError(f"OpenRouter API error: {error_msg}")

                print(f"[LLM] Success with model: {model_name} on attempt {attempt}")
                content = data["choices"][0]["message"].get("content")
                if content is None:
                    print(f"[LLM] Warning: Response content is None. Full response JSON: {data}")
                    raise ValueError("Empty or None response content from model")
                return content

            except Exception as e:
                print(f"[LLM] Attempt {attempt} failed for model {model_name}: {str(e)}")
                last_error = e
                
                # Check for 402 Payment Required to skip retries immediately
                is_payment_required = False
                if isinstance(e, requests.exceptions.HTTPError) and e.response is not None and e.response.status_code == 402:
                    is_payment_required = True
                elif "402" in str(e) or "payment required" in str(e).lower():
                    is_payment_required = True
                
                if is_payment_required:
                    print(f"[LLM] Payment Required detected. Skipping retries for {model_name}...")
                    break  # Try the next model fallback immediately
                
                # Check for network offline / DNS resolution failures to trigger local fallback immediately
                is_connection_error = False
                err_str = str(e).lower()
                if isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
                    is_connection_error = True
                elif "nameresolutionerror" in err_str or "getaddrinfo failed" in err_str or "connectionpool" in err_str:
                    is_connection_error = True
                    
                if is_connection_error:
                    print(f"[LLM] Network connectivity/DNS resolution error detected: {e}")
                    try:
                        offline_response = generate_offline_fallback(system_prompt, user_prompt)
                        print("[LLM] Successfully generated offline mockup fallback response!")
                        return offline_response
                    except Exception as fallback_err:
                        print(f"[LLM] Failed to generate offline fallback: {fallback_err}")
                
                if attempt < MAX_RETRIES:
                    time.sleep(1)
                    continue

        print(f"[LLM] Model {model_name} failed completely. Trying next fallback...")

    # If all models failed, raise the last exception
    raise last_error or ValueError("All models and fallbacks failed to respond.")
