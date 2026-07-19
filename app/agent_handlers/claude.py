from pathlib import Path

from ._utils import backup_config, read_json_config, restore_config, write_json_config


def configure(config_path: Path, base_url: str) -> None:
    """Configure Claude Code to use CliMEM."""
    backup_config(config_path)
    config = read_json_config(config_path)
    config.setdefault("env", {})
    config["env"]["ANTHROPIC_BASE_URL"] = base_url
    write_json_config(config_path, config)


def restore(config_path: Path) -> None:
    """Restore the original Claude Code configuration."""
    restore_config(config_path)
