"""storage.py — Pure SQLite persistence layer for sessions.

This module owns the database connection and provides low-level CRUD
operations.  It holds NO in-memory session state — that lives in
session.py.  This separation keeps session lifecycle logic and
persistence decoupled.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

APP_DIR = Path.home() / ".climem"
DATABASE = APP_DIR / "sessions.db"

connection = None


def init_database() -> None:
    """Create the database directory and tables if they don't exist."""
    global connection

    APP_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_name TEXT NOT NULL,
            working_directory TEXT NOT NULL,
            cli_tool TEXT NOT NULL,
            provider_name TEXT NOT NULL,
            model TEXT NOT NULL,
            api_key_fingerprint TEXT NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            ended_reason TEXT
        )
    """)

    connection.commit()
    print(f"✓ Database: {DATABASE}")


def insert_session(
    session_name: str,
    working_directory: str,
    cli_tool: str,
    provider_name: str,
    model: str,
    api_key_fingerprint: str,
    started_at: str,
) -> None:
    """Insert a new session row."""
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO sessions (
            session_name, working_directory, cli_tool,
            provider_name, model, api_key_fingerprint, started_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            session_name,
            working_directory,
            cli_tool,
            provider_name,
            model,
            api_key_fingerprint,
            started_at,
        ),
    )
    connection.commit()


def update_session_end(session_name: str, ended_at: str, ended_reason: str) -> None:
    """Record the end time and reason for a session."""
    cursor = connection.cursor()
    cursor.execute(
        """
        UPDATE sessions
        SET ended_at = ?, ended_reason = ?
        WHERE session_name = ?
    """,
        (ended_at, ended_reason, session_name),
    )
    connection.commit()


def close_database() -> None:
    """Close the database connection if open."""
    global connection

    if connection is not None:
        connection.close()
        connection = None


def get_recent_sessions(limit: int = 5) -> list[tuple]:
    """Return the most recent session rows, newest first."""
    if connection is None:
        return []

    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT session_name, working_directory, cli_tool,
               provider_name, model, started_at, ended_at, ended_reason
        FROM sessions
        ORDER BY started_at DESC
        LIMIT ?
    """,
        (limit,),
    )

    return cursor.fetchall()
