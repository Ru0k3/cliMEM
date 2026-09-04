"""Concurrency and throughput integration tests for the local mock provider."""

import asyncio
import time
import unittest

import httpx

from test.mock_provider import MAX_REQUEST_LOG, app


class MockProviderConcurrencyTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.transport = httpx.ASGITransport(app=app)
        self.client = httpx.AsyncClient(transport=self.transport, base_url="http://test")
        await self.client.delete("/reset")

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_concurrent_chat_and_embedding_requests_remain_correct(self):
        async def chat(index: int):
            response = await self.client.post(
                "/v1/chat/completions",
                json={"model": f"chat-{index}", "messages": [{"role": "user", "content": f"message-{index}"}]},
            )
            return response

        async def embedding(index: int):
            response = await self.client.post(
                "/v1/embeddings",
                json={"model": "mock-embedding", "input": [f"embedding-{index}"]},
            )
            return response

        responses = await asyncio.gather(
            *(chat(index) for index in range(50)),
            *(embedding(index) for index in range(50)),
        )

        self.assertEqual(len(responses), 100)
        self.assertTrue(all(response.status_code == 200 for response in responses))
        chat_responses = [response for response in responses if response.json().get("object") == "chat.completion"]
        embedding_responses = [response for response in responses if response.json().get("object") == "list"]
        self.assertEqual(len(chat_responses), 50)
        self.assertEqual(len(embedding_responses), 50)
        self.assertTrue(all(len(response.json()["data"][0]["embedding"]) == 384 for response in embedding_responses))

        diagnostics = await self.client.get("/request-log")
        self.assertEqual(diagnostics.status_code, 200)
        self.assertLessEqual(diagnostics.json()["count"], MAX_REQUEST_LOG)
        self.assertNotIn("message-", diagnostics.text)
        self.assertNotIn("embedding-", diagnostics.text)

    async def test_high_throughput_chat_requests_complete_within_bound(self):
        request_count = 250
        started = time.perf_counter()

        async def timed_request(index: int):
            request_started = time.perf_counter()
            response = await self.client.post(
                "/v1/chat/completions",
                json={"model": "throughput", "messages": [{"role": "user", "content": str(index)}]},
            )
            return response, time.perf_counter() - request_started

        results = await asyncio.gather(*(timed_request(index) for index in range(request_count)))
        elapsed = time.perf_counter() - started
        responses = [response for response, _ in results]
        latencies = sorted(latency for _, latency in results)
        p50 = latencies[len(latencies) // 2]
        p95 = latencies[int(len(latencies) * 0.95) - 1]
        print(
            f"throughput metrics: count={request_count} total={elapsed:.4f}s "
            f"p50={p50:.4f}s p95={p95:.4f}s max={latencies[-1]:.4f}s",
            flush=True,
        )

        self.assertEqual(len(responses), request_count)
        self.assertTrue(all(response.status_code == 200 for response in responses))
        self.assertLess(elapsed, 10.0, f"high-throughput requests took {elapsed:.2f}s")
        diagnostics = await self.client.get("/request-log")
        self.assertEqual(diagnostics.json()["count"], min(request_count, MAX_REQUEST_LOG))

    async def test_intermittent_timeouts_are_bounded_and_recover(self):
        configured = await self.client.post(
            "/failmode",
            json={"model": "flaky", "timeout_ms": 50, "timeout_every": 3},
        )
        self.assertEqual(configured.status_code, 200)

        async def request_with_deadline():
            try:
                response = await asyncio.wait_for(
                    self.client.post(
                        "/v1/chat/completions",
                        json={"model": "flaky", "messages": []},
                    ),
                    timeout=0.01,
                )
                return response
            except asyncio.TimeoutError:
                return "timeout"

        results = await asyncio.gather(*(request_with_deadline() for _ in range(30)))
        self.assertGreaterEqual(results.count("timeout"), 1)
        self.assertTrue(all(result == "timeout" or result.status_code == 200 for result in results))

        cleared = await self.client.post("/failmode", json={"model": "flaky"})
        self.assertEqual(cleared.status_code, 200)
        recovered = await asyncio.gather(
            *(
                self.client.post(
                    "/v1/chat/completions",
                    json={"model": "flaky", "messages": []},
                )
                for _ in range(30)
            )
        )
        self.assertTrue(all(response.status_code == 200 for response in recovered))

    async def test_embedding_timeouts_are_bounded_and_recover(self):
        configured = await self.client.post(
            "/failmode",
            json={"model": "embed-flaky", "timeout_ms": 50, "timeout_every": 2},
        )
        self.assertEqual(configured.status_code, 200)

        async def embedding_with_deadline(index: int):
            try:
                return await asyncio.wait_for(
                    self.client.post(
                        "/v1/embeddings",
                        json={"model": "embed-flaky", "input": [f"embedding-{index}"]},
                    ),
                    timeout=0.01,
                )
            except asyncio.TimeoutError:
                return "timeout"

        results = await asyncio.gather(*(embedding_with_deadline(index) for index in range(30)))
        self.assertGreaterEqual(results.count("timeout"), 1)
        self.assertTrue(all(result == "timeout" or result.status_code == 200 for result in results))

        cleared = await self.client.post("/failmode", json={"model": "embed-flaky"})
        self.assertEqual(cleared.status_code, 200)
        recovered = await self.client.post(
            "/v1/embeddings",
            json={"model": "embed-flaky", "input": ["recovered"]},
        )
        self.assertEqual(recovered.status_code, 200)

    async def test_failmode_updates_are_safe_during_active_requests(self):
        configured = await self.client.post(
            "/failmode",
            json={"model": "active", "timeout_ms": 40, "timeout_every": 1},
        )
        self.assertEqual(configured.status_code, 200)

        async def active_request(index: int):
            return await self.client.post(
                "/v1/chat/completions",
                json={"model": "active", "messages": [{"role": "user", "content": str(index)}]},
            )

        requests = [asyncio.create_task(active_request(index)) for index in range(30)]
        updates = [
            self.client.post(
                "/failmode",
                json=(
                    {"model": "active", "timeout_ms": 20, "timeout_every": 2}
                    if index % 2
                    else {"model": "active", "status": 503}
                ),
            )
            for index in range(12)
        ]
        update_results = await asyncio.gather(*updates)
        request_results = await asyncio.gather(*requests)
        self.assertTrue(all(response.status_code == 200 for response in update_results))
        self.assertTrue(all(response.status_code in {200, 503} for response in request_results))
        cleared = await self.client.post("/failmode", json={"model": "active"})
        self.assertEqual(cleared.status_code, 200)

    async def test_request_log_reads_and_writes_are_safe_concurrently(self):
        async def writer(index: int):
            return await self.client.post(
                "/v1/chat/completions",
                json={"model": "writer", "messages": [{"role": "user", "content": f"secret-{index}"}]},
            )

        async def reader():
            return await self.client.get("/request-log")

        results = await asyncio.gather(
            *(writer(index) for index in range(150)),
            *(reader() for _ in range(75)),
        )
        writes = results[:150]
        reads = results[150:]
        self.assertTrue(all(response.status_code == 200 for response in writes))
        self.assertTrue(all(response.status_code == 200 for response in reads))
        self.assertTrue(all(response.json()["count"] <= MAX_REQUEST_LOG for response in reads))
        final_log = (await self.client.get("/request-log")).json()
        self.assertLessEqual(final_log["count"], MAX_REQUEST_LOG)
        self.assertNotIn("secret-", repr(final_log))

    async def test_streamed_response_can_be_cancelled_after_first_chunk(self):
        from starlette.requests import Request
        from starlette.responses import StreamingResponse
        from test.mock_provider import chat_completions

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/v1/chat/completions",
            "raw_path": b"/v1/chat/completions",
            "query_string": b"",
            "headers": [(b"content-type", b"application/json")],
            "client": ("test", 1),
            "server": ("test", 80),
            "scheme": "http",
            "http_version": "1.1",
        }
        body = b'{"model":"cancel","stream":true,"messages":[]}'

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        request = Request(scope, receive=receive)
        response = await chat_completions(request)
        self.assertIsInstance(response, StreamingResponse)
        first_chunk = await anext(response.body_iterator)
        self.assertIn("data:", first_chunk)
        await response.body_iterator.aclose()

    async def test_concurrent_failure_mode_recovers_without_stale_failures(self):
        failure = await self.client.post("/failmode", json={"model": "unstable", "status": 503})
        self.assertEqual(failure.status_code, 200)

        failed_responses = await asyncio.gather(
            *(
                self.client.post(
                    "/v1/chat/completions",
                    json={"model": "unstable", "messages": []},
                )
                for _ in range(40)
            )
        )
        self.assertTrue(all(response.status_code == 503 for response in failed_responses))

        cleared = await self.client.post("/failmode", json={"model": "unstable"})
        self.assertEqual(cleared.status_code, 200)
        recovered = await asyncio.gather(
            *(
                self.client.post(
                    "/v1/chat/completions",
                    json={"model": "unstable", "messages": []},
                )
                for _ in range(40)
            )
        )
        self.assertTrue(all(response.status_code == 200 for response in recovered))


if __name__ == "__main__":
    unittest.main()
