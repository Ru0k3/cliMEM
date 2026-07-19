"""utils.py — Shared utility functions for CliMEM."""

import re
from pathlib import Path


def get_cwd() -> Path:
    """Return the current working directory as a Path.

    Centralizes ``Path.cwd()`` calls so the codebase uses a single
    import source, making mocking for tests straightforward.
    """
    return Path.cwd()


# ─── Regex helpers (shared by cues.py and parsers.py) ──────────────────────────

def compile_boundary_pattern(words: list[str]) -> re.Pattern:
    """Join word/phrase fragments into a compiled ``\\b(?:...)\\b`` pattern.

    Each fragment can contain regex constructs (e.g. ``(?:\\s+to)?``) —
    they are joined verbatim, not escaped.
    """
    return re.compile(
        r"\b(?:" + "|".join(words) + r")\b", re.IGNORECASE,
    )


# ─── Content extraction (shared by memory.py and parsers.py) ──────────────────

def extract_text(content: str | list) -> str:
    """Normalize OpenAI-style message content into plain text.

    Some clients (e.g. OpenCode) send content as a list of parts like
    ``[{"type": "text", "text": "..."}]`` or a mix of strings and dicts,
    instead of a plain string.
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and part.get("type") == "text":
                parts.append(part.get("text", ""))
        return " ".join(parts)

    return ""


# ─── Whitespace (shared by parsers.py, cues.py, filter.py) ────────────────────

_WHITESPACE_RE = re.compile(r"[ \t]{2,}")


def collapse_whitespace(text: str) -> str:
    """Collapse runs of 2+ spaces/tabs into a single space, then strip."""
    return _WHITESPACE_RE.sub(" ", text).strip()
