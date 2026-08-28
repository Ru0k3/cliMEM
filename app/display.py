"""display.py — Terminal presentation helpers for cliMEM.

Pure standard-library ANSI rendering: startup banner, session-history
table, and small formatting utilities. No external dependencies — every
color degrades gracefully when stdout is not a TTY.
"""

import os
import shutil
import sys
from datetime import datetime


# ─── ANSI plumbing ────────────────────────────────────────────────────────────

def _supports_color() -> bool:
    if os.getenv("NO_COLOR"):
        return False
    if os.getenv("FORCE_COLOR"):
        return True
    return sys.stdout.isatty()


_COLOR = _supports_color()

_RESET = "\033[0m" if _COLOR else ""
_BOLD = "\033[1m" if _COLOR else ""
_DIM = "\033[2m" if _COLOR else ""
_CYAN = "\033[36m" if _COLOR else ""
_GREEN = "\033[32m" if _COLOR else ""
_YELLOW = "\033[33m" if _COLOR else ""
_RED = "\033[31m" if _COLOR else ""
_MAGENTA = "\033[35m" if _COLOR else ""


def bold(text: str) -> str:
    return f"{_BOLD}{text}{_RESET}"


def dim(text: str) -> str:
    return f"{_DIM}{text}{_RESET}"


def green(text: str) -> str:
    return f"{_GREEN}{text}{_RESET}"


def yellow(text: str) -> str:
    return f"{_YELLOW}{text}{_RESET}"


def red(text: str) -> str:
    return f"{_RED}{text}{_RESET}"


def cyan(text: str) -> str:
    return f"{_CYAN}{text}{_RESET}"


def magenta(text: str) -> str:
    return f"{_MAGENTA}{text}{_RESET}"


# ─── Banner ───────────────────────────────────────────────────────────────────

_LOGO = r"""
   _____ _ _       __  __ ___  __  ___
  / ____| (_)     |  \/  |_ _|/ _|/ _ \
 | |     | |_ ___ | \  / || || |_| (_) |
 | |     | | / __|| |\/| || ||  _|\__, |
 | |____| | \__ \| |  | || || |     / /
  \_____|_|_|___/|_|  |_|___|_|    /_/
"""


def render_banner(
    *,
    version: str,
    provider_name: str,
    provider_base_url: str,
    model_proxy: str,
    host: str,
    port: int,
    cli_tool: str,
    extra_lines: list[str] | None = None,
) -> str:
    """Startup panel shown by `climem start` before uvicorn takes over."""
    width = min(shutil.get_terminal_size((80, 24)).columns, 78)
    out: list[str] = []

    def rule(char: str = "─") -> None:
        out.append(dim(char * width))

    out.append(cyan(_LOGO))
    rule("═")
    out.append(f"  {bold('cliMEM')} {dim('v' + version)}   "
               f"{dim('— persistent memory for CLI coding agents')}")
    out.append("")
    out.append(f"  {bold('proxy')}      http://{host}:{port}/v1"
               f"   {dim('(point your agent here)')}")
    out.append(f"  {bold('agent')}      {cli_tool}")
    out.append(f"  {bold('provider')}   {provider_name}  "
               f"{dim(_shorten(provider_base_url, 40))}")
    out.append(f"  {bold('model')}      {_shorten(model_proxy, 46)}")
    for line in extra_lines or []:
        out.append(f"  {line}")
    out.append("")
    out.append(f"  {dim('stop:')} Ctrl+C  "
               f"{dim('| sessions flush to memory automatically on idle/shutdown')}")
    rule("═")
    return "\n".join(out)


def _shorten(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


# ─── History table ────────────────────────────────────────────────────────────

_STATUS_STYLES = {
    "active": lambda s: green("● " + s),
    "idle_timeout": lambda s: cyan("◐ " + s),
    "normal_shutdown": lambda s: green("✓ " + s),
}


def render_history_table(rows: list[tuple]) -> str:
    """
    Render get_recent_sessions() rows as an aligned table.

    Row shape (from storage.get_recent_sessions):
        (session_name, working_directory, cli_tool, provider_name,
         model, started_at, ended_at, ended_reason)
    """
    if not rows:
        return dim("No sessions recorded yet.")

    def rel_time(iso: str | None) -> str:
        if not iso:
            return "—"
        try:
            dt = datetime.fromisoformat(iso)
        except ValueError:
            return iso
        delta = datetime.now() - dt
        seconds = int(delta.total_seconds())
        if seconds < 0:
            return "now"
        if seconds < 60:
            return f"{seconds}s ago"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}m ago"
        hours = minutes // 60
        if hours < 24:
            return f"{hours}h ago"
        days = hours // 24
        return f"{days}d ago"

    headers = ["SESSION", "PROJECT", "AGENT/MODEL", "STATUS", "ENDED"]
    cells_raw: list[list[str]] = []
    for (session_name, wd, cli_tool, provider, model, started, ended, reason) in rows:
        project = wd.rstrip("/").split("/")[-1] or "/"
        status = (reason or "active").strip()
        cells_raw.append([
            session_name,
            project,
            f"{cli_tool}/{model}",
            status,
            rel_time(ended),
        ])

    widths = [
        max(len(headers[i]), *(len(r[i]) for r in cells_raw))
        for i in range(len(headers))
    ]

    # Colorize AFTER padding so ANSI escape bytes never affect alignment.
    def style_cell(col: int, text: str) -> str:
        if col == 0:
            return bold(text)
        if col == 3:
            styler = _STATUS_STYLES.get(text.strip(), lambda s: yellow("? " + s))
            return styler(text.strip()) + " " * (len(text) - len(text.strip()))
        if col == 4:
            return dim(text)
        return text

    def line(cells: list[str], colorize: bool) -> str:
        parts = []
        for i, cell in enumerate(cells):
            padded = cell.ljust(widths[i])
            parts.append(style_cell(i, padded) if colorize else padded)
            if i < len(cells) - 1:
                parts.append(dim("  │  "))
        return "".join(parts).rstrip()

    out = [line(headers, colorize=False), dim("─" * (
        sum(widths) + 5 * (len(widths) - 1)))]
    for row in cells_raw:
        out.append(line(row, colorize=True))
    return "\n".join(out)
