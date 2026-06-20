#!/usr/bin/env python3
"""
Unit tests for graphviz_layout_v4.py
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.architecture_v4.graphviz_layout_v4 import (
    add_invisible_layout_edges,
    layout_graph,
    TOPOLOGY_LAYOUT_CONFIG
)

class TestGraphvizLayoutV4(unittest.TestCase):
    def setUp(self):
        self.sample_graph = {
            "containers": [
                {"id": "layer_frontend", "label": "UI Layer", "parent": None},
                {"id": "layer_backend", "label": "Services Layer", "parent": None}
            ],
            "nodes": [
                {"id": "gateway", "label": "API Gateway", "type": "gateway", "parent": "layer_frontend", "flow_order": 1, "rank_group": "ingress"},
                {"id": "service_a", "label": "Auth Service", "type": "service", "parent": "layer_backend", "flow_order": 2, "rank_group": "logic"},
                {"id": "service_b", "label": "Order Service", "type": "service", "parent": "layer_backend", "flow_order": 2, "rank_group": "logic"}
            ],
            "edges": [
                {"source": "gateway", "target": "service_a", "importance": "high", "local_edge": True},
                {"source": "gateway", "target": "service_b", "importance": "high", "local_edge": True}
            ]
        }

    def test_add_invisible_layout_edges(self):
        nodes = self.sample_graph["nodes"]
        edges = self.sample_graph["edges"]
        
        enriched_edges = add_invisible_layout_edges(nodes, edges)
        
        # Should have added invisible edges between consecutive flow_orders, rank_groups, etc.
        invis_edges = [e for e in enriched_edges if e.get("style") == "invis"]
        self.assertTrue(len(invis_edges) > 0)
        for ie in invis_edges:
            self.assertEqual(ie["constraint"], "true")
            self.assertEqual(ie["weight"], 20)

    def test_topology_layout_config(self):
        self.assertIn("microservices", TOPOLOGY_LAYOUT_CONFIG)
        self.assertIn("cnn", TOPOLOGY_LAYOUT_CONFIG)
        self.assertIn("ring", TOPOLOGY_LAYOUT_CONFIG)
        
        # Verify specific settings
        self.assertEqual(TOPOLOGY_LAYOUT_CONFIG["cnn"]["splines"], "polyline")
        self.assertEqual(TOPOLOGY_LAYOUT_CONFIG["ring"]["engine"], "circo")

    def test_layout_graph_basic(self):
        # Run a basic layout calculation using dot (since it's installed/mockable on system)
        try:
            result = layout_graph(self.sample_graph, "microservices")
            self.assertIn("_canvas", result)
            self.assertIn("w", result["_canvas"])
            self.assertIn("h", result["_canvas"])
            
            # Verify coordinates mapped
            for n in result["nodes"]:
                self.assertIn("layout", n)
                self.assertIn("x", n["layout"])
                self.assertIn("y", n["layout"])
                self.assertIn("w", n["layout"])
                
            for c in result["containers"]:
                self.assertIn("layout", c)
                self.assertIn("x", c["layout"])
                self.assertIn("y", c["layout"])
        except FileNotFoundError:
            # Graphviz might not be installed in the test environment, skip execution check
            pass

if __name__ == "__main__":
    unittest.main()
