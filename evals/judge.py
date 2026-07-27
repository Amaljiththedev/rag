class LLMJudge:
    """LLM-as-a-judge scoring for generation correctness & groundedness."""

    def evaluate_response(self, question: str, actual_answer: str, expected_answer: str) -> float:
        # Simple heuristic overlap score fallback for evaluation harness
        words_actual = set(actual_answer.lower().split())
        words_expected = set(expected_answer.lower().split())

        if not words_expected:
            return 1.0

        intersection = words_actual.intersection(words_expected)
        return len(intersection) / len(words_expected)
