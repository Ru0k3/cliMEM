import json

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import Response, StreamingResponse

from .config import MODEL, NVIDIA_API_KEY, NVIDIA_BASE_URL
from .filter import add_message

router = APIRouter()

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

    if messages:
        last = messages[-1]

        if last.get("role") == "user":
            add_message(
                "user",
                last.get("content", ""),
            )

    requested_model = body.get("model", "proxy")
    body["model"] = MODEL_MAP.get(requested_model, MODEL)

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    client = httpx.AsyncClient(timeout=None)

    nvidia_request = client.build_request(
        "POST",
        f"{NVIDIA_BASE_URL}/chat/completions",
        headers=headers,
        json=body,
    )

    response = await client.send(
        nvidia_request,
        stream=True,
    )

    print(
        f"NVIDIA -> {response.status_code} ({response.headers.get('content-type')})"
    )

    if response.status_code != 200:
        text = await response.aread()
        await client.aclose()

        return Response(
            content=text,
            status_code=response.status_code,
            media_type=response.headers.get(
                "content-type",
                "text/plain",
            ),
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

                            delta = (
                                obj["choices"][0]
                                .get("delta", {})
                                .get("content")
                            )

                            if delta:
                                assistant_response += delta

                        except Exception:
                            pass

                yield chunk

        finally:

            if assistant_response:

                add_message(
                    "assistant",
                    assistant_response,
                )

            await response.aclose()
            await client.aclose()

    return StreamingResponse(
        stream_generator(),
        status_code=response.status_code,
        media_type=response.headers.get(
            "content-type",
            "text/event-stream",
        ),
    )