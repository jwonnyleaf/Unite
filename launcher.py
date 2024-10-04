import os
import logging
from logging.handlers import RotatingFileHandler
import asyncio
import discord
from contextlib import contextmanager

from bot import UniteBot


@contextmanager
def setup_logging():
    log = logging.getLogger()

    try:
        discord.utils.setup_logging()
        max_bytes = 32 * 1024 * 1024  # 32 MB
        logging.getLogger("discord").setLevel(logging.INFO)
        logging.getLogger("discord.http").setLevel(logging.WARNING)
        logging.getLogger("discord.state").setLevel(logging.WARNING)

        log.setLevel(logging.INFO)
        handler = RotatingFileHandler(
            filename="unite.log",
            encoding="utf-8",
            mode="w",
            maxBytes=max_bytes,
            backupCount=5,
        )
        datefmt = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(
            "[{asctime}] [{levelname:<8}] {name}: {message}", datefmt, style="{"
        )
        handler.setFormatter(formatter)
        log.addHandler(handler)
        yield
    finally:
        handlers = log.handlers[:]
        for handler in handlers:
            handler.close()
            log.removeHandler(handler)


async def run_bot():
    async with UniteBot() as bot:
        await bot.start()


def main():
    """Launches the bot."""
    with setup_logging():
        asyncio.run(run_bot())


if __name__ == "__main__":
    main()
