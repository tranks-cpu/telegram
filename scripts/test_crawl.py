"""Test crawling a single URL.

Usage:
    python -m scripts.test_crawl <URL>
    python -m scripts.test_crawl https://x.com/elonmusk/status/123456
    python -m scripts.test_crawl https://medium.com/@author/article-slug
"""

import asyncio
import sys
import logging

from src.crawlers.router import crawl_urls

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    url = sys.argv[1]
    print(f"Crawling: {url}\n")

    results = await crawl_urls([url])
    r = results[0]

    print(f"URL:    {r.url}")
    print(f"Title:  {r.title}")
    print(f"Author: {r.author}")
    print(f"Type:   {r.source_type}")
    print(f"Error:  {r.error}")
    print(f"Text length: {len(r.text)} chars")
    print(f"\n--- Text (first 1000 chars) ---\n{r.text[:1000]}")


if __name__ == "__main__":
    asyncio.run(main())
