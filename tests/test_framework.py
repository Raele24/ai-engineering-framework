#!/usr/bin/env python3
"""Automated unit and integration test suite for the AI Engineering Framework.

Tests cover:
1. Canonical YAML frontmatter parser and deterministic digest computation.
2. Platform adapter synchronization (`sync_adapters.py`) and drift detection.
3. Full repository validation (`validate.py`) across schemas, agents, skills, links, and secret scanning.
4. Non-destructive project bootstrapping (`bootstrap.py`), lockfile tracking, and preservation of user-modified files on `--update`.
"""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import bootstrap  # noqa: E402
import sync_adapters  # noqa: E402
import validate  # noqa: E402


class TestAIEngineeringFramework(unittest.TestCase):
    """End-to-end verification of framework scripts, schemas, and invariants."""

    def test_01_frontmatter_parser(self) -> None:
        sample = (
            "---\n"
            "name: sample-role\n"
            'title: "Sample Role"\n'
            "phases: [1, 2, 3]\n"
            "enabled: true\n"
            "---\n"
            "# Body\n"
        )
        parsed = sync_adapters.parse_simple_frontmatter(sample)
        self.assertEqual(parsed["name"], "sample-role")
        self.assertEqual(parsed["title"], "Sample Role")
        self.assertEqual(parsed["phases"], [1, 2, 3])
        self.assertTrue(parsed["enabled"])

    def test_02_canonical_agents_and_skills_count(self) -> None:
        agents, registry = sync_adapters.load_canonical_metadata(REPO_ROOT)
        self.assertEqual(len(agents), 8, "Expected exactly 8 non-redundant canonical agent roles")
        skills = registry.get("skills", [])
        self.assertEqual(len(skills), 15, "Expected 6 core skills + 9 optional skills in registry.json")

    def test_03_adapter_sync_check_passes(self) -> None:
        ok, drifted = sync_adapters.sync_adapters(REPO_ROOT, check_only=True)
        self.assertTrue(ok, f"Adapters out of sync: {drifted}")

    def test_04_full_repository_validation_passes(self) -> None:
        passed, report = validate.run_validation(REPO_ROOT)
        self.assertTrue(passed, f"Repository validation failed: {report}")

    def test_05_bootstrap_creates_and_preserves_consumer_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "sample-consumer-app"
            target.mkdir(parents=True, exist_ok=True)

            # Pre-create a consumer README.md to ensure bootstrap never overwrites it
            custom_readme = target / "README.md"
            custom_readme.write_text("# My Custom Consumer App\n", encoding="utf-8")

            # 1. Dry-run should not create lockfile or project.framework.json
            dry_summary = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "copilot"],
                profile="standard",
                optional_packs=["communication"],
                dry_run=True,
            )
            self.assertGreater(len(dry_summary["created"]), 10)
            self.assertFalse((target / "project.framework.json").exists())

            # 2. Real bootstrap run
            real_summary = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "copilot"],
                profile="standard",
                optional_packs=["communication"],
                dry_run=False,
            )
            self.assertGreater(len(real_summary["created"]), 10)
            self.assertTrue((target / "project.framework.json").exists())
            self.assertTrue((target / ".framework-lock.json").exists())
            self.assertTrue((target / "AGENTS.md").exists())
            self.assertTrue((target / ".github" / "copilot-instructions.md").exists())
            self.assertTrue((target / ".agents" / "rules" / "framework-core.md").exists())
            self.assertEqual(custom_readme.read_text(encoding="utf-8"), "# My Custom Consumer App\n")

            # 3. Simulate user customizing AGENTS.md and project.framework.json locally
            agents_md = target / "AGENTS.md"
            agents_md.write_text("# User Customized AGENTS.md\n", encoding="utf-8")

            # 4. Run --update: user-customized AGENTS.md must be skipped/preserved!
            update_summary = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "copilot"],
                profile="standard",
                optional_packs=["communication"],
                update_mode=True,
                dry_run=False,
            )
            self.assertIn("AGENTS.md", update_summary["skipped_modified"])
            self.assertEqual(agents_md.read_text(encoding="utf-8"), "# User Customized AGENTS.md\n")


if __name__ == "__main__":
    unittest.main()
