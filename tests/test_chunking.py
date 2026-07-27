import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

import unittest

class TestChunking(unittest.TestCase):
    def test_chunking_config(self):
        try:
            from app.config import settings
            self.assertEqual(settings.CHUNK_SIZE, 1000)
        except ImportError:
            self.skipTest("pydantic_settings dependency not installed in local environment")

if __name__ == "__main__":
    unittest.main()
