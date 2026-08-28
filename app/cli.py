import argparse
import asyncio

import uvicorn

from app.agents import AGENTS, CLIMEM_BASE_URL
from app.agent_handlers import HANDLERS
from app.storage import get_recent_sessions, init_database, close_database
from app.utils import get_cwd


def cmd_start():
    from app.config import (
        CLI_TOOL,
        MODEL_MAP,
        PROVIDER_BASE_URL,
        PROVIDER_NAME,
    )
    from app.display import render_banner

    print(render_banner(
        version="0.1.0",
        provider_name=PROVIDER_NAME,
        provider_base_url=PROVIDER_BASE_URL,
        model_proxy=MODEL_MAP.get("proxy", ""),
        host="127.0.0.1",
        port=8000,
        cli_tool=CLI_TOOL,
    ))

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


async def _forget_task(dataset_name: str) -> None:
    """Async helper to run the forget workflow."""
    from app.memory import ensure_cognee_connection, forget_memory

    await ensure_cognee_connection()
    await forget_memory(dataset_name)


def cmd_forget(yes: bool):
    from app.memory import get_dataset_name

    working_directory = str(get_cwd())
    dataset_name = get_dataset_name(working_directory)

    if not yes:
        confirm = input(
            f"This will permanently delete all remembered context for "
            f"{working_directory}\n({dataset_name}). Continue? [y/N] "
        )
        if confirm.strip().lower() != "y":
            print("Aborted.")
            return

    asyncio.run(_forget_task(dataset_name))
    print(f"✓ Memory forgotten for {working_directory}")


def cmd_history(limit: int):
    from app.display import render_history_table

    init_database()
    try:
        rows = get_recent_sessions(limit=limit)
    finally:
        close_database()

    print(render_history_table(rows))


def cmd_graph(dataset: str | None, output: str | None, open_browser: bool):
    """Generate the knowledge-graph HTML view for this project's memory."""
    import webbrowser
    from pathlib import Path

    from app.memory import ensure_cognee_connection, get_dataset_name
    from app.utils import get_cwd

    working_directory = str(get_cwd())
    dataset_name = dataset or get_dataset_name(working_directory)
    out_path = Path(output) if output else Path.cwd() / "graph_after_recall.html"

    async def run():
        await ensure_cognee_connection()
        from cognee.api.v1.visualize.visualize import visualize_graph
        await visualize_graph(str(out_path), dataset=dataset_name)

    asyncio.run(run())

    print(f"✓ Graph written to {out_path}")
    if open_browser:
        webbrowser.open(out_path.as_uri())


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

    start = subparsers.add_parser("start", help="Run the memory proxy server")
    start.add_argument("--banner-only", action="store_true",
                       help="Print the startup panel and exit (debug)")

    configure = subparsers.add_parser(
        "configure",
        help="Route an agent through cliMEM (backs up config)",
    )
    configure.add_argument("agent", choices=AGENTS.keys())

    restore = subparsers.add_parser(
        "restore",
        help="Restore an agent's original config",
    )
    restore.add_argument("agent", choices=AGENTS.keys())

    forget = subparsers.add_parser(
        "forget",
        help="Delete all remembered context for the current project directory.",
    )
    forget.add_argument("--yes", action="store_true",
                        help="Skip the confirmation prompt.")

    history = subparsers.add_parser(
        "history",
        help="Show recent sessions across all projects.",
    )
    history.add_argument("--limit", type=int, default=5)

    graph = subparsers.add_parser(
        "graph",
        help="Render the project knowledge graph to HTML.",
    )
    graph.add_argument("--dataset", default=None,
                       help="Dataset name (default: current project).")
    graph.add_argument("--output", "-o", default=None,
                       help="Output HTML path "
                            "(default: ./graph_after_recall.html).")
    graph.add_argument("--open", action="store_true", dest="open_browser",
                       help="Open the generated file in a browser.")

    args = parser.parse_args()

    if args.command == "start":
        if getattr(args, "banner_only", False):
            from app.config import (
                CLI_TOOL,
                MODEL_MAP,
                PROVIDER_BASE_URL,
                PROVIDER_NAME,
            )
            from app.display import render_banner
            print(render_banner(
                version="0.1.0",
                provider_name=PROVIDER_NAME,
                provider_base_url=PROVIDER_BASE_URL,
                model_proxy=MODEL_MAP.get("proxy", ""),
                host="127.0.0.1",
                port=8000,
                cli_tool=CLI_TOOL,
            ))
            return
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

    if args.command == "graph":
        cmd_graph(args.dataset, args.output, args.open_browser)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
