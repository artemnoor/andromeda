"""Long-polling entry point for the single-instance deployment."""

from __future__ import annotations

import asyncio
import logging

from .bot import create_runtime
from .config import Settings
from .logging import configure_logging


async def run() -> None:
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    logger = logging.getLogger("andromeda_telegram")
    bot, dispatcher, backend, renderer, _sessions = create_runtime(settings)
    logger.info("telegram_bot_start mode=long_polling")
    try:
        await dispatcher.start_polling(bot)
    finally:
        await backend.close()
        await renderer.close()
        await bot.session.close()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
