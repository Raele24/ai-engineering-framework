#!/usr/bin/env python3
"""M7 Regression Test Suite: Consumer-aware validation, optional skill pack filtering,
Antigravity adapter relative path rewriting, stack templates, and Windows SDK preflight.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import bootstrap  # noqa: E402
import validate  # noqa: E402


class TestM7FrameworkHardening(unittest.TestCase):
    """TDD verification for M7-01 (REC-01) through M7-05."""

    def test_m7_01_validation_modes_framework_consumer_and_auto(self) -> None:
        self.assertEqual(validate.detect_validation_mode(REPO_ROOT), "framework")
        passed_fw, report_fw = validate.run_validation(REPO_ROOT, mode="framework")
        self.assertTrue(passed_fw, f"Framework validation failed: {report_fw}")

        with tempfile.TemporaryDirectory() as tmp:
            consumer_dir = Path(tmp) / "clean-consumer"
            bootstrap.bootstrap_project(
                target_dir=consumer_dir,
                platforms=["antigravity", "copilot"],
                profile="standard",
                optional_packs=["communication"],
            )

            # Ensure framework-authoring files are NOT in consumer_dir
            self.assertFalse((consumer_dir / "PROJECT_CHARTER.md").exists())
            self.assertFalse((consumer_dir / ".aief" / "scripts" / "bootstrap.py").exists())
            self.assertFalse((consumer_dir / ".aief" / "scripts" / "sync_adapters.py").exists())
            self.assertFalse((consumer_dir / "scripts" / "bootstrap.py").exists())

            self.assertEqual(validate.detect_validation_mode(consumer_dir), "consumer")
            passed_auto, report_auto = validate.run_validation(consumer_dir, mode="auto")
            self.assertTrue(passed_auto, f"Auto consumer validation failed: {report_auto}")

            passed_con, report_con = validate.run_validation(consumer_dir, mode="consumer")
            self.assertTrue(passed_con, f"Explicit consumer validation failed: {report_con}")

    def test_m7_01_consumer_validation_detects_invalid_and_incomplete_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            consumer_dir = Path(tmp) / "broken-consumer"
            bootstrap.bootstrap_project(
                target_dir=consumer_dir,
                platforms=["antigravity"],
                profile="standard",
                optional_packs=[],
            )

            # 1. Remove .aief/state/manifest.json -> must fail
            manifest_path = consumer_dir / ".aief" / "state" / "manifest.json"
            manifest_backup = manifest_path.read_text(encoding="utf-8")
            manifest_path.unlink()

            passed, report = validate.run_validation(consumer_dir, mode="consumer")
            self.assertFalse(passed)
            self.assertTrue(
                any("manifest.json" in err for errs in report.values() for err in errs),
                f"Expected missing manifest.json error, got: {report}",
            )

            # Restore manifest, inject invalid handoff packet & fake secret
            manifest_path.write_text(manifest_backup, encoding="utf-8")
            bad_handoff = consumer_dir / ".aief" / "state" / "handoffs" / "phase-01-handoff.json"
            bad_handoff.write_text(json.dumps({"schema_version": "1.0.0"}), encoding="utf-8")

            secret_file = consumer_dir / "leaked.txt"
            fake_token = "ghp_" + ("a" * 36)
            secret_file.write_text(f"token = {fake_token}\n", encoding="utf-8")

            passed2, report2 = validate.run_validation(consumer_dir, mode="consumer")
            self.assertFalse(passed2)
            self.assertTrue(len(report2.get("consumer_state", [])) > 0)
            self.assertTrue(len(report2.get("secret_scan", [])) > 0)

    def test_m7_02_optional_pack_filtering_four_scenarios(self) -> None:
        scenarios = [
            ("core-only", [], 8, {"ponytail", "grill-me", "tdd-cycle", "graphify"}, {"caveman", "ui-ux-pro-max", "evaluation", "seo-audit"}),
            ("core-plus-design-ui", ["design-ui"], 13, {"ponytail", "ui-ux-pro-max", "angular-developer"}, {"caveman", "evaluation", "seo-audit"}),
            (
                "core-plus-context-and-agent",
                ["context-engineering", "agent-architecture"],
                17,
                {"ponytail", "context-optimization", "filesystem-context", "session-handoff", "evaluation", "tool-design"},
                {"caveman", "ui-ux-pro-max", "seo-audit"},
            ),
            (
                "all-packs",
                ["communication", "context-engineering", "agent-architecture", "frontend-design", "growth-media"],
                33,
                {"ponytail", "caveman", "i-have-adhd", "humanizer", "context-optimization", "session-handoff", "evaluation", "ui-ux-pro-max", "seo-audit"},
                set(),
            ),
        ]

        for label, packs, expected_count, must_include, must_exclude in scenarios:
            with self.subTest(scenario=label):
                with tempfile.TemporaryDirectory() as tmp:
                    target = Path(tmp) / f"consumer-{label}"
                    bootstrap.bootstrap_project(
                        target_dir=target,
                        platforms=["antigravity", "copilot", "claude-code"],
                        optional_packs=packs,
                    )

                    reg = json.loads((target / ".aief" / "skills" / "registry.json").read_text(encoding="utf-8"))
                    self.assertEqual(reg["total_skills"], expected_count)
                    self.assertEqual(len(reg["skills"]), expected_count)

                    installed_names = {s["name"] for s in reg["skills"]}
                    for inc in must_include:
                        self.assertIn(inc, installed_names)
                        # Verify metadata preservation
                        entry = next(s for s in reg["skills"] if s["name"] == inc)
                        self.assertTrue(entry.get("license"))
                        self.assertTrue(entry.get("source"))
                        self.assertTrue((target / Path(entry["path"])).exists())

                    agents_md = (target / "AGENTS.md").read_text(encoding="utf-8")
                    for exc in must_exclude:
                        self.assertNotIn(exc, installed_names)
                        self.assertNotIn(f"`{exc}`", agents_md)

                    passed, report = validate.run_validation(target, mode="consumer")
                    self.assertTrue(passed, f"Scenario '{label}' failed consumer validation: {report}")

    def test_m7_03_antigravity_adapter_path_rewriting_and_resolution(self) -> None:
        sample_md = (
            "---\ntrigger: always_on\n---\n"
            "Follow [`AGENTS.md`](../../../AGENTS.md) and [`core/rules/engineering-principles.md`](../../../core/rules/engineering-principles.md#tdd).\n"
            "External link: [GitHub](https://github.com/example/repo/../../../keep) and [Anchor](#local-section).\n"
            "Literal prose ../../../ should not change, nor should inline code `../../../AGENTS.md`.\n"
            "```bash\ncd ../../../do-not-touch\n```\n"
        )
        rewritten = bootstrap.rewrite_markdown_relative_links(
            sample_md,
            src_rel_path="adapters/antigravity/rules/framework-core.md",
            dst_rel_path=".agents/rules/framework-core.md",
        )
        self.assertIn("[`AGENTS.md`](../../AGENTS.md)", rewritten)
        self.assertIn(
            "[`core/rules/engineering-principles.md`](../../core/rules/engineering-principles.md#tdd)",
            rewritten,
        )
        self.assertIn("https://github.com/example/repo/../../../keep", rewritten)
        self.assertIn("[Anchor](#local-section)", rewritten)
        self.assertIn("Literal prose ../../../ should not change", rewritten)
        self.assertIn("`../../../AGENTS.md`", rewritten)
        self.assertIn("cd ../../../do-not-touch", rewritten)

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agy-consumer"
            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity"],
                optional_packs=[],
            )
            rule_file = target / ".agents" / "rules" / "framework-core.md"
            self.assertTrue(rule_file.exists())
            rule_text = rule_file.read_text(encoding="utf-8")
            self.assertNotIn("../../../AGENTS.md", rule_text)
            self.assertIn("../../AGENTS.md", rule_text)

            # Verify that breaking the link to escape consumer workspace fails validation
            rule_file.write_text(rule_text.replace("../../AGENTS.md", "../../../../AGENTS.md"), encoding="utf-8")
            passed, report = validate.run_validation(target, mode="consumer")
            self.assertFalse(passed)
            self.assertTrue(len(report["markdown_links"]) > 0)

    def test_m7_04_stack_templates_gitignore_preservation_and_preflight(self) -> None:
        import preflight  # noqa: F401

        with tempfile.TemporaryDirectory() as tmp:
            # Case A: Clean directory without .gitignore -> creates .gitignore
            target_a = Path(tmp) / "stack-clean"
            bootstrap.bootstrap_project(
                target_dir=target_a,
                platforms=["antigravity"],
                optional_packs=[],
                stacks=["dotnet", "node/angular", "python"],
            )
            gitignore_a = target_a / ".gitignore"
            self.assertTrue(gitignore_a.exists())
            content_a = gitignore_a.read_text(encoding="utf-8")
            self.assertIn("bin/", content_a)
            self.assertIn("node_modules/", content_a)
            self.assertIn("__pycache__/", content_a)
            self.assertTrue((target_a / ".aief" / "ENVIRONMENT_PREFLIGHT.md").exists())

            # Case B: Existing consumer .gitignore -> NEVER overwrite, write .aief/gitignore.recommended
            target_b = Path(tmp) / "stack-existing"
            target_b.mkdir(parents=True, exist_ok=True)
            custom_gi = "# Custom Consumer Gitignore\nmy-secret-folder/\n"
            (target_b / ".gitignore").write_text(custom_gi, encoding="utf-8")

            bootstrap.bootstrap_project(
                target_dir=target_b,
                platforms=["antigravity"],
                optional_packs=[],
                stacks=["dotnet"],
            )
            self.assertEqual((target_b / ".gitignore").read_text(encoding="utf-8"), custom_gi)
            rec_gi = target_b / ".aief" / "gitignore.recommended"
            self.assertTrue(rec_gi.exists())
            self.assertIn("bin/", rec_gi.read_text(encoding="utf-8"))

            # Verify preflight Windows user-space DOTNET_ROOT detection
            report = preflight.run_preflight_checks(["dotnet", "node-angular", "python"])
            self.assertIn("dotnet", report["stacks"])
            self.assertIn("node-angular", report["stacks"])
            self.assertIn("python", report["stacks"])
            self.assertIn(report["stacks"]["dotnet"]["status"], {"AVAILABLE", "AVAILABLE_USER_SPACE", "MISSING"})
            self.assertTrue(len(report["stacks"]["dotnet"]["guidance"]) > 0)

    def test_m7_05_bootstrap_repeatability_and_determinism(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "repeat-consumer"
            first = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "copilot"],
                optional_packs=["communication"],
                stacks=["dotnet"],
            )
            self.assertGreater(len(first["created"]), 10)

            second = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "copilot"],
                optional_packs=["communication"],
                stacks=["dotnet"],
            )
            self.assertEqual(second["created"], [])
            self.assertEqual(second["updated"], [])

            # Cross-directory byte-for-byte determinism check
            other_root = Path(tmp) / "other" / "repeat-consumer"
            bootstrap.bootstrap_project(
                target_dir=other_root,
                platforms=["antigravity", "copilot"],
                optional_packs=["communication"],
                stacks=["dotnet"],
            )
            for p1 in sorted(target.rglob("*")):
                if p1.is_file():
                    rel = p1.relative_to(target)
                    p2 = other_root / rel
                    self.assertTrue(p2.exists(), f"Missing {rel} in second bootstrap")
                    self.assertEqual(
                        bootstrap.sha256_file(p1),
                        bootstrap.sha256_file(p2),
                        f"Non-deterministic content in {rel}",
                    )

            # Updating optional_packs from ['communication'] to [] (core-only) prunes optional skills cleanly
            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "copilot"],
                optional_packs=[],
                stacks=["dotnet"],
                update_mode=True,
            )
            passed, report = validate.run_validation(target, mode="consumer")
            self.assertTrue(passed, f"Validation after pack pruning failed: {report}")

    def test_m7_06_dotnet_sdk_detection_missing_and_userspace(self) -> None:
        import preflight

        with tempfile.TemporaryDirectory() as tmp:
            empty_home = Path(tmp) / "empty-home"
            empty_home.mkdir(parents=True, exist_ok=True)
            res_missing = preflight.detect_dotnet_sdk(env={"PATH": ""}, home_dir=empty_home)
            self.assertEqual(res_missing["status"], "MISSING")
            self.assertIn("dotnet-install.ps1", str(res_missing["guidance"]))

            # If host has user-space %USERPROFILE%\.dotnet, test with empty PATH so it detects AVAILABLE_USER_SPACE
            real_user_dotnet = Path.home() / ".dotnet"
            if (real_user_dotnet / "dotnet.exe").exists() or (real_user_dotnet / "dotnet").exists():
                res_userspace = preflight.detect_dotnet_sdk(env={"PATH": ""}, home_dir=Path.home())
                self.assertEqual(res_userspace["status"], "AVAILABLE_USER_SPACE")
                self.assertIn("DOTNET_ROOT", str(res_userspace["guidance"]))


if __name__ == "__main__":
    unittest.main()
