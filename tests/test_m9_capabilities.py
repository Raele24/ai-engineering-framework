#!/usr/bin/env python3
"""M9-01 Regression & Unit Tests: Canonical platform capability model & upstream registry parity."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import platform_capabilities  # noqa: E402
import sync_adapters  # noqa: E402
import validate  # noqa: E402


class TestM9PlatformCapabilities(unittest.TestCase):
    """Focused verification for core/platform-capabilities.json, loader, registry parity, and sync."""

    def test_m9_01_valid_capability_model_and_evidence_boundaries(self) -> None:
        model = platform_capabilities.load_platform_capabilities()
        self.assertEqual(model["schema_version"], "1.0.0")
        self.assertEqual(
            model["platform_ids"],
            ["antigravity", "copilot", "claude-code", "codex", "gemini-cli"],
        )

        # Evidence integrity: only Antigravity may hold RUNTIME_VERIFIED in v0.3.0 baseline
        for pid in model["platform_ids"]:
            plat = platform_capabilities.get_platform(model, pid)
            if pid == "antigravity":
                self.assertEqual(plat["runtime_status"], "RUNTIME_VERIFIED")
            else:
                self.assertNotEqual(
                    plat["runtime_status"],
                    "RUNTIME_VERIFIED",
                    f"Platform '{pid}' must not claim RUNTIME_VERIFIED without runtime evidence",
                )

    def test_m9_02_rejects_missing_required_fields(self) -> None:
        base = json.loads(platform_capabilities.DEFAULT_CAPABILITIES_PATH.read_text(encoding="utf-8"))

        # Missing top-level key
        bad_top = copy.deepcopy(base)
        del bad_top["schema_version"]
        errs_top = platform_capabilities.validate_capability_data(bad_top)
        self.assertTrue(any("schema_version" in e for e in errs_top), f"Expected schema_version error, got: {errs_top}")

        # Missing platform-level capability domain
        bad_plat = copy.deepcopy(base)
        del bad_plat["platforms"][0]["tool_id_map"]
        errs_plat = platform_capabilities.validate_capability_data(bad_plat)
        self.assertTrue(any("tool_id_map" in e for e in errs_plat), f"Expected tool_id_map error, got: {errs_plat}")

    def test_m9_03_rejects_duplicate_platform_identifiers(self) -> None:
        base = json.loads(platform_capabilities.DEFAULT_CAPABILITIES_PATH.read_text(encoding="utf-8"))
        dup_data = copy.deepcopy(base)
        dup_data["platforms"].append(copy.deepcopy(base["platforms"][0]))

        errors = platform_capabilities.validate_capability_data(dup_data)
        self.assertTrue(
            any("Duplicate platform identifier" in e and "antigravity" in e for e in errors),
            f"Expected duplicate platform ID error, got: {errors}",
        )

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp) / "dup-capabilities.json"
            tmp_path.write_text(json.dumps(dup_data), encoding="utf-8")
            with self.assertRaises(platform_capabilities.CapabilityModelError):
                platform_capabilities.load_platform_capabilities(tmp_path)

    def test_m9_04_rejects_invalid_capability_and_runtime_states(self) -> None:
        base = json.loads(platform_capabilities.DEFAULT_CAPABILITIES_PATH.read_text(encoding="utf-8"))
        bad_state = copy.deepcopy(base)
        bad_state["platforms"][1]["native_skill_dirs"]["state"] = "assumed_supported"
        bad_state["platforms"][1]["runtime_status"] = "FULLY_SUPPORTED"

        errors = platform_capabilities.validate_capability_data(bad_state)
        self.assertTrue(any("invalid state 'assumed_supported'" in e for e in errors), errors)
        self.assertTrue(any("invalid runtime_status 'FULLY_SUPPORTED'" in e for e in errors), errors)

    def test_m9_05_rejects_unknown_platform_lookup_and_mismatch(self) -> None:
        model = platform_capabilities.load_platform_capabilities()
        with self.assertRaises(platform_capabilities.CapabilityModelError) as ctx:
            platform_capabilities.get_platform(model, "nonexistent-runtime")
        self.assertIn("Unknown platform identifier 'nonexistent-runtime'", str(ctx.exception))

    def test_m9_06_upstream_registry_parity_includes_growth_media(self) -> None:
        registry = json.loads((REPO_ROOT / "skills" / "registry.json").read_text(encoding="utf-8"))
        entries = sync_adapters.build_antigravity_skills_entries(registry)
        entry_paths = [e["path"] for e in entries]

        self.assertEqual(
            entry_paths,
            [
                "skills/core",
                "skills/optional/communication",
                "skills/optional/context-engineering",
                "skills/optional/agent-architecture",
                "skills/optional/frontend-design",
                "skills/optional/growth-media",
            ],
        )

        root_agy = json.loads((REPO_ROOT / ".agents" / "skills.json").read_text(encoding="utf-8"))
        adapter_agy = json.loads((REPO_ROOT / "adapters" / "antigravity" / "skills.json").read_text(encoding="utf-8"))
        self.assertEqual(root_agy["entries"], entries)
        self.assertEqual(adapter_agy["entries"], entries)

        # Negative parity verification: dropping growth-media from .agents/skills.json must fail validation
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp) / "parity-test"
            (tmp_root / "skills" / "optional" / "growth-media" / "seo-audit").mkdir(parents=True)
            (tmp_root / "skills" / "core" / "grill-me").mkdir(parents=True)
            (tmp_root / "skills" / "registry.json").write_text(
                (REPO_ROOT / "skills" / "registry.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (tmp_root / ".agents").mkdir(parents=True)
            (tmp_root / ".agents" / "skills.json").write_text(
                json.dumps({"entries": [{"path": "skills/core"}]}),
                encoding="utf-8",
            )
            errs = validate.check_skills_and_registry(tmp_root)
            self.assertTrue(
                any("omits registered skill" in e and "growth-media" in e for e in errs),
                f"Expected missing growth-media directory error, got: {errs}",
            )

    def test_m9_07_deterministic_repeated_sync_check(self) -> None:
        ok1, drifted1 = sync_adapters.sync_adapters(REPO_ROOT, check_only=True)
        self.assertTrue(ok1, f"Adapters drifted before repeated check: {drifted1}")
        expected1 = sync_adapters.generate_expected_files(REPO_ROOT)
        expected2 = sync_adapters.generate_expected_files(REPO_ROOT)
        self.assertEqual(expected1, expected2)

    def test_m9_08_exact_evidence_statuses_unsupported_states_and_determinism(self) -> None:
        model_a = platform_capabilities.load_platform_capabilities()
        model_b = platform_capabilities.load_platform_capabilities()
        self.assertEqual(model_a, model_b)

        expected_runtime_status = {
            "antigravity": "RUNTIME_VERIFIED",
            "copilot": "BLOCKED_EXTERNAL",
            "claude-code": "BLOCKED_EXTERNAL",
            "codex": "PARTIAL_RUNTIME_VERIFIED",
            "gemini-cli": "BLOCKED_EXTERNAL",
        }
        self.assertEqual(set(model_a["platform_ids"]), set(expected_runtime_status.keys()))

        for pid, expected_status in expected_runtime_status.items():
            plat = platform_capabilities.get_platform(model_a, pid)
            self.assertEqual(plat["runtime_status"], expected_status)
            for domain in platform_capabilities.REQUIRED_CAPABILITY_DOMAINS:
                self.assertIn(plat[domain]["state"], platform_capabilities.VALID_CAPABILITY_STATES)

        # Verify explicit unsupported / unknown capability boundaries remain documented
        self.assertEqual(platform_capabilities.get_platform(model_a, "copilot")["hooks_support"]["state"], "unsupported")
        self.assertEqual(platform_capabilities.get_platform(model_a, "codex")["hooks_support"]["state"], "unsupported")
        self.assertEqual(platform_capabilities.get_platform(model_a, "gemini-cli")["hooks_support"]["state"], "unknown")

    def test_m9_09_canonical_registry_hashes_uniqueness_and_contract_level(self) -> None:
        registry = json.loads((REPO_ROOT / "skills" / "registry.json").read_text(encoding="utf-8"))
        skills = registry.get("skills", [])
        self.assertEqual(len(skills), 33)
        self.assertEqual(registry.get("total_skills"), 33)

        names = [str(item["name"]) for item in skills]
        self.assertEqual(len(names), len(set(names)), "Duplicate skill entries in canonical skills/registry.json")

        for item in skills:
            skill_path = REPO_ROOT / Path(str(item["path"]))
            self.assertTrue(skill_path.exists(), f"Missing canonical skill file: {item['path']}")
            actual_sha = hashlib.sha256(skill_path.read_bytes()).hexdigest()
            self.assertEqual(
                str(item.get("sha256", "")).lower(),
                actual_sha,
                f"Registry SHA-256 mismatch for '{item['name']}'",
            )

        # Static tests only validate static/contract levels; never establish RUNTIME_VERIFIED
        self.assertIn("CONTRACT_VALIDATED", platform_capabilities.VALID_RUNTIME_STATUSES)
        self.assertIn("STATICALLY_VALIDATED", platform_capabilities.VALID_RUNTIME_STATUSES)


if __name__ == "__main__":
    unittest.main()
