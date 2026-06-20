"""
Layout Engine
=============
Handles layout selection scoring, content fitting into zones,
overflow resolution, and automatic slide splitting.
"""

from typing import List, Dict, Tuple, Optional
import re
from models.layout_definitions import ALL_LAYOUTS, LayoutDefinition, LayoutZone, get_layout


def count_words(text: str) -> int:
    """Helper to count words in a string."""
    if not text:
        return 0
    return len(re.findall(r'\b\w+\b', text))


# ─── Scoring Algorithm ────────────────────────────────────────────────

def score_layout(slide_dict: dict, layout: LayoutDefinition, recent_layouts: List[str]) -> float:
    """
    Score a layout against slide content using the weighted rubric:
    - Content type match: 0.35
    - Word count fits within capacity: 0.25
    - Block count matches column count: 0.20
    - Visual intent has matching asset: 0.12
    - Variety penalty (avoid repeating same layout 3x in a row): -0.08
    """
    score = 0.0

    # 1. Content Type Match (Weight 0.35)
    # Map slide_type or inferred content_type to best_for tags
    stype = slide_dict.get("slide_type", "content").lower()
    
    # Map slide_type to layout best_for tags
    type_matches = False
    if stype == "title" and "title" in layout.best_for:
        type_matches = True
    elif stype == "conclusion" and "conclusion" in layout.best_for:
        type_matches = True
    elif stype == "comparison" and "comparison" in layout.best_for:
        type_matches = True
    elif stype in ("architecture", "tech_stack") and "architecture" in layout.best_for:
        type_matches = True
    elif stype in ("process", "timeline") and "timeline" in layout.best_for:
        type_matches = True
    elif stype in ("data", "metrics") and "data" in layout.best_for:
        type_matches = True
    elif stype in ("content", "abstract", "problem", "solution") and "content" in layout.best_for:
        type_matches = True

    content_type_score = 1.0 if type_matches else 0.2
    score += content_type_score * 0.35

    # 2. Word Count Fit (Weight 0.25)
    # Calculate total words in slide title + bullets
    title_words = count_words(slide_dict.get("title", ""))
    bullets = slide_dict.get("bullet_points", [])
    bullet_words = sum(count_words(b) for b in bullets)
    total_words = title_words + bullet_words

    if total_words <= layout.capacity_words:
        word_fit_score = 1.0
    else:
        # Graceful decay: score drops as word count exceeds capacity
        overflow_ratio = (total_words - layout.capacity_words) / layout.capacity_words
        word_fit_score = max(0.0, 1.0 - overflow_ratio)
    score += word_fit_score * 0.25

    # 3. Block Count Matches Column Count (Weight 0.20)
    # Block count is the number of bullet points
    block_count = len(bullets)
    col_count = layout.column_count
    
    if col_count == 1:
        # 1-column layouts fit any reasonably small block count well
        block_match_score = 1.0 if 1 <= block_count <= 4 else 0.7
    elif col_count == block_count:
        block_match_score = 1.0
    else:
        # Penalty for mismatch in column count vs block count
        diff = abs(block_count - col_count)
        block_match_score = max(0.0, 1.0 - 0.25 * diff)
    
    score += block_match_score * 0.20

    # 4. Visual Intent Match (Weight 0.12)
    # Check if slide has visual intent and if layout has visual zones
    visual_type = slide_dict.get("visual_type", "none").lower()
    has_visual_intent = visual_type != "none"
    
    # Check if layout zones accept visual elements (image, chart, diagram, icon)
    layout_has_visual_zone = any(
        any(acc in zone.accepts for acc in ("image", "chart", "diagram", "icon"))
        for zone in layout.zones
    )

    if has_visual_intent == layout_has_visual_zone:
        visual_score = 1.0
    else:
        visual_score = 0.4
        
    score += visual_score * 0.12

    # 5. Variety Penalty (Weight -0.08)
    # Deduct if same layout used 3x in a row (i.e. last 2 layouts were the same as this layout)
    if len(recent_layouts) >= 2 and recent_layouts[-1] == layout.id and recent_layouts[-2] == layout.id:
        score -= 0.08

    return score


# ─── Content Fitting ──────────────────────────────────────────────────

def fit_content_to_layout(slide_dict: dict, layout: LayoutDefinition) -> dict:
    """
    Distribute slide title and bullets into layout zones.
    Returns a copy of the slide dict with a populated 'zone_content' dict.
    """
    result = dict(slide_dict)
    zone_content = {}

    title = slide_dict.get("title", "")
    bullets = slide_dict.get("bullet_points", [])

    if layout.id == "1-column":
        zone_content["headline"] = title
        zone_content["body"] = "\n".join(bullets)
        if slide_dict.get("visual_type") != "none":
            zone_content["hero_image"] = slide_dict.get("visual_items", [""])[0] if slide_dict.get("visual_items") else "Placeholder Image"

    elif layout.id == "2-column":
        # Left column gets first half of bullets, Right column gets second half or image
        zone_content["left_column"] = "\n".join(bullets[:3])
        if len(bullets) > 3:
            zone_content["right_column"] = "\n".join(bullets[3:])
        else:
            zone_content["right_column"] = "Visual Asset"

    elif layout.id == "3-column":
        # Distribute bullets across 3 columns
        for idx, zone_name in enumerate(["col_1", "col_2", "col_3"]):
            if idx < len(bullets):
                zone_content[zone_name] = bullets[idx]
            else:
                zone_content[zone_name] = ""

    elif layout.id == "4-grid":
        # Distribute bullets across 4 cells
        for idx, zone_name in enumerate(["cell_tl", "cell_tr", "cell_bl", "cell_br"]):
            if idx < len(bullets):
                zone_content[zone_name] = bullets[idx]
            else:
                zone_content[zone_name] = ""

    elif layout.id == "hero":
        zone_content["title"] = title
        zone_content["background_image"] = "Hero background"

    elif layout.id == "dashboard":
        zone_content["stat_row"] = bullets[0] if len(bullets) > 0 else "KPI Metric"
        zone_content["chart_area"] = "Dashboard Chart"
        zone_content["insight_area"] = "\n".join(bullets[1:]) if len(bullets) > 1 else ""

    elif layout.id == "architecture":
        zone_content["diagram_canvas"] = "Architecture Diagram"
        zone_content["labels"] = "\n".join(bullets)

    elif layout.id == "timeline":
        zone_content["events"] = "\n".join(bullets)

    result["zone_content"] = zone_content
    result["layout_id"] = layout.id
    return result


# ─── Overflow Handling ────────────────────────────────────────────────

def check_overflow(slide_dict: dict, layout: LayoutDefinition) -> bool:
    """Check if slide content exceeds layout limits."""
    # Check total words
    title_words = count_words(slide_dict.get("title", ""))
    bullets = slide_dict.get("bullet_points", [])
    bullet_words = sum(count_words(b) for b in bullets)
    
    if (title_words + bullet_words) > layout.capacity_words:
        return True
        
    # Check bullet count (typically max 5 bullets for single slide)
    if len(bullets) > 5:
        return True

    return False


def handle_overflow(slide_dict: dict, current_layout: LayoutDefinition, recent_layouts: List[str], allow_split: bool = True) -> List[dict]:
    """
    Handle overflow with 3-tier priority:
    1. Truncate: Trim body to zone budget, append "...see notes", move full text to speaker_notes.
    2. Split: If bullets > 5 and allow_split is True, split into slide N and slide N+1 (continued) with same layout template.
    3. Upgrade: Switch to a higher-capacity layout variant.
    """
    # If the slide has drawio_xml, bypass overflow/upgrade handling and force fit it to layout
    if "drawio_xml" in slide_dict and bool(slide_dict.get("drawio_xml")):
        return [fit_content_to_layout(slide_dict, current_layout)]

    bullets = slide_dict.get("bullet_points", [])
    
    # TIER 2: Automatic Slide Splitting (Triggered when > 5 bullets)
    if allow_split and len(bullets) > 5:
        # Split into two slides
        slide_n_bullets = bullets[:4]
        slide_n1_bullets = bullets[4:]
        
        slide_n = dict(slide_dict)
        slide_n["bullet_points"] = slide_n_bullets
        slide_n["layout_id"] = current_layout.id
        slide_n = fit_content_to_layout(slide_n, current_layout)
        
        slide_n1 = dict(slide_dict)
        slide_n1["title"] = f"{slide_dict.get('title', '')} (continued)"
        slide_n1["bullet_points"] = slide_n1_bullets
        slide_n1["layout_id"] = current_layout.id
        slide_n1["is_continuation"] = True
        slide_n1 = fit_content_to_layout(slide_n1, current_layout)
        
        # Recurse on slide_n1 in case it also overflows
        return [slide_n] + handle_overflow(slide_n1, current_layout, recent_layouts, allow_split=allow_split)

    # TIER 3: Upgrade to higher capacity layout if word count is too high for current layout
    title_words = count_words(slide_dict.get("title", ""))
    bullet_words = sum(count_words(b) for b in bullets)
    total_words = title_words + bullet_words
    
    if total_words > current_layout.capacity_words:
        # Try to find a layout with higher capacity
        better_layouts = [l for l in ALL_LAYOUTS if l.capacity_words > current_layout.capacity_words]
        if better_layouts:
            # Sort by highest capacity
            better_layouts.sort(key=lambda x: x.capacity_words, reverse=True)
            # Switch to the highest capacity layout
            upgraded_layout = better_layouts[0]
            upgraded_slide = dict(slide_dict)
            upgraded_slide["layout_id"] = upgraded_layout.id
            upgraded_slide = fit_content_to_layout(upgraded_slide, upgraded_layout)
            
            # If the upgraded layout still overflows, go to truncation tier
            if (title_words + bullet_words) > upgraded_layout.capacity_words:
                return [truncate_slide(upgraded_slide, upgraded_layout)]
            return [upgraded_slide]

    # TIER 1: Truncate to summary + "...see notes"
    if total_words > current_layout.capacity_words:
        return [truncate_slide(slide_dict, current_layout)]

    # Fits perfectly
    fitted = fit_content_to_layout(slide_dict, current_layout)
    return [fitted]


def truncate_slide(slide_dict: dict, layout: LayoutDefinition) -> dict:
    """Truncate body text/bullets to fit within layout capacity and append see notes."""
    truncated = dict(slide_dict)
    bullets = list(slide_dict.get("bullet_points", []))
    
    # Store full original text in speaker notes
    original_text = "\n".join(bullets)
    existing_notes = slide_dict.get("speaker_notes") or ""
    truncated["speaker_notes"] = f"{existing_notes}\n[Full Content]:\n{original_text}".strip()
    
    # Truncate bullets until they fit
    title_words = count_words(slide_dict.get("title", ""))
    current_words = title_words
    truncated_bullets = []
    
    for bullet in bullets:
        b_words = count_words(bullet)
        if current_words + b_words < layout.capacity_words - 5:
            truncated_bullets.append(bullet)
            current_words += b_words
        else:
            # Add final truncated bullet + "see notes"
            words = bullet.split()
            available = max(0, (layout.capacity_words - 5) - current_words)
            if available > 0:
                short_bullet = " ".join(words[:available]) + "... see notes"
            else:
                short_bullet = "... see notes"
            truncated_bullets.append(short_bullet)
            break
            
    if not truncated_bullets:
        truncated_bullets = ["Content truncated... see notes"]
        
    truncated["bullet_points"] = truncated_bullets
    return fit_content_to_layout(truncated, layout)


# ─── Orchestrator ─────────────────────────────────────────────────────

def assign_layouts(slides: List[dict], max_slides: int = None) -> List[dict]:
    """
    Iterate over generated slides, score and select the best layout,
    fit content, and handle any overflow/splitting.
    
    If max_slides is provided, splitting is disabled so that layout assignment
    does not alter the exact count or sequence generated by the planner.
    """
    processed_slides = []
    recent_layouts = []
    
    allow_split = (max_slides is None)

    for slide in slides:
        # If slide has drawio_xml, force architecture layout
        if "drawio_xml" in slide and bool(slide.get("drawio_xml")):
            best_layout_id = "architecture"
            scores = {layout.id: (1.0 if layout.id == "architecture" else 0.0) for layout in ALL_LAYOUTS}
        else:
            # Score all layouts
            scores = {layout.id: score_layout(slide, layout, recent_layouts) for layout in ALL_LAYOUTS}
            best_layout_id = max(scores, key=scores.get)
        best_layout = get_layout(best_layout_id)
        
        # Create a slide copy and set scoring metadata
        slide_copy = dict(slide)
        slide_copy["layout_id"] = best_layout_id
        slide_copy["layout_score"] = float(scores[best_layout_id])
        
        # Handle fitting and overflow
        resolved_slides = handle_overflow(slide_copy, best_layout, recent_layouts, allow_split=allow_split)
        
        for resolved in resolved_slides:
            processed_slides.append(resolved)
            recent_layouts.append(resolved["layout_id"])
            if len(recent_layouts) > 3:
                recent_layouts.pop(0)

    if max_slides and len(processed_slides) > max_slides:
        processed_slides = processed_slides[:max_slides]

    return processed_slides

