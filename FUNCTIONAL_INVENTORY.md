# CliMEM Functional Inventory

Generated from the current workspace on 2026-07-04.

Scope included: tracked and untracked project files in this repo, excluding generated/external artifacts such as `.git/`, `.venv/`, `climem.egg-info/`, `.pytest_cache/`, and `__pycache__/`.

Note: `.env` is inventoried by role and variable names only. Secret values are intentionally not reproduced.

## `.env`

Purpose: Local environment configuration for provider, model, Cognee, embedding, and graph database settings.

Functions: none.

Depends on / used by: Loaded by `app.config` via `python-dotenv`; Cognee may also read related settings from the process environment.

Smells / notes: Contains secret-bearing variables. Both `PROVIDER_*` and older-looking `LLM_*` groups exist, which may be migration leftovers.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| None | Environment configuration only | yes | keep |

## `.gitignore`

Purpose: Keeps Python caches, virtualenvs, environment files, databases, test caches, build output, IDE files, and OS metadata out of git.

Functions: none.

Depends on / used by: Git.

Smells / notes: Good baseline. It ignores `*.egg-info/`, but the generated `climem.egg-info/` directory still exists locally.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| None | Git ignore rules only | yes | keep |

## `.opencode/commands/opsx-apply.md`

Purpose: OpenCode command instructions for implementing tasks from an OpenSpec change.

Functions: none.

Depends on / used by: OpenCode command system; OpenSpec CLI.

Smells / notes: Duplicates much of `.opencode/skills/openspec-apply-change/SKILL.md`, so the two may drift.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| None | OpenCode apply command instructions | unclear | review |

## `.opencode/commands/opsx-archive.md`

Purpose: OpenCode command instructions for archiving completed OpenSpec changes.

Functions: none.

Depends on / used by: OpenCode command system; OpenSpec CLI.

Smells / notes: Duplicates the matching skill file with small wording differences.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| None | OpenCode archive command instructions | unclear | review |

## `.opencode/commands/opsx-explore.md`

Purpose: OpenCode command instructions for non-implementation exploration of ideas, code, and requirements.

Functions: none.

Depends on / used by: OpenCode command system; OpenSpec CLI.

Smells / notes: Duplicates the matching skill file.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| None | OpenCode explore command instructions | unclear | review |

## `.opencode/commands/opsx-propose.md`

Purpose: OpenCode command instructions for creating OpenSpec proposal/design/tasks artifacts.

Functions: none.

Depends on / used by: OpenCode command system; OpenSpec CLI.

Smells / notes: Duplicates the matching skill file.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| None | OpenCode propose command instructions | unclear | review |

## `.opencode/commands/opsx-sync.md`

Purpose: OpenCode command instructions for syncing OpenSpec delta specs into main specs.

Functions: none.

Depends on / used by: OpenCode command system; OpenSpec CLI.

Smells / notes: Duplicates the matching skill file.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| None | OpenCode sync command instructions | unclear | review |

## `.opencode/skills/openspec-apply-change/SKILL.md`

Purpose: OpenCode skill definition and workflow for applying OpenSpec change tasks.

Functions: none.

Depends on / used by: OpenCode skills; OpenSpec CLI.

Smells / notes: Near-duplicate of `.opencode/commands/opsx-apply.md`.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| None | OpenSpec apply skill instructions | unclear | review |

## `.opencode/skills/openspec-archive-change/SKILL.md`

Purpose: OpenCode skill definition and workflow for archiving completed OpenSpec changes.

Functions: none.

Depends on / used by: OpenCode skills; OpenSpec CLI.

Smells / notes: Near-duplicate of `.opencode/commands/opsx-archive.md`.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| None | OpenSpec archive skill instructions | unclear | review |

## `.opencode/skills/openspec-explore/SKILL.md`

Purpose: OpenCode skill definition for exploratory OpenSpec/codebase thinking without implementation.

Functions: none.

Depends on / used by: OpenCode skills; OpenSpec CLI.

Smells / notes: Near-duplicate of `.opencode/commands/opsx-explore.md`.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| None | OpenSpec explore skill instructions | unclear | review |

## `.opencode/skills/openspec-propose/SKILL.md`

Purpose: OpenCode skill definition and workflow for proposing OpenSpec changes.

Functions: none.

Depends on / used by: OpenCode skills; OpenSpec CLI.

Smells / notes: Near-duplicate of `.opencode/commands/opsx-propose.md`.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| None | OpenSpec propose skill instructions | unclear | review |

## `.opencode/skills/openspec-sync-specs/SKILL.md`

Purpose: OpenCode skill definition and workflow for syncing OpenSpec delta specs.

Functions: none.

Depends on / used by: OpenCode skills; OpenSpec CLI.

Smells / notes: Near-duplicate of `.opencode/commands/opsx-sync.md`.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| None | OpenSpec sync skill instructions | unclear | review |

## `PROJECT_AUDIT.md`

Purpose: Human-readable audit report summarizing current risks, verification, and recommended fix order.

Functions: none.

Depends on / used by: Documentation only.

Smells / notes: Generated working document. Keep if useful for planning; remove before release if you do not want repo-local audit artifacts.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| None | Audit documentation only | no | review |

## `FUNCTIONAL_INVENTORY.md`

Purpose: This working document inventories the project file by file for keep/refactor/cut decisions.

Functions: none.

Depends on / used by: Humans reviewing the codebase.

Smells / notes: Generated documentation. Keep while planning; remove or archive if it should not ship with the project.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| None | Functional inventory documentation | no | review |

## `README.md`

Purpose: Minimal project title.

Functions: none.

Depends on / used by: Humans browsing the repo or package index.

Smells / notes: Too sparse for setup, configuration, or usage. Needs install/run/configure examples.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| None | Project title only | yes | review |

## `app/__init__.py`

Purpose: Marks `app` as an importable Python package.

Functions: none.

Depends on / used by: Python package imports.

Smells / notes: Empty package marker; normal.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| None | Package marker file | yes | keep |

## `app/agent_handlers/__init__.py`

Purpose: Registers per-agent configure/restore handlers in one dispatch table.

Functions: none.

Depends on / used by: Imports `configure` and `restore` from `claude.py`, `codex.py`, and `opencode.py`; `app.cli` uses `HANDLERS`.

Smells / notes: Eagerly imports all handlers. Fine at this size.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| None | Agent handler registry only | yes | keep |

## `app/agent_handlers/claude.py`

Purpose: Configures and restores Claude Code settings so Claude uses the local CliMEM proxy.

### `configure(config_path: Path, base_url: str)`

Plain English: Creates the Claude config directory if needed, backs up an existing JSON settings file, loads or creates settings, sets `env.ANTHROPIC_BASE_URL` to the CliMEM base URL, and writes the file.

Calls / depends on: `Path.parent.mkdir`, `Path.exists`, `Path.with_suffix`, `shutil.copy2`, `json.load`, `json.dump`.

Used elsewhere: Yes. Registered in `HANDLERS["claude"]["configure"]` and called by `cmd_configure`.

Smells / notes: Backup suffix is hardcoded instead of using `AGENTS["claude"]["backup_suffix"]`. Invalid JSON raises raw errors.

### `restore(config_path: Path)`

Plain English: Restores Claude settings by copying the `.json.bak` backup over the active config.

Calls / depends on: `Path.with_suffix`, `Path.exists`, `shutil.copy2`.

Used elsewhere: Yes. Registered in `HANDLERS["claude"]["restore"]` and called by `cmd_restore`.

Smells / notes: Missing backup gets a clear `FileNotFoundError`, but CLI does not format it for users.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| `configure` | Point Claude Code at CliMEM | yes | keep |
| `restore` | Restore Claude Code config backup | yes | keep |

## `app/agent_handlers/codex.py`

Purpose: Configures and restores Codex CLI config so Codex uses the local CliMEM proxy.

### `configure(config_path: Path, base_url: str)`

Plain English: Creates the Codex config directory if needed, backs up an existing config, replaces the first `openai_base_url` line or appends one, and writes the config.

Calls / depends on: `Path.parent.mkdir`, `Path.exists`, `Path.with_suffix`, `Path.read_text`, `Path.write_text`, `shutil.copy2`.

Used elsewhere: Yes. Registered in `HANDLERS["codex"]["configure"]` and called by `cmd_configure`.

Smells / notes: Edits TOML as raw lines instead of using a TOML parser; can behave oddly with duplicate keys, commented keys, or table-specific settings.

### `restore(config_path: Path)`

Plain English: Restores Codex config by copying the `.toml.bak` backup over the active config.

Calls / depends on: `Path.with_suffix`, `Path.exists`, `shutil.copy2`.

Used elsewhere: Yes. Registered in `HANDLERS["codex"]["restore"]` and called by `cmd_restore`.

Smells / notes: Backup suffix is hardcoded, duplicating metadata from `app/agents.py`.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| `configure` | Point Codex CLI at CliMEM | yes | review |
| `restore` | Restore Codex config backup | yes | keep |

## `app/agent_handlers/opencode.py`

Purpose: Configures and restores OpenCode settings so OpenCode uses CliMEM as an OpenAI-compatible provider.

### `configure(config_path: Path, base_url: str)`

Plain English: Creates the OpenCode config directory if needed, backs up an existing JSON config, loads or creates config data, adds a `climem` provider/model, selects `climem/proxy`, and writes the JSON file.

Calls / depends on: `Path.parent.mkdir`, `Path.exists`, `Path.with_suffix`, `shutil.copy2`, `json.load`, `json.dump`.

Used elsewhere: Yes. Registered in `HANDLERS["opencode"]["configure"]` and called by `cmd_configure`.

Smells / notes: Duplicates much of the Claude JSON backup/write flow. Invalid JSON raises raw errors.

### `restore(config_path: Path)`

Plain English: Restores OpenCode config by copying the `.json.bak` backup over the active config.

Calls / depends on: `Path.with_suffix`, `Path.exists`, `shutil.copy2`.

Used elsewhere: Yes. Registered in `HANDLERS["opencode"]["restore"]` and called by `cmd_restore`.

Smells / notes: Same backup suffix duplication as other handlers.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| `configure` | Add CliMEM provider to OpenCode | yes | keep |
| `restore` | Restore OpenCode config backup | yes | keep |

## `app/agents.py`

Purpose: Defines supported agent metadata and the local CliMEM proxy base URL.

Functions: none.

Depends on / used by: `app.cli` uses `AGENTS` and `CLIMEM_BASE_URL`; handler modules conceptually correspond to `handler`, `format`, and `backup_suffix`.

Smells / notes: `handler`, `backup_suffix`, `format`, and `supported` are metadata but are not fully used by handler code. Backup suffixes are duplicated in handler modules.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| None | Agent metadata constants only | yes | keep |

## `app/cli.py`

Purpose: Provides the `climem` command-line interface for starting the proxy, configuring/restoring agents, forgetting memory, and showing session history.

### `cmd_start()`

Plain English: Runs the FastAPI app with Uvicorn on `127.0.0.1:8000` with reload enabled.

Calls / depends on: `uvicorn.run("app.main:app", host=..., port=..., reload=True)`.

Used elsewhere: Yes. Called by `main()` for `climem start`.

Smells / notes: `reload=True` is development-friendly but surprising for production CLI use.

### `cmd_configure(agent)`

Plain English: Looks up the selected agent and calls its configure handler with the agent config path and CliMEM base URL.

Calls / depends on: `AGENTS`, `HANDLERS`, `CLIMEM_BASE_URL`.

Used elsewhere: Yes. Called by `main()` for `climem configure <agent>`.

Smells / notes: No friendly error handling for malformed config files or missing backups.

### `cmd_restore(agent)`

Plain English: Looks up the selected agent and calls its restore handler with the agent config path.

Calls / depends on: `AGENTS`, `HANDLERS`.

Used elsewhere: Yes. Called by `main()` for `climem restore <agent>`.

Smells / notes: Raw `FileNotFoundError` can reach users.

### `cmd_forget(yes: bool)`

Plain English: Computes the current project's dataset name, optionally asks for confirmation, and deletes that project's Cognee memory.

Calls / depends on: local import of `forget_memory` and `get_dataset_name`, `Path.cwd`, `input`, `asyncio.run`.

Used elsewhere: Yes. Called by `main()` for `climem forget`.

Smells / notes: The file also imports `get_dataset_name` at module load, so Cognee still initializes for non-memory commands. Remove the top-level `from app.memory import get_dataset_name`.

### `cmd_history(limit: int)`

Plain English: Opens the session database, fetches recent sessions, closes the database, and prints each row.

Calls / depends on: `init_database`, `get_recent_sessions`, `close_database`.

Used elsewhere: Yes. Called by `main()` for `climem history`.

Smells / notes: Initializes/prints database path as a side effect. Output ignores `started_at` and `ended_at` even though it fetches them.

### `main()`

Plain English: Builds the argument parser, defines subcommands, parses the command line, and dispatches to the matching command function.

Calls / depends on: `argparse`, `cmd_start`, `cmd_configure`, `cmd_restore`, `cmd_forget`, `cmd_history`.

Used elsewhere: Yes. Registered in `pyproject.toml` as `climem = "app.cli:main"` and called when running `python -m app.cli`.

Smells / notes: No required subcommand, so empty invocation prints help. That is acceptable.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| `cmd_start` | Start local FastAPI proxy | yes | keep |
| `cmd_configure` | Configure selected CLI agent | yes | keep |
| `cmd_restore` | Restore selected agent config | yes | keep |
| `cmd_forget` | Delete current project memory | yes | review |
| `cmd_history` | Print recent stored sessions | yes | keep |
| `main` | Parse and route CLI commands | yes | keep |

## `app/config.py`

Purpose: Loads environment variables and exposes provider/model constants used by the proxy.

Functions: none.

Depends on / used by: `app.proxy` imports provider settings, model aliases, CLI tool, and API key fingerprint.

Smells / notes: Missing provider URL/API key default to empty strings with no validation. `API_KEY_FINGERPRINT` hashes an empty string if no key is set.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| None | Runtime configuration constants only | yes | review |

## `app/filetree.py`

Purpose: Builds a readable tree of project file and directory names for prompt injection.

### `build_file_tree(root: Path) -> str`

Plain English: Creates the first tree line from the root name, recursively walks the directory, and returns the tree as text.

Calls / depends on: `_walk`, `Path.name`.

Used elsewhere: Yes. Called by `memory.inject_memory`.

Smells / notes: Includes file names only, not contents. Can still expose local file names in prompts.

### `_walk(directory: Path, prefix: str, lines: list[str])`

Plain English: Lists child entries, skips ignored names, appends tree branch lines, and recurses into directories.

Calls / depends on: `Path.iterdir`, `Path.is_file`, `Path.is_dir`, itself recursively, `IGNORE`.

Used elsewhere: Yes, internally by `build_file_tree`.

Smells / notes: Ignores common caches but not all hidden/local files such as `.env`, `.opencode`, `.codex`, `.agents`, or audit docs. No max depth/entry count.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| `build_file_tree` | Return readable project tree | yes | keep |
| `_walk` | Recursively append tree entries | yes | review |

## `app/filter.py`

Purpose: Maintains the in-memory chat log and extracts clean, categorized memory facts from raw chat transcripts.

### `add_message(role: str, content: str)`

Plain English: Adds one role/content message dictionary to the current in-memory chat log.

Calls / depends on: module-level `chat_log`.

Used elsewhere: Yes. Called by `proxy.chat` for user and assistant messages.

Smells / notes: Global mutable state can mix concurrent sessions.

### `get_chat_log()`

Plain English: Returns the current in-memory chat log list.

Calls / depends on: module-level `chat_log`.

Used elsewhere: Yes. Used by `main.chat_log` and `session.save_current_session`.

Smells / notes: Returns the live list, so callers can mutate it.

### `clear_chat_log()`

Plain English: Empties the current in-memory chat log.

Calls / depends on: module-level `chat_log`.

Used elsewhere: Yes. Used by `session.save_current_session`.

Smells / notes: Global clearing is unsafe for concurrent sessions.

### `_strip_code(text: str) -> str`

Plain English: Removes fenced code blocks, inline code, and duplicate spaces from transcript text.

Calls / depends on: `_FENCED_CODE_RE`, `_INLINE_CODE_RE`, `_WHITESPACE_RE`.

Used elsewhere: Yes. Called by `_pair_blocks`.

Smells / notes: Inline code may contain important filenames or commands, so useful facts can be lost.

### `_try_parse_jsonl(raw_log: str) -> list[Exchange] | None`

Plain English: Tries to parse a raw transcript as JSON Lines with role/content fields.

Calls / depends on: `json.loads`, `_pair_blocks`.

Used elsewhere: Yes. Called by `_parse_chat_log`.

Smells / notes: One non-JSON line makes it reject the whole log.

### `_pair_blocks(blocks: list[tuple[str, str]]) -> list[Exchange]`

Plain English: Converts adjacent user/assistant role blocks into `Exchange` objects.

Calls / depends on: `_USER_LABELS`, `_ASSISTANT_LABELS`, `_strip_code`, `Exchange`.

Used elsewhere: Yes. Used by every parser variant.

Smells / notes: Skips non-adjacent or tool/system-heavy transcripts.

### `_try_parse_labeled(raw_log: str) -> list[Exchange] | None`

Plain English: Parses transcripts that mark turns with labels like `User:` or `Assistant:`.

Calls / depends on: `_LABEL_LINE_RE`, `_pair_blocks`.

Used elsewhere: Yes. Called by `_parse_chat_log`.

Smells / notes: A prose line that starts with a known label can be misread as a turn boundary.

### `_try_parse_prompt_style(raw_log: str) -> list[Exchange] | None`

Plain English: Parses transcripts where user prompts begin with `>` and assistant output follows.

Calls / depends on: `_PROMPT_LINE_RE`, `_pair_blocks`.

Used elsewhere: Yes. Called by `_parse_chat_log`.

Smells / notes: Quoted text beginning with `>` can create false turns.

### `_parse_chat_log(raw_log: str) -> list[Exchange]`

Plain English: Tries JSONL, labeled text, then prompt-style parsing and returns the detected exchanges.

Calls / depends on: `_try_parse_jsonl`, `_try_parse_labeled`, `_try_parse_prompt_style`.

Used elsewhere: Yes. Called by `process_session`.

Smells / notes: Returns an empty list silently for unknown formats.

### `_is_dead_end_or_reverted(window: list[Exchange], idx: int) -> bool`

Plain English: Looks at nearby later exchanges for revert/abandon cues with enough shared vocabulary to treat the current exchange as obsolete.

Calls / depends on: `_REVERT_CUES`, `re.findall`.

Used elsewhere: Yes. Called by `process_session`.

Smells / notes: Heuristic may miss real reversions or suppress unrelated facts.

### `_split_sentences(text: str) -> list[str]`

Plain English: Splits assistant text into sentence-like chunks.

Calls / depends on: `re.split`.

Used elsewhere: Yes. Called by `process_session`.

Smells / notes: Simple punctuation splitting can mishandle abbreviations.

### `_has_dangling_pronoun(sentence: str) -> bool`

Plain English: Checks whether a sentence starts with a pronoun after removing small leading filler words.

Calls / depends on: `re.sub`.

Used elsewhere: Yes. Called by `_make_self_contained`.

Smells / notes: `_PRONOUN_RE` exists but is not used; function checks only first-word pronouns.

### `_categorize_sentence(sentence: str) -> str | None`

Plain English: Classifies a sentence as decision, convention, open thread, state, or not a fact based on cue phrases.

Calls / depends on: `_DECISION_CUES`, `_CONVENTION_CUES`, `_OPEN_THREAD_CUES`, `_RESOLVED_CUES`, `_STATE_CUES`.

Used elsewhere: Yes. Called by `process_session`.

Smells / notes: Category priority is hardcoded by if-order.

### `_make_self_contained(sentence: str, topic_subject: str) -> str | None`

Plain English: Rewrites simple pronoun-leading sentences using a subject derived from the user message, or drops ambiguous sentences.

Calls / depends on: `_has_dangling_pronoun`, `re.sub`, `re.match`.

Used elsewhere: Yes. Called by `process_session`.

Smells / notes: Conservative and grammar-sensitive; may drop useful facts.

### `_derive_topic_subject(user_text: str) -> str`

Plain English: Pulls a short subject-like phrase from the user's message for pronoun repair.

Calls / depends on: `re.sub`.

Used elsewhere: Yes. Called by `process_session`.

Smells / notes: First-eight-word heuristic can produce awkward subjects.

### `_normalize_for_dedup(text: str) -> str`

Plain English: Lowercases text and removes punctuation/extra spacing for duplicate comparison.

Calls / depends on: `re.sub`.

Used elsewhere: Yes. Called by `_dedup_facts`.

Smells / notes: Token-level dedup, not semantic dedup.

### `_dedup_facts(facts: list[dict]) -> list[dict]`

Plain English: Removes facts that overlap heavily with facts already kept.

Calls / depends on: `_normalize_for_dedup`.

Used elsewhere: Yes. Called by `process_session`.

Smells / notes: O(n^2), fine for short sessions; could merge distinct similar facts.

### `process_session(chat_log: str, working_directory: str, session_name: str) -> list[dict]`

Plain English: Parses a raw chat transcript, filters small talk/exploration/reverted work, extracts categorized fact sentences, repairs simple pronouns, removes duplicates, and returns fact dictionaries.

Calls / depends on: `_parse_chat_log`, `_SMALL_TALK_RE`, `_EXPLORATORY_CUES`, `_is_dead_end_or_reverted`, `_derive_topic_subject`, `_split_sentences`, `_categorize_sentence`, `_make_self_contained`, `_WHITESPACE_RE`, `_dedup_facts`.

Used elsewhere: Yes. Called by `session.save_current_session` and the module's manual CLI runner.

Smells / notes: `working_directory` and `session_name` are accepted but not used in the returned facts. Manual runner imports unused `sys`.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| `add_message` | Append message to chat log | yes | review |
| `get_chat_log` | Return in-memory chat log | yes | review |
| `clear_chat_log` | Clear in-memory chat log | yes | review |
| `_strip_code` | Remove code before fact extraction | yes | keep |
| `_try_parse_jsonl` | Parse JSONL transcript logs | yes | keep |
| `_pair_blocks` | Pair user/assistant transcript blocks | yes | keep |
| `_try_parse_labeled` | Parse labeled transcript logs | yes | keep |
| `_try_parse_prompt_style` | Parse prompt-style transcript logs | yes | keep |
| `_parse_chat_log` | Auto-detect transcript format | yes | keep |
| `_is_dead_end_or_reverted` | Skip abandoned or reverted facts | yes | review |
| `_split_sentences` | Split text into sentences | yes | keep |
| `_has_dangling_pronoun` | Detect ambiguous leading pronouns | yes | review |
| `_categorize_sentence` | Categorize fact by cue phrases | yes | keep |
| `_make_self_contained` | Repair simple pronoun references | yes | review |
| `_derive_topic_subject` | Infer subject from user prompt | yes | review |
| `_normalize_for_dedup` | Normalize text for deduping | yes | keep |
| `_dedup_facts` | Remove near-duplicate facts | yes | keep |
| `process_session` | Extract memory facts from chat | yes | review |

## `app/main.py`

Purpose: Defines the FastAPI app, lifecycle hooks, and simple health/debug endpoints.

### `lifespan(app: FastAPI)`

Plain English: Initializes SQLite session storage at startup, then saves the current session and closes the database during shutdown.

Calls / depends on: `init_database`, `save_current_session`, `close_database`.

Used elsewhere: Yes. Passed to `FastAPI(lifespan=lifespan)`.

Smells / notes: Unused imports: `Path`, `process_session`, `clear_chat_log`, `end_session`, `get_current_session`, `get_dataset_name`, `store_memory`, `improve_memory`. Prints during shutdown.

### `health()`

Plain English: Returns a small JSON response showing the server is alive.

Calls / depends on: FastAPI route decorator.

Used elsewhere: Yes. Bound to `GET /`.

Smells / notes: Fine.

### `chat_log()`

Plain English: Returns the current in-memory chat log.

Calls / depends on: `get_chat_log`.

Used elsewhere: Yes. Bound to `GET /chat-log`.

Smells / notes: Debug endpoint exposes conversation content without auth.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| `lifespan` | Manage startup and shutdown | yes | keep |
| `health` | Report server health | yes | keep |
| `chat_log` | Expose current chat log | yes | review |

## `app/memory.py`

Purpose: Wraps Cognee dataset naming, memory storage, recall, improvement, forgetting, and prompt injection.

### `get_dataset_name(working_directory: str) -> str`

Plain English: Converts a working directory path into a stable Cognee dataset name using the folder name plus a short SHA-256 hash.

Calls / depends on: `re.sub`, `hashlib.sha256`.

Used elsewhere: Yes. Used by CLI forget, session save, memory injection, and sample scripts.

Smells / notes: Does not resolve symlinks or normalize `..`, so equivalent paths can create different datasets.

### `store_memory(facts: Iterable[dict], dataset_name: str) -> None`

Plain English: Turns extracted fact dictionaries into `[category] text` strings, adds them to Cognee, and runs Cognee graph building.

Calls / depends on: `cognee.add`, `cognee.cognify`.

Used elsewhere: Yes. Called by `session.save_current_session`.

Smells / notes: No local error handling. Cognee failures propagate to `save_current_session`, whose `finally` still clears and ends the session.

### `search_memory(query: str, dataset_name: str) -> str`

Plain English: Queries Cognee for relevant project context and returns flattened text, or an empty string if recall fails.

Calls / depends on: `cognee.recall`, `SearchType.GRAPH_COMPLETION`, `_flatten_results`.

Used elsewhere: Yes. Called by `inject_memory`.

Smells / notes: Catches all exceptions silently, hiding recall failures.

### `_flatten_results(results) -> str`

Plain English: Converts Cognee result strings, dictionaries, or objects into a deduplicated newline-separated text block.

Calls / depends on: `isinstance`, `getattr`.

Used elsewhere: Yes. Called by `search_memory`.

Smells / notes: Only reads `.text` from unknown objects.

### `improve_memory(dataset_name: str) -> None`

Plain English: Runs Cognee's dataset improvement/reconciliation step.

Calls / depends on: `cognee.improve`.

Used elsewhere: Yes. Called by `session.save_current_session`.

Smells / notes: No error handling.

### `forget_memory(dataset_name: str) -> None`

Plain English: Deletes memory for one project dataset.

Calls / depends on: `cognee.forget`.

Used elsewhere: Yes. Called by `cli.cmd_forget`.

Smells / notes: No dry-run or existence check.

### `inject_memory(body: dict, working_directory: str) -> dict`

Plain English: Builds a system message containing recalled memory and the current project tree, then inserts or appends it to the outgoing chat request.

Calls / depends on: `get_dataset_name`, `build_file_tree`, `search_memory`, `Path`.

Used elsewhere: Yes. Called by `proxy.chat` for non-title chat requests.

Smells / notes: Injects file tree every real request, which may be costly and expose file names. Mutates the input `body`.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| `get_dataset_name` | Build stable project dataset name | yes | keep |
| `store_memory` | Store extracted facts in Cognee | yes | keep |
| `search_memory` | Recall project memory text | yes | review |
| `_flatten_results` | Normalize Cognee result objects | yes | keep |
| `improve_memory` | Reconcile Cognee memory graph | yes | keep |
| `forget_memory` | Delete current project memory | yes | keep |
| `inject_memory` | Add memory context to request | yes | review |

## `app/proxy.py`

Purpose: Implements the OpenAI-compatible FastAPI chat proxy that records sessions, injects memory, forwards provider requests, and streams responses.

### `chat(request: Request)`

Plain English: Reads the incoming chat body, resolves model aliases, detects title-generation calls, starts/rotates sessions, records user turns, injects memory for real conversations, forwards the request to the configured provider, and returns the provider response stream.

Calls / depends on: `request.json`, `MODEL_MAP`, `get_current_session`, `ensure_session`, `save_current_session`, `start_session`, `add_message`, `inject_memory`, `httpx.AsyncClient`, `StreamingResponse`, nested `stream_generator`.

Used elsewhere: Yes. Bound to `POST /v1/chat/completions`.

Smells / notes: `previous_session` is assigned but no longer used. `logger.debug(body)` can log sensitive prompts/secrets. Provider URL/API key are not validated before use.

### `stream_generator()`

Plain English: Reads upstream streaming chunks, extracts assistant text from OpenAI-style `data:` JSON events for session logging, yields chunks unchanged, and closes HTTP resources.

Calls / depends on: `response.aiter_text`, `json.loads`, `add_message`, `response.aclose`, `client.aclose`.

Used elsewhere: Yes, internally by `chat`.

Smells / notes: Only captures OpenAI-style delta text; nonstandard stream formats pass through but will not be logged well.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| `chat` | Proxy chat completions request | yes | review |
| `stream_generator` | Stream response and log assistant | yes | keep |

## `app/session.py`

Purpose: Saves the current in-memory chat session into Cognee memory and ends the SQLite session.

### `save_current_session(reason: str)`

Plain English: Gets the in-memory chat log, ends empty sessions, formats messages into a raw transcript, extracts facts, stores and improves memory, then always clears the chat log and ends the SQLite session.

Calls / depends on: `get_chat_log`, `end_session`, `get_current_session`, `clear_chat_log`, `process_session`, `get_dataset_name`, `store_memory`, `improve_memory`, `Path.cwd`.

Used elsewhere: Yes. Called by FastAPI shutdown and by `proxy.chat` when session metadata changes.

Smells / notes: `finally` cleanup is good, but Cognee errors still propagate to caller. Transcript formatting can be confused if message content contains role-like lines.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| `save_current_session` | Persist and close current session | yes | keep |

## `app/storage.py`

Purpose: Manages SQLite session records and process-local active session metadata.

### `init_database()`

Plain English: Creates the app data directory, opens `~/.climem/sessions.db`, creates the `sessions` table if needed, and stores the connection globally.

Calls / depends on: `APP_DIR.mkdir`, `sqlite3.connect`, SQL `CREATE TABLE`.

Used elsewhere: Yes. Called by app lifespan and CLI history.

Smells / notes: Reinitializing can replace the global connection without closing an old one. Prints directly.

### `start_session(working_directory, cli_tool, provider_name, model, api_key_fingerprint)`

Plain English: Creates a timestamp session name, stores active session metadata in globals, inserts the session into SQLite, and prints session details.

Calls / depends on: global `connection`, `datetime.now`, SQL `INSERT`.

Used elsewhere: Yes. Called by `ensure_session` and `proxy.chat` after rotation.

Smells / notes: Assumes `init_database` already ran. Second-resolution session names can collide.

### `ensure_session(working_directory, cli_tool, provider_name, model, api_key_fingerprint)`

Plain English: Starts a session if none exists, otherwise compares metadata and returns a reason if a new session should replace the current one.

Calls / depends on: `start_session`, module-level active session globals.

Used elsewhere: Yes. Called by `proxy.chat`.

Smells / notes: Returns `None` both for "created a new session" and "no rotation needed".

### `end_session(ended_reason='normal_shutdown')`

Plain English: Marks the active session row ended, commits the end reason/time, prints, and clears active session globals.

Calls / depends on: global `connection`, SQL `UPDATE`, `datetime.now`.

Used elsewhere: Yes. Called by `session.save_current_session`; imported but unused in `main.py`.

Smells / notes: Updates by `session_name` instead of row id, so collisions could update multiple rows.

### `close_database()`

Plain English: Closes the global SQLite connection if open and clears it.

Calls / depends on: global `connection`.

Used elsewhere: Yes. Called by app shutdown and CLI history.

Smells / notes: Does not reset active session globals.

### `get_current_session()`

Plain English: Returns the active session name or `None`.

Calls / depends on: module-level `_session_name`.

Used elsewhere: Yes. Called by `proxy.chat` and `session.save_current_session`; imported but unused in `main.py`.

Smells / notes: Exposes only the name, not row id or metadata.

### `get_recent_sessions(limit=5)`

Plain English: Fetches recent session rows from SQLite, newest first.

Calls / depends on: global `connection`, SQL `SELECT`.

Used elsewhere: Yes. Called by `cli.cmd_history`.

Smells / notes: Returns raw tuples instead of named objects.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| `init_database` | Initialize local session database | yes | keep |
| `start_session` | Create active session record | yes | keep |
| `ensure_session` | Start or rotate session state | yes | keep |
| `end_session` | Mark active session ended | yes | keep |
| `close_database` | Close SQLite database connection | yes | keep |
| `get_current_session` | Return active session name | yes | keep |
| `get_recent_sessions` | Fetch recent session history | yes | keep |

## `openspec/config.yaml`

Purpose: OpenSpec configuration selecting the `spec-driven` schema and leaving optional project context/rules placeholders.

Functions: none.

Depends on / used by: OpenSpec CLI and OpenCode OpenSpec commands/skills.

Smells / notes: Mostly placeholder comments. Add real project context if OpenSpec remains part of workflow.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| None | OpenSpec schema configuration | unclear | review |

## `pyproject.toml`

Purpose: Defines package build backend, project metadata, and the `climem` console script.

Functions: none.

Depends on / used by: Python packaging tools.

Smells / notes: Runtime dependencies are not declared in `[project]`; they only appear in `requirements.txt`. `pip install .` may install a broken CLI unless dependencies are installed separately.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| None | Package and console metadata | yes | review |

## `requirements.txt`

Purpose: Lists runtime Python dependencies for manual installation.

Functions: none.

Depends on / used by: `pip install -r requirements.txt`.

Smells / notes: Only Cognee is pinned. No dev dependencies such as `pytest`.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| None | Runtime dependency list | yes | keep |

## `scripts/recall_sample.py`

Purpose: Manual sample script that recalls Cognee memory for the current project dataset.

### `main()`

Signature: `async def main()`

Plain English: Computes the dataset name for the current working directory, asks Cognee what it knows about CliMEM, and prints the result.

Calls / depends on: `get_dataset_name`, `Path.cwd`, `cognee.recall`, `asyncio.run`.

Used elsewhere: Yes, as the script entry point under `if __name__ == "__main__"`; not imported by application code.

Smells / notes: Useful manual script, but not a test. Uses raw Cognee API instead of `app.memory.search_memory`, so it can drift from production recall behavior.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| `main` | Manually recall project memory | yes | review |

## `scripts/remember_sample.py`

Purpose: Manual sample script that writes a sample Cognee memory for the current project dataset.

### `main()`

Signature: `async def main()`

Plain English: Computes the dataset name for the current working directory, stores a sample "CliMEM uses FastAPI" memory through Cognee, and prints progress.

Calls / depends on: `get_dataset_name`, `Path.cwd`, `cognee.remember`, `asyncio.run`.

Used elsewhere: Yes, as the script entry point under `if __name__ == "__main__"`; not imported by application code.

Smells / notes: Useful smoke script, but it mutates real Cognee state. Stray comment says "Import this from your project".

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| `main` | Manually store sample memory | yes | review |

## `test/test_cognee.py`

Purpose: Minimal import smoke check for Cognee.

Functions: none.

Depends on / used by: Test runner if `pytest` is installed; imports `cognee` and prints immediately.

Smells / notes: Not a real assertion-based test. Import-time print is noisy. It may fail in environments without Cognee.

| function name | purpose in 5-10 words | used elsewhere? | keep/review/remove |
|---|---|---:|---|
| None | Cognee import smoke check | unclear | review |

# Project-Wide Summary

## Functions That Appear Duplicated Across Files

| functions/files | duplication | recommendation |
|---|---|---|
| `configure` in `claude.py`, `codex.py`, `opencode.py` | Same backup/create/load/write structure with agent-specific mutation | Extract backup helpers; keep mutation per agent |
| `restore` in `claude.py`, `codex.py`, `opencode.py` | Same backup-path check and copy behavior | Extract shared `restore_backup(config_path, suffix)` |
| `.opencode/commands/opsx-*.md` and `.opencode/skills/*/SKILL.md` | Matching command and skill workflows are duplicated | Choose one source of truth or generate one from the other |
| `scripts/remember_sample.py::main` and `scripts/recall_sample.py::main` | Same dataset-name and print scaffolding | Keep as scripts or wrap shared sample helper |

## Functions Defined But Never Called

Strictly inside the current codebase, no application function is completely unreferenced:

- CLI helpers are called by `main()`.
- Agent handlers are referenced through `HANDLERS`.
- FastAPI handlers are bound by decorators.
- Private parser/memory helpers are called by their public entry points.
- Script `main()` functions are called by their own `if __name__ == "__main__"` blocks.

Near-dead or low-value items:

| item | why it looks questionable | recommendation |
|---|---|---|
| `test/test_cognee.py` | Print-only smoke file, no assertions | Replace with real test or move to `scripts/` |
| top-level `get_dataset_name` import in `app/cli.py` | Local lazy import also exists in `cmd_forget` | Remove top-level import |
| `/chat-log` endpoint in `app/main.py` | Debug endpoint exposing conversation data | Remove, protect, or development-gate |
| unused imports in `app/main.py` | Imported names not used in file | Remove |
| unused `previous_session` in `app/proxy.py` | Assigned but no longer used after injection change | Remove |

## Functions With Unclear Ownership Or Purpose

| function/area | unclear point | team decision |
|---|---|---|
| `filter.add_message`, `get_chat_log`, `clear_chat_log` | Chat log is global, not per session | Decide whether single-session local use is the contract |
| `memory.inject_memory` | Injects full project tree on each real chat request | Decide once-per-session vs every-request injection |
| `filter.process_session` | Accepts `working_directory` and `session_name` but does not use them | Keep signature for contract or remove unused params |
| `storage.start_session` / `end_session` | Session identity is second-resolution name | Use row id/UUID or accept collision risk |
| Agent handler backup metadata | `AGENTS` stores suffix/format, handlers hardcode them | Centralize metadata use or remove unused fields |
| OpenSpec/OpenCode support files | Many docs are present, but app CLI no longer exposes OpenSpec commands | Decide whether OpenSpec remains in this repo |

## Keep / Review / Remove Snapshot

Keep core runtime files: `app/proxy.py`, `app/session.py`, `app/storage.py`, `app/filter.py`, `app/memory.py`, `app/config.py`, `app/cli.py`, `app/agents.py`, `app/agent_handlers/*`, `app/filetree.py`.

Review before release: `.env` variable scheme, `README.md`, `pyproject.toml`, `/chat-log`, debug logging, global chat/session state, OpenSpec/OpenCode duplicated docs, sample scripts, and `test/test_cognee.py`.

Remove candidates: no clear source file should be removed immediately, but `test/test_cognee.py` should either become a real test or leave `test/`.
