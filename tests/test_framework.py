#!/usr/bin/env python3
"""Automated unit and integration test suite for the AI Engineering Framework.

Tests cover:
1. Canonical YAML frontmatter parser and deterministic digest computation.
2. Verification of all 8 canonical agent roles and all 30 registered skills (including P0/P1/P2 categories and UPSTREAM_SKILL.md preservation).
3. Platform adapter synchronization (`sync_adapters.py`) and drift detection.
4. Full repository validation (`validate.py`) across schemas, agents, skills, links, and secret scanning.
5. Offline execution of the vendored UI/UX Pro Max BM25 search engine (`search.py`) for Angular and design system generation.
6. Non-destructive project bootstrapping (`bootstrap.py`), lockfile tracking, and preservation of user-modified files on `--update`.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
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
    """End-to-end verification of framework scripts, schemas, skills, and invariants."""

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

    def test_02_canonical_agents_and_skills_inventory(self) -> None:
        agents, registry = sync_adapters.load_canonical_metadata(REPO_ROOT)
        self.assertEqual(len(agents), 13, "Expected 13 non-redundant canonical agent roles")
        agent_names = {a.get("name") for a in agents}
        for expected_role in [
            "product-analyst",
            "software-architect",
            "ui-ux-designer",
            "data-engineer",
            "planner-orchestrator",
            "backend-engineer",
            "frontend-engineer",
            "ai-engineer",
            "implementation-engineer",
            "code-reviewer",
            "qa-engineer",
            "security-engineer",
            "devops-release-engineer",
        ]:
            self.assertIn(expected_role, agent_names, f"Missing canonical agent '{expected_role}'")
        skills = registry.get("skills", [])
        self.assertEqual(len(skills), 33, "Expected 33 curated skills in skills/registry.json")

        skill_names = {s["name"] for s in skills}
        for must_have in [
            "ponytail",
            "caveman",
            "i-have-adhd",
            "humanizer",
            "rtk-cli",
            "graphify",
            "context-optimization",
            "context-compression",
            "filesystem-context",
            "memory-systems",
            "session-handoff",
            "multi-agent-patterns",
            "tool-design",
            "evaluation",
            "self-improvement-loops",
            "ui-ux-pro-max",
            "angular-developer",
            "angular-new-app",
            "seo-audit",
            "ai-seo",
            "video-lens",
            "video-use",
        ]:
            self.assertIn(must_have, skill_names, f"Missing required skill '{must_have}' in registry")

    def test_03_adapter_sync_check_passes(self) -> None:
        ok, drifted = sync_adapters.sync_adapters(REPO_ROOT, check_only=True)
        self.assertTrue(ok, f"Adapters out of sync: {drifted}")

    def test_04_full_repository_validation_passes(self) -> None:
        passed, report = validate.run_validation(REPO_ROOT)
        self.assertTrue(passed, f"Repository validation failed: {report}")

    def test_05_ui_ux_pro_max_offline_bm25_search_works(self) -> None:
        search_script = (
            REPO_ROOT
            / "skills"
            / "optional"
            / "frontend-design"
            / "ui-ux-pro-max"
            / "scripts"
            / "search.py"
        )
        self.assertTrue(search_script.exists())
        out = subprocess.check_output(
            [sys.executable, str(search_script), "signals standalone", "--stack", "angular", "--max-results", "2"],
            cwd=REPO_ROOT,
            text=True,
            encoding="utf-8",
        )
        self.assertIn("UI Pro Max Stack Guidelines", out)
        self.assertIn("stacks/angular.csv", out)

    def test_06_bootstrap_creates_and_preserves_consumer_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "sample-consumer-app"
            target.mkdir(parents=True, exist_ok=True)

            custom_readme = target / "README.md"
            custom_readme.write_text("# My Custom Consumer App\n", encoding="utf-8")

            dry_summary = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "copilot"],
                profile="standard",
                optional_packs=["communication", "context-engineering"],
                dry_run=True,
            )
            self.assertGreater(len(dry_summary["created"]), 15)
            self.assertFalse((target / ".aief" / "config.json").exists())

            real_summary = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "copilot"],
                profile="standard",
                optional_packs=["communication", "context-engineering"],
                dry_run=False,
            )
            self.assertGreater(len(real_summary["created"]), 15)
            self.assertTrue((target / ".aief" / "config.json").exists())
            self.assertTrue((target / ".aief" / "lock.json").exists())
            self.assertTrue((target / "AGENTS.md").exists())
            self.assertTrue((target / ".aief" / "skills" / "registry.json").exists())
            self.assertFalse((target / ".aief" / "skills" / "core").exists())
            self.assertTrue((target / ".agents" / "skills" / "ponytail" / "SKILL.md").exists())
            self.assertTrue((target / ".agents" / "skills" / "context-optimization" / "SKILL.md").exists())
            self.assertEqual(custom_readme.read_text(encoding="utf-8"), "# My Custom Consumer App\n")

            agents_md = target / "AGENTS.md"
            agents_md.write_text("# User Customized AGENTS.md\n", encoding="utf-8")

            update_summary = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "copilot"],
                profile="standard",
                optional_packs=["communication", "context-engineering"],
                update_mode=True,
                dry_run=False,
            )
            self.assertIn("AGENTS.md", update_summary["skipped_modified"])
            self.assertEqual(agents_md.read_text(encoding="utf-8"), "# User Customized AGENTS.md\n")


if __name__ == "__main__":
    unittest.main()
