import unittest
from unittest.mock import patch, MagicMock
from services.pptx_builder import build_pptx

class TestNeumorphismLayouts(unittest.TestCase):
    @patch('services.pptx_builder._add_1_column_slide')
    @patch('services.professional_layouts._add_prof_1_column_slide')
    @patch('services.neumorphism_layouts._add_neuro_photo_showcase')
    def test_neumorphism_tone_calls_neumorphic_layout(self, mock_neuro_layout, mock_prof_layout, mock_std_layout):
        deck = {
            "deck_title": "Neumorphism Test",
            "slides": [
                {
                    "title": "Intro",
                    "layout_id": "1-column",
                    "slide_type": "content",
                    "bullet_points": ["Point 1"]
                }
            ]
        }
        
        # Call build_pptx with Neumorphism tone
        build_pptx(deck, topic="Neumorphism_Test", tone="Neumorphism")
        
        # Verify the neumorphic layout builder was called
        mock_neuro_layout.assert_called_once()
        mock_prof_layout.assert_not_called()
        mock_std_layout.assert_not_called()

    @patch('services.pptx_builder._add_1_column_slide')
    @patch('services.professional_layouts._add_prof_hero_slide')
    @patch('services.neumorphism_layouts._add_neuro_blob_hero')
    def test_neumorphism_hero_layout(self, mock_neuro_hero, mock_prof_hero, mock_std_layout):
        deck = {
            "deck_title": "Neumorphism Hero Test",
            "slides": [
                {
                    "title": "Hero Slide Title",
                    "layout_id": "hero",
                    "slide_type": "title",
                    "bullet_points": ["Subheading"]
                }
            ]
        }
        
        # Call build_pptx with Neumorphism tone
        build_pptx(deck, topic="Neumorphism_Hero_Test", tone="Neumorphism")
        
        # Verify the neumorphic hero layout builder was called
        mock_neuro_hero.assert_called_once()
        mock_prof_hero.assert_not_called()

if __name__ == "__main__":
    unittest.main()
