import io
import os
import re
from typing import Dict, Any, List


def load_pdf(filepath: str) -> str:
    """Extract text from a digital PDF, page by page."""
    import pdfplumber

    pages = []
    skipped = 0
    with pdfplumber.open(filepath) as pdf:
        total = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            # extract_text() returns None for image-only pages. Scanned PDFs are
            # entirely such pages and need OCR (pytesseract) to be readable —
            # out of scope for now, digital PDFs only.
            if text is None:
                skipped += 1
                continue
            pages.append(text)

    if skipped:
        print(f"[loaders] {skipped}/{total} pages had no extractable text (image-only; needs OCR)")
    if not pages:
        raise ValueError(
            f"No extractable text in {os.path.basename(filepath)}. "
            "It is likely a scanned PDF, which requires OCR (not supported yet)."
        )

    print(f"[loaders] extracted text from {len(pages)}/{total} PDF pages")
    return "\n\n".join(pages)


def load_txt(filepath: str) -> str:
    """Read a plain text file."""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    if not text.strip():
        raise ValueError(f"{os.path.basename(filepath)} is empty.")
    print(f"[loaders] read {len(text):,} chars of text")
    return text


LOADERS = {".pdf": load_pdf, ".txt": load_txt}


def load_file(filepath: str) -> str:
    """Dispatch to the right loader based on file extension."""
    ext = os.path.splitext(filepath)[1].lower()
    loader = LOADERS.get(ext)
    if loader is None:
        raise ValueError(f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(LOADERS))}")
    print(f"[loaders] loading {os.path.basename(filepath)} as {ext}")
    return loader(filepath)


class DocumentLoader:
    """PDF/HTML/Markdown document loader returning raw text + metadata."""

    @staticmethod
    def parse_sec_header(text: str):
        """Extract metadata header if present at top of SEC txt file."""
        metadata = {}
        header_pattern = r"^={10,}\s*\n(.*?)\n={10,}\s*\n"
        match = re.search(header_pattern, text, re.DOTALL)
        if match:
            header_content = match.group(1)
            for line in header_content.splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    key_clean = key.strip().lower().replace(" ", "_")
                    val_clean = val.strip()
                    if key_clean == "source_company":
                        metadata["company"] = val_clean
                    elif key_clean == "fiscal_year":
                        year_match = re.search(r'\d{4}', val_clean)
                        metadata["filing_year"] = int(year_match.group(0)) if year_match else val_clean
                    elif key_clean == "form_type":
                        metadata["form_type"] = val_clean
                    elif key_clean == "filing_date":
                        metadata["filing_date"] = val_clean
                    elif key_clean == "original_url":
                        metadata["original_url"] = val_clean
            body = text[match.end():]
            return metadata, body
        return metadata, text

    @staticmethod
    def load_pdf(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        pages_data = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages_data.append({
                "content": text,
                "metadata": {
                    "filename": filename,
                    "page_number": i + 1,
                    "file_type": "pdf"
                }
            })
        return pages_data

    @staticmethod
    def load_text(text: str, filename: str, file_type: str = "txt") -> List[Dict[str, Any]]:
        parsed_meta, clean_body = DocumentLoader.parse_sec_header(text)
        metadata = {
            "filename": filename,
            "source_file": filename,
            "file_type": file_type,
            **parsed_meta
        }
        return [{
            "content": clean_body,
            "metadata": metadata
        }]

    @staticmethod
    def load_sec_filing_file(filepath: str) -> List[Dict[str, Any]]:
        filename = os.path.basename(filepath)
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return DocumentLoader.load_text(content, filename)

