#!/usr/bin/env python3
"""M9-03 Static Contract & Consumer Adapter Tests (`tests/test_m9_agent_platform_contracts.py`).

Covers Claude/Copilot agent tool schemas, read-only reviewer constraints, unknown tool
handling, Antigravity hooks contract, Claude & Gemini settings schemas, capability
model consistency, deterministic adapter sync, and consumer generation regressions.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import tomllib
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import bootstrap  # noqa: E402
import platform_capabilities  # noqa: E402
import sync_adapters  # noqa: E402
import validate  # noqa: E402


class TestM9AgentPlatformContracts(unittest.TestCase):
    """Static contract verification for M9-03 (GAP-03, GAP-04, GAP-06)."""

    def test_01_claude_agent_schema_and_readonly_reviewer(self) -> None:
        agent_path = REPO_ROOT / "adapters" / "claude-code" / "agents" / "code-reviewer.md"
        meta = validate.parse_simple_frontmatter(agent_path.read_text(encoding="utf-8"))
        self.assertEqual(meta.get("name"), "framework-code-reviewer")
        self.assertTrue(meta.get("description"))
        self.assertNotIn("subagent", meta)
        self.assertNotIn("mainAgent", meta)

        tools = validate._parse_tools_field(meta.get("tools"))
        self.assertEqual(set(tools), {"Read", "Glob", "Grep"})
        disallowed = validate._parse_tools_field(meta.get("disallowedTools"))
        self.assertEqual(set(disallowed), {"Write", "Edit", "Bash"})

    def test_02_copilot_agent_schema_and_readonly_reviewer(self) -> None:
        agent_path = REPO_ROOT / "adapters" / "copilot" / "code-reviewer.agent.md"
        meta = validate.parse_simple_frontmatter(agent_path.read_text(encoding="utf-8"))
        self.assertTrue(meta.get("description"))
        tools = validate._parse_tools_field(meta.get("tools"))
        self.assertEqual(set(tools), {"read", "search"})
        self.assertFalse(any(t in {"edit", "terminal", "read_file", "run_command"} for t in tools))

    def test_03_rejects_unmapped_or_write_tools_in_reviewer_agents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "bad-agents"
            (root / "adapters" / "claude-code" / "agents").mkdir(parents=True)
            (root / "adapters" / "copilot").mkdir(parents=True)

            (root / "adapters" / "claude-code" / "agents" / "code-reviewer.md").write_text(
                "---\nname: framework-code-reviewer\ndescription: Review\nsubagent: true\ntools: [read_file, Bash]\n---\nBody\n",
                encoding="utf-8",
            )
            (root / "adapters" / "copilot" / "code-reviewer.agent.md").write_text(
                "---\ndescription: Review\ntools: [\"read\", \"terminal\"]\n---\nBody\n",
                encoding="utf-8",
            )

            errs = validate.check_m9_agent_and_settings_contracts(root, mode="framework")
            self.assertTrue(any("subagent" in e for e in errs), errs)
            self.assertTrue(any("read_file" in e for e in errs), errs)
            self.assertTrue(any("read-only" in e and "code-reviewer.md" in e for e in errs), errs)
            self.assertTrue(any("read-only" in e and "code-reviewer.agent.md" in e for e in errs), errs)

    def test_04_missing_or_unknown_tool_mappings_explicit_in_capability_model(self) -> None:
        model = platform_capabilities.load_platform_capabilities()
        claude_cap = platform_capabilities.get_platform(model, "claude-code")
        copilot_cap = platform_capabilities.get_platform(model, "copilot")
        codex_cap = platform_capabilities.get_platform(model, "codex")
        gemini_cap = platform_capabilities.get_platform(model, "gemini-cli")

        self.assertEqual(claude_cap["tool_id_map"]["state"], "documentation_derived")
        self.assertEqual(copilot_cap["tool_id_map"]["state"], "documentation_derived")
        self.assertEqual(codex_cap["tool_id_map"]["state"], "unknown")
        self.assertEqual(codex_cap["tool_id_map"]["canonical_to_native"], {})
        self.assertEqual(gemini_cap["tool_id_map"]["state"], "unknown")
        self.assertEqual(gemini_cap["tool_id_map"]["canonical_to_native"], {})

        # Static contract alignment never implies RUNTIME_VERIFIED
        for pid in ("copilot", "claude-code", "gemini-cli"):
            self.assertNotEqual(platform_capabilities.get_platform(model, pid)["runtime_status"], "RUNTIME_VERIFIED")

    def test_05_antigravity_hooks_contract_valid_and_disabled_by_default(self) -> None:
        hooks_path = REPO_ROOT / "adapters" / "antigravity" / "hooks.json"
        hooks = json.loads(hooks_path.read_text(encoding="utf-8"))
        self.assertNotIn("description", hooks)
        self.assertNotIn("hooks", hooks)
        self.assertIn("framework-validation-reminder", hooks)

        cfg = hooks["framework-validation-reminder"]
        self.assertIs(cfg.get("enabled"), False)
        self.assertIn("Stop", cfg)
        self.assertEqual(cfg["Stop"][0]["type"], "command")
        self.assertIn("scripts/validate.py", cfg["Stop"][0]["command"])

        errs = validate.check_m9_agent_and_settings_contracts(REPO_ROOT, mode="framework")
        self.assertEqual(errs, [])

    def test_06_rejects_unsupported_hook_fields_and_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "bad-hooks"
            (root / "adapters" / "antigravity").mkdir(parents=True)
            (root / "adapters" / "antigravity" / "hooks.json").write_text(
                json.dumps({
                    "description": "Legacy conceptual hooks",
                    "hooks": {"preCommit": {"command": "python scripts/validate.py"}},
                    "bad-hook": {"preCommit": []},
                }),
                encoding="utf-8",
            )
            errs = validate.check_m9_agent_and_settings_contracts(root, mode="framework")
            self.assertTrue(any("top-level 'description'/'hooks'" in e for e in errs), errs)
            self.assertTrue(any("unsupported hook event 'preCommit'" in e for e in errs), errs)

    def test_07_claude_and_gemini_settings_schemas_clean(self) -> None:
        claude_settings = json.loads(
            (REPO_ROOT / "adapters" / "claude-code" / "settings.json").read_text(encoding="utf-8")
        )
        self.assertNotIn("description", claude_settings)
        self.assertIn("permissions", claude_settings)
        self.assertTrue(set(claude_settings.keys()).issubset(validate.CLAUDE_SETTINGS_ALLOWED_KEYS))

        gemini_settings = json.loads(
            (REPO_ROOT / "adapters" / "gemini-cli" / "settings.json").read_text(encoding="utf-8")
        )
        self.assertNotIn("description", gemini_settings)
        self.assertEqual(gemini_settings.get("contextFileName"), ["GEMINI.md", "AGENTS.md"])

        # Negative test rejecting description key in settings
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "bad-settings"
            (root / "adapters" / "claude-code").mkdir(parents=True)
            (root / "adapters" / "gemini-cli").mkdir(parents=True)
            (root / "adapters" / "claude-code" / "settings.json").write_text(
                json.dumps({"description": "invalid", "bogusKey": True}),
                encoding="utf-8",
            )
            (root / "adapters" / "gemini-cli" / "settings.json").write_text(
                json.dumps({"description": "invalid", "contextFileName": "GEMINI.md"}),
                encoding="utf-8",
            )
            errs = validate.check_m9_agent_and_settings_contracts(root, mode="framework")
            self.assertTrue(any("claude-code/settings.json" in e and "description" in e for e in errs), errs)
            self.assertTrue(any("bogusKey" in e for e in errs), errs)
            self.assertTrue(any("gemini-cli/settings.json" in e and "description" in e for e in errs), errs)

    def test_08_deterministic_adapter_sync_and_consumer_generation(self) -> None:
        ok, drifted = sync_adapters.sync_adapters(REPO_ROOT, check_only=True)
        self.assertTrue(ok, f"Adapters out of sync: {drifted}")
        self.assertEqual(sync_adapters.generate_expected_files(REPO_ROOT), sync_adapters.generate_expected_files(REPO_ROOT))

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "consumer-m903"
            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity", "copilot", "claude-code", "codex", "gemini-cli"],
                optional_packs=["communication"],
            )
            passed, report = validate.run_validation(target, mode="consumer")
            self.assertTrue(passed, f"Consumer M9-03 validation failed: {report}")

            # Consumer Claude & Copilot reviewers must preserve mapped read-only tools
            c_claude = validate.parse_simple_frontmatter(
                (target / ".claude" / "agents" / "framework-code-reviewer.md").read_text(encoding="utf-8")
            )
            self.assertNotIn("subagent", c_claude)
            self.assertEqual(set(validate._parse_tools_field(c_claude.get("tools"))), {"Read", "Glob", "Grep"})

            c_copilot = validate.parse_simple_frontmatter(
                (target / ".github" / "agents" / "code-reviewer.agent.md").read_text(encoding="utf-8")
            )
            self.assertEqual(set(validate._parse_tools_field(c_copilot.get("tools"))), {"read", "search"})

            # Consumer settings omit description
            self.assertNotIn(
                "description",
                json.loads((target / ".claude" / "settings.json").read_text(encoding="utf-8")),
            )
            self.assertNotIn(
                "description",
                json.loads((target / ".gemini" / "settings.json").read_text(encoding="utf-8")),
            )

            # Consumer hooks template is valid, disabled, and points to consumer validate mode
            c_hooks = json.loads((target / ".aief" / "adapters" / "antigravity" / "hooks.json").read_text(encoding="utf-8"))
            self.assertIs(c_hooks["framework-validation-reminder"]["enabled"], False)
            self.assertIn("--mode consumer", c_hooks["framework-validation-reminder"]["Stop"][0]["command"])

    def test_09_all_required_platform_files_toml_schemas_and_frontmatter(self) -> None:
        # Verify all schema files and project template parse cleanly
        for rel in (
            "core/schemas/agent-role.schema.json",
            "core/schemas/skill-frontmatter.schema.json",
            "core/schemas/handoff-packet.schema.json",
            "core/schemas/framework-config.schema.json",
            "templates/project.framework.json",
        ):
            parsed = json.loads((REPO_ROOT / Path(rel)).read_text(encoding="utf-8"))
            self.assertIsInstance(parsed, dict, rel)

        # Verify all upstream mapped adapter source files exist
        for pid, mappings in bootstrap.PLATFORM_ADAPTER_MAPPINGS.items():
            for src_rel, _ in mappings:
                self.assertTrue((REPO_ROOT / Path(src_rel)).exists(), f"Missing adapter source {src_rel} for {pid}")

        # Verify TOML files (Codex config + Gemini command) parse strictly
        codex_toml = tomllib.loads((REPO_ROOT / "adapters" / "codex" / "config.toml").read_text(encoding="utf-8"))
        self.assertIn("approval_policy", codex_toml)
        self.assertIn("sandbox_mode", codex_toml)

        gemini_toml = tomllib.loads(
            (REPO_ROOT / "adapters" / "gemini-cli" / "commands" / "workflow.toml").read_text(encoding="utf-8")
        )
        self.assertTrue(gemini_toml.get("description"))
        self.assertTrue(gemini_toml.get("prompt"))

        # Verify Copilot .prompt.md / .instructions.md and Claude .md command contracts
        copilot_inst = validate.parse_simple_frontmatter(
            (REPO_ROOT / "adapters" / "copilot" / "framework.instructions.md").read_text(encoding="utf-8")
        )
        self.assertTrue(copilot_inst.get("applyTo"))
        copilot_prompt = validate.parse_simple_frontmatter(
            (REPO_ROOT / "adapters" / "copilot" / "grill-me.prompt.md").read_text(encoding="utf-8")
        )
        self.assertTrue(copilot_prompt.get("description"))

        # Verify consumer-generated TOML & adapter files per platform match static contracts
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "contract-consumer"
            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=list(bootstrap.ALL_PLATFORMS),
                optional_packs=[],
            )
            c_codex = tomllib.loads((target / ".codex" / "config.toml").read_text(encoding="utf-8"))
            self.assertEqual(c_codex.get("sandbox_mode"), codex_toml.get("sandbox_mode"))
            c_gemini = tomllib.loads((target / ".gemini" / "commands" / "workflow.toml").read_text(encoding="utf-8"))
            self.assertIn("workflows/", str(c_gemini.get("prompt", "")))
            for banned in validate.BANNED_CONSUMER_UPSTREAM_TOKENS:
                self.assertNotIn(banned, str(c_gemini.get("prompt", "")))

    def test_10_all_canonical_roles_projected_to_claude_and_copilot(self) -> None:
        import compose

        expected_specialists = [
            "product-analyst",
            "software-architect",
            "ui-ux-designer",
            "data-engineer",
            "planner-orchestrator",
            "backend-engineer",
            "frontend-engineer",
            "ai-engineer",
            "implementation-engineer",
            "qa-engineer",
            "security-engineer",
            "devops-release-engineer",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "subagent-consumer"
            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["claude-code", "copilot", "antigravity"],
                optional_packs=["all"],
            )
            self.assertTrue((target / ".claude" / "agents" / "framework-code-reviewer.md").exists())
            self.assertTrue((target / ".github" / "agents" / "code-reviewer.agent.md").exists())
            for role in expected_specialists:
                claude_f = target / ".claude" / "agents" / f"{role}.md"
                copilot_f = target / ".github" / "agents" / f"{role}.agent.md"
                self.assertTrue(claude_f.exists(), f"Missing Claude subagent {claude_f}")
                self.assertTrue(copilot_f.exists(), f"Missing Copilot subagent {copilot_f}")

            cfg_path = target / ".aief" / "config.json"
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            cfg.setdefault("disabled", {})["agents"] = ["ui-ux-designer"]
            cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

            compose.compose_consumer(target)
            self.assertFalse((target / ".claude" / "agents" / "ui-ux-designer.md").exists())
            self.assertFalse((target / ".github" / "agents" / "ui-ux-designer.agent.md").exists())
            self.assertTrue((target / ".claude" / "agents" / "backend-engineer.md").exists())
            self.assertTrue((target / ".github" / "agents" / "frontend-engineer.agent.md").exists())

            passed, report, _warns, _infos = validate.run_validation_full(target, mode="consumer")
            self.assertTrue(passed, report)


if __name__ == "__main__":
    unittest.main()
