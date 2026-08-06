# RAG Retrieval Evaluation Results

**Date:** 2026-08-06  
**Model:** `all-MiniLM-L6-v2` (dense vector search)  
**Dataset:** `evals/dataset/regression_set.jsonl` (10 questions, Apple 10-K 2013)  
**Method:** Pure cosine-similarity retrieval (`embedding <=> query`) — no hybrid/reranking  
**top_k:** 5  

---

## Summary

| Metric | Value |
|--------|-------|
| **Score** | **9 / 10 (90.0%)** |
| Questions Passed | 9 |
| Questions Failed | 1 |

> **Criterion:** At least one of the top-5 retrieved chunks must come from an *acceptable section* for that question.

---

## Per-Question Results

| ID | Question | Status | Retrieved Sections |
|----|----------|--------|--------------------|
| q001 | What was Apple's total R&D expense in 2013? | ✅ PASS | Item 7, Item 8 |
| q002 | How many full-time employees did Apple have (Sep 2013)? | ✅ PASS | Item 1 |
| q003 | What was Apple's total net sales in FY2013? | ✅ PASS | Item 6, Item 7, Item 8 |
| q004 | What operating segments does Apple report? | ✅ PASS | Item 1 |
| q005 | In which country did Apple own a manufacturing facility? | ❌ FAIL | Item 1, Item 7, Item 8 |
| q006 | Outcome of the Apple eBooks antitrust case? | ✅ PASS | Item 3 |
| q007 | What was Apple's net income in FY2013? | ✅ PASS | Item 6, Item 7, Item 8 |
| q008 | Why is Apple exposed to supply/pricing risks? | ✅ PASS | Item 1A |
| q009 | On what stock exchange is Apple traded & under what symbol? | ✅ PASS | Item 5 |
| q010 | How much did Apple pay in dividends in FY2013? | ✅ PASS | Item 5, Item 7 |

---

## Failure Analysis

### q005 — Manufacturing facility in Ireland (Expected: Item 2. Properties)

- **Root cause:** "Ireland" and "Cork" appear in **6 different sections** (tax discussions, subsidiary listings, risk factors, etc.). The dense embedder surfaces the more semantically-general mentions (Item 1, Item 7, Item 8) before the specific Item 2. Properties chunk.
- **Why it's hard:** The question asks about a *manufacturing facility*, which is a narrow fact buried in a short Item 2 chunk. Dense search matches the *country name* broadly rather than the *facility-specific* context.
- **Potential fixes:**
  1. **Hybrid search (BM25 + dense):** Keyword match on "manufacturing" + "facility" would boost the Item 2 chunk.
  2. **Reranking:** A cross-encoder reranker on top-20 candidates could re-score for the specific manufacturing context.
  3. **Increase top_k:** At top_k=10 or 20, Item 2 may appear but at lower rank.

---

## Bug Fix Applied This Run

### Apostrophe normalization (60% → 90%)

The initial run scored **6/10 (60%)** due to a string-matching bug: section names in PostgreSQL contained Unicode curly apostrophes (`'`, U+2019), while the JSONL dataset used straight apostrophes (`'`, U+0027). This caused false FAILs on q001, q009, and q010.

**Fix:** Added a `normalize()` function in `run_eval.py`:
```python
def normalize(s: str) -> str:
    return s.replace("\u2019", "'").replace("\xa0", " ").strip()
```

| Run | Score | Notes |
|-----|-------|-------|
| Before fix | 6/10 (60%) | 3 false failures from apostrophe mismatch |
| After fix | 9/10 (90%) | Only genuine retrieval miss (q005) remains |

---

## Previous Run (Before Fix)

| ID | Status | Notes |
|----|--------|-------|
| q001 | ❌ FAIL (false) | Apostrophe mismatch in "Management's Discussion..." |
| q002 | ✅ PASS | — |
| q003 | ✅ PASS | — |
| q004 | ✅ PASS | — |
| q005 | ❌ FAIL | Genuine miss — Item 2 not retrieved |
| q006 | ✅ PASS | — |
| q007 | ✅ PASS | — |
| q008 | ✅ PASS | — |
| q009 | ❌ FAIL (false) | Apostrophe mismatch in "Registrant's Common Equity..." |
| q010 | ❌ FAIL (false) | Apostrophe mismatch in "Management's Discussion..." |

---

## Next Steps

1. **Implement hybrid search** (BM25 + dense with RRF fusion) to fix q005
2. **Add a cross-encoder reranker** for precision on ambiguous queries
3. **Expand dataset** beyond 10 questions for more robust evaluation
4. **Track results over time** — re-run after each retrieval change and append to this file
