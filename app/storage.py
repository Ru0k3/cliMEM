import sqlite3
from datetime import datetime
from pathlib import Path

# ~/.climem/
APP_DIR = Path.home() / ".climem"

# ~/.climem/sessions.db
DATABASE = APP_DIR / "sessions.db"

connection = None
current_session = None


def init_database():
    """
    Create ~/.climem and sessions.db if they don't exist.
    """

    global connection
    global current_session

    # Create ~/.climem/
    APP_DIR.mkdir(parents=True, exist_ok=True)

    # Open database
    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_name TEXT NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT
        )
        """
    )

    connection.commit()

    current_session = datetime.now().strftime("%d%m%Y_%H%M")

    cursor.execute(
        """
        INSERT INTO sessions (
            session_name,
            started_at
        )
        VALUES (?, ?)
        """,
        (
            current_session,
            datetime.now().isoformat(),
        ),
    )

    connection.commit()

    print(f"✓ Session started: {current_session}")
    print(f"✓ Database: {DATABASE}")


def end_session():
    """
    Save the end timestamp for the current session.
    """

    if connection is None:
        return

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE sessions
        SET ended_at = ?
        WHERE session_name = ?
        """,
        (
            datetime.now().isoformat(),
            current_session,
        ),
    )

    connection.commit()
    connection.close()

    print(f"✓ Session ended: {current_session}")


def get_recent_sessions(limit=3):
    """
    Return the most recent sessions.
    """

    if connection is None:
        return []

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            session_name,
            started_at,
            ended_at
        FROM sessions
        ORDER BY started_at DESC
        LIMIT ?
        """,
        (limit,),
    )

    return cursor.fetchall()