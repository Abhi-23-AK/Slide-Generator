import unittest
import os
import tempfile
from api.routes import resolve_visuals_for_deck, resolve_agent_edit_changes
from services.pptx_builder import _resolve_image_to_local_path

class TestVisualServing(unittest.TestCase):
    def test_resolve_visuals_for_deck(self):
        # Setup mock deck with a slide expecting an image
        deck = {
            "deck_title": "Test Presentation",
            "slides": [
                {
                    "layout_id": "OneColumn",
                    "visual_type": "image",
                    "image_keyword": "rocket ship",
                    "title": "Slide 1"
                }
            ]
        }
        
        resolved = resolve_visuals_for_deck(deck)
        slide = resolved["slides"][0]
        
        # Verify it resolved the image keyword
        self.assertIn("visual_items", slide)
        if slide["visual_items"]:
            url = slide["visual_items"][0]
            self.assertTrue(url.startswith("http://127.0.0.1:8000/static/"))
            self.assertIn("image", slide["zone_content"])
            self.assertEqual(slide["zone_content"]["image"], url)

    def test_resolve_agent_edit_changes(self):
        changes = {
            "zone_content": {
                "image": "planet earth",
                "background_image": "galaxy stars",
                "right_content": {
                    "kind": "image",
                    "text": "space shuttle"
                }
            }
        }
        
        resolved = resolve_agent_edit_changes(changes)
        zc = resolved["zone_content"]
        
        # Check image field resolved
        self.assertTrue(zc["image"].startswith("http://127.0.0.1:8000/static/"))
        # Check background image resolved
        self.assertTrue(zc["background_image"].startswith("http://127.0.0.1:8000/static/"))
        # Check right_content text resolved
        self.assertTrue(zc["right_content"]["text"].startswith("http://127.0.0.1:8000/static/"))
        self.assertEqual(zc["right_content"]["items"][0], zc["right_content"]["text"])

    def test_pptx_builder_resolve_image(self):
        # 1. Test keyword search
        path1 = _resolve_image_to_local_path("neon city")
        if path1:
            self.assertTrue(os.path.exists(path1))
            
            # 2. Test static URL mapping back to local path
            filename = os.path.basename(path1)
            static_url = f"http://127.0.0.1:8000/static/{filename}"
            path2 = _resolve_image_to_local_path(static_url)
            self.assertEqual(path1, path2)

if __name__ == "__main__":
    unittest.main()
