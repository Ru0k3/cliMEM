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


def build_file_tree(root: Path) -> str:
    """
    Return a human-readable project tree rooted at `root`.

    Only directory and file names are included.
    File contents are NEVER read.
    """
    lines = [root.name]

    _walk(root, "", lines)

    return "\n".join(lines)


def _walk(directory: Path, prefix: str, lines: list[str]):
    entries = sorted(
        (
            entry
            for entry in directory.iterdir()
            if entry.name not in IGNORE
        ),
        key=lambda p: (p.is_file(), p.name.lower()),
    )

    for index, entry in enumerate(entries):
        last = index == len(entries) - 1

        branch = "└── " if last else "├── "

        lines.append(prefix + branch + entry.name)

        if entry.is_dir():
            extension = "    " if last else "│   "
            _walk(entry, prefix + extension, lines)