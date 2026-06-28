chat_log = []


def add_message(role: str, content: str):
    """
    Add a message to the in-memory session log.
    """

    chat_log.append(
        {
            "role": role,
            "content": content,
        }
    )


def get_chat_log():
    """
    Return the complete session log.
    """

    return chat_log


def clear_chat_log():
    """
    Clear the session log.
    """

    chat_log.clear()


def process_session():
    """
    Placeholder for Member 3.

    For now just print the collected conversation.
    """

    print("\n========== SESSION ==========\n")

    for message in chat_log:
        print(f"[{message['role'].upper()}]")
        print(message["content"])
        print()

    print("=============================\n")