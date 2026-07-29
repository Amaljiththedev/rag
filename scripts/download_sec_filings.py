import os
import re
import time
import urllib.request
from urllib.parse import urljoin, parse_qs, urlparse
from html.parser import HTMLParser

HEADERS = {
    'User-Agent': 'RAG-Project-Research contact@example.com',
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'www.sec.gov'
}

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sec_filings")

class SECHTMLToTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.ignore = False
        self.ignore_tags = {'script', 'style', 'head', 'title', 'meta', 'noscript'}

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        if tag_lower in self.ignore_tags:
            self.ignore = True
        elif tag_lower in {'p', 'div', 'tr', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'hr', 'table'}:
            self.text_parts.append('\n')

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in self.ignore_tags:
            self.ignore = False
        elif tag_lower in {'p', 'div', 'tr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'table'}:
            self.text_parts.append('\n')

    def handle_data(self, data):
        if not self.ignore:
            self.text_parts.append(data)

    def get_clean_text(self):
        raw = "".join(self.text_parts)
        import html
        raw = html.unescape(raw)
        
        lines = [line.strip() for line in raw.splitlines()]
        cleaned_lines = []
        prev_empty = False
        for line in lines:
            if line:
                cleaned_lines.append(line)
                prev_empty = False
            else:
                if not prev_empty and cleaned_lines:
                    cleaned_lines.append("")
                    prev_empty = True
        return "\n".join(cleaned_lines)

def fetch_url(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as response:
        content = response.read()
        if response.info().get('Content-Encoding') == 'gzip':
            import gzip
            content = gzip.decompress(content)
        return content.decode('utf-8', errors='replace')

def html_to_clean_text(html_content):
    parser = SECHTMLToTextParser()
    parser.feed(html_content)
    return parser.get_clean_text()

def unwrap_ix_url(url):
    if '/ix?doc=' in url:
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        if 'doc' in query and query['doc']:
            doc_path = query['doc'][0]
            return urljoin('https://www.sec.gov', doc_path)
    return url

def find_main_doc_url_from_index(index_url, index_html):
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', index_html, re.IGNORECASE)
    doc_url = None
    
    for href in hrefs:
        href_lower = href.lower()
        if (href_lower.endswith('.htm') or href_lower.endswith('.html')) and not href_lower.endswith('-index.html') and not href_lower.endswith('-index.htm'):
            if 'aapl' in href_lower or '10-k' in href_lower or '10k' in href_lower or 'd10k' in href_lower or '320193' in href_lower:
                doc_url = urljoin(index_url, href)
                break
                
    if not doc_url:
        for href in hrefs:
            href_lower = href.lower()
            if (href_lower.endswith('.htm') or href_lower.endswith('.html')) and not href_lower.endswith('-index.html') and not href_lower.endswith('-index.htm'):
                doc_url = urljoin(index_url, href)
                break

    if doc_url:
        doc_url = unwrap_ix_url(doc_url)
        
    return doc_url

def process_filing(name, main_url, company, form, fy, filing_date, target_path, is_index=False):
    print(f"=== Processing {name} ===")
    if is_index:
        print(f"Fetching index page: {main_url}")
        index_html = fetch_url(main_url)
        time.sleep(0.5)
        
        doc_url = find_main_doc_url_from_index(main_url, index_html)
        if not doc_url:
            raise Exception(f"Could not locate main 10-K document link on index page {main_url}")
            
        print(f"Found main filing document URL: {doc_url}")
        actual_url = doc_url
    else:
        actual_url = main_url
        
    print(f"Fetching filing content from: {actual_url}")
    html_content = fetch_url(actual_url)
    print(f"Raw HTML size: {len(html_content):,} bytes")
    
    clean_text = html_to_clean_text(html_content)
    
    header = (
        f"========================================================================\n"
        f"Source Company : {company}\n"
        f"Form Type      : {form}\n"
        f"Fiscal Year    : {fy}\n"
        f"Filing Date    : {filing_date}\n"
        f"Original URL   : {actual_url}\n"
        f"========================================================================\n\n"
    )
    
    full_text = header + clean_text
    
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(full_text)
        
    file_size = os.path.getsize(target_path)
    print(f"Saved to: {target_path}")
    print(f"File size: {file_size:,} bytes")
    print(f"First 200 characters of saved file:\n{'-'*40}\n{full_text[:200]}\n{'-'*40}\n")
    return actual_url

def main():
    filings = [
        {
            "name": "Apple 10-K FY2013",
            "url": "https://www.sec.gov/Archives/edgar/data/0000320193/000119312513416534/d590790d10k.htm",
            "company": "Apple Inc.",
            "form": "10-K",
            "fy": "FY2013",
            "filing_date": "October 30, 2013",
            "target": os.path.join(DATA_DIR, "apple_10k_2013.txt"),
            "is_index": False,
            "desc": "Apple Inc. Annual Report (10-K) for Fiscal Year 2013 ended September 28, 2013."
        },
        {
            "name": "Tesla 10-K FY2022",
            "url": "https://www.sec.gov/Archives/edgar/data/1318605/000095017023001409/tsla-20221231.htm",
            "company": "Tesla, Inc.",
            "form": "10-K",
            "fy": "FY2022",
            "filing_date": "January 31, 2023",
            "target": os.path.join(DATA_DIR, "tesla_10k_2022.txt"),
            "is_index": False,
            "desc": "Tesla, Inc. Annual Report (10-K) for Fiscal Year 2022 ended December 31, 2022."
        },
        {
            "name": "Apple 10-K FY2023",
            "url": "https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/0000320193-23-000106-index.html",
            "company": "Apple Inc.",
            "form": "10-K",
            "fy": "FY2023",
            "filing_date": "November 3, 2023",
            "target": os.path.join(DATA_DIR, "apple_10k_2023.txt"),
            "is_index": True,
            "desc": "Apple Inc. Annual Report (10-K) for Fiscal Year 2023 ended September 30, 2023."
        }
    ]

    downloaded_info = []

    for f in filings:
        try:
            actual_url = process_filing(
                name=f["name"],
                main_url=f["url"],
                company=f["company"],
                form=f["form"],
                fy=f["fy"],
                filing_date=f["filing_date"],
                target_path=f["target"],
                is_index=f["is_index"]
            )
            downloaded_info.append({
                "filename": os.path.basename(f["target"]),
                "url": actual_url,
                "desc": f["desc"]
            })
            time.sleep(1)
        except Exception as e:
            print(f"ERROR downloading {f['name']}: {e}")

    readme_path = os.path.join(DATA_DIR, "README.md")
    readme_content = "# SEC 10-K Filings Test Dataset\n\n"
    readme_content += "This directory contains parsed plain text SEC 10-K annual filings for RAG ingestion pipeline testing.\n\n"
    readme_content += "## Dataset Files\n\n"
    readme_content += "| Filename | Source URL | Description |\n"
    readme_content += "| --- | --- | --- |\n"
    for item in downloaded_info:
        readme_content += f"| `{item['filename']}` | [{item['url']}]({item['url']}) | {item['desc']} |\n"

    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"Created README.md at {readme_path}")

if __name__ == "__main__":
    main()
