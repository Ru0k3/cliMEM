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
    facts passed to store_memory() are dictionaries in the form:

        {
            "category": "decision" | "state" | "convention" | "open_thread",
            "text": "<atomic, self-contained sentence>",
        }

    store_memory() formats each fact internally as:

        "[category] text"

    before storing it in Cognee. Member 3 should not prefix category tags
    manually.
"""

from __future__ import annotations

import hashlib
import re
from typing import Iterable

import cognee
from cognee.modules.search.types.SearchType import SearchType

from .filetree import build_file_tree
from pathlib import Path

# ---------------------------------------------------------------------------
# 0. Cloud connection (optional)
#    Called once at startup. If COGNEE_MODE=cloud, routes all subsequent
#    cognee.add/recall/improve/forget calls to Cognee Cloud instead of the
#    local embedded databases. Safe to call multiple times — no-ops after
#    the first successful connection.
# ---------------------------------------------------------------------------

from .config import COGNEE_MODE, COGNEE_SERVICE_URL, COGNEE_API_KEY

_cloud_connected = False


async def ensure_cognee_connection() -> None:
    global _cloud_connected

    if _cloud_connected or COGNEE_MODE != "cloud":
        return

    if not COGNEE_SERVICE_URL or not COGNEE_API_KEY:
        raise RuntimeError(
            "COGNEE_MODE=cloud but COGNEE_SERVICE_URL or COGNEE_API_KEY is missing in .env"
        )

    await cognee.serve(url=COGNEE_SERVICE_URL, api_key=COGNEE_API_KEY)
    _cloud_connected = True
    print(f"[VERIFY] Connected to Cognee Cloud: {COGNEE_SERVICE_URL}")

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

async def store_memory(facts: Iterable[dict], dataset_name: str) -> None:
    """
    Store distilled, categorized fact sentences into Cognee, scoped to
    dataset_name. Builds the knowledge graph over them via cognify().

    facts: Iterable of dictionaries produced by filter.process_session():

       {
           "category": "...",
           "text": "..."
       }

       Raw chat logs and code blocks must already have been removed.
    """
    fact_list = []

    for fact in facts:
        if not fact:
            continue

        category = fact.get("category", "").strip()
        text = fact.get("text", "").strip()

        if not category or not text:
            continue

        fact_list.append(f"[{category}] {text}")

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

    Two-stage: first probe with a lightweight search type to check relevance,
    then only run GRAPH_COMPLETION synthesis if the probe found something.
    Returns "" if nothing relevant is found. Callers treat "" as
    "no memory to inject", not an error.
    """
    probe_type = None
    for candidate in ("CHUNKS", "INSIGHTS", "RAG_COMPLETION", "VECTOR"):
        if hasattr(SearchType, candidate):
            probe_type = getattr(SearchType, candidate)
            break

    if probe_type is not None:
        try:
            probe = await cognee.recall(
                query_text=query,
                query_type=probe_type,
                datasets=[dataset_name],
                only_context=True,
            )
        except Exception as e:
            print(f"[DEBUG] probe exception: {e!r}")
            probe = None

        print(f"[DEBUG] probe_type={probe_type} probe={probe!r}")

        if not probe:
            return ""

        probe_text = " ".join(getattr(item, "text", "") or "" for item in probe)
        if not _is_probably_relevant(query, probe_text):
            return ""

    try:
        results = await cognee.recall(
            query_text=query,
            query_type=SearchType.GRAPH_COMPLETION,
            datasets=[dataset_name],
            only_context=True,
        )
    except Exception as e:
        print(f"[DEBUG] graph_completion exception: {e!r}")
        return ""

    return _flatten_results(results)

def _is_probably_relevant(query: str, probe_text: str) -> bool:
    """
    Crude fallback relevance check: since this Cognee version exposes no
    usable score data, require some lexical/word overlap between the query
    and the retrieved chunk before trusting it enough to run GRAPH_COMPLETION.
    """
    query_words = {w.lower() for w in re.findall(r"[a-zA-Z]{4,}", query)}
    text_words = {w.lower() for w in re.findall(r"[a-zA-Z]{4,}", probe_text)}
    overlap = query_words & text_words
    return len(overlap) >= 1

def _flatten_results(results) -> str:
    """
    Extract clean node-content sentences from Cognee's GRAPH_COMPLETION text
    output, stripping graph structure markers (Nodes:, Connections:, etc.)
    """
    if not results:
        return ""

    seen: set[str] = set()
    pieces: list[str] = []

    for item in results:
        text = getattr(item, "text", None) if not isinstance(item, (str, dict)) else None
        if text is None:
            if isinstance(item, str):
                text = item
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content") or ""
            else:
                text = ""

        matches = re.findall(
            r"__node_content_start__\n(.*?)\n__node_content_end__",
            text,
            flags=re.DOTALL,
        )

        for match in matches:
            match = match.strip()
            if not match or match == "None" or match in seen:
                continue
            seen.add(match)
            pieces.append(match)

        if not matches:
            plain = text.strip()
            if plain and plain not in seen and "Nodes:" not in plain:
                seen.add(plain)
                pieces.append(plain)

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

_FILETREE_PREFIX = (
    "\n\nCurrent project structure:\n\n"
)


async def inject_memory(body: dict, working_directory: str) -> dict:
    """
    Called for every incoming chat completion request from proxy.py,
    immediately before the request is forwarded to the AI provider.

    Retrieves relevant memory for the current project and injects it as a
    system message at the front of body["messages"]. If the client already
    provided a system message, the remembered context is appended to it
    rather than replacing it, preserving the client's original instructions.

    Returns the modified request body. All other fields remain unchanged.
    """
    dataset_name = get_dataset_name(working_directory)
    print(f"[VERIFY] Dataset: {dataset_name}")

    messages = body.get("messages", [])

    query = "Project context"

    for message in reversed(messages):
        if message.get("role") == "user":
            query = message.get("content", "").strip()
            break
    print(f"[VERIFY] Recall query: {query}")

    project_tree = build_file_tree(Path(working_directory))
    memory_text = await search_memory(query, dataset_name)

    content = _FILETREE_PREFIX + project_tree

    if memory_text:
        content = _SYSTEM_PREFIX + memory_text + content

    memory_message = {
        "role": "system",
        "content": content,
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