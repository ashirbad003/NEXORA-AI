import unittest
import sys
import os

# Import validation functions from scripts/validate_feature_registry.py
from scripts.validate_feature_registry import (
    parse_feature_registry,
    validate_traceability_matrix,
    validate_implementation_status,
    validate_dependency_map
)

class TestFeatureRegistryIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry_path = "docs/MASTER_FEATURE_REGISTRY.md"
        cls.matrix_path = "docs/FEATURE_TRACEABILITY_MATRIX.md"
        cls.status_path = "docs/FEATURE_IMPLEMENTATION_STATUS.md"
        cls.dep_path = "docs/FEATURE_DEPENDENCY_MAP.md"
        
        cls.features, cls.parse_errors = parse_feature_registry(cls.registry_path)

    def test_parse_without_errors(self):
        self.assertEqual(len(self.parse_errors), 0, f"Parse errors encountered: {self.parse_errors}")

    def test_exact_feature_count(self):
        self.assertIsNotNone(self.features)
        self.assertEqual(len(self.features), 346, f"Expected 346 features, got {len(self.features)}")

    def test_feature_id_continuity(self):
        expected_ids = {f"FEAT-{i:03d}" for i in range(1, 347)}
        actual_ids = set(self.features.keys())
        self.assertEqual(actual_ids, expected_ids, "Feature IDs are not strictly continuous from FEAT-001 to FEAT-346")

    def test_required_fields_present_and_non_empty(self):
        for fid, data in self.features.items():
            self.assertTrue(len(data["title"]) > 0, f"Feature {fid} has empty title")
            fields = data["fields"]
            self.assertIn("- **Category:**", fields, f"{fid} missing Category")
            self.assertIn("- **Description:**", fields, f"{fid} missing Description")
            self.assertIn("- **Frontend Requirements:**", fields, f"{fid} missing Frontend Requirements")
            self.assertIn("- **Backend Requirements:**", fields, f"{fid} missing Backend Requirements")
            self.assertIn("- **Database Requirements:**", fields, f"{fid} missing Database Requirements")
            self.assertIn("- **API Requirements:**", fields, f"{fid} missing API Requirements")
            self.assertIn("- **Security Requirements:**", fields, f"{fid} missing Security Requirements")
            self.assertIn("- **Acceptance Criteria:**", fields, f"{fid} missing Acceptance Criteria")
            self.assertIn("- **Test Cases:**", fields, f"{fid} missing Test Cases")
            self.assertIn("- **Status:**", fields, f"{fid} missing Status")
            self.assertIn("- **Dependencies:**", fields, f"{fid} missing Dependencies")

    def test_traceability_matrix_consistency(self):
        errors = validate_traceability_matrix(self.matrix_path, set(self.features.keys()))
        self.assertEqual(len(errors), 0, f"Traceability matrix errors: {errors}")

    def test_implementation_status_consistency(self):
        errors = validate_implementation_status(self.status_path, set(self.features.keys()))
        self.assertEqual(len(errors), 0, f"Implementation status errors: {errors}")

    def test_dependency_map_consistency(self):
        errors = validate_dependency_map(self.dep_path, set(self.features.keys()))
        self.assertEqual(len(errors), 0, f"Dependency map errors: {errors}")

    def test_dependency_references_validity(self):
        import re
        actual_ids = set(self.features.keys())
        for fid, f in self.features.items():
            dep_str = f["fields"].get("- **Dependencies:**", "")
            refs = re.findall(r'FEAT-\d{3}', dep_str)
            for ref in refs:
                self.assertIn(ref, actual_ids, f"{fid} references non-existent dependency {ref}")

if __name__ == "__main__":
    unittest.main()
