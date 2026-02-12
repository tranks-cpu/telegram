import asyncio
import logging
from urllib.parse import urlparse

from src.crawlers.base import CrawlResult
from src.crawlers.article import crawl_article
from src.crawlers.twitter import crawl_twitter

logger = logging.getLogger(__name__)

TWITTER_DOMAINS = {"twitter.com", "x.com", "mobile.twitter.com"}
MAX_CONCURRENT = 5


def _is_twitter(url: str) -> bool:
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    return domain in TWITTER_DOMAINS


async def crawl_urls(urls: list[str]) -> list[CrawlResult]:
    """Crawl multiple URLs with concurrency control and fallback."""
    sem = asyncio.Semaphore(MAX_CONCURRENT)
    browser = None
    pw = None

    twitter_urls = [u for u in urls if _is_twitter(u)]
    article_urls = [u for u in urls if not _is_twitter(u)]

    # Launch shared browser if there are twitter URLs
    if twitter_urls:
        try:
            from playwright.async_api import async_playwright
            pw = await async_playwright().start()
            browser = await pw.chromium.launch(headless=True)
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")

    async def _crawl_one(url: str) -> CrawlResult:
        async with sem:
            if _is_twitter(url):
                result = await crawl_twitter(url, browser=browser)
            else:
                result = await crawl_article(url)
                # Fallback to Playwright if article extraction failed
                if not result.ok and result.error == "extraction_empty" and browser:
                    logger.info(f"Article fallback to Playwright: {url}")
                    result = await _playwright_fallback(url, browser)
            return result

    tasks = [_crawl_one(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Clean up shared browser
    if browser:
        await browser.close()
    if pw:
        await pw.stop()

    final = []
    for url, r in zip(urls, results):
        if isinstance(r, Exception):
            logger.error(f"Crawl exception for {url}: {r}")
            final.append(CrawlResult(url=url, error=str(r)))
        else:
            final.append(r)

    ok_count = sum(1 for r in final if r.ok)
    logger.info(f"Crawled {len(final)} URLs: {ok_count} ok, {len(final) - ok_count} failed")
    return final


async def _playwright_fallback(url: str, browser) -> CrawlResult:
    """Fallback: use Playwright to render JS-heavy pages."""
    try:
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle", timeout=30000)

        title = await page.title()
        # Extract main text content
        text = await page.evaluate("""
            () => {
                const article = document.querySelector('article') || document.querySelector('main') || document.body;
                return article.innerText;
            }
        """)
        await context.close()

        if not text or len(text.strip()) < 50:
            return CrawlResult(url=url, source_type="generic", error="fallback_empty")

        return CrawlResult(url=url, title=title, text=text.strip(), source_type="generic")
    except Exception as e:
        logger.warning(f"Playwright fallback failed for {url}: {e}")
        return CrawlResult(url=url, source_type="generic", error=f"fallback_{e}")
