import discord
from database.database import Database


class Guilds:
    def __init__(self, db: Database):
        self._db = db

    async def create_table(self) -> None:
        conn = await self._db.connect()
        query = f"""
            CREATE TABLE IF NOT EXISTS guilds (
                guildID BIGINT PRIMARY KEY,
                prefix TEXT NOT NULL DEFAULT '!',
                assassinsChannelID BIGINT,
                assassinsStarted BOOLEAN DEFAULT FALSE
            );
            """

        await self._db.run(
            query,
            conn=conn,
        )
        await conn.close()

    async def add_guild(self, guildID: int) -> None:
        """Add a guild to the database."""
        conn = await self._db.connect()
        await self._db.run(
            f"INSERT INTO guilds (guildID) VALUES (?);",
            (guildID,),
            conn=conn,
        )
        await conn.close()

    async def get_guild(self, guildID: int) -> bool:
        """Check if the guild exists in the database."""
        query = f"SELECT guildID FROM guilds WHERE guildID = ?;"
        result = await self._db.execute(query, (guildID,), fetch="one")

        return result

    async def get_all_guilds(self):
        """Get all guilds in the database."""
        query = f"SELECT * FROM guilds;"
        result = await self._db.execute(query, fetch="all")

        return result

    async def get_prefix(self, guild: discord.Guild) -> str:
        """Get the prefix for the specified guild."""
        query = f"SELECT prefix FROM guilds WHERE guildID = ?;"
        result = await self._db.execute(query, (guild.id,), fetch="one")

        return result.prefix if result else "!"

    async def set_prefix(self, guild: discord.Guild, prefix: str) -> None:
        """Set the prefix for the specified guild."""
        query = f"UPDATE guilds SET prefix = ? WHERE guildID = ?;"
        await self._db.execute(query, (prefix, guild.id), commit=True)

    async def get_channel(self, guild: discord.Guild, channelType: str) -> int:
        """Get the channel ID for the specified guild."""
        channelType = f"{channelType}ChannelID"
        print(channelType)
        query = f"SELECT {channelType} FROM guilds WHERE guildID = ?;"
        print(query)
        result = await self._db.execute(query, (guild.id,), fetch="one")
        return result[0] if result else None

    async def set_channel(
        self, guild: discord.Guild, channelType: str, channelID: discord.TextChannel
    ) -> None:
        """Set the channel ID for the specified guild."""
        channelType = f"{channelType}ChannelID"
        query = f"UPDATE guilds SET {channelType} = ? WHERE guildID = ?;"
        await self._db.execute(query, (channelID.id, guild.id), commit=True)

    async def get_allowed_columns(self):
        """Get the allowed columns dynamically from the database schema."""
        query = """
        PRAGMA table_info(guilds);  -- This query fetches the column names of the guilds table
        """
        result = await self._db.execute(query, fetch="all")

        allowed_columns = [row["name"] for row in result]
        return allowed_columns
