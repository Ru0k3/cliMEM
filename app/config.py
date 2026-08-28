import hashlib
import os

from dotenv import load_dotenv

load_dotenv(override=True)

# cognee calls load_dotenv(override=True) at import time (usually BEFORE this
# module runs, since memory.py imports cognee first), which clobbers anything
# the caller put in the process environment. Loading .env with override=True
# keeps cliMEM deterministic — .env wins over ambient/exported variables,
# matching cognee's own precedence. CLIMEM_ENV_FILE gives embedders and the
# test-suite a final-say overlay: point it at an env file and it is applied
# last, also with override semantics.
_env_overlay = os.getenv("CLIMEM_ENV_FILE")
if _env_overlay:
    load_dotenv(_env_overlay, override=True)

PROVIDER_NAME = os.getenv("PROVIDER_NAME", "Unknown")
PROVIDER_API_KEY = os.getenv("PROVIDER_API_KEY", "")
PROVIDER_BASE_URL = os.getenv("PROVIDER_BASE_URL", "")
CLI_TOOL = os.getenv("CLI_TOOL", "unknown")

MODEL_MAP = {
    "proxy": os.getenv("MODEL_PROXY", ""),
    "kimi": os.getenv("MODEL_KIMI", ""),
    "claude": os.getenv("MODEL_CLAUDE", ""),
    "codex": os.getenv("MODEL_CODEX", ""),
    "gemini": os.getenv("MODEL_GEMINI", ""),
    "deepseek": os.getenv("MODEL_DEEPSEEK", ""),
    "qwen": os.getenv("MODEL_QWEN", ""),
    "nemotron": os.getenv("MODEL_NEMOTRON", ""),
}

COGNEE_MODE = os.getenv("COGNEE_MODE", "local").lower()

# Optional comma-separated fallback chain for the proxied chat hop. When the
# primary model keeps answering with transient provider errors (429/5xx),
# the proxy automatically moves to the next model in this list, in order.
# Example: MODEL_FALLBACK=openai/gpt-4o-mini,moonshotai/kimi-k2-instruct
MODEL_FALLBACK = [
    m.strip() for m in os.getenv("MODEL_FALLBACK", "").split(",") if m.strip()
]
COGNEE_SERVICE_URL = os.getenv("COGNEE_SERVICE_URL", "")
COGNEE_API_KEY = os.getenv("COGNEE_API_KEY", "")

API_KEY_FINGERPRINT = hashlib.sha256(
    PROVIDER_API_KEY.encode("utf-8")
).hexdigest()