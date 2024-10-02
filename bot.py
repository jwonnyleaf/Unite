import os
import logging
import platform
from dotenv import load_dotenv, find_dotenv

import discord
from discord.ext import commands
from discord.ext.commands import Context

from database import Database

INITIAL_EXTENSIONS = ["cogs.owner", "cogs.admin", "cogs.assassins"]

# Environment Variables
load_dotenv(find_dotenv())
TOKEN = os.getenv("DISCORD_TOKEN")
DB_NAME = os.getenv("DB_NAME")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True


class LoggingFormatter(logging.Formatter):
    black = "\x1b[30m"
    red = "\x1b[31m"
    green = "\x1b[32m"
    yellow = "\x1b[33m"
    blue = "\x1b[34m"
    gray = "\x1b[38m"

    reset = "\x1b[0m"
    bold = "\x1b[1m"

    COLORS = {
        logging.DEBUG: gray + bold,
        logging.INFO: blue + bold,
        logging.WARNING: yellow + bold,
        logging.ERROR: red,
        logging.CRITICAL: red + bold,
    }

    def format(self, record):
        log_color = self.COLORS[record.levelno]
        format = "(black){asctime}(reset) (levelcolor){levelname:<8}(reset) (green){name}(reset) {message}"
        format = format.replace("(black)", self.black + self.bold)
        format = format.replace("(reset)", self.reset)
        format = format.replace("(levelcolor)", log_color)
        format = format.replace("(green)", self.green + self.bold)
        formatter = logging.Formatter(format, "%Y-%m-%d %H:%M:%S", style="{")
        return formatter.format(record)


logger = logging.getLogger("UniteSystem")
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(LoggingFormatter())
# File handler
file_handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
file_handler_formatter = logging.Formatter(
    "[{asctime}] [{levelname:<8}] {name}: {message}", "%Y-%m-%d %H:%M:%S", style="{"
)
file_handler.setFormatter(file_handler_formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)


class UniteBot(
    commands.Bot,
):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
            allowed_mentions=discord.AllowedMentions(
                everyone=True, roles=True, users=True
            ),
            activity=discord.Activity(type=discord.ActivityType.watching, name="/help"),
            status=discord.Status.do_not_disturb,
        )
        self.logger = logger
        self.db = None

    async def setup_hook(self) -> None:
        """
        This will just be executed when the bot starts the first time.
        """
        self.logger.info(f"Logged in as {self.user.name}")
        self.logger.info(f"Using discord.py API Version {discord.__version__}")
        self.logger.info(f"Using Python Version {platform.python_version()}")
        self.logger.info("-------------------")
        await self.load_database()
        await self.load_cogs()
        self.logger.info("UniteBot is ready.")

    async def load_cogs(self):
        for extension in INITIAL_EXTENSIONS:
            try:
                await self.load_extension(extension)
                self.logger.info(f"Loaded extension '{extension}'")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                self.logger.error(f"Failed to load extension {extension}\n{exception}")

    async def load_database(self):
        """Connect to the database and create the necessary tables."""
        self.db = Database(DB_NAME)
        if self.db is None:
            self.logger.error("Failed to connect to the database.")
            return

        self.logger.info("Connected to the database.")

        await self.db.assassins.create_table()

    async def on_message(self, message: discord.Message) -> None:
        """Executed every time a message is sent in a channel the bot can see."""
        if message.author == self.user or message.author.bot:
            return
        try:
            await self.process_commands(message)
        except Exception as e:
            self.logger.error(f"Error processing message from {message.author}: {e}")

    async def on_command_completion(self, context: Context) -> None:
        """Executed when a command is successfully completed."""
        full_command_name = context.command.qualified_name
        split = full_command_name.split(" ")
        executed_command = str(split[0])
        if context.guild is not None:
            self.logger.info(
                f"Executed {executed_command} command in {context.guild.name} (ID: {context.guild.id}) by {context.author} (ID: {context.author.id})"
            )
        else:
            self.logger.info(
                f"Executed {executed_command} command by {context.author} (ID: {context.author.id}) in DMs"
            )

    async def on_app_command_completion(self, context: Context) -> None:
        """Executed when an application command is successfully completed."""
        if context.guild is not None:
            self.logger.info(
                f"Executed {context.command} command in {context.guild.name} (ID: {context.guild.id}) by {context.author} (ID: {context.author.id})"
            )
        else:
            self.logger.info(
                f"Executed {context.command} command by {context.author} (ID: {context.author.id}) in DMs"
            )

    async def start(self) -> None:
        """Start the bot."""
        await super().start(TOKEN, reconnect=True)
