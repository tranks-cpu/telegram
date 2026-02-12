"""First-time Telegram authentication.

Creates a .session file in data/ for subsequent headless runs.

Usage:
    python -m scripts.auth
"""

import asyncio

from telethon import TelegramClient
from src.config import Config


async def main():
    errors = Config.validate()
    if errors:
        print("Configuration errors:")
        for e in errors:
            print(f"  - {e}")
        print("\nPlease fill in .env file first.")
        return

    client = TelegramClient(
        Config.SESSION_FILE,
        Config.TELEGRAM_API_ID,
        Config.TELEGRAM_API_HASH,
    )

    await client.start(phone=Config.TELEGRAM_PHONE)
    me = await client.get_me()
    print(f"\nAuthenticated as: {me.first_name} (@{me.username})")
    print(f"Session saved to: {Config.SESSION_FILE}.session")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
