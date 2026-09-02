"""mock_provider.py — Minimal OpenAI-compatible provider for integration tests."""

import json
import re
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

app = FastAPI()

last_request: dict = {}
request_log: list[dict] = []
fail_mode: dict[str, int] = {}


FACT_TEXT = (
    "PostgreSQL was chosen instead of SQLite for cliMEM session storage; "
    "the sessions table schema must be preserved during migration."
)


def _resolve_schema(schema: dict[str, Any], root: dict[str, Any]) -> dict[str, Any]:
    """Resolve the local `$defs` references emitted by Pydantic schemas."""
    reference = schema.get("$ref")
    if not reference or not reference.startswith("#/$defs/"):
        return schema
    definition = root.get("$defs", {}).get(reference.removeprefix("#/$defs/"), {})
    return definition if isinstance(definition, dict) else schema


def _schema_value(name: str, schema: dict[str, Any], root: dict[str, Any]) -> Any:
    """Build a small valid value for a JSON-schema property."""
    schema = _resolve_schema(schema, root)
    if "anyOf" in schema:
        non_null = [item for item in schema["anyOf"] if item.get("type") != "null"]
        if non_null:
            return _schema_value(name, non_null[0], root)
        return None
    schema_type = schema.get("type")
    if schema_type == "object" or "properties" in schema:
        return {
            child_name: _schema_value(child_name, child_schema, root)
            for child_name, child_schema in schema.get("properties", {}).items()
        }
    if schema_type == "array":
        item_schema = schema.get("items", {})
        lowered = name.lower()
        if lowered in {"entities", "nodes", "facts", "memories", "items"}:
            return [_schema_value(name.rstrip("s"), item_schema, root)]
        return []
    if schema_type == "boolean":
        return False
    if schema_type in {"integer", "number"}:
        return 0
    if schema_type == "null":
        return None

    lowered = name.lower()
    if any(word in lowered for word in
           ("text", "content", "description", "summary", "answer", "response")):
        return FACT_TEXT
    if any(word in lowered for word in ("name", "label", "title", "entity")):
        return "PostgreSQL"
    if any(word in lowered for word in ("relation", "type", "category")):
        return "decision"
    return "mock"


def _structured_payload(body: dict[str, Any]) -> dict[str, Any] | None:
    """Return a deterministic payload for JSON-schema or prompted JSON calls."""
    response_format = body.get("response_format") or {}
    schema_wrapper = response_format.get("json_schema") or {}
    schema = schema_wrapper.get("schema") or {}

    # Cognee's native adapter uses response_format=json_object and puts the
    # actual Pydantic schema in a fenced JSON block in the system prompt.
    if not schema and response_format.get("type") == "json_object":
        messages_text = "\n".join(
            str(message.get("content", ""))
            for message in body.get("messages", [])
            if isinstance(message, dict)
        )
        matches = re.findall(r"```json\s*(\{.*?\})\s*```", messages_text, re.DOTALL)
        for candidate in reversed(matches):
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict) and ("properties" in parsed or "$defs" in parsed):
                schema = parsed
                break

    if not schema:
        return None
    if schema.get("type") == "object" or "properties" in schema:
        return {
            name: _schema_value(name, property_schema, schema)
            for name, property_schema in schema.get("properties", {}).items()
        }
    return _schema_value("response", schema, schema)


def _chat_content(body: dict[str, Any]) -> str:
    structured = _structured_payload(body)
    if structured is not None:
        return json.dumps(structured)
    return "Acknowledged — continuing the task."


@app.post("/v1/embeddings")
async def embeddings(request: Request):
    """Return deterministic 384-dimensional embeddings for Cognee tests."""
    body = await request.json()
    raw_input = body.get("input", [])
    inputs = raw_input if isinstance(raw_input, list) else [raw_input]
    data = []
    for index, value in enumerate(inputs):
        text = str(value)
        seed = sum((position + 1) * ord(char)
                   for position, char in enumerate(text))
        vector = [((seed + (index + 1) * (dimension + 1)) % 2000) / 1000 - 1
                  for dimension in range(384)]
        data.append({"object": "embedding", "embedding": vector, "index": index})
    token_count = sum(len(str(value).split()) for value in inputs)
    return {
        "object": "list",
        "data": data,
        "model": body.get("model", "mock-embedding"),
        "usage": {"prompt_tokens": token_count, "total_tokens": token_count},
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    global last_request
    body = await request.json()
    last_request = body
    request_log.append(body)
    model = body.get("model", "")
    if model in fail_mode:
        return JSONResponse(
            status_code=fail_mode[model],
            content={"error": {"message": f"injected failure for {model}",
                                "type": "test_failure"}},
        )

    content = _chat_content(body)
    if not body.get("stream", False):
        return {
            "id": "chatcmpl-mock",
            "object": "chat.completion",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": content},
                         "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }

    async def sse_stream():
        for token in [content]:
            chunk = {
                "id": "chatcmpl-mock",
                "object": "chat.completion.chunk",
                "choices": [{"index": 0, "delta": {"content": token}}],
            }
            yield f"data: {json.dumps(chunk)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_stream(), media_type="text/event-stream")


@app.get("/last-request")
async def get_last_request():
    return last_request


@app.get("/request-log")
async def get_request_log():
    return {"count": len(request_log), "requests": request_log}


@app.delete("/reset")
async def reset():
    global last_request, request_log
    last_request = {}
    request_log = []
    fail_mode.clear()
    return {"ok": True}


@app.post("/failmode")
async def set_fail_mode(request: Request):
    spec = await request.json()
    model, status = spec.get("model", ""), spec.get("status")
    if status is None:
        fail_mode.pop(model, None)
        return {"ok": True, "fail_mode": dict(fail_mode)}
    fail_mode[model] = int(status)
    return {"ok": True, "fail_mode": dict(fail_mode)}


@app.get("/failmode")
async def get_fail_mode():
    return {"fail_mode": dict(fail_mode)}
