import asyncio
import time
from pathlib import Path

from .filter import clear_chat_log, get_chat_log, process_session
from .memory import get_dataset_name, improve_memory, store_memory
from .storage import end_session, get_current_session

CHECK_INTERVAL_SECONDS = 30
IDLE_TIMEOUT_SECONDS = 10  # keep short while testing; raise once verified

_last_activity: float | None = None


def mark_activity() -> None:
    """Record the timestamp of the most recent chat activity."""
    global _last_activity
    _last_activity = time.time()


async def idle_watcher():
    global _last_activity
    while True:
        try:
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)

            if get_current_session() is None:
                continue
            if _last_activity is None:
                continue

            idle_for = time.time() - _last_activity
            if idle_for >= IDLE_TIMEOUT_SECONDS:
                print(f"✓ Idle for {int(idle_for)}s, ending session")
                await save_current_session("idle_timeout")
                _last_activity = None  # prevent repeat-firing on empty log

        except asyncio.CancelledError:
            break


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

    facts = process_session(raw_chat, str(Path.cwd()), session_name)
    dataset_name = get_dataset_name(str(Path.cwd()))

    print(f"[DEBUG] save_current_session called, reason={reason}, facts extracted={facts}")

    try:
        await store_memory(facts, dataset_name)
        await improve_memory(dataset_name)
        print("✓ Session memory saved")
    finally:
        clear_chat_log()
        end_session(reason)