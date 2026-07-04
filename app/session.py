from pathlib import Path

from .filter import clear_chat_log, get_chat_log, process_session
from .memory import get_dataset_name, improve_memory, store_memory
from .storage import end_session, get_current_session
from .storage import end_session, get_current_session, mark_activity as _mark_activity
import time

_last_activity: float | None = None

import asyncio
from datetime import datetime

from .storage import (
    end_session,
    get_current_session,
    get_last_activity,
    mark_activity,
)

CHECK_INTERVAL_SECONDS = 60
IDLE_TIMEOUT_SECONDS = 10  # 30 minutes


async def idle_watcher():
    while True:
        try:
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)

            if get_current_session() is None:
                continue

            last_activity = get_last_activity()
            if last_activity is None:
                continue

            idle_for = (datetime.now() - last_activity).total_seconds()

            if idle_for >= IDLE_TIMEOUT_SECONDS:
                print(f"✓ Idle for {int(idle_for)}s, ending session")
                await save_current_session("idle_timeout")

        except asyncio.CancelledError:
            break


def mark_activity():
    _mark_activity()
def mark_activity() -> None:
    """Record the timestamp of the most recent user activity."""
    global _last_activity
    _last_activity = time.time()


def get_last_activity() -> float | None:
    return _last_activity

async def save_current_session(reason: str):
    messages = get_chat_log()

    if not messages:
        end_session(reason)
        return

    raw_chat = "\n".join(
        f"{message['role']}: {message['content']}"
        for message in messages
    )

    session_name = get_current_session()

    if session_name is None:
        clear_chat_log()
        return

    facts = process_session(
        raw_chat,
        str(Path.cwd()),
        session_name,
    )

    dataset_name = get_dataset_name(str(Path.cwd()))

    try:
        await store_memory(
            facts,
            dataset_name,
        )

        await improve_memory(
            dataset_name,
        )

        print("✓ Session memory saved")

    finally:
        clear_chat_log()
        end_session(reason)