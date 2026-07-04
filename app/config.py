import hashlib
import os

from dotenv import load_dotenv

load_dotenv()

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
COGNEE_SERVICE_URL = os.getenv("COGNEE_SERVICE_URL", "")
COGNEE_API_KEY = os.getenv("COGNEE_API_KEY", "")

API_KEY_FINGERPRINT = hashlib.sha256(
    PROVIDER_API_KEY.encode("utf-8")
).hexdigest()