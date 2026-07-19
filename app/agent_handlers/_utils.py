import json
import shutil
from pathlib import Path


def _backup_suffix(config_path: Path) -> str:
    """Derive the backup suffix from the config file's extension.

    e.g. ``.json`` → ``.json.bak``, ``.toml`` → ``.toml.bak``
    """
    return config_path.suffix + ".bak"


def backup_config(config_path: Path) -> Path | None:
    """Back up a configuration file before modifying it.

    Creates the parent directory if it doesn't exist.  Only creates the
    backup if the config file already exists and no previous backup is
    present.  Returns the backup path, or ``None`` if the config file
    doesn't exist (nothing to back up).
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)

    if not config_path.exists():
        return None

    backup_path = config_path.with_suffix(_backup_suffix(config_path))
    if not backup_path.exists():
        shutil.copy2(config_path, backup_path)

    return backup_path


def restore_config(config_path: Path) -> None:
    """Restore a configuration file from its backup.

    Raises ``FileNotFoundError`` if no backup exists.
    """
    backup_path = config_path.with_suffix(_backup_suffix(config_path))

    if not backup_path.exists():
        raise FileNotFoundError(
            f"Backup configuration not found at {backup_path}."
        )

    shutil.copy2(backup_path, config_path)


def read_json_config(config_path: Path) -> dict:
    """Read a JSON config file, returning an empty dict if it doesn't exist."""
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8"))
    return {}


def write_json_config(config_path: Path, config: dict) -> None:
    """Write a dict as pretty-printed JSON to the given path."""
    config_path.write_text(
        json.dumps(config, indent=2) + "\n", encoding="utf-8",
    )
