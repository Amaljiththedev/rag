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

if __name__ == "__main__":
    with open("data/sec_filings/apple_10k_2013.txt", encoding="utf-8") as f:
        text = f.read()
    sections = split_by_section(text)
    # item8_sections = [s for s in sections if s["section"].startswith("Item 8") and len(s["text"]) > 100]
    # item8_chunks = chunk_section(item8_sections[0]["text"], chunk_size=400, overlap=60)
    # for i, chk in enumerate(item8_chunks):
    #     print(f"Chunk {i+1}: {len(chk.split())} words")
    chunks = []

    for sec in sections:
        sec_chunks = chunk_section(sec["text"], chunk_size=400, overlap=60)
        for i, chk in enumerate(sec_chunks):
            chunks.append({
                "chunk_id": f"apple_10k_2013__{sec['section'][:15]}__{i:03d}",
                "section": sec["section"],
                "chunk_index": i,
                "content": chk,
                "metadata": {
                    "filename": "apple_10k_2013.txt",
                    "source_file": "apple_10k_2013.txt",
                    "file_type": "txt"
                }
            })
    
    print(f"Total Chunks Generated: {len(chunks)}")
    print("=" * 60)
    substantial_chunks = [c for c in chunks if len(c['content'].split()) > 10]
    for chk in substantial_chunks[:5]:
        print(f"ID      : {chk['chunk_id']}")
        print(f"Section : {chk['section']}")
        print(f"Index   : {chk['chunk_index']}")
        print(f"Words   : {len(chk['content'].split())}")
        print(f"Preview : {chk['content'][:150]}...")
        print("-" * 60)

    item1a_chunks = [c for c in chunks if c["section"]   == "Item 1A. Risk Factors"]
    print(f"Item 1A chunks found: {len(item1a_chunks)}")
    print(f"First Item 1A chunk word count: {len(item1a_chunks[0]['content'].split())}")

    # also print all unique section names to eyeball for duplicates/junk
    unique_sections = sorted(set(c["section"] for c in chunks))
    print(f"\nUnique sections ({len(unique_sections)}):")
    for s in unique_sections:
        print(f"  {s}")