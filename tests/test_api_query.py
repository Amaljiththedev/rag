import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

import unittest

class TestAPIQuery(unittest.TestCase):
    def test_query_schema(self):
        try:
            from app.schemas.query import QueryRequest
            req = QueryRequest(question="What is RAG?")
            self.assertEqual(req.question, "What is RAG?")
        except ImportError:
            self.skipTest("pydantic dependency not installed in local environment")

if __name__ == "__main__":
    unittest.main()
