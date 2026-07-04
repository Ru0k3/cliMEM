from pathlib import Path

IGNORE = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    ".idea",
    ".vscode",
}


def build_file_tree(
    root: Path,
    *,
    max_depth: int = 4,
    max_entries: int = 250,
) -> str:
    """
    Return a human-readable project tree.

    Only names are included.
    File contents are never read.

    The tree is intentionally limited so very large repositories
    don't consume the model's context window.
    """
    lines = [root.name]

    state = {"entries": 0}

    _walk(
        directory=root,
        prefix="",
        lines=lines,
        depth=0,
        max_depth=max_depth,
        max_entries=max_entries,
        state=state,
    )

    if state["entries"] >= max_entries:
        lines.append("... (tree truncated)")

    return "\n".join(lines)


def _walk(
    directory: Path,
    prefix: str,
    lines: list[str],
    depth: int,
    max_depth: int,
    max_entries: int,
    state: dict,
):
    if depth >= max_depth:
        return

    try:
        entries = sorted(
            (
                entry
                for entry in directory.iterdir()
                if entry.name not in IGNORE
            ),
            key=lambda p: (p.is_file(), p.name.lower()),
        )
    except (PermissionError, OSError):
        return

    for index, entry in enumerate(entries):

        if state["entries"] >= max_entries:
            return

        last = index == len(entries) - 1

        branch = "└── " if last else "├── "

        lines.append(prefix + branch + entry.name)

        state["entries"] += 1

        if entry.is_dir():

            extension = "    " if last else "│   "

            _walk(
                directory=entry,
                prefix=prefix + extension,
                lines=lines,
                depth=depth + 1,
                max_depth=max_depth,
                max_entries=max_entries,
                state=state,
            )