"""filter.py — Chat log scanning and fact extraction entry point.

Re-exports the public API from sub-modules and owns the orchestration
logic (``process_session``) and the CLI test runner.
"""

from .chat_log import add_message, clear_chat_log, get_chat_log  # noqa: F401
from .utils import collapse_whitespace
from .cues import (
    categorize_sentence,
    dedup_facts,
    derive_topic_subject,
    make_self_contained,
    split_sentences,
)
from .parsers import (
    _EXPLORATORY_CUES,
    _SMALL_TALK_RE,
    _parse_chat_log,
    is_dead_end_or_reverted,
)


def process_session(chat_log: str, working_directory: str, session_name: str) -> list[dict]:
    """Scan a raw session chat log and extract clean, categorized facts.

    Parameters
    ----------
    chat_log          : full raw conversation text for the session
    working_directory : scoping key — the codebase this session belongs to
    session_name      : session identifier (used for chronology / forget targeting)

    Returns
    -------
    list[dict] — each dict:

        {
            "category": "decision" | "state" | "convention" | "open_thread"
                        | "architecture" | "api" | "implementation"
                        | "database" | "identity" | "goal",
            "text": str,
        }
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

        # Skip exchanges that a later message explicitly reverts / abandons
        if is_dead_end_or_reverted(exchanges, idx):
            continue

        topic_subject = derive_topic_subject(ex.user)

        candidate_sentences = split_sentences(ex.user) + split_sentences(ex.assistant)

        for sentence in candidate_sentences:
            if len(sentence.split()) < 6:
                continue  # too short to be a standalone fact

            category = categorize_sentence(sentence)
            if category is None:
                continue

            repaired = make_self_contained(sentence, topic_subject)
            if repaired is None:
                continue

            # Strip any remaining relative-time language
            repaired = re.sub(
                r"\b(earlier today|just now|a moment ago|previously in this session)\b",
                "", repaired, flags=re.IGNORECASE,
            )
            repaired = collapse_whitespace(repaired)

            facts.append({
                "category": category,
                "text": repaired,
            })

    facts = dedup_facts(facts)
    return facts


# ─── CLI for manual verification ───────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import json

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

    for cat in (
        "decision", "state", "convention", "open_thread",
        "architecture", "api", "implementation", "database",
        "identity", "goal",
    ):
        items = by_category.get(cat, [])
        print(f"\n[{cat}] ({len(items)})")
        for t in items:
            print(f"  - {t}")

    print(f"\nTotal facts: {len(facts)}")
    print("\nRaw JSON:")
    print(json.dumps(facts, indent=2))
