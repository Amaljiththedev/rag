from typing import List

class RetrievalMetrics:
    """Calculates retrieval precision, recall, and hit-rate."""

    @staticmethod
    def calculate_hit_rate(retrieved_sources: List[str], expected_sources: List[str]) -> float:
        if not expected_sources:
            return 1.0
        hits = any(exp in src for exp in expected_sources for src in retrieved_sources)
        return 1.0 if hits else 0.0

    @staticmethod
    def calculate_precision(retrieved_sources: List[str], expected_sources: List[str]) -> float:
        if not retrieved_sources:
            return 0.0
        relevant = sum(1 for src in retrieved_sources if any(exp in src for exp in expected_sources))
        return relevant / len(retrieved_sources)
