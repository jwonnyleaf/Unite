from __future__ import annotations

import os
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from utils.constants import EmbedColors

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

    @app_commands.command(name="prefix", description="Set the prefix for the bot.")
    @app_commands.describe(prefix="The new prefix for the bot.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_prefix(self, interaction: discord.Interaction, prefix: str) -> None:
        """Set the prefix for the bot."""
        # Check if the prefix is longer than 5 characters and only alphabetical
        if len(prefix) > 5 or not prefix.isalpha():
            embed = discord.Embed(
                title="Error",
                description="Prefix must be less than 5 characters and only alphabetical.",
                color=EmbedColors.RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await self.bot.db.guilds.set_prefix(interaction.guild, prefix)
        embed = discord.Embed(
            title="Prefix Set",
            description=f"The prefix for this server has been set to `{prefix}`.",
            color=EmbedColors.GREEN,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="setchannel", description="Set the channel for the bot.")
    @app_commands.describe(
        channel_type="The type of channel to set.",
        channel="The channel to set.",
    )
    @app_commands.choices(
        channel_type=[app_commands.Choice(name="Assassins", value="assassins")]
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def set_channel(
        self,
        interaction: discord.Interaction,
        channel_type: str,
        channel: discord.TextChannel,
    ) -> None:
        """Set the channel for the bot."""
        await self.bot.db.guilds.set_channel(
            interaction.guild, channel_type, channel.id
        )
        embed = discord.Embed(
            title="Channel Set",
            description=f"The {channel_type} channel for this server has been set to {channel.mention}.",
            color=EmbedColors.GREEN,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Admin(bot))
