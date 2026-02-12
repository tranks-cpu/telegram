"""Test reading messages from a Telegram channel.

Usage:
    python -m scripts.test_read <channel_username> [hours]
    python -m scripts.test_read crypto_channel 24
"""

import asyncio
import sys
import logging
from datetime import datetime, timezone, timedelta

from telethon import TelegramClient
from src.config import Config
from src.link_extractor import extract_links

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    channel = sys.argv[1]
    hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    client = TelegramClient(
        Config.SESSION_FILE,
        Config.TELEGRAM_API_ID,
        Config.TELEGRAM_API_HASH,
    )
    await client.start(phone=Config.TELEGRAM_PHONE)

    entity = await client.get_entity(channel)
    messages = []
    async for msg in client.iter_messages(entity, offset_date=since, reverse=True):
        if msg.date > since:
            messages.append(msg)

    print(f"\nFound {len(messages)} messages in last {hours}h from {channel}\n")

    links = extract_links(messages)
    print(f"Extracted {len(links)} links:\n")
    for link in links:
        print(f"  [{link['source_type']:10s}] {link['url']}")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
