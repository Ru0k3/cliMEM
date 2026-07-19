"""session.py — Session lifecycle and in-memory state.

This module owns all session-global state (_session_name, current project
context, _last_activity).  Persistence is delegated to storage.py, which
this module calls for SQLite reads/writes only.
"""

import asyncio
import time
from datetime import datetime
from . import storage as _storage
from .filter import clear_chat_log, get_chat_log, process_session
from .memory import get_dataset_name, improve_memory, store_memory
from .utils import get_cwd

CHECK_INTERVAL_SECONDS = 30
IDLE_TIMEOUT_SECONDS = 10  # keep short while testing; raise once verified

# ── Session identity state ────────────────────────────────────────────────────

_session_name: str | None = None
_working_directory: str | None = None
_cli_tool: str | None = None
_provider_name: str | None = None
_model: str | None = None
_api_key_fingerprint: str | None = None

_last_activity: float | None = None


# ── Public accessors ──────────────────────────────────────────────────────────

def get_current_session() -> str | None:
    """Return the active session name, or None if no session is running."""
    return _session_name


def mark_activity() -> None:
    """Record the timestamp of the most recent chat activity."""
    global _last_activity
    _last_activity = time.time()


# ── Session lifecycle ─────────────────────────────────────────────────────────

def start_session(
    working_directory: str,
    cli_tool: str,
    provider_name: str,
    model: str,
    api_key_fingerprint: str,
) -> None:
    """Begin a new session, persisting it to the database."""
    global _session_name, _working_directory, _cli_tool
    global _provider_name, _model, _api_key_fingerprint

    _session_name = datetime.now().strftime("%Y%m%d_%H%M%S")
    _working_directory = working_directory
    _cli_tool = cli_tool
    _provider_name = provider_name
    _model = model
    _api_key_fingerprint = api_key_fingerprint

    _storage.insert_session(
        session_name=_session_name,
        working_directory=working_directory,
        cli_tool=cli_tool,
        provider_name=provider_name,
        model=model,
        api_key_fingerprint=api_key_fingerprint,
        started_at=datetime.now().isoformat(),
    )

    print(f"✓ Session started : {_session_name}")
    print(f"✓ Project         : {working_directory}")
    print(f"✓ Provider        : {provider_name}")
    print(f"✓ Model           : {model}")


def ensure_session(
    working_directory: str,
    cli_tool: str,
    provider_name: str,
    model: str,
    api_key_fingerprint: str,
) -> str | None:
    """Ensure a session exists and return a rotation reason if any parameter changed."""
    if _session_name is None:
        start_session(
            working_directory,
            cli_tool,
            provider_name,
            model,
            api_key_fingerprint,
        )
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

    return reason


def end_session(ended_reason: str = "normal_shutdown") -> None:
    """End the current session and record it in the database."""
    global _session_name, _working_directory, _cli_tool
    global _provider_name, _model, _api_key_fingerprint

    if _session_name is None:
        return

    _storage.update_session_end(
        session_name=_session_name,
        ended_at=datetime.now().isoformat(),
        ended_reason=ended_reason,
    )

    print(f"✓ Session ended : {_session_name} ({ended_reason})")

    _session_name = None
    _working_directory = None
    _cli_tool = None
    _provider_name = None
    _model = None
    _api_key_fingerprint = None


# ── Idle detection ────────────────────────────────────────────────────────────

async def idle_watcher() -> None:
    """Background task that ends the session after IDLE_TIMEOUT_SECONDS of inactivity."""
    global _last_activity

    while True:
        try:
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)

            if _session_name is None:
                continue
            if _last_activity is None:
                continue

            idle_for = time.time() - _last_activity
            if idle_for >= IDLE_TIMEOUT_SECONDS:
                print(f"✓ Idle for {int(idle_for)}s, ending session")
                await save_current_session("idle_timeout")
                _last_activity = None

        except asyncio.CancelledError:
            break


# ── Save & flush ──────────────────────────────────────────────────────────────

async def save_current_session(reason: str) -> None:
    """Extract facts from the session log, store them in Cognee, then end the session."""
    messages = get_chat_log()

    if not messages:
        end_session(reason)
        return

    raw_chat = "\n".join(
        f"{message['role']}: {message['content']}"
        for message in messages
    )

    if _session_name is None:
        clear_chat_log()
        return

    facts = process_session(raw_chat, str(get_cwd()), _session_name)
    dataset_name = get_dataset_name(str(get_cwd()))

    print(f"[DEBUG] save_current_session called, reason={reason}, facts extracted={facts}")

    try:
        await store_memory(facts, dataset_name)
        await improve_memory(dataset_name)
        print("✓ Session memory saved")
    finally:
        clear_chat_log()
        end_session(reason)
