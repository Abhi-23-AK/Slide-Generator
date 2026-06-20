#!/usr/bin/env python3
"""
Unit tests for drawio_xml_builder_v4.py
"""

import unittest
import sys
import os
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.architecture_v4.drawio_xml_builder_v4 import (
    scale_style_string,
    build_drawio_xml
)
import services.architecture_v4.style_engine_v4 as style_engine

class TestDrawioXmlBuilderV4(unittest.TestCase):
    def setUp(self):
        # Sample graph with pre-calculated absolute coords
        self.sample_graph = {
            "containers": [
                {"id": "layer_frontend", "label": "UI Layer", "parent": None, "layout": {"x": 10, "y": 10, "w": 300, "h": 200}}
            ],
            "nodes": [
                {"id": "gateway", "label": "API Gateway", "type": "gateway", "parent": "layer_frontend", "layout": {"x": 20, "y": 30, "w": 160, "h": 80}},
                {"id": "db_node", "label": "User DB", "type": "database", "parent": "layer_frontend", "layout": {"x": 190, "y": 30, "w": 100, "h": 80}}
            ],
            "edges": [
                {"source": "gateway", "target": "db_node", "label": "reads", "waypoints": [(50, 60), (100, 60)]}
            ],
            "_absolute_coords": {
                "nodes": {
                    "gateway": {"x": 30, "y": 40, "w": 160, "h": 80},
                    "db_node": {"x": 200, "y": 40, "w": 100, "h": 80}
                },
                "containers": {
                    "layer_frontend": {"x": 10, "y": 10, "w": 300, "h": 200}
                }
            }
        }

    def test_scale_style_string_with_dashpattern(self):
        style = "strokeWidth=2;dashPattern=8 4;fontSize=12;"
        scaled_1 = scale_style_string(style, 1.0)
        self.assertIn("strokeWidth=2", scaled_1)
        self.assertIn("dashPattern=8 4", scaled_1)
        self.assertIn("fontSize=12", scaled_1)

        scaled_2 = scale_style_string(style, 2.0)
        self.assertIn("strokeWidth=4", scaled_2)
        self.assertIn("dashPattern=16 8", scaled_2)
        self.assertIn("fontSize=24", scaled_2)

    def test_build_drawio_xml_well_formed(self):
        style_engine.set_current_style("classic")
        xml_str = build_drawio_xml(self.sample_graph)
        
        # Should be a well-formed XML document
        try:
            root = ET.fromstring(xml_str)
            self.assertEqual(root.tag, "mxfile")
            
            # Check diagram elements
            diagram = root.find("diagram")
            self.assertIsNotNone(diagram)
            
            graph_model = diagram.find("mxGraphModel")
            self.assertIsNotNone(graph_model)
            
            mxroot = graph_model.find("root")
            self.assertIsNotNone(mxroot)
            
            cells = mxroot.findall("mxCell")
            self.assertTrue(len(cells) >= 5)  # 0, 1, container, 2 nodes, edge, plus dummy nodes
        except ET.ParseError as e:
            self.fail(f"XML parsing failed: {e}\nXML string:\n{xml_str}")

    def test_aspect_ratio_padding_added(self):
        # We no longer add dummy padding cells (Problem 1)
        # Bounding box width is 300, height is 200
        style_engine.set_current_style("classic")
        xml_str = build_drawio_xml(self.sample_graph)
        
        self.assertNotIn("dummy_left_", xml_str)
        self.assertNotIn("dummy_right_", xml_str)
        self.assertNotIn("dummy_top_", xml_str)
        self.assertNotIn("dummy_bottom_", xml_str)
        
        # Verify dynamic canvas aspect ratio is exactly 1.875
        root = ET.fromstring(xml_str)
        model = root.find(".//mxGraphModel")
        self.assertIsNotNone(model)
        pw = float(model.get("pageWidth", 0))
        ph = float(model.get("pageHeight", 0))
        self.assertAlmostEqual(pw / ph, 1.875, places=3)

    def test_image_node_font_color_neon_theme(self):
        # Mocking resolve_node_visuals to return use_image = True
        # Let's verify that the neon theme sets white/neon text colors rather than #000000
        style_engine.set_current_style("ai_dark_neon")
        
        # DB category under dark neon has white text/accent
        xml_str = build_drawio_xml(self.sample_graph)
        
        # Check standard palette colors for dark neon
        # Let's inspect the style of cells
        root = ET.fromstring(xml_str)
        cells = root.findall(".//mxCell")
        
        found_db_node = False
        for cell in cells:
            if cell.get("id") == "db_node":
                style = cell.get("style", "")
                self.assertIn("fontColor=#ffffff", style)
                found_db_node = True
                
        self.assertTrue(found_db_node)

    def test_native_shape_sizing_preserved(self):
        style_engine.set_current_style("classic")
        xml_str = build_drawio_xml(self.sample_graph)
        
        root = ET.fromstring(xml_str)
        cells = root.findall(".//mxCell")
        
        found_gateway = False
        for cell in cells:
            if cell.get("id") == "gateway":
                # Check geometry
                geom = cell.find("mxGeometry")
                self.assertIsNotNone(geom)
                # Sizing from layout should be preserved (width=160, height=80)
                self.assertEqual(geom.get("width"), "160")
                self.assertEqual(geom.get("height"), "80")
                found_gateway = True
                
        self.assertTrue(found_gateway)

if __name__ == "__main__":
    unittest.main()
