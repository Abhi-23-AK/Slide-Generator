import unittest
from api.routes import _build_local_agent_edit

class TestAgentLocalEdit(unittest.TestCase):
    def setUp(self):
        self.mock_slide = {
            "id": "slide-123",
            "title": "Old Title",
            "background": "#ffffff",
            "layout_id": "OneColumn",
            "zone_content": {},
            "elements": []
        }

    def test_direct_color_matches(self):
        # Direct color name
        result = _build_local_agent_edit(self.mock_slide, "red")
        self.assertIsNotNone(result)
        self.assertEqual(result["changes"]["background"], "#ef4444")
        self.assertEqual(result["message"], "Updated the background color.")

        # "make it green"
        result2 = _build_local_agent_edit(self.mock_slide, "make it green")
        self.assertIsNotNone(result2)
        self.assertEqual(result2["changes"]["background"], "#22c55e")

        # Color with punctuation
        result3 = _build_local_agent_edit(self.mock_slide, "change background to blue.")
        self.assertIsNotNone(result3)
        self.assertEqual(result3["changes"]["background"], "#2563eb")

    def test_direct_layout_matches(self):
        # Direct layout name
        result = _build_local_agent_edit(self.mock_slide, "timeline")
        self.assertIsNotNone(result)
        self.assertEqual(result["changes"]["layout_id"], "Timeline")
        self.assertEqual(result["message"], "Changed layout to Timeline.")

        # Layout name with punctuation / trailing text
        result2 = _build_local_agent_edit(self.mock_slide, "timeline layout")
        self.assertIsNotNone(result2)
        self.assertEqual(result2["changes"]["layout_id"], "Timeline")

        # "make it a timeline"
        result3 = _build_local_agent_edit(self.mock_slide, "make it a timeline")
        self.assertIsNotNone(result3)
        self.assertEqual(result3["changes"]["layout_id"], "Timeline")

    def test_formatting_robustness(self):
        # Font size increase
        result = _build_local_agent_edit(self.mock_slide, "increase font size")
        self.assertIsNotNone(result)
        self.assertIn("zone_styles", result["changes"])

        # Font size set
        result2 = _build_local_agent_edit(self.mock_slide, "set size to 24px")
        self.assertIsNotNone(result2)
        self.assertIn("zone_styles", result2["changes"])

if __name__ == "__main__":
    unittest.main()
