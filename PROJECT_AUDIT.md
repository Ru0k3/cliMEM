# CliMEM Project Audit

Fresh pass date: 2026-07-04.

Scope checked: `app/`, `scripts/`, `test/`, packaging/config files, OpenSpec/OpenCode support files, and the previously generated `FUNCTIONAL_INVENTORY.md`. Excluded generated/external directories: `.git/`, `.venv/`, caches, and egg metadata.

Verification run:

- `python -m compileall app scripts test` passed.
- System Python import checks failed because `uvicorn` and `cognee` are not installed outside the local `.venv`.
- `.venv/bin/python` successfully imported `app.cli`, `app.main`, and `app.proxy`.
- `.venv/bin/python -m app.cli --help` and `.venv/bin/python -m app.cli history --limit 2` ran.
- `pytest` is not installed in either the active shell or `.venv`, so the test suite could not be run.

## What Improved Since The First Inventory

- `app/cli.py` now imports `CLIMEM_BASE_URL` correctly.
- The broken OpenSpec CLI delegation was removed from `app/cli.py`.
- `climem forget` now exists and uses `forget_memory`.
- `climem history` now exists and uses `get_recent_sessions`.
- `app/agent_handlers/opencode.py` now handles a missing config file and missing backup more cleanly.
- Cognee sample scripts moved from `test/` into `scripts/`, which is the right direction.
- `app/memory.py` comments now match the dict-shaped facts emitted by `filter.process_session`.

## Findings

### High: CLI imports Cognee for commands that do not need memory

`app/cli.py` imports `forget_memory` and `get_dataset_name` at module load time: `app/cli.py:9`. That imports `app.memory`, which imports Cognee: `app/memory.py:36`.

Impact: even `climem --help` and `climem history` initialize Cognee, print Cognee logs/warnings, and require Cognee to import. This showed up during verification: help/history worked only under `.venv`, and both printed Cognee startup logs before CLI output.

Recommendation: lazy-import `get_dataset_name` and `forget_memory` inside `cmd_forget`. Keep history independent from Cognee.

### High: Runtime request bodies and chat logs can expose sensitive content

`app/proxy.py:34` logs the full request body at debug level. `app/main.py:44-46` exposes `/chat-log`, returning the in-memory conversation log.

Impact: user prompts, code snippets, secrets pasted into chats, and provider request fields can leak into logs or an unauthenticated local HTTP endpoint.

Recommendation: remove full-body debug logging or redact it. Remove `/chat-log`, gate it behind explicit development mode, or require a local auth token.

### High: Session and chat state are global process state

`app/filter.py:33` stores all chat messages in one module-level list. `app/storage.py:8-15` stores the active session in module-level globals.

Impact: concurrent requests, multiple agents, or multiple projects served by the same process can mix conversations and session metadata. This is especially risky because the proxy is async and may stream multiple responses at once.

Recommendation: introduce a real session key and store chat logs by session id. At minimum, document single-user/single-session-only behavior and guard against concurrent use.

### High: Memory/file-tree injection runs on every request, including title requests

`app/proxy.py:57-87` skips session tracking for OpenCode title-generation requests, but `inject_memory` is still called afterward at `app/proxy.py:89-92`. `session_started` is computed at `app/proxy.py:82` and never used.

Impact: title-generation calls can receive project memory and file-tree context. Normal chat calls also receive the full file tree every turn, increasing token usage and potentially repeating context already injected earlier.

Recommendation: either inject only when `session_started` is true, or intentionally keep every-turn injection and remove the stale `session_started` variable/comment. Also skip injection for title requests unless there is a strong reason not to.

### High: Failed memory save can leave sessions active and chat logs uncleared

`app/session.py:34-41` stores memory, improves memory, clears the chat log, and ends the session in sequence without `try/finally`.

Impact: if `store_memory` or `improve_memory` fails, `clear_chat_log()` and `end_session()` do not run. The `history` command already showed old sessions marked `[active]`, which may be explained by shutdown/save failure or interrupted process shutdown.

Recommendation: wrap memory persistence so session cleanup always happens. Log memory-save errors, then still clear/end according to the desired data-retention policy.

### Medium: Packaging metadata does not declare runtime dependencies

`pyproject.toml` defines the package and console script but has no `[project].dependencies`. Dependencies live only in `requirements.txt`.

Impact: `pip install .` can install the `climem` command without installing FastAPI/Uvicorn/HTTPX/python-dotenv/Cognee, producing runtime import failures.

Recommendation: add runtime dependencies to `pyproject.toml`, or switch fully to a requirements-driven install workflow and document it clearly in `README.md`.

### Medium: Provider configuration is not validated before forwarding

`app/proxy.py:94-109` builds an upstream request from `PROVIDER_BASE_URL` and `PROVIDER_API_KEY` without checking that they are set. `app/config.py` defaults missing values to empty strings.

Impact: a missing base URL creates an invalid or relative provider URL, and a missing key still sends `Authorization: Bearer `. The failure will surface late and unclearly.

Recommendation: validate required env vars at startup or before first request, and return a clear local error if configuration is incomplete.

### Medium: SQLite session identity can collide

`app/storage.py:48` uses second-resolution timestamps as `session_name`. `app/storage.py:105-109` ends sessions by `session_name`, not by row id.

Impact: two sessions created within the same second can share a name, and ending one can update multiple rows.

Recommendation: store the inserted row id as active session identity, or add a UUID/random suffix to `session_name` and make it unique.

### Medium: Project tree injection includes many non-source/local files

`app/filetree.py:3-15` ignores common caches but does not ignore `.env`, `.opencode`, `.codex`, `.agents`, `climem.egg-info`, generated reports, or other hidden/local metadata. `app/memory.py:232-238` injects the tree into provider requests.

Impact: file names only are exposed, not contents, but the tree can still reveal local tooling/private structure and waste tokens.

Recommendation: expand ignores, skip hidden files/directories by default, and consider a max-depth or max-entry limit.

### Medium: Recall failures are silently hidden

`app/memory.py:120-128` catches every exception from Cognee recall and returns an empty string.

Impact: the proxy keeps working, which is good, but memory recall can be broken for a long time with no visible signal.

Recommendation: log the exception at warning level with dataset/query metadata, without logging user content verbatim.

### Medium: The current `test/` folder is not a real test suite

`test/test_cognee.py:1-3` only imports Cognee and prints a message. `pytest` is not installed, and the actual sample scripts live in `scripts/`.

Impact: there is no automated safety net for proxy behavior, fact extraction, dataset naming, session rotation, or handler config edits.

Recommendation: add pytest as a dev dependency and create focused tests for pure functions first: `get_dataset_name`, `process_session`, `_flatten_results`, agent config transforms, and storage lifecycle with a temp DB.

### Low: OpenSpec/OpenCode command and skill docs are duplicated

The `.opencode/commands/opsx-*.md` files mirror `.opencode/skills/*/SKILL.md`.

Impact: they can drift over time.

Recommendation: keep one as the source of truth, or accept the duplication but audit it during OpenSpec updates.

### Low: Cleanup and style debt

Examples:

- `app/main.py:2`, `app/main.py:8-9`, `app/main.py:13`, and `app/main.py:15-19` contain unused imports.
- `app/filter.py:516` imports `sys` but does not use it.
- `app/proxy.py:89-92` has awkward indentation.
- Several modules use direct `print()` for operational messages.

Impact: low runtime risk, but it increases noise and makes real issues harder to spot.

Recommendation: run a formatter/linter once the behavior fixes above are decided.

## Dead Or Questionable Code

| item | status | recommendation |
|---|---|---|
| `session_started` in `app/proxy.py` | computed but unused | use to gate injection or remove |
| `/chat-log` endpoint | debug-only and sensitive | remove or protect |
| `test/test_cognee.py` | print-only smoke check | move to `scripts/` or replace with assertion test |
| `scripts/remember_sample.py` | useful manual script | keep under `scripts/`, not tests |
| `scripts/recall_sample.py` | useful manual script | keep under `scripts/`, not tests |
| `.opencode` command/skill pairs | duplicated docs | review source-of-truth strategy |

## Suggested Fix Order

1. Make CLI imports lazy so help/history do not initialize Cognee.
2. Protect or remove `/chat-log` and full-body debug logging.
3. Decide memory injection policy, then fix `session_started` and title-request behavior.
4. Make `save_current_session` cleanup robust with `try/finally`.
5. Add startup/provider configuration validation.
6. Move session state away from single global variables if multi-session use matters.
7. Add real pytest tests and declare dev/runtime dependencies.
8. Clean imports/formatting and deduplicate OpenSpec/OpenCode docs.

## Overall Assessment

The project is coherent and the main shape is understandable: local OpenAI-compatible proxy, session log, heuristic fact extraction, Cognee memory, and agent config helpers. The risky parts are mostly operational rather than architectural: global state, sensitive debug surfaces, import-time side effects, and weak failure cleanup. I would keep the core design, but harden the request/session lifecycle before adding more features.
