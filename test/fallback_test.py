"""fallback_test.py — Behavioral verification for MODEL_FALLBACK in the proxy.

Starts the mock provider + one climem server pointed at it via CLIMEM_ENV_FILE,
then injects failures per-model through the mock's /failmode hook:

  F1  Baseline:            no failures -> primary model answers.
  F2  Transient (429):     primary rate-limited -> chain falls to next model,
                           exactly ONE attempt spent on the primary.
  F3  Permanent (400):     same fall-through (retrying same model can't help).
  F4  Total outage:        every model in the chain failing -> provider error
                           is surfaced to the client (non-200), never a hang.
  F5  Recovery:            failures cleared -> primary answers again.

Run:  .venv/bin/python test/fallback_test.py
"""

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PROVIDER_PORT = 9919
CLIMEM_PORT = 8125  # dedicated: never collides with e2e (8123) or user runs (8000)
MOCK_URL = f"http://127.0.0.1:{PROVIDER_PORT}"
CLIMEM_URL = f"http://127.0.0.1:{CLIMEM_PORT}"

PRIMARY = "mock-primary"
SECONDARY = "mock-secondary"
TERTIARY = "mock-tertiary"

PASS: list[str] = []
FAIL: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""),
          flush=True)
    (PASS if ok else FAIL).append(name)


def http(method: str, url: str, payload: dict | None = None,
         timeout: float = 60.0) -> tuple[int, Any]:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode()
            return r.status, (json.loads(body) if body.strip().startswith(("{", "["))
                              else body)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return e.code, (json.loads(body) if body.strip().startswith(("{", "["))
                        else body)


def chat(text: str) -> tuple[int, str]:
    status, body = http("POST", f"{CLIMEM_URL}/v1/chat/completions", {
        "model": "proxy",
        "messages": [
            {"role": "system", "content": "You are a helpful coding assistant."},
            {"role": "user", "content": text},
        ],
        "stream": True,
    })
    return status, body if isinstance(body, str) else json.dumps(body)


def failmodel(model: str, status: int | None) -> None:
    spec = {"model": model} if status is None else {"model": model, "status": status}
    http("POST", f"{MOCK_URL}/failmode", spec)


def request_counts() -> dict[str, int]:
    _, data = http("GET", f"{MOCK_URL}/request-log")
    counts: dict[str, int] = {}
    for entry in data["requests"]:
        counts[entry.get("model", "?")] = counts.get(entry.get("model", "?"), 0) + 1
    return counts


def wait_ready(url: str, timeout: float = 240.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2.0) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def main() -> int:
    print("=" * 70)
    print("cliMEM MODEL_FALLBACK behavior test")
    print("=" * 70)

    for old in ROOT.glob("test/_sandbox_fb_*"):
        shutil.rmtree(old, ignore_errors=True)
    sandbox = ROOT / "test" / f"_sandbox_fb_{int(time.time())}"
    sandbox.mkdir(parents=True)

    overlay = ROOT / "test" / "_overlay_fb.env"
    overlay.write_text(
        "PROVIDER_NAME=MockProvider\n"
        "PROVIDER_API_KEY=test-key-not-real\n"
        f"PROVIDER_BASE_URL={MOCK_URL}/v1\n"
        "CLI_TOOL=opencode\n"
        f"MODEL_PROXY={PRIMARY}\n"
        f"MODEL_FALLBACK={SECONDARY},{TERTIARY}\n"
    )

    mock = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "test.mock_provider:app",
         "--port", str(PROVIDER_PORT), "--log-level", "warning"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    srv = None
    try:
        check("F0 mock ready",
              wait_ready(f"{MOCK_URL}/docs", timeout=30))

        env = os.environ.copy()
        env["CLIMEM_ENV_FILE"] = str(overlay)
        srv = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app",
             "--host", "127.0.0.1", "--port", str(CLIMEM_PORT),
             "--log-level", "info"],
            cwd=ROOT, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        check("F0 climem ready", wait_ready(f"{CLIMEM_URL}/"))

        # ---- F1: baseline -------------------------------------------------
        http("DELETE", f"{MOCK_URL}/reset")
        status, sse = chat("hello there")
        fwd_model = http("GET", f"{MOCK_URL}/last-request")[1].get("model")
        check("F1 baseline uses primary",
              status == 200 and "Acknowledged" in sse and fwd_model == PRIMARY,
              f"status={status} model={fwd_model}")

        # ---- F2: transient 429 on primary ---------------------------------
        http("DELETE", f"{MOCK_URL}/reset")
        failmodel(PRIMARY, 429)
        t0 = time.time()
        status, sse = chat("fallback please")
        took = time.time() - t0
        fwd_model = http("GET", f"{MOCK_URL}/last-request")[1].get("model")
        counts = request_counts()
        check("F2 429-on-primary falls back to secondary",
              status == 200 and "Acknowledged" in sse and fwd_model == SECONDARY,
              f"status={status} model={fwd_model}")
        check("F2 single attempt on primary (no wasted retries)",
              counts.get(PRIMARY, 0) == 1 and counts.get(SECONDARY, 0) == 1,
              f"counts={counts}")
        check("F2 fast failover (<10s)", took < 10, f"took={took:.1f}s")

        # ---- F3: permanent 400 on primary ----------------------------------
        http("DELETE", f"{MOCK_URL}/reset")
        failmodel(PRIMARY, 400)
        status, sse = chat("still working?")
        fwd_model = http("GET", f"{MOCK_URL}/last-request")[1].get("model")
        check("F3 400-on-primary falls back to secondary",
              status == 200 and fwd_model == SECONDARY,
              f"status={status} model={fwd_model}")

        # ---- F4: total outage ----------------------------------------------
        http("DELETE", f"{MOCK_URL}/reset")
        failmodel(PRIMARY, 429)
        failmodel(SECONDARY, 429)
        failmodel(TERTIARY, 429)
        status, body = chat("anyone there?")
        check("F4 total outage surfaces error (non-200, no hang)",
              status != 200 and "injected failure" in body,
              f"status={status}")

        # ---- F5: recovery ----------------------------------------------------
        http("DELETE", f"{MOCK_URL}/reset")  # also clears fail modes
        status, sse = chat("back online")
        fwd_model = http("GET", f"{MOCK_URL}/last-request")[1].get("model")
        check("F5 recovers to primary after failures clear",
              status == 200 and fwd_model == PRIMARY,
              f"status={status} model={fwd_model}")

    finally:
        # Hard-kill on purpose: this test must NOT trigger the graceful
        # shutdown cognee save (keeps the run fast and credit-free).
        if srv is not None and srv.poll() is None:
            srv.kill()
            srv.wait(timeout=10)
        mock.terminate()
        try:
            mock.wait(timeout=10)
        except subprocess.TimeoutExpired:
            mock.kill()
        shutil.rmtree(sandbox, ignore_errors=True)
        overlay.unlink(missing_ok=True)

    print("=" * 70)
    print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        for name in FAIL:
            print(f"  - {name}")
    print("=" * 70)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
