import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

PROVIDER_NAME = os.getenv("PROVIDER_NAME", "Unknown")
PROVIDER_API_KEY = os.getenv("PROVIDER_API_KEY", "")
PROVIDER_BASE_URL = os.getenv("PROVIDER_BASE_URL", "")
MODEL = os.getenv("MODEL", "")
CLI_TOOL = os.getenv("CLI_TOOL", "unknown")

API_KEY_FINGERPRINT = hashlib.sha256(
    PROVIDER_API_KEY.encode("utf-8")
).hexdigest()