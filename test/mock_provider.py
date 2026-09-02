"""Minimal OpenAI-compatible provider used by cliMEM integration tests."""

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


class SchemaResolutionError(ValueError):
    """Raised when a structured mock response cannot resolve its schema."""


def _resolve_schema(schema: dict[str, Any], root: dict[str, Any], seen: set[str] | None = None) -> dict[str, Any]:
    """Resolve local JSON-schema references and fail clearly on bad references."""
    if not isinstance(schema, dict):
        raise SchemaResolutionError(f"schema must be an object, got {type(schema).__name__}")
    reference = schema.get("$ref")
    if not reference:
        return schema
    if not reference.startswith("#/$defs/"):
        raise SchemaResolutionError(f"unsupported schema reference: {reference}")
    seen = set() if seen is None else seen
    if reference in seen:
        raise SchemaResolutionError(f"cyclic schema reference: {reference}")
    name = reference.removeprefix("#/$defs/")
    definition = root.get("$defs", {}).get(name)
    if not isinstance(definition, dict):
        raise SchemaResolutionError(f"unresolved schema reference: {reference}")
    return _resolve_schema(definition, root, seen | {reference})


def _constraints_conflict(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Return whether two property schemas cannot share one generated value."""
    if "const" in left and "const" in right:
        return left["const"] != right["const"]
    if "enum" in left and "enum" in right:
        return not set(left["enum"]).intersection(right["enum"])
    return bool(left.get("type") and right.get("type") and left["type"] != right["type"])


def _combine_all_of(parts: list[dict[str, Any]], root: dict[str, Any]) -> dict[str, Any]:
    """Merge object constraints from an allOf schema into one generation view."""
    merged: dict[str, Any] = {"type": "object", "properties": {}, "required": []}
    if "$defs" in root:
        merged["$defs"] = root["$defs"]
    for part in parts:
        part = _resolve_schema(part, root)
        if part.get("type") not in (None, "object") and "properties" not in part:
            raise SchemaResolutionError("allOf contains a non-object branch")
        for name, property_schema in part.get("properties", {}).items():
            previous = merged["properties"].get(name)
            if previous is not None and _constraints_conflict(previous, property_schema):
                raise SchemaResolutionError(f"conflicting allOf constraints for {name}")
            merged["properties"][name] = property_schema
        merged["required"].extend(part.get("required", []))
        for key in ("$defs", "additionalProperties"):
            if key in part:
                merged[key] = part[key]
    merged["required"] = list(dict.fromkeys(merged["required"]))
    return merged


def _schema_value(name: str, schema: dict[str, Any], root: dict[str, Any]) -> Any:
    """Generate a deterministic value satisfying the supported JSON-schema subset."""
    schema = _resolve_schema(schema, root)

    if "const" in schema:
        return schema["const"]
    if "enum" in schema:
        values = schema["enum"]
        if not values:
            raise SchemaResolutionError(f"empty enum for {name}")
        return values[0]
    if "default" in schema:
        return schema["default"]
    if "allOf" in schema:
        schema = _combine_all_of(schema["allOf"], root)
    elif "oneOf" in schema or "anyOf" in schema:
        branches = schema.get("oneOf", schema.get("anyOf", []))
        errors = []
        for branch in branches:
            try:
                return _schema_value(name, branch, root)
            except SchemaResolutionError as exc:
                errors.append(str(exc))
        raise SchemaResolutionError(f"no usable branch for {name}: {'; '.join(errors)}")

    schema = _resolve_schema(schema, root)
    schema_type = schema.get("type")
    if schema_type == "object" or "properties" in schema:
        return {
            child_name: _schema_value(child_name, child_schema, root)
            for child_name, child_schema in schema.get("properties", {}).items()
        }
    if schema_type == "array":
        item_schema = schema.get("items", {})
        if name.lower() in {"entities", "nodes", "facts", "memories", "items"}:
            return [_schema_value(name.rstrip("s"), item_schema, root)]
        return []
    if schema_type == "boolean":
        return False
    if schema_type in {"integer", "number"}:
        return 0
    if schema_type == "null":
        return None

    lowered = name.lower()
    if any(word in lowered for word in ("text", "content", "description", "summary", "answer", "response")):
        return FACT_TEXT
    if any(word in lowered for word in ("name", "label", "title", "entity")):
        return "PostgreSQL"
    if any(word in lowered for word in ("relation", "type", "category")):
        return "decision"
    return "mock"


def _structured_payload(body: dict[str, Any]) -> dict[str, Any] | None:
    """Return a deterministic payload for explicit or prompt-embedded schemas."""
    response_format = body.get("response_format") or {}
    schema = (response_format.get("json_schema") or {}).get("schema") or {}
    if not schema and response_format.get("type") == "json_object":
        messages_text = "\n".join(
            str(message.get("content", ""))
            for message in body.get("messages", [])
            if isinstance(message, dict)
        )
        matches = re.findall(r"```json\s*(.*?)\s*```", messages_text, re.DOTALL | re.IGNORECASE)
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
    if schema.get("type") == "object" or "properties" in schema or "allOf" in schema:
        resolved = _combine_all_of(schema["allOf"], schema) if "allOf" in schema else schema
        return {
            name: _schema_value(name, property_schema, resolved)
            for name, property_schema in resolved.get("properties", {}).items()
        }
    return _schema_value("response", schema, schema)


def _chat_content(body: dict[str, Any]) -> str:
    structured = _structured_payload(body)
    return json.dumps(structured) if structured is not None else "Acknowledged — continuing the task."


@app.post("/v1/embeddings")
async def embeddings(request: Request):
    body = await request.json()
    raw_input = body.get("input", [])
    inputs = raw_input if isinstance(raw_input, list) else [raw_input]
    data = []
    for index, value in enumerate(inputs):
        text = str(value)
        seed = sum((position + 1) * ord(char) for position, char in enumerate(text))
        vector = [((seed + (index + 1) * (dimension + 1)) % 2000) / 1000 - 1 for dimension in range(384)]
        data.append({"object": "embedding", "embedding": vector, "index": index})
    token_count = sum(len(str(value).split()) for value in inputs)
    return {"object": "list", "data": data, "model": body.get("model", "mock-embedding"),
            "usage": {"prompt_tokens": token_count, "total_tokens": token_count}}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    global last_request
    body = await request.json()
    last_request = body
    request_log.append(body)
    model = body.get("model", "")
    if model in fail_mode:
        return JSONResponse(status_code=fail_mode[model], content={"error": {"message": f"injected failure for {model}", "type": "test_failure"}})
    content = _chat_content(body)
    if not body.get("stream", False):
        return {"id": "chatcmpl-mock", "object": "chat.completion",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}

    async def sse_stream():
        chunk = {"id": "chatcmpl-mock", "object": "chat.completion.chunk",
                 "choices": [{"index": 0, "delta": {"content": content}}]}
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
    last_request, request_log = {}, []
    fail_mode.clear()
    return {"ok": True}


@app.post("/failmode")
async def set_fail_mode(request: Request):
    spec = await request.json()
    model, status = spec.get("model", ""), spec.get("status")
    if status is None:
        fail_mode.pop(model, None)
    else:
        fail_mode[model] = int(status)
    return {"ok": True, "fail_mode": dict(fail_mode)}


@app.get("/failmode")
async def get_fail_mode():
    return {"fail_mode": dict(fail_mode)}
