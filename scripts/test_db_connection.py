import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="rag_db",
    user="rag_user",
    password="rag_password"
)

cur = conn.cursor()
cur.execute("SELECT version();")
print("PostgreSQL Version:")
print(cur.fetchone()[0])

cur.execute("SELECT extname, extversion FROM pg_extension;")
print("\nInstalled Extensions:")
for extname, extversion in cur.fetchall():
    print(f"- {extname}: v{extversion}")

cur.close()
conn.close()
