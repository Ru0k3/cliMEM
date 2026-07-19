from pathlib import Path

from ._utils import backup_config, restore_config


def configure(config_path: Path, base_url: str) -> None:
    """Configure Codex CLI to use CliMEM."""
    backup_config(config_path)

    lines = (
        config_path.read_text(encoding="utf-8").splitlines()
        if config_path.exists()
        else []
    )

    found = False
    for i, line in enumerate(lines):
        if line.strip().startswith("openai_base_url"):
            lines[i] = f'openai_base_url = "{base_url}"'
            found = True
            break

    if not found:
        lines.append(f'openai_base_url = "{base_url}"')

    config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def restore(config_path: Path) -> None:
    """Restore the original Codex CLI configuration."""
    restore_config(config_path)
