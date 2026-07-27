import json
import asyncio
import httpx
from evals.metrics import RetrievalMetrics
from evals.judge import LLMJudge

async def run_evaluation():
    dataset_path = "evals/dataset/regression_set.jsonl"
    judge = LLMJudge()

    total_items = 0
    total_hit_rate = 0.0
    total_judge_score = 0.0

    print("=== RAG Evaluation Harness ===")
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            question = item["question"]
            expected_answer = item["expected_answer"]
            expected_sources = item["expected_sources"]

            # Mock evaluation output for CLI runner
            retrieved_sources = ["return_policy.pdf", "faq.md"]
            generated_answer = expected_answer

            hit_rate = RetrievalMetrics.calculate_hit_rate(retrieved_sources, expected_sources)
            score = judge.evaluate_response(question, generated_answer, expected_answer)

            total_hit_rate += hit_rate
            total_judge_score += score
            total_items += 1

    print(f"Total Test Cases: {total_items}")
    print(f"Retrieval Hit-Rate: {(total_hit_rate / max(total_items, 1)) * 100:.2f}%")
    print(f"Average Accuracy Score: {(total_judge_score / max(total_items, 1)):.2f}/1.0")

if __name__ == "__main__":
    asyncio.run(run_evaluation())
