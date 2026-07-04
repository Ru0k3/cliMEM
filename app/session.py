from pathlib import Path

from .filter import clear_chat_log, get_chat_log, process_session
from .memory import get_dataset_name, improve_memory, store_memory
from .storage import end_session, get_current_session


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