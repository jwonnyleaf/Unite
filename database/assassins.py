from enum import Enum
import discord
from database.database import Database

TABLE_NAME = "assassins"


class PlayerStatus(Enum):
    SPECTATOR = "Spectator"
    ALIVE = "Alive"
    DEAD = "Dead"


class Assassins:
    def __init__(self, db: Database):
        self._db = db
        self.status = PlayerStatus

    async def create_table(self) -> None:
        conn = await self._db.connect()
        query = f"""
            CREATE TABLE IF NOT EXISTS assassins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guildID INTEGER NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                discordID INTEGER NOT NULL UNIQUE,
                photoURL TEXT,
                wins INTEGER DEFAULT 0,
                kills INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0,
                gamesPlayed INTEGER DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'Spectator'
            );
            """

        await self._db.run(
            query,
            conn=conn,
        )
        await conn.close()

    async def set_game_state(self, guildID: int, state: bool):
        """Set the current Guild's Assassins game state."""
        conn = await self._db.connect()
        await self._db.run(
            f"UPDATE guilds SET assassinsStarted = ? WHERE guildID = ?;",
            (state, guildID),
            conn=conn,
        )
        await conn.close()

    async def add_player(
        self,
        guildID: int,
        name: str,
        email: str,
        discordID: discord.Member,
        photoURL: str,
    ):
        """Add a player to the database."""
        conn = await self._db.connect()

        # Check if the player already exists
        player = await self.get_player_by_discord_id(discordID)

        if player is None:
            await self._db.run(
                f"""INSERT INTO {TABLE_NAME} (guildID, name, email, discordID, photoURL, status)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    guildID,
                    name,
                    email,
                    discordID.id,
                    photoURL,
                    self.status.SPECTATOR.value,
                ),
                conn=conn,
            )

        await conn.close()

    async def set_player_status(self, discordID: discord.Member, status: PlayerStatus):
        """Set a player's game status."""
        conn = await self._db.connect()
        await self._db.run(
            f"UPDATE {TABLE_NAME} SET status = ? WHERE discordID = ?;",
            (status.value, discordID.id),
        )
        await conn.close()

    async def get_player_by_discord_id(self, player: discord.Member):
        """Get a player by their discord ID."""
        player = await self._db.execute(
            f"SELECT * FROM {TABLE_NAME} WHERE discordID = ?;",
            (player.id,),
            fetch="one",
        )

        return player

    async def get_player_by_email(self, email: str):
        """Get a player by their email."""
        player = await self._db.execute(
            f"SELECT * FROM {TABLE_NAME} WHERE email = ?;",
            (email,),
            fetch="one",
        )

        return player

    async def get_all_players(self, column: str = None, filter: str = None):
        """Get all players from the database."""
        filter = f"WHERE {column} = '{filter}'" if filter else ""
        players = await self._db.execute(
            f"SELECT * FROM {TABLE_NAME} {filter};",
            fetch="all",
        )

        return players

    async def delete_player_by_discord_id(self, player: discord.Member):
        """Delete a player by their discord ID."""
        conn = await self._db.connect()
        await self._db.run(
            f"DELETE FROM {TABLE_NAME} WHERE discordID = ?;",
            (player.id,),
            conn=conn,
        )
        await conn.close()
