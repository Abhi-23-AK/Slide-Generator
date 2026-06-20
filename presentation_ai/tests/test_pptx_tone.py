import unittest
from unittest.mock import patch, MagicMock
from services.pptx_builder import build_pptx

class TestPptxTone(unittest.TestCase):
    @patch('services.pptx_builder._add_1_column_slide')
    @patch('services.professional_layouts._add_prof_1_column_slide')
    def test_professional_tone_calls_professional_layout(self, mock_prof_layout, mock_std_layout):
        deck = {
            "deck_title": "Professional Test",
            "slides": [
                {
                    "title": "Intro",
                    "layout_id": "1-column",
                    "slide_type": "content",
                    "bullet_points": ["Point 1"]
                }
            ]
        }
        
        # Call build_pptx with Professional tone
        build_pptx(deck, topic="Professional_Test", tone="Professional")
        
        # Verify the professional layout builder was called
        mock_prof_layout.assert_called_once()
        mock_std_layout.assert_not_called()

    @patch('services.pptx_builder._add_1_column_slide')
    @patch('services.professional_layouts._add_prof_1_column_slide')
    def test_non_professional_tone_calls_standard_layout(self, mock_prof_layout, mock_std_layout):
        deck = {
            "deck_title": "Technical Test",
            "slides": [
                {
                    "title": "Intro",
                    "layout_id": "1-column",
                    "slide_type": "content",
                    "bullet_points": ["Point 1"]
                }
            ]
        }
        
        # Call build_pptx with Technical tone
        build_pptx(deck, topic="Technical_Test", tone="Technical")
        
        # Verify the standard layout builder was called, NOT the professional one
        mock_std_layout.assert_called_once()
        mock_prof_layout.assert_not_called()

    @patch('api.routes.build_pptx')
    def test_export_pptx_route_preserves_tone(self, mock_build_pptx):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from api.routes import router
        
        # Setup test client for routers
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Mock build_pptx return path to exist
        import os
        import tempfile
        temp_pptx = os.path.join(tempfile.gettempdir(), "test_export.pptx")
        with open(temp_pptx, "wb") as f:
            f.write(b"dummy pptx data")
            
        mock_build_pptx.return_value = temp_pptx
        
        # Call /export-pptx with tone "Neumorphism"
        response = client.post("/export-pptx", json={
            "title": "Sports in Neumorphism",
            "tone": "Neumorphism",
            "slides": [
                {
                    "title": "Soccer Overview",
                    "layout_id": "OneColumn",
                    "zone_content": {
                        "body": "Soccer is played globally."
                    }
                }
            ]
        })
        
        self.assertEqual(response.status_code, 200)
        # Verify build_pptx was called with tone="Neumorphism"
        mock_build_pptx.assert_called_once()
        self.assertEqual(mock_build_pptx.call_args[1].get("tone"), "Neumorphism")

if __name__ == "__main__":
    unittest.main()
