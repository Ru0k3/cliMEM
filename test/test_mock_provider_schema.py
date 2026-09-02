import unittest

from test.mock_provider import (
    SchemaResolutionError,
    _schema_value,
    _structured_payload,
)


class MockProviderSchemaTests(unittest.TestCase):
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

    def test_unresolved_reference_is_explicit(self):
        with self.assertRaisesRegex(SchemaResolutionError, "unresolved schema reference"):
            _schema_value("value", {"$ref": "#/$defs/Unknown"}, {"$defs": {}})

    def test_cyclic_reference_is_explicit(self):
        root = {"$defs": {"Node": {"$ref": "#/$defs/Node"}}}
        with self.assertRaisesRegex(SchemaResolutionError, "cyclic schema reference"):
            _schema_value("node", {"$ref": "#/$defs/Node"}, root)

    def test_empty_enum_is_rejected(self):
        with self.assertRaisesRegex(SchemaResolutionError, "empty enum"):
            _schema_value("status", {"enum": []}, {})


if __name__ == "__main__":
    unittest.main()
