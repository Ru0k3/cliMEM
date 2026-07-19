from pathlib import Path

from ._utils import backup_config, read_json_config, restore_config, write_json_config


def configure(config_path: Path, base_url: str) -> None:
    """Configure OpenCode to use CliMEM."""
    backup_config(config_path)
    config = read_json_config(config_path)
    config.setdefault("provider", {})
    config["provider"]["climem"] = {
        "npm": "@ai-sdk/openai-compatible",
        "name": "CliMEM Local",
        "options": {"baseURL": base_url},
        "models": {"proxy": {"name": "Local Proxy"}},
    }
    config["model"] = "climem/proxy"
    write_json_config(config_path, config)


def restore(config_path: Path) -> None:
    """Restore the original OpenCode configuration."""
    restore_config(config_path)
