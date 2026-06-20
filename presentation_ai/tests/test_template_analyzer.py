"""
Unit tests for template analyzer role and card detection logic.
"""

import unittest
from services.template_analyzer import _determine_semantic_roles

class TestTemplateAnalyzer(unittest.TestCase):

    def test_determine_semantic_roles_decorative_filter(self):
        # Decorative shapes (width_pct < 3 or height_pct < 3) should become decorative_{shape_id}
        shapes = [
            {
                "shape_id": 1,
                "name": "Line 1",
                "shape_type": "LINE",
                "left_pct": 10.0,
                "top_pct": 10.0,
                "width_pct": 2.0,
                "height_pct": 50.0,
                "has_text_frame": False,
                "is_picture": False,
                "capacity": 0
            },
            {
                "shape_id": 2,
                "name": "Horizontal Divider",
                "shape_type": "RECTANGLE",
                "left_pct": 10.0,
                "top_pct": 20.0,
                "width_pct": 80.0,
                "height_pct": 1.5,
                "has_text_frame": False,
                "is_picture": False,
                "capacity": 0
            }
        ]
        card_groups = _determine_semantic_roles(shapes)
        self.assertEqual(shapes[0]["role"], "decorative_1")
        self.assertEqual(shapes[1]["role"], "decorative_2")

    def test_determine_semantic_roles_no_body1_body2_body3(self):
        # The analyzer must NEVER assign body1, body2, or body3
        shapes = [
            {
                "shape_id": 10,
                "name": "Title Text",
                "shape_type": "TEXT_BOX",
                "left_pct": 10.0,
                "top_pct": 5.0,
                "width_pct": 80.0,
                "height_pct": 10.0,
                "has_text_frame": True,
                "is_picture": False,
                "capacity": 10
            },
            {
                "shape_id": 11,
                "name": "Body Text",
                "shape_type": "TEXT_BOX",
                "left_pct": 10.0,
                "top_pct": 20.0,
                "width_pct": 80.0,
                "height_pct": 40.0,
                "has_text_frame": True,
                "is_picture": False,
                "capacity": 100
            }
        ]
        card_groups = _determine_semantic_roles(shapes)
        roles = [s["role"] for s in shapes]
        self.assertNotIn("body1", roles)
        self.assertNotIn("body2", roles)
        self.assertNotIn("body3", roles)

    def test_determine_semantic_roles_card_clustering(self):
        # Two visual cards side-by-side:
        # Card 1: at left_pct=10, containing an icon oval, a title, a description
        # Card 2: at left_pct=50, containing an icon oval, a title, a description
        shapes = [
            # Slide Title
            {
                "shape_id": 1,
                "name": "Slide Title",
                "shape_type": "TEXT_BOX",
                "left_pct": 10.0,
                "top_pct": 5.0,
                "width_pct": 80.0,
                "height_pct": 10.0,
                "has_text_frame": True,
                "is_picture": False,
                "placeholder_type": "TITLE",
                "capacity": 10
            },
            # Card 1 Components
            {
                "shape_id": 10,
                "name": "Oval 1",  # Circle Icon
                "shape_type": "OVAL",
                "left_pct": 10.0,
                "top_pct": 25.0,
                "width_pct": 5.0,
                "height_pct": 5.0,
                "has_text_frame": False,
                "is_picture": False,
                "capacity": 0
            },
            {
                "shape_id": 11,
                "name": "Card 1 Title",
                "shape_type": "TEXT_BOX",
                "left_pct": 10.0,
                "top_pct": 32.0,
                "width_pct": 25.0,
                "height_pct": 8.0,
                "has_text_frame": True,
                "is_picture": False,
                "capacity": 8
            },
            {
                "shape_id": 12,
                "name": "Card 1 Description",
                "shape_type": "TEXT_BOX",
                "left_pct": 10.0,
                "top_pct": 42.0,
                "width_pct": 25.0,
                "height_pct": 30.0,
                "has_text_frame": True,
                "is_picture": False,
                "capacity": 60
            },
            # Card 2 Components
            {
                "shape_id": 20,
                "name": "Oval 2",  # Circle Icon
                "shape_type": "OVAL",
                "left_pct": 50.0,
                "top_pct": 25.0,
                "width_pct": 5.0,
                "height_pct": 5.0,
                "has_text_frame": False,
                "is_picture": False,
                "capacity": 0
            },
            {
                "shape_id": 21,
                "name": "Card 2 Title",
                "shape_type": "TEXT_BOX",
                "left_pct": 50.0,
                "top_pct": 32.0,
                "width_pct": 25.0,
                "height_pct": 8.0,
                "has_text_frame": True,
                "is_picture": False,
                "capacity": 8
            },
            {
                "shape_id": 22,
                "name": "Card 2 Description",
                "shape_type": "TEXT_BOX",
                "left_pct": 50.0,
                "top_pct": 42.0,
                "width_pct": 25.0,
                "height_pct": 30.0,
                "has_text_frame": True,
                "is_picture": False,
                "capacity": 60
            }
        ]
        
        card_groups = _determine_semantic_roles(shapes)
        
        # Verify slide title
        slide_title = next(s for s in shapes if s["shape_id"] == 1)
        self.assertEqual(slide_title["role"], "title")
        
        # Verify card 1 roles
        c1_icon = next(s for s in shapes if s["shape_id"] == 10)
        c1_title = next(s for s in shapes if s["shape_id"] == 11)
        c1_desc = next(s for s in shapes if s["shape_id"] == 12)
        
        self.assertEqual(c1_icon["role"], "card1_icon")
        self.assertEqual(c1_title["role"], "card1_title")
        self.assertEqual(c1_desc["role"], "card1_description")
        
        # Verify card 2 roles
        c2_icon = next(s for s in shapes if s["shape_id"] == 20)
        c2_title = next(s for s in shapes if s["shape_id"] == 21)
        c2_desc = next(s for s in shapes if s["shape_id"] == 22)
        
        self.assertEqual(c2_icon["role"], "card2_icon")
        self.assertEqual(c2_title["role"], "card2_title")
        self.assertEqual(c2_desc["role"], "card2_description")
        
        # Verify uniqueness of roles
        roles = [s["role"] for s in shapes]
        self.assertEqual(len(roles), len(set(roles)))
        
        # Verify returned card groups metadata
        self.assertEqual(len(card_groups), 2)
        self.assertEqual(card_groups[0]["group_id"], 1)
        self.assertEqual(card_groups[0]["icon_shape_id"], 10)
        self.assertEqual(card_groups[0]["title_shape_id"], 11)
        self.assertEqual(card_groups[0]["description_shape_id"], 12)
        
        self.assertEqual(card_groups[1]["group_id"], 2)
        self.assertEqual(card_groups[1]["icon_shape_id"], 20)
        self.assertEqual(card_groups[1]["title_shape_id"], 21)
        self.assertEqual(card_groups[1]["description_shape_id"], 22)

    def test_determine_semantic_roles_small_narrow_shapes(self):
        # Small narrow shapes (width_pct < 25 or height_pct < 10 or capacity < 15) outside cards
        # should become label, caption, footer depending on vertical position
        shapes = [
            {
                "shape_id": 1,
                "name": "Label Box",
                "shape_type": "TEXT_BOX",
                "left_pct": 10.0,
                "top_pct": 15.0,  # Top section -> label
                "width_pct": 20.0,
                "height_pct": 5.0,
                "has_text_frame": True,
                "is_picture": False,
                "capacity": 10
            },
            {
                "shape_id": 2,
                "name": "Caption Box",
                "shape_type": "TEXT_BOX",
                "left_pct": 10.0,
                "top_pct": 50.0,  # Middle section -> caption
                "width_pct": 20.0,
                "height_pct": 5.0,
                "has_text_frame": True,
                "is_picture": False,
                "capacity": 10
            },
            {
                "shape_id": 3,
                "name": "Footer Box",
                "shape_type": "TEXT_BOX",
                "left_pct": 10.0,
                "top_pct": 85.0,  # Bottom section -> footer
                "width_pct": 20.0,
                "height_pct": 5.0,
                "has_text_frame": True,
                "is_picture": False,
                "capacity": 10
            }
        ]
        card_groups = _determine_semantic_roles(shapes)
        self.assertEqual(shapes[0]["role"], "label_1")
        self.assertEqual(shapes[1]["role"], "caption_2")
        self.assertEqual(shapes[2]["role"], "footer1")

    def test_generate_outline_from_template_filtering(self):
        from services.slide_planner import generate_outline_from_template
        # Mock template schema
        template_schema = {
            "slide_count": 1,
            "theme": {
                "heading_font": "Arial",
                "body_font": "Calibri",
                "colors": {}
            },
            "slides": [
                {
                    "slide_index": 0,
                    "inferred_layout": "hero",
                    "zones": [
                        {"role": "title", "capacity": 20},
                        {"role": "subtitle", "capacity": 30},
                        {"role": "image1", "capacity": 0},
                        {"role": "card1_title", "capacity": 15},
                        {"role": "card1_description", "capacity": 40},
                        {"role": "footer1", "capacity": 10},      # Filtered
                        {"role": "caption_2", "capacity": 10},     # Filtered
                        {"role": "label_3", "capacity": 10},       # Filtered
                        {"role": "icon_1", "capacity": 0},         # Filtered
                        {"role": "decorative_10", "capacity": 0},  # Filtered
                    ]
                }
            ]
        }
        
        from unittest.mock import patch
        with patch("services.slide_planner.call_llm") as mock_call:
            mock_call.return_value = """
            {
              "deck_title": "Test Deck",
              "template_mode": true,
              "slides": [
                {
                  "slide_index": 0,
                  "layout": "hero",
                  "title": "Main Title",
                  "subtitle": "Sub Title",
                  "card1_title": "Card Title",
                  "card1_description": "Card Desc",
                  "image1_keyword": "ai future"
                }
              ]
            }
            """
            
            deck = generate_outline_from_template(
                topic="AI Innovation",
                template_schema=template_schema,
                tone="Professional"
            )
            
            # Verify filtered zones did not reach LLM
            user_prompt = mock_call.call_args[0][1]
            self.assertIn("title", user_prompt)
            self.assertIn("subtitle", user_prompt)
            self.assertIn("card1_title", user_prompt)
            self.assertIn("image1", user_prompt)
            
            # Filtered roles should not be in the prompt's layout zones configuration
            self.assertNotIn("footer1", user_prompt)
            self.assertNotIn("caption_2", user_prompt)
            self.assertNotIn("label_3", user_prompt)
            self.assertNotIn("icon_1", user_prompt)
            self.assertNotIn("decorative_10", user_prompt)
            
            # Check slide content has the dynamic keyword
            slide = deck["slides"][0]
            self.assertEqual(slide["image1_keyword"], "ai future")
            # Verify no icon_emoji was added in template mode
            self.assertNotIn("icon_emoji", slide)

        # Test missing image keyword post-processing
        with patch("services.slide_planner.call_llm") as mock_call:
            mock_call.return_value = """
            {
              "deck_title": "Test Deck",
              "template_mode": true,
              "slides": [
                {
                  "slide_index": 0,
                  "layout": "hero",
                  "title": "Main Title",
                  "subtitle": "Sub Title",
                  "card1_title": "Card Title",
                  "card1_description": "Card Desc"
                }
              ]
            }
            """
            
            deck = generate_outline_from_template(
                topic="AI Innovation",
                template_schema=template_schema,
                tone="Professional"
            )
            
            slide = deck["slides"][0]
            # Verify image1_keyword was automatically generated and populated
            self.assertIn("image1_keyword", slide)
            self.assertEqual(slide["image1_keyword"], "Main Title image1")

if __name__ == "__main__":
    unittest.main()
