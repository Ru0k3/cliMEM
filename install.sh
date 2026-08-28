#!/usr/bin/env bash
# cliMEM installer — sets up a venv, installs cliMEM, and puts `climem`
# on your PATH via ~/.local/bin (no venv activation needed afterwards).
#
# Usage:  ./install.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$REPO_DIR/.venv"
BIN_DIR="${HOME}/.local/bin"

echo "==> Installing cliMEM from $REPO_DIR"

# 1 ── Python 3.10+
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found. Install Python 3.10 or newer first." >&2
    exit 1
fi

PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info[0])')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info[1])')
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    echo "ERROR: Python >= 3.10 required (found $(python3 --version))." >&2
    exit 1
fi

# 2 ── venv module availability (missing python3-venv is the #1 setup failure)
if ! python3 -c "import ensurepip" >/dev/null 2>&1; then
    echo "ERROR: your Python is missing the venv/ensurepip module." >&2
    echo "       Debian/Ubuntu:  sudo apt install python3-venv python3-pip" >&2
    echo "       Fedora:         sudo dnf install python3-pip" >&2
    echo "       Arch:           sudo pacman -S python-pip" >&2
    exit 1
fi

# 3 ── create venv
if [ ! -x "$VENV_DIR/bin/python" ]; then
    echo "==> Creating virtual environment at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
else
    echo "==> Reusing existing venv at $VENV_DIR"
fi

# 4 ── install project + dependencies into the venv
echo "==> Installing dependencies (this can take a few minutes)"
"$VENV_DIR/bin/python" -m pip install --upgrade pip >/dev/null
"$VENV_DIR/bin/python" -m pip install -r "$REPO_DIR/requirements.txt"
"$VENV_DIR/bin/python" -m pip install -e "$REPO_DIR"

# 5 ── expose `climem` outside the venv
mkdir -p "$BIN_DIR"
ln -sf "$VENV_DIR/bin/climem" "$BIN_DIR/climem"
echo "==> Linked climem -> $BIN_DIR/climem"

case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *)
        echo ""
        echo "NOTE: $BIN_DIR is not on your PATH."
        echo "      Add this to your shell config (~/.bashrc, ~/.zshrc or fish: config.fish):"
        echo "          fish:   fish_add_path ~/.local/bin"
        echo "          bash/zsh:  export PATH=\"\$HOME/.local/bin:\$PATH\""
        ;;
esac

# 6 ── .env bootstrap
if [ ! -f "$REPO_DIR/.env" ]; then
    cp "$REPO_DIR/.env.example" "$REPO_DIR/.env"
    echo "==> Created .env from .env.example"
    echo ""
    echo "NEXT STEP (required): edit $REPO_DIR/.env and set PROVIDER_API_KEY"
    echo "(and optionally LLM_API_KEY — cognee's memory engine uses it)."
else
    echo "==> Existing .env left untouched"
fi

echo ""
echo "cliMEM installed. Quick start:"
echo "    climem start                 # terminal 1 — the memory proxy"
echo "    climem configure opencode    # terminal 2 — route your agent (or: claude / codex)"
echo "    <use your agent normally>    # memory just works"
