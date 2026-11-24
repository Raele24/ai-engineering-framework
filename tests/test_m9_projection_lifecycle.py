#!/usr/bin/env python3
"""M9-02 Lifecycle, Ownership, Migration, Security & Contract Test Suite.

Covers all 12 M9-02A lifecycle scenarios (LT-01..LT-12) plus Lockfile v0.3.0 migration,
Markdown link rewriting, multi-file projected skill assets, and consumer-safe validation.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import bootstrap  # noqa: E402
import validate  # noqa: E402


def _copy_mock_framework(dst_framework: Path) -> Path:
    """Create an isolated copy of the canonical framework in dst_framework for mutation tests."""
    for folder in (
        "core",
        "agents",
        "workflows",
        "quality",
        "security",
        "templates",
        "scripts",
        "adapters",
        "skills",
    ):
        src = REPO_ROOT / folder
        if src.exists():
            shutil.copytree(
                src,
                dst_framework / folder,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
    for root_file in ("AGENTS.md", "CLAUDE.md", "GEMINI.md"):
        shutil.copy2(REPO_ROOT / root_file, dst_framework / root_file)
    gh_src = REPO_ROOT / ".github" / "copilot-instructions.md"
    (dst_framework / ".github").mkdir(parents=True, exist_ok=True)
    shutil.copy2(gh_src, dst_framework / ".github" / "copilot-instructions.md")
    return dst_framework


class TestM9ProjectionLifecycle(unittest.TestCase):
    """Comprehensive lifecycle tests isolated in TemporaryDirectory fixtures."""

    def test_lt01_clean_bootstrap_native_projections_and_exclusions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "clean-app"
            target.mkdir()
            (target / "README.md").write_text("# App Owned\n", encoding="utf-8")

            summary = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "claude-code"],
                optional_packs=["communication"],
            )
            self.assertGreater(len(summary["created"]), 20)
            self.assertEqual((target / "README.md").read_text(encoding="utf-8"), "# App Owned\n")

            # 13 installed skills (8 core + 5 communication) projected to both roots
            for sk in ("grill-me", "tdd-cycle", "find-skills", "graphify", "caveman", "rtk-cli"):
                self.assertTrue((target / ".agents" / "skills" / sk / "SKILL.md").exists())
                self.assertTrue((target / ".claude" / "skills" / sk / "SKILL.md").exists())

            # Unselected optional skills and UPSTREAM_SKILL.md must not appear in projections
            self.assertFalse((target / ".agents" / "skills" / "seo-audit").exists())
            self.assertFalse((target / ".agents" / "skills" / "graphify" / "UPSTREAM_SKILL.md").exists())
            self.assertFalse((target / ".claude" / "skills" / "caveman" / "UPSTREAM_SKILL.md").exists())
            # No duplicate UPSTREAM_SKILL.md or skills/core copies duplicated inside .aief/skills/
            self.assertFalse((target / ".aief" / "skills" / "core").exists())
            self.assertTrue((target / ".aief" / "skills" / "registry.json").exists())

            lock = json.loads((target / ".aief" / "lock.json").read_text(encoding="utf-8"))
            self.assertEqual(lock["schema_version"], "2.0.0")
            self.assertEqual(lock["projection_state"]["status"], "completed")
            self.assertEqual(lock["projection_state"]["pending_entries"], {})
            self.assertEqual(lock["projection_state"]["last_successful_projection"]["projected_skill_count"], 13)

            passed, report = validate.run_validation(target, mode="consumer")
            self.assertTrue(passed, f"LT-01 consumer validation failed: {report}")

    def test_lt02_repeated_bootstrap_zero_unnecessary_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "idempotent-app"
            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "codex", "claude-code"],
                optional_packs=["communication"],
            )

            lock_path = target / ".aief" / "lock.json"
            sample_proj = target / ".agents" / "skills" / "grill-me" / "SKILL.md"
            before_lock_bytes = lock_path.read_bytes()
            before_lock_mtime = lock_path.stat().st_mtime_ns
            before_proj_mtime = sample_proj.stat().st_mtime_ns

            second = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "codex", "claude-code"],
                optional_packs=["communication"],
                update_mode=True,
            )
            self.assertEqual(second["created"], [])
            self.assertEqual(second["updated"], [])
            self.assertEqual(second["pruned"], [])
            self.assertEqual(second["skipped_modified"], [])
            self.assertEqual(lock_path.read_bytes(), before_lock_bytes)
            self.assertEqual(lock_path.stat().st_mtime_ns, before_lock_mtime)
            self.assertEqual(sample_proj.stat().st_mtime_ns, before_proj_mtime)

    def test_lt03_upstream_skill_modification_updates_unmodified_projections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mock_fw = _copy_mock_framework(Path(tmp) / "mock-framework")
            target = Path(tmp) / "consumer-app"

            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "claude-code"],
                optional_packs=[],
                framework_root=mock_fw,
            )

            upstream_skill = mock_fw / "skills" / "core" / "grill-me" / "SKILL.md"
            updated_text = upstream_skill.read_text(encoding="utf-8") + "\n<!-- M9 UPSTREAM UPDATE -->\n"
            upstream_skill.write_text(updated_text, encoding="utf-8", newline="\n")

            res = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "claude-code"],
                optional_packs=[],
                update_mode=True,
                framework_root=mock_fw,
            )
            self.assertIn(".agents/skills/grill-me/SKILL.md", res["updated"])
            self.assertIn(".claude/skills/grill-me/SKILL.md", res["updated"])
            self.assertIn("<!-- M9 UPSTREAM UPDATE -->", (target / ".agents" / "skills" / "grill-me" / "SKILL.md").read_text(encoding="utf-8"))

            passed, report = validate.run_validation(target, mode="consumer")
            self.assertTrue(passed, f"LT-03 validation failed: {report}")

    def test_lt04_consumer_modification_preserved_with_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mock_fw = _copy_mock_framework(Path(tmp) / "mock-framework")
            target = Path(tmp) / "consumer-custom"

            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "claude-code"],
                optional_packs=[],
                framework_root=mock_fw,
            )

            custom_proj = target / ".agents" / "skills" / "grill-me" / "SKILL.md"
            custom_content = custom_proj.read_text(encoding="utf-8") + "\n# User Custom Note\n"
            custom_proj.write_text(custom_content, encoding="utf-8")

            # Change upstream to trigger update conflict on .agents copy while updating .claude copy
            upstream_skill = mock_fw / "skills" / "core" / "grill-me" / "SKILL.md"
            upstream_skill.write_text(
                upstream_skill.read_text(encoding="utf-8") + "\n<!-- NEW UPSTREAM -->\n",
                encoding="utf-8",
            )

            res = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "claude-code"],
                optional_packs=[],
                update_mode=True,
                framework_root=mock_fw,
            )
            self.assertIn(".agents/skills/grill-me/SKILL.md", res["skipped_modified"])
            self.assertIn(".agents/skills/grill-me/SKILL.md", res["conflicts_preserved"])
            self.assertIn(".claude/skills/grill-me/SKILL.md", res["updated"])
            self.assertEqual(custom_proj.read_text(encoding="utf-8"), custom_content)

            passed, report, warnings = validate.run_validation_with_warnings(target, mode="consumer")
            self.assertTrue(passed, f"Expected pass with warning, got errors: {report}")
            self.assertTrue(any(".agents/skills/grill-me/SKILL.md" in w for w in warnings))

    def test_lt05_skill_removal_prunes_unmodified_and_preserves_customized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "pack-prune"
            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "claude-code"],
                optional_packs=["communication"],
            )

            # Customize caveman in .agents/skills while leaving rtk-cli unmodified
            custom_caveman = target / ".agents" / "skills" / "caveman" / "SKILL.md"
            custom_caveman.write_text("# Custom Caveman Override\n", encoding="utf-8")

            res = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "claude-code"],
                optional_packs=[],
                update_mode=True,
            )
            # Unmodified rtk-cli and .claude caveman pruned cleanly
            self.assertIn(".agents/skills/rtk-cli/SKILL.md", res["pruned"])
            self.assertIn(".claude/skills/rtk-cli/SKILL.md", res["pruned"])
            self.assertIn(".claude/skills/caveman/SKILL.md", res["pruned"])
            self.assertFalse((target / ".agents" / "skills" / "rtk-cli").exists())
            self.assertFalse((target / ".claude" / "skills" / "caveman").exists())

            # Customized file preserved on disk and reported
            self.assertTrue(custom_caveman.exists())
            self.assertEqual(custom_caveman.read_text(encoding="utf-8"), "# Custom Caveman Override\n")
            self.assertIn(".agents/skills/caveman/SKILL.md", res["conflicts_preserved"])

            passed, report, warnings = validate.run_validation_with_warnings(target, mode="consumer")
            self.assertTrue(passed, f"Validation failed with conflict preserved: {report}")
            self.assertTrue(any("caveman/SKILL.md" in w for w in warnings))

    def test_lt06_platform_removal_removes_exclusive_claude_keeps_codex_shared(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "platform-remove"
            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["claude-code", "codex"],
                optional_packs=["communication"],
            )
            self.assertTrue((target / ".claude" / "skills" / "grill-me" / "SKILL.md").exists())
            self.assertTrue((target / ".agents" / "skills" / "grill-me" / "SKILL.md").exists())
            self.assertTrue((target / ".codex" / "config.toml").exists())

            res = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["codex"],
                optional_packs=["communication"],
                update_mode=True,
            )
            self.assertFalse((target / ".claude" / "skills").exists())
            self.assertFalse((target / ".claude" / "commands" / "grill-me.md").exists())
            self.assertTrue((target / ".agents" / "skills" / "grill-me" / "SKILL.md").exists())
            self.assertTrue((target / ".codex" / "config.toml").exists())
            self.assertIn(".claude/skills/grill-me/SKILL.md", res["pruned"])

            passed, report = validate.run_validation(target, mode="consumer")
            self.assertTrue(passed, f"LT-06 validation failed: {report}")

    def test_lt07_unknown_file_retained_and_flagged_by_validator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "unknown-file"
            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity"],
                optional_packs=[],
            )
            rogue_dir = target / ".agents" / "skills" / "my-local-skill"
            rogue_dir.mkdir(parents=True)
            rogue_file = rogue_dir / "SKILL.md"
            rogue_file.write_text("# Local Private Skill\n", encoding="utf-8")

            custom_note = target / ".agents" / "skills" / "grill-me" / "custom-notes.md"
            custom_note.write_text("My local notes\n", encoding="utf-8")

            res = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity"],
                optional_packs=[],
                update_mode=True,
            )
            self.assertTrue(rogue_file.exists())
            self.assertTrue(custom_note.exists())
            self.assertEqual(res["pruned"], [])

            passed, report, warnings = validate.run_validation_with_warnings(target, mode="consumer")
            self.assertTrue(passed, f"Untracked user files should warn rather than hard-fail: {report}")
            self.assertTrue(any("my-local-skill/SKILL.md" in w for w in warnings), warnings)
            self.assertTrue(any("grill-me/custom-notes.md" in w for w in warnings), warnings)

    def test_lt08_interrupted_bootstrap_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "interrupted-app"
            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity"],
                optional_packs=[],
            )
            # Simulate interrupted expansion to claude-code: half-written file + in_progress lockfile
            claude_skill = target / ".claude" / "skills" / "grill-me" / "SKILL.md"
            claude_skill.parent.mkdir(parents=True, exist_ok=True)
            expected_bytes = (target / ".agents" / "skills" / "grill-me" / "SKILL.md").read_bytes()
            claude_skill.write_bytes(expected_bytes)
            expected_hash = bootstrap.sha256_bytes(expected_bytes)

            lock_path = target / ".aief" / "lock.json"
            lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
            lock_data["projection_state"]["status"] = "in_progress"
            lock_data["projection_state"]["pending_entries"] = {
                ".claude/skills/grill-me/SKILL.md": {
                    "ownership": "platform_projected_skill",
                    "skill": "grill-me",
                    "source": ".aief/skills/core/grill-me/SKILL.md",
                    "sha256": expected_hash,
                    "platforms": ["claude-code"],
                }
            }
            lock_path.write_text(json.dumps(lock_data, indent=2), encoding="utf-8")

            # Validator must reject in_progress interrupted state
            passed_before, report_before = validate.run_validation(target, mode="consumer")
            self.assertFalse(passed_before)
            self.assertTrue(any("in_progress" in e for e in report_before["consumer_state"]))

            # Subsequent run recovers without falsely marking .claude/skills/grill-me as unknown/conflict
            res = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "claude-code"],
                optional_packs=[],
                update_mode=True,
            )
            self.assertIn(".claude/skills/grill-me/SKILL.md", res["recovered"])
            self.assertEqual(res["unknown_preserved"], [])
            self.assertEqual(res["conflicts_preserved"], [])

            passed_after, report_after = validate.run_validation(target, mode="consumer")
            self.assertTrue(passed_after, f"Recovery failed consumer validation: {report_after}")

    def test_lt09_corrupted_lockfile_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "corrupt-lock"
            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity"],
                optional_packs=[],
            )
            sentinel = target / ".agents" / "skills" / "grill-me" / "SKILL.md"
            before_bytes = sentinel.read_bytes()
            lock_path = target / ".aief" / "lock.json"
            lock_path.write_text("{truncated-json", encoding="utf-8")

            with self.assertRaises(bootstrap.LockfileError):
                bootstrap.bootstrap_project(
                    target_dir=target,
                    platforms=["antigravity"],
                    optional_packs=[],
                    update_mode=True,
                )
            self.assertEqual(lock_path.read_text(encoding="utf-8"), "{truncated-json")
            self.assertEqual(sentinel.read_bytes(), before_bytes)

            # Unsupported schema version also fails closed
            lock_path.write_text(json.dumps({"schema_version": "99.0.0"}), encoding="utf-8")
            with self.assertRaises(bootstrap.LockfileError):
                bootstrap.bootstrap_project(target_dir=target, platforms=["antigravity"], optional_packs=[], update_mode=True)

    def test_lt10_path_traversal_and_symlink_reparse_protection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "safe-root"
            target.mkdir()
            outside = Path(tmp) / "outside-secret.txt"
            outside.write_text("DO_NOT_DELETE", encoding="utf-8")

            with self.assertRaises(bootstrap.BootstrapSecurityError):
                bootstrap.assert_safe_target_path(target, "../../outside-secret.txt")
            with self.assertRaises(bootstrap.BootstrapSecurityError):
                bootstrap.assert_safe_target_path(target, "/etc/passwd")
            with self.assertRaises(bootstrap.BootstrapSecurityError):
                bootstrap.assert_safe_target_path(target, "C:/Windows/win.ini")

            # Simulated or OS symlink/reparse point blocked on write/prune check
            link_candidate = target / ".agents" / "skills" / "evil" / "SKILL.md"
            link_candidate.parent.mkdir(parents=True)
            with mock.patch.object(bootstrap, "_is_reparse_or_symlink", return_value=True):
                with self.assertRaises(bootstrap.BootstrapSecurityError):
                    bootstrap.assert_safe_target_path(target, ".agents/skills/evil/SKILL.md")
            self.assertEqual(outside.read_text(encoding="utf-8"), "DO_NOT_DELETE")

            # Windows NTFS junction integration test when mklink /J is permitted
            if sys.platform == "win32":
                junction_dst = target / ".agents" / "skills" / "junc-target"
                outside_dir = Path(tmp) / "outside-dir"
                outside_dir.mkdir()
                (outside_dir / "keep.txt").write_text("keep", encoding="utf-8")
                proc = subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(junction_dst), str(outside_dir)],
                    capture_output=True,
                    text=True,
                )
                if proc.returncode == 0:
                    with self.assertRaises(bootstrap.BootstrapSecurityError):
                        bootstrap.assert_safe_target_path(target, ".agents/skills/junc-target/keep.txt")
                    self.assertTrue((outside_dir / "keep.txt").exists())

    def test_lt11_windows_case_collision_rejected(self) -> None:
        with self.assertRaises(bootstrap.BootstrapSecurityError) as ctx:
            bootstrap.check_case_collisions(
                [".agents/skills/MySkill/SKILL.md", ".agents/skills/myskill/SKILL.md"]
            )
        self.assertIn("Case-insensitive path collision", str(ctx.exception))

    def test_lt12_shared_projection_ownership_across_four_platforms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "shared-proj"
            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "copilot", "codex", "gemini-cli", "claude-code"],
                optional_packs=[],
            )
            shared_skill = target / ".agents" / "skills" / "grill-me" / "SKILL.md"
            claude_skill = target / ".claude" / "skills" / "grill-me" / "SKILL.md"
            self.assertTrue(shared_skill.exists())
            self.assertTrue(claude_skill.exists())

            # Remove codex + gemini-cli -> antigravity & copilot still keep .agents/skills intact
            res1 = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "copilot", "claude-code"],
                optional_packs=[],
                update_mode=True,
            )
            self.assertTrue(shared_skill.exists())
            self.assertNotIn(".agents/skills/grill-me/SKILL.md", res1["pruned"])
            lock1 = json.loads((target / ".aief" / "lock.json").read_text(encoding="utf-8"))
            self.assertEqual(lock1["managed_files"][".agents/skills/grill-me/SKILL.md"]["platforms"], ["antigravity", "copilot"])

            # Remove copilot -> antigravity keeps .agents/skills intact
            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "claude-code"],
                optional_packs=[],
                update_mode=True,
            )
            self.assertTrue(shared_skill.exists())

            # Remove last .agents/skills owner (antigravity) -> .agents/skills pruned, .claude/skills intact
            res3 = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["claude-code"],
                optional_packs=[],
                update_mode=True,
            )
            self.assertFalse(shared_skill.exists())
            self.assertTrue(claude_skill.exists())
            self.assertIn(".agents/skills/grill-me/SKILL.md", res3["pruned"])

            passed, report = validate.run_validation(target, mode="consumer")
            self.assertTrue(passed, f"LT-12 final validation failed: {report}")

    def test_m9_lockfile_v030_migration_backup_and_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "legacy-v030"
            target.mkdir(parents=True, exist_ok=True)
            # Pre-seed valid legacy project.framework.json so layout auto-detects as legacy v0.3.x root install
            legacy_cfg = json.loads((REPO_ROOT / "templates" / "project.framework.json").read_text(encoding="utf-8"))
            legacy_cfg["frameworkVersion"] = "0.3.0"
            legacy_cfg["projectName"] = "legacy-v030"
            legacy_cfg["enabledPlatforms"] = ["antigravity", "claude-code"]
            legacy_cfg["paths"]["stateDir"] = ".framework-state"
            legacy_cfg["customizations"]["overlayDir"] = ".framework-custom"
            (target / "project.framework.json").write_text(json.dumps(legacy_cfg, indent=2), encoding="utf-8")
            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "claude-code"],
                optional_packs=["communication"],
            )
            # Downgrade lockfile to synthetic v0.3.0 flat shape and remove .agents/skills/ + .claude/skills/
            shutil.rmtree(target / ".agents" / "skills")
            shutil.rmtree(target / ".claude" / "skills")
            v2_lock = json.loads((target / ".framework-lock.json").read_text(encoding="utf-8"))
            flat_managed = {
                k: v["sha256"]
                for k, v in v2_lock["managed_files"].items()
                if not k.startswith((".agents/skills/", ".claude/skills/"))
            }
            # Customize AGENTS.md locally to ensure migration preserves it cleanly
            (target / "AGENTS.md").write_text("# Legacy Custom AGENTS.md\n", encoding="utf-8")

            legacy_lock = {
                "framework_version": "0.3.0",
                "platforms": ["antigravity", "claude-code"],
                "optional_packs": ["communication"],
                "stacks": [],
                "managed_files": flat_managed,
            }
            (target / ".framework-lock.json").write_text(json.dumps(legacy_lock, indent=2), encoding="utf-8")

            # Legacy validation exits pass with deprecation warning
            passed_old, report_old, warnings_old = validate.run_validation_with_warnings(target, mode="consumer")
            self.assertTrue(passed_old, report_old)
            self.assertTrue(any("Legacy v0.3.0" in w for w in warnings_old))

            # Migrate via --update
            res = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "claude-code"],
                optional_packs=["communication"],
                update_mode=True,
            )
            self.assertEqual(res["migrated_from"], "0.3.0")
            self.assertTrue(
                (target / ".framework-state" / "lock-backups" / "framework-lock-v0.3.0.json").exists()
            )
            self.assertEqual((target / "AGENTS.md").read_text(encoding="utf-8"), "# Legacy Custom AGENTS.md\n")
            self.assertTrue((target / ".agents" / "skills" / "grill-me" / "SKILL.md").exists())
            self.assertTrue((target / ".claude" / "skills" / "grill-me" / "SKILL.md").exists())

            passed_new, report_new, warnings_new = validate.run_validation_with_warnings(target, mode="consumer")
            self.assertTrue(passed_new, f"Post-migration validation failed: {report_new}")
            self.assertTrue(any("AGENTS.md" in w for w in warnings_new))

            # Ambiguous/invalid legacy hash triggers fail-closed LockfileError
            bad_target = Path(tmp) / "bad-legacy"
            bad_target.mkdir()
            (bad_target / ".framework-lock.json").write_text(
                json.dumps({
                    "framework_version": "0.3.0",
                    "platforms": ["antigravity"],
                    "managed_files": {"AGENTS.md": "not-a-sha256"},
                }),
                encoding="utf-8",
            )
            with self.assertRaises(bootstrap.LockfileError):
                bootstrap.bootstrap_project(target_dir=bad_target, platforms=["antigravity"], optional_packs=[], update_mode=True)

    def test_m9_markdown_link_rewriting_find_skills_and_multi_file_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "assets-links"
            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "claude-code"],
                optional_packs=["frontend-design"],
            )

            # find-skills relative ../../registry.json must become ../../../.aief/skills/registry.json
            fs_agents = (target / ".agents" / "skills" / "find-skills" / "SKILL.md").read_text(encoding="utf-8")
            fs_claude = (target / ".claude" / "skills" / "find-skills" / "SKILL.md").read_text(encoding="utf-8")
            self.assertNotIn("(../../registry.json)", fs_agents)
            self.assertIn("(../../../.aief/skills/registry.json)", fs_agents)
            self.assertIn("(../../../.aief/skills/registry.json)", fs_claude)
            # Canonical source untouched
            self.assertIn("(../../registry.json)", (REPO_ROOT / "skills" / "core" / "find-skills" / "SKILL.md").read_text(encoding="utf-8"))

            # Multi-file skill assets projected & runnable offline
            proj_search = target / ".agents" / "skills" / "ui-ux-pro-max" / "scripts" / "search.py"
            self.assertTrue(proj_search.exists())
            self.assertTrue((target / ".claude" / "skills" / "ui-ux-pro-max" / "data" / "stacks" / "angular.csv").exists())
            self.assertTrue((target / ".agents" / "skills" / "angular-developer" / "references" / "cli.md").exists())

            out = subprocess.check_output(
                [sys.executable, str(proj_search), "signals standalone", "--stack", "angular", "--max-results", "1"],
                cwd=target,
                text=True,
                encoding="utf-8",
            )
            self.assertIn("stacks/angular.csv", out)

            # claude-code omitted -> .claude/skills must NOT exist
            no_claude = Path(tmp) / "no-claude"
            bootstrap.bootstrap_project(target_dir=no_claude, platforms=["codex"], optional_packs=[])
            self.assertFalse((no_claude / ".claude" / "skills").exists())
            self.assertTrue((no_claude / ".agents" / "skills" / "find-skills" / "SKILL.md").exists())

    def test_m9_consumer_safe_adapters_and_validation_error_separation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "all-platforms"
            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "copilot", "claude-code", "codex", "gemini-cli"],
                optional_packs=["communication"],
            )
            passed, report = validate.run_validation(target, mode="consumer")
            self.assertTrue(passed, f"All-platform consumer failed validation: {report}")

            # Verify banned upstream-only tokens absent in all consumer adapters
            for rel in (
                "CLAUDE.md",
                "GEMINI.md",
                ".github/copilot-instructions.md",
                ".github/instructions/framework.instructions.md",
                ".agents/rules/framework-core.md",
                ".claude/settings.json",
                ".claude/commands/validate-framework.md",
                ".gemini/commands/workflow.toml",
            ):
                txt = (target / Path(rel)).read_text(encoding="utf-8")
                for token in validate.BANNED_CONSUMER_UPSTREAM_TOKENS:
                    self.assertNotIn(token, txt, f"{rel} leaked upstream token {token}")

            # Stale projected skill in registry check fails cleanly
            claude_md = target / ".claude" / "skills" / "grill-me" / "SKILL.md"
            claude_md.unlink()
            passed_miss, rep_miss = validate.run_validation(target, mode="consumer")
            self.assertFalse(passed_miss)
            self.assertTrue(any("grill-me/SKILL.md" in e for e in rep_miss["consumer_state"]))

    def test_m9_bootstrap_pack_and_platform_matrix(self) -> None:
        pack_cases = [
            ("empty-core", [], 8),
            ("none-core", ["none"], 8),
            ("only-communication", ["communication"], 13),
            ("only-context-engineering", ["context-engineering"], 13),
            ("only-agent-architecture", ["agent-architecture"], 12),
            ("only-frontend-design", ["frontend-design"], 14),
            ("only-design-ui-alias", ["design-ui"], 14),
            ("only-growth-media", ["growth-media"], 15),
            ("only-backend-dotnet", ["backend-dotnet"], 10),
            ("only-dotnet-alias", ["dotnet"], 10),
            ("multi-comm-growth", ["communication", "growth-media"], 20),
            ("multi-ctx-arch", ["context-engineering", "agent-architecture"], 17),
            ("all-packs", ["all"], 37),
        ]
        for label, packs, expected_count in pack_cases:
            with self.subTest(pack_matrix=label):
                with tempfile.TemporaryDirectory() as tmp:
                    target = Path(tmp) / label
                    bootstrap.bootstrap_project(
                        target_dir=target,
                        platforms=["antigravity", "claude-code"],
                        optional_packs=packs,
                    )
                    reg = json.loads((target / ".aief" / "skills" / "registry.json").read_text(encoding="utf-8"))
                    self.assertEqual(reg["total_skills"], expected_count)
                    agents_proj = {p.name for p in (target / ".agents" / "skills").iterdir() if p.is_dir()}
                    claude_proj = {p.name for p in (target / ".claude" / "skills").iterdir() if p.is_dir()}
                    expected_names = {s["name"] for s in reg["skills"]}
                    self.assertEqual(agents_proj, expected_names)
                    self.assertEqual(claude_proj, expected_names)
                    passed, report = validate.run_validation(target, mode="consumer")
                    self.assertTrue(passed, f"{label} validation failed: {report}")

        platform_cases = [
            ("antigravity-only", ["antigravity"], True, False),
            ("claude-only", ["claude-code"], False, True),
            ("copilot-only", ["copilot"], True, False),
            ("codex-only", ["codex"], True, False),
            ("gemini-only", ["gemini-cli"], True, False),
            ("shared-agents-no-claude", ["antigravity", "copilot", "codex", "gemini-cli"], True, False),
            ("all-five-platforms", ["antigravity", "copilot", "claude-code", "codex", "gemini-cli"], True, True),
        ]
        for label, plats, expect_agents, expect_claude in platform_cases:
            with self.subTest(platform_matrix=label):
                with tempfile.TemporaryDirectory() as tmp:
                    target = Path(tmp) / label
                    bootstrap.bootstrap_project(
                        target_dir=target,
                        platforms=plats,
                        optional_packs=["communication"],
                    )
                    self.assertEqual((target / ".agents" / "skills").exists(), expect_agents)
                    self.assertEqual((target / ".claude" / "skills").exists(), expect_claude)
                    passed, report = validate.run_validation(target, mode="consumer")
                    self.assertTrue(passed, f"{label} validation failed: {report}")

    def test_m9_v2_lockfile_pack_expansion_update(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "v2-expand"
            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["codex"],
                optional_packs=[],
            )
            spec_note = target / "docs" / "specs" / "01-spec.md"
            spec_note.parent.mkdir(parents=True, exist_ok=True)
            spec_note.write_text("# Consumer Owned Spec\n", encoding="utf-8")

            res = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["codex", "claude-code"],
                optional_packs=["communication"],
                update_mode=True,
            )
            self.assertIn(".claude/skills/caveman/SKILL.md", res["created"])
            self.assertIn(".agents/skills/caveman/SKILL.md", res["created"])
            self.assertEqual(spec_note.read_text(encoding="utf-8"), "# Consumer Owned Spec\n")

            lock = json.loads((target / ".aief" / "lock.json").read_text(encoding="utf-8"))
            self.assertEqual(lock["schema_version"], "2.0.0")
            self.assertEqual(lock["enabled_platforms"], ["claude-code", "codex"])
            self.assertEqual(lock["projection_state"]["last_successful_projection"]["projected_skill_count"], 13)
            passed, report = validate.run_validation(target, mode="consumer")
            self.assertTrue(passed, report)

    def test_m9_reparse_prune_and_plan_case_collision_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "reparse-prune"
            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity"],
                optional_packs=["communication"],
            )
            # Pruning optional pack when _is_reparse_or_symlink reports True on target path must fail closed
            real_is_reparse = bootstrap._is_reparse_or_symlink

            def _flag_caveman(path: Path) -> bool:
                if path.name == "caveman" or path.parent.name == "caveman":
                    return True
                return real_is_reparse(path)

            with mock.patch.object(bootstrap, "_is_reparse_or_symlink", side_effect=_flag_caveman):
                with self.assertRaises(bootstrap.BootstrapSecurityError):
                    bootstrap.bootstrap_project(
                        target_dir=target,
                        platforms=["antigravity"],
                        optional_packs=[],
                        update_mode=True,
                    )

            # End-to-end case-insensitive cross-pack skill collision rejected before consumer writes
            mock_fw = _copy_mock_framework(Path(tmp) / "collide-fw")
            dup_skill_dir = mock_fw / "skills" / "optional" / "communication" / "Grill-Me"
            dup_skill_dir.mkdir(parents=True)
            (dup_skill_dir / "SKILL.md").write_text("# Duplicate case\n", encoding="utf-8")

            reg_path = mock_fw / "skills" / "registry.json"
            reg_data = json.loads(reg_path.read_text(encoding="utf-8"))
            dup_entry = dict(reg_data["skills"][0])
            dup_entry["name"] = "Grill-Me"
            dup_entry["tier"] = "optional"
            dup_entry["path"] = "skills/optional/communication/Grill-Me/SKILL.md"
            reg_data["skills"].append(dup_entry)
            reg_data["total_skills"] = len(reg_data["skills"])
            reg_path.write_text(json.dumps(reg_data, indent=2), encoding="utf-8")

            collide_target = Path(tmp) / "collide-consumer"
            with self.assertRaises(bootstrap.BootstrapSecurityError):
                bootstrap.bootstrap_project(
                    target_dir=collide_target,
                    platforms=["antigravity"],
                    optional_packs=["communication"],
                    framework_root=mock_fw,
                )


if __name__ == "__main__":
    unittest.main()
