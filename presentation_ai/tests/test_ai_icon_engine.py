import unittest
from services.architecture_v4.ai_icon_engine import get_ai_icon

class TestAIIconEngine(unittest.TestCase):
    def test_semantic_resolution_queries(self):
        cases = [
            ("postgres db", "postgresql"),
            ("redis cache", "redis"),
            ("vector database", "pinecone"),
            ("large language model", "openai"),
            ("embedding model", "openai"),
            ("react frontend", "react"),
            ("chrome extension", "chrome"),
            ("spring boot", "spring"),
            ("rag pipeline", "openai"),
            ("aws serverless", "aws"),
            ("kubernetes cluster", "kubernetes")
        ]
        
        for query, expected_brand in cases:
            with self.subTest(query=query):
                res = get_ai_icon(query)
                self.assertIsNotNone(res, f"Query '{query}' failed to resolve.")
                self.assertEqual(
                    res["brand"].lower(), 
                    expected_brand.lower(), 
                    f"Query '{query}' resolved to brand '{res['brand']}', expected '{expected_brand}'"
                )
                self.assertIn("style", res)
                self.assertIn("w", res)
                self.assertIn("h", res)
                self.assertIn("confidence", res)
                self.assertIn("source", res)
                self.assertGreaterEqual(res["confidence"], 65)

if __name__ == "__main__":
    unittest.main()
