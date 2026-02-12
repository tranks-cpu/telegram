import asyncio
import logging

from telethon import TelegramClient
from telethon.errors import FloodWaitError

from src.config import Config
from src.state import load_last_run, save_last_run
from src.telegram_reader import read_messages
from src.link_extractor import extract_links, extract_message_texts
from src.crawlers.router import crawl_urls
from src.summarizer import summarize
from src.telegram_sender import send_summary

logger = logging.getLogger(__name__)


async def run_pipeline() -> None:
    """Run the full news aggregation pipeline."""
    # Validate config
    errors = Config.validate()
    if errors:
        for e in errors:
            logger.error(f"Config error: {e}")
        return

    # 1. Load last run timestamp
    last_run = load_last_run()
    logger.info(f"Last run: {last_run.isoformat()}")

    # 2. Connect to Telegram
    client = TelegramClient(
        Config.SESSION_FILE,
        Config.TELEGRAM_API_ID,
        Config.TELEGRAM_API_HASH,
    )
    await client.start(phone=Config.TELEGRAM_PHONE)

    try:
        # 3. Read messages from source channels
        try:
            messages = await read_messages(client, last_run)
        except FloodWaitError as e:
            logger.warning(f"FloodWaitError: waiting {e.seconds}s")
            await asyncio.sleep(e.seconds)
            messages = await read_messages(client, last_run)

        if not messages:
            logger.info("No new messages found")
            save_last_run()
            return

        # 4. Extract links and message texts
        links = extract_links(messages)
        message_texts = extract_message_texts(messages)

        if not links and not message_texts:
            logger.info("No links or meaningful text found")
            save_last_run()
            return

        # 5. Crawl URLs
        results = []
        if links:
            urls = [link["url"] for link in links]
            logger.info(f"Found {len(urls)} unique URLs to crawl")
            results = await crawl_urls(urls)

        # 6. Summarize with Claude
        summary = await summarize(results, message_texts)
        if not summary:
            logger.error("Summarization failed, skipping send")
            save_last_run()
            return

        # 7. Send to output channel
        await send_summary(client, summary)

        # 8. Save state
        save_last_run()

    finally:
        await client.disconnect()
