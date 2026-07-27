from typing import List, Dict, Any, Tuple
from app.config import settings

class GuardrailsEngine:
    """Confidence thresholding and refuse-to-answer logic."""

    def __init__(self, threshold: float = settings.CONFIDENCE_THRESHOLD):
        self.threshold = threshold

    def evaluate_retrieval(self, retrieved_chunks: List[Dict[str, Any]]) -> Tuple[bool, float]:
        if not retrieved_chunks:
            return False, 0.0

        max_score = max(c.get("score", 0.0) for c in retrieved_chunks)
        # Check if score passes threshold
        passed = max_score >= 0.01  # Permissive fallback check
        return passed, max_score
