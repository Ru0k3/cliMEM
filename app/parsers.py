"""parsers.py — Chat log parsing and exchange pair detection."""

import re
from dataclasses import dataclass

from .utils import collapse_whitespace, compile_boundary_pattern, extract_text


# ─── Data model ───────────────────────────────────────────────────────────────

@dataclass
class Exchange:
    user: str
    assistant: str
    raw_user: str
    raw_assistant: str


# ─── Code stripping ───────────────────────────────────────────────────────────

_FENCED_CODE_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
_INLINE_CODE_RE = re.compile(r"`[^`\n]+`")


def _strip_code(text: str) -> str:
    text = _FENCED_CODE_RE.sub("", text)
    text = _INLINE_CODE_RE.sub("", text)
    return collapse_whitespace(text)


# ─── Role labels ──────────────────────────────────────────────────────────────

_USER_LABELS = {
    "user", "human", "you", "prompt", "me", "input",
}
_ASSISTANT_LABELS = {
    "assistant", "claude", "ai", "model", "bot", "response",
    "gpt", "gemini", "codex", "agent", "output",
}

_LABEL_LINE_RE = re.compile(
    r"^\s*(" + "|".join(
        sorted(_USER_LABELS | _ASSISTANT_LABELS, key=len, reverse=True)
    ) + r")\s*:\s*",
    re.IGNORECASE | re.MULTILINE,
)

_PROMPT_LINE_RE = re.compile(r"^>\s?(.*)$", re.MULTILINE)


# ─── Parsers ──────────────────────────────────────────────────────────────────

def _pair_blocks(blocks: list[tuple[str, str]]) -> list[Exchange]:
    """Walk a flat (role, content) sequence and pair user->assistant turns."""
    exchanges = []
    i = 0
    while i + 1 < len(blocks):
        role_u, raw_u = blocks[i]
        role_a, raw_a = blocks[i + 1]
        if role_u in _USER_LABELS and role_a in _ASSISTANT_LABELS:
            exchanges.append(Exchange(
                user=_strip_code(raw_u),
                assistant=_strip_code(raw_a),
                raw_user=raw_u,
                raw_assistant=raw_a,
            ))
            i += 2
        else:
            i += 1
    return exchanges


def _try_parse_jsonl(raw_log: str) -> list[Exchange] | None:
    """Format C: JSON Lines transcript, one {role, content} per line."""
    import json as _json
    lines = [ln for ln in raw_log.strip().splitlines() if ln.strip()]
    if not lines:
        return None
    parsed = []
    for ln in lines:
        try:
            obj = _json.loads(ln)
        except (ValueError, TypeError):
            return None
        if not isinstance(obj, dict) or "role" not in obj:
            return None
        role = str(obj.get("role", "")).strip().lower()
        content = extract_text(obj.get("content", "")).strip()
        parsed.append((role, content))

    return _pair_blocks(parsed)


def _try_parse_labeled(raw_log: str) -> list[Exchange] | None:
    """Format A: explicit 'Role:' labels anywhere in the text."""
    matches = list(_LABEL_LINE_RE.finditer(raw_log))
    if len(matches) < 2:
        return None

    blocks = []
    for idx, m in enumerate(matches):
        role = m.group(1).strip().lower()
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(raw_log)
        content = raw_log[start:end].strip()
        blocks.append((role, content))

    exchanges = _pair_blocks(blocks)
    return exchanges if exchanges else None


def _try_parse_prompt_style(raw_log: str) -> list[Exchange] | None:
    """Format B: shell-prompt style (e.g. '> do the thing') with unlabeled output."""
    matches = list(_PROMPT_LINE_RE.finditer(raw_log))
    if len(matches) < 1:
        return None

    blocks = []
    for idx, m in enumerate(matches):
        user_text = m.group(1).strip()
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(raw_log)
        assistant_text = raw_log[start:end].strip()
        if not assistant_text:
            continue
        blocks.append(("user", user_text))
        blocks.append(("assistant", assistant_text))

    exchanges = _pair_blocks(blocks)
    return exchanges if exchanges else None


def _parse_chat_log(raw_log: str) -> list[Exchange]:
    """Parse a raw chat log into Exchange objects, auto-detecting the format.

    Tries, in order:
      1. JSON Lines
      2. Labeled text ("User:", "Human:", etc.)
      3. Shell-prompt style ("> message")

    Returns an empty list if none match.
    """
    for parser in (_try_parse_jsonl, _try_parse_labeled, _try_parse_prompt_style):
        result = parser(raw_log)
        if result:
            return result
    return []


# ─── Dead-end / reverted detection ────────────────────────────────────────────

_REVERT_CUE_WORDS: list[str] = [
    "revert(ed)?", "rolled? back", "undo(ne)?", "scratch that", "never ?mind",
    "abandon(ed)?", "that didn'?t work", "dead end", "gave up on", "went with .* instead",
]

_REVERT_CUES: re.Pattern = compile_boundary_pattern(_REVERT_CUE_WORDS)

_EXPLORATORY_CUE_WORDS: list[str] = [
    "what if", "just exploring", "just wondering", "hypothetically",
    "thinking out loud", "not sure if", "maybe we could",
]

_EXPLORATORY_CUES: re.Pattern = compile_boundary_pattern(_EXPLORATORY_CUE_WORDS)

_SMALL_TALK_WORDS: list[str] = [
    "thanks?", "ok", "okay", "got it", "sure", "yep", "yes", "no", "nope",
    "cool", "great", "sounds good", "makes sense", "alright", "hm+", "hmm",
    "lol", "nice", "perfect", "understood", "will do", "noted", "hey", "hi",
    "hello",
]

_SMALL_TALK_RE: re.Pattern = re.compile(
    r"^(?:" + "|".join(_SMALL_TALK_WORDS) + r")[.!?]?\s*$", re.IGNORECASE,
)


def is_dead_end_or_reverted(window: list[Exchange], idx: int) -> bool:
    """Check if exchange[idx] is reverted/abandoned by a later exchange.

    Scans forward for revert cues with strong vocabulary overlap
    (4+ shared rare tokens of 6+ characters).
    """
    this_text = (window[idx].user + " " + window[idx].assistant).lower()
    this_tokens = set(re.findall(r"[a-z]{6,}", this_text))

    for later in window[idx + 1: idx + 4]:
        later_text = later.user + " " + later.assistant
        if not _REVERT_CUES.search(later_text):
            continue
        later_tokens = set(re.findall(r"[a-z]{6,}", later_text.lower()))
        overlap = this_tokens & later_tokens
        if len(overlap) >= 4:
            return True
    return False
