#!/usr/bin/env python3
"""M10 customizability, inline composition, feature toggles, brownfield import, and safety tests."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import bootstrap  # noqa: E402
import compose  # noqa: E402
import validate  # noqa: E402

ALL_PLATFORMS = ["antigravity", "copilot", "claude-code", "codex", "gemini-cli"]


class TestM10CustomComposition(unittest.TestCase):
    """Verify inline customization auto-loading across all 5 platforms, toggles, updates, and guards."""

    def test_01_inline_custom_instructions_and_rules_across_all_5_platforms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "app-inline"
            fake_home = root / "isolated-home"
            fake_home.mkdir()

            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=ALL_PLATFORMS,
                optional_packs=["communication"],
            )
            self.assertTrue((target / ".aief" / "scripts" / "compose.py").exists())
            self.assertTrue((target / ".aief" / "custom" / "instructions.md").exists())

            (target / ".aief" / "custom" / "instructions.md").write_text(
                "# Project Custom Rules\n- USE STRICT POSTGRESQL MIGRATIONS.\n",
                encoding="utf-8",
            )
            rules_dir = target / ".aief" / "custom" / "rules"
            rules_dir.mkdir(parents=True, exist_ok=True)
            (rules_dir / "api-style.md").write_text(
                "- ALL ENDPOINTS MUST VALIDATE JWT CLAIMS.\n",
                encoding="utf-8",
            )

            proc = subprocess.run(
                [sys.executable, str(target / ".aief" / "scripts" / "compose.py")],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)

            # Full inline rules live in AGENTS.md and CLAUDE.md (Antigravity/Gemini/Copilot point to AGENTS.md without 3x duplication)
            for rel in ("AGENTS.md", "CLAUDE.md"):
                content = (target / Path(rel)).read_text(encoding="utf-8")
                self.assertIn("USE STRICT POSTGRESQL MIGRATIONS", content, f"Missing inline custom in {rel}")
                self.assertIn("ALL ENDPOINTS MUST VALIDATE JWT CLAIMS", content, f"Missing inline rule in {rel}")
                self.assertIn("HARD GATE", content, f"Missing subagent HARD GATE in {rel}")
                self.assertIn("conversationId", content, f"Missing conversationId audit rule in {rel}")
            for thin_rel in (
                "GEMINI.md",
                ".agents/rules/framework-core.md",
                ".github/copilot-instructions.md",
                ".github/instructions/framework.instructions.md",
            ):
                thin_txt = (target / Path(thin_rel)).read_text(encoding="utf-8")
                self.assertIn("AGENTS.md", thin_txt, f"Missing AGENTS.md pointer in {thin_rel}")
                self.assertNotIn("USE STRICT POSTGRESQL MIGRATIONS", thin_txt, f"Unexpected duplication in {thin_rel}")
            fw_rule_txt = (target / ".agents" / "rules" / "framework-core.md").read_text(encoding="utf-8")
            self.assertIn("code-reviewer", fw_rule_txt)
            self.assertIn("conversationId", fw_rule_txt)

            passed, report, warnings, _ = validate.run_validation_full(
                target, mode="consumer", home_dir=fake_home
            )
            self.assertTrue(passed, report)
            self.assertEqual(warnings, [])

    def test_02_custom_skill_projected_with_zero_warnings_and_lock_tracking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "app-custom-skill"
            fake_home = root / "isolated-home"
            fake_home.mkdir()

            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "claude-code"],
                optional_packs=[],
            )
            cskill_dir = target / ".aief" / "custom" / "skills" / "billing-invariants"
            cskill_dir.mkdir(parents=True, exist_ok=True)
            (cskill_dir / "SKILL.md").write_text(
                "---\nname: billing-invariants\ndescription: Domain ledger invariants\n---\n\n# Billing Invariants\nNever store floats for money.\n",
                encoding="utf-8",
            )
            (cskill_dir / "checklist.md").write_text("- Always use Decimal cents.\n", encoding="utf-8")

            summary = compose.compose_consumer(target)
            self.assertEqual(summary["custom_skills"], ["billing-invariants"])
            self.assertTrue((target / ".agents" / "skills" / "billing-invariants" / "SKILL.md").exists())
            self.assertTrue((target / ".agents" / "skills" / "billing-invariants" / "checklist.md").exists())
            self.assertTrue((target / ".claude" / "skills" / "billing-invariants" / "SKILL.md").exists())

            lock = json.loads((target / ".aief" / "lock.json").read_text(encoding="utf-8"))
            self.assertIn("billing-invariants", lock["projected_skills"]["antigravity"]["skills"])
            self.assertEqual(
                lock["managed_files"][".agents/skills/billing-invariants/SKILL.md"]["ownership"],
                "consumer_custom_skill",
            )
            self.assertIn("billing-invariants", (target / "AGENTS.md").read_text(encoding="utf-8"))

            passed, report, warnings, _ = validate.run_validation_full(
                target, mode="consumer", home_dir=fake_home
            )
            self.assertTrue(passed, report)
            self.assertEqual(warnings, [])

    def test_03_custom_agent_append_override_and_readonly_reviewer_enforcement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "app-custom-agent"
            fake_home = root / "isolated-home"
            fake_home.mkdir()

            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["claude-code", "copilot"],
                optional_packs=[],
            )
            cagents = target / ".aief" / "custom" / "agents"
            cagents.mkdir(parents=True, exist_ok=True)
            (cagents / "implementation-engineer.append.md").write_text(
                "- Always verify database migrations roll back cleanly.",
                encoding="utf-8",
            )
            (cagents / "code-reviewer.append.md").write_text(
                "- Reject endpoints missing idempotency keys.",
                encoding="utf-8",
            )
            (cagents / "db-migrator.md").write_text(
                "---\nname: db-migrator\ntitle: DB Migrator\ndescription: Schema migration specialist\n"
                "phases: [9]\nallowed_tools: [read_file, write_file, run_command]\n---\n\nRun safe migrations only.\n",
                encoding="utf-8",
            )
            (cagents / "sql-reviewer.md").write_text(
                "---\nname: sql-reviewer\ntitle: SQL Reviewer\ndescription: Read-only SQL reviewer\n"
                "phases: [10]\nallowed_tools: [read_file, write_file]\n---\n\nInspect SQL queries read-only.\n",
                encoding="utf-8",
            )

            compose.compose_consumer(target)
            # Second consecutive compose must be strictly idempotent without duplicating appended blocks
            second_summary = compose.compose_consumer(target)
            self.assertEqual(second_summary["updated"], [], second_summary)

            impl_md = (target / ".aief" / "agents" / "implementation-engineer.md").read_text(encoding="utf-8")
            self.assertIn("Always verify database migrations roll back cleanly", impl_md)
            self.assertEqual(impl_md.count("## Project-Specific Rules (implementation-engineer)"), 1)

            claude_rev = (target / ".claude" / "agents" / "framework-code-reviewer.md").read_text(encoding="utf-8")
            self.assertIn("Reject endpoints missing idempotency keys", claude_rev)

            claude_db = (target / ".claude" / "agents" / "db-migrator.md").read_text(encoding="utf-8")
            self.assertIn("Read, Glob, Grep, Write, Bash", claude_db)

            copilot_db = (target / ".github" / "agents" / "db-migrator.agent.md").read_text(encoding="utf-8")
            self.assertIn('["read", "search", "edit", "terminal"]', copilot_db)

            # Reviewer custom agents must remain strictly read-only in generated Claude/Copilot configs
            sql_rev_claude = (target / ".claude" / "agents" / "sql-reviewer.md").read_text(encoding="utf-8")
            self.assertIn("tools: Read, Glob, Grep", sql_rev_claude)
            self.assertIn("disallowedTools: Write, Edit, Bash", sql_rev_claude)

            passed, report, _, _ = validate.run_validation_full(
                target, mode="consumer", home_dir=fake_home
            )
            self.assertTrue(passed, report)

    def test_04_granular_disable_controls_and_re_enable_offline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "app-toggles"
            fake_home = root / "isolated-home"
            fake_home.mkdir()

            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=ALL_PLATFORMS,
                optional_packs=["communication"],
            )
            self.assertTrue((target / ".agents" / "skills" / "caveman" / "SKILL.md").exists())
            self.assertTrue((target / ".claude" / "agents" / "framework-code-reviewer.md").exists())

            cfg_path = target / ".aief" / "config.json"
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            cfg["disabled"] = {
                "skills": ["caveman"],
                "agents": ["code-reviewer"],
                "phases": [2, 3, 10],
                "gates": ["Gate-02"],
                "mechanisms": ["tdd", "handoffs"],
            }
            cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

            compose.compose_consumer(target)

            # Disabled skill pruned from projections while entry remains disabled in .aief/skills/registry.json for re-enable
            self.assertFalse((target / ".agents" / "skills" / "caveman").exists())
            self.assertFalse((target / ".claude" / "skills" / "caveman").exists())
            reg_disabled = json.loads((target / ".aief" / "skills" / "registry.json").read_text(encoding="utf-8"))
            cav_entries = [s for s in reg_disabled["skills"] if s["name"] == "caveman"]
            self.assertEqual(len(cav_entries), 1)
            self.assertIs(cav_entries[0].get("enabled"), False)

            # Disabled reviewer agent omitted from AGENTS.md and pruned from .claude/agents/, .github/agents/
            # while canonical source remains in .aief/agents/ for offline re-enabling and intact workflow links
            self.assertTrue((target / ".aief" / "agents" / "code-reviewer.md").exists())
            self.assertFalse((target / ".claude" / "agents" / "framework-code-reviewer.md").exists())
            self.assertFalse((target / ".github" / "agents" / "code-reviewer.agent.md").exists())

            agents_md = (target / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("TDD Requirement:** Disabled", agents_md)
            self.assertIn("Filesystem Handoffs:** Disabled", agents_md)
            self.assertIn("Independent Code Review:** Disabled", agents_md)
            self.assertNotIn("MUST run an independent `code-reviewer`", agents_md)
            self.assertNotIn("`Gate-02`", agents_md)
            self.assertNotIn("| `caveman` |", agents_md)
            self.assertNotIn("| `code-reviewer` |", agents_md)
            fw_rule_disabled = (target / ".agents" / "rules" / "framework-core.md").read_text(encoding="utf-8")
            self.assertIn("`code-reviewer` disabled", fw_rule_disabled)
            self.assertNotIn("run an independent `code-reviewer`", fw_rule_disabled)

            passed, report, _, _ = validate.run_validation_full(
                target, mode="consumer", home_dir=fake_home
            )
            self.assertTrue(passed, report)

            # Re-enable caveman and code-reviewer offline without needing upstream framework repo
            cfg["disabled"]["skills"] = []
            cfg["disabled"]["agents"] = []
            cfg["disabled"]["phases"] = []
            cfg["disabled"]["mechanisms"] = []
            cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
            compose.compose_consumer(target)
            self.assertTrue((target / ".agents" / "skills" / "caveman" / "SKILL.md").exists())
            self.assertTrue((target / ".claude" / "skills" / "caveman" / "SKILL.md").exists())
            self.assertTrue((target / ".claude" / "agents" / "framework-code-reviewer.md").exists())
            self.assertTrue((target / ".github" / "agents" / "code-reviewer.agent.md").exists())

    def test_05_framework_update_updates_core_and_recomposes_inline_customs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mock_fw = root / "mock-framework"
            for item in (
                "core",
                "agents",
                "workflows",
                "quality",
                "security",
                "templates",
                "scripts",
                "skills",
                "adapters",
            ):
                src = REPO_ROOT / item
                if src.exists():
                    shutil.copytree(src, mock_fw / item, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            for root_md in ("AGENTS.md", "CLAUDE.md", "GEMINI.md"):
                shutil.copy2(REPO_ROOT / root_md, mock_fw / root_md)
            (mock_fw / ".github").mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO_ROOT / ".github" / "copilot-instructions.md", mock_fw / ".github" / "copilot-instructions.md")

            target = root / "consumer-update"
            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "claude-code"],
                optional_packs=["communication"],
                framework_root=mock_fw,
            )

            # Customize overlay + disable caveman
            (target / ".aief" / "custom" / "instructions.md").write_text(
                "# My Rules\nCUSTOM KEEP ME ACROSS UPDATES\n", encoding="utf-8"
            )
            cfg_path = target / ".aief" / "config.json"
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            cfg["disabled"]["skills"] = ["caveman"]
            cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
            compose.compose_consumer(target)

            # Upstream releases a rule update
            ep_path = mock_fw / "core" / "rules" / "engineering-principles.md"
            ep_path.write_text(ep_path.read_text(encoding="utf-8") + "\n<!-- M10 RULE UPDATE -->\n", encoding="utf-8")

            res = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "claude-code"],
                optional_packs=["communication"],
                update_mode=True,
                framework_root=mock_fw,
            )
            self.assertIn(".aief/core/rules/engineering-principles.md", res["updated"])
            self.assertIn("AGENTS.md", res["updated"])
            self.assertIn("CLAUDE.md", res["updated"])
            self.assertIn("M10 RULE UPDATE", (target / ".aief" / "core" / "rules" / "engineering-principles.md").read_text(encoding="utf-8"))
            self.assertIn("CUSTOM KEEP ME ACROSS UPDATES", (target / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertIn("CUSTOM KEEP ME ACROSS UPDATES", (target / "CLAUDE.md").read_text(encoding="utf-8"))
            self.assertNotIn("CUSTOM KEEP ME ACROSS UPDATES", (target / ".agents" / "rules" / "framework-core.md").read_text(encoding="utf-8"))
            self.assertFalse((target / ".agents" / "skills" / "caveman").exists())

    def test_06_brownfield_auto_import_preserves_existing_instruction_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "brownfield-app"
            target.mkdir()
            (target / "CLAUDE.md").write_text(
                "# Legacy Repo Claude\nLegacy rule: always run cargo test.\n",
                encoding="utf-8",
            )
            gh = target / ".github"
            gh.mkdir()
            (gh / "copilot-instructions.md").write_text(
                "Copilot legacy rule: prefer snake_case functions.\n",
                encoding="utf-8",
            )
            fake_home = root / "isolated-home"
            fake_home.mkdir()

            res = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "copilot", "claude-code"],
                optional_packs=[],
            )
            self.assertIn(".aief/custom/imported/CLAUDE.md", res["imported"])
            self.assertIn(".aief/custom/imported/copilot-instructions.md", res["imported"])
            self.assertTrue((target / ".aief" / "custom" / "imported" / "CLAUDE.md").exists())
            self.assertTrue((target / ".aief" / "custom" / "imported" / "copilot-instructions.md").exists())

            for rel in ("CLAUDE.md", "AGENTS.md"):
                txt = (target / Path(rel)).read_text(encoding="utf-8")
                self.assertIn("always run cargo test", txt, rel)
                self.assertIn("prefer snake_case functions", txt, rel)

            passed, report, _, _ = validate.run_validation_full(
                target, mode="consumer", home_dir=fake_home
            )
            self.assertTrue(passed, report)

    def test_07_reference_mode_and_inline_byte_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "budget-app"
            bootstrap.bootstrap_project(target_dir=target, platforms=["claude-code"], optional_packs=[])

            (target / ".aief" / "custom" / "instructions.md").write_text(
                "LINE\n" * 600, encoding="utf-8"
            )
            cfg_path = target / ".aief" / "config.json"
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            cfg["customizations"]["inlineMaxBytes"] = 1024
            cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

            compose.compose_consumer(target)
            claude_txt = (target / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertIn("Inline budget `1024` bytes reached", claude_txt)

            cfg["customizations"]["promptInjectionMode"] = "reference"
            cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
            compose.compose_consumer(target)
            claude_ref = (target / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertIn("Read `.aief/custom/instructions.md` before executing project changes", claude_ref)
            self.assertNotIn("Inline budget", claude_ref)

    def test_08_security_guards_reject_overlay_traversal_and_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "sec-app"
            bootstrap.bootstrap_project(target_dir=target, platforms=["antigravity"], optional_packs=[])

            cfg_path = target / ".aief" / "config.json"
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            cfg["customizations"]["overlayDir"] = "../escape"
            cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

            with self.assertRaises(compose.BootstrapSecurityError):
                compose.compose_consumer(target)

            passed, report = validate.run_validation(target, mode="consumer")
            self.assertFalse(passed)
            self.assertTrue(report["consumer_state"])

            # Restore valid overlayDir and simulate symlink/reparse point inside .aief/custom/
            cfg["customizations"]["overlayDir"] = ".aief/custom"
            cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
            bad_rule_dir = target / ".aief" / "custom" / "rules"
            bad_rule_dir.mkdir(parents=True, exist_ok=True)
            bad_rule = bad_rule_dir / "linked.md"
            bad_rule.write_text("bad", encoding="utf-8")

            with mock.patch.object(compose, "is_reparse_or_symlink", side_effect=lambda p: Path(p).name == "linked.md"):
                with self.assertRaises(compose.BootstrapSecurityError):
                    compose.compose_consumer(target)

            with mock.patch.object(bootstrap, "_is_reparse_or_symlink", side_effect=lambda p: Path(p).name == "linked.md"):
                with self.assertRaises(bootstrap.BootstrapSecurityError):
                    bootstrap.bootstrap_project(target_dir=target, platforms=["antigravity"], update_mode=True)

    def test_09_zero_flag_cli_bootstrap_all_packs_autodetect_and_one_cmd_compose(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "auto-app"
            target.mkdir()
            (target / "MyApp.csproj").write_text("<Project Sdk=\"Microsoft.NET.Sdk\"></Project>\n", encoding="utf-8")
            (target / "pyproject.toml").write_text("[project]\nname = \"auto-app\"\n", encoding="utf-8")

            proc = subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts" / "bootstrap.py"), str(target)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            reg = json.loads((target / ".aief" / "skills" / "registry.json").read_text(encoding="utf-8"))
            self.assertEqual(reg["total_skills"], 33)
            cfg = json.loads((target / ".aief" / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(sorted(cfg["stacks"]), ["dotnet", "python"])
            self.assertEqual(len(cfg["enabledPlatforms"]), 5)

            comp_proc = subprocess.run(
                [sys.executable, str(target / ".aief" / "scripts" / "compose.py")],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(comp_proc.returncode, 0, comp_proc.stderr + comp_proc.stdout)
            self.assertIn("Updated:          0", comp_proc.stdout)
            self.assertIn("Validation:", comp_proc.stdout)
            self.assertIn("PASS", comp_proc.stdout)

            upd_proc = subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts" / "bootstrap.py"), str(target), "--update"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(upd_proc.returncode, 0, upd_proc.stderr + upd_proc.stdout)

    def test_10_jsonc_tsconfig_and_vscode_configs_supported_in_consumer_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "angular-jsonc"
            fake_home = root / "isolated-home"
            fake_home.mkdir()
            target.mkdir()
            (target / "package.json").write_text('{"name": "angular-jsonc"}\n', encoding="utf-8")
            (target / "tsconfig.json").write_text(
                '/* TypeScript config */\n{\n  // comment inside root\n  "compilerOptions": { "strict": true, }\n}\n',
                encoding="utf-8",
            )
            vscode_dir = target / ".vscode"
            vscode_dir.mkdir()
            (vscode_dir / "launch.json").write_text(
                '{\n  // VS Code URL contains https://example.com\n  "version": "0.2.0",\n  "configurations": [],\n}\n',
                encoding="utf-8",
            )
            nested_vscode = target / "apps" / "web" / ".vscode"
            nested_vscode.mkdir(parents=True)
            (nested_vscode / "extensions.json").write_text(
                '{\n  // Nested workspace recommendations\n  "recommendations": ["angular.ng-template"]\n}\n',
                encoding="utf-8",
            )

            bootstrap.bootstrap_project(target_dir=target, platforms=["antigravity", "copilot"], optional_packs=[])
            passed, report, _, _ = validate.run_validation_full(target, mode="consumer", home_dir=fake_home)
            self.assertTrue(passed, report)

    def test_11_preflight_detects_pnpm_when_lockfile_present(self) -> None:
        sys.path.insert(0, str(SCRIPTS_DIR))
        import preflight  # noqa: E402

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "pnpm-app"
            target.mkdir()
            (target / "package.json").write_text('{"name": "pnpm-app"}\n', encoding="utf-8")
            (target / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")

            def _which_present(cmd: str, path: str | None = None) -> str | None:
                return f"C:\\bin\\{cmd}.cmd" if cmd in {"node", "npm", "pnpm"} else None

            fake_proc = mock.Mock(returncode=0, stdout="10.0.0\n")
            with mock.patch.object(preflight.shutil, "which", side_effect=_which_present), mock.patch.object(
                preflight.subprocess, "run", return_value=fake_proc
            ):
                ok_res = preflight.detect_node_angular(env={"PATH": "C:\\bin"}, project_root=target)
                self.assertEqual(ok_res["status"], "AVAILABLE")
                self.assertEqual(ok_res["package_manager"], "pnpm")
                self.assertIn("pnpm-lock.yaml", str(ok_res["guidance"]))

            def _which_no_pnpm(cmd: str, path: str | None = None) -> str | None:
                return f"C:\\bin\\{cmd}.cmd" if cmd in {"node", "npm"} else None

            with mock.patch.object(preflight.shutil, "which", side_effect=_which_no_pnpm), mock.patch.object(
                preflight.subprocess, "run", return_value=fake_proc
            ):
                miss_res = preflight.detect_node_angular(env={"PATH": "C:\\bin"}, project_root=target)
                self.assertEqual(miss_res["status"], "MISSING")
                self.assertEqual(miss_res["package_manager"], "pnpm")
                self.assertIn("corepack enable pnpm", str(miss_res["guidance"]))

    def test_12_custom_prompts_projected_and_pruned_across_platforms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "prompt-app"
            fake_home = root / "isolated-home"
            fake_home.mkdir()
            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=ALL_PLATFORMS,
                optional_packs=[],
            )

            prompts_dir = target / ".aief" / "custom" / "prompts"
            prompts_dir.mkdir(parents=True, exist_ok=True)
            prompt_file = prompts_dir / "api-audit.md"
            prompt_file.write_text(
                "---\n"
                'description: "Audit API routes and OpenAPI schemas"\n'
                "---\n"
                'Check every route for auth "guards" and input validation.\n',
                encoding="utf-8",
            )

            res = compose.compose_consumer(target)
            self.assertIn("api-audit", res.get("custom_prompts", []))
            copilot_p = target / ".github" / "prompts" / "api-audit.prompt.md"
            claude_p = target / ".claude" / "commands" / "api-audit.md"
            gemini_p = target / ".gemini" / "commands" / "api-audit.toml"
            self.assertTrue(copilot_p.exists())
            self.assertTrue(claude_p.exists())
            self.assertTrue(gemini_p.exists())
            parsed_toml = tomllib.loads(gemini_p.read_text(encoding="utf-8"))
            self.assertEqual(parsed_toml["description"], "Audit API routes and OpenAPI schemas")
            self.assertIn('auth "guards"', parsed_toml["prompt"])
            self.assertIn("/api-audit", (target / "AGENTS.md").read_text(encoding="utf-8"))

            lock = json.loads((target / ".aief" / "lock.json").read_text(encoding="utf-8"))
            self.assertEqual(lock["managed_files"][".claude/commands/api-audit.md"]["ownership"], "consumer_custom_prompt")

            passed, report, _, _ = validate.run_validation_full(target, mode="consumer", home_dir=fake_home)
            self.assertTrue(passed, report)

            # Remove custom prompt and verify custom artifacts are pruned without touching built-ins
            prompt_file.unlink()
            res2 = compose.compose_consumer(target)
            self.assertIn(".github/prompts/api-audit.prompt.md", res2["pruned"])
            self.assertIn(".claude/commands/api-audit.md", res2["pruned"])
            self.assertIn(".gemini/commands/api-audit.toml", res2["pruned"])
            self.assertFalse(copilot_p.exists())
            self.assertFalse(claude_p.exists())
            self.assertFalse(gemini_p.exists())
            self.assertTrue((target / ".github" / "prompts" / "grill-me.prompt.md").exists())
            self.assertTrue((target / ".claude" / "commands" / "validate-framework.md").exists())

            passed2, report2, _, _ = validate.run_validation_full(target, mode="consumer", home_dir=fake_home)
            self.assertTrue(passed2, report2)

    def test_13_custom_mcp_projected_secret_rejected_and_pruned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "mcp-app"
            fake_home = root / "isolated-home"
            fake_home.mkdir()
            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=ALL_PLATFORMS,
                optional_packs=[],
            )

            mcp_path = target / ".aief" / "custom" / "mcp.json"
            # Literal secret must fail closed
            mcp_path.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "bad-gh": {
                                "command": "npx",
                                "args": ["-y", "@modelcontextprotocol/server-github"],
                                "env": {"TOKEN": "ghp_" + ("x" * 36)},
                            }
                        }
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            with self.assertRaises(compose.BootstrapSecurityError):
                compose.compose_consumer(target)

            # Valid MCP config with ${ENV_VAR} placeholder succeeds across all 5 platforms
            mcp_path.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "github": {
                                "command": "npx",
                                "args": ["-y", "@modelcontextprotocol/server-github"],
                                "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"},
                            },
                            "playwright": {
                                "command": "npx",
                                "args": ["-y", "@playwright/mcp@latest"],
                            },
                            "disabled-srv": {
                                "command": "npx",
                                "args": ["-y", "unused-server"],
                                "disabled": True,
                            },
                        }
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            res = compose.compose_consumer(target)
            self.assertEqual(res.get("custom_mcp"), ["github", "playwright"])

            claude_mcp = json.loads((target / ".mcp.json").read_text(encoding="utf-8"))
            self.assertIn("github", claude_mcp["mcpServers"])
            self.assertNotIn("disabled-srv", claude_mcp["mcpServers"])

            vscode_mcp = json.loads((target / ".vscode" / "mcp.json").read_text(encoding="utf-8"))
            self.assertEqual(vscode_mcp["servers"]["github"]["type"], "stdio")

            codex_parsed = tomllib.loads((target / ".codex" / "config.toml").read_text(encoding="utf-8"))
            self.assertIn("github", codex_parsed["mcp_servers"])
            self.assertEqual(
                codex_parsed["mcp_servers"]["github"]["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"],
                "${GITHUB_PERSONAL_ACCESS_TOKEN}",
            )

            gemini_cfg = json.loads((target / ".gemini" / "settings.json").read_text(encoding="utf-8"))
            self.assertIn("playwright", gemini_cfg["mcpServers"])
            self.assertTrue((target / ".aief" / "adapters" / "antigravity" / "mcp_config.json").exists())

            passed, report, _, _ = validate.run_validation_full(target, mode="consumer", home_dir=fake_home)
            self.assertTrue(passed, report)

            # Remove mcp.json -> auxiliary MCP files pruned cleanly, .codex/.gemini reverted cleanly
            mcp_path.unlink()
            res2 = compose.compose_consumer(target)
            self.assertIn(".mcp.json", res2["pruned"])
            self.assertIn(".vscode/mcp.json", res2["pruned"])
            self.assertIn(".aief/adapters/antigravity/mcp_config.json", res2["pruned"])
            self.assertFalse((target / ".mcp.json").exists())
            self.assertFalse((target / ".vscode" / "mcp.json").exists())
            codex_after = tomllib.loads((target / ".codex" / "config.toml").read_text(encoding="utf-8"))
            self.assertNotIn("mcp_servers", codex_after)
            gemini_after = json.loads((target / ".gemini" / "settings.json").read_text(encoding="utf-8"))
            self.assertNotIn("mcpServers", gemini_after)

            passed2, report2, _, _ = validate.run_validation_full(target, mode="consumer", home_dir=fake_home)
            self.assertTrue(passed2, report2)

    def test_14_new_skills_adhd_humanizer_session_handoff_and_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "skills-app"
            fake_home = root / "isolated-home"
            fake_home.mkdir()
            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "claude-code"],
                optional_packs=["communication", "context-engineering"],
            )

            for sk in ("i-have-adhd", "humanizer", "session-handoff"):
                self.assertTrue((target / ".agents" / "skills" / sk / "SKILL.md").exists(), f"Missing .agents skill {sk}")
                self.assertTrue((target / ".claude" / "skills" / sk / "SKILL.md").exists(), f"Missing .claude skill {sk}")

            # Toggle off humanizer cleanly
            cfg_path = target / ".aief" / "config.json"
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            cfg["disabled"]["skills"] = ["humanizer"]
            cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

            compose.compose_consumer(target)
            self.assertFalse((target / ".agents" / "skills" / "humanizer").exists())
            self.assertFalse((target / ".claude" / "skills" / "humanizer").exists())
            self.assertTrue((target / ".agents" / "skills" / "session-handoff" / "SKILL.md").exists())

            # Run session-handoff scaffold inside consumer project -> creates .aief/state/session-handoffs/ file
            script_path = target / ".agents" / "skills" / "session-handoff" / "scripts" / "create_handoff.py"
            proc = subprocess.run(
                [sys.executable, str(script_path), "test-resume"],
                cwd=target,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            handoffs_dir = target / ".aief" / "state" / "session-handoffs"
            created_files = list(handoffs_dir.glob("*-test-resume.md"))
            self.assertEqual(len(created_files), 1, f"Expected handoff md file, stdout={proc.stdout}")

            passed, report, _, _ = validate.run_validation_full(target, mode="consumer", home_dir=fake_home)
            self.assertTrue(passed, report)

    def test_15_packaging_version_parity_and_aief_cli(self) -> None:
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        import aief_cli  # noqa: E402
        from aief_cli import cli as aief_cli_mod  # noqa: E402

        py_ver = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
        tpl_ver = json.loads((REPO_ROOT / "templates" / "project.framework.json").read_text(encoding="utf-8"))[
            "frameworkVersion"
        ]
        reg_ver = json.loads((REPO_ROOT / "skills" / "registry.json").read_text(encoding="utf-8"))["framework_version"]
        self.assertEqual(py_ver, aief_cli.__version__)
        self.assertEqual(py_ver, bootstrap.FRAMEWORK_VERSION)
        self.assertEqual(py_ver, tpl_ver)
        self.assertEqual(py_ver, reg_ver)

        self.assertEqual(aief_cli.resolve_framework_root(), REPO_ROOT)

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "cli-app"
            self.assertEqual(
                aief_cli_mod.main(["init", str(target), "--platforms", "antigravity,copilot"]),
                0,
            )
            self.assertEqual(aief_cli_mod.main(["compose", str(target)]), 0)
            self.assertEqual(aief_cli_mod.main(["update", str(target), "--dry-run"]), 0)
            self.assertEqual(aief_cli_mod.main(["validate", str(target), "--mode", "consumer"]), 0)
            self.assertEqual(aief_cli_mod.main(["check-sync"]), 0)
            with mock.patch.object(aief_cli_mod, "resolve_framework_root", return_value=Path(tmp)):
                old_cwd = Path.cwd()
                try:
                    import os
                    os.chdir(tmp)
                    self.assertEqual(aief_cli_mod.main(["check-sync"]), 2)
                finally:
                    os.chdir(old_cwd)

            # Verify bundle.zip short-path extraction & zip-slip guard (avoids Windows MAX_PATH)
            import zipfile
            bundle_zip = Path(tmp) / "bundle.zip"
            with zipfile.ZipFile(bundle_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for p in (REPO_ROOT / "core" / "rules").glob("*.md"):
                    zf.write(p, arcname=p.relative_to(REPO_ROOT).as_posix())
            extracted = aief_cli._extract_bundle_zip(bundle_zip, cache_base=Path(tmp) / "cache")
            self.assertTrue((extracted / "core" / "rules" / "engineering-principles.md").is_file())
            evil_zip = Path(tmp) / "evil.zip"
            with zipfile.ZipFile(evil_zip, "w") as zf:
                zf.writestr("../escape.txt", "bad")
            with self.assertRaises(ValueError):
                aief_cli._extract_bundle_zip(evil_zip, cache_base=Path(tmp) / "cache2")

    def test_16_graphify_missing_cli_reported_to_user(self) -> None:
        import io
        from contextlib import redirect_stdout

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "no-graphify-app"
            fake_home = root / "isolated-home"
            fake_home.mkdir()

            with mock.patch("bootstrap.shutil.which", return_value=None), mock.patch(
                "validate.shutil.which", return_value=None
            ):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = bootstrap.main([str(target), "--platforms", "antigravity", "--optional-packs", "none"])
                self.assertEqual(rc, 0)
                out = buf.getvalue()
                self.assertIn("Graphify CLI:       NOT INSTALLED", out)

                passed, report, _, info_msgs = validate.run_validation_full(target, mode="consumer", home_dir=fake_home)
                self.assertTrue(passed, report)
                self.assertTrue(
                    any("Graphify CLI not installed" in msg for msg in info_msgs),
                    f"Expected Graphify CLI missing notice in info: {info_msgs}",
                )

    def test_17_vintgen_brownfield_isolation_no_skills_collision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "vintgen-like"
            fake_home = root / "isolated-home"
            fake_home.mkdir()
            target.mkdir()

            (target / "package.json").write_text('{"name": "vintgen-like"}\n', encoding="utf-8")
            (target / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
            (target / "AGENTS.md").write_text("# VintGen Custom Agent Guide\nAlways preserve domain prompts.\n", encoding="utf-8")

            ext_skill_dir = target / "skills" / "vintgen" / "prompts"
            ext_skill_dir.mkdir(parents=True)
            vintgen_skill = target / "skills" / "vintgen" / "SKILL.md"
            vintgen_skill_text = "---\nname: vintgen\ndescription: VintGen listing skill\n---\n\n# VintGen\n"
            vintgen_skill.write_text(vintgen_skill_text, encoding="utf-8")
            (ext_skill_dir / "web-instructions.md").write_text("# Web Prompt\n", encoding="utf-8")

            ext_rules = target / ".agents" / "rules"
            ext_rules.mkdir(parents=True)
            strict_rule = ext_rules / "strict-rules.md"
            strict_rule_text = "# Strict Host Rule\nNever break user layout.\n"
            strict_rule.write_text(strict_rule_text, encoding="utf-8")

            stacks = bootstrap.detect_project_stacks(target)
            res = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=ALL_PLATFORMS,
                optional_packs=["all"],
                stacks=stacks,
            )

            self.assertEqual(res["layout"], "isolated")
            self.assertIn(".aief/custom/imported/AGENTS.md", res["imported"])
            self.assertIn("skills/vintgen/SKILL.md", res["preserved_external"])
            self.assertIn(".agents/rules/strict-rules.md", res["preserved_external"])

            # Framework assets live solely inside .aief/ (never colliding at root)
            self.assertTrue((target / ".aief" / "config.json").exists())
            self.assertTrue((target / ".aief" / "lock.json").exists())
            self.assertTrue((target / ".aief" / ".gitignore").exists())
            aief_gi_text = (target / ".aief" / ".gitignore").read_text(encoding="utf-8")
            self.assertIn("__pycache__/", aief_gi_text)
            self.assertIn("*.py[cod]", aief_gi_text)
            self.assertTrue((target / ".aief" / "state" / "manifest.json").exists())
            self.assertTrue((target / ".aief" / "skills" / "registry.json").exists())
            for legacy_root in ("project.framework.json", ".framework-lock.json", ".framework-state", ".framework-custom", "core", "agents", "workflows", "scripts"):
                self.assertFalse((target / legacy_root).exists(), f"Unexpected root framework artifact: {legacy_root}")

            # Pre-existing skills/ and .agents/rules/ remain untouched
            self.assertEqual(vintgen_skill.read_text(encoding="utf-8"), vintgen_skill_text)
            self.assertEqual(strict_rule.read_text(encoding="utf-8"), strict_rule_text)
            self.assertIn("Always preserve domain prompts", (target / "AGENTS.md").read_text(encoding="utf-8"))

            passed, report, warnings, _ = validate.run_validation_full(
                target, mode="consumer", home_dir=fake_home
            )
            self.assertTrue(passed, f"Brownfield isolated validation failed: {report}")
            self.assertEqual(warnings, [], f"Expected zero warnings, got: {warnings}")

    def test_18_interactive_wizard_discovery_duplicates_and_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "wizard-brownfield"
            fake_home = root / "isolated-home"
            fake_home.mkdir()
            target.mkdir()
            (target / "package.json").write_text('{"name": "wizard-app"}\n', encoding="utf-8")

            shared_rules = "# Product Domain Rules\nKeep domain model clean.\n"
            (target / "AGENTS.md").write_text(shared_rules, encoding="utf-8")
            (target / "CLAUDE.md").write_text("# Claude Legacy Rules\nCheck security.\n", encoding="utf-8")
            (target / ".github").mkdir()
            (target / ".github" / "copilot-instructions.md").write_text(shared_rules, encoding="utf-8")

            ext_skill_dir = target / "skills" / "museum-api"
            ext_skill_dir.mkdir(parents=True)
            (ext_skill_dir / "SKILL.md").write_text(
                "---\nname: museum-api\ndescription: Museum domain API rules\n---\n\n# Museum API\n",
                encoding="utf-8",
            )
            ext_rules_dir = target / ".agents" / "rules"
            ext_rules_dir.mkdir(parents=True)
            (ext_rules_dir / "ascii-only.md").write_text("# ASCII Rule\nUse ASCII in new files.\n", encoding="utf-8")

            ctx = bootstrap.discover_workspace_context(target)
            legacy_map = {item["rel"]: item for item in ctx["legacy_instructions"]}  # type: ignore[index]
            self.assertEqual(legacy_map[".github/copilot-instructions.md"]["duplicate_of"], "AGENTS.md")
            self.assertIsNone(legacy_map["CLAUDE.md"]["duplicate_of"])

            answers = iter([
                "1,5",     # platforms: antigravity, gemini-cli
                "1,2,4",   # packs: communication, context-engineering, frontend-design
                "1",       # AGENTS.md -> copy
                "2",       # CLAUDE.md -> move to .aief/custom/rules/ and remove old
                "project-guidelines",  # custom rule filename for moved CLAUDE.md
                "4",       # .github/copilot-instructions.md -> delete duplicate
                "2",       # external skills -> copy into .aief/custom/skills/
                "2",       # external .agents/rules/ -> move into .aief/custom/rules/
                "y",       # confirm
            ])
            logs: list[str] = []
            wiz = bootstrap.run_interactive_init_wizard(
                target,
                input_fn=lambda _prompt: next(answers),
                output_fn=logs.append,
            )
            self.assertIsNotNone(wiz)
            assert wiz is not None
            self.assertEqual(wiz["platforms"], ["antigravity", "gemini-cli"])
            self.assertEqual(
                wiz["optional_packs"],
                ["communication", "context-engineering", "frontend-design"],
            )
            self.assertEqual(wiz["legacy_actions"]["CLAUDE.md"], "move")
            self.assertEqual(wiz["legacy_move_names"]["CLAUDE.md"], "project-guidelines.md")
            self.assertEqual(wiz["legacy_actions"][".github/copilot-instructions.md"], "delete")
            self.assertTrue(any("DUPLICATE CONTENT" in line for line in logs), logs)

            res = bootstrap.bootstrap_project(
                target_dir=target,
                platforms=list(wiz["platforms"]),
                optional_packs=list(wiz["optional_packs"]),
                stacks=bootstrap.detect_project_stacks(target),
                legacy_actions=dict(wiz["legacy_actions"]),
                legacy_move_names=dict(wiz["legacy_move_names"]),
                unify_external_skills=bool(wiz["unify_external_skills"]),
                move_external_rules=bool(wiz["move_external_rules"]),
            )

            self.assertFalse((target / "CLAUDE.md").exists())
            self.assertFalse((target / ".github" / "copilot-instructions.md").exists())
            self.assertFalse((target / ".agents" / "rules" / "ascii-only.md").exists())
            self.assertTrue((target / ".aief" / "custom" / "imported" / "AGENTS.md").exists())
            self.assertTrue((target / ".aief" / "custom" / "rules" / "project-guidelines.md").exists())
            self.assertTrue((target / ".aief" / "custom" / "rules" / "ascii-only.md").exists())
            self.assertTrue((target / ".agents" / "skills" / "museum-api" / "SKILL.md").exists())
            self.assertIn(".github/copilot-instructions.md", res["deleted_legacy"])
            self.assertTrue(any("CLAUDE.md" in m for m in res["moved"]), res["moved"])

            agents_txt = (target / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Check security.", agents_txt)
            self.assertIn("Use ASCII in new files.", agents_txt)
            self.assertIn("museum-api", agents_txt)

            passed, report, warnings, _ = validate.run_validation_full(
                target, mode="consumer", home_dir=fake_home
            )
            self.assertTrue(passed, f"Wizard brownfield validation failed: {report}")
            self.assertEqual(warnings, [], f"Expected zero warnings, got: {warnings}")

            # --no-import flag skips legacy instruction import in non-interactive mode
            target_no_imp = root / "no-import-app"
            target_no_imp.mkdir()
            (target_no_imp / ".github").mkdir()
            (target_no_imp / ".github" / "copilot-instructions.md").write_text("# Old\n", encoding="utf-8")
            res_no_imp = bootstrap.bootstrap_project(
                target_dir=target_no_imp,
                platforms=["antigravity"],
                optional_packs=[],
                no_import=True,
            )
            self.assertEqual(res_no_imp["imported"], [])
            self.assertIn(".github/copilot-instructions.md", res_no_imp["skipped_legacy"])
            self.assertFalse((target_no_imp / ".aief" / "custom" / "imported" / "copilot-instructions.md").exists())

            # Arrow-key TUI mode (UP/DOWN/SPACE/ALL/ENTER) drives multi-select and single-select identically
            import io
            buf = io.StringIO()
            with mock.patch("sys.stdout", buf):
                # Toggle off item 1 (a -> none, then space selects 1=antigravity, DOWNx4, space selects 5=gemini-cli, ENTER)
                keys = iter(["ALL", "SPACE", "DOWN", "DOWN", "DOWN", "DOWN", "SPACE", "ENTER"])
                picked_tui = bootstrap._tui_multiselect(
                    "Target platforms",
                    list(bootstrap.ALL_PLATFORMS),
                    preselected=set(bootstrap.ALL_PLATFORMS),
                    min_selected=1,
                    key_fn=lambda: next(keys),
                    stream=buf,
                )
                self.assertEqual(picked_tui, ["antigravity", "gemini-cli"])

                keys_sel = iter(["DOWN", "ENTER"])
                picked_action = bootstrap._tui_select(
                    "Legacy action",
                    [("copy", "Copy"), ("move", "Move"), ("skip", "Skip")],
                    default_index=0,
                    key_fn=lambda: next(keys_sel),
                    stream=buf,
                )
                self.assertEqual(picked_action, "move")

                keys_esc = iter(["ESC"])
                self.assertIsNone(
                    bootstrap._tui_select(
                        "Cancel check",
                        [("a", "A")],
                        key_fn=lambda: next(keys_esc),
                        stream=buf,
                    )
                )


if __name__ == "__main__":
    unittest.main()
