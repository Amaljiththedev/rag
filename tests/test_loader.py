import os
import sys

# Ensure backend directory is in python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from app.ingestion.loaders import DocumentLoader

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sec_filings")

def test_load_sec_filings():
    files = ["apple_10k_2013.txt", "tesla_10k_2022.txt", "apple_10k_2023.txt"]
    for filename in files:
        filepath = os.path.join(DATA_DIR, filename)
        assert os.path.exists(filepath), f"File {filename} does not exist in {DATA_DIR}"
        
        docs = DocumentLoader.load_sec_filing_file(filepath)
        assert len(docs) == 1
        doc = docs[0]
        
        # Check raw text extracted
        assert len(doc["content"]) > 1000
        
        # Check metadata extraction
        meta = doc["metadata"]
        assert meta["source_file"] == filename
        assert "company" in meta
        assert "filing_year" in meta
        assert meta["form_type"] == "10-K"
        
        print(f"Successfully loaded {filename}: Company='{meta['company']}', Filing Year={meta['filing_year']}, Content length={len(doc['content']):,} chars")

if __name__ == "__main__":
    test_load_sec_filings()
    print("All SEC loader tests passed successfully!")
