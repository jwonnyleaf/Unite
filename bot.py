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

log = logging.getLogger("UniteBot")


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
        self.logger = log
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

    async def on_app_command_completion(
        self, interaction: discord.Interaction, command: discord.app_commands.Command
    ) -> None:
        """Executed when an application command is successfully completed."""
        self.logger.info(
            f"Executed /{command.name} application command in {interaction.guild.name} (ID: {interaction.guild.id}) by {interaction.user} (ID: {interaction.user.id})"
        )

    async def start(self) -> None:
        """Start the bot."""
        await super().start(TOKEN, reconnect=True)
