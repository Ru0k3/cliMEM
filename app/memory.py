"""
memory.py — Member 2's scope: Cognee lifecycle wrappers + proxy recall hook.

Five functions:
    get_dataset_name(working_directory) -> str
    store_memory(facts, dataset_name)   -> None
    search_memory(query, dataset_name)  -> str
    improve_memory(dataset_name)        -> None
    forget_memory(dataset_name)         -> None

Plus the proxy contract function:
    inject_memory(body, working_directory) -> dict

CONTRACT WITH MEMBER 3:
    facts passed to store_memory() are plain strings, already prefixed with
    their category tag, e.g.:
        "[decision] We chose FastAPI for the backend."
        "[state] Auth is broken on Android."
        "[convention] All endpoints use snake_case."
        "[open_thread] Still undecided on deployment target."
    store_memory() stores them exactly as given — it does NOT re-parse or
    strip tags. Confirm the exact prefix format with Member 3 before either
    of you build, so nobody double-prefixes or silently drops a tag.
"""

from __future__ import annotations

import hashlib
import re
from typing import Iterable

import cognee
from cognee.modules.search.types.SearchType import SearchType


# ---------------------------------------------------------------------------
# 1. Dataset naming
#    Must be deterministic — same working_directory always produces the same
#    string. This is the single mechanism for project isolation. Never inline
#    this logic elsewhere; always call this function.
# ---------------------------------------------------------------------------

def get_dataset_name(working_directory: str) -> str:
    """
    Convert a working directory path into a stable, Cognee-safe dataset name.

    Uses a SHA-256 hash of the full normalized path to guarantee uniqueness
    even when two different repos share the same folder name (e.g. two repos
    both named "backend"). The human-readable slug from the last path component
    is kept as a prefix purely for debuggability.
    """
    normalized = working_directory.strip().rstrip("/")
    tail = normalized.split("/")[-1] or "root"
    slug = re.sub(r"[^a-zA-Z0-9_-]", "_", tail).lower()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
    return f"climem_{slug}_{digest}"


# ---------------------------------------------------------------------------
# 2. store_memory
# ---------------------------------------------------------------------------

async def store_memory(facts: Iterable[str], dataset_name: str) -> None:
    """
    Store distilled, categorized fact sentences into Cognee, scoped to
    dataset_name. Builds the knowledge graph over them via cognify().

    facts: Member 3's output — self-contained sentences, not raw chat logs
           and not code. Category-tagged strings like "[decision] ...".
    """
    fact_list = [f.strip() for f in facts if f and f.strip()]
    if not fact_list:
        return

    await cognee.add(fact_list, dataset_name=dataset_name)
    await cognee.cognify(datasets=[dataset_name])


# ---------------------------------------------------------------------------
# 3. search_memory
# ---------------------------------------------------------------------------

async def search_memory(query: str, dataset_name: str) -> str:
    """
    Query Cognee scoped to dataset_name and return plain text ready to inject
    into a system message.

    Uses GRAPH_COMPLETION so Cognee synthesizes an answer from the whole
    graph rather than doing exact keyword matching — this is what makes
    recall work even when the query wording differs from what was stored.

    Returns "" if nothing relevant is found. Callers treat "" as
    "no memory to inject", not an error.
    """
    try:
        results = await cognee.recall(
            query_text=query,
            query_type=SearchType.GRAPH_COMPLETION,
            datasets=[dataset_name],
            only_context=True,
        )
    except Exception:
        return ""

    return _flatten_results(results)


def _flatten_results(results) -> str:
    """
    Normalize whatever Cognee returns (ResponseGraphEntry objects, dicts, or
    plain strings) into a single clean prose string with no duplicate lines.
    """
    if not results:
        return ""

    seen: set[str] = set()
    pieces: list[str] = []

    for item in results:
        if isinstance(item, str):
            text = item.strip()
        elif isinstance(item, dict):
            text = (item.get("text") or item.get("content") or "").strip()
        else:
            # ResponseGraphEntry-style object (what your test run returned)
            text = (getattr(item, "text", None) or "").strip()

        if text and text not in seen:
            seen.add(text)
            pieces.append(text)

    return "\n".join(pieces)


# ---------------------------------------------------------------------------
# 4. improve_memory
# ---------------------------------------------------------------------------

async def improve_memory(dataset_name: str) -> None:
    """
    Trigger Cognee's graph reconciliation for a dataset. Call this right after
    store_memory() at end-of-session so Cognee merges/updates contradictions
    in the knowledge graph rather than leaving stale duplicates.

    Real signature confirmed from installed cognee version:
        improve(dataset: str = 'main_dataset', *, run_in_background=False, ...)
    Parameter is `dataset` (singular), NOT `datasets`.
    """
    await cognee.improve(dataset=dataset_name)


# ---------------------------------------------------------------------------
# 5. forget_memory
# ---------------------------------------------------------------------------

async def forget_memory(dataset_name: str) -> None:
    """
    Wipe memory scoped to a single dataset (one project's working directory),
    leaving all other projects' datasets untouched.

    Backs the `climem forget` CLI command.

    Real signature confirmed from installed cognee version:
        forget(*, dataset=None, dataset_id=None, everything=False, ...)
    Passing dataset=dataset_name gives project-scoped deletion.
    """
    await cognee.forget(dataset=dataset_name)


# ---------------------------------------------------------------------------
# 6. inject_memory — the one function that touches proxy.py's contract
# ---------------------------------------------------------------------------

_SYSTEM_PREFIX = (
    "The following is prior context remembered about this project. "
    "Use it if relevant, but always prioritize the current conversation:\n\n"
)

_RECALL_QUERY = (
    "What prior decisions, state, conventions, and open threads are "
    "relevant to this project?"
)


async def inject_memory(body: dict, working_directory: str) -> dict:
    """
    Called ONCE per new session from the MEMBER 2 HOOK in proxy.py, right
    before the request is forwarded. Do NOT call this on every turn —
    only on session start to avoid unnecessary latency and Groq API calls.

    Retrieves relevant memory for the project and inserts it as a system
    message at the front of body["messages"]. If the client already sent a
    system message, the memory is APPENDED to it rather than overwriting it,
    so any client-provided system prompt is preserved.

    Returns the modified body. Everything else in body is untouched.
    """
    dataset_name = get_dataset_name(working_directory)
    memory_text = await search_memory(_RECALL_QUERY, dataset_name)

    if not memory_text:
        # No memory for this project yet — return body unchanged.
        return body

    memory_message = {
        "role": "system",
        "content": _SYSTEM_PREFIX + memory_text,
    }

    messages = list(body.get("messages", []))

    if messages and messages[0].get("role") == "system":
        # Merge into the existing system message — don't clobber it.
        existing_content = messages[0].get("content", "")
        messages[0] = {
            "role": "system",
            "content": existing_content + "\n\n" + memory_message["content"],
        }
    else:
        messages = [memory_message] + messages

    body["messages"] = messages
    return body