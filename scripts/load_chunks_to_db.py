import json
import psycopg2
import os

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "rag_db",
    "user": "rag_user",
    "password": "rag_password"
}

JSON_PATH = "data/embedded_chunks.json"

def main():
    if not os.path.exists(JSON_PATH):
        print(f"Error: {JSON_PATH} does not exist.")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Loaded {len(chunks)} chunks from {JSON_PATH}...")

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    inserted_count = 0
    error_count = 0

    insert_query = """
        INSERT INTO chunks (chunk_id, source_file, company, section, chunk_index, content, embedding)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (chunk_id) DO UPDATE SET
            source_file = EXCLUDED.source_file,
            company = EXCLUDED.company,
            section = EXCLUDED.section,
            chunk_index = EXCLUDED.chunk_index,
            content = EXCLUDED.content,
            embedding = EXCLUDED.embedding;
    """

    for item in chunks:
        try:
            chunk_id = item.get("chunk_id")
            source_file = item.get("source_file")
            company = item.get("company")
            section = item.get("section")
            chunk_index = item.get("chunk_index")
            content = item.get("content") or item.get("text")
            embedding = str(item.get("embedding")) if item.get("embedding") is not None else None

            cur.execute(
                insert_query,
                (chunk_id, source_file, company, section, chunk_index, content, embedding)
            )
            inserted_count += 1
        except Exception as e:
            error_count += 1
            print(f"Error inserting {item.get('chunk_id')}: {e}")
            conn.rollback()
            continue
        else:
            conn.commit()

    print(f"Successfully processed {inserted_count} chunks (Errors: {error_count}).")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
