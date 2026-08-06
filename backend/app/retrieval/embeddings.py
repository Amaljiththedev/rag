import json
from typing import List, Optional, Dict, Any
from sentence_transformers import SentenceTransformer
from app.ingestion.chunking import chunk_document
from app.config import settings

# Default model name
DEFAULT_MODEL_NAME = getattr(settings, "EMBEDDING_MODEL", "all-MiniLM-L6-v2")
if not DEFAULT_MODEL_NAME or DEFAULT_MODEL_NAME.startswith("text-embedding"):
    DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"

# Singleton model cache to avoid re-instantiating model weights
_MODEL_CACHE: Dict[str, SentenceTransformer] = {}


def get_model(model_name: str = DEFAULT_MODEL_NAME) -> SentenceTransformer:
    if model_name not in _MODEL_CACHE:
        _MODEL_CACHE[model_name] = SentenceTransformer(model_name)
    return _MODEL_CACHE[model_name]


# Module-level model reference
model = get_model(DEFAULT_MODEL_NAME)


def embed_text(text: str) -> List[float]:
    """Converts a piece of text into a vector representing its meaning."""
    vector = model.encode(text)
    return vector.tolist()


def embed_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Adds an 'embedding' field to each chunk dict, based on its 'text' field."""
    total = len(chunks)
    for i, chunk in enumerate(chunks):
        chunk["embedding"] = embed_text(chunk["text"])
        if (i + 1) % 20 == 0 or (i + 1) == total:
            print(f"Embedded {i + 1}/{total} chunks...")
    return chunks


class EmbeddingWrapper:
    """Embedding model wrapper using SentenceTransformer (default: all-MiniLM-L6-v2, dim 384)."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or DEFAULT_MODEL_NAME
        self.model = get_model(self.model_name)
        if hasattr(self.model, "get_embedding_dimension"):
            self.embedding_dim = self.model.get_embedding_dimension()
        else:
            self.embedding_dim = self.model.get_sentence_embedding_dimension()

    async def embed_query(self, query: str) -> List[float]:
        """Convert a search query into an embedding vector."""
        if not query or not query.strip():
            return [0.0] * self.embedding_dim
        vector = self.model.encode(query)
        return vector.tolist()

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Convert a list of text chunks into embedding vectors."""
        if not texts:
            return []
        vectors = self.model.encode(texts)
        if hasattr(vectors, "tolist"):
            return vectors.tolist()
        return [v.tolist() if hasattr(v, "tolist") else list(v) for v in vectors]


if __name__ == "__main__":
    with open("data/sec_filings/apple_10k_2013.txt", encoding="utf-8") as f:
        text = f.read()

    # Step 1: build chunks using chunk_document
    chunks = chunk_document(text, source_file="apple_10k_2013.txt", company="Apple Inc.", chunk_size=400, overlap=60)
    print(f"Total chunks to embed: {len(chunks)}")

    # Step 2: embed all of them
    chunks = embed_chunks(chunks)

    # Step 3: verify — print details for the first chunk
    print("\n--- Sample chunk after embedding ---")
    print(f"chunk_id: {chunks[0]['chunk_id']}")
    print(f"section: {chunks[0]['section']}")
    print(f"embedding length: {len(chunks[0]['embedding'])}")
    print(f"first 5 numbers: {chunks[0]['embedding'][:5]}")

    # Step 4: save to local JSON file
    output_path = "data/embedded_chunks.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f)
    print(f"\nSaved {len(chunks)} embedded chunks to {output_path}")