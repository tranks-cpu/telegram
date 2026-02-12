import logging
from datetime import datetime

from telethon import TelegramClient
from telethon.tl.types import Message

from src.config import Config

logger = logging.getLogger(__name__)


async def read_messages(
    client: TelegramClient,
    since: datetime,
) -> list[Message]:
    """Read messages from all source channels since the given datetime."""
    all_messages: list[Message] = []

    for channel in Config.SOURCE_CHANNELS:
        try:
            entity = await client.get_entity(channel)
            count = 0
            async for msg in client.iter_messages(
                entity,
                offset_date=since,
                reverse=True,
            ):
                if isinstance(msg, Message) and msg.date > since:
                    all_messages.append(msg)
                    count += 1
            logger.info(f"Read {count} messages from {channel}")
        except Exception as e:
            logger.error(f"Failed to read {channel}: {e}")

    # Sort by date
    all_messages.sort(key=lambda m: m.date)
    logger.info(f"Total messages: {len(all_messages)}")
    return all_messages
