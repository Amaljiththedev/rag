import psycopg2
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_text(text: str) -> list[float]:
    return model.encode(text).tolist()

def search_chunks(query: str, top_k: int = 5) -> list[dict]:
    """
    Embeds a query and returns the top_k most similar chunks from Postgres.
    """
    query_embedding = embed_text(query)
    
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="rag_db",
        user="rag_user",
        password="rag_password"
    )
    cur = conn.cursor()
    
    cur.execute("""
        SELECT chunk_id, section, content, embedding <=> %s::vector AS distance
        FROM chunks
        ORDER BY distance
        LIMIT %s;
    """, (str(query_embedding), top_k))
    
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


if __name__ == "__main__":
    query = "What was Apple's research and development expense in 2013?"
    results = search_chunks(query, top_k=3)
    
    print(f"Query: {query}\n")
    for i, r in enumerate(results):
        print(f"--- Result {i+1} (distance: {r['distance']:.4f}) ---")
        print(f"Section: {r['section']}")
        print(f"Content preview: {r['content'][:200]}...\n")
