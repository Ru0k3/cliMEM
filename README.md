# cliMEM 🧠

**A memory-aware wrapper for CLI coding agents.**

Your coding agent forgets everything the moment a session ends. cliMEM sits between your CLI agent and its AI provider, quietly building a persistent, per-project memory — so every new session starts with the context of every session before it.

Built with [Cognee](https://www.cognee.ai/)'s graph + vector memory engine. Works with **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)**, **[OpenCode](https://opencode.ai/)**, and **[Codex CLI](https://github.com/openai/codex)**.

<div align="center">

### 🎬 See cliMEM in action (60s)

[![Watch the cliMEM demo](https://img.youtube.com/vi/uCybQO2Kptk/maxresdefault.jpg)](https://youtu.be/uCybQO2Kptk?si=-4TKtDujUzYduSZI)

**[▶ Watch on YouTube](https://youtu.be/uCybQO2Kptk?si=-4TKtDujUzYduSZI)**

</div>

---

## 📚 Table of contents

- [The problem](#-the-problem)
- [The solution](#-the-solution)
- [Features](#-features)
- [Supported agents](#-supported-agents)
- [Getting started](#-getting-started)
- [Commands](#-commands)
- [Project structure](#-project-structure)
- [Team](#-team)

---

## ❌ The problem

CLI coding agents are **stateless**. Close the terminal and everything is gone — architectural decisions, naming conventions, the bug you were halfway through fixing. Next session, you re-explain it all from scratch.

## ✅ The solution

cliMEM is a local proxy that transparently intercepts the OpenAI-compatible traffic between your agent and its provider:

```
CLI Agent  →  cliMEM proxy (localhost:8000)  →  AI Provider
                    │
                    ├── injects remembered context into every request
                    ├── logs the conversation as it happens
                    └── on session end: extracts facts → stores in Cognee
```

- **Recall** — before each request is forwarded, cliMEM searches project memory and injects relevant context (plus a live file tree) into the system message. Your agent's original instructions are preserved, never replaced.
- **Remember** — when a session ends (or goes idle), the chat log is scanned by a fast, rule-based extractor that distills it into atomic, self-contained facts: `decision`, `state`, `convention`, `open_thread`, `architecture`, `api`, `implementation`, `database`, `identity`, `goal`. No extra LLM calls, no added cost or latency.
- **Scoped per project** — memory is keyed to your working directory, so contexts never bleed between projects.

## ✨ Features

| | Feature | Description |
|---|---|---|
| 🔌 | **Drop-in** | One command reconfigures your agent to route through cliMEM; one command restores it. Config backups are made automatically. |
| 🕸️ | **Graph + vector memory** | Powered by [Cognee](https://github.com/topoteretes/cognee) (local mode or hosted service). |
| 🧾 | **Session history** | Every session is recorded in SQLite (`climem history`). |
| 🧹 | **Forgettable** | Wipe a project's memory anytime with `climem forget`. |
| 🔀 | **Provider-agnostic** | Model aliases map to any OpenAI-compatible provider (Claude, Kimi, DeepSeek, Qwen, Gemini, Nemotron, and more) via `.env`. |

## 🤖 Supported agents

| Agent | Config managed |
|---|---|
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | `~/.claude/settings.json` |
| [OpenCode](https://opencode.ai/) | `~/.config/opencode/opencode.json` |
| [Codex CLI](https://github.com/openai/codex) | `~/.codex/config.toml` |

## 🚀 Getting started

**Requirements:** Python 3.10+, an API key from any OpenAI-compatible provider.

### 1. Install (one command)

```bash
git clone https://github.com/Ru0k3/cliMEM.git
cd cliMEM
./install.sh
```

The installer creates an isolated virtualenv, installs everything, links the
`climem` command into `~/.local/bin` (available in every terminal and shell,
no venv activation needed), and bootstraps your `.env`.

> Prefer manual setup? Create a venv, then:
> `pip install -r requirements.txt && pip install -e . && ln -s "$(pwd)/.venv/bin/climem" ~/.local/bin/climem`

### 2. Configure your provider

```bash
cp .env.example .env   # the installer already did this if .env didn't exist
```

Edit `.env` and set at minimum:

```env
PROVIDER_API_KEY=your-key-here
MODEL_PROXY=a-model-id-your-provider-supports
# Optional: backup models tried in order when the primary keeps failing
MODEL_FALLBACK=another-model-id,yet-another-model-id
```

Everything else (provider endpoints, cognee local-mode settings) has working
defaults. If you change `PROVIDER_API_KEY`, set `LLM_API_KEY` to the same key.

**Provider flakiness:** the proxy transparently retries transient provider
errors (429/5xx/404) once on the same model, then automatically walks down
`MODEL_FALLBACK` (comma-separated, in order) before surfacing an error to your
CLI. With a fallback configured, a rate-limited or cold-starting primary model
no longer breaks your chat — the next backup answers instead, and cliMEM logs
each hop (`model X unavailable — falling back to Y`).

### 3. Run

```bash
# Terminal 1 — start the memory proxy
climem start

# Terminal 2 — route your agent through it (backs up its config)
climem configure opencode      # or: claude / codex

# Use your agent exactly as before — memory just works.
cd ~/Projects/my-app && opencode
```

## ⌨️ Commands

```bash
climem start               # run the proxy server on 127.0.0.1:8000
climem configure <agent>   # route an agent through cliMEM (backs up config)
climem restore <agent>     # restore the agent's original config
climem history [--limit N] # show recent sessions across projects
climem forget [--yes]      # delete all memory for the current project
climem graph [--open]      # render this project's knowledge graph to HTML
climem --version
```

The only graphical surface is the knowledge-graph view: `climem graph`
writes a self-contained HTML file you can open in any browser. Everything
else lives in the terminal.

## 📁 Project structure

```
app/
├── cli.py            # climem command-line entry point
├── main.py           # FastAPI app + session lifecycle
├── proxy.py          # OpenAI-compatible passthrough proxy
├── memory.py         # Cognee store / search / forget + recall injection
├── filter.py         # rule-based chat-log → fact extraction
├── session.py        # idle watcher + end-of-session persistence
├── storage.py        # SQLite session records
├── filetree.py       # live project file-tree snapshot
├── display.py        # terminal UI (banner, history table)
├── semantic.py       # embedding fallback for fact extraction (local, offline)
└── agent_handlers/   # per-agent config writers (claude, opencode, codex)
patches/              # local cognee fixes; run apply-cognee-patches.sh after reinstall
test/
├── e2e.py            # end-to-end test (mock provider → proxy → cognee recall)
└── mock_provider.py  # OpenAI-compatible stub so tests spend no provider credits
```

## 🧪 End-to-end test

```bash
python test/e2e.py
```

Boots a mock OpenAI-compatible provider plus the real cliMEM server against
a throwaway project directory, pushes a conversation through the proxy,
shuts the server down (triggering the real cognee add/cognify/improve
pipeline), restarts, and asserts the remembered facts are re-injected on
the next request. Requires the cognee LLM credentials in `.env` (cognify
calls your configured LLM); the proxied chat hops themselves are free.

## 👥 Team

Built by **Team AIALCHEMISTS** for the [WeMakeDevs](https://www.wemakedevs.org/) hackathon — *The Hangover Part AI: Where's My Context?*

[![GitHub](https://img.shields.io/badge/GitHub-Ru0k3%2FcliMEM-181717?logo=github)](https://github.com/Ru0k3/cliMEM)
[![YouTube Demo](https://img.shields.io/badge/YouTube-Watch%20Demo-FF0000?logo=youtube)](https://youtu.be/uCybQO2Kptk?si=-4TKtDujUzYduSZI)
[![Instagram](https://img.shields.io/badge/Instagram-%40alchemists.ai-E4405F?logo=instagram)](https://www.instagram.com/alchemists.ai/)
