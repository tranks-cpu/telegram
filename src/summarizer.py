import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from src.crawlers.base import CrawlResult

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 300
PROMPT_TEMPLATE = (Path(__file__).parent / "prompts" / "summary.txt").read_text


async def call_claude(prompt: str, model: str = "sonnet") -> str | None:
    """Call Claude CLI with the given prompt. Returns result or None on failure."""
    process = None
    try:
        process = await asyncio.create_subprocess_exec(
            "claude",
            "-p",
            "--model",
            model,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(input=prompt.encode("utf-8")),
            timeout=TIMEOUT_SECONDS,
        )

        if process.returncode != 0:
            logger.error(f"Claude CLI error: {stderr.decode()[:500]}")
            return None

        return stdout.decode("utf-8").strip()

    except asyncio.TimeoutError:
        logger.error(f"Claude CLI timeout after {TIMEOUT_SECONDS}s")
        if process:
            try:
                process.kill()
            except Exception:
                pass
        return None
    except FileNotFoundError:
        logger.error("Claude CLI not found. Make sure 'claude' is in PATH")
        return None
    except Exception as e:
        logger.error(f"Claude CLI unexpected error: {e}")
        return None


def build_prompt(
    results: list[CrawlResult],
    message_texts: list[dict] | None = None,
) -> str:
    """Build the summarization prompt from crawl results and message texts."""
    template = PROMPT_TEMPLATE()

    content_blocks = []
    idx = 1

    # Crawled content
    for r in results:
        if r.ok:
            block = f"[{idx}] {r.title or 'Untitled'}\nURL: {r.url}\nAuthor: {r.author or 'Unknown'}\nType: {r.source_type}\n\n{r.text}"
        else:
            block = f"[{idx}] Crawl failed\nURL: {r.url}\nError: {r.error}"
        content_blocks.append(block)
        idx += 1

    # Message texts (no URL)
    if message_texts:
        for mt in message_texts:
            block = f"[{idx}] Channel message\nChannel: {mt['channel']}\nDate: {mt['date']}\n\n{mt['text']}"
            content_blocks.append(block)
            idx += 1

    total = idx - 1
    today = datetime.now(timezone.utc).strftime("%Y년 %m월 %d일")
    content = "\n\n---\n\n".join(content_blocks)
    return (
        template
        .replace("{{CONTENT}}", content)
        .replace("{{COUNT}}", str(total))
        .replace("{{DATE}}", today)
    )


async def summarize(
    results: list[CrawlResult],
    message_texts: list[dict] | None = None,
) -> str | None:
    """Summarize crawled content and message texts using Claude CLI."""
    if not results and not message_texts:
        logger.info("No content to summarize")
        return None

    prompt = build_prompt(results, message_texts)
    logger.info(f"Summarizing {len(results)} crawled + {len(message_texts or [])} messages (prompt: {len(prompt)} chars)")

    summary = await call_claude(prompt)
    if summary:
        logger.info(f"Summary generated: {len(summary)} chars")
    return summary
