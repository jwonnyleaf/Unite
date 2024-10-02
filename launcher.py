import os
import asyncio

from bot import UniteBot


async def run_bot():
    async with UniteBot() as bot:
        await bot.start()


def main():
    """Launches the bot."""
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
