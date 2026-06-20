"""
Slide Planner V2 — Template-Aware Content Generation
=====================================================
Generates LLM-driven content that maps 1:1 to template zone roles.

This is the V2 pipeline planner. It:
  - Only sends allowed roles (title, subtitle, body1-4, image1-3) to the LLM
  - Returns flat-dict slides with template_mode = True
  - Enforces strict word limits based on zone capacity
  - Generates image keywords for every image placeholder
  - Never generates content for icons, decorative shapes, footers, etc.
"""

import json
import re
from services.llm_client import call_llm


# ─── Tone descriptions ───────────────────────────────────────────────
TONE_DESCRIPTIONS = {
    "professional":  "Formal, corporate tone with clear and concise language.",
    "technical":     "Precise, data-driven tone suitable for engineering or scientific audiences.",
    "lavish":        "Luxurious, premium tone with elegant and sophisticated language.",
    "academic":      "Scholarly, well-referenced tone for educational or research contexts.",
    "creative":      "Bold, imaginative tone with vivid language and fresh metaphors.",
    "education":     "Friendly, accessible tone optimized for teaching and learning.",
    "ecommerce":     "Persuasive, benefits-focused tone for products and conversions.",
    "neumorphism":   "Modern, tech-forward tone with clean minimal language.",
}

# ─── Roles the LLM is allowed to generate content for ────────────────
ALLOWED_CONTENT_ROLES = {
    "title", "subtitle",
    "body1", "body2", "body3", "body4",
}

# Roles that should produce image/icon keywords instead of text
IMAGE_ROLES = {
    "image1", "image2", "image3",
    "image_left", "image_right", "hero_image",
    "icon1", "icon2",
}

# Roles that must NEVER reach the LLM
SKIP_KEYWORDS = (
    "icon", "logo", "vector", "symbol", "circle", "ellipse",
    "shape", "decorative", "other", "footer", "caption", "label",
    "chart", "table", "arrow", "note", "source", "reference",
    "separator", "line", "border",
)

# ─── Word limits per role ─────────────────────────────────────────────
DEFAULT_WORD_LIMITS = {
    "title":    8,
    "subtitle": 12,
    "body1":    18,
    "body2":    18,
    "body3":    18,
    "body4":    18,
}


def generate_outline_from_template_v2(
    topic: str,
    template_schema: dict,
    tone: str,
    source_text: str = "",
) -> dict:
    """Generate a content outline for a V2 template schema.

    Args:
        topic: Presentation topic string.
        template_schema: V2 schema dict from analyze_template_v2().
        tone: Tone name (matched against TONE_DESCRIPTIONS).
        source_text: Optional source document text for context.

    Returns:
        Dict with deck_title, template_mode=True, and slides list.
        Each slide is a flat dict with role-name keys.
    """
    print(f"[PLANNER_V2] Generating outline for topic='{topic}', tone='{tone}'")

    slide_count = template_schema.get("slide_count", 5)
    theme_info = template_schema.get("theme", {})
    slides_schema = template_schema.get("slides", [])

    # ── Build per-slide zone info for the LLM ──
    slide_data_list = []
    slide_image_roles_map = {}  # slide_index -> list of image role names

    for s_schema in slides_schema:
        slide_idx = s_schema.get("slide_index", 0)
        zones = s_schema.get("zones", [])

        filtered_zones = []
        image_roles_for_slide = []

        for zone in zones:
            role = zone.get("role", "other")
            role_lower = role.lower()

            # Handle image/icon roles separately
            if role in IMAGE_ROLES or role_lower.startswith("image") or role_lower.startswith("icon"):
                image_roles_for_slide.append(role)
                continue

            # Skip anything with forbidden keywords
            if any(k in role_lower for k in SKIP_KEYWORDS):
                continue

            # Only allow title, subtitle, and body1-N roles
            is_valid_content_role = role in ALLOWED_CONTENT_ROLES or role.startswith("body") or role.startswith("title") or role.startswith("subtitle")
            if not is_valid_content_role:
                continue

            # Determine word limit based on original text length to avoid overflow and overlapping
            orig_text = zone.get("original_text", "")
            orig_words = len(orig_text.split())
            
            if orig_words == 0:
                word_limit = 12
            elif orig_words <= 3:
                word_limit = orig_words + 1
            elif orig_words <= 8:
                word_limit = orig_words + 2
            else:
                word_limit = int(orig_words * 1.2) + 1

            # Ensure word_limit is within safe bounds of capacity and reasonable maximums
            capacity = zone.get("capacity", 40)
            word_limit = min(word_limit, max(5, capacity))

            filtered_zones.append({
                "role": role,
                "word_limit": word_limit,
                "original_text": orig_text,
            })

        slide_data_list.append({
            "slide_index": slide_idx + 1,  # 1-based for LLM
            "zones": filtered_zones,
            "image_roles": image_roles_for_slide,
        })
        slide_image_roles_map[slide_idx] = image_roles_for_slide

    slides_layout_info = json.dumps(slide_data_list, indent=2)

    # ── Build LLM prompts ──
    tone_desc = TONE_DESCRIPTIONS.get(tone, TONE_DESCRIPTIONS["professional"])

    system_prompt = _build_system_prompt(tone_desc)
    user_prompt = _build_user_prompt(
        topic=topic,
        slide_count=slide_count,
        tone_desc=tone_desc,
        theme_info=theme_info,
        slides_layout_info=slides_layout_info,
        source_text=source_text,
    )

    # ── Call LLM ──
    print(f"[PLANNER_V2] Calling LLM with {slide_count} slides...")
    raw_response = call_llm(system_prompt, user_prompt)

    # ── Parse response ──
    deck = _parse_llm_response(raw_response, topic)

    # ── Post-process: enforce allowed keys + image keyword fallbacks ──
    for slide_content in deck.get("slides", []):
        s_idx = slide_content.get("slide_index", 1) - 1  # back to 0-based

        # Remove unauthorized keys
        allowed_keys = {"slide_index", "layout"}
        for sd in slide_data_list:
            if sd["slide_index"] == s_idx + 1:
                allowed_keys.update(z["role"] for z in sd["zones"])
                allowed_keys.update(f"{ir}_keyword" for ir in sd["image_roles"])
                break

        keys_to_remove = [
            k for k in list(slide_content.keys())
            if k not in allowed_keys and not k.endswith("_keyword")
        ]
        for k in keys_to_remove:
            if k not in ("slide_index", "layout", "title", "subtitle"):
                del slide_content[k]

        # Enforce word limits
        for sd in slide_data_list:
            if sd["slide_index"] == s_idx + 1:
                for z in sd["zones"]:
                    role = z["role"]
                    limit = z["word_limit"]
                    val = slide_content.get(role, "")
                    if isinstance(val, str) and len(val.split()) > limit:
                        words = val.split()[:limit]
                        slide_content[role] = " ".join(words)
                break

        # Image keyword fallbacks
        img_roles = slide_image_roles_map.get(s_idx, [])
        for img_role in img_roles:
            kw_key = f"{img_role}_keyword"
            if not slide_content.get(kw_key):
                # Try generic image_keyword
                fallback = slide_content.get("image_keyword", "")
                if fallback:
                    slide_content[kw_key] = fallback
                else:
                    # Build from title + topic
                    title_text = slide_content.get("title", "") or topic
                    slide_content[kw_key] = f"{title_text} professional photo".strip()

    # Force template_mode flag
    deck["template_mode"] = True
    if "deck_title" not in deck:
        deck["deck_title"] = topic

    print(f"[PLANNER_V2] Outline generation complete: {len(deck.get('slides', []))} slides")
    return deck


# ─── Private helpers ──────────────────────────────────────────────────

def _build_system_prompt(tone_desc: str) -> str:
    return f"""You are a presentation content generator.
You receive a list of slides, each with specific text zones, their word limits, and the original template text (original_text).
Your job is to generate content for EXACTLY those zones — nothing more, nothing less.

RULES:
1. For each slide, return a flat JSON object with keys matching the zone roles.
2. Each text zone has a word_limit. Do NOT exceed it. Keep content tight and impactful.
3. For image zones (like image1, image2), generate a key like "[role]_keyword" containing a highly specific stock photo search query (3-6 words).
4. For icon zones (like icon1, icon2), generate a key like "[role]_keyword" containing a simple 1-2 word noun describing a flat icon or symbol representing that concept (e.g. "rocket", "gear", "brain", "chart"). Never leave image/icon keywords empty.
5. Do NOT add keys that are not in the zone list.
6. Use the tone: {tone_desc}
7. Content must be specific and relevant to the topic. No generic placeholders.
8. Title should be punchy and concise (maximum 8 words).
9. Subtitle should expand on the title (maximum 12 words).
10. Body text (body1, body2, etc.) must match the word limit specified for each zone. Generate concise, card-friendly text.
11. No paragraph should exceed two lines. Keep every zone short and scannable.
12. CRITICAL: Look at the "original_text" provided for each text zone. You MUST rewrite the content to match the new topic, but you must match the exact style, purpose, semantic context, and length of the original_text. For example, if the original_text is a step (e.g., 'Step 1: Planning'), rewrite it as a step for the new topic (e.g., 'Step 1: Design'). If the original_text is a short label (e.g., 'Introduction'), rewrite it as a short label (e.g., 'Overview'). If the original_text contains tech names or numbers, replace them with appropriate values for the new topic. Do NOT add extra paragraphs or content.
13. CRITICAL: ALL slides in the deck MUST be about the SAME topic. Never mix different projects, subjects, or unrelated content across slides. If the topic is "festivals", every slide discusses festivals. If the topic is "AI Study Planner", every slide discusses that single project. Never introduce unrelated subjects like random algorithms, diseases, or other projects.

Return ONLY valid JSON. No markdown fences, no commentary."""


def _build_user_prompt(
    topic: str,
    slide_count: int,
    tone_desc: str,
    theme_info: dict,
    slides_layout_info: str,
    source_text: str,
) -> str:
    prompt = f"""Generate content for a {slide_count}-slide presentation about: "{topic}"

Tone: {tone_desc}
Theme fonts: heading={theme_info.get('heading_font', 'Calibri')}, body={theme_info.get('body_font', 'Calibri')}

Here are the slides with their zones, word limits, and original template text:
{slides_layout_info}

Return a JSON object with this structure:
{{
  "deck_title": "Short deck title",
  "slides": [
    {{
      "slide_index": 1,
      "title": "Slide Title Here",
      "subtitle": "Expanding subtitle text",
      "body1": "First body paragraph with details...",
      "image1_keyword": "specific photo search query",
      "icon1_keyword": "rocket"
    }}
  ]
}}

Each slide's keys must EXACTLY match the zone roles listed above.
For image and icon roles, generate "[role]_keyword" keys with search queries."""

    if source_text:
        # Truncate source text to avoid token overflow
        max_source = 2000
        if len(source_text) > max_source:
            source_text = source_text[:max_source] + "..."
        prompt += f"\n\nSource document context:\n{source_text}"

    return prompt


def _parse_llm_response(raw: str, topic: str) -> dict:
    """Parse LLM JSON response with fallback handling."""
    # Strip markdown code fences
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        # Remove opening fence
        first_newline = cleaned.index("\n")
        cleaned = cleaned[first_newline + 1:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        deck = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"[PLANNER_V2] JSON parse error: {e}")
        # Try to extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', cleaned)
        if json_match:
            try:
                deck = json.loads(json_match.group())
            except json.JSONDecodeError:
                print("[PLANNER_V2] Fallback JSON parse also failed. Returning minimal deck.")
                deck = {
                    "deck_title": topic,
                    "slides": [{"slide_index": 1, "title": topic}]
                }
        else:
            deck = {
                "deck_title": topic,
                "slides": [{"slide_index": 1, "title": topic}]
            }

    # Ensure slides is a list
    if "slides" not in deck or not isinstance(deck["slides"], list):
        deck["slides"] = [{"slide_index": 1, "title": topic}]

    return deck
