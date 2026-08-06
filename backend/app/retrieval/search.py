"""
Retrieval module for eval harness.
Wraps the search_chunks function from scripts/search_chunks.py so that
evals/run_eval.py can do: from backend.app.retrieval.search import search_chunks
"""
import psycopg2
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "rag_db",
    "user": "rag_user",
    "password": "rag_password",
}


def embed_text(text: str) -> list[float]:
    return model.encode(text).tolist()

STOPWORDS = {
    "what", "was", "were", "the", "did", "does", "how", "much", "many",
    "who", "when", "where", "which", "are", "and", "for", "its", "has",
    "have", "had", "with", "from", "that", "this", "you", "our"
}

def keyword_search(query: str, document_set_id: str, top_k: int = 10) -> list[dict]:
    if not document_set_id:
        raise ValueError("keyword_search requires a document_set_id — refusing to search across all sets.")

    import re
    words = re.findall(r'\b\w{3,}\b', query.lower())
    words = [w for w in words if w not in STOPWORDS]   # <-- drop stopwords
    if not words:
        return []

    ts_query = " | ".join(words)

    print(f"[debug] keyword terms: {ts_query}")

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT chunk_id, section, content,
               ts_rank(to_tsvector('english', content),
                       to_tsquery('english', %s)) AS rank
        FROM chunks
        WHERE document_set_id = %s
          AND to_tsvector('english', content) @@ to_tsquery('english', %s)
        ORDER BY rank DESC
        LIMIT %s;
    """, (ts_query, document_set_id, ts_query, top_k))

    results = []
    for row in cur.fetchall():
        results.append({
            "chunk_id": row[0],
            "section": row[1],
            "content": row[2],
            "keyword_rank": row[3]
        })
    cur.close()
    conn.close()
    return results


def search_chunks(query: str, document_set_id: str, top_k: int = 5) -> list[dict]:
    """
    Embeds a query and returns the top_k most similar chunks from Postgres,
    restricted to the given document set.
    """
    if not document_set_id:
        raise ValueError("search_chunks requires a document_set_id — refusing to search across all sets.")

    query_embedding = embed_text(query)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT chunk_id, section, content, embedding <=> %s::vector AS distance
        FROM chunks
        WHERE document_set_id = %s
        ORDER BY distance
        LIMIT %s;
    """, (str(query_embedding), document_set_id, top_k))

    results = []
    for row in cur.fetchall():
        results.append({
            "chunk_id": row[0],
            "section": row[1],
            "content": row[2],
            "distance": row[3]
        })

    cur.close()
    conn.close()
    return results


def reciprocal_rank_fusion(dense_results, keyword_results, k=60, top_k=5):
    """
    Combines two ranked lists using Reciprocal Rank Fusion.
    A chunk ranked highly by EITHER method gets boosted.
    """
    scores = {}      # chunk_id -> fused score
    chunk_data = {}  # chunk_id -> the chunk dict (so we can return full info)

    # Add dense results: position in list determines contribution
    for rank, chunk in enumerate(dense_results):
        cid = chunk["chunk_id"]
        scores[cid] = scores.get(cid, 0) + 1 / (k + rank)
        chunk_data[cid] = chunk

    # Add keyword results the same way
    for rank, chunk in enumerate(keyword_results):
        cid = chunk["chunk_id"]
        scores[cid] = scores.get(cid, 0) + 1 / (k + rank)
        chunk_data[cid] = chunk

    # Sort by fused score, highest first
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for cid, score in ranked[:top_k]:
        chunk = chunk_data[cid]
        chunk["rrf_score"] = score
        results.append(chunk)
    return results


def hybrid_search(query: str, document_set_id: str, top_k: int = 5) -> list[dict]:
    # document_set_id must reach BOTH sub-searches: if either one misses the
    # filter, chunks leak across sessions.
    if not document_set_id:
        raise ValueError("hybrid_search requires a document_set_id — refusing to search across all sets.")

    dense = search_chunks(query, document_set_id, top_k=20)
    keyword = keyword_search(query, document_set_id, top_k=20)
    return reciprocal_rank_fusion(dense, keyword, top_k=top_k)

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python search.py <document_set_id> [query]")
        sys.exit(1)

    document_set_id = sys.argv[1]
    query = sys.argv[2] if len(sys.argv) > 2 else "What was Apple's research and development expense in 2013?"

    print(f"\nQuery: {query}")
    print(f"Document set: {document_set_id}\n")
    print("=" * 70)
    print("DENSE SEARCH (top 5)")
    print("=" * 70)
    results = search_chunks(query, document_set_id, top_k=5)
    for i, r in enumerate(results):
        print(f"  [{i+1}] dist={r['distance']:.4f} | {r['chunk_id']}")
        print(f"       section: {r['section']}")
        print(f"       {r['content'][:120]}...")

    print()
    print("=" * 70)
    print("KEYWORD SEARCH (top 5)")
    print("=" * 70)
    kw_results = keyword_search(query, document_set_id, top_k=5)
    if kw_results:
        for i, r in enumerate(kw_results):
            print(f"  [{i+1}] rank={r['keyword_rank']:.4f} | {r['chunk_id']}")
            print(f"       section: {r['section']}")
            print(f"       {r['content'][:120]}...")
    else:
        print("  No keyword matches found.")

    print("\n" + "=" * 70)
    print("HYBRID SEARCH (RRF, top 5)")
    print("=" * 70)
    for i, r in enumerate(hybrid_search(query, document_set_id, top_k=5)):
        print(f"  [{i+1}] rrf={r['rrf_score']:.5f} | {r['chunk_id']}")
        print(f"       section: {r['section']}")
        print(f"       {r['content'][:120]}...")
