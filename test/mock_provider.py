"""Minimal OpenAI-compatible provider used by cliMEM integration tests."""

import json
import os
import re
from typing import Any
from urllib.parse import unquote

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

app = FastAPI()
last_request: dict = {}
request_log: list[dict] = []


def _read_positive_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc
    if value < 1:
        raise ValueError(f"{name} must be at least 1, got {value}")
    return value


MAX_REQUEST_LOG = _read_positive_int("MOCK_PROVIDER_MAX_REQUEST_LOG", 100)
MAX_SCHEMA_DEPTH = _read_positive_int("MOCK_PROVIDER_MAX_SCHEMA_DEPTH", 32)
fail_mode: dict[str, int] = {}

FACT_TEXT = (
    "PostgreSQL was chosen instead of SQLite for cliMEM session storage; "
    "the sessions table schema must be preserved during migration."
)


class SchemaResolutionError(ValueError):
    """Raised when a structured mock response cannot resolve its schema."""


def _decode_pointer_token(token: str) -> str:
    """Decode and strictly validate an RFC 6901 JSON Pointer token."""
    if re.search(r"~(?![01])", token):
        raise SchemaResolutionError(f"invalid JSON Pointer escape: ~ in {token!r}")
    return token.replace("~1", "/").replace("~0", "~")


def _resolve_json_pointer(root: Any, reference: str) -> Any:
    """Resolve a JSON Pointer fragment against an arbitrary JSON document."""
    if not isinstance(reference, str) or not reference.startswith("#"):
        raise SchemaResolutionError(f"unsupported schema reference: {reference}")
    pointer = reference[1:]
    if re.search(r"%(?![0-9A-Fa-f]{2})", pointer):
        raise SchemaResolutionError(f"invalid percent escape in JSON Pointer: {reference}")
    try:
        pointer = unquote(pointer, errors="strict")
    except UnicodeDecodeError as exc:
        raise SchemaResolutionError(f"invalid UTF-8 in JSON Pointer: {reference}") from exc
    if pointer == "":
        return root
    if not pointer.startswith("/"):
        raise SchemaResolutionError(f"invalid JSON Pointer: {reference}")
    value = root
    for raw_token in pointer[1:].split("/"):
        token = _decode_pointer_token(raw_token)
        if isinstance(value, dict):
            if token not in value:
                raise SchemaResolutionError(f"unresolved schema reference: {reference}")
            value = value[token]
        elif isinstance(value, list):
            if token == "-" or not token.isdigit() or (len(token) > 1 and token.startswith("0")) or int(token) >= len(value):
                raise SchemaResolutionError(f"unresolved schema reference: {reference}")
            value = value[int(token)]
        else:
            raise SchemaResolutionError(f"unresolved schema reference: {reference}")
    return value


def _resolve_schema(schema: dict[str, Any], root: dict[str, Any], seen: set[str] | None = None) -> dict[str, Any]:
    """Resolve JSON-schema references and fail clearly on bad references."""
    if not isinstance(schema, dict):
        raise SchemaResolutionError(f"schema must be an object, got {type(schema).__name__}")
    reference = schema.get("$ref")
    if not reference:
        return schema
    seen = set() if seen is None else seen
    if reference in seen:
        raise SchemaResolutionError(f"cyclic schema reference: {reference}")
    if len(seen) >= MAX_SCHEMA_DEPTH:
        raise SchemaResolutionError(f"maximum schema depth exceeded ({MAX_SCHEMA_DEPTH})")
    definition = _resolve_json_pointer(root, reference)
    if not isinstance(definition, dict):
        raise SchemaResolutionError(f"schema reference does not point to an object: {reference}")
    return _resolve_schema(definition, root, seen | {reference})


def _json_equal(left: Any, right: Any) -> bool:
    """Compare JSON values without requiring them to be hashable."""
    return left == right


def _allowed_values(schema: dict[str, Any]) -> list[Any] | None:
    if "const" in schema:
        return [schema["const"]]
    if "enum" in schema:
        return list(schema["enum"])
    return None


def _constraints_conflict(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Return whether two schemas cannot describe the same JSON value."""
    left_values, right_values = _allowed_values(left), _allowed_values(right)
    if left_values is not None and right_values is not None:
        return not any(_json_equal(a, b) for a in left_values for b in right_values)
    if left.get("type") and right.get("type") and left["type"] != right["type"]:
        return True
    if left.get("additionalProperties") is not None and right.get("additionalProperties") is not None:
        if left["additionalProperties"] != right["additionalProperties"]:
            return True
    if isinstance(left.get("properties"), dict) and isinstance(right.get("properties"), dict):
        for name in left["properties"].keys() & right["properties"].keys():
            if _constraints_conflict(left["properties"][name], right["properties"][name]):
                return True
    return False


def _combine_all_of(parts: list[dict[str, Any]], root: dict[str, Any]) -> dict[str, Any]:
    """Merge object constraints from an allOf schema into one generation view."""
    merged: dict[str, Any] = {"type": "object", "properties": {}, "required": []}
    branch_type: str | None = None
    if "$defs" in root:
        merged["$defs"] = root["$defs"]
    for part in parts:
        part = _resolve_schema(part, root)
        part_type = part.get("type")
        if part_type not in (None, "object") and "properties" not in part:
            raise SchemaResolutionError("allOf contains a non-object branch")
        if part_type is not None:
            if branch_type is not None and branch_type != part_type:
                raise SchemaResolutionError("conflicting allOf object types")
            branch_type = part_type
        for name, property_schema in part.get("properties", {}).items():
            property_schema = _resolve_schema(property_schema, root)
            previous = merged["properties"].get(name)
            if previous is not None and _constraints_conflict(previous, property_schema):
                raise SchemaResolutionError(f"conflicting allOf constraints for {name}")
            merged["properties"][name] = property_schema
        merged["required"].extend(part.get("required", []))
        if "additionalProperties" in part:
            previous_additional = merged.get("additionalProperties")
            if previous_additional is not None and _constraints_conflict(
                {"additionalProperties": previous_additional},
                {"additionalProperties": part["additionalProperties"]},
            ):
                raise SchemaResolutionError("conflicting allOf additionalProperties constraints")
            merged["additionalProperties"] = part["additionalProperties"]
        if "$defs" in part:
            merged["$defs"] = part["$defs"]
    merged["required"] = list(dict.fromkeys(merged["required"]))
    return merged


def _schema_value(name: str, schema: dict[str, Any], root: dict[str, Any], depth: int = 0) -> Any:
    """Generate a deterministic value satisfying the supported JSON-schema subset."""
    if depth > MAX_SCHEMA_DEPTH:
        raise SchemaResolutionError(f"maximum schema depth exceeded ({MAX_SCHEMA_DEPTH})")
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
                return _schema_value(name, branch, root, depth + 1)
            except SchemaResolutionError as exc:
                errors.append(str(exc))
        raise SchemaResolutionError(f"no usable branch for {name}: {'; '.join(errors)}")

    schema = _resolve_schema(schema, root)
    schema_type = schema.get("type")
    if schema_type == "object" or "properties" in schema:
        return {
            child_name: _schema_value(child_name, child_schema, root, depth + 1)
            for child_name, child_schema in schema.get("properties", {}).items()
        }
    if schema_type == "array":
        item_schema = schema.get("items", {})
        if name.lower() in {"entities", "nodes", "facts", "memories", "items"}:
            return [_schema_value(name.rstrip("s"), item_schema, root, depth + 1)]
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


def _request_summary(body: dict[str, Any], kind: str) -> dict[str, Any]:
    """Return redacted metadata suitable for bounded diagnostics."""
    if kind == "embeddings":
        raw_input = body.get("input", [])
        inputs = raw_input if isinstance(raw_input, list) else [raw_input]
        return {
            "kind": kind,
            "model": body.get("model", ""),
            "input_count": len(inputs),
            "input_chars": sum(len(str(value)) for value in inputs),
        }
    messages = body.get("messages", [])
    return {
        "kind": kind,
        "model": body.get("model", ""),
        "stream": bool(body.get("stream", False)),
        "message_count": len(messages) if isinstance(messages, list) else 0,
        "response_format": (body.get("response_format") or {}).get("type"),
        "has_json_schema": bool((body.get("response_format") or {}).get("json_schema")),
    }


def _record_request(body: dict[str, Any], kind: str = "chat") -> None:
    """Record only redacted metadata for the newest bounded request window."""
    request_log.append(_request_summary(body, kind))
    if len(request_log) > MAX_REQUEST_LOG:
        del request_log[:-MAX_REQUEST_LOG]


@app.post("/v1/embeddings")
async def embeddings(request: Request):
    try:
        body = await request.json()
    except (ValueError, UnicodeDecodeError):
        return JSONResponse(
            status_code=400,
            content={"error": {"message": "request body is not valid JSON", "type": "invalid_request_error", "code": "invalid_json"}},
        )
    _record_request(body, "embeddings")
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
    try:
        body = await request.json()
    except (ValueError, UnicodeDecodeError):
        return JSONResponse(
            status_code=400,
            content={"error": {"message": "request body is not valid JSON", "type": "invalid_request_error", "code": "invalid_json"}},
        )
    last_request = body
    _record_request(body)
    model = body.get("model", "")
    if model in fail_mode:
        return JSONResponse(status_code=fail_mode[model], content={"error": {"message": f"injected failure for {model}", "type": "test_failure"}})
    try:
        content = _chat_content(body)
    except SchemaResolutionError as exc:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "message": str(exc),
                    "type": "invalid_request_error",
                    "code": "invalid_structured_schema",
                }
            },
        )
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
    last_request.clear()
    request_log.clear()
    fail_mode.clear()
    return {"ok": True}


@app.post("/failmode")
async def set_fail_mode(request: Request):
    try:
        spec = await request.json()
    except (ValueError, UnicodeDecodeError):
        return JSONResponse(
            status_code=400,
            content={"error": {"message": "request body is not valid JSON", "type": "invalid_request_error", "code": "invalid_json"}},
        )
    if not isinstance(spec, dict):
        return JSONResponse(
            status_code=400,
            content={"error": {"message": "failmode body must be a JSON object", "type": "invalid_request_error", "code": "invalid_failmode"}},
        )
    model, status = spec.get("model"), spec.get("status")
    if not isinstance(model, str) or not model.strip():
        return JSONResponse(
            status_code=400,
            content={"error": {"message": "failmode.model must be a non-empty string", "type": "invalid_request_error", "code": "invalid_failmode"}},
        )
    if status is not None and (isinstance(status, bool) or not isinstance(status, int) or not 100 <= status <= 599):
        return JSONResponse(
            status_code=400,
            content={"error": {"message": "failmode.status must be an integer HTTP status from 100 to 599", "type": "invalid_request_error", "code": "invalid_failmode"}},
        )
    if status is None:
        fail_mode.pop(model, None)
    else:
        fail_mode[model] = status
    return {"ok": True, "fail_mode": dict(fail_mode)}


@app.get("/failmode")
async def get_fail_mode():
    return {"fail_mode": dict(fail_mode)}
