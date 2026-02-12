import logging

import httpx
import trafilatura

from src.crawlers.base import CrawlResult

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


async def crawl_article(url: str) -> CrawlResult:
    """Crawl article using HTTPX + Trafilatura."""
    try:
        async with httpx.AsyncClient(
            headers=HEADERS, follow_redirects=True, timeout=30
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text

        text = trafilatura.extract(html, favor_recall=True)
        if not text:
            return CrawlResult(url=url, source_type="article", error="extraction_empty")

        metadata = trafilatura.extract_metadata(html)
        title = metadata.title if metadata and metadata.title else ""
        author = metadata.author if metadata and metadata.author else ""

        return CrawlResult(
            url=url,
            title=title,
            author=author,
            text=text,
            source_type="article",
        )
    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP {e.response.status_code} for {url}")
        return CrawlResult(url=url, source_type="article", error=f"http_{e.response.status_code}")
    except Exception as e:
        logger.warning(f"Article crawl failed for {url}: {e}")
        return CrawlResult(url=url, source_type="article", error=str(e))
