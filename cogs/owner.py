from __future__ import annotations

import os
from typing import TYPE_CHECKING, Optional
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from dotenv import load_dotenv, find_dotenv

# Environment Variables
load_dotenv(find_dotenv())

if TYPE_CHECKING:
    from bot import UniteBot
    from utils.context import Context, GuildContext


class Owner(commands.Cog, name="owner"):
    def __init__(self, bot: UniteBot):
        self.bot: UniteBot = bot

    @commands.command(hidden=True)
    @commands.is_owner()
    async def load(self, ctx: Context, *, module: str):
        """Loads a module."""
        try:
            await self.bot.load_extension(f"cogs.{module}")
            embed = discord.Embed(
                title="Load",
                description=f"Loaded extension '{module}'",
                color=discord.Color.green(),
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Load",
                description=f"Failed to load extension {module}\n{e}",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def unload(self, ctx: Context, *, module: str):
        """Unloads a module."""
        try:
            await self.bot.unload_extension(f"cogs.{module}")
            embed = discord.Embed(
                title="Unload",
                description=f"Unloaded extension '{module}'",
                color=discord.Color.green(),
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Unload",
                description=f"Failed to unload extension {module}\n{e}",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)

    @commands.command(name="reload", hidden=True)
    @commands.is_owner()
    async def _reload(self, ctx: Context, *, module: str):
        """Reload a cog."""
        try:
            await self.bot.reload_extension(f"cogs.{module}")
            embed = discord.Embed(
                title="Reload",
                description=f"Reloaded extension '{module}'",
                color=discord.Color.green(),
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Reload",
                description=f"Failed to reload extension {module}\n{e}",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True)
    @commands.is_owner()
    @commands.guild_only()
    async def sync(
        self, ctx: GuildContext, guild_id: Optional[int], copy: bool = False
    ):
        """Sync the commands to the guild."""
        if guild_id:
            guild = discord.Object(id=guild_id)
        else:
            guild = ctx.guild

        if copy:
            await self.bot.tree.copy_global_to(guild=guild)

        await self.bot.tree.sync(guild=guild)
        embed = discord.Embed(
            title="Sync",
            description=f"Synced commands to Guild {guild.name}.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @sync.command(name="global")
    @commands.is_owner()
    async def sync_global(self, ctx: Context):
        """Sync the commands globally."""
        commands = await self.bot.tree.sync(guild=None)
        await ctx.send(f"Successfully synced {len(commands)} commands")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Owner(bot))
