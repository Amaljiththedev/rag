from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import settings

class TextChunker:
    """Chunking strategy using recursive character text splitting with overlap."""

    def __init__(self, chunk_size: int = settings.CHUNK_SIZE, chunk_overlap: int = settings.CHUNK_OVERLAP):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

    def split_documents(self, loaded_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        chunks = []
        chunk_idx = 0
        for doc in loaded_docs:
            sub_chunks = self.splitter.split_text(doc["content"])
            for text in sub_chunks:
                chunks.append({
                    "chunk_index": chunk_idx,
                    "content": text,
                    "metadata": {**doc["metadata"], "chunk_index": chunk_idx}
                })
                chunk_idx += 1
        return chunks
