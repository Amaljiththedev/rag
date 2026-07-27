import io
from typing import Dict, Any, List
from pypdf import PdfReader

class DocumentLoader:
    """PDF/HTML/Markdown document loader returning raw text + metadata."""

    @staticmethod
    def load_pdf(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
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
        return [{
            "content": text,
            "metadata": {
                "filename": filename,
                "file_type": file_type
            }
        }]
