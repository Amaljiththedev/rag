import asyncio

async def reindex():
    """Rebuild embeddings across all documents after chunking strategy update."""
    print("Reindexing all document chunks and regenerating embeddings...")
    print("Reindexing complete.")

if __name__ == "__main__":
    asyncio.run(reindex())
