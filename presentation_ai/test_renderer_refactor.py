#!/usr/bin/env python3
"""
Test script to verify the renderer refactoring works correctly with different visual styles.
"""

import sys
sys.path.append('E:/Slide_Generator/presentation_ai')

from services.architecture_v4.renderer import generate_architecture_v4

print("Testing renderer refactoring with different visual styles...")
print("=" * 60)

test_cases = [
    {
        "architecture_type": "cloud",
        "visual_style": "aws",
        "topic": "AWS Cloud Architecture"
    },
    {
        "architecture_type": "kubernetes",
        "visual_style": "kubernetes",
        "topic": "Kubernetes Cluster"
    },
    {
        "architecture_type": "rag",
        "visual_style": "ai_dark_neon",
        "topic": "RAG Pipeline"
    },
    {
        "architecture_type": "microservices",
        "visual_style": "drawio_vivid",
        "topic": "Microservices Architecture"
    },
    {
        "architecture_type": "transformer",
        "visual_style": "minimal",
        "topic": "Transformer Model"
    }
]

for i, test_case in enumerate(test_cases, 1):
    print(f"\nTest {i}: {test_case['architecture_type']} + {test_case['visual_style']}")
    print("-" * 60)
    try:
        xml = generate_architecture_v4(
            architecture_type=test_case["architecture_type"],
            visual_style=test_case["visual_style"],
            topic=test_case["topic"],
            slide_title=test_case["topic"],
            slide_content=""
        )
        if xml:
            print(f"✓ Successfully generated XML ({len(xml)} characters)")
            print(f"  First 200 chars: {xml[:200]}...")
        else:
            print("✗ Failed: No XML generated")
    except Exception as e:
        print(f"✗ Failed with exception: {e}")

print("\n" + "=" * 60)
print("Renderer refactoring test complete!")
