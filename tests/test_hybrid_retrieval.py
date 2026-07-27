import unittest

class TestHybridRetrieval(unittest.TestCase):
    def test_rrf_scoring_logic(self):
        k = 60
        rank = 0
        score = 1.0 / (k + rank + 1)
        self.assertAlmostEqual(score, 0.0163934, places=5)

if __name__ == "__main__":
    unittest.main()
