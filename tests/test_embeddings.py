import pytest
from app.retrieval.embeddings import EmbeddingWrapper

@pytest.mark.asyncio
async def test_embedding_wrapper_single_query():
    embedder = EmbeddingWrapper(model_name="all-MiniLM-L6-v2")
    query = "Total research and development expense was $4.5 billion in 2013."
    vector = await embedder.embed_query(query)
    
    assert isinstance(vector, list)
    assert len(vector) == 384
    assert isinstance(vector[0], float)

@pytest.mark.asyncio
async def test_embedding_wrapper_batch_documents():
    embedder = EmbeddingWrapper(model_name="all-MiniLM-L6-v2")
    texts = [
        "First document text snippet.",
        "Second document text snippet."
    ]
    vectors = await embedder.embed_documents(texts)
    
    assert isinstance(vectors, list)
    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    assert len(vectors[1]) == 384
