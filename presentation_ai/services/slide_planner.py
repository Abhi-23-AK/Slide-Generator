# -*- coding: utf-8 -*-
import json
import os
import inspect
from datetime import datetime
from services.llm_client import call_llm
from services.layout_engine import assign_layouts

# Intercept transcript fetch to save transcript length for logging
try:
    import services.transcript_service
    _orig_fetch = services.transcript_service.fetch_transcript
    TRANSCRIPT_LENGTHS = {}

    def patched_fetch_transcript(video_id: str) -> str:
        t = _orig_fetch(video_id)
        if t:
            TRANSCRIPT_LENGTHS[video_id] = len(t)
        return t

    services.transcript_service.fetch_transcript = patched_fetch_transcript
except Exception as e:
    print(f"[SLIDE_PLANNER] Warning: Failed to patch fetch_transcript: {e}")
    TRANSCRIPT_LENGTHS = {}

ARCHITECTURE_XML_TEMPLATE = """<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" pageWidth="1654" pageHeight="1169">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <mxCell id="2" value="{cloud_label}" style="rounded=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=14;fontStyle=1;verticalAlign=top;align=center;" vertex="1" parent="1">
      <mxGeometry x="200" y="50" width="900" height="650" as="geometry"/>
    </mxCell>
    <mxCell id="3" value="{vpc_label}" style="rounded=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=13;fontStyle=1;verticalAlign=top;align=center;" vertex="1" parent="2">
      <mxGeometry x="20" y="40" width="860" height="590" as="geometry"/>
    </mxCell>
    <mxCell id="4" value="{zone1_label}" style="rounded=1;fillColor=#f5f5f5;strokeColor=#666666;fontStyle=1;verticalAlign=top;align=center;" vertex="1" parent="3">
      <mxGeometry x="20" y="40" width="380" height="520" as="geometry"/>
    </mxCell>
    <mxCell id="5" value="{zone2_label}" style="rounded=1;fillColor=#f5f5f5;strokeColor=#666666;fontStyle=1;verticalAlign=top;align=center;" vertex="1" parent="3">
      <mxGeometry x="460" y="40" width="380" height="520" as="geometry"/>
    </mxCell>
    <mxCell id="6" value="{z1_comp1_name}" style="rounded=1;fillColor={z1_comp1_fill};strokeColor=#6c8ebf;" vertex="1" parent="4">
      <mxGeometry x="110" y="60" width="160" height="90" as="geometry"/>
    </mxCell>
    <mxCell id="7" value="{z1_comp2_name}" style="rounded=1;fillColor={z1_comp2_fill};strokeColor=#6c8ebf;" vertex="1" parent="4">
      <mxGeometry x="110" y="215" width="160" height="90" as="geometry"/>
    </mxCell>
    <mxCell id="8" value="{z1_comp3_name}" style="rounded=1;fillColor={z1_comp3_fill};strokeColor=#6c8ebf;" vertex="1" parent="4">
      <mxGeometry x="110" y="370" width="160" height="90" as="geometry"/>
    </mxCell>
    <mxCell id="9" value="{z2_comp1_name}" style="rounded=1;fillColor={z2_comp1_fill};strokeColor=#6c8ebf;" vertex="1" parent="5">
      <mxGeometry x="110" y="60" width="160" height="90" as="geometry"/>
    </mxCell>
    <mxCell id="10" value="{z2_comp2_name}" style="rounded=1;fillColor={z2_comp2_fill};strokeColor=#6c8ebf;" vertex="1" parent="5">
      <mxGeometry x="110" y="215" width="160" height="90" as="geometry"/>
    </mxCell>
    <mxCell id="11" value="{z2_comp3_name}" style="rounded=1;fillColor={z2_comp3_fill};strokeColor=#6c8ebf;" vertex="1" parent="5">
      <mxGeometry x="110" y="370" width="160" height="90" as="geometry"/>
    </mxCell>
    <mxCell id="12" value="{lb_label}" style="rounded=1;fillColor=#0075db;strokeColor=#005a99;fontColor=#ffffff;fontStyle=1;align=center;" vertex="1" parent="3">
      <mxGeometry x="350" y="290" width="160" height="60" as="geometry"/>
    </mxCell>
    <mxCell id="13" value="{ext1_label}" style="rounded=1;fillColor=#f5f5f5;strokeColor=#666666;align=center;" vertex="1" parent="1">
      <mxGeometry x="30" y="200" width="100" height="60" as="geometry"/>
    </mxCell>
    <mxCell id="14" value="{ext2_label}" style="rounded=1;fillColor=#f5f5f5;strokeColor=#666666;align=center;" vertex="1" parent="1">
      <mxGeometry x="30" y="350" width="100" height="60" as="geometry"/>
    </mxCell>
    <mxCell id="15" style="edgeStyle=orthogonalEdgeStyle;strokeColor=#0075db;strokeWidth=2;endArrow=block;endFill=1;" edge="1" source="13" target="14" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="16" style="edgeStyle=orthogonalEdgeStyle;strokeColor=#0075db;strokeWidth=2;endArrow=block;endFill=1;" edge="1" source="14" target="12" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="17" style="edgeStyle=orthogonalEdgeStyle;strokeColor=#0075db;strokeWidth=2;endArrow=block;endFill=1;" edge="1" source="12" target="6" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="18" style="edgeStyle=orthogonalEdgeStyle;strokeColor=#0075db;strokeWidth=2;endArrow=block;endFill=1;" edge="1" source="12" target="9" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="19" style="edgeStyle=orthogonalEdgeStyle;strokeColor=#82b366;strokeWidth=2;endArrow=block;endFill=1;" edge="1" source="6" target="7" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="20" style="edgeStyle=orthogonalEdgeStyle;strokeColor=#82b366;strokeWidth=2;endArrow=block;endFill=1;" edge="1" source="9" target="10" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="21" style="edgeStyle=orthogonalEdgeStyle;strokeColor=#ff8000;strokeWidth=2;endArrow=block;endFill=1;" edge="1" source="7" target="8" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="22" style="edgeStyle=orthogonalEdgeStyle;strokeColor=#ff8000;strokeWidth=2;endArrow=block;endFill=1;" edge="1" source="10" target="11" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>"""

def xml_escape(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;")
                .replace("\n", "&#xa;"))

def build_architecture_xml_from_slots(slots: dict) -> str:
    if not isinstance(slots, dict):
        slots = {}
        
    defaults = {
        "cloud_label": "Cloud Platform",
        "vpc_label": "Virtual Private Cloud (VPC)",
        "zone1_label": "Availability Zone 1",
        "zone2_label": "Availability Zone 2",
        "z1_comp1_name": "Web Server\\nNginx",
        "z1_comp1_fill": "#dae8fc",
        "z1_comp2_name": "App Service\\nNode.js",
        "z1_comp2_fill": "#dae8fc",
        "z1_comp3_name": "Database\\nPostgreSQL",
        "z1_comp3_fill": "#d5e8d4",
        "z2_comp1_name": "API Gateway\\nKong",
        "z2_comp1_fill": "#ff8000",
        "z2_comp2_name": "Worker Service\\nGo",
        "z2_comp2_fill": "#dae8fc",
        "z2_comp3_name": "Cache Service\\nRedis",
        "z2_comp3_fill": "#fff2cc",
        "lb_label": "Load Balancer",
        "ext1_label": "User",
        "ext2_label": "Internet"
    }
    
    color_map = {
        "compute": "#dae8fc",
        "server": "#dae8fc",
        "database": "#d5e8d4",
        "storage": "#d5e8d4",
        "db": "#d5e8d4",
        "security": "#f8cecc",
        "gateway": "#ff8000",
        "api": "#ff8000",
        "load balancer": "#0075db",
        "lb": "#0075db",
        "cache": "#fff2cc",
        "queue": "#fff2cc",
        "external": "#f5f5f5",
        "actor": "#f5f5f5"
    }
    
    params = {}
    for k, default_val in defaults.items():
        val = slots.get(k) or slots.get(k.replace("_", "")) or default_val
        if k.endswith("_fill"):
            val_str = str(val).lower().strip()
            if val_str.startswith("#"):
                pass
            elif val_str in color_map:
                val = color_map[val_str]
            else:
                matched = False
                for name, hexcode in color_map.items():
                    if name in val_str:
                        val = hexcode
                        matched = True
                        break
                if not matched:
                    val = default_val
            params[k] = xml_escape(str(val))
        else:
            params[k] = xml_escape(str(val))
            
    return ARCHITECTURE_XML_TEMPLATE.format(**params)

DRAWIO_ARCHITECTURE_INSTRUCTIONS = """
=== ARCHITECTURE DIAGRAM REQUIREMENTS ===

For architecture/tech_stack slides, you MUST provide a "drawio_slots" JSON object.
The system will inject your values into a pre-positioned coordinate template.
DO NOT generate raw mxGraphModel XML. Only provide the drawio_slots object.

Slot fields (all are strings):
- cloud_label: Name for the outer cloud container (e.g. "AWS Cloud", "Azure Platform")
- vpc_label: Name for the VPC/network container (e.g. "Production VPC")
- zone1_label: Name for Zone 1 (e.g. "us-east-1a", "Availability Zone 1")
- zone2_label: Name for Zone 2 (e.g. "us-east-1b", "Availability Zone 2")
- z1_comp1_name: Zone 1 component 1 label (use \\n for line breaks, e.g. "Web Server\\nnginx")
- z1_comp1_fill: fillColor hex (e.g. "#dae8fc" for compute, "#d5e8d4" for database, "#ff8000" for gateway, "#f8cecc" for security)
- z1_comp2_name, z1_comp2_fill: Zone 1 component 2
- z1_comp3_name, z1_comp3_fill: Zone 1 component 3
- z2_comp1_name, z2_comp1_fill: Zone 2 component 1
- z2_comp2_name, z2_comp2_fill: Zone 2 component 2
- z2_comp3_name, z2_comp3_fill: Zone 2 component 3
- lb_label: Load balancer label (e.g. "Application LB")
- ext1_label: External actor 1 (e.g. "User", "Client")
- ext2_label: External actor 2 (e.g. "Internet", "CDN")

COLOR GUIDE for fillColor:
- Compute/Server: #dae8fc (blue)
- Database/Storage: #d5e8d4 (green)
- Security: #f8cecc (red/pink)
- Gateway/API: #ff8000 (orange)
- Load Balancer: #0075db (dark blue)
- Cache/Queue: #fff2cc (yellow)
- External/Actor: #f5f5f5 (gray)

Each zone MUST have exactly 3 components. Choose component names and colors
that match the slide topic (e.g. microservices = API Gateway, Auth Service,
Order Service, Payment DB, Cache, Message Queue, etc.).

GENERATE DYNAMICALLY based on slide topic:
- Web app → Internet > CDN > LB > App servers > DB
- ML pipeline → Data lake > Processing > Model > API > Client
- Microservices → API Gateway > Service mesh > services > DB per service
- CI/CD → Dev > Git > Pipeline > Docker > K8s > Monitoring
- Security → Firewall > WAF > IDS > App > Vault > Audit

Example drawio_slots for "Cloud Microservices":
{
  "cloud_label": "AWS Cloud Platform",
  "vpc_label": "Production VPC",
  "zone1_label": "Availability Zone 1",
  "zone2_label": "Availability Zone 2",
  "z1_comp1_name": "API Gateway\\nnginx",
  "z1_comp1_fill": "#ff8000",
  "z1_comp2_name": "Auth Service\\nNode.js",
  "z1_comp2_fill": "#dae8fc",
  "z1_comp3_name": "User DB\\nPostgreSQL",
  "z1_comp3_fill": "#d5e8d4",
  "z2_comp1_name": "Order Service\\nJava",
  "z2_comp1_fill": "#dae8fc",
  "z2_comp2_name": "Payment Service\\nPython",
  "z2_comp2_fill": "#dae8fc",
  "z2_comp3_name": "Redis Cache\\nCluster",
  "z2_comp3_fill": "#fff2cc",
  "lb_label": "Application Load Balancer",
  "ext1_label": "User",
  "ext2_label": "Internet"
}
"""

def generate_architecture_xml_prompt(topic: str, context: str = "") -> str:
    return f"""
Generate a COMPLEX professional architecture diagram 
in draw.io mxGraph XML for topic: {topic}

{f'Context: {context}' if context else ''}

REQUIREMENTS:
- Minimum 150 XML elements (mxCell nodes)
- Use nested containers: Cloud > Region > VPC > Zone > Subnet
- Include ALL these component types:
  * External actors (users, internet, enterprise)
  * Network layer (gateways, load balancers, CDN)
  * Application layer (servers, services, APIs)
  * Data layer (databases, caches, storage)
  * Security overlays (dashed zone borders)
  * Monitoring/logging components if relevant

- Use IBM Cloud / AWS architecture visual style
- Color-code by category (network=blue, 
  security=red, compute=green, gateway=orange)
- Add connection arrows between ALL related components
- Include dashed security zone overlays
- Add component labels with technical specs

COMPLEXITY LEVEL: Enterprise production architecture
NOT a simple flow diagram - a full infrastructure diagram.

Return ONLY the mxGraphModel XML, nothing else.
Start with: <mxGraphModel dx="1422" dy="762"...
"""


TONE_DESCRIPTIONS = {
  "professional": """
    Style: Corporate, clean, authoritative.
    Use clear data-driven language.
    Headings are action-oriented and uppercase.
    Content is structured with clear hierarchy.
    Yellow accent elemePnts highlight key information.
  """,
  "creative": """
    Style: Modern, artistic, visually dynamic.
    Use engaging storytelling language.
    Headings are bold and expressive.
    Content flows naturally with creative metaphors.
    Teal and pink hexagonal visual elements.
  """,
  "academic": """
    Style: Scholarly, research-focused, structured.
    Use formal academic language with citations style.
    Headings are informative, not promotional.
    Content is evidence-based and analytical.
    Green-accented clean white layouts.
  """,
  "technical": """
    Style: Futuristic, precise, technology-focused.
    Use technical terminology confidently.
    Headings are bold and impactful.
    Content includes specs, metrics, architecture.
    Dark background with neon blue/pink accents.
  """,
  "neumorphism": """
    Style: Clean, soft, minimalist, tactile 3D.
    Use professional and modern language.
    Headings are soft, lowercase or capitalized (not uppercase).
    Background color is soft grey #F1F4F7.
    Containers use soft dual shadow effects (extruded or inset feel).
    Uses organic pebble shapes, fluid curves, and pop accents of pink, yellow, blue, and teal.
  """
}


SYSTEM_PROMPT = """You are a professional presentation designer.
Generate a slide deck outline as valid JSON only.
No markdown, no explanation - pure JSON.

CONTENT QUALITY RULES - STRICTLY FOLLOW:
- The bullet points and visual items MUST contain real, highly specific factual content derived from the user's topic and source document.
- EACH content slide MUST have 4-6 meaningful bullet points.
- Never generate bullet points shorter than 12 words. Each bullet must be 12-20 words long and be a complete meaningful sentence.
- Always generate a hero/lead sentence for content slides (20-30 words, 1 full sentence, representing a big statement).
- Always generate section headings.
- Sub-grid items must have both a title AND description (1-2 full sentences, not single words).
- Never leave any field empty or with placeholder text.
- For timeline slides, format each event bullet point as "Year/Date - Stage Title: Specific description of what happens" (e.g. "2024 Q1 - Discovery: Establish core parameters and target personas through research.").
- For process slides, format each step bullet point as "Step Title: Specific description of the action" (e.g. "Research: Gather requirements, analyze existing data, and identify constraints.").
- For 3-column/4-grid/comparison slides, format each bullet point as "Topic/Metric: Specific details/numbers".
- NEVER generate a slide with fewer than 4 bullet points. Aim for 4-6 per slide.
- For EVERY architecture slide (slide_type "architecture" or "tech_stack"), you MUST include a "drawio_slots" JSON object with the slot fills. Do NOT generate raw XML. You MUST set the slide_type to "architecture" or "tech_stack".
- For each slide, you MUST provide an "icon_keyword" which is a single word or short phrase describing the core topic of this slide (e.g. ai, data, python, business, summary, introduction, timeline, security, design, health, education, rocket, mobile, chart, team, etc.).
- NEVER leave "icon_keyword" empty or null.
- For title/hero slides: use the main topic keyword.
- For conclusion slides: always use "summary".
- For agenda slides: always use "agenda".

VISUAL ASSET FIELDS (include when relevant):
- "image_keyword": A descriptive search phrase for hero/feature images (e.g. "artificial intelligence technology"). Include for hero and 1-column slides.
- "icon_keywords": An array of short icon keywords, one per column/step (e.g. ["growth", "team", "target"]). Include for 3-column and process slides.
""" + DRAWIO_ARCHITECTURE_INSTRUCTIONS + """
- "chart_data": An object with keys "type" (bar|pie|line), "labels" (array of strings), "values" (array of numbers), and "title" (string). Include for dashboard and data slides.
- "table_data": An object with keys "headers" (array of strings) and "rows" (array of arrays of strings). Include for comparison and table slides.

STRUCTURED LAYOUT FIELDS - MANDATORY for specific slide types:
- For slide_type "process": MUST include "process_steps" - an array of 3-5 objects, each with "title" (short phase name) and "body" (1-2 sentence description). Example: [{"title": "Data Collection", "body": "Gather raw datasets from multiple sensors and IoT endpoints for preprocessing."}]
- For slide_type "timeline": MUST include "timeline_steps" - an array of 3-6 objects, each with "title" (date/period/milestone) and "description" (what happened). Example: [{"title": "2023 Q1", "description": "Initial prototype developed and tested with focus groups."}]
- For slide_type "comparison": MUST include "comparison_items" - an array of 3-5 objects, each with "left" (text for left column) and "right" (text for right column). Also include "comparison_left_title" and "comparison_right_title" (column headings).
- For slide_type "data" or "metrics": MUST include "dashboard_metrics" - an array of 3-4 objects, each with "label" (metric name) and "value" (metric value as string). Also include "dashboard_insight" (1-2 sentence executive summary).
- For slide_type "architecture" or "tech_stack": MUST include "architecture_nodes" - an array of 3-6 objects, each with "title" (component name) and "description" (what it does).
- For 3-column or 4-grid content slides: include "grid_items" - an array of 3-4 objects, each with "title" (item heading) and "description" (1-2 sentence explanation).
- NEVER use generic placeholder names like "Phase 1", "Step 1", "Metric 1", "Option A", "Feature 1". Always use topic-specific, meaningful names.

Output format:
{
  "deck_title": "...",
  "slides": [
    {
      "slide_type": "title|abstract|problem|solution|tech_stack|architecture|process|comparison|data|content|conclusion",
      "title": "...",
      "icon_keyword": "pandas",
      "bullet_points": ["...", "...", "..."],
      "visual_type": "none|hero|icons|flowchart|architecture|mindmap|chart|table|process|comparison|infographic",
      "visual_items": ["...", "...", "..."],
      "speaker_notes": "...",
      "image_keyword": "optional - descriptive image search phrase",
      "icon_keywords": ["optional", "icon", "keywords"],
      "drawio_slots": {
        "cloud_label": "AWS Cloud Platform",
        "vpc_label": "Production VPC",
        "zone1_label": "Availability Zone 1",
        "zone2_label": "Availability Zone 2",
        "z1_comp1_name": "API Gateway\\nNginx",
        "z1_comp1_fill": "#ff8000",
        "z1_comp2_name": "Auth\\nNode.js",
        "z1_comp2_fill": "#dae8fc",
        "z1_comp3_name": "User DB\\nPostgreSQL",
        "z1_comp3_fill": "#d5e8d4",
        "z2_comp1_name": "Order Service\\nJava",
        "z2_comp1_fill": "#dae8fc",
        "z2_comp2_name": "Payment Service\\nGo",
        "z2_comp2_fill": "#dae8fc",
        "z2_comp3_name": "Redis Cache\\nCluster",
        "z2_comp3_fill": "#fff2cc",
        "lb_label": "Application LB",
        "ext1_label": "User",
        "ext2_label": "Internet"
      },
      "chart_data": {"type": "bar", "labels": [], "values": [], "title": ""},
      "table_data": {"headers": [], "rows": []},
      "process_steps": [{"title": "...", "body": "..."}],
      "timeline_steps": [{"title": "...", "description": "..."}],
      "comparison_items": [{"left": "...", "right": "..."}],
      "comparison_left_title": "...",
      "comparison_right_title": "...",
      "dashboard_metrics": [{"label": "...", "value": "..."}],
      "dashboard_insight": "...",
      "architecture_nodes": [{"title": "...", "description": "..."}],
      "grid_items": [{"title": "...", "description": "..."}]
    }
  ]
}

CRITICAL layout capacity budgets to design for:
- 1-column: Hero image top, title + body below. Max 90 words body.
- 2-column: Left text/bullets, right image/chart. Max 80 words in the text column.
- 3-column: Icon + heading + short text. Max 3 columns, 42 words per column.
- 4-grid: 2x2 metric cards or icon boxes. Max 4 cells, 25 words per cell.
- Hero layout: Centered title. Max 15 words.
- Dashboard layout: Stat row + chart + table/insight. Max 80 words total.
- Architecture layout: Diagram canvas + labels. Max 60 words labels.
- Timeline layout: Horizontal/vertical dated events. Max 50 words total."""


def generate_outline(
    topic,
    slide_count,
    tone,
    sample_titles,
    source_text="",
    template_blueprint=None,
    architecture_type=None,
) -> dict:
    tone_key = tone.lower()
    tone_desc = TONE_DESCRIPTIONS.get(tone_key, TONE_DESCRIPTIONS["professional"])
    tone_hint = f"\n- Tone: {tone.capitalize()}\n- Tone Design & Content Principles:\n{tone_desc}\n"

    context = f"Source document content:\n{source_text}" if source_text else ""
    
    titles_hint = ""
    if sample_titles:
        titles_hint = (
            f"- CRITICAL: The user has requested these specific slide titles: '{sample_titles}'. "
            "You MUST generate slides using these exact titles in the order listed. "
            "Tailor the bullet points and visual elements of each slide to directly and deeply cover the respective title."
        )

    template_hint = ""
    if template_blueprint:
        template_hint = (
            "Uploaded custom template blueprint:\n"
            f"{json.dumps(template_blueprint, ensure_ascii=True)}\n"
            "Use exactly this slide order and detected_role intent. Replace old "
            "template content with new content for the user's topic. Match each "
            "slide's suggested_visual_type when choosing visual_type."
        )

    if source_text:
        intro_line = (
            f"Create EXACTLY {slide_count} slides using the Source document content below.\n"
            "The Source document content is the PRIMARY SOURCE OF TRUTH.\n"
            "The topic is only a label.\n"
            "ALL slide titles, bullet points, visual items, charts, timelines, architecture diagrams, speaker notes must be derived from the source content.\n"
            "If there is any conflict between topic and source content, source content always wins.\n"
            "Do not invent concepts not present in the source."
        )
        context_rule = (
            "- CRITICAL - HIGHEST PRIORITY\n"
            "The provided Source document content is the PRIMARY SOURCE OF TRUTH.\n"
            "All slides must be based on the source text.\n"
            "Do not rely on prior knowledge.\n"
            "Do not generate generic content.\n"
            "Do not hallucinate.\n"
            "The topic string is only a label.\n"
            "Source content overrides topic."
        )
    else:
        intro_line = f"Create EXACTLY {slide_count} slides (no more, no fewer) about: {topic}"
        context_rule = ""

    template_rule = (
        "- CRITICAL: If a template blueprint is provided, generate one output "
        "slide for each template slide and preserve its intent, such as title, "
        "abstract, problem statement, tech stack, architecture, or conclusion."
        if template_blueprint else ""
    )

    architecture_hint = ""
    if architecture_type:
        architecture_hint = f"""
ARCHITECTURE REQUIREMENT:

The user selected architecture type:

{architecture_type}

You MUST include one slide whose slide_type is "architecture".

That slide MUST contain:

- drawio_slots
- architecture_nodes
- visual_type = "architecture"

Generate the architecture according to the chosen type.

Examples:

ai_pipeline →
Data Sources → ETL → Vector DB → LLM → API → User

microservices →
Gateway → Auth → Services → Databases

aws →
CloudFront → ALB → EC2 → RDS

ml_pipeline →
Dataset → Training → Model Registry → Inference API

kubernetes →
Ingress → Pods → Services → Databases

This architecture slide is mandatory.
"""

    user_prompt = f"""{intro_line}
Tone: {tone}
{tone_hint}
{architecture_hint}
{titles_hint}
{context}
{template_hint}

Rules:
- You MUST generate EXACTLY {slide_count} slides. Not one more, not one fewer.
- First slide must be type 'title'
- Last slide must be type 'conclusion'
- Each content slide MUST have 4-6 detailed, substantive bullet points. Never generate bullet points shorter than 12 words; each bullet must be 12-20 words long and be a complete meaningful sentence.
- Always generate the hero/lead sentence for content slides (20-30 words, 1 full sentence, representing a big statement).
- Always generate section headings.
- Sub-grid items must have both a title AND description (1-2 full sentences, not single words).
- Respect the capacity constraints outlined in the system prompt. Split dense ideas across slides instead of producing crowded paragraphs.
- Add a useful visual_type for every non-title slide
- visual_items must be short labels for icons, nodes, chart categories, table rows, or process steps
- Speaker notes: 1-2 sentences per slide
- For hero and 1-column slides, include "image_keyword" with a descriptive search phrase for a stock photo
- For 3-column and process slides, include "icon_keywords" array with one short keyword per column/step
- For EVERY architecture/tech_stack slide, include a "drawio_slots" object filled with component names and colors as described in the ARCHITECTURE DIAGRAM REQUIREMENTS. DO NOT output raw mxGraphModel XML under drawio_slots.
- For dashboard/data slides, include "chart_data" with type, labels, values, and title
- For comparison/table slides, include "table_data" with headers and rows arrays
- MANDATORY STRUCTURED FIELDS: For process slides include "process_steps", for timeline slides include "timeline_steps", for comparison slides include "comparison_items" + "comparison_left_title" + "comparison_right_title", for data/metrics slides include "dashboard_metrics" + "dashboard_insight", for architecture slides include "architecture_nodes", for 3-column/4-grid slides include "grid_items". Each structured field must contain topic-specific content - NEVER use generic placeholders.
{context_rule}
{template_rule}
- Return ONLY valid JSON"""

    # Print debugging information before call_llm
    print("====================================")
    print("[SOURCE LENGTH]")
    print(len(source_text) if source_text else 0)
    print()
    print("[TOPIC]")
    print(topic)
    print()
    print("[SOURCE PREVIEW]")
    print(source_text[:1500] if source_text else "")
    print()
    print("====================================")

    # Logging support for YouTube mode
    youtube_url = None
    frame = inspect.currentframe()
    try:
        while frame:
            locals_dict = frame.f_locals
            if "youtube_url" in locals_dict and locals_dict["youtube_url"]:
                youtube_url = locals_dict["youtube_url"]
                break
            frame = frame.f_back
    except Exception:
        pass
    finally:
        del frame

    if youtube_url and source_text:
        from services.youtube_service import extract_video_id
        try:
            video_id = extract_video_id(youtube_url)
        except Exception:
            video_id = None

        transcript_len = 0
        if video_id:
            transcript_len = TRANSCRIPT_LENGTHS.get(video_id, 0)
            if not transcript_len:
                try:
                    from services.transcript_service import fetch_transcript
                    t = fetch_transcript(video_id)
                    transcript_len = len(t)
                    TRANSCRIPT_LENGTHS[video_id] = transcript_len
                except Exception:
                    transcript_len = len(source_text) * 4

        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        os.makedirs(logs_dir, exist_ok=True)

        # Append to logs/video_summary_log.txt
        txt_path = os.path.join(logs_dir, "video_summary_log.txt")
        txt_entry = (
            "====================================================\n"
            f"Timestamp:\n{timestamp_str}\n\n"
            f"Video URL:\n{youtube_url}\n\n"
            f"Topic:\n{topic}\n\n"
            f"Transcript Length:\n{transcript_len}\n\n"
            f"Summary Length:\n{len(source_text)}\n\n"
            f"Summary Preview:\n{source_text[:3000]}\n"
            "====================================================\n"
        )
        try:
            with open(txt_path, "a", encoding="utf-8") as f:
                f.write(txt_entry)
        except Exception as e:
            print(f"[SLIDE_PLANNER] Warning: Failed to write to txt log: {e}")

        # Append to logs/video_summary_log.json
        json_path = os.path.join(logs_dir, "video_summary_log.json")
        json_entry = {
            "timestamp": timestamp_str,
            "video_url": youtube_url,
            "topic": topic,
            "transcript_length": transcript_len,
            "summary_length": len(source_text),
            "summary_preview": source_text[:3000]
        }
        try:
            with open(json_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(json_entry, indent=4) + "\n")
        except Exception as e:
            print(f"[SLIDE_PLANNER] Warning: Failed to write to json log: {e}")

    raw = call_llm(SYSTEM_PROMPT, user_prompt)

    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

    try:
        deck = json.loads(raw)
    except Exception as e:
        print("[SLIDE_PLANNER] Failed to parse JSON. Raw LLM response:")
        print(raw)
        raise e

    if architecture_type:
        has_arch = any(
            s.get("slide_type", "").lower()
            in ("architecture", "tech_stack")
            for s in deck["slides"]
        )
        if not has_arch:
            deck["slides"].insert(
                2,
                {
                    "slide_type": "architecture",
                    "title": architecture_type.replace("_", " ").title(),
                    "visual_type": "architecture",
                    "architecture_nodes": [],
                    "drawio_slots": {
                        "cloud_label": architecture_type.upper(),
                        "vpc_label": "Production Layer",
                        "zone1_label": "Input Layer",
                        "zone2_label": "Processing Layer",

                        "z1_comp1_name": "Data Sources",
                        "z1_comp1_fill": "#dae8fc",

                        "z1_comp2_name": "ETL",
                        "z1_comp2_fill": "#dae8fc",

                        "z1_comp3_name": "Vector DB",
                        "z1_comp3_fill": "#d5e8d4",

                        "z2_comp1_name": "LLM",
                        "z2_comp1_fill": "#ff8000",

                        "z2_comp2_name": "API Layer",
                        "z2_comp2_fill": "#dae8fc",

                        "z2_comp3_name": "Cache",
                        "z2_comp3_fill": "#fff2cc",

                        "lb_label": "Gateway",
                        "ext1_label": "User",
                        "ext2_label": "Internet"
                    }
                }
            )

    # Convert drawio_slots to drawio_xml using the coordinate template
    if "slides" in deck:
        for slide in deck["slides"]:
            stype = slide.get("slide_type", "").lower()
            if stype in ("architecture", "tech_stack"):
                slots = slide.get("drawio_slots")
                if slots:
                    print("[SLIDE_PLANNER] Found drawio_slots, building XML...")
                    slide["drawio_xml"] = build_architecture_xml_from_slots(slots)
                elif not slide.get("drawio_xml"):
                    print("[SLIDE_PLANNER] No drawio_slots or drawio_xml found, using defaults...")
                    slide["drawio_xml"] = build_architecture_xml_from_slots({})
    
    # Run the dynamic layout engine on the planned slides
    if "slides" in deck:
        deck["slides"] = assign_layouts(deck["slides"], max_slides=slide_count)
        
        # Enrich slides with icons
        from services.icon_resolver import resolve_icon_emoji
        for slide in deck["slides"]:
            icon_keyword = slide.get('icon_keyword', '')
            if icon_keyword:
                slide['icon_emoji'] = resolve_icon_emoji(icon_keyword)
            else:
                slide['icon_emoji'] = ''
        
    print("=== SLIDE PLANNER DEBUG ===")
    for i, slide in enumerate(deck.get('slides', [])):
        print(f"Slide {i+1}: type={slide.get('slide_type')} "
              f"| has_drawio={'drawio_xml' in slide and bool(slide.get('drawio_xml'))} "
              f"| drawio_length={len(slide.get('drawio_xml') or '')}")
    print("===========================")
        
    return deck


def generate_outline_from_template(
    topic: str,
    template_schema: dict,
    tone: str,
    source_text: str = "",
) -> dict:
    """Generate slide content tailored to a template's layout structure.
    
    The LLM is zone-aware, generating flat dictionaries with keys matching
    each slide's exact shape roles and respecting the estimated capacity.
    """
    tone_key = tone.lower()
    tone_desc = TONE_DESCRIPTIONS.get(tone_key, TONE_DESCRIPTIONS["professional"])
    
    slide_count = template_schema.get("slide_count", 5)
    theme_info = template_schema.get("theme", {})
    slides_schema = template_schema.get("slides", [])
    
    # Build per-slide layout zones and capacity for the LLM
    slide_data_list = []
    
    allowed_list = {
        "title", "subtitle", "body1", "body2", "body3",
        "card1_title", "card1_description",
        "card2_title", "card2_description",
        "card3_title", "card3_description",
        "card4_title", "card4_description",
        "quote", "stat", "metric",
        "image1", "image2", "image3", "image_left", "image_right", "hero_image"
    }
    
    skip_keywords = (
        "icon", "logo", "vector", "symbol", "circle", "ellipse",
        "shape", "decorative", "other", "footer", "caption", "label",
        "chart", "table", "arrow"
    )

    for i, s in enumerate(slides_schema):
        layout = s.get("inferred_layout", "content")
        zones = []
        allowed_roles = []
        filtered_roles = []
        image_roles = []
        
        for zone in s.get("zones", []):
            role = zone.get("role", "other")
            role_lower = role.lower()
            
            # Check if role contains any skip keywords or is not in allowed list
            is_skipped = any(k in role_lower for k in skip_keywords) or (role not in allowed_list)
            
            if is_skipped:
                filtered_roles.append(role)
            else:
                zone_dict = {
                    "role": role,
                    "capacity": zone.get("capacity", 40),
                    "width_pct": zone.get("width_pct", 50),
                    "height_pct": zone.get("height_pct", 30),
                    "left_pct": zone.get("left_pct", 0),
                    "top_pct": zone.get("top_pct", 0)
                }
                zones.append(zone_dict)
                allowed_roles.append(role)
                if role.startswith("image") or "image" in role_lower:
                    image_roles.append(role)
                    
        print(f"[PLANNER TEMPLATE ZONES] Slide {i + 1}:")
        print(f"  Allowed roles: {allowed_roles}")
        print(f"  Filtered roles: {filtered_roles}")
        print(f"  Image roles: {image_roles}")
        
        slide_data_list.append({
            "slide_index": i,
            "layout": layout,
            "zones": zones
        })
        
    slides_layout_info = json.dumps(slide_data_list, indent=2)
    
    context = f"Source document content:\n{source_text}" if source_text else ""
    
    system_prompt = """You are a professional presentation content writer.
Generate slide content as valid JSON only. No markdown, no explanation — pure JSON.

CRITICAL RULES:
- Generate content matching the EXACT zones of each slide in the template configuration.
- For each slide, return a flat dictionary of keys matching the zone roles.
- For text roles (e.g. title, subtitle, body1, body2, card1_title, card1_description, etc.), the value must be a flat string.
- You MUST obey strict word capacity limits for each zone. The word count of the generated text for any role must not exceed its specified "capacity" value.
- Do NOT generate generic body1/body2/body3 paragraphs if card roles (e.g. card1_title, card1_description) are provided. Use card-aware content.
- For image roles (roles starting with 'image' or containing 'image', such as 'image1', 'image2', 'image3', 'image_left', 'image_right', 'hero_image'), generate a key like "[role]_keyword" (e.g. "image1_keyword", "image_left_keyword", "hero_image_keyword") containing a highly specific stock photo search query. Never leave these image keywords empty or generic.
- Never generate search keywords or change values for icon roles, decorative shapes, labels, captions, footers, charts, tables, or other unallowed roles.
- Avoid generic placeholders or dummy content. All content must be tailored to the presentation topic."""

    user_prompt = f"""Create content for EXACTLY {slide_count} slides about: {topic}
Tone: {tone}
{tone_desc}

Template theme: heading_font={theme_info.get('heading_font', 'unknown')}, body_font={theme_info.get('body_font', 'unknown')}, colors={json.dumps(theme_info.get('colors', {}))}

Template slide layout zones configuration (the absolute source of truth):
{slides_layout_info}

{context}

Generate a JSON object matching this structure:
{{
  "deck_title": "...",
  "template_mode": true,
  "slides": [
    // For each slide, return the slide_index, layout, and a flat map of content matching its zones roles.
    // Ensure you generate values for all text zones using their capacity as the word limit.
    // Example slide with "title", "card1_title", "card1_description", "card2_title", "card2_description", "image1" zones:
    {{
      "slide_index": 1,
      "layout": "icon_cards",
      "title": "Innovation and Growth",
      "card1_title": "Innovation",
      "card1_description": "Create next-gen solutions.",
      "card2_title": "Growth",
      "card2_description": "Scale businesses globally.",
      "image1_keyword": "modern workspace collaboration"
    }}
  ]
}}

Rules:
- Return EXACTLY {slide_count} slides, matching the slide_index sequence.
- Do not add any keys that are not defined in the template slide's zones configuration.
- Word counts must strictly follow the "capacity" value defined in the zones list above.
- Return ONLY valid JSON."""

    raw = call_llm(system_prompt, user_prompt)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        
    try:
        deck = json.loads(raw)
    except Exception as e:
        print("[SLIDE_PLANNER] Failed to parse template outline JSON. Raw:")
        print(raw)
        raise e
        
    deck["template_mode"] = True
    
    # Post-process generated slide content to ensure image keywords are never empty
    # and unallowed keys are removed.
    if "slides" in deck:
        for idx, slide_content in enumerate(deck["slides"]):
            schema_slide = slides_schema[idx] if idx < len(slides_schema) else None
            
            slide_allowed_roles = set()
            slide_image_roles = set()
            
            if schema_slide:
                for zone in schema_slide.get("zones", []):
                    role = zone.get("role", "other")
                    role_lower = role.lower()
                    is_skipped = any(k in role_lower for k in skip_keywords) or (role not in allowed_list)
                    if not is_skipped:
                        slide_allowed_roles.add(role)
                        if role.startswith("image") or "image" in role_lower:
                            slide_image_roles.add(role)
            
            # Filter keys generated by the LLM
            keys_to_delete = []
            for k in list(slide_content.keys()):
                if k in ("slide_index", "layout"):
                    continue
                if k.endswith("_keyword") or k == "image_keyword":
                    base_role = k[:-8] if k.endswith("_keyword") else "image"
                    if k == "image_keyword" and slide_image_roles:
                        continue
                    if any(img_r in k for img_r in slide_image_roles):
                        continue
                if k in slide_allowed_roles:
                    continue
                keys_to_delete.append(k)
                
            for k in keys_to_delete:
                slide_content.pop(k, None)
                
            # Guarantee image keywords are populated
            for img_role in slide_image_roles:
                kw_key = f"{img_role}_keyword"
                if not slide_content.get(kw_key):
                    fallback_kw = slide_content.get("image_keyword")
                    if fallback_kw:
                        slide_content[kw_key] = fallback_kw
                    else:
                        title_text = slide_content.get("title", "") or topic
                        slide_content[kw_key] = f"{title_text} {img_role}".strip()
                        
    print(f"[SLIDE_PLANNER] Template outline generated: {len(deck.get('slides', []))} slides")
    return deck
