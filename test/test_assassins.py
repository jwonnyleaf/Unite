import pytest
from unittest.mock import AsyncMock, MagicMock
from aiosqlite import IntegrityError
from database.assassins import Assassins, PlayerStatus

@pytest.mark.asyncio
async def test_create_table():
    # Mock the database
    mock_db = AsyncMock()
    
    # Initialize the Assassins class
    assassins = Assassins(mock_db)

    # Call create_table and check if it runs successfully
    await assassins.create_table()
    
    # Ensure the execute method was called with the table creation command
    mock_db.execute.assert_called()

@pytest.mark.asyncio
async def test_add_player():
    # Mock the database
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=None)
    assassins = Assassins(mock_db)
    
    # Add a player
    await assassins.add_player("John Doe", "john@example.com", "12345", "photo_url")

    # Assert the SQL insert query was called with the correct values
    mock_db.execute.assert_called_once_with(
        f"INSERT INTO assassins (name, email, discord_id, photo_url, wins, kills, deaths, status) "
        "VALUES (?, ?, ?, ?, 0, 0, 0, ?);",
        ("John Doe", "john@example.com", "12345", "photo_url", PlayerStatus.ALIVE.value)
    )

@pytest.mark.asyncio
async def test_set_player_status():
    # Mock the database
    mock_db = AsyncMock()
    assassins = Assassins(mock_db)

    # Set the player status
    await assassins.set_player_status("12345", PlayerStatus.DEAD.value)

    # Assert the update query was called with the correct arguments
    mock_db.execute.assert_called_once_with(
        f"UPDATE assassins SET status = ? WHERE discord_id = ?;",
        (PlayerStatus.DEAD.value, "12345")
    )

@pytest.mark.asyncio
async def test_get_player_by_discord_id():
    # Mock the database cursor and return a mock player
    mock_cursor = AsyncMock()
    mock_cursor.fetchone = AsyncMock(return_value={"name": "John Doe", "discord_id": "12345"})

    # Mock the database
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_cursor)
    assassins = Assassins(mock_db)

    # Fetch a player by discord_id
    player = await assassins.get_player_by_discord_id("12345")

    # Check if the correct SQL query was made
    mock_db.execute.assert_called_once_with(
        f"SELECT * FROM assassins WHERE discord_id = ?;",
        ("12345",)
    )
    # Ensure the player is correctly returned
    assert player == {"name": "John Doe", "discord_id": "12345"}

@pytest.mark.asyncio
async def test_get_player_by_email():
    # Mock the database cursor and return a mock player
    mock_cursor = AsyncMock()
    mock_cursor.fetchone = AsyncMock(return_value={"name": "John Doe", "email": "john@example.com"})

    # Mock the database
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_cursor)
    assassins = Assassins(mock_db)

    # Fetch a player by email
    player = await assassins.get_player_by_email("john@example.com")

    # Check if the correct SQL query was made
    mock_db.execute.assert_called_once_with(
        f"SELECT * FROM assassins WHERE email = ?;",
        ("john@example.com",)
    )
    # Ensure the player is correctly returned
    assert player == {"name": "John Doe", "email": "john@example.com"}
