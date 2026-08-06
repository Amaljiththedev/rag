import psycopg2
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_text(text: str) -> list[float]:
    return model.encode(text).tolist()

def main():
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="rag_db",
        user="rag_user",
        password="rag_password"
    )
    cur = conn.cursor()

    print("=== Step 1: Querying for chunks containing R&D terms ===")
    cur.execute("""
        SELECT chunk_id, section, LEFT(content, 120)
        FROM chunks
        WHERE content ILIKE '%research and development%'
           OR content ILIKE '%R&D%';
    """)
    rd_chunks = cur.fetchall()
    print(f"Found {len(rd_chunks)} chunks containing R&D terms:")
    rd_ids = set()
    for row in rd_chunks:
        print(f" - [{row[0]}] ({row[1]}): {row[2]}...")
        rd_ids.add(row[0])

    print("\n=== Step 2: Vector Search Top 20 for 'What was Apple\'s research and development expense in 2013?' ===")
    query = "What was Apple's research and development expense in 2013?"
    query_vector = embed_text(query)

    cur.execute("""
        SELECT chunk_id, section, content, embedding <=> %s::vector AS distance
        FROM chunks
        ORDER BY distance
        LIMIT 20;
    """, (str(query_vector),))

    results = cur.fetchall()
    found_ranks = []
    for rank, row in enumerate(results, start=1):
        cid, section, content, dist = row[0], row[1], row[2], row[3]
        is_match = " *** MATCHING R&D CHUNK ***" if cid in rd_ids else ""
        if cid in rd_ids:
            found_ranks.append((rank, cid, dist))
        print(f"Rank {rank:02d} | dist: {dist:.4f} | ID: {cid}{is_match}")
        print(f"        Section: {section}")
        print(f"        Content: {content[:120]}...\n")

    print("=== Diagnostic Summary ===")
    if found_ranks:
        for r, cid, dist in found_ranks:
            print(f"R&D Chunk {cid} was found at Rank {r} (distance: {dist:.4f})")
    else:
        print("None of the explicit R&D chunks appeared in the Top 20 results.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
