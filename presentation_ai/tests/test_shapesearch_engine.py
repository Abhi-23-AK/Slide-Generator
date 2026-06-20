#!/usr/bin/env python3
"""
Unit tests for shapesearch_engine.py
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.architecture_v4.shapesearch_engine import (
    soundex,
    split_compound,
    normalize_query,
    search_shapes,
    search_multiple_shapes
)

class TestShapeSearchEngine(unittest.TestCase):
    def test_split_compound(self):
        self.assertEqual(split_compound("gpt4Model"), ["gpt", "4", "model"])
        self.assertEqual(split_compound("PascalCase"), ["pascal", "case"])
        self.assertEqual(split_compound("snake_case_123"), ["snake", "case", "123"])
        self.assertEqual(split_compound("kebab-case-test"), ["kebab", "case", "test"])
        
    def test_normalize_query(self):
        self.assertEqual(normalize_query("postgres db"), "postgresql")
        self.assertEqual(normalize_query("sql database"), "postgresql")
        self.assertEqual(normalize_query("aws lambda function"), "lambda")
        self.assertEqual(normalize_query("vector store"), "pinecone")
        
    def test_soundex(self):
        self.assertEqual(soundex("postgresql"), soundex("postgres"))
        self.assertEqual(soundex("lambda"), soundex("lambdas"))
        
    def test_search_shapes_basic(self):
        # Test basic shape search (which should load the database successfully)
        res = search_shapes("aws lambda", limit=3, theme="aws")
        self.assertTrue(len(res) > 0)
        first = res[0]
        self.assertIn("style", first)
        self.assertIn("confidence", first)
        self.assertIn("aspect_ratio", first)
        self.assertGreaterEqual(first["confidence"], 0.0)
        
    def test_theme_priority_reward(self):
        # AWS theme should rank an AWS shape above an Azure shape for postgresql
        aws_res = search_shapes("postgresql", theme="aws")
        aws_libraries = [r["library"] for r in aws_res]
        self.assertIn("aws", aws_libraries)
        
        # Azure theme should rank Azure shape higher
        azure_res = search_shapes("postgresql", theme="azure")
        azure_libraries = [r["library"] for r in azure_res]
        self.assertIn("azure", azure_libraries)
        
        first_aws_idx_in_aws = aws_libraries.index("aws") if "aws" in aws_libraries else 99
        first_azure_idx_in_aws = aws_libraries.index("azure") if "azure" in aws_libraries else 99
        self.assertLess(first_aws_idx_in_aws, first_azure_idx_in_aws)
        
        first_azure_idx_in_azure = azure_libraries.index("azure") if "azure" in azure_libraries else 99
        first_aws_idx_in_azure = azure_libraries.index("aws") if "aws" in azure_libraries else 99
        self.assertLess(first_azure_idx_in_azure, first_aws_idx_in_azure)
            
    def test_batch_search(self):
        queries = ["aws lambda", "postgresql", "redis"]
        results = search_multiple_shapes(queries, limit=2, theme="aws")
        self.assertEqual(set(results.keys()), set(queries))
        for q in queries:
            self.assertTrue(isinstance(results[q], list))

if __name__ == "__main__":
    unittest.main()
