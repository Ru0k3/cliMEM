"""mock_provider.py — Minimal OpenAI-compatible chat completions stub.

Used by the end-to-end test to exercise cliMEM's proxy without calling a
real LLM provider. Records every forwarded request so tests can assert on
the system message cliMEM injected.

Run:  .venv/bin/python -m uvicorn test.mock_provider:app --port 9919
"""

import json

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

app = FastAPI()

last_request: dict = {}
request_log: list[dict] = []
# Failure injection for tests: maps model name -> status code to reject with.
# Managed at runtime via the /failmode endpoints below; empty = never fail.
fail_mode: dict[str, int] = {}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    global last_request
    body = await request.json()
    last_request = body
    request_log.append(body)

    model = body.get("model", "")
    if model in fail_mode:
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=fail_mode[model],
            content={"error": {"message": f"injected failure for {model}",
                               "type": "test_failure"}},
        )

    async def sse_stream():
        for token in ["Acknowledged", " — ", "continuing", " the", " task."]:
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
    """Test hook: {"model": "m", "status": 429} to reject a model;
    {"model": "m"} (no status) clears it."""
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
