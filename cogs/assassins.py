from __future__ import annotations

import os
from typing import TYPE_CHECKING
import re

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from utils.context import ConfirmationView
from utils.constants import EmbedColors, GuildChannelTypes
from utils.utils import validImageURL, sendAnnouncement
from database.assassins import PlayerStatus

if TYPE_CHECKING:
    from bot import UniteBot
    from utils.context import Context, GuildContext


class Assassins(commands.Cog, name="assassin"):
    def __init__(self, bot: UniteBot):
        self.bot = bot
        self.db = bot.db
        self.started = {}
        self.lobby = {}

    async def cog_load(self):
        guilds = await self.db.guilds.get_all_guilds()
        for guild in guilds:
            self.started[guild.guildID] = guild.assassinsStarted
            players = await self.db.assassins.get_all_players("guildID", guild.guildID)
            self.lobby[guild.guildID] = []
            for player in players:
                if player.status == PlayerStatus.ALIVE.value:
                    user = await self.bot.fetch_user(player.discordID)
                    if user:
                        self.lobby[guild.guildID].append(user)

    @commands.Cog.listener()
    async def on_player_death(self, user: discord.Member):
        """Announce when a player is eliminated."""
        player = await self.db.assassins.get_player_by_discord_id(user)
        embed = discord.Embed(
            title="Assassins Announcement",
            description=f"{player.name} ({user.mention}) has been eliminated. {len(self.lobby[user.guild.id])} players remain.",
            color=EmbedColors.RED,
        )
        self.lobby[user.guild.id].remove(user)
        await sendAnnouncement(
            self, user.guild, GuildChannelTypes.ASSASSINS, embed, everyone=True
        )

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
        await self.db.assassins.add_player(
            interaction.guild.id, name, email, interaction.user, photo_url
        )

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
        guild: discord.Guild = interaction.guild
        user: discord.Member = interaction.user

        # Check if the user has already registered
        player = await self.db.assassins.get_player_by_discord_id(user)
        if not player:
            embed = discord.Embed(
                title="Join",
                description="You are not a registered player. Please use the /register command first.",
                color=EmbedColors.RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # If the game has started, set the player status to spectator
        if self.started[interaction.guild.id]:
            embed = discord.Embed(
                title="Asssassins Join",
                description="The game has already started. Please wait for the game to end before joining.",
                color=EmbedColors.RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # If the player is already in the lobby, do not add them again
        if interaction.user in self.lobby[guild.id]:
            embed = discord.Embed(
                title="Assassins Join",
                description="You are already in the lobby.",
                color=EmbedColors.RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # If the game has not started, allow the player to join
        if guild.id not in self.lobby:
            self.lobby[guild.id] = []

        self.lobby[guild.id].append(user)
        await self.db.assassins.set_player_status(user, PlayerStatus.ALIVE)
        embed = discord.Embed(
            title="Assassins Join",
            description="Successfully joined the Assassins lobby. The game will start soon.",
            color=EmbedColors.GREEN,
        )

        # Announce the player's entry
        announceEmbed = discord.Embed(
            title="Assassins Announcement",
            description=f"{player.name} ({user.mention}) has joined the game. {len(self.lobby[guild.id])} players are waiting in the lobby.",
            color=EmbedColors.PRIMARY,
        )

        await sendAnnouncement(self, guild, GuildChannelTypes.ASSASSINS, announceEmbed)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="leave", description="Leave the Assassins game.")
    async def leave(self, interaction: discord.Interaction):
        """Leave the Assassin game/lobby."""
        guild = interaction.guild
        user = interaction.user

        # Check if the user has already registered
        player = await self.db.assassins.get_player_by_discord_id(user)
        if not player:
            embed = discord.Embed(
                title="Assassins Leave",
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
                title="Assassins Leave",
                description="You are already dead and cannot leave the game.",
                color=EmbedColors.RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # If user is not in the lobby, they cannot leave
        if guild.id not in self.lobby or user not in self.lobby[guild.id]:
            embed = discord.Embed(
                title="Assassins Leave",
                description="You are not in the Assassins lobby.",
                color=EmbedColors.RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # If game has not started and the user is in the lobby, remove them
        if not self.started[guild.id] and user in self.lobby[guild.id]:
            self.lobby[guild.id].remove(user)
            await self.db.assassins.set_player_status(user, PlayerStatus.SPECTATOR)
            embed = discord.Embed(
                title="Assassins Leave",
                description="You have been removed from the Assassins lobby.",
                color=EmbedColors.GREEN,
            )

            # Announce the player's removal
            announceEmbed = discord.Embed(
                title="Assassins Announcement",
                description=f"{player.name} ({user.mention}) has left the lobby. {len(self.lobby[guild.id])} players waiting now.",
                color=EmbedColors.PRIMARY,
            )
            await sendAnnouncement(
                self, guild, GuildChannelTypes.ASSASSINS, announceEmbed
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # If the game has started, set the player status to dead after confirming
        embed = discord.Embed(
            title="Are You Sure?",
            description="This will mark you as dead in the game. Are you sure you want to leave?",
            color=EmbedColors.PRIMARY,
        )
        confirm = ConfirmationView(timeout=60.0, authorID=user.id, delete_after=False)
        await interaction.response.send_message(
            embed=embed, view=confirm, ephemeral=True
        )
        confirm.message = await interaction.original_response()
        await confirm.wait()

        # If the user confirms, set their status to dead
        if confirm.value:
            await self.db.assassins.set_player_status(user, PlayerStatus.DEAD)
            embed = discord.Embed(
                title="Assassins Leave",
                description="You have forfeitted the current game and now declared dead.",
                color=EmbedColors.GREEN,
            )
            await (await interaction.original_response()).edit(embed=embed, view=None)

            # Announce the player's death
            self.bot.dispatch("player_death", user)

    @app_commands.command(name="start", description="Start the Assassins game.")
    async def start(self, interaction: discord.Interaction):
        """Start the Assassin game."""
        # Check if the guild has an Assassins channel set
        guild = interaction.guild
        guildID = guild.id
        channelID = await self.db.guilds.get_channel(interaction.guild, "assassins")
        if not channelID:
            embed = discord.Embed(
                title="Assassins Start",
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

        announceEmbed = discord.Embed(
            title="Assassins Game Started!",
            description="The game has officially started. Best of luck to everyone!",
            color=EmbedColors.GREEN,
        )

        # Send the announcement with @everyone mention
        await sendAnnouncement(
            self, guild, GuildChannelTypes.ASSASSINS, announceEmbed, everyone=True
        )
        await interaction.response.send_message(embed=announceEmbed, ephemeral=True)

    @app_commands.command(name="end", description="End the Assassins game.")
    async def end(self, interaction: discord.Interaction):
        """End the Assassin game."""
        # Check if the game has already ended
        guild = interaction.guild
        guildID = guild.id

        if not self.started.get(guildID, False):
            embed = discord.Embed(
                title="Assassins End",
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
        self.lobby[guildID] = []

        # Send the announcement with @everyone mention
        embed = discord.Embed(
            title="Assassins Game Ended!",
            description="The game has officially ended. Thank you for playing!",
            color=EmbedColors.GREEN,
        )
        await sendAnnouncement(
            self, guild, GuildChannelTypes.ASSASSINS, embed, everyone=True
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="status", description="View the Assassins game status.")
    async def status(self, interaction: discord.Interaction):
        """View the Assassin game status."""
        guild = interaction.guild
        guildID = guild.id

        embed = discord.Embed(
            title="Assassins Game Status",
            description=f"""
            **Game Status:** {'Started' if self.started.get(guildID, False) else 'Not Started'}
            **Players in Lobby:** {len(self.lobby.get(guildID, []))}
            **Target:** {None}""",
            color=EmbedColors.PRIMARY,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="profile", description="View an Assassin's profile.")
    @app_commands.describe(target="Discord User")
    async def profile(
        self, interaction: discord.Interaction, target: discord.Member = None
    ):
        """View an Assassin's profile."""
        # Get the player's profile
        if not target:
            target = interaction.user

        player = await self.db.assassins.get_player_by_discord_id(target)
        if not player:
            embed = discord.Embed(
                title="Profile",
                description=f"{target.mention} has not registered for the Assassins game.",
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
