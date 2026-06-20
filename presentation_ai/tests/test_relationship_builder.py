#!/usr/bin/env python3
"""
Unit tests for relationship_builder.py
"""

import unittest
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.architecture_v4.relationship_builder import (
    detect_hub_node,
    find_semantic_matches,
    get_semantic_label,
    score_edge,
    prune_and_control_edges,
    build_relationships
)

class TestRelationshipBuilder(unittest.TestCase):
    def setUp(self):
        self.sample_components = [
            {"name": "Auth Service", "kind": "service", "tier": "backend", "importance": "high", "flow_order": 2, "parent": "App Layer", "group": "Logic", "cluster_id": "microservices_cluster"},
            {"name": "Auth Database", "kind": "database", "tier": "data", "importance": "high", "flow_order": 3, "parent": "Data Layer", "group": "Data", "cluster_id": "microservices_cluster"},
            {"name": "Order Service", "kind": "service", "tier": "backend", "importance": "critical", "flow_order": 2, "parent": "App Layer", "group": "Logic", "cluster_id": "microservices_cluster"},
            {"name": "Order Database", "kind": "database", "tier": "data", "importance": "critical", "flow_order": 3, "parent": "Data Layer", "group": "Data", "cluster_id": "microservices_cluster"},
            {"name": "API Gateway", "kind": "gateway", "tier": "frontend", "importance": "critical", "flow_order": 1, "parent": "Ingress", "group": "Ingress", "cluster_id": "microservices_cluster"},
            {"name": "Monitoring Stack", "kind": "monitoring", "tier": "infra", "importance": "low", "flow_order": 4, "parent": "Infra", "group": "Ops", "cluster_id": "microservices_cluster"}
        ]

    def test_detect_hub_node(self):
        hub = detect_hub_node(self.sample_components)
        # Gateway has kind='gateway' and should be the hub
        self.assertEqual(hub["name"], "API Gateway")

    def test_find_semantic_matches(self):
        auth_service = self.sample_components[0]
        matches = find_semantic_matches(auth_service, self.sample_components)
        matched_names = [m["name"] for m in matches]
        # Auth Database should be the top match
        self.assertIn("Auth Database", matched_names)
        self.assertEqual(matched_names[0], "Auth Database")
        
        order_service = self.sample_components[2]
        order_matches = find_semantic_matches(order_service, self.sample_components)
        order_matched_names = [m["name"] for m in order_matches]
        self.assertIn("Order Database", order_matched_names)
        self.assertEqual(order_matched_names[0], "Order Database")

    def test_get_semantic_label(self):
        auth_service = self.sample_components[0]
        auth_db = self.sample_components[1]
        lbl = get_semantic_label(auth_service, auth_db, "microservices")
        self.assertEqual(lbl, "Authenticate")

    def test_score_edge(self):
        edge = {"source": "Auth Service", "target": "Auth Database", "importance": "high"}
        score = score_edge(edge, self.sample_components, "microservices")
        # Direct word match (auth / auth), same cluster, flow diff 1 -> should be quite high
        self.assertTrue(score > 5.0)

    def test_prune_and_control_edges(self):
        edges = [
            {"source": "API Gateway", "target": "Auth Service", "label": "Route"},
            {"source": "API Gateway", "target": "Order Service", "label": "Route"},
            {"source": "Auth Service", "target": "Auth Database", "label": "Query"},
            {"source": "Order Service", "target": "Order Database", "label": "Query"},
            {"source": "Auth Database", "target": "API Gateway", "label": "BackEdge"}, # cycle
        ]
        
        # In a microservices topology (which allows some feedback), let's check enrichment
        processed = prune_and_control_edges(edges, self.sample_components, "microservices")
        self.assertTrue(len(processed) > 0)
        
        # Check layout attributes
        back_edges = [e for e in processed if e["source"] == "Auth Database" and e["target"] == "API Gateway"]
        if back_edges:
            self.assertTrue(back_edges[0]["back_edge"])
            
        # In an acyclic topology (like CNN), back edges must be pruned
        processed_cnn = prune_and_control_edges(edges, self.sample_components, "cnn")
        back_edges_cnn = [e for e in processed_cnn if e["source"] == "Auth Database"]
        self.assertEqual(len(back_edges_cnn), 0)

    def test_build_relationships_fallback(self):
        # We test that the fallback relationship builder generates proper edges and applies limits
        edges = build_relationships(self.sample_components, "test topic without LLM", topology="microservices")
        self.assertTrue(len(edges) > 0)
        for e in edges:
            self.assertIn("source", e)
            self.assertIn("target", e)
            self.assertIn("label", e)
            self.assertIn("same_rank", e)
            self.assertIn("cross_cluster", e)

if __name__ == "__main__":
    unittest.main()
