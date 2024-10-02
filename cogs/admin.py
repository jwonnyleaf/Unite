from __future__ import annotations

import os
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

if TYPE_CHECKING:
    from bot import UniteBot
    from utils.context import Context, GuildContext


class Admin(commands.Cog, name="admin"):
    def __init__(self, bot: UniteBot):
        self.bot = bot

    @app_commands.command(name="tps", description="Get the current TPS of the bot.")
    async def tps(self, interaction: discord.Interaction):
        """Get the current TPS of the bot."""
        embed = discord.Embed(
            title="TPS",
            description=f"The current TPS of the bot is 20.0.",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Admin(bot))
