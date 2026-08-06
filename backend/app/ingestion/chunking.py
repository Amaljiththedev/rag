"""Page- and section-aware chunking.

Citations show a section name and a page number, so both must be tracked from
the source rather than reconstructed later. Chunks are built from (line, page)
pairs so every chunk knows exactly which pages it spans.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

Line = Tuple[str, int]  # (text, page number)

# Ordered by specificity. Each returns (label, rest-of-heading).
_NUMBERED = re.compile(r"^\s*(\d+(?:\.\d+){0,3})\.?\s+(\S.*)$")
_SECTION_WORD = re.compile(r"^\s*(Section|Article|Clause|Appendix|Schedule|Annex)\s+"
                           r"([A-Z0-9]+(?:\.\d+)*)\.?\s*(.*)$", re.IGNORECASE)
_SEC_ITEM = re.compile(r"^\s*(Item\s+\d+[A-Z]?\.)\s*(.*)$", re.IGNORECASE)
_MARKDOWN = re.compile(r"^\s*(#{1,4})\s+(\S.*)$")

_MAX_HEADING_CHARS = 90
_MAX_HEADING_WORDS = 12


def _title_ratio(text: str) -> float:
    """Fraction of alphabetic words starting with a capital.

    Guards the numbered-heading pattern against body text that merely starts
    with a figure — "2.80 US dollars per pound" scores low, "4.2 Annual Leave
    Policy" scores high.
    """
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z'-]*", text)]
    if not words:
        return 0.0
    capped = sum(1 for w in words if w[0].isupper())
    return capped / len(words)


def detect_heading(line: str) -> Optional[str]:
    """Return a normalised heading label, or None if the line is body text."""
    stripped = line.strip()
    if not stripped or len(stripped) > _MAX_HEADING_CHARS:
        return None
    if len(stripped.split()) > _MAX_HEADING_WORDS:
        return None

    m = _MARKDOWN.match(stripped)
    if m:
        return m.group(2).strip()

    m = _SEC_ITEM.match(stripped)
    if m:
        return f"{m.group(1).strip()} {m.group(2).strip()}".strip()

    m = _SECTION_WORD.match(stripped)
    if m:
        word = m.group(1).title()
        return f"{word} {m.group(2)} {m.group(3)}".strip()

    m = _NUMBERED.match(stripped)
    if m:
        rest = m.group(2).strip()
        # Headings are not sentences: they rarely end in punctuation and are
        # mostly capitalised.
        if rest.endswith((".", ",", ";", ":")):
            return None
        if _title_ratio(rest) < 0.6:
            return None
        return f"{m.group(1)} {rest}"

    # Short ALL-CAPS lines are headings in many policy documents.
    letters = [c for c in stripped if c.isalpha()]
    if len(letters) >= 3 and all(c.isupper() for c in letters):
        return stripped.title()

    return None


def _to_lines(pages: List[Dict[str, Any]]) -> List[Line]:
    lines: List[Line] = []
    for page in pages:
        for raw in page["text"].replace("\xa0", " ").split("\n"):
            lines.append((raw.rstrip(), page["page"]))
    return lines


def split_into_sections(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group a document's lines into sections keyed by detected headings."""
    sections: List[Dict[str, Any]] = []
    current: Dict[str, Any] = {"section": None, "lines": []}

    for text, page in _to_lines(pages):
        heading = detect_heading(text)
        if heading:
            if current["lines"]:
                sections.append(current)
            current = {"section": heading, "lines": []}
        elif text.strip():
            current["lines"].append((text, page))

    if current["lines"]:
        sections.append(current)

    return sections


def chunk_lines(lines: List[Line], chunk_size: int, overlap: int) -> List[List[Line]]:
    """Split (line, page) pairs into word-bounded chunks with overlap."""
    if not lines:
        return []

    # Expand to (word, page) so chunk boundaries can fall inside a long line.
    words: List[Tuple[str, int]] = []
    for text, page in lines:
        for word in text.split():
            words.append((word, page))

    if not words:
        return []
    if len(words) <= chunk_size:
        return [lines]

    chunks: List[List[Line]] = []
    start = 0
    while start < len(words):
        window = words[start : start + chunk_size]
        if not window:
            break
        # Collapse the window back into one line per page it touches.
        by_page: Dict[int, List[str]] = {}
        for word, page in window:
            by_page.setdefault(page, []).append(word)
        chunks.append([(" ".join(ws), pg) for pg, ws in sorted(by_page.items())])

        if start + chunk_size >= len(words):
            break
        start += chunk_size - overlap

    return chunks


def chunk_document(
    pages: List[Dict[str, Any]],
    source_file: str,
    company: str = "User Upload",
    chunk_size: int = 400,
    overlap: int = 60,
) -> List[Dict[str, Any]]:
    """Turn loaded pages into chunks carrying section name and page range."""
    sections = split_into_sections(pages)
    if not sections:
        return []

    all_chunks: List[Dict[str, Any]] = []
    index = 0

    for section in sections:
        for piece in chunk_lines(section["lines"], chunk_size, overlap):
            text = "\n".join(t for t, _ in piece).strip()
            if not text:
                continue
            pages_touched = [p for _, p in piece]
            label = section["section"] or "Body"
            all_chunks.append(
                {
                    "chunk_id": f"{source_file}__{label[:24]}__{index:04d}",
                    "source_file": source_file,
                    "company": company,
                    "section": section["section"],
                    "chunk_index": index,
                    "page_start": min(pages_touched),
                    "page_end": max(pages_touched),
                    "text": text,
                }
            )
            index += 1

    return all_chunks
