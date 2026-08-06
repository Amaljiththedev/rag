import os
from typing import Any, Dict, List

# A loaded document is a list of pages: [{"page": 1, "text": "..."}, ...].
# Page numbers are carried all the way through to citations, so they must be
# the real 1-based page of the source file — never renumbered after skipping
# unreadable pages.
Page = Dict[str, Any]


def load_pdf(filepath: str) -> List[Page]:
    """Extract text from a digital PDF, one entry per readable page."""
    import pdfplumber

    pages: List[Page] = []
    skipped = 0
    with pdfplumber.open(filepath) as pdf:
        total = len(pdf.pages)
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            # extract_text() returns None for image-only pages. Scanned PDFs are
            # entirely such pages and need OCR (pytesseract) to be readable —
            # out of scope for now, digital PDFs only.
            if not text or not text.strip():
                skipped += 1
                continue
            pages.append({"page": i, "text": text})

    if skipped:
        print(f"[loaders] {skipped}/{total} pages had no extractable text (image-only; needs OCR)")
    if not pages:
        raise ValueError(
            f"No extractable text in {os.path.basename(filepath)}. "
            "It is likely a scanned PDF, which requires OCR (not supported yet)."
        )

    print(f"[loaders] extracted text from {len(pages)}/{total} PDF pages")
    return pages


def load_txt(filepath: str) -> List[Page]:
    """Read a plain text file. Text files have no pages, so it is all page 1."""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    if not text.strip():
        raise ValueError(f"{os.path.basename(filepath)} is empty.")
    print(f"[loaders] read {len(text):,} chars of text")
    return [{"page": 1, "text": text}]


LOADERS = {".pdf": load_pdf, ".txt": load_txt}


def load_file(filepath: str) -> List[Page]:
    """Dispatch to the right loader based on file extension."""
    ext = os.path.splitext(filepath)[1].lower()
    loader = LOADERS.get(ext)
    if loader is None:
        raise ValueError(f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(LOADERS))}")
    print(f"[loaders] loading {os.path.basename(filepath)} as {ext}")
    return loader(filepath)


def page_count(pages: List[Page]) -> int:
    return max((p["page"] for p in pages), default=0)
