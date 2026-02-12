import logging

from src.crawlers.base import CrawlResult

logger = logging.getLogger(__name__)


async def crawl_twitter(url: str, browser=None) -> CrawlResult:
    """Crawl tweet using Playwright with stealth."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return CrawlResult(url=url, source_type="twitter", error="playwright_not_installed")

    own_browser = browser is None

    try:
        pw = None
        if own_browser:
            pw = await async_playwright().start()
            browser = await pw.chromium.launch(headless=True)

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )

        # Stealth: mask webdriver detection
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        """)

        page = await context.new_page()

        # Normalize URL: x.com -> twitter.com for better compatibility
        normalized_url = url.replace("x.com", "twitter.com")
        await page.goto(normalized_url, wait_until="domcontentloaded", timeout=30000)

        # Wait for tweet content to load
        try:
            await page.wait_for_selector('[data-testid="tweetText"]', timeout=15000)
        except Exception:
            # Try alternative: maybe it's a thread or quote tweet
            await page.wait_for_selector("article", timeout=10000)

        # Extract tweet text
        tweet_els = await page.query_selector_all('[data-testid="tweetText"]')
        texts = []
        for el in tweet_els:
            t = await el.inner_text()
            if t:
                texts.append(t.strip())

        text = "\n\n".join(texts) if texts else ""

        # Extract author
        author = ""
        author_el = await page.query_selector('[data-testid="User-Name"]')
        if author_el:
            author = (await author_el.inner_text()).strip()
            # Usually "DisplayName\n@handle" — take just the first line as display name
            if "\n" in author:
                author = author.split("\n")[0]

        await context.close()
        if own_browser and pw:
            await browser.close()
            await pw.stop()

        if not text:
            return CrawlResult(url=url, source_type="twitter", error="no_tweet_text")

        return CrawlResult(
            url=url,
            title=f"Tweet by {author}" if author else "Tweet",
            author=author,
            text=text,
            source_type="twitter",
        )

    except Exception as e:
        logger.warning(f"Twitter crawl failed for {url}: {e}")
        return CrawlResult(url=url, source_type="twitter", error=str(e))
