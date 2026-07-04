import argparse
import asyncio
from pathlib import Path

import uvicorn

from app.agents import AGENTS, CLIMEM_BASE_URL
from app.agent_handlers import HANDLERS
from app.storage import get_recent_sessions, init_database, close_database


def cmd_start():
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )


def cmd_configure(agent):
    info = AGENTS[agent]
    HANDLERS[agent]["configure"](
        info["config"],
        CLIMEM_BASE_URL,
    )
    print(f"✓ {info['name']} configured.")


def cmd_restore(agent):
    info = AGENTS[agent]
    HANDLERS[agent]["restore"](
        info["config"],
    )
    print(f"✓ {info['name']} restored.")


def cmd_forget(yes: bool):
    from app.memory import forget_memory, get_dataset_name

    working_directory = str(Path.cwd())
    dataset_name = get_dataset_name(working_directory)

    if not yes:
        confirm = input(
            f"This will permanently delete all remembered context for "
            f"{working_directory}\n({dataset_name}). Continue? [y/N] "
        )
        if confirm.strip().lower() != "y":
            print("Aborted.")
            return

    asyncio.run(forget_memory(dataset_name))
    print(f"✓ Memory forgotten for {working_directory}")


def cmd_history(limit: int):
    init_database()
    try:
        rows = get_recent_sessions(limit=limit)
    finally:
        close_database()

    if not rows:
        print("No sessions recorded yet.")
        return

    for (
        session_name,
        working_directory,
        cli_tool,
        provider_name,
        model,
        started_at,
        ended_at,
        ended_reason,
    ) in rows:
        status = ended_reason or "active"
        timing = f"{started_at} → {ended_at or '...'}"
        print(f"{session_name}  {cli_tool}/{provider_name}/{model}  "
              f"{working_directory}  [{status}]  {timing}")

def main():
    parser = argparse.ArgumentParser(
        prog="climem",
        description="CliMEM - Memory-aware wrapper for CLI coding agents",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="CliMEM 0.1.0",
    )

    subparsers = parser.add_subparsers(dest="command")

    # start
    subparsers.add_parser("start")

    # configure
    configure = subparsers.add_parser("configure")
    configure.add_argument(
        "agent",
        choices=AGENTS.keys(),
    )

    # restore
    restore = subparsers.add_parser("restore")
    restore.add_argument(
        "agent",
        choices=AGENTS.keys(),
    )

    # forget
    forget = subparsers.add_parser(
        "forget",
        help="Delete all remembered context for the current project directory.",
    )
    forget.add_argument(
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt.",
    )

    # history
    history = subparsers.add_parser(
        "history",
        help="Show recent sessions across all projects.",
    )
    history.add_argument(
        "--limit",
        type=int,
        default=5,
    )

    args = parser.parse_args()

    if args.command == "start":
        cmd_start()
        return

    if args.command == "configure":
        cmd_configure(args.agent)
        return

    if args.command == "restore":
        cmd_restore(args.agent)
        return

    if args.command == "forget":
        cmd_forget(args.yes)
        return

    if args.command == "history":
        cmd_history(args.limit)
        return

    parser.print_help()


if __name__ == "__main__":
    main()