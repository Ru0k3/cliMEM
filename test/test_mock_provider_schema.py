import os
import unittest
from unittest.mock import patch

import httpx

from test.mock_provider import (
    SchemaResolutionError,
    _schema_value,
    _structured_payload,
    MAX_REQUEST_LOG,
    MAX_SCHEMA_DEPTH,
    app,
    request_log,
    _record_request,
    _constraints_conflict,
    _read_positive_int,
    _resolve_json_pointer,
    _request_summary,
)


class MockProviderSchemaTests(unittest.IsolatedAsyncioTestCase):
    def test_const_wins_over_type(self):
        self.assertEqual(_schema_value("status", {"type": "string", "const": "ready"}, {}), "ready")

    def test_enum_selects_valid_value(self):
        value = _schema_value("status", {"type": "string", "enum": ["queued", "ready"]}, {})
        self.assertIn(value, {"queued", "ready"})

    def test_default_is_used(self):
        self.assertEqual(_schema_value("limit", {"type": "integer", "default": 25}, {}), 25)

    def test_one_of_skips_unusable_branch(self):
        schema = {"oneOf": [{"$ref": "#/$defs/Missing"}, {"const": "ready"}]}
        self.assertEqual(_schema_value("status", schema, {"$defs": {}}), "ready")

    def test_all_of_merges_properties_and_preserves_defs(self):
        root = {
            "$defs": {"State": {"type": "string", "enum": ["ready"]}},
            "allOf": [
                {"type": "object", "properties": {"name": {"const": "PostgreSQL"}}},
                {"type": "object", "properties": {"state": {"$ref": "#/$defs/State"}}},
            ],
        }
        payload = _structured_payload({"response_format": {"json_schema": {"schema": root}}})
        self.assertEqual(payload, {"name": "PostgreSQL", "state": "ready"})

    def test_nested_one_of_inside_array(self):
        schema = {
            "type": "array",
            "items": {"oneOf": [{"type": "string", "enum": ["postgres"]}, {"const": "sqlite"}]},
        }
        self.assertEqual(_schema_value("items", schema, {}), ["postgres"])

    def test_multi_hop_reference_chain(self):
        root = {"$defs": {"A": {"$ref": "#/$defs/B"}, "B": {"$ref": "#/$defs/C"}, "C": {"const": "ready"}}}
        self.assertEqual(_schema_value("state", {"$ref": "#/$defs/A"}, root), "ready")

    def test_nested_ref_chain_inside_one_of(self):
        root = {
            "$defs": {
                "Ready": {"$ref": "#/$defs/Status"},
                "Status": {"const": "ready"},
            }
        }
        schema = {"oneOf": [{"$ref": "#/$defs/Missing"}, {"$ref": "#/$defs/Ready"}]}
        self.assertEqual(_schema_value("state", schema, root), "ready")

    def test_general_json_pointer_resolves_nested_schema(self):
        root = {"components": {"schemas": {"Widget": {"const": "widget"}}}}
        self.assertEqual(_resolve_json_pointer(root, "#/components/schemas/Widget"), {"const": "widget"})

    def test_percent_decoded_json_pointer_resolves_nested_schema(self):
        root = {"components": {"schemas": {"My Schema": {"const": "decoded"}}}}
        self.assertEqual(_resolve_json_pointer(root, "#/components/schemas/My%20Schema"), {"const": "decoded"})

    def test_invalid_pointer_escape_is_rejected(self):
        with self.assertRaisesRegex(SchemaResolutionError, "invalid JSON Pointer escape"):
            _resolve_json_pointer({"a~2b": 1}, "#/a~2b")

    def test_noncanonical_array_index_is_rejected(self):
        with self.assertRaisesRegex(SchemaResolutionError, "unresolved schema reference"):
            _resolve_json_pointer({"items": ["x"]}, "#/items/01")

    def test_json_pointer_escaping_resolves_definition_name(self):
        root = {"$defs": {"foo/bar~baz": {"const": "escaped"}}}
        reference = {"$ref": "#/$defs/foo~1bar~0baz"}
        self.assertEqual(_schema_value("value", reference, root), "escaped")

    def test_all_of_conflicting_const_is_rejected(self):
        schema = {
            "allOf": [
                {"type": "object", "properties": {"state": {"const": "ready"}}},
                {"type": "object", "properties": {"state": {"const": "failed"}}},
            ]
        }
        with self.assertRaisesRegex(SchemaResolutionError, "conflicting allOf constraints"):
            _structured_payload({"response_format": {"json_schema": {"schema": schema}}})

    def test_all_of_additional_properties_conflict_is_rejected(self):
        schema = {
            "allOf": [
                {"type": "object", "additionalProperties": False},
                {"type": "object", "additionalProperties": True},
            ]
        }
        with self.assertRaisesRegex(SchemaResolutionError, "additionalProperties"):
            _structured_payload({"response_format": {"json_schema": {"schema": schema}}})

    def test_all_of_disjoint_enums_are_rejected(self):
        schema = {
            "allOf": [
                {"type": "object", "properties": {"state": {"enum": ["ready"]}}},
                {"type": "object", "properties": {"state": {"enum": ["failed"]}}},
            ]
        }
        with self.assertRaisesRegex(SchemaResolutionError, "conflicting allOf constraints"):
            _structured_payload({"response_format": {"json_schema": {"schema": schema}}})

    def test_request_log_keeps_only_bounded_redacted_tail(self):
        request_log.clear()
        for index in range(MAX_REQUEST_LOG + 3):
            _record_request({"model": f"model-{index}", "messages": [{"content": "secret"}]})
        self.assertEqual(len(request_log), MAX_REQUEST_LOG)
        self.assertEqual(request_log[0]["model"], "model-3")
        self.assertNotIn("secret", repr(request_log))
        self.assertNotIn("messages", request_log[0])
        request_log.clear()

    def test_invalid_environment_value_is_rejected(self):
        with patch.dict(os.environ, {"MOCK_PROVIDER_TEST_LIMIT": "not-a-number"}):
            with self.assertRaisesRegex(ValueError, "must be an integer"):
                _read_positive_int("MOCK_PROVIDER_TEST_LIMIT", 10)

    def test_request_summary_contains_metadata_only(self):
        summary = _request_summary({"model": "mock", "messages": [{"role": "user", "content": "secret prompt"}]}, "chat")
        self.assertEqual(summary["message_count"], 1)
        self.assertNotIn("secret prompt", repr(summary))
        self.assertNotIn("messages", summary)

    async def test_embedding_endpoint_returns_openai_compatible_vectors(self):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            await client.delete("/reset")
            response = await client.post("/v1/embeddings", json={"model": "mock-embedding", "input": ["secret embedding"]})
            diagnostics = await client.get("/request-log")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["object"], "list")
        self.assertEqual(len(payload["data"]), 1)
        self.assertEqual(len(payload["data"][0]["embedding"]), 384)
        self.assertEqual(diagnostics.json()["requests"][-1]["kind"], "embeddings")
        self.assertNotIn("secret embedding", repr(diagnostics.json()))

    async def test_chat_endpoint_returns_non_streaming_success(self):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            await client.delete("/reset")
            response = await client.post("/v1/chat/completions", json={"model": "mock-chat", "messages": [{"role": "user", "content": "hello"}]})
            diagnostics = await client.get("/request-log")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["choices"][0]["message"]["role"], "assistant")
        self.assertIn("Acknowledged", response.json()["choices"][0]["message"]["content"])
        self.assertEqual(diagnostics.json()["requests"][-1]["kind"], "chat")
        self.assertNotIn("hello", repr(diagnostics.json()))

    async def test_chat_endpoint_returns_streaming_sse_success(self):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/v1/chat/completions", json={"model": "mock-chat", "stream": True, "messages": []})
        self.assertEqual(response.status_code, 200)
        self.assertIn("data:", response.text)
        self.assertIn("[DONE]", response.text)

    async def test_invalid_structured_schema_returns_http_400(self):
        payload = {
            "model": "mock-chat",
            "stream": False,
            "response_format": {"json_schema": {"schema": {"$ref": "#/$defs/Missing"}}},
            "messages": [],
        }
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/v1/chat/completions", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "invalid_structured_schema")

    def test_unresolved_reference_is_explicit(self):
        with self.assertRaisesRegex(SchemaResolutionError, "unresolved schema reference"):
            _schema_value("value", {"$ref": "#/$defs/Unknown"}, {"$defs": {}})

    def test_cyclic_reference_is_explicit(self):
        root = {"$defs": {"Node": {"$ref": "#/$defs/Node"}}}
        with self.assertRaisesRegex(SchemaResolutionError, "cyclic schema reference"):
            _schema_value("node", {"$ref": "#/$defs/Node"}, root)

    def test_schema_depth_limit_is_enforced(self):
        schema = {"type": "object", "properties": {"child": {"type": "object", "properties": {"leaf": {"const": "x"}}}}}
        with self.assertRaisesRegex(SchemaResolutionError, "maximum schema depth"):
            _schema_value("root", schema, {}, depth=MAX_SCHEMA_DEPTH)

    def test_const_and_object_enum_intersection_is_safe(self):
        self.assertFalse(_constraints_conflict({"const": {"kind": "node"}}, {"enum": [{"kind": "node"}]}))
        self.assertTrue(_constraints_conflict({"const": {"kind": "node"}}, {"enum": [{"kind": "edge"}]}))

    async def test_streamed_invalid_schema_returns_400_without_sse(self):
        payload = {
            "model": "mock-chat",
            "stream": True,
            "response_format": {"json_schema": {"schema": {"$ref": "#/$defs/Missing"}}},
            "messages": [],
        }
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/v1/chat/completions", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("data:", response.text)
        self.assertEqual(response.json()["error"]["code"], "invalid_structured_schema")

    async def test_malformed_failmode_and_invalid_values_return_400(self):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            malformed = await client.post("/failmode", content=b"{invalid")
            missing_model = await client.post("/failmode", json={"status": 500})
            invalid_status = await client.post("/failmode", json={"model": "mock", "status": "500"})
            out_of_range = await client.post("/failmode", json={"model": "mock", "status": 700})
        self.assertEqual(malformed.status_code, 400)
        self.assertEqual(malformed.json()["error"]["code"], "invalid_json")
        for response in (missing_model, invalid_status, out_of_range):
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["error"]["code"], "invalid_failmode")

    async def test_malformed_json_returns_400(self):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            chat_response = await client.post("/v1/chat/completions", content=b"{invalid")
            embedding_response = await client.post("/v1/embeddings", content=b"{invalid")
        self.assertEqual(chat_response.status_code, 400)
        self.assertEqual(embedding_response.status_code, 400)
        self.assertEqual(chat_response.json()["error"]["code"], "invalid_json")
        self.assertEqual(embedding_response.json()["error"]["code"], "invalid_json")

    def test_empty_enum_is_rejected(self):
        with self.assertRaisesRegex(SchemaResolutionError, "empty enum"):
            _schema_value("status", {"enum": []}, {})


if __name__ == "__main__":
    unittest.main()
