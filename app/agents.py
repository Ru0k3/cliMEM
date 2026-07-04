from pathlib import Path

CLIMEM_BASE_URL = "http://127.0.0.1:8000/v1"

AGENTS = {
    "opencode": {
        "name": "OpenCode",
        "handler": "opencode",
        "config": Path.home() / ".config" / "opencode" / "opencode.json",
        "backup_suffix": ".json.bak",
        "format": "json",
        "supported": True,
    },
    "claude": {
        "name": "Claude Code",
        "handler": "claude",
        "config": Path.home() / ".claude" / "settings.json",
        "backup_suffix": ".json.bak",
        "format": "json",
        "supported": True,
    },
    "codex": {
        "name": "Codex CLI",
        "handler": "codex",
        "config": Path.home() / ".codex" / "config.toml",
        "backup_suffix": ".toml.bak",
        "format": "toml",
        "supported": True,
    },
}