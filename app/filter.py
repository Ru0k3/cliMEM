"""
filter.py — CliMem end-of-session chat log scanning and signal extraction

Scope (locked):
  - Owns: raw chat log -> clean, categorized, atomic, self-contained facts
  - Does NOT touch: SQLite (Member 1), Cognee (Member 2), proxy/streaming logic
  - Pure heuristic/rule-based. No model calls. (LLM/Ollama summarization
    was rejected as too costly/friction-heavy — confirmed.)

Entry point (frozen signature — do not change):
    process_session(chat_log, working_directory, session_name) -> list[dict]

Output contract (updated):

    {
        "category": "decision" | "state" | "convention" | "open_thread" | "architecture" | "api" | "implementation" | "database" | "identity" | "goal",
        "text": "<atomic, self-contained, pronoun-free sentence>",
    }

Member 2 (memory.py) consumes this list directly. Dataset scoping is
handled separately using the current working directory, so individual
facts do not include working_directory or session_name.
"""

import re
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# In-memory chat log
# ---------------------------------------------------------------------------

chat_log = []


def add_message(role: str, content: str):
    """
    Add a message to the current session log.
    """
    chat_log.append(
        {
            "role": role,
            "content": content,
        }
    )


def get_chat_log():
    """
    Return the current session log.
    """
    return chat_log


def clear_chat_log():
    """
    Clear the current session log.
    """
    chat_log.clear()

# ─── Data model ───────────────────────────────────────────────────────────────

@dataclass
class Exchange:
    user: str
    assistant: str
    raw_user: str
    raw_assistant: str


# ─── Code stripping ────────────────────────────────────────────────────────────

_FENCED_CODE_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
_INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
_WHITESPACE_RE  = re.compile(r"[ \t]{2,}")


def _strip_code(text: str) -> str:
    text = _FENCED_CODE_RE.sub("", text)
    text = _INLINE_CODE_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


# ─── Parsing ────────────────────────────────────────────────────────────────────

# Role labels recognized across common CLI agent transcript formats.
# Maps lowercase label -> normalized role ("user" | "assistant").
_USER_LABELS = {
    "user", "human", "you", "prompt", "me", "input",
}
_ASSISTANT_LABELS = {
    "assistant", "claude", "ai", "model", "bot", "response",
    "gpt", "gemini", "codex", "agent", "output",
}

# Format A: "Label:" at start of line (covers Claude Code, Aider, most
# transcript exports -- "User:", "Human:", "Assistant:", "AI:", etc.)
_LABEL_LINE_RE = re.compile(
    r"^\s*(" + "|".join(sorted(_USER_LABELS | _ASSISTANT_LABELS, key=len, reverse=True))
    + r")\s*:\s*",
    re.IGNORECASE | re.MULTILINE,
)

# Format B: shell-prompt style, e.g. "> some prompt" for user turns,
# common in CLI tools that don't label the assistant's reply at all --
# everything until the next "> " is treated as the assistant's output.
_PROMPT_LINE_RE = re.compile(r"^>\s?(.*)$", re.MULTILINE)

# Format C: JSON Lines transcript, one {"role": ..., "content": ...} per
# line -- used by some agents' --output-format jsonl / session export.
def _try_parse_jsonl(raw_log: str) -> list[Exchange] | None:
    import json as _json
    lines = [ln for ln in raw_log.strip().splitlines() if ln.strip()]
    if not lines:
        return None
    parsed = []
    for ln in lines:
        try:
            obj = _json.loads(ln)
        except (ValueError, TypeError):
            return None  # not JSONL, bail to try other formats
        if not isinstance(obj, dict) or "role" not in obj:
            return None
        role = str(obj.get("role", "")).strip().lower()
        content = obj.get("content", "")
        if isinstance(content, list):  # some agents nest content blocks
            content = " ".join(
                blk.get("text", "") for blk in content
                if isinstance(blk, dict) and blk.get("type") == "text"
            )
        parsed.append((role, str(content).strip()))

    return _pair_blocks(parsed)


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
            i += 1  # misaligned roles -- slide forward one and retry
    return exchanges


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
    """
    Format B: shell-prompt style where only the user turn is marked
    (e.g. "> do the thing") and everything until the next "> " line is
    the assistant's unlabeled output. Common in minimal CLI agent logs.
    """
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
    """
    Parse a raw chat log into Exchange objects, auto-detecting the
    transcript format so this works across different CLI coding agents.

    Tries, in order:
      1. JSON Lines  (role/content per line -- some agents' session export)
      2. Labeled text ("User:", "Human:", "AI:", "Assistant:", etc.)
      3. Shell-prompt style ("> message" with unlabeled output below)

    If none of these match, returns an empty list rather than guessing --
    a silent empty result is safer than fabricating exchange boundaries
    from a format this function does not actually understand. Whoever
    wires CliMem to a new agent should confirm its transcript shape
    against these three before assuming process_session() will "just work".
    """
    for parser in (_try_parse_jsonl, _try_parse_labeled, _try_parse_prompt_style):
        result = parser(raw_log)
        if result:
            return result
    return []


# ─── Dead-end / reverted detection ──────────────────────────────────────────────
# What NOT to store: debugging back-and-forth that ended in a dead end or got
# reverted, exploratory questions that led nowhere, errors fixed within the
# same session (only the final resolved state matters).

_REVERT_CUES = re.compile(
    r"\b(revert(ed)?|rolled? back|undo(ne)?|scratch that|never ?mind|"
    r"abandon(ed)?|that didn'?t work|dead end|gave up on|went with .* instead)\b",
    re.IGNORECASE,
)

_EXPLORATORY_CUES = re.compile(
    r"\b(what if|just exploring|just wondering|hypothetically|"
    r"thinking out loud|not sure if|maybe we could)\b",
    re.IGNORECASE,
)

_SMALL_TALK_RE = re.compile(
    r"^(thanks?|ok|okay|got it|sure|yep|yes|no|nope|cool|great|"
    r"sounds good|makes sense|alright|hm+|hmm|lol|nice|perfect|"
    r"understood|will do|noted|hey|hi|hello)[.!?]?\s*$",
    re.IGNORECASE,
)


def _is_dead_end_or_reverted(window: list[Exchange], idx: int) -> bool:
    """
    A fact derived from exchange[idx] is suspect if a LATER exchange in the
    same session explicitly reverts/abandons it. Heuristic: scan forward
    for revert cues with STRONG vocabulary overlap (3+ shared rare tokens),
    so a revert of one sub-decision doesn't wipe out an unrelated earlier
    decision that happened to share a couple of common words.
    """
    this_text = (window[idx].user + " " + window[idx].assistant).lower()
    this_tokens = set(re.findall(r"[a-z]{6,}", this_text))  # 6+ chars = rarer, more specific

    # Only look at the next 3 exchanges -- a revert mentioned much later
    # in the session is unlikely to be about this specific exchange, and
    # broad vocabulary overlap across a whole session causes false positives.
    for later in window[idx + 1: idx + 4]:
        later_text = later.user + " " + later.assistant
        if not _REVERT_CUES.search(later_text):
            continue
        later_tokens = set(re.findall(r"[a-z]{6,}", later_text.lower()))
        overlap = this_tokens & later_tokens
        if len(overlap) >= 4:
            return True
    return False


# ─── Category cue phrases ──────────────────────────────────────────────────────

# Priority Order:
# 1. Identity (highest specificity)
# 2. Convention
# 3. Decision
# 4. Goal
# 5. Open Thread
# 6. Architecture
# 7. API
# 8. Database
# 9. Implementation (file/module mentions)
# 10. State (generic "is/now" -- lowest specificity)

CUE_PATTERNS = {
    "identity": re.compile(
        r"\b("
        r"project name is|"
        r"next project name is|"
        r"repo name is|"
        r"repository name is|"
        r"called|"
        r"named"
        r")\b",
        re.IGNORECASE,
    ),
    "convention": re.compile(
        r"\b("
        r"should be named|"
        r"must be named|"
        r"always name|"
        r"never name|"
        r"always use|"
        r"never use|"
        r"don't use|"
        r"do not use|"
        r"prefer(?:\s+to)?|"
        r"recommended|"
        r"best practice|"
        r"convention|"
        r"naming convention|"
        r"style rule|"
        r"coding standard|"
        r"must follow|"
        r"should follow|"
        r"going forward|"
        r"from now on|"
        r"hereafter|"
        r"keep using|"
        r"continue using|"
        r"all files should|"
        r"every file should|"
        r"every function should|"
        r"all functions should|"
        r"always call|"
        r"always inject|"
        r"always store|"
        r"always return|"
        r"always validate|"
        r"always strip|"
        r"must always|"
        r"should always|"
        r"must never|"
        r"should never"
        r")\b",
        re.IGNORECASE,
    ),
    "decision": re.compile(
        r"\b("
        r"decided(?:\s+to|\s+on)?|"
        r"decision(?:\s+was)?|"
        r"going with|"
        r"we(?:'ll| will)? use|"
        r"we(?:'ll| will)? keep|"
        r"we(?:'ll| will)? stick with|"
        r"we(?:'ll| will)? switch to|"
        r"we(?:'ll| will)? migrate to|"
        r"we(?:'ll| will)? move to|"
        r"we(?:'ll| will)? adopt|"
        r"we(?:'ll| will)? implement|"
        r"we(?:'ll| will)? store|"
        r"we(?:'ll| will)? save|"
        r"we(?:'ll| will)? inject|"
        r"we(?:'ll| will)? call|"
        r"we(?:'ll| will)? expose|"
        r"we(?:'ll| will)? create|"
        r"we(?:'ll| will)? remove|"
        r"we(?:'ll| will)? rename|"
        r"we(?:'ll| will)? refactor|"
        r"chose|"
        r"choosing|"
        r"choice(?:\s+is)?|"
        r"opted(?:\s+for)?|"
        r"settled(?:\s+on)?|"
        r"selected|"
        r"picked|"
        r"preferred?|"
        r"standardized on|"
        r"committed to|"
        r"agreed(?:\s+to|\s+on)?|"
        r"the plan is to|"
        r"the approach is|"
        r"the solution is|"
        r"the fix is|"
        r"the design is|"
        r"the architecture is|"
        r"instead of|"
        r"rather than|"
        r"replace(?:d)? with|"
        r"swap(?:ped)? to|"
        r"use(?:d)? instead|"
        r"keep using|"
        r"continue using"
        r")\b",
        re.IGNORECASE,
    ),
    "goal": re.compile(
        r"\b("
        r"I want to|"
        r"I'm going to|"
        r"I plan to|"
        r"trying to|"
        r"learning|"
        r"studying|"
        r"goal is|"
        r"objective is"
        r")\b",
        re.IGNORECASE,
    ),
    "open_thread": re.compile(
        r"\b("
        r"todo|"
        r"to-do|"
        r"fixme|"
        r"xxx|"
        r"hack|"
        r"temporary|"
        r"workaround|"
        r"unresolved|"
        r"still need to|"
        r"need to|"
        r"needs to|"
        r"remaining|"
        r"left to do|"
        r"follow[- ]?up|"
        r"future work|"
        r"not yet(?:\s+implemented|\s+decided|\s+finished)?|"
        r"pending|"
        r"known bug|"
        r"known issue|"
        r"bug|"
        r"issue|"
        r"edge case|"
        r"fails when|"
        r"doesn't work|"
        r"does not work|"
        r"broken|"
        r"missing|"
        r"incomplete|"
        r"blocked by|"
        r"waiting for|"
        r"need to investigate|"
        r"need to verify|"
        r"need to figure out|"
        r"unclear(?:\s+whether|\s+how)?|"
        r"unknown|"
        r"question is|"
        r"haven't decided|"
        r"haven't implemented|"
        r"hasn't been done"
        r")\b",
        re.IGNORECASE,
    ),
    "architecture": re.compile(
        r"\b("
        r"architecture|design|pipeline|workflow|"
        r"request flow|response flow|proxy|wrapper|"
        r"middleware|hook|lifecycle|startup|shutdown|"
        r"dependency injection|session lifecycle|"
        r"data flow|control flow"
        r")\b",
        re.IGNORECASE,
    ),
    "api": re.compile(
        r"\b("
        r"endpoint|route|api|request|response|"
        r"payload|body|json|header|status code|"
        r"GET|POST|PUT|PATCH|DELETE|"
        r"/v1/|http://|https://"
        r")\b",
        re.IGNORECASE,
    ),
    "database": re.compile(
        r"\b("
        r"sqlite|postgres|database|schema|table|"
        r"column|row|index|migration|dataset|"
        r"cognee|vector|embedding|knowledge graph|"
        r"remember|recall|forget|improve"
        r")\b",
        re.IGNORECASE,
    ),
    "implementation": re.compile(
        r"\b("
        r"file|module|package|directory|folder|"
        r"class|function|method|variable|"
        r"app\.|main\.py|memory\.py|proxy\.py|"
        r"filter\.py|config\.py|session\.py|"
        r"README|\.env"
        r")\b",
        re.IGNORECASE,
    ),
    "state": re.compile(
        r"\b("
        r"currently|"
        r"now|"
        r"today|"
        r"is now|"
        r"exists(?:\s+at)?|"
        r"is located at|"
        r"lives in|"
        r"resides in|"
        r"is stored in|"
        r"is saved in|"
        r"is cached in|"
        r"is persisted in|"
        r"is indexed by|"
        r"is backed by|"
        r"is implemented(?:\s+as|\s+in)?|"
        r"is defined in|"
        r"is declared in|"
        r"is exposed at|"
        r"is available at|"
        r"is handled by|"
        r"is managed by|"
        r"is called from|"
        r"is invoked by|"
        r"is generated by|"
        r"is created by|"
        r"contains|"
        r"includes|"
        r"consists of|"
        r"uses|"
        r"depends on|"
        r"relies on|"
        r"runs on|"
        r"listens on|"
        r"maps to|"
        r"points to|"
        r"returns|"
        r"accepts|"
        r"expects|"
        r"supports|"
        r"tracks|"
        r"stores|"
        r"loads|"
        r"reads from|"
        r"writes to|"
        r"the schema(?:\s+has|\s+includes)?|"
        r"the database(?:\s+has|\s+contains)?|"
        r"the table(?:\s+has|\s+contains)?|"
        r"the endpoint(?:\s+is)?|"
        r"the route(?:\s+is)?|"
        r"the file .*?(?:contains|has|defines)|"
        r"the function .*?(?:returns|accepts|calls)|"
        r"the class .*?(?:contains|implements)"
        r")\b",
        re.IGNORECASE,
    ),
}

_RESOLVED_CUES = re.compile(
    r"\b("
    r"fixed|"
    r"resolved|"
    r"solved|"
    r"completed|"
    r"implemented|"
    r"finished|"
    r"done|"
    r"working|"
    r"verified|"
    r"confirmed|"
    r"validated|"
    r"addressed|"
    r"patched|"
    r"merged|"
    r"closed|"
    r"removed|"
    r"eliminated|"
    r"cleaned up|"
    r"refactored|"
    r"figured out|"
    r"no longer(?:\s+an)? issue|"
    r"works now|"
    r"passes|"
    r"successfully"
    r")\b",
    re.IGNORECASE,
)

# Bare pronouns that break self-containment if left dangling
_PRONOUN_RE = re.compile(
    r"\b(it|this|that|these|those|they|he|she|him|her|its|their)\b",
    re.IGNORECASE,
)


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def _has_dangling_pronoun(sentence: str) -> bool:
    """
    Heuristic self-containment check. A sentence that STARTS with a pronoun
    (after stripping a leading discourse filler like "Yes," or "Well,")
    almost always refers back to prior context and cannot be trusted
    standalone.
    """
    working = re.sub(
        r"^(yes|no|sure|ok|okay|well|so|right)\s*,?\s*",
        "", sentence.strip(), flags=re.IGNORECASE,
    )
    first_word = working.split(" ", 1)[0].lower().strip(",.!?") if working else ""
    return first_word in {"it", "this", "that", "these", "those", "they", "he", "she"}


def _categorize_sentence(sentence: str) -> str | None:
    for category, pattern in CUE_PATTERNS.items():
        if pattern.search(sentence):
            if category == "open_thread" and _RESOLVED_CUES.search(sentence):
                continue
            return category

    return None

# ─── Self-containment repair ───────────────────────────────────────────────────

def _make_self_contained(sentence: str, topic_subject: str) -> str | None:
    """
    Attempt to rewrite a sentence so it does not open with a dangling
    pronoun, by substituting a subject derived from the user question.
    If the sentence still reads ambiguous after substitution, drop it
    (return None) rather than emit a broken fact.
    """
    if not _has_dangling_pronoun(sentence):
        return sentence

    if not topic_subject:
        return None

    working = re.sub(
        r"^(yes|no|sure|ok|okay|well|so|right)\s*,?\s*",
        "", sentence, flags=re.IGNORECASE,
    )

    # Only repair the clean "<pronoun> <is/was/are/were> <rest>" pattern.
    # Anything messier (e.g. "it is still need to figure out", which is
    # already ungrammatical in the source) is too risky to rewrite
    # automatically -- drop rather than emit a broken fact.
    m = re.match(
        r"^(it|this|that|these|those|they)\s+(is|was|are|were)\s+(.*)$",
        working, flags=re.IGNORECASE,
    )
    if not m:
        return None

    verb, rest = m.group(2), m.group(3)

    # Guard against rewriting already-ungrammatical source text. If `rest`
    # starts with another modal/verb stack (e.g. "still need to", "going
    # to"), substituting a noun phrase for the pronoun produces broken
    # grammar ("X is still need to..."). Safer to drop than emit that.
    broken_rest = re.match(
        r"^(still |also |now |currently )?(need to|going to|able to|trying to)\b",
        rest, flags=re.IGNORECASE,
    )
    if broken_rest:
        return None

    repaired = f"{topic_subject} {verb} {rest}".strip()
    repaired = repaired[0].upper() + repaired[1:] if repaired else repaired

    if _has_dangling_pronoun(repaired):
        return None

    return repaired


def _derive_topic_subject(user_text: str) -> str:
    """
    Pull a short noun-phrase-ish subject out of the user's question to use
    as a pronoun replacement. Best-effort, heuristic only.
    """
    cleaned = re.sub(
        r"^(why|what|how|when|where|which|who|should|can|does|do|is|are|would)\b",
        "", user_text.strip(), flags=re.IGNORECASE
    ).strip(" ?.!")
    words = cleaned.split()
    return " ".join(words[:8]) if words else ""


# ─── Deduplication ──────────────────────────────────────────────────────────────

def _normalize_for_dedup(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _dedup_facts(facts: list[dict]) -> list[dict]:
    """Collapse duplicate/near-duplicate facts within the same session."""
    seen = []
    out = []
    for fact in facts:
        norm = _normalize_for_dedup(fact["text"])
        norm_tokens = set(norm.split())
        is_dup = False
        for seen_norm, seen_tokens in seen:
            if not seen_tokens or not norm_tokens:
                continue
            overlap = len(norm_tokens & seen_tokens) / max(len(norm_tokens), len(seen_tokens))
            if overlap >= 0.8:
                is_dup = True
                break
        if not is_dup:
            seen.append((norm, norm_tokens))
            out.append(fact)
    return out


# ─── Main entry point (frozen signature) ───────────────────────────────────────

def process_session(chat_log: str, working_directory: str, session_name: str) -> list[dict]:
    """
    Scan a raw session chat log and extract a short list of clean,
    categorized, atomic, self-contained facts.

    Parameters
    ----------
    chat_log          : full raw conversation text for the session
    working_directory : scoping key — the codebase this session belongs to
    session_name       : session identifier, used for chronology/forget targeting

    Returns
    -------
    list[dict] — each dict:

    {
        "category": "decision" | "state" | "convention" | "open_thread" | "architecture" | "api" | "implementation" | "database" | "identity" | "goal",
        "text": str,
    }

    This function does not write to SQLite or call Cognee. It is pure
    extraction: raw log in, fact list out.
    """
    exchanges = _parse_chat_log(chat_log)
    facts: list[dict] = []

    for idx, ex in enumerate(exchanges):

        # Skip pure small talk exchanges outright
        if _SMALL_TALK_RE.match(ex.user.strip()):
            continue

        # Skip exploratory dead ends
        if _EXPLORATORY_CUES.search(ex.user) and len(ex.assistant.split()) < 15:
            continue

        # Skip exchanges that a later message explicitly reverts/abandons
        if _is_dead_end_or_reverted(exchanges, idx):
            continue

        topic_subject = _derive_topic_subject(ex.user)

        candidate_sentences = _split_sentences(ex.user) + _split_sentences(ex.assistant)

        for sentence in candidate_sentences:
            if len(sentence.split()) < 6:
                continue  # too short to be a standalone fact

            category = _categorize_sentence(sentence)
            if category is None:
                continue  # no cue phrase, not confidently categorizable

            repaired = _make_self_contained(sentence, topic_subject)
            if repaired is None:
                continue  # dangling pronoun we couldn't safely fix — drop

            # Strip any remaining relative-time language
            repaired = re.sub(
                r"\b(earlier today|just now|a moment ago|previously in this session)\b",
                "", repaired, flags=re.IGNORECASE
            )
            repaired = _WHITESPACE_RE.sub(" ", repaired).strip()

            facts.append({
                "category": category,
                "text": repaired,
            })

    facts = _dedup_facts(facts)
    return facts


# ─── CLI for manual verification ───────────────────────────────────────────────

if __name__ == "__main__":
    import argparse, json, sys
    from pathlib import Path

    parser = argparse.ArgumentParser(description="filter.py — fact extraction test runner")
    parser.add_argument("logfile", help="Path to raw chat log")
    parser.add_argument("--wd", default="/home/user/climem", help="working_directory value")
    parser.add_argument("--session", default="test_session")
    args = parser.parse_args()

    log_text = Path(args.logfile).read_text(encoding="utf-8")
    facts = process_session(log_text, args.wd, args.session)

    by_category: dict[str, list[str]] = {}
    for f in facts:
        by_category.setdefault(f["category"], []).append(f["text"])

    for cat in ("decision", "state", "convention", "open_thread", "architecture", "api", "implementation", "database", "identity", "goal"):
        items = by_category.get(cat, [])
        print(f"\n[{cat}] ({len(items)})")
        for t in items:
            print(f"  - {t}")

    print(f"\nTotal facts: {len(facts)}")
    print("\nRaw JSON:")
    print(json.dumps(facts, indent=2))
