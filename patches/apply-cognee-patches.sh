#!/usr/bin/env bash
# Re-apply cliMEM's local cognee patches after a reinstall/upgrade of cognee.
#
# Why this exists: cognee 1.5.3's strict-schema demotion logic only inspects
# str(error) for "schema", but OpenRouter upstreams hide the real
# "Invalid schema ..." message inside body.metadata.raw. The result: models
# like gpt-4o-mini (whose schemas cognee can't send strictly) hard-fail with
# BadRequestError instead of demoting to non-strict json_schema.
#
# Usage: ./patches/apply-cognee-patches.sh
set -euo pipefail

# Resolve the project root from this script's location (patches/ lives there).
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Always target the project's .venv — bare `python3` may be the system
# interpreter (PEP 668, no cognee installed), which is never what we want.
VENV_PY="$PROJECT_ROOT/.venv/bin/python"
if [ ! -x "$VENV_PY" ]; then
    echo "ERROR: $VENV_PY not found. Run this from the cliMEM project checkout." >&2
    exit 1
fi

SITE="$("$VENV_PY" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
TARGET="$SITE/cognee/infrastructure/llm/structured_output_framework/litellm_native/native_adapter.py"

if [ ! -f "$TARGET" ]; then
    echo "ERROR: native_adapter.py not found under $SITE — is cognee installed in .venv?" >&2
    exit 1
fi

echo "==> Patching $TARGET"
if grep -q "cliMEM local patch" "$TARGET"; then
    echo "    already applied — nothing to do"
    exit 0
fi

patch "$TARGET" < "$(dirname "${BASH_SOURCE[0]}")/cognee-native-adapter-openrouter-schema400.patch"
"$VENV_PY" -m compileall -q "$TARGET"
echo "==> Done."
