import sys
import os

# Add presentation_ai root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.pptx_builder import build_pptx

# Define a sample 5-slide deck
sample_deck = {
    "deck_title": "E-Commerce Strategy",
    "slides": [
        {
            "slide_type": "title",
            "layout_id": "hero",
            "title": "E-Commerce Expansion Blueprint",
            "bullet_points": ["Achieving 10x Scale with Decoupled Tech Stack and Dynamic Conversion Funnels"]
        },
        {
            "slide_type": "content",
            "layout_id": "1-column",
            "title": "Strategy Overview",
            "headline": "Strategic Growth Pillars for 2026",
            "bullet_points": [
                "Deploy modular storefronts using Next.js and Tailwind CSS for instant rendering and high speed.",
                "Integrate real-time inventory synchronization across Shopify and Amazon marketplaces.",
                "Challenge: High customer acquisition costs restrict traditional direct-to-consumer search advertising channels.",
                "Optimize search engine presence with automated schema markup and rich editorial blogs."
            ]
        },
        {
            "slide_type": "content",
            "layout_id": "2-column",
            "title": "Target Conversion Metrics",
            "left_headline": "Direct Channel Performance",
            "left_text": "Our dynamic conversion funnel is designed to minimize friction and maximize lifetime customer value.",
            "bullet_points": [
                "Implement 1-click checkout buttons to reduce cart abandonment rates by 25%.",
                "Challenge: Mobile users experience higher drop-off rates on multi-step shipping detail screens.",
                "Personalize post-purchase email recommendations using machine learning models.",
                "A/B test home page layout variants to prioritize hero banners."
            ],
            "visual_type": "image",
            "visual_items": ["shopping checkout"]
        },
        {
            "slide_type": "content",
            "layout_id": "3-column",
            "title": "Fulfilment Workflow Phases",
            "bullet_points": [
                "Order Placement: Users purchase products via mobile app or responsive desktop browser.",
                "Warehouse Processing: Automated picking robots select items and route them to shipping docks.",
                "Last-mile Delivery: Local shipping partners deliver parcels directly to consumer doorsteps."
            ],
            "zone_content": {
                "col_1_image": "",
                "col_2_image": "",
                "col_3_image": ""
            }
        },
        {
            "slide_type": "content",
            "layout_id": "dashboard",
            "title": "Executive Performance Summary",
            "bullet_points": [
                "Overall quarterly performance shows extremely high growth across channels.",
                "Strong user retention and pricing optimizations have yielded double-digit revenue expansions across all major product lines this quarter."
            ]
        }
    ]
}

# Test standard and ecommerce tones
for tone in ["Professional", "Ecommerce"]:
    print(f"Generating PPTX with tone '{tone}'...")
    filepath = build_pptx(sample_deck, topic=f"Ecommerce_Strategy_{tone}_test", tone=tone, output_dir="outputs")
    print(f"Successfully generated: {filepath}")
