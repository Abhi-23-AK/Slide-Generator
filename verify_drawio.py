# -*- coding: utf-8 -*-
import sys
import os
import io

# Set sys.stdout/stderr to UTF-8 to avoid encoding errors when printing to console
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', errors='replace')

sys.path.append('./presentation_ai')

from services.slide_planner import generate_outline
from services.layout_engine import assign_layouts  
from services.visual_engine import generate_drawio_diagram
import json

print("=== STEP 1: Generate outline ===")
deck = generate_outline(
    topic="Cloud Microservices Architecture",
    slide_count=3,
    tone="technical",
    sample_titles=None,
    source_text=""
)

print(f"Total slides: {len(deck.get('slides',[]))}")

print("\n=== STEP 2: Check each slide ===")
for i, slide in enumerate(deck.get('slides',[])):
    print(f"\nSlide {i+1}:")
    print(f"  type: {slide.get('slide_type')}")
    print(f"  layout: {slide.get('layout')} (layout_id: {slide.get('layout_id')})")
    print(f"  has drawio_xml: {'drawio_xml' in slide}")
    xml = slide.get('drawio_xml','')
    print(f"  drawio_xml length: {len(xml)}")
    
    if xml:
        import re
        cells = len(re.findall(r'<mxCell', xml))
        arrows = len(re.findall(r'edge="1"', xml))
        nested = len(re.findall(r'parent="(?!0|1")', xml))
        print(f"  XML stats: {cells} cells, {arrows} arrows, {nested} nested")
        
        print(f"\n=== STEP 3: Render diagram for slide {i+1} ===")
        # Pass slide title as topic context
        svg_path, png_path = generate_drawio_diagram(xml, topic=slide.get("title") or "")
        print(f"  SVG path: {svg_path}")
        print(f"  PNG path: {png_path}")
        
        if png_path:
            exists = os.path.exists(png_path)
            size = os.path.getsize(png_path) if exists else 0
            print(f"  PNG exists: {exists}")
            print(f"  PNG size: {size} bytes")
            if size < 5000:
                print("  ⚠️ WARNING: PNG too small — likely blank/failed render!")
            else:
                print("  ✅ PNG looks valid!")
        else:
            print("  ❌ PNG path is None — rendering FAILED!")

print("\n=== STEP 4: Full PPTX generation test ===")
from services.pptx_builder import build_pptx

# Pass the tone to preserve technical style
output_path = build_pptx(deck, topic="Cloud Microservices Architecture", tone="technical")
print(f"PPTX saved: {output_path}")
print(f"PPTX size: {os.path.getsize(output_path)} bytes")

# Open the PPTX to verify
print("\nOpen the generated PPTX file and check:")
print(f"  Location: {output_path}")
print("  Does slide 1/2/3 show a complex diagram?")
print("  Or does it still show simple cards?")
