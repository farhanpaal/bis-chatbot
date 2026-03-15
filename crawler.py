"""
BIS Website Crawler — English-only async crawler for bis.gov.in
Saves pages as JSON with URL, title, content, timestamp
"""

import asyncio
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import Set

import aiohttp
from bs4 import BeautifulSoup

BASE_URL = "https://www.bis.gov.in"
OUTPUT_FILE = "crawled_data.json"
MAX_PAGES = 300  # Adjust as needed
DELAY = 0.5  # Seconds between requests

# Seed URLs covering all BIS sections
SEED_URLS = [
    "https://www.bis.gov.in",
    "https://www.bis.gov.in/index.php/about-bis/",
    "https://www.bis.gov.in/index.php/certification/",
    "https://www.bis.gov.in/index.php/laboratory/",
    "https://www.bis.gov.in/index.php/standards/",
    "https://www.bis.gov.in/index.php/consumer-affairs/",
    "https://www.bis.gov.in/index.php/publications/",
    "https://www.bis.gov.in/index.php/international-relations/",
    "https://www.bis.gov.in/index.php/press-release/",
    "https://www.bis.gov.in/index.php/legislation/",
    "https://www.bis.gov.in/index.php/grievance/",
    "https://www.bis.gov.in/index.php/schemes/",
    "https://www.bis.gov.in/index.php/scheme/compulsory-registration-scheme/",
    "https://www.bis.gov.in/index.php/scheme/foreign-manufacturers-certification-scheme/",
    "https://www.bis.gov.in/index.php/scheme/hallmarking/",
    "https://www.bis.gov.in/index.php/scheme/eco-mark-scheme/",
    "https://www.bis.gov.in/index.php/about-bis/what-is-bis/",
    "https://www.bis.gov.in/index.php/about-bis/organization-structure/",
    "https://www.bis.gov.in/index.php/about-bis/achievements/",
    "https://www.bis.gov.in/index.php/consumer-affairs/consumer-awareness/",
    "https://www.bis.gov.in/index.php/consumer-affairs/consumer-connect/",
]

SKIP_EXTENSIONS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar',
                   '.jpg', '.jpeg', '.png', '.gif', '.svg', '.mp4', '.mp3'}

HINDI_PATTERN = re.compile(r'[\u0900-\u097F]')


def is_english_content(text: str) -> bool:
    """Returns True if content is predominantly English (not Hindi)."""
    if not text:
        return False
    hindi_chars = len(HINDI_PATTERN.findall(text))
    total_chars = len(text.strip())
    if total_chars == 0:
        return False
    return (hindi_chars / total_chars) < 0.15  # Allow < 15% Hindi characters


def clean_text(text: str) -> str:
    """Clean and normalize extracted text."""
    # Remove Hindi characters
    text = HINDI_PATTERN.sub('', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove very short lines mixed in
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 10]
    return ' '.join(lines)


def extract_content(soup: BeautifulSoup, url: str) -> dict:
    """Extract structured content from a page."""
    # Remove nav, footer, scripts, styles
    for tag in soup(['script', 'style', 'nav', 'footer', 'header',
                     'iframe', 'noscript', '.menu', '#menu', '.navbar']):
        tag.decompose()

    title = ""
    if soup.title:
        title = soup.title.get_text(strip=True)
    if not title and soup.find('h1'):
        title = soup.find('h1').get_text(strip=True)

    # Extract main content
    main = (soup.find('main') or soup.find('article') or
            soup.find(class_=re.compile(r'content|main|body', re.I)) or
            soup.find('body'))

    if not main:
        return None

    # Extract text with structure
    content_parts = []

    for element in main.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'td', 'th']):
        text = element.get_text(separator=' ', strip=True)
        if len(text) < 15:
            continue
        if not is_english_content(text):
            continue
        clean = clean_text(text)
        if clean:
            if element.name in ['h1', 'h2', 'h3', 'h4']:
                content_parts.append(f"\n## {clean}\n")
            else:
                content_parts.append(clean)

    full_content = ' '.join(content_parts)

    if len(full_content) < 100:
        return None

    return {
        "url": url,
        "title": clean_text(title),
        "content": full_content,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }


def is_valid_url(url: str) -> bool:
    """Check if URL should be crawled."""
    parsed = urlparse(url)
    if parsed.netloc and 'bis.gov.in' not in parsed.netloc:
        return False
    ext = Path(parsed.path).suffix.lower()
    if ext in SKIP_EXTENSIONS:
        return False
    if any(skip in url.lower() for skip in ['#', 'javascript:', 'mailto:', 'tel:']):
        return False
    return True


def extract_links(soup: BeautifulSoup, current_url: str) -> list:
    """Extract all internal links from a page."""
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        if not href or href.startswith('#'):
            continue
        full_url = urljoin(current_url, href)
        # Normalize: remove fragments and trailing slashes
        parsed = urlparse(full_url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if normalized.endswith('/index.php'):
            normalized = normalized.replace('/index.php', '/')
        if is_valid_url(normalized) and 'bis.gov.in' in normalized:
            links.append(normalized)
    return links


async def crawl_page(session: aiohttp.ClientSession, url: str) -> tuple:
    """Crawl a single page and return (data, links)."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; BIS-RAG-Bot/1.0)',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                return None, []
            content_type = resp.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                return None, []
            html = await resp.text(errors='ignore')

        soup = BeautifulSoup(html, 'html.parser')
        data = extract_content(soup, url)
        links = extract_links(soup, url)
        return data, links

    except Exception as e:
        print(f"  Error crawling {url}: {e}")
        return None, []


async def crawl_bis():
    """Main async crawl function."""
    visited: Set[str] = set()
    queue = list(SEED_URLS)
    results = []

    print(f"Starting BIS crawler — target: {MAX_PAGES} pages")
    print(f"Output: {OUTPUT_FILE}\n")

    connector = aiohttp.TCPConnector(limit=5, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        while queue and len(visited) < MAX_PAGES:
            url = queue.pop(0)
            if url in visited:
                continue

            visited.add(url)
            print(f"[{len(visited)}/{MAX_PAGES}] Crawling: {url}")

            data, links = await crawl_page(session, url)

            if data:
                results.append(data)
                print(f"  ✓ '{data['title'][:60]}...' ({len(data['content'])} chars)")

            # Add new links to queue
            for link in links:
                if link not in visited and link not in queue:
                    queue.append(link)

            await asyncio.sleep(DELAY)

    # Save results
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Crawl complete!")
    print(f"   Pages crawled: {len(visited)}")
    print(f"   Pages with content: {len(results)}")
    print(f"   Saved to: {OUTPUT_FILE}")
    return results


if __name__ == "__main__":
    asyncio.run(crawl_bis())
