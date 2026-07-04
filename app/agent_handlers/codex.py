import shutil
from pathlib import Path


def configure(config_path: Path, base_url: str):
    """Configure Codex CLI to use CliMEM."""

    config_path.parent.mkdir(parents=True, exist_ok=True)

    if config_path.exists():
        backup_path = config_path.with_suffix(".toml.bak")

        if not backup_path.exists():
            shutil.copy2(config_path, backup_path)

        lines = config_path.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

    found = False

    for i, line in enumerate(lines):
        if line.strip().startswith("openai_base_url"):
            lines[i] = f'openai_base_url = "{base_url}"'
            found = True
            break

    if not found:
        lines.append(f'openai_base_url = "{base_url}"')

    config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def restore(config_path: Path):
    """Restore the original Codex CLI configuration."""

    backup_path = config_path.with_suffix(".toml.bak")

    if not backup_path.exists():
        raise FileNotFoundError("Backup configuration not found.")

    shutil.copy2(backup_path, config_path)