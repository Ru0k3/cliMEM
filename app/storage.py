import sqlite3
from datetime import datetime
from pathlib import Path

APP_DIR = Path.home() / ".climem"
DATABASE = APP_DIR / "sessions.db"

connection = None

_session_name = None
_working_directory = None
_cli_tool = None
_provider_name = None
_model = None
_api_key_fingerprint = None
_last_activity = None


def init_database():
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


def start_session(working_directory, cli_tool, provider_name, model, api_key_fingerprint):
    global _session_name, _working_directory, _cli_tool
    global _provider_name, _model, _api_key_fingerprint

    _session_name = datetime.now().strftime("%Y%m%d_%H%M%S")
    _working_directory = working_directory
    _cli_tool = cli_tool
    _provider_name = provider_name
    _model = model
    _api_key_fingerprint = api_key_fingerprint

    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO sessions (
            session_name, working_directory, cli_tool,
            provider_name, model, api_key_fingerprint, started_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        _session_name, working_directory, cli_tool,
        provider_name, model, api_key_fingerprint,
        datetime.now().isoformat(),
    ))
    connection.commit()

    print(f"✓ Session started : {_session_name}")
    print(f"✓ Project         : {working_directory}")
    print(f"✓ Provider        : {provider_name}")
    print(f"✓ Model           : {model}")


def ensure_session(working_directory, cli_tool, provider_name, model, api_key_fingerprint):
    if _session_name is None:
        start_session(working_directory, cli_tool, provider_name, model, api_key_fingerprint)
        return None

    reason = None

    if working_directory != _working_directory:
        reason = "working_directory_changed"
    elif cli_tool != _cli_tool:
        reason = "cli_tool_changed"
    elif provider_name != _provider_name:
        reason = "provider_changed"
    elif model != _model:
        reason = "model_changed"
    elif api_key_fingerprint != _api_key_fingerprint:
        reason = "api_key_changed"

    if reason:
        return reason
    
    return None

def end_session(ended_reason="normal_shutdown"):
    global _session_name, _working_directory, _cli_tool
    global _provider_name, _model, _api_key_fingerprint

    if connection is None or _session_name is None:
        return

    cursor = connection.cursor()
    cursor.execute("""
        UPDATE sessions
        SET ended_at = ?, ended_reason = ?
        WHERE session_name = ?
    """, (datetime.now().isoformat(), ended_reason, _session_name))
    connection.commit()

    print(f"✓ Session ended : {_session_name} ({ended_reason})")

    _session_name = None
    _working_directory = None
    _cli_tool = None
    _provider_name = None
    _model = None
    _api_key_fingerprint = None


def close_database():
    global connection

    if connection is not None:
        connection.close()
        connection = None


def get_current_session():
    return _session_name
def mark_activity():
    global _last_activity
    _last_activity = datetime.now()


def get_last_activity():
    return _last_activity

def get_recent_sessions(limit=5):
    if connection is None:
        return []

    cursor = connection.cursor()
    cursor.execute("""
        SELECT session_name, working_directory, cli_tool,
               provider_name, model, started_at, ended_at, ended_reason
        FROM sessions
        ORDER BY started_at DESC
        LIMIT ?
    """, (limit,))

    return cursor.fetchall()