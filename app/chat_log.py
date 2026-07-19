"""chat_log.py — In-memory session chat log."""

chat_log: list[dict] = []


def add_message(role: str, content: str) -> None:
    """Add a message to the current session log."""
    chat_log.append({"role": role, "content": content})


def get_chat_log() -> list[dict]:
    """Return the current session log."""
    return chat_log


def clear_chat_log() -> None:
    """Clear the current session log."""
    chat_log.clear()
