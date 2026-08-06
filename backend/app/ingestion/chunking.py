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

def chunk_document(text: str, source_file: str, company: str, chunk_size: int = 400, overlap: int = 60) -> list[dict]:
    sections = split_by_section(text)
    # split_by_section only recognises SEC "Item N." headers. Arbitrary user
    # uploads have none, so treat the whole document as a single section rather
    # than returning zero chunks.
    if not sections:
        sections = [{"section": "Document", "text": text}]

    all_chunks = []
    
    for section in sections:
        sub_chunks = chunk_section(section["text"], chunk_size=chunk_size, overlap=overlap)
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
