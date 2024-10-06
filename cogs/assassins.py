from __future__ import annotations

import os
from typing import TYPE_CHECKING
import re

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from utils.context import ConfirmationView
from utils.constants import EmbedColors
from utils.utils import validImageURL
from database.assassins import PlayerStatus

if TYPE_CHECKING:
    from bot import UniteBot
    from utils.context import Context, GuildContext


class Assassins(commands.Cog, name="assassin"):
    def __init__(self, bot: UniteBot):
        self.bot = bot
        self.db = bot.db
        self.started = {}

    async def cog_load(self):
        guilds = await self.db.guilds.get_all_guilds()
        for guild in guilds:
            self.started[guild.guildID] = guild.assassinsStarted

    @commands.Cog.listener()
    async def on_player_dead(self, user: discord.Member):
        """Announce when a player is eliminated."""
        player = await self.db.assassins.get_player_by_discord_id(user)
        channelID = await self.db.guilds.get_channel(user.guild, "assassins")
        embed = discord.Embed(
            title="Assassins Announcement",
            description=f"{player.name ({user.mention})} has been eliminated.",
            color=EmbedColors.RED,
        )

        await self.bot.get_channel(channelID).send(embed=embed)

    @app_commands.command(
        name="register", description="Create and link your Assassin profile."
    )
    @app_commands.describe(
        name="Your Full Name",
        email="TAMU Email Address",
        photo_url="Link To Your Headshot Photo",
    )
    async def register(
        self, interaction: discord.Interaction, name: str, email: str, photo_url: str
    ):
        """Register for the Assassin game."""
        # Check if the user has already registered
        if await self.db.assassins.get_player_by_discord_id(interaction.user):
            embed = discord.Embed(
                title="Register",
                description="You have already registered.",
                color=EmbedColors.RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Validate Name
        if not name or not re.match(r"^[a-zA-Z\s]+$", name):
            embed = discord.Embed(
                title="Register",
                description="Invalid name. Please provide your full name (only letters and spaces).",
                color=EmbedColors.RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Validate TAMU email
        if not re.match(r"^[\w\.-]+@tamu\.edu$", email):
            embed = discord.Embed(
                title="Register",
                description="Please provide a valid Texas A&M University email (must end with @tamu.edu).",
                color=EmbedColors.RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Validate URL
        if not await validImageURL(photo_url):
            embed = discord.Embed(
                title="Register",
                description="The Photo URL provided is not a valid image. Please provide a valid link to your profile photo.",
                color=EmbedColors.RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Register the player
        await self.db.assassins.add_player(name, email, interaction.user, photo_url)

        embed = discord.Embed(
            title="Register",
            description=f"Successfully registered as an Assassin!",
            color=EmbedColors.GREEN,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="unregister", description="Unlink your Assassins profile."
    )
    async def unregister(self, interaction: discord.Interaction):
        """Unregister from the Assassin game."""
        # Check if the user has already registered
        if not await self.db.assassins.get_player_by_discord_id(interaction.user):
            embed = discord.Embed(
                title="Unregister",
                description="You have not registered.",
                color=EmbedColors.RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Confirm the user wants to unregister
        embed = discord.Embed(
            title="Are You Sure?",
            description="This will permanently delete your profile and you will not be able to participate in the game unless you recreate a profile.",
            color=EmbedColors.PRIMARY,
        )
        confirm = ConfirmationView(
            timeout=60.0, authorID=interaction.user.id, delete_after=False
        )
        await interaction.response.send_message(
            embed=embed, view=confirm, ephemeral=True
        )
        confirm.message = await interaction.original_response()
        await confirm.wait()

        # If the user confirms, unregister them
        if confirm.value:
            await self.db.assassins.delete_player_by_discord_id(interaction.user)
            embed = discord.Embed(
                title="Unregister",
                description="Successfully unregistered from the Assassins game.",
                color=EmbedColors.GREEN,
            )
            await (await interaction.original_response()).edit(embed=embed, view=None)

    @app_commands.command(name="join", description="Join the Assassins game.")
    async def join(self, interaction: discord.Interaction):
        """Join the Assassin game."""
        # Check if the user has already registered
        player = await self.db.assassins.get_player_by_discord_id(interaction.user)
        if not player:
            embed = discord.Embed(
                title="Join",
                description="You are not a registered player. Please use the /register command first.",
                color=EmbedColors.RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # If the game has started, set the player status to spectator
        if self.started:
            embed = discord.Embed(
                title="Join",
                description="The game has already started. Please wait for the game to end before joining.",
                color=EmbedColors.RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # If the game has not started, set the player status to alive
        await self.db.assassins.set_player_status(interaction.user, PlayerStatus.ALIVE)
        embed = discord.Embed(
            title="Join",
            description="Successfully joined the Assassins game. The game will start soon.",
            color=EmbedColors.GREEN,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="leave", description="Leave the Assassins game.")
    async def leave(self, interaction: discord.Interaction):
        """Leave the Assassin game."""
        # Check if the user has already registered
        player = await self.db.assassins.get_player_by_discord_id(interaction.user)
        if not player:
            embed = discord.Embed(
                title="Leave",
                description="You are not a registered player. Please use the /register command first.",
                color=EmbedColors.RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # If the user is dead, they cannot leave the game
        if (
            player.status == PlayerStatus.DEAD
            or player.status == PlayerStatus.SPECTATOR
        ):
            embed = discord.Embed(
                title="Leave",
                description="You are already dead and cannot leave the game.",
                color=EmbedColors.RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # If game has not started, set the player status to spectator
        if not self.started:
            await self.db.assassins.set_player_status(
                interaction.user, PlayerStatus.SPECTATOR
            )
            embed = discord.Embed(
                title="Leave",
                description="Successfully left the Assassins game.",
                color=EmbedColors.GREEN,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # If the game has started, set the player status to dead after confirming
        embed = discord.Embed(
            title="Are You Sure?",
            description="This will mark you as dead in the game. Are you sure you want to leave?",
            color=EmbedColors.PRIMARY,
        )
        confirm = ConfirmationView(
            timeout=60.0, authorID=interaction.user.id, delete_after=False
        )
        await interaction.response.send_message(
            embed=embed, view=confirm, ephemeral=True
        )
        confirm.message = await interaction.original_response()
        await confirm.wait()

        # If the user confirms, set their status to dead
        if confirm.value:
            await self.db.assassins.set_player_status(
                interaction.user, PlayerStatus.DEAD
            )
            embed = discord.Embed(
                title="Leave",
                description="You have forfeitted the current game and now declared dead.",
                color=EmbedColors.GREEN,
            )
            await (await interaction.original_response()).edit(embed=embed)

            # Announce the player's death
            embed = discord.Embed(
                title="Assassins Announcement",
                description=f"{player.name} has forfeitted the game and is now dead.",
                color=EmbedColors.PRIMARY,
            )

    @app_commands.command(name="start", description="Start the Assassins game.")
    async def start(self, interaction: discord.Interaction):
        """Start the Assassin game."""
        # Check if the guild has an Assassins channel set
        guildID = interaction.guild.id
        channelID = await self.db.guilds.get_channel(interaction.guild, "assassins")
        if not channelID:
            embed = discord.Embed(
                title="Start",
                description="The Assassins channel has not been set for this server. Please set the channel before starting the game.",
                color=EmbedColors.RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Check if the game has already started
        if self.started.get(guildID, False):
            embed = discord.Embed(
                title="Start",
                description="The game has already started.",
                color=EmbedColors.RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        self.started[guildID] = True
        await self.db.assassins.set_game_state(guildID, True)

        embed = discord.Embed(
            title="Assassins Game Started!",
            description="The game has officially started. Best of luck to everyone!",
            color=EmbedColors.GREEN,
        )

        # Send the announcement with @everyone mention
        await interaction.response.send_message(
            content="@everyone",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(everyone=True),
        )

    @app_commands.command(name="end", description="End the Assassins game.")
    async def end(self, interaction: discord.Interaction):
        """End the Assassin game."""
        # Check if the game has already ended
        guildID = interaction.guild.id
        if not self.started.get(guildID, False):
            embed = discord.Embed(
                title="End",
                description="The game has not started yet.",
                color=EmbedColors.RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        self.started[guildID] = False
        await self.db.assassins.set_game_state(guildID, False)

        # Assign all players to spectators
        players = await self.db.assassins.get_all_players()
        for player in players:
            await self.db.assassins.set_player_status(
                interaction.guild.get_member(player.discordID), PlayerStatus.SPECTATOR
            )

        # Send the announcement with @everyone mention
        embed = discord.Embed(
            title="Assassins Game Ended!",
            description="The game has officially ended. Thank you for playing!",
            color=EmbedColors.GREEN,
        )
        await interaction.response.send_message(
            content="@everyone",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(everyone=True),
        )

    @app_commands.command(name="profile", description="View an Assassin's profile.")
    @app_commands.describe(target="Discord User")
    async def profile(self, interaction: discord.Interaction, target: discord.Member):
        """View an Assassin's profile."""
        # Get the player's profile
        player = await self.db.assassins.get_player_by_discord_id(target)
        if not player:
            embed = discord.Embed(
                title="Profile",
                description="This user has not registered for the Assassins game.",
                color=EmbedColors.RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Create the profile embed
        embed = discord.Embed(
            title=f"{player.name}'s Profile",
            description=f"**Status:** {player.status}\n**Kills:** {player.kills}\n**Deaths:** {player.deaths}\n**Wins:** {player.wins}\n**Games Played:** {player.gamesPlayed}",
            color=EmbedColors.PRIMARY,
        )
        try:
            embed.set_thumbnail(url=player.photoURL)
        except:
            pass

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Assassins(bot))
