import logging
import re

from telethon import TelegramClient
from telethon.tl.functions.messages import CheckChatInviteRequest

from src.config import Config

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 4096


def split_message(text: str, max_len: int = MAX_MESSAGE_LENGTH) -> list[str]:
    """Split long messages at paragraph boundaries."""
    if len(text) <= max_len:
        return [text]

    parts = []
    current = ""

    for line in text.split("\n"):
        if len(current) + len(line) + 1 > max_len:
            if current:
                parts.append(current.rstrip())
            current = line + "\n"
        else:
            current += line + "\n"

    if current.strip():
        parts.append(current.rstrip())

    return parts


async def _resolve_output(client: TelegramClient) -> object:
    """Resolve output channel — supports usernames and private invite links."""
    channel = Config.OUTPUT_CHANNEL

    # Private invite link: https://t.me/+HASH or https://t.me/joinchat/HASH
    match = re.search(r"t\.me/\+([A-Za-z0-9_-]+)", channel) or \
            re.search(r"t\.me/joinchat/([A-Za-z0-9_-]+)", channel)
    if match:
        invite_hash = match.group(1)
        result = await client(CheckChatInviteRequest(invite_hash))
        # If already joined, result has .chat
        if hasattr(result, "chat"):
            return result.chat
        raise ValueError(f"Not a member of the channel. Join first: {channel}")

    return await client.get_entity(channel)


async def send_summary(client: TelegramClient, summary: str) -> bool:
    """Send summary to the output channel in HTML format."""
    try:
        entity = await _resolve_output(client)
        parts = split_message(summary)

        for i, part in enumerate(parts):
            await client.send_message(
                entity,
                part,
                parse_mode="html",
                link_preview=False,
            )
            logger.info(f"Sent part {i + 1}/{len(parts)} ({len(part)} chars)")

        logger.info(f"Summary sent to {Config.OUTPUT_CHANNEL}")
        return True
    except Exception as e:
        logger.error(f"Failed to send summary: {e}")
        return False
