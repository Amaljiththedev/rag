from typing import Dict, Any, List
import re

def split_by_section(text: str) -> list[dict]:
    """
    Splits raw filing text into sections based on 'Item N.' headers.
    Returns a list of {"section": "Item 1A. Risk Factors", "text": "..."}
    """
    text = text.replace('\xa0', ' ')
    
    # Strip initial Table of Contents summary block by finding main Item 1. Business
    intro_match = re.search(r'\nItem\s+1\.\s+Business\s*\n\s*[A-Za-z]', text[300:], re.IGNORECASE)
    if intro_match:
        text = text[300 + intro_match.start():]

    # Matches things like "Item 1.", "Item 1A.", "Item 10." at line start/newline
    pattern = r"(?:^|\n)(Item\s+\d+[A-Z]?\.\s*[^\n]*)"
    
    parts = re.split(pattern, text)
    
    sections = []
    for i in range(1, len(parts), 2):
        header = re.sub(r'\s+', ' ', parts[i]).strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if body.strip():
            sections.append({"section": header, "text": body.strip()})
    
    return sections

def chunk_section(section_text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Splits a section's text into overlapping chunks, roughly chunk_size words each.
    Tries not to cut mid-sentence.
    """
    words = section_text.split()
    if len(words) <= chunk_size:
        return [section_text]  # short enough, no need to split
    
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        start = end - overlap  # step back by overlap amount
    
    return chunks

def chunk_document(text: str, source_file: str, company: str) -> list[dict]:
    sections = split_by_section(text)
    all_chunks = []
    
    for section in sections:
        sub_chunks = chunk_section(section["text"], chunk_size=500, overlap=50)
        for i, chunk_text in enumerate(sub_chunks):
            all_chunks.append({
                "chunk_id": f"{source_file}__{section['section'][:20]}__{i:03d}",
                "source_file": source_file,
                "company": company,
                "section": section["section"],
                "chunk_index": i,
                "text": chunk_text
            })
    
    return all_chunks


class TextChunker:
    """Chunker class for ingestion pipeline compatibility."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split_documents(self, raw_docs: list[dict]) -> list[dict]:
        all_chunks = []
        for doc in raw_docs:
            source = doc.get("filename", "unknown")
            text = doc.get("text", "") or doc.get("content", "")
            chunks = chunk_document(text, source_file=source, company="Default")
            for idx, c in enumerate(chunks):
                all_chunks.append({
                    "chunk_index": idx,
                    "content": c["text"],
                    "metadata": {
                        "source_file": source,
                        "section": c["section"],
                        "chunk_id": c["chunk_id"]
                    }
                })
        return all_chunks


if __name__ == "__main__":
    with open("data/sec_filings/apple_10k_2013.txt", encoding="utf-8") as f:
        text = f.read()
    
    chunks = chunk_document(text, "apple_10k_2013.txt", "Apple Inc.")
    print(f"Total chunks: {len(chunks)}")
    for c in chunks[:3]:
        print(f"[{c['section']}] {c['text'][:100]}...")
    