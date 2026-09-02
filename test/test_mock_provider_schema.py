import unittest

import httpx

from test.mock_provider import (
    SchemaResolutionError,
    _schema_value,
    _structured_payload,
    MAX_REQUEST_LOG,
    app,
    request_log,
    _record_request,
    _constraints_conflict,
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

    def test_all_of_disjoint_enums_are_rejected(self):
        schema = {
            "allOf": [
                {"type": "object", "properties": {"state": {"enum": ["ready"]}}},
                {"type": "object", "properties": {"state": {"enum": ["failed"]}}},
            ]
        }
        with self.assertRaisesRegex(SchemaResolutionError, "conflicting allOf constraints"):
            _structured_payload({"response_format": {"json_schema": {"schema": schema}}})

    def test_request_log_keeps_only_bounded_tail(self):
        request_log.clear()
        for index in range(MAX_REQUEST_LOG + 3):
            _record_request({"index": index})
        self.assertEqual(len(request_log), MAX_REQUEST_LOG)
        self.assertEqual(request_log[0]["index"], 3)
        request_log.clear()

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
