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

**Requirements:** Python 3.10+

```bash
git clone https://github.com/Ru0k3/cliMEM.git
cd cliMEM
pip install -r requirements.txt
pip install -e .
```

Create a `.env` in the project root:

```env
PROVIDER_NAME=YourProvider
PROVIDER_API_KEY=sk-...
PROVIDER_BASE_URL=https://api.yourprovider.com/v1
CLI_TOOL=opencode

# Model aliases (map to real model IDs on your provider)
MODEL_PROXY=your-default-model
MODEL_CLAUDE=...
MODEL_KIMI=...

# Cognee: "local" (default) or hosted
COGNEE_MODE=local
# COGNEE_SERVICE_URL=...
# COGNEE_API_KEY=...
```

Then:

```bash
# 1. Start the memory proxy
climem start

# 2. Point your agent at it (in another terminal)
climem configure opencode      # or: claude / codex

# 3. Use your agent exactly as before — memory just works.
```

## ⌨️ Commands

```bash
climem start               # run the proxy server on 127.0.0.1:8000
climem configure <agent>   # route an agent through cliMEM (backs up config)
climem restore <agent>     # restore the agent's original config
climem history [--limit N] # show recent sessions across projects
climem forget [--yes]      # delete all memory for the current project
climem --version
```

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
└── agent_handlers/   # per-agent config writers (claude, opencode, codex)
```

## 👥 Team

Built by **Team AIALCHEMISTS** for the [WeMakeDevs](https://www.wemakedevs.org/) hackathon — *The Hangover Part AI: Where's My Context?*

[![GitHub](https://img.shields.io/badge/GitHub-Ru0k3%2FcliMEM-181717?logo=github)](https://github.com/Ru0k3/cliMEM)
[![YouTube Demo](https://img.shields.io/badge/YouTube-Watch%20Demo-FF0000?logo=youtube)](https://youtu.be/uCybQO2Kptk?si=-4TKtDujUzYduSZI)
[![Instagram](https://img.shields.io/badge/Instagram-%40alchemists.ai-E4405F?logo=instagram)](https://www.instagram.com/alchemists.ai/)
