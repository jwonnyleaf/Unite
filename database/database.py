import aiosqlite
from typing import Any, Optional, Tuple
from collections import namedtuple


class Database:
    def __init__(self, dbName: str):
        self.dbName = dbName

    @staticmethod
    async def _fetch(cursor: aiosqlite.Cursor, mode: str) -> Optional[Any]:
        """Fetch the result and return it as a namedtuple if data exists."""
        if mode == "one":
            row = await cursor.fetchone()
            if row:
                return Database._row_to_namedtuple(cursor, row)
        elif mode == "many":
            rows = await cursor.fetchmany()
            if rows:
                return [Database._row_to_namedtuple(cursor, row) for row in rows]
        elif mode == "all":
            rows = await cursor.fetchall()
            if rows:
                return [Database._row_to_namedtuple(cursor, row) for row in rows]
        return None

    @staticmethod
    def _row_to_namedtuple(cursor: aiosqlite.Cursor, row: Tuple) -> namedtuple:
        """Convert a database row into a namedtuple using cursor column descriptions."""
        columns = [col[0] for col in cursor.description]

        RowTuple = namedtuple("RowTuple", columns)
        return RowTuple(*row)

    async def connect(self) -> aiosqlite.Connection:
        """Connect to the database and return the connection object."""
        return aiosqlite.connect(self.dbName)

    async def execute(
        self,
        query: str,
        values: Tuple = (),
        *,
        fetch: str = None,
        commit: bool = False,
        conn: aiosqlite.Connection = None
    ) -> Optional[Any]:
        """Execute a query and return the result."""
        async with aiosqlite.connect(self.dbName) as conn:
            cursor = await conn.cursor()
            await cursor.execute(query, values)

            if fetch is not None:
                result = await self._fetch(cursor, fetch)
            else:
                result = None

            if commit:
                await conn.commit()

            await cursor.close()
            if conn is None:
                await conn.close()

            return result

    async def run(
        self, query: str, values: Tuple = (), conn: aiosqlite.Connection = None
    ) -> None:
        """Execute a query and commit the changes."""
        await self.execute(query, values, commit=True, conn=conn)
