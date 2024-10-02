from __future__ import annotations

from typing import TYPE_CHECKING, Union, Any, Optional
import discord
from discord.ext import commands

if TYPE_CHECKING:
    from bot import UniteBot


class Context(commands.Context):
    channel: Union[
        discord.VoiceChannel, discord.TextChannel, discord.Thread, discord.DMChannel
    ]
    prefix: str
    command: commands.Command[Any, ..., Any]
    bot: UniteBot

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class GuildContext(Context):
    author: discord.Member
    guild: discord.Guild
    channel: Union[discord.VoiceChannel, discord.TextChannel, discord.Thread]
    me: discord.Member
    prefix: str


class ConfirmationView(discord.ui.View):
    def __init__(self, *, timeout: float, authorID: int, delete_after: bool) -> None:
        super().__init__(timeout=timeout)
        self.value: Optional[bool] = None
        self.authorID = authorID
        self.delete_after = delete_after
        self.message: Optional[discord.Message] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user.id == self.authorID:
            return True
        return False

    async def on_timeout(self) -> None:
        """Handle the view's timeout event."""
        if self.delete_after and self.message:
            await self.message.delete()

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.value = True
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_response()

        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_response()

        self.stop()
