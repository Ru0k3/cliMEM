import json
import shutil
from pathlib import Path


def configure(config_path: Path, base_url: str):
    """Configure Claude Code to use CliMEM."""

    config_path.parent.mkdir(parents=True, exist_ok=True)

    if config_path.exists():
        backup_path = config_path.with_suffix(".json.bak")

        if not backup_path.exists():
            shutil.copy2(config_path, backup_path)

        with config_path.open("r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {}

    config.setdefault("env", {})
    config["env"]["ANTHROPIC_BASE_URL"] = base_url

    with config_path.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")


def restore(config_path: Path):
    """Restore the original Claude Code configuration."""

    backup_path = config_path.with_suffix(".json.bak")

    if not backup_path.exists():
        raise FileNotFoundError("Backup configuration not found.")

    shutil.copy2(backup_path, config_path)