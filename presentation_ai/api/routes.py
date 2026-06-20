from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
from fastapi.responses import FileResponse
from typing import Optional, Union, Dict, Any
import os
import threading
import uuid

from services.pdf_extractor import extract_text
from services.slide_planner import generate_outline, generate_outline_from_template
from services.pptx_builder import build_pptx
from services.template_analyzer import analyze_template

# V2 template pipeline imports
from services.template_analyzer_v2 import analyze_template_v2
from services.slide_planner_v2 import generate_outline_from_template_v2
from models.layout_definitions import get_layout_summaries
import tempfile

# Cache for pre-built PPTX files
PPTX_CACHE = {}  # session_id → file_path

# Cache for custom templates
TEMPLATE_SCHEMA_CACHE = {}  # session_id -> template_schema dict
TEMPLATE_PATH_CACHE = {}    # session_id -> template_path str

# Cache for YouTube summaries
YOUTUBE_SUMMARY_CACHE = {}  # video_id -> summary str

# Cache for session topics to resolve dynamic download names
SESSION_TOPICS = {}  # session_id -> topic string

def resolve_visuals_for_deck(deck: dict) -> dict:
    if not deck or "slides" not in deck:
        return deck
    
    try:
        from services.visual_engine import get_hero_image
    except ImportError:
        print("[ROUTES] visual_engine not found, skipping keyword resolution")
        return deck
        
    for slide in deck["slides"]:
        layout_id = slide.get("layout_id")
        visual_type = slide.get("visual_type", "none").lower()
        image_keyword = slide.get("image_keyword") or slide.get("title") or ""
        
        is_image_slide = False
        if layout_id in ("Hero", "hero"):
            is_image_slide = True
        elif layout_id in ("OneColumn", "1-column"):
            is_image_slide = True
        elif layout_id in ("TwoColumn", "2-column"):
            if visual_type not in ("chart", "table", "architecture", "flowchart", "process", "timeline", "comparison"):
                is_image_slide = True
                
        if is_image_slide:
            search_keyword = image_keyword or slide.get("title") or deck.get("deck_title") or "presentation"
            img_path = get_hero_image(search_keyword)
            if img_path and os.path.exists(img_path):
                filename = os.path.basename(img_path)
                public_url = f"http://127.0.0.1:8000/static/{filename}"
                slide["visual_items"] = [public_url]
                slide["visual_type"] = "image"
                
                if "zone_content" not in slide:
                    slide["zone_content"] = {}
                
                if layout_id in ("OneColumn", "1-column"):
                    slide["zone_content"]["image"] = public_url
                elif layout_id in ("TwoColumn", "2-column"):
                    slide["zone_content"]["right_content"] = {
                        "kind": "image",
                        "items": [public_url],
                        "text": public_url
                    }
                elif layout_id in ("Hero", "hero"):
                    slide["zone_content"]["background_image"] = public_url
                    
    return deck


def resolve_agent_edit_changes(changes: dict, slide_summary: dict = None) -> dict:
    if not changes:
        return changes
    
    try:
        from services.visual_engine import get_hero_image
    except ImportError:
        return changes

    def _resolve_kw(kw):
        if kw and not kw.startswith("http://") and not kw.startswith("https://") and not kw.startswith("data:"):
            img_path = get_hero_image(kw)
            if img_path and os.path.exists(img_path):
                filename = os.path.basename(img_path)
                return f"http://127.0.0.1:8000/static/{filename}"
        return kw

    zone_content = changes.get("zone_content")
    if zone_content is None and slide_summary:
        if changes.get("layout_id"):
            changes["zone_content"] = {}
            zone_content = changes["zone_content"]

    layout_id = changes.get("layout_id") or (slide_summary.get("layout_id") if slide_summary else None)

    if isinstance(zone_content, dict):
        if layout_id in ("OneColumn", "1-column"):
            current_img = zone_content.get("image") or (slide_summary.get("zone_content", {}).get("image") if slide_summary else None)
            if not current_img or not (str(current_img).startswith("http://") or str(current_img).startswith("https://")):
                kw = current_img or (slide_summary.get("title") if slide_summary else "presentation")
                url = _resolve_kw(kw)
                if url:
                    zone_content["image"] = url
                    
        elif layout_id in ("Hero", "hero"):
            current_img = zone_content.get("background_image") or (slide_summary.get("zone_content", {}).get("background_image") if slide_summary else None)
            if not current_img or not (str(current_img).startswith("http://") or str(current_img).startswith("https://")):
                kw = current_img or (slide_summary.get("title") if slide_summary else "presentation")
                url = _resolve_kw(kw)
                if url:
                    zone_content["background_image"] = url
                    
        elif layout_id in ("TwoColumn", "2-column"):
            current_rc = zone_content.get("right_content") or (slide_summary.get("zone_content", {}).get("right_content") if slide_summary else None)
            if isinstance(current_rc, dict):
                if current_rc.get("kind") == "image":
                    val = current_rc.get("text")
                    if val and not (str(val).startswith("http://") or str(val).startswith("https://")):
                        url = _resolve_kw(val)
                        if url:
                            zone_content["right_content"] = {
                                "kind": "image",
                                "text": url,
                                "items": [url]
                            }
            else:
                vtype = slide_summary.get("visual_type", "none").lower() if slide_summary else "none"
                if vtype not in ("chart", "table", "architecture", "flowchart", "process", "timeline", "comparison"):
                    kw = slide_summary.get("title") if slide_summary else "presentation"
                    url = _resolve_kw(kw)
                    if url:
                        zone_content["right_content"] = {
                            "kind": "image",
                            "text": url,
                            "items": [url]
                        }

        # Resolve explicit changes if present
        if "image" in zone_content and isinstance(zone_content["image"], str):
            zone_content["image"] = _resolve_kw(zone_content["image"])
        if "background_image" in zone_content and isinstance(zone_content["background_image"], str):
            zone_content["background_image"] = _resolve_kw(zone_content["background_image"])
        if "right_content" in zone_content and isinstance(zone_content["right_content"], dict):
            rc = zone_content["right_content"]
            if rc.get("kind") == "image" and isinstance(rc.get("text"), str):
                url = _resolve_kw(rc["text"])
                if url:
                    rc["text"] = url
                    rc["items"] = [url]

    elements = changes.get("elements")
    if isinstance(elements, dict):
        for el_id, el_patch in elements.items():
            if isinstance(el_patch, dict) and el_patch.get("kind") == "image" and isinstance(el_patch.get("text"), str):
                el_patch["text"] = _resolve_kw(el_patch["text"])

    return changes


router = APIRouter()



@router.post("/generate")
async def generate_deck(
    topic: Optional[str] = Form(None),
    slide_count: int = Form(10),
    tone: str = Form("Professional"),
    sample_titles: Optional[str] = Form(None),
    pdf_file: Union[UploadFile, str, None] = File(None),
    document_file: Union[UploadFile, str, None] = File(None),
    doc_file: Union[UploadFile, str, None] = File(None),
    docs_file: Union[UploadFile, str, None] = File(None),
    template_file: Union[UploadFile, str, None] = File(None),
    youtube_url: Optional[str] = Form(None)
):
    # 1. Extract content from YouTube video if provided
    source_text = ""
    if youtube_url:
        try:
            from services.youtube_service import extract_video_id, validate_duration, get_video_duration
            from services.transcript_service import fetch_transcript
            from services.summarizer_service import generate_video_summary
            
            video_id = extract_video_id(youtube_url)
            if video_id in YOUTUBE_SUMMARY_CACHE:
                summary = YOUTUBE_SUMMARY_CACHE[video_id]
            else:
                duration = get_video_duration(video_id)
                is_valid, msg = validate_duration(duration)
                if not is_valid:
                    raise HTTPException(status_code=400, detail=msg)
                    
                transcript = fetch_transcript(video_id)
                summary = generate_video_summary(transcript)
                YOUTUBE_SUMMARY_CACHE[video_id] = summary
                
            source_text = summary
            if not topic or not topic.strip():
                topic = "YouTube Video Summary"
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"YouTube processing failed: {str(e)}")

    # 1.5. Extract content from uploaded document (PDF, DOCX, TXT) — optional (falls back to youtube if not provided)
    upload = None
    if not source_text:
        upload = _first_upload(pdf_file, document_file, doc_file, docs_file)
    if upload:
        try:
            content = await upload.read()
            if content:
                source_text = extract_text(content, upload.filename)
                if not source_text.strip():
                    raise ValueError(
                        "No readable text was found in the uploaded document. "
                        "Please upload a text-based PDF, DOCX, or TXT file."
                    )
                print(f"[EXTRACT] Extracted {len(source_text)} chars from '{upload.filename}'")
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process uploaded file: {str(e)}")

    # 2. Read custom template PPTX if uploaded — optional
    template_bytes = None
    template_blueprint = None
    if _is_upload(template_file):
        if not template_file.filename.lower().endswith(".pptx"):
            raise HTTPException(status_code=400, detail="Template must be a .pptx file.")
        try:
            template_bytes = await template_file.read()
            if not template_bytes:
                template_bytes = None
            else:
                template_blueprint = analyze_template(template_bytes)
                print(f"[TEMPLATE] Using custom template: '{template_file.filename}'")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read template file: {str(e)}")

    # 3. Generate slide outline via LLM
    try:
        deck = generate_outline(topic, slide_count, tone,
                                sample_titles, source_text, template_blueprint)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM outline generation failed: {str(e)}")

    # 4. Build PPTX (use topic as filename, pass template if provided)
    try:
        output_path = build_pptx(deck, topic=topic, template_bytes=template_bytes, tone=tone)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assemble PPTX: {str(e)}")

    # 5. Return as downloadable file
    if not os.path.exists(output_path):
        raise HTTPException(status_code=500, detail="Generated PPTX file not found.")

    # Use the topic as download filename
    safe_name = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).strip()
    download_name = f"{safe_name[:50]}.pptx" if safe_name else "presentation.pptx"

    return FileResponse(output_path,
                        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        filename=download_name)


@router.post("/generate-json")
async def generate_deck_json(
    topic: Optional[str] = Form(None),
    slide_count: int = Form(10),
    tone: str = Form("Professional"),
    sample_titles: Optional[str] = Form(None),
    pdf_file: Union[UploadFile, str, None] = File(None),
    document_file: Union[UploadFile, str, None] = File(None),
    doc_file: Union[UploadFile, str, None] = File(None),
    docs_file: Union[UploadFile, str, None] = File(None),
    template_file: Union[UploadFile, str, None] = File(None),
    youtube_url: Optional[str] = Form(None),
    architecture_type: str = Form("none"),
    architecture_style: str = Form("classic")
):
    # Generate session ID early so we can associate all cached items with it
    session_id = uuid.uuid4().hex[:12]
    SESSION_TOPICS[session_id] = topic

    # 1. Extract content from YouTube video if provided
    source_text = ""
    if youtube_url:
        try:
            from services.youtube_service import extract_video_id, validate_duration, get_video_duration
            from services.transcript_service import fetch_transcript
            from services.summarizer_service import generate_video_summary
            
            video_id = extract_video_id(youtube_url)
            if video_id in YOUTUBE_SUMMARY_CACHE:
                summary = YOUTUBE_SUMMARY_CACHE[video_id]
            else:
                duration = get_video_duration(video_id)
                is_valid, msg = validate_duration(duration)
                if not is_valid:
                    raise HTTPException(status_code=400, detail=msg)
                    
                transcript = fetch_transcript(video_id)
                summary = generate_video_summary(transcript)
                YOUTUBE_SUMMARY_CACHE[video_id] = summary
                
            source_text = summary
            if not topic or not topic.strip():
                topic = "YouTube Video Summary"
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"YouTube processing failed: {str(e)}")

    # 1.5. Extract content from uploaded document (PDF, DOCX, TXT) — optional
    upload = None
    if not source_text:
        upload = _first_upload(pdf_file, document_file, doc_file, docs_file)
    if upload:
        try:
            content = await upload.read()
            if content:
                source_text = extract_text(content, upload.filename)
                if not source_text.strip():
                    raise ValueError(
                        "No readable text was found in the uploaded document. "
                        "Please upload a text-based PDF, DOCX, or TXT file."
                    )
                print(f"[EXTRACT] Extracted {len(source_text)} chars from '{upload.filename}'")
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process uploaded file: {str(e)}")

    # 2. Read custom template PPTX if uploaded — optional
    template_schema = None
    template_bytes = None
    template_temp_path = None
    if _is_upload(template_file):
        if not template_file.filename.lower().endswith(".pptx"):
            raise HTTPException(status_code=400, detail="Template must be a .pptx file.")
        try:
            template_bytes = await template_file.read()
            if not template_bytes:
                template_bytes = None
            else:
                template_schema = analyze_template_v2(template_bytes)
                print(f"[TEMPLATE] Analyzed custom template: '{template_file.filename}' — {template_schema.get('slide_count', '?')} slides")
                # Save template to disk under the session ID
                template_temp_path = os.path.join(tempfile.gettempdir(), f"template_{session_id}.pptx")
                with open(template_temp_path, "wb") as tf_out:
                    tf_out.write(template_bytes)
                
                # Save template schema to disk as JSON under the session ID
                import json
                schema_temp_path = os.path.join(tempfile.gettempdir(), f"schema_{session_id}.json")
                with open(schema_temp_path, "w", encoding="utf-8") as schema_out:
                    json.dump(template_schema, schema_out, ensure_ascii=False, indent=2)
                
                # Cache globally for later download exports (backup)
                TEMPLATE_SCHEMA_CACHE[session_id] = template_schema
                TEMPLATE_PATH_CACHE[session_id] = template_temp_path
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read template file: {str(e)}")

    # 3. Generate slide outline via LLM
    try:
        if template_schema:
            # Template mode: override slide count and use template-aware generation
            slide_count = template_schema["slide_count"]
            deck = generate_outline_from_template_v2(
                topic=topic,
                template_schema=template_schema,
                tone=tone,
                source_text=source_text,
            )
            print(f"[TEMPLATE] Generated template-aware outline: {len(deck.get('slides', []))} slides")
            
            # Save raw generated slides to disk under the session ID
            slides_temp_path = os.path.join(tempfile.gettempdir(), f"slides_{session_id}.json")
            with open(slides_temp_path, "w", encoding="utf-8") as slides_out:
                import json
                json.dump(deck.get("slides", []), slides_out, ensure_ascii=False, indent=2)

            # Map to lightweight slide objects for frontend compat (preserving raw keys in zone_content)
            try:
                from services.visual_engine import get_hero_image
            except ImportError:
                get_hero_image = None

            frontend_slides = []
            for i, slide in enumerate(deck.get("slides", [])):
                layout = slide.get("layout", "content")
                layout_id = "Hero" if (i == 0 and layout == "hero") else "OneColumn"
                
                # Combine bodies
                body_parts = []
                # Sort slide keys to maintain body1, body2, ... bodyN order
                for k in sorted(slide.keys()):
                    if k.startswith("body") and slide[k]:
                        body_parts.append(slide[k])
                slide["body"] = "\n".join(body_parts)
                slide["headline"] = slide.get("subtitle", "")
                
                # Resolve image/icon keywords to URLs for frontend preview
                if get_hero_image:
                    for k in list(slide.keys()):
                        if k.endswith("_keyword") and slide[k]:
                            role = k[:-8]  # strip '_keyword'
                            img_path = get_hero_image(slide[k])
                            if img_path and os.path.exists(img_path):
                                filename = os.path.basename(img_path)
                                public_url = f"http://127.0.0.1:8000/static/{filename}"
                                slide[role] = public_url
                                if role == "image1":
                                    slide["image"] = public_url
                                elif role == "icon1":
                                    slide["icon"] = public_url

                frontend_slides.append({
                    **slide,
                    "slide_index": i,
                    "title": slide.get("title", ""),
                    "layout_id": layout_id,
                    "zone_content": slide
                })
            deck["slides"] = frontend_slides
        else:
            deck = generate_outline(
                topic,
                slide_count,
                tone,
                sample_titles,
                source_text,
                architecture_type=architecture_type if architecture_type != "none" else None
            )
            deck = resolve_visuals_for_deck(deck)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM outline generation failed: {str(e)}")

    # 3.2. Override architecture diagrams if architecture_type is specified
    if architecture_type != "none":
        try:
            from config import ARCH_ENGINE_VERSION
            from services.visual_engine import generate_drawio_diagram
            from services.architecture_v3.style_engine import set_current_style
            resolved_style = architecture_style
            if resolved_style in ("classic", "auto"):
                topic_lower = (topic or "").lower()
                if any(x in topic_lower for x in ("aws", "amazon", "lambda", "s3", "rds", "ec2", "cloudfront", "route53", "cognito", "serverless")):
                    resolved_style = "aws_icons"
                elif any(x in topic_lower for x in ("kubernetes", "k8s", "cluster", "pod", "docker", "container")):
                    resolved_style = "k8s_icons"
                elif any(x in topic_lower for x in ("ai", "llm", "rag", "openai", "gpt", "gemini", "claude", "agent", "embedding", "vector")):
                    resolved_style = "aiicons"
                else:
                    resolved_style = "drawio_skill"
            print(f"[ROUTES] Setting visual style to '{resolved_style}' (requested '{architecture_style}') for topic '{topic}'")
            set_current_style(resolved_style)
            
            for slide in deck.get("slides", []):
                slide_type = slide.get("slide_type", "").lower()
                if slide_type in ("architecture", "tech_stack"):
                    bullets = slide.get("bullet_points", [])
                    slide_content = "\n".join(bullets) if isinstance(bullets, list) else str(bullets)
                    
                    drawio_xml = None
                    diagram_png = None
                    
                    # 1. Try Version 4 first if configured
                    if ARCH_ENGINE_VERSION == "v4":
                        try:
                            from services.architecture_v4.renderer import generate_architecture_v4
                            
                            resolved_style_v4 = architecture_style
                            if resolved_style_v4 in ("classic", "auto"):
                                topic_lower = (topic or "").lower()
                                if any(x in topic_lower for x in ("aws", "amazon", "lambda", "s3", "rds", "ec2", "cloudfront", "route53", "cognito", "serverless")):
                                    resolved_style_v4 = "aws"
                                elif any(x in topic_lower for x in ("kubernetes", "k8s", "cluster", "pod", "docker", "container")):
                                    resolved_style_v4 = "kubernetes"
                                elif any(x in topic_lower for x in ("ai", "llm", "rag", "openai", "gpt", "gemini", "claude", "agent", "embedding", "vector")):
                                    resolved_style_v4 = "ai_dark_neon"
                                else:
                                    resolved_style_v4 = "drawio_vivid"
                            
                            print(f"[ROUTES] [V4] Using visual style '{resolved_style_v4}' for topic '{topic}'")
                            print(f"[ROUTES] [V4] Generating diagram (type={architecture_type}) for slide '{slide.get('title')}'")
                            v4_xml = generate_architecture_v4(
                                architecture_type=architecture_type,
                                visual_style=resolved_style_v4,
                                topic=topic or "Architecture",
                                slide_title=slide.get("title", ""),
                                slide_content=slide_content
                            )
                            if v4_xml:
                                print(f"[ROUTES] [V4] Testing diagram rendering (disable_fallback=True)...")
                                svg_p, png_p = generate_drawio_diagram(v4_xml, topic=slide.get("title", ""), disable_fallback=True)
                                if png_p and os.path.exists(png_p):
                                    drawio_xml = v4_xml
                                    filename = os.path.basename(png_p)
                                    diagram_png = f"http://127.0.0.1:8000/static/{filename}"
                                    print(f"[ROUTES] [V4] Success! Diagram rendered to PNG.")
                        except Exception as e_v4:
                            print(f"[ROUTES] [V4] Failed: {e_v4}. Falling back to V3...")
                            
                    # 2. Try Version 3 if V4 failed or is not configured
                    if not drawio_xml and ARCH_ENGINE_VERSION in ("v3", "v4"):
                        try:
                            from services.architecture_v3.renderer import generate_architecture_v3
                            print(f"[ROUTES] [V3] Generating diagram (type={architecture_type}) for slide '{slide.get('title')}'")
                            v3_xml = generate_architecture_v3(
                                architecture_type=architecture_type,
                                topic=topic or "Architecture",
                                slide_title=slide.get("title", ""),
                                slide_content=slide_content
                            )
                            if v3_xml:
                                print(f"[ROUTES] [V3] Testing diagram rendering (disable_fallback=True)...")
                                svg_p, png_p = generate_drawio_diagram(v3_xml, topic=slide.get("title", ""), disable_fallback=True)
                                if png_p and os.path.exists(png_p):
                                    drawio_xml = v3_xml
                                    filename = os.path.basename(png_p)
                                    diagram_png = f"http://127.0.0.1:8000/static/{filename}"
                                    print(f"[ROUTES] [V3] Success! Diagram rendered to PNG.")
                        except Exception as e_v3:
                            print(f"[ROUTES] [V3] Failed: {e_v3}. Falling back to V2...")
                            
                    # 2. Try Version 2 if V3 failed or is not configured
                    if not drawio_xml:
                        try:
                            from services.architecture_v2.renderer import generate_architecture_v2
                            print(f"[ROUTES] [V2] Generating diagram (type={architecture_type}) for slide '{slide.get('title')}'")
                            v2_xml = generate_architecture_v2(
                                architecture_type=architecture_type,
                                topic=topic or "Architecture",
                                slide_title=slide.get("title", ""),
                                slide_content=slide_content
                            )
                            if v2_xml:
                                print(f"[ROUTES] [V2] Testing diagram rendering (disable_fallback=False)...")
                                svg_p, png_p = generate_drawio_diagram(v2_xml, topic=slide.get("title", ""), disable_fallback=False)
                                if png_p and os.path.exists(png_p):
                                    drawio_xml = v2_xml
                                    filename = os.path.basename(png_p)
                                    diagram_png = f"http://127.0.0.1:8000/static/{filename}"
                                    print(f"[ROUTES] [V2] Success! Diagram resolved.")
                        except Exception as e_v2:
                            print(f"[ROUTES] [V2] Failed: {e_v2}. Falling back to old architecture engine...")
                            
                    # 3. Apply resolved outputs to slide
                    if drawio_xml:
                        slide["drawio_xml"] = drawio_xml
                    if diagram_png:
                        slide["diagram_png"] = diagram_png
        except Exception as e:
            print(f"[ROUTES] Failed to execute architecture override flow: {e}")


    # 4. Start building PPTX in background
    
    # Capture template variables for background thread closure
    is_template_mode = bool(template_schema)
    _bg_template_temp_path = template_temp_path
    _bg_template_schema = template_schema
    _bg_deck = deck
    
    def build_background():
        try:
            import time
            start_time = time.time()
            
            if is_template_mode:
                if not _bg_template_temp_path or not _bg_template_schema:
                    raise ValueError("Template mode active but template files or schema is missing.")
                # Template mode: use template_filler to preserve design
                from services.template_filler_v2 import fill_template_v2
                output_path = fill_template_v2(
                    template_path=_bg_template_temp_path,
                    template_schema=_bg_template_schema,
                    slide_contents=_bg_deck.get("slides", []),
                    output_dir="outputs",
                )
                elapsed = time.time() - start_time
                print(f"[CACHE] ✅ Template PPTX filled in {elapsed:.2f}s: {output_path}")
            else:
                # Standard mode: build from scratch
                deck_outline = {
                    "deck_title": _bg_deck.get("title", "Presentation"),
                    "slides": []
                }
                
                for slide in _bg_deck.get("slides", []):
                    deck_outline["slides"].append({
                        "slide_type": slide.get("slide_type", "content"),
                        "title": slide.get("title", ""),
                        "headline": slide.get("headline", ""),
                        "bullet_points": slide.get("bullet_points", []),
                        "layout_id": slide.get("layout_id", ""),
                        "visual_type": slide.get("visual_type", ""),
                        "visual_items": slide.get("visual_items", []),
                        "image_keyword": slide.get("image_keyword", ""),
                        "icon_emoji": slide.get("icon_emoji", ""),
                        "drawio_xml": slide.get("drawio_xml", ""),
                        "diagram_png": slide.get("diagram_png", ""),
                        "process_steps": slide.get("process_steps"),
                        "timeline_steps": slide.get("timeline_steps"),
                        "comparison_items": slide.get("comparison_items"),
                        "architecture_nodes": slide.get("architecture_nodes"),
                        "grid_items": slide.get("grid_items"),
                        "chart_data": slide.get("chart_data"),
                    })
                
                output_path = build_pptx(deck_outline, topic=topic, tone=tone)
                elapsed = time.time() - start_time
                print(f"[CACHE] ✅ PPTX pre-built in {elapsed:.2f}s: {output_path}")
            
            PPTX_CACHE[session_id] = output_path
        except Exception as e:
            print(f"[CACHE] ❌ Pre-build failed: {e}")
            import traceback
            traceback.print_exc()
            PPTX_CACHE[session_id] = "failed"
    
    threading.Thread(target=build_background, daemon=True).start()
    
    # Return JSON immediately with session_id — don't wait for PPTX
    return {
        **deck,
        "session_id": session_id,
        "template_mode": bool(template_schema),
        "template_slide_count": template_schema["slide_count"] if template_schema else None,
    }


@router.get("/pptx-status/{session_id}")
async def check_pptx_status(session_id: str):
    """Check if PPTX is ready for download"""
    status = PPTX_CACHE.get(session_id)
    if not status:
        return {"ready": False, "status": "building"}
    if status == "failed":
        return {"ready": False, "status": "failed"}
    return {"ready": True, "status": "ready"}


@router.get("/download-pptx/{session_id}")
async def download_cached_pptx(session_id: str):
    """Download pre-built PPTX by session ID"""
    path = PPTX_CACHE.get(session_id)
    if not path or path == "failed":
        raise HTTPException(status_code=404, detail="PPTX not ready yet")
    
    import os
    # Try to retrieve the user-entered topic to rename the download file
    topic = SESSION_TOPICS.get(session_id)
    if topic:
        safe_name = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).strip()
        download_name = f"{safe_name[:50]}.pptx" if safe_name else "presentation.pptx"
    else:
        download_name = os.path.basename(path)
        
    return FileResponse(
        path,
        filename=download_name,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )


def map_react_deck_to_template_contents(deck_obj: dict) -> list:
    """Map frontend React deck representation to standard template filler inputs.
    
    Preserves all original zone roles and custom flat keys.
    """
    template_contents = []
    if not isinstance(deck_obj, dict) or "slides" not in deck_obj:
        return template_contents

    for slide in deck_obj["slides"]:
        layout_id = slide.get("layout_id")
        layout = "content"
        if layout_id == "Hero":
            layout = "hero"
        elif layout_id == "TwoColumn":
            layout = "two_column"
        elif layout_id == "ThreeColumn":
            layout = "three_column"
        elif layout_id == "Process":
            layout = "process"
            
        zone_content = slide.get("zone_content") or {}
        title = zone_content.get("title") or slide.get("title", "")
        subtitle = zone_content.get("subtitle", "")
        
        # Bullets
        bullets = []
        body_text = zone_content.get("body", "")
        if body_text:
            bullets = [b.strip() for b in body_text.split("\n") if b.strip()]
        else:
            bullets = slide.get("bullet_points", [])
            
        # Left and Right Column content
        left_content = {}
        right_content = {}
        if layout == "two_column":
            left_text = zone_content.get("left_text") or ""
            left_bullets = [b.strip() for b in left_text.split("\n") if b.strip()] if isinstance(left_text, str) else []
            left_content = {
                "heading": zone_content.get("left_headline", "Key Points"),
                "bullets": left_bullets
            }
            rc = zone_content.get("right_content") or {}
            if isinstance(rc, dict):
                r_text = rc.get("text") or ""
                right_bullets = [b.strip() for b in r_text.split("\n") if b.strip()] if isinstance(r_text, str) else []
                right_content = {
                    "heading": rc.get("heading", ""),
                    "bullets": right_bullets
                }
            else:
                right_content = {
                    "heading": "",
                    "bullets": [str(rc)]
                }
                
        # Three Columns content
        columns = []
        if layout == "three_column":
            cols_data = zone_content.get("columns", [])
            if cols_data:
                for col in cols_data:
                    columns.append({
                        "heading": col.get("heading", ""),
                        "description": col.get("description", "")
                    })
            else:
                for col_key in ["col_1", "col_2", "col_3"]:
                    col_val = zone_content.get(col_key, "")
                    if col_val:
                        columns.append({
                            "heading": "",
                            "description": col_val
                        })
                        
        # Steps
        steps = []
        if layout == "process":
            steps_data = zone_content.get("steps", [])
            for step in steps_data:
                steps.append({
                    "step_title": step.get("title", ""),
                    "step_description": step.get("body", "")
                })
                
        slide_dict = {
            "layout": layout,
            "title": title,
            "subtitle": subtitle,
            "bullets": bullets,
            "left_content": left_content,
            "right_content": right_content,
            "columns": columns,
            "steps": steps,
            "image_keyword": slide.get("image_keyword", "")
        }
        
        # Preserve all other original keys (e.g. body1, body2, image1_keyword)
        for k, v in slide.items():
            if k not in slide_dict:
                slide_dict[k] = v
                
        template_contents.append(slide_dict)
        
    return template_contents


@router.post("/export-pptx")
async def export_pptx_deck(
    request_data: Dict[str, Any] = Body(...)
):
    import time
    start_time = time.time()
    try:
        # Extract the actual deck data and tone from the nested structure if sent inside a wrapper
        deck_obj = request_data.get("deck") if "deck" in request_data else request_data
        actual_tone = request_data.get("tone") or deck_obj.get("tone") or "Professional"

        print(f"[EXPORT] Received deck keys: {list(deck_obj.keys()) if isinstance(deck_obj, dict) else type(deck_obj)}")
        print(f"[EXPORT] Slides count in input: {len(deck_obj.get('slides', [])) if isinstance(deck_obj, dict) else 0}")
        print(f"[EXPORT] Starting PPTX generation...")
        # Convert React Deck layout back to outline format compatible with pptx_builder
        pptx_slides = []
        for slide in deck_obj.get("slides", []):
            layout_id = slide.get("layout_id")
            mapped_layout_id = None
            if layout_id:
                mapping = {
                    "OneColumn": "1-column",
                    "TwoColumn": "2-column",
                    "ThreeColumn": "3-column",
                    "FourGrid": "4-grid",
                    "Hero": "hero",
                    "Dashboard": "dashboard",
                    "Architecture": "architecture",
                    "Timeline": "timeline",
                    "Comparison": "comparison",
                    "Process": "process",
                }
                mapped_layout_id = mapping.get(layout_id)

            title = slide.get("title", "")
            zone_content = slide.get("zone_content") or {}
            bullets = []
            visual_type = "none"
            visual_items = []
            
            # Additional layout metadata
            left_text = ""
            left_headline = "Key Points"
            headline = ""
            left_points = []
            right_points = []

            if mapped_layout_id == "1-column":
                body = zone_content.get("body", "")
                bullets = [b.strip() for b in body.split("\n") if b.strip()] if body else []
                if zone_content.get("image"):
                    visual_type = "image"
                    visual_items = [zone_content.get("image")]
                headline = zone_content.get("headline", "")
                if headline == title:
                    headline = ""
            elif mapped_layout_id == "2-column":
                left_text = zone_content.get("left_text") or zone_content.get("body") or ""
                left_bullets = [b.strip() for b in left_text.split("\n") if b.strip()] if isinstance(left_text, str) else []
                bullets = zone_content.get("bullets") or left_bullets
                left_headline = zone_content.get("left_headline", "Key Points")
                right_content = zone_content.get("right_content") or {}
                if isinstance(right_content, dict):
                    visual_type = right_content.get("kind", "none")
                    visual_items = right_content.get("items", [])
                    if not visual_items and right_content.get("text"):
                        visual_items = [right_content.get("text")]
            elif mapped_layout_id == "3-column":
                bullets = [
                    zone_content.get("col_1", ""),
                    zone_content.get("col_2", ""),
                    zone_content.get("col_3", ""),
                ]
                bullets = [b for b in bullets if b]
            elif mapped_layout_id == "4-grid":
                bullets = [
                    zone_content.get("cell_tl", ""),
                    zone_content.get("cell_tr", ""),
                    zone_content.get("cell_bl", ""),
                    zone_content.get("cell_br", ""),
                ]
                bullets = [b for b in bullets if b]
            elif mapped_layout_id == "hero":
                subtitle = zone_content.get("subtitle", "")
                bullets = [subtitle] if subtitle else []
                bg_img = zone_content.get("background_image")
                if bg_img:
                    visual_type = "image"
                    visual_items = [bg_img]
            elif mapped_layout_id == "dashboard":
                stat_row = zone_content.get("stat_row", "")
                insight_area = zone_content.get("insight_area", "")
                insight_bullets = [b.strip() for b in insight_area.split("\n") if b.strip()] if insight_area else []
                bullets = [stat_row] if stat_row else []
                bullets.extend(insight_bullets)
            elif mapped_layout_id == "architecture":
                labels = zone_content.get("labels", "")
                bullets = [b.strip() for b in labels.split("\n") if b.strip()] if labels else []
            elif mapped_layout_id == "timeline":
                events = zone_content.get("events", "")
                bullets = [b.strip() for b in events.split("\n") if b.strip()] if events else []
            elif mapped_layout_id == "comparison":
                left_points = zone_content.get("left_points", [])
                right_points = zone_content.get("right_points", [])
                bullets = left_points + right_points
                visual_type = "comparison"
                visual_items = [zone_content.get("left_title", ""), zone_content.get("right_title", "")]
            elif mapped_layout_id == "process":
                bullets = zone_content.get("steps", [])
                visual_type = "process"
                visual_items = bullets
            else:
                elements = slide.get("elements", [])
                bullets = [el.get("text", "") for el in elements if el.get("kind") == "text" and el.get("id") != "title-1"]
                bullets = [b for b in bullets if b]

            speaker_notes = slide.get("speaker_notes") or ""

            pptx_slides.append({
                "title": title,
                "bullet_points": bullets,
                "visual_type": visual_type,
                "visual_items": visual_items,
                "speaker_notes": speaker_notes,
                "layout_id": mapped_layout_id,
                "slide_type": slide.get("content_type", "content"),
                "left_text": left_text,
                "left_headline": left_headline,
                "headline": headline,
                "left_points": left_points,
                "right_points": right_points,
                "zone_content": zone_content,
                "icon_emoji": slide.get("icon_emoji", ""),
                "icon_keyword": slide.get("icon_keyword", ""),
                # Draw.io XML for architecture diagrams
                "drawio_xml": slide.get("drawio_xml", ""),
                # Pre-generated PNG path for architecture diagrams (from /generate-json)
                "diagram_png": slide.get("diagram_png", ""),
                # Structured layout fields (AI-generated)
                "process_steps": slide.get("process_steps"),
                "timeline_steps": slide.get("timeline_steps"),
                "comparison_items": slide.get("comparison_items"),
                "comparison_left_title": slide.get("comparison_left_title"),
                "comparison_right_title": slide.get("comparison_right_title"),
                "dashboard_metrics": slide.get("dashboard_metrics"),
                "dashboard_insight": slide.get("dashboard_insight"),
                "architecture_nodes": slide.get("architecture_nodes"),
                "grid_items": slide.get("grid_items"),
                "chart_data": slide.get("chart_data"),
            })

        deck_outline = {
            "deck_title": deck_obj.get("title", "Presentation"),
            "slides": pptx_slides
        }

        actual_topic = request_data.get("topic") or deck_obj.get("title") or "presentation"
        session_id = request_data.get("session_id")
        template_mode = request_data.get("template_mode", False)

        # Check if template files exist on disk to survive server restarts/reloads
        disk_template_path = os.path.join(tempfile.gettempdir(), f"template_{session_id}.pptx") if session_id else None
        disk_schema_path = os.path.join(tempfile.gettempdir(), f"schema_{session_id}.json") if session_id else None
        
        has_disk_template = disk_template_path and disk_schema_path and os.path.exists(disk_template_path) and os.path.exists(disk_schema_path)

        if template_mode:
            if not session_id:
                raise HTTPException(status_code=400, detail="Template mode requires a valid session_id.")
                
            if not has_disk_template and session_id not in TEMPLATE_PATH_CACHE:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Template files for session {session_id} could not be found. Please upload the template again."
                )
                
            from services.template_filler_v2 import fill_template_v2
            
            if has_disk_template:
                template_path = disk_template_path
                import json
                with open(disk_schema_path, "r", encoding="utf-8") as schema_f:
                    template_schema = json.load(schema_f)
            else:
                template_path = TEMPLATE_PATH_CACHE[session_id]
                template_schema = TEMPLATE_SCHEMA_CACHE[session_id]
            
            # Load cached slides (original LLM generated slides with raw flat zone keys)
            disk_slides_path = os.path.join(tempfile.gettempdir(), f"slides_{session_id}.json")
            if os.path.exists(disk_slides_path):
                import json
                try:
                    with open(disk_slides_path, "r", encoding="utf-8") as sf:
                        cached_slides = json.load(sf)
                except Exception as e:
                    print(f"[EXPORT] Warning: Failed to load cached slides: {e}")
                    cached_slides = []
            else:
                cached_slides = []
            
            # Merge edits from the frontend slide_obj
            import copy
            slide_contents = []
            for idx, cached_slide in enumerate(cached_slides):
                if idx < len(deck_obj.get("slides", [])):
                    frontend_slide = deck_obj["slides"][idx]
                    merged_slide = copy.deepcopy(cached_slide)
                    
                    # Overlay slide title
                    f_title = frontend_slide.get("title")
                    if f_title:
                        merged_slide["title"] = f_title
                        
                    # Overlay zone_content keys (which contains the edited raw keys)
                    f_zone = frontend_slide.get("zone_content")
                    if isinstance(f_zone, dict):
                        for k, v in f_zone.items():
                            if not k.startswith("__") and v is not None:
                                merged_slide[k] = v
                                
                    slide_contents.append(merged_slide)
                else:
                    slide_contents.append(cached_slide)
            
            print(f"[EXPORT] Filling custom template for session {session_id}...")
            build_start = time.time()
            output_path = fill_template_v2(
                template_path=template_path,
                template_schema=template_schema,
                slide_contents=slide_contents,
                output_dir="outputs"
            )
            build_time = time.time() - build_start
            print(f"[EXPORT] fill_template completed in {build_time:.2f}s")
        else:
            print(f"[EXPORT] Calling build_pptx with {len(pptx_slides)} slides...")
            build_start = time.time()
            output_path = build_pptx(deck_outline, topic=actual_topic, tone=actual_tone)
            build_time = time.time() - build_start
            print(f"[EXPORT] build_pptx completed in {build_time:.2f}s")
        
        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="Failed to generate PPTX file.")

        safe_name = "".join(c for c in actual_topic if c.isalnum() or c in (' ', '-', '_')).strip()
        download_name = f"{safe_name[:50]}.pptx" if safe_name else "presentation.pptx"

        total_time = time.time() - start_time
        print(f"[EXPORT] Total export time: {total_time:.2f}s")

        return FileResponse(output_path,
                            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            filename=download_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export presentation: {str(e)}")


def _first_upload(*files: Union[UploadFile, str, None]) -> Optional[UploadFile]:
    for file in files:
        if _is_upload(file):
            return file
    return None


def _is_upload(file: Union[UploadFile, str, None]) -> bool:
    return bool(
        file
        and getattr(file, "filename", None)
        and callable(getattr(file, "read", None))
    )


def _build_local_agent_edit(slide: Dict[str, Any], instruction: str, selected_element_id=None, selected_zone_key=None):
    text = instruction.lower().strip()
    changes: Dict[str, Any] = {}
    messages = []

    color_names = {
        "red": "#ef4444",
        "blue": "#2563eb",
        "cyan": "#22d3ee",
        "green": "#22c55e",
        "yellow": "#facc15",
        "orange": "#f97316",
        "purple": "#8b5cf6",
        "pink": "#ec4899",
        "black": "#020617",
        "white": "#ffffff",
        "gray": "#64748b",
        "grey": "#64748b",
    }

    def target_element():
        if selected_element_id:
            return next((el for el in slide.get("elements", []) if el.get("id") == selected_element_id), None)
        for el in slide.get("elements", []):
            if el.get("kind") == "text":
                return el
        return None

    def target_zone():
        return selected_zone_key or ("title" if "title" in text else "left_text")

    def apply_text_style(patch):
        el = target_element()
        if selected_element_id and el:
            changes.setdefault("elements", {})[selected_element_id] = patch
        else:
            changes.setdefault("zone_styles", {})[target_zone()] = patch

    # Find any color name or hex code in the instruction
    chosen_color = None
    for name, hex_value in color_names.items():
        import re
        if re.search(r'\b' + re.escape(name) + r'\b', text):
            chosen_color = hex_value
            break

    if not chosen_color:
        import re
        match = re.search(r"#[0-9a-fA-F]{6}", instruction)
        if match:
            chosen_color = match.group(0)

    # 1. Layout logic
    layout_map = {
        "hero": "Hero",
        "one column": "OneColumn",
        "onecolumn": "OneColumn",
        "two column": "TwoColumn",
        "twocolumn": "TwoColumn",
        "three column": "ThreeColumn",
        "threecolumn": "ThreeColumn",
        "four grid": "FourGrid",
        "fourgrid": "FourGrid",
        "dashboard": "Dashboard",
        "architecture": "Architecture",
        "timeline": "Timeline",
        "comparison": "Comparison",
        "process": "Process",
    }

    matched_layout = None
    for key, layout in layout_map.items():
        import re
        if re.search(r'\b' + re.escape(key) + r'\b', text) or text == key:
            matched_layout = layout
            break

    if matched_layout:
        changes["layout_id"] = matched_layout
        messages.append(f"Changed layout to {matched_layout}.")

    # 2. Background color logic
    if any(k in text for k in ("background", "bg", "color", "colour")) or text in color_names or any(text == f"make it {c}" for c in color_names) or any(text == f"change to {c}" for c in color_names):
        if chosen_color:
            changes["background"] = chosen_color
            messages.append("Updated the background color.")

    # 3. Title / text update logic
    if ("title text" in text or "title to" in text or text.startswith("rename") or "change title" in text) and not any(
        word in text for word in ("color", "colour", "font", "align", "background", "layout")
    ):
        import re
        cleaned = re.sub(r"^(make\s+the\s+)?title\s+(text\s+)?(to\s+)?", "", instruction, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"^rename\s+(the\s+)?title\s+(to\s+)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"^change\s+(the\s+)?title\s+(to\s+)?", "", cleaned, flags=re.IGNORECASE).strip()
        if cleaned:
            changes["title"] = cleaned
            changes.setdefault("zone_content", {})["title"] = cleaned
            messages.append("Updated the title text.")

    # 4. Font size and text formatting logic
    if "font" in text or "text" in text or "title" in text or "align" in text or "bold" in text or "size" in text:
        patch: Dict[str, Any] = {}
        import re
        size_match = re.search(r"(\d{1,3})\s*(?:px|point|pt)?", text)
        el = target_element()
        base_size = int((el or {}).get("fontSize") or 34)
        if "increase" in text or "bigger" in text or "larger" in text or "grow" in text:
            patch["fontSize"] = min(base_size + 6, 96)
        elif "decrease" in text or "smaller" in text or "reduce" in text or "shrink" in text:
            patch["fontSize"] = max(base_size - 6, 8)
        elif size_match and ("font" in text or "size" in text):
            patch["fontSize"] = max(8, min(int(size_match.group(1)), 96))

        if "bold" in text:
            patch["fontWeight"] = 800

        for align in ("left", "center", "right", "justify"):
            if align in text:
                patch["textAlign"] = align
                break

        if chosen_color and ("color" in text or "colour" in text or "font" in text or "text" in text):
            patch["color"] = chosen_color

        if patch:
            apply_text_style(patch)
            messages.append("Updated text formatting.")

    if not changes:
        return None
    return {"changes": changes, "message": " ".join(messages) or "Changes applied."}


@router.post("/generate-diagram")
async def generate_diagram(body: Dict[str, Any] = Body(...)):
    """
    Generate architecture diagram PNG from drawio_xml using matplotlib renderer.
    This endpoint is used by the editor shell to display architecture diagrams
    with the same styling as the downloaded PPT.
    """
    drawio_xml = body.get("drawio_xml")
    if not drawio_xml:
        raise HTTPException(status_code=400, detail="Missing 'drawio_xml' in request body.")
    
    try:
        from services.visual_engine import generate_drawio_diagram
        svg_path, png_path = generate_drawio_diagram(drawio_xml, topic="editor-preview")
        
        if png_path and os.path.exists(png_path):
            filename = os.path.basename(png_path)
            return {"png_path": png_path, "filename": filename}
        else:
            raise HTTPException(status_code=500, detail="Failed to generate diagram PNG")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate diagram: {str(e)}")


@router.post("/generate-from-prompts")
async def generate_from_prompts(body: Dict[str, Any] = Body(...)):
    """
    Generate presentation from custom slide prompts.
    This endpoint allows users to provide custom content/instructions for each slide.
    """
    tone = body.get("tone", "Professional")
    slides = body.get("slides", [])
    
    if not slides:
        raise HTTPException(status_code=400, detail="Missing 'slides' in request body.")
    
    # Generate session ID
    session_id = uuid.uuid4().hex[:12]
    
    try:
        # Build deck from custom prompts
        deck = {
            "title": "Custom Presentation",
            "slides": []
        }
        
        for idx, slide_data in enumerate(slides):
            title = slide_data.get("title", f"Slide {idx + 1}")
            content = slide_data.get("content", "")
            
            # Split content into bullet points
            bullet_points = []
            if content:
                bullet_points = [line.strip() for line in content.split("\n") if line.strip()]
            
            deck["slides"].append({
                "slide_type": "content",
                "title": title,
                "headline": title,
                "bullet_points": bullet_points,
                "layout_id": "OneColumn",  # Default layout
                "visual_type": "none",
                "visual_items": [],
                "image_keyword": "",
                "icon_emoji": "",
                "drawio_xml": "",
                "process_steps": None,
                "timeline_steps": None,
                "comparison_items": None,
                "architecture_nodes": None,
                "grid_items": None,
                "chart_data": None,
            })
        
        # Resolve visuals for the deck
        deck = resolve_visuals_for_deck(deck)
        
        # Generate PNGs for architecture slides
        try:
            from services.visual_engine import generate_drawio_diagram
            for slide in deck.get("slides", []):
                if slide.get("drawio_xml"):
                    try:
                        svg_path, png_path = generate_drawio_diagram(
                            slide["drawio_xml"],
                            topic=slide.get("title", ""),
                            disable_fallback=True
                        )
                        if png_path and os.path.exists(png_path):
                            filename = os.path.basename(png_path)
                            slide["diagram_png"] = f"http://127.0.0.1:8000/static/{filename}"
                            print(f"[ROUTES] Generated diagram PNG for slide: {slide.get('title')}")
                    except Exception as e:
                        print(f"[ROUTES] Failed to generate diagram PNG: {e}")
        except Exception as e:
            print(f"[ROUTES] Failed to import visual_engine: {e}")
        
        # Start building PPTX in background
        def build_background():
            try:
                import time
                start_time = time.time()
                
                # Prepare deck outline for PPTX builder
                deck_outline = {
                    "deck_title": deck.get("title", "Presentation"),
                    "slides": []
                }
                
                for slide in deck.get("slides", []):
                    deck_outline["slides"].append({
                        "slide_type": slide.get("slide_type", "content"),
                        "title": slide.get("title", ""),
                        "headline": slide.get("headline", ""),
                        "bullet_points": slide.get("bullet_points", []),
                        "layout_id": slide.get("layout_id", ""),
                        "visual_type": slide.get("visual_type", ""),
                        "visual_items": slide.get("visual_items", []),
                        "image_keyword": slide.get("image_keyword", ""),
                        "icon_emoji": slide.get("icon_emoji", ""),
                        "drawio_xml": slide.get("drawio_xml", ""),
                        "diagram_png": slide.get("diagram_png", ""),
                        "process_steps": slide.get("process_steps"),
                        "timeline_steps": slide.get("timeline_steps"),
                        "comparison_items": slide.get("comparison_items"),
                        "architecture_nodes": slide.get("architecture_nodes"),
                        "grid_items": slide.get("grid_items"),
                        "chart_data": slide.get("chart_data"),
                    })
                
                output_path = build_pptx(deck_outline, topic="Custom Prompts", tone=tone)
                
                elapsed = time.time() - start_time
                print(f"[CACHE] ✅ PPTX pre-built in {elapsed:.2f}s: {output_path}")
                PPTX_CACHE[session_id] = output_path
            except Exception as e:
                print(f"[CACHE] ❌ Pre-build failed: {e}")
                PPTX_CACHE[session_id] = "failed"
        
        threading.Thread(target=build_background, daemon=True).start()
        
        # Return JSON immediately with session_id
        return {
            **deck,
            "session_id": session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate presentation from prompts: {str(e)}")


@router.post("/agent-edit")
async def agent_edit_slide(body: Dict[str, Any] = Body(...)):
    """
    AI Agent endpoint: receives a slide JSON + user instruction,
    returns structured JSON changes to apply to the slide.
    """
    from services.llm_client import call_llm
    import json as _json

    slide_data = body.get("slide")
    selected_element_id = body.get("selectedElementId")
    selected_zone_key = body.get("selectedZoneKey")
    instruction = body.get("instruction", "").strip()

    if not slide_data:
        raise HTTPException(status_code=400, detail="Missing 'slide' in request body.")
    if not instruction:
        raise HTTPException(status_code=400, detail="Missing 'instruction' in request body.")

    # Build a compact slide summary for the LLM
    slide_summary = {
        "id": slide_data.get("id"),
        "title": slide_data.get("title"),
        "background": slide_data.get("background"),
        "layout_id": slide_data.get("layout_id"),
        "zone_content": slide_data.get("zone_content"),
        "elements": [
            {
                "id": el.get("id"),
                "kind": el.get("kind"),
                "text": el.get("text"),
                "fontSize": el.get("fontSize"),
                "fontWeight": el.get("fontWeight"),
                "color": el.get("color"),
                "fill": el.get("fill"),
                "x": el.get("x"),
                "y": el.get("y"),
                "width": el.get("width"),
                "height": el.get("height"),
                "items": el.get("items"),
            }
            for el in slide_data.get("elements", [])
        ],
    }

    local_result = _build_local_agent_edit(slide_summary, instruction, selected_element_id, selected_zone_key)
    if local_result:
        if "changes" in local_result:
            local_result["changes"] = resolve_agent_edit_changes(local_result["changes"], slide_summary)
        return local_result

    system_prompt = """You are an AI slide editor assistant. The user will give you a slide's current data (JSON) and an instruction to modify it.

You MUST respond with ONLY a valid JSON object (no markdown, no code fences, no explanation outside JSON) with exactly these two keys:
{
  "changes": { ... },
  "message": "Human-readable summary of what you changed"
}

The "changes" object can contain any combination of:
- "background": "#hexcolor" — to change the slide background color
- "title": "new title" — to change the slide title
- "layout_id": "Hero"|"OneColumn"|"TwoColumn"|"ThreeColumn"|"FourGrid"|"Dashboard"|"Architecture"|"Timeline"|"Comparison"|"Process" — to change layout
- "zone_content": { ... } — partial update to zone_content fields (merged with existing)
- "elements": { "element-id": { "text": "...", "fontSize": 24, "fontWeight": 700, "color": "#hex", "fill": "#hex", "width": 100, "height": 50, "x": 10, "y": 20, "items": ["a","b"] }, ... } — partial updates to specific elements by their ID

Only include fields that need to change. Do NOT include unchanged fields.

IMPORTANT RULES:
- All colors must be valid hex codes (e.g. "#ff0000" for red, "#1e40af" for dark blue).
- Font sizes are numbers in pixels (e.g. 24, 36, 48).
- Font weights: 400 = normal, 600 = semi-bold, 700 = bold, 800 = extra-bold.
- For text changes, provide the full new text value.
- Respond with ONLY the JSON object, nothing else."""

    user_prompt = f"""Current slide data:
{_json.dumps(slide_summary, indent=2)}

User instruction: {instruction}"""

    try:
        raw_response = call_llm(system_prompt, user_prompt)
        print(f"[AGENT] Raw LLM response: {raw_response[:500]}")

        # Clean up the response — strip markdown code fences if present
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            # Remove opening fence (with optional language tag)
            first_newline = cleaned.index("\n")
            cleaned = cleaned[first_newline + 1:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        result = _json.loads(cleaned)

        # Validate structure
        if "changes" not in result:
            result = {"changes": result, "message": "Changes applied."}
        
        result["changes"] = resolve_agent_edit_changes(result["changes"], slide_summary)

        if "message" not in result:
            result["message"] = "Changes applied successfully."

        return result

    except _json.JSONDecodeError as e:
        print(f"[AGENT] JSON parse error: {e}")
        print(f"[AGENT] Raw response was: {raw_response}")
        raise HTTPException(
            status_code=500,
            detail=f"AI returned invalid JSON. Please try rephrasing your instruction. Raw: {raw_response[:200]}"
        )
    except Exception as e:
        print(f"[AGENT] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Agent edit failed: {str(e)}")


@router.get("/layouts")
def list_layouts():
    return get_layout_summaries()


from pydantic import BaseModel

class TranslateRequest(BaseModel):
    deck_data: dict
    target_language: str        # e.g. "ta"
    target_language_name: str   # e.g. "Tamil"


@router.post("/translate")
async def translate_deck(request: TranslateRequest):
    """
    Translate entire deck to target language.
    Uses existing OpenRouter LLM — no extra cost.
    """
    from services.llm_client import call_llm
    import json
    import copy

    deck = request.deck_data
    if not deck:
        return {"translated_deck": deck}

    # Extract all translatable texts to a flat dictionary
    extracted = {}
    
    # 1. Deck title
    if "deck_title" in deck and isinstance(deck["deck_title"], str):
        extracted["deck_title"] = deck["deck_title"]
        
    # 2. Slides
    for s_idx, slide in enumerate(deck.get("slides", [])):
        if "title" in slide and isinstance(slide["title"], str):
            extracted[f"slides.{s_idx}.title"] = slide["title"]
        if "speaker_notes" in slide and isinstance(slide["speaker_notes"], str):
            extracted[f"slides.{s_idx}.speaker_notes"] = slide["speaker_notes"]
        if "description" in slide and isinstance(slide["description"], str):
            extracted[f"slides.{s_idx}.description"] = slide["description"]
            
        # Bullet points list
        if "bullet_points" in slide and isinstance(slide["bullet_points"], list):
            for b_idx, bp in enumerate(slide["bullet_points"]):
                if isinstance(bp, str):
                    extracted[f"slides.{s_idx}.bullet_points.{b_idx}"] = bp

        # Zone content
        zone = slide.get("zone_content")
        if isinstance(zone, dict):
            for k, v in zone.items():
                if k in ("title", "subtitle", "body", "headline", "left_headline", "left_text", "right_headline", "right_text", "insight") and isinstance(v, str):
                    extracted[f"slides.{s_idx}.zone_content.{k}"] = v
                elif k == "bullets" and isinstance(v, list):
                    for b_idx, bp in enumerate(v):
                        if isinstance(bp, str):
                            extracted[f"slides.{s_idx}.zone_content.bullets.{b_idx}"] = bp

        # Elements
        elements = slide.get("elements", [])
        if isinstance(elements, list):
            for e_idx, el in enumerate(elements):
                if isinstance(el, dict):
                    # Check text field
                    if "text" in el and isinstance(el["text"], str):
                        text_val = el["text"]
                        # Skip if it is an image URL or placeholder
                        if not (text_val.startswith("http://") or text_val.startswith("https://") or text_val.startswith("data:")):
                            extracted[f"slides.{s_idx}.elements.{e_idx}.text"] = text_val
                    # Check items list
                    if "items" in el and isinstance(el["items"], list):
                        for item_idx, item in enumerate(el["items"]):
                            if isinstance(item, str):
                                extracted[f"slides.{s_idx}.elements.{e_idx}.items.{item_idx}"] = item

    # If there's nothing to translate, return early
    if not extracted:
        return {"translated_deck": deck}

    # Prepare translation request to LLM
    TRANSLATE_SYSTEM = """You are a professional translator.
Translate the values of the given JSON dictionary to the target language.
Keep the keys EXACTLY the same.
Return ONLY a valid JSON dictionary containing the exact same keys with translated values.
Do not include any explanation, intro/outro text, or markdown formatting outside the JSON."""

    user_prompt = f"""
Translate the values of this dictionary to: {request.target_language} ({request.target_language_name})

DICTIONARY TO TRANSLATE:
{json.dumps(extracted, ensure_ascii=False, indent=2)}
"""

    result = call_llm(TRANSLATE_SYSTEM, user_prompt)
    
    # Clean and parse
    result = result.strip()
    if result.startswith('```'):
        # Remove opening fence
        first_newline = result.index("\n")
        result = result[first_newline + 1:]
    if result.endswith('```'):
        result = result[:-3]
    result = result.strip()
    
    translated_texts = json.loads(result)

    # Reconstruct the deck with translated values
    new_deck = copy.deepcopy(deck)
    for path, translated_text in translated_texts.items():
        parts = path.split(".")
        current = new_deck
        
        # Traverse to the parent container
        for part in parts[:-1]:
            if part.isdigit():
                idx = int(part)
                if isinstance(current, list) and idx < len(current):
                    current = current[idx]
                else:
                    break
            else:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    break
        else:
            # Set the value at the last key/index
            last_key = parts[-1]
            if last_key.isdigit():
                idx = int(last_key)
                if isinstance(current, list) and idx < len(current):
                    current[idx] = translated_text
            else:
                if isinstance(current, dict):
                    current[last_key] = translated_text
                    
    return {"translated_deck": new_deck}


class YouTubeSummarizeRequest(BaseModel):
    url: str


@router.post("/video/summarize")
async def youtube_summarize(url: str = Form(...)):
    if not url:
        raise HTTPException(status_code=400, detail="YouTube URL is required.")
    try:
        from services.youtube_service import extract_video_id, validate_duration, get_video_duration
        from services.transcript_service import fetch_transcript
        from services.summarizer_service import generate_video_summary
        
        video_id = extract_video_id(url)
        if video_id in YOUTUBE_SUMMARY_CACHE:
            summary = YOUTUBE_SUMMARY_CACHE[video_id]
        else:
            duration = get_video_duration(video_id)
            is_valid, msg = validate_duration(duration)
            if not is_valid:
                raise HTTPException(status_code=400, detail=msg)
                
            transcript = fetch_transcript(video_id)
            summary = generate_video_summary(transcript)
            YOUTUBE_SUMMARY_CACHE[video_id] = summary
            
        return {
            "success": True,
            "summary": summary
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"YouTube processing failed: {str(e)}")

