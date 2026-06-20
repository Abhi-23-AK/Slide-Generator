"""
Unit tests for Layout Engine (using standard unittest library)
"""

import unittest
from services.layout_engine import (
    score_layout,
    fit_content_to_layout,
    handle_overflow,
    assign_layouts,
    count_words
)
from models.layout_definitions import (
    ALL_LAYOUTS,
    get_layout,
    ONE_COLUMN,
    TWO_COLUMN,
    THREE_COLUMN,
    FOUR_GRID,
    HERO,
    TIMELINE
)


class TestLayoutEngine(unittest.TestCase):

    def test_count_words(self):
        self.assertEqual(count_words("Hello world"), 2)
        self.assertEqual(count_words(""), 0)
        self.assertEqual(count_words(None), 0)
        self.assertEqual(count_words("Test, with punctuation: here!"), 4)

    def test_score_layout_type_match(self):
        # Title slide matches Hero best_for
        title_slide = {"slide_type": "title", "bullet_points": []}
        hero_score = score_layout(title_slide, HERO, [])
        timeline_score = score_layout(title_slide, TIMELINE, [])
        self.assertGreater(hero_score, timeline_score)

    def test_score_layout_word_count_fit(self):
        # Small slide fits ONE_COLUMN capacity (92 words)
        small_slide = {"slide_type": "content", "bullet_points": ["Short point 1", "Short point 2"]}
        # Large slide exceeds ONE_COLUMN capacity
        large_bullets = ["Word " * 20 for _ in range(5)]
        large_slide = {"slide_type": "content", "bullet_points": large_bullets}

        small_score = score_layout(small_slide, ONE_COLUMN, [])
        large_score = score_layout(large_slide, ONE_COLUMN, [])
        self.assertGreater(small_score, large_score)

    def test_score_layout_variety_penalty(self):
        slide = {"slide_type": "content", "bullet_points": ["point 1"]}
        # No penalty
        score_normal = score_layout(slide, ONE_COLUMN, [])
        # Penalty applied when last two layouts were '1-column'
        score_penalized = score_layout(slide, ONE_COLUMN, ["1-column", "1-column"])
        self.assertLess(score_penalized, score_normal)
        self.assertAlmostEqual(score_normal - score_penalized, 0.08, places=5)

    def test_fit_content_to_layout(self):
        slide = {
            "title": "My Title",
            "bullet_points": ["Point A", "Point B", "Point C"],
            "visual_type": "none"
        }
        fitted = fit_content_to_layout(slide, ONE_COLUMN)
        self.assertEqual(fitted["zone_content"]["headline"], "My Title")
        self.assertEqual(fitted["zone_content"]["body"], "Point A\nPoint B\nPoint C")

    def test_handle_overflow_split(self):
        # Slide with 6 bullets should be split
        overflow_slide = {
            "title": "Overflow Slide",
            "bullet_points": ["P1", "P2", "P3", "P4", "P5", "P6"],
            "slide_type": "content"
        }
        results = handle_overflow(overflow_slide, ONE_COLUMN, [])
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["title"], "Overflow Slide")
        self.assertEqual(len(results[0]["bullet_points"]), 4)
        self.assertEqual(results[1]["title"], "Overflow Slide (continued)")
        self.assertEqual(len(results[1]["bullet_points"]), 2)
        self.assertEqual(results[1]["is_continuation"], True)

    def test_handle_overflow_upgrade(self):
        # Word count too high for timeline (50 words capacity) but fits 2-column (120 words)
        heavy_timeline_slide = {
            "title": "Heavy Timeline",
            "bullet_points": ["This is a very long description word word word " * 10],
            "slide_type": "timeline"
        }
        results = handle_overflow(heavy_timeline_slide, TIMELINE, [])
        self.assertEqual(len(results), 1)
        self.assertIn(results[0]["layout_id"], ("1-column", "2-column", "3-column"))

    def test_assign_layouts_orchestrator(self):
        slides = [
            {"title": "Intro", "bullet_points": [], "slide_type": "title"},
            {"title": "Point Comparison", "bullet_points": ["Item A", "Item B"], "slide_type": "comparison"},
            {"title": "KPI Metrics", "bullet_points": ["Stat 1", "Stat 2", "Stat 3", "Stat 4"], "slide_type": "data"}
        ]
        resolved = assign_layouts(slides)
        self.assertGreaterEqual(len(resolved), 3)
        self.assertEqual(resolved[0]["layout_id"], "hero")
        self.assertIn(resolved[1]["layout_id"], ("2-column", "3-column", "1-column"))
        self.assertIn(resolved[2]["layout_id"], ("4-grid", "dashboard", "1-column", "2-column"))


if __name__ == "__main__":
    unittest.main()
