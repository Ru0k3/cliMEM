import json
import logging
import time
from pathlib import Path

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import Response, StreamingResponse

from .config import (
    API_KEY_FINGERPRINT,
    CLI_TOOL,
    MODEL,
    PROVIDER_API_KEY,
    PROVIDER_BASE_URL,
    PROVIDER_NAME,
)
from .filter import add_message
from .storage import ensure_session

router = APIRouter()
logger = logging.getLogger("climem")
MODEL_MAP = {
    "proxy": "moonshotai/kimi-k2.6",
    "kimi": "moonshotai/kimi-k2.6",
    "claude": "mistralai/mistral-large-3-675b-instruct-2512",
    "codex": "openai/gpt-oss-120b",
    "gemini": "google/gemma-4-31b-it",
    "deepseek": "deepseek-ai/deepseek-v4-pro",
    "qwen": "qwen/qwen3.5-397b-a17b",
    "nemotron": "nvidia/nemotron-3-super-120b-a12b",
}


@router.post("/v1/chat/completions")
async def chat(request: Request):
    body = await request.json()

    print("\n===== Incoming Request =====")
    print(body)

    messages = body.get("messages", [])

    # Resolve model alias before session check so the session
    # records the real model name, not the alias.
    requested_model = body.get("model", "proxy")
    resolved_model = MODEL_MAP.get(requested_model, MODEL)
    body["model"] = resolved_model

    # Detect OpenCode's internal title generation requests.
    is_title_request = False
    if messages:
        first = messages[0]
        if (
            first.get("role") == "system"
            and "You are a title generator" in first.get("content", "")
        ):
            is_title_request = True

    if not is_title_request:
        # Ensure a session exists and rotate if anything changed.
        ensure_session(
            working_directory=str(Path.cwd()),
            cli_tool=CLI_TOOL,
            provider_name=PROVIDER_NAME,
            model=resolved_model,
            api_key_fingerprint=API_KEY_FINGERPRINT,
        )

        if messages:
            last = messages[-1]
            if last.get("role") == "user":
                add_message("user", last.get("content", ""))

    # ==========================================================
    # MEMBER 2 HOOK
    #
    # Cognee retrieval happens here.
    #
    # Member 2 will:
    # 1. Use Path.cwd() as the project identifier
    # 2. Retrieve relevant memories from Cognee
    # 3. Inject them into body["messages"] as a system message
    #
    # body = inject_memory(body, str(Path.cwd()))
    # ==========================================================

    headers = {
        "Authorization": f"Bearer {PROVIDER_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    client = httpx.AsyncClient(timeout=None)

    provider_request = client.build_request(
        "POST",
        f"{PROVIDER_BASE_URL}/chat/completions",
        headers=headers,
        json=body,
    )

    response = await client.send(provider_request, stream=True)

    print(f"{PROVIDER_NAME} -> {response.status_code} ({response.headers.get('content-type')})")

    if response.status_code != 200:
        text = await response.aread()
        await client.aclose()
        return Response(
            content=text,
            status_code=response.status_code,
            media_type=response.headers.get("content-type", "text/plain"),
        )

    async def stream_generator():
        assistant_response = ""

        try:
            async for chunk in response.aiter_text():
                if chunk.startswith("data: "):
                    data = chunk[6:].strip()
                    if data != "[DONE]":
                        try:
                            obj = json.loads(data)
                            delta = obj["choices"][0].get("delta", {}).get("content")
                            if delta:
                                assistant_response += delta
                        except Exception:
                            pass
                yield chunk
        finally:
            if assistant_response:
                add_message("assistant", assistant_response)
            await response.aclose()
            await client.aclose()

    return StreamingResponse(
        stream_generator(),
        status_code=response.status_code,
        media_type=response.headers.get("content-type", "text/event-stream"),
    )