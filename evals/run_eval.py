import json
from backend.app.retrieval.search import search_chunks as hybrid_search

LEGACY_SEC_CORPUS = "legacy_sec_corpus"


def normalize(s: str) -> str:
    return s.replace("\u2019", "'").replace("\xa0", " ").strip()


def first_correct_rank(retrieved_sections, acceptable):
    """Returns 1-based position of the first correct section, or None."""
    for position, section in enumerate(retrieved_sections, start=1):
        if section in acceptable:
            return position
    return None


def run_eval(dataset_path: str, top_k: int = 5, document_set_id: str = LEGACY_SEC_CORPUS):
    with open(dataset_path, encoding="utf-8") as f:
        questions = [json.loads(line) for line in f]

    passed = 0
    reciprocal_ranks = []
    results = []

    for q in questions:
        retrieved = hybrid_search(q["question"], document_set_id, top_k=top_k)

        acceptable = [normalize(s) for s in q["acceptable_sections"]]
        retrieved_sections = [normalize(r["section"]) for r in retrieved]

        rank = first_correct_rank(retrieved_sections, acceptable)

        # pass/fail (unchanged headline metric)
        hit = rank is not None
        if hit:
            passed += 1

        # reciprocal rank for MRR
        rr = (1 / rank) if rank is not None else 0.0
        reciprocal_ranks.append(rr)

        results.append({
            "id": q["id"],
            "question": q["question"],
            "hit": hit,
            "rank": rank,
            "rr": rr
        })

    # Per-question breakdown
    print(f"\n{'='*70}")
    print(f"RETRIEVAL EVAL — top_k={top_k}")
    print(f"{'='*70}")
    for r in results:
        status = "PASS" if r["hit"] else "FAIL"
        rank_str = f"rank {r['rank']}" if r["rank"] else "not found"
        print(f"[{status}] {r['id']}: {rank_str} (rr={r['rr']:.3f}) | {r['question'][:45]}")

    # Summary metrics
    pass_rate = passed / len(questions) * 100
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)

    print(f"\n{'='*70}")
    print(f"PASS RATE: {passed}/{len(questions)} ({pass_rate:.1f}%) — acceptable section in top-{top_k}")
    print(f"MRR:       {mrr:.4f} — mean reciprocal rank of first correct section")
    print(f"{'='*70}")

    return results


if __name__ == "__main__":
    run_eval("backend/app/evals/dataset/regression_set.jsonl", top_k=5)