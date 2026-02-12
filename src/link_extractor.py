import re
import logging
from urllib.parse import urlparse

from telethon.tl.types import (
    Message,
    MessageEntityUrl,
    MessageEntityTextUrl,
)

logger = logging.getLogger(__name__)

URL_REGEX = re.compile(r"https?://[A-Za-z0-9][^\s<>\"'\)\]]*")

TWITTER_DOMAINS = {"twitter.com", "x.com", "mobile.twitter.com"}
MEDIUM_DOMAINS = {"medium.com"}
SUBSTACK_KEYWORDS = {"substack.com"}
MIRROR_DOMAINS = {"mirror.xyz"}

# Skip URLs that are not worth crawling
SKIP_DOMAINS = {
    "t.me", "telegram.me", "telegram.org",
    "youtube.com", "youtu.be",
    "instagram.com",
    "tiktok.com",
    "discord.gg", "discord.com",
}


def classify_url(url: str) -> str:
    """Classify URL into source type."""
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    if domain in TWITTER_DOMAINS:
        return "twitter"
    if domain in MEDIUM_DOMAINS or ".medium.com" in domain:
        return "medium"
    if any(kw in domain for kw in SUBSTACK_KEYWORDS):
        return "substack"
    if domain in MIRROR_DOMAINS:
        return "mirror"
    return "article"


def should_skip(url: str) -> bool:
    """Check if URL should be skipped."""
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    return domain in SKIP_DOMAINS


def _is_valid_url(url: str) -> bool:
    """Check if URL is well-formed."""
    if "\n" in url or "\r" in url or " " in url:
        return False
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        # Domain must have a dot (e.g. "example.com")
        if "." not in parsed.netloc:
            return False
        return True
    except Exception:
        return False


def _utf16_extract(text: str, offset: int, length: int) -> str:
    """Extract substring using UTF-16 offsets (Telegram entity standard)."""
    encoded = text.encode("utf-16-le")
    # Each UTF-16 code unit = 2 bytes
    start_byte = offset * 2
    end_byte = (offset + length) * 2
    return encoded[start_byte:end_byte].decode("utf-16-le")


def extract_links(messages: list[Message]) -> list[dict]:
    """Extract and deduplicate URLs from messages.

    Returns list of dicts: {url, source_type, channel, date}
    """
    seen_urls: set[str] = set()
    links: list[dict] = []

    for msg in messages:
        if not msg.text:
            continue

        urls_in_msg: list[str] = []

        # Extract from message entities
        if msg.entities:
            for ent in msg.entities:
                if isinstance(ent, MessageEntityTextUrl):
                    # TextUrl has the URL as attribute — always reliable
                    urls_in_msg.append(ent.url)
                elif isinstance(ent, MessageEntityUrl):
                    # Extract using UTF-16 offsets to handle emoji correctly
                    try:
                        url = _utf16_extract(msg.text, ent.offset, ent.length)
                    except Exception:
                        url = msg.text[ent.offset : ent.offset + ent.length]
                    if not url.startswith("http"):
                        url = "https://" + url
                    urls_in_msg.append(url)

        # Regex fallback only if no entities found URLs
        if not urls_in_msg:
            urls_in_msg = URL_REGEX.findall(msg.text)

        # Validate, deduplicate, and classify
        for url in urls_in_msg:
            # Clean trailing punctuation
            url = url.rstrip(".,;:!?)")

            # If URL contains another URL (broken extraction), take the last valid one
            # e.g. "https://ce: https://www.binance.com/..." → "https://www.binance.com/..."
            all_urls = URL_REGEX.findall(url)
            if len(all_urls) > 1:
                url = all_urls[-1].rstrip(".,;:!?)")
            elif not all_urls:
                continue

            if not _is_valid_url(url):
                logger.debug(f"Skipping invalid URL: {url[:80]}")
                continue

            if url in seen_urls or should_skip(url):
                continue
            seen_urls.add(url)

            channel_name = ""
            if msg.peer_id and hasattr(msg.peer_id, "channel_id"):
                channel_name = str(msg.peer_id.channel_id)

            links.append({
                "url": url,
                "source_type": classify_url(url),
                "channel": channel_name,
                "date": msg.date.isoformat(),
            })

    logger.info(f"Extracted {len(links)} unique links from {len(messages)} messages")
    return links


MIN_TEXT_LENGTH = 30


def extract_message_texts(messages: list[Message]) -> list[dict]:
    """Extract message texts that have meaningful content (with or without links).

    Returns list of dicts: {text, channel, date}
    """
    texts = []
    seen = set()

    for msg in messages:
        if not msg.text or len(msg.text.strip()) < MIN_TEXT_LENGTH:
            continue

        # Remove URLs from text to get the "message body"
        clean = URL_REGEX.sub("", msg.text).strip()
        if len(clean) < MIN_TEXT_LENGTH:
            continue

        # Deduplicate by first 100 chars
        key = clean[:100]
        if key in seen:
            continue
        seen.add(key)

        channel_name = ""
        if msg.peer_id and hasattr(msg.peer_id, "channel_id"):
            channel_name = str(msg.peer_id.channel_id)

        texts.append({
            "text": clean,
            "channel": channel_name,
            "date": msg.date.isoformat(),
        })

    logger.info(f"Extracted {len(texts)} message texts from {len(messages)} messages")
    return texts
