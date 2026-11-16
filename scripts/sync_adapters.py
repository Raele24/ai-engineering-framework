#!/usr/bin/env python3
"""Synchronize thin platform adapters from canonical AI Engineering Framework sources.

Single Source of Truth:
- core/rules/*.md
- docs/WORKFLOW.md & workflows/*.md
- agents/*.md
- skills/registry.json & skills/*/*/SKILL.md
- integrations/mcp/mcp.template.json

Generated / Synchronized Outputs:
- Root entry points: AGENTS.md, CLAUDE.md, GEMINI.md, .github/copilot-instructions.md
- Platform adapter suites under adapters/{copilot,antigravity,claude-code,codex,gemini-cli}/

Usage:
    python scripts/sync_adapters.py           # Write/update all adapter files
    python scripts/sync_adapters.py --check   # Verify zero drift (exits 1 if out of sync)
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def parse_simple_frontmatter(markdown_text: str) -> Dict[str, object]:
    """Parse canonical YAML frontmatter using only the Python standard library."""
    match = FRONTMATTER_RE.match(markdown_text.replace("\r\n", "\n"))
    if not match:
        return {}
    raw_block = match.group(1)
    result: Dict[str, object] = {}
    for raw_line in raw_block.split("\n"):
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            if not inner:
                result[key] = []
            else:
                items: List[object] = []
                for part in inner.split(","):
                    cleaned = part.strip().strip('"').strip("'")
                    if cleaned.isdigit():
                        items.append(int(cleaned))
                    else:
                        items.append(cleaned)
                result[key] = items
        elif val.startswith('"') and val.endswith('"'):
            result[key] = val[1:-1]
        elif val.startswith("'") and val.endswith("'"):
            result[key] = val[1:-1]
        elif val.lower() in ("true", "false"):
            result[key] = val.lower() == "true"
        elif val.isdigit():
            result[key] = int(val)
        else:
            result[key] = val
    return result


def load_canonical_metadata(root: Path) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    """Load canonical agents and skill registry metadata."""
    agents_dir = root / "agents"
    agents: List[Dict[str, object]] = []
    for agent_path in sorted(agents_dir.glob("*.md")):
        text = agent_path.read_text(encoding="utf-8")
        meta = parse_simple_frontmatter(text)
        meta["path"] = f"agents/{agent_path.name}"
        agents.append(meta)

    registry_path = root / "skills" / "registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    return agents, registry


def compute_canonical_digest(root: Path) -> str:
    """Compute a deterministic SHA-256 digest across canonical rule, role, and workflow sources."""
    hasher = hashlib.sha256()
    canonical_globs = [
        "core/rules/*.md",
        "agents/*.md",
        "workflows/*.md",
        "skills/registry.json",
    ]
    for pattern in canonical_globs:
        for path in sorted(root.glob(pattern)):
            rel = path.relative_to(root).as_posix()
            content = path.read_text(encoding="utf-8").replace("\r\n", "\n")
            hasher.update(f"{rel}:{len(content)}\n".encode("utf-8"))
            hasher.update(content.encode("utf-8"))
    return hasher.hexdigest()[:16]


def build_agents_table(agents: List[Dict[str, object]]) -> str:
    lines = [
        "| Role ID | Title | Workflow Phases | Canonical Specification |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for agent in agents:
        phases_list = agent.get("phases", [])
        phases_str = ", ".join(str(p) for p in phases_list) if isinstance(phases_list, list) else str(phases_list)
        lines.append(
            f"| `{agent['name']}` | {agent['title']} | {phases_str} | [`{agent['path']}`](./{agent['path']}) |"
        )
    return "\n".join(lines)


def build_core_skills_table(registry: Dict[str, object]) -> str:
    lines = [
        "| Skill Name | Tier | Default | Path |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for skill in registry.get("skills", []):
        lines.append(
            f"| `{skill['name']}` | `{skill['tier']}` | `{skill['default_enabled']}` | [`{skill['path']}`](./{skill['path']}) |"
        )
    return "\n".join(lines)


def generate_expected_files(root: Path) -> Dict[str, str]:
    """Generate all adapter files in memory mapped by repo-relative POSIX path."""
    agents, registry = load_canonical_metadata(root)
    digest = compute_canonical_digest(root)
    agents_table = build_agents_table(agents)
    skills_table = build_core_skills_table(registry)

    files: Dict[str, str] = {}

    # 1. Universal AGENTS.md (OpenAI Codex, Google Antigravity, GitHub Copilot, Cursor)
    files["AGENTS.md"] = f"""<!-- AUTO-GENERATED BY scripts/sync_adapters.py | Canonical Digest: {digest} -->
# AI Engineering Framework — Universal Agent Instructions (`AGENTS.md`)

This repository is governed by the **AI Engineering Framework**. Do not improvise ad-hoc workflows.
All instructions below derive from the canonical source of truth in `core/rules/` and `docs/WORKFLOW.md`.

## 1. Non-Negotiable Core Rules
1. **Engineering Principles ([`core/rules/engineering-principles.md`](./core/rules/engineering-principles.md)):**
   - Clarify ambiguities (`Phase 2: Grill Me`) and lock testable `Given / When / Then` acceptance criteria (`Phase 3`) before writing production code.
   - Follow strict **Red -> Green -> Refactor TDD** (`Phase 9`).
   - Query `graphify-out/graph.json` (`graphify query`) first when present.
2. **Filesystem Context Handoff ([`core/rules/context-handoff-protocol.md`](./core/rules/context-handoff-protocol.md)):**
   - Persist phase deliverables to `docs/specs/`, `docs/adr/`, `docs/plans/`, and `.framework-state/handoffs/phase-<NN>-handoff.json`.
3. **Human Approval Gates ([`core/rules/human-approval-gates.md`](./core/rules/human-approval-gates.md)):**
   - Pause for explicit human approval at `Gate-01a` (Clarifications), `Gate-01b` (Spec), `Gate-02` (Architecture/ADR), `Gate-03` (Plan), `Gate-Sec` (Active Security/Strix), `Gate-04` (Release/Push), and `Gate-05` (Rule Evolution).
4. **Security Guardrails ([`core/rules/security-guardrails.md`](./core/rules/security-guardrails.md)):**
   - Never commit or echo secrets, tokens, or private keys. Never run active security scans without `Gate-Sec` approval.

## 2. Canonical Stage Runbooks (`workflows/`)
- **Stage 1 (Phases 1–3):** [`workflows/01-discovery-and-grill-me.md`](./workflows/01-discovery-and-grill-me.md)
- **Stage 2 (Phases 4–5):** [`workflows/02-specification-and-adr.md`](./workflows/02-specification-and-adr.md)
- **Stage 3 (Phases 6–8):** [`workflows/03-planning-and-decomposition.md`](./workflows/03-planning-and-decomposition.md)
- **Stage 4 (Phase 9):** [`workflows/04-tdd-and-implementation.md`](./workflows/04-tdd-and-implementation.md)
- **Stage 5 (Phases 10–12):** [`workflows/05-review-qa-and-security.md`](./workflows/05-review-qa-and-security.md)
- **Stage 6 (Phases 13–15):** [`workflows/06-release-and-retrospective.md`](./workflows/06-release-and-retrospective.md)

## 3. Canonical Agent Roles (`agents/`)
{agents_table}

## 4. Registered Skills (`skills/registry.json`)
{skills_table}

## 5. Verification Commands
```bash
python scripts/sync_adapters.py --check
python scripts/validate.py
python -m unittest discover -s tests -v
```
"""

    # 2. Root CLAUDE.md (Claude Code)
    files["CLAUDE.md"] = f"""<!-- AUTO-GENERATED BY scripts/sync_adapters.py | Canonical Digest: {digest} -->
# Claude Code Instructions (`CLAUDE.md`)

This project uses the **AI Engineering Framework**.
Read and follow [`AGENTS.md`](./AGENTS.md) and [`core/rules/engineering-principles.md`](./core/rules/engineering-principles.md) as the single canonical source of truth.

## Quick Routing for Claude Code
- **Core Rules:** [`core/rules/engineering-principles.md`](./core/rules/engineering-principles.md), [`core/rules/human-approval-gates.md`](./core/rules/human-approval-gates.md), [`core/rules/security-guardrails.md`](./core/rules/security-guardrails.md)
- **Claude Subagents:** Configured in `adapters/claude-code/agents/` (installed into `.claude/agents/` via `bootstrap.py`)
- **Claude Slash Commands:** Configured in `adapters/claude-code/commands/` (installed into `.claude/commands/`)
- **Validation Command:** `python scripts/validate.py`
"""

    # 3. Root GEMINI.md (Google Antigravity & Gemini CLI)
    files["GEMINI.md"] = f"""<!-- AUTO-GENERATED BY scripts/sync_adapters.py | Canonical Digest: {digest} -->
# Google Antigravity & Gemini CLI Instructions (`GEMINI.md`)

This repository is governed by the **AI Engineering Framework**.
Follow [`AGENTS.md`](./AGENTS.md) and [`core/rules/engineering-principles.md`](./core/rules/engineering-principles.md) as the canonical source of truth.

## Platform Integration Notes
- **Google Antigravity:**
  - Use `graphify` (`graphify query`, `graphify update .`) when exploring architecture or reviewing diffs.
  - Delegate isolated research to the `research` subagent and UI verification to the `browser` subagent (`Model="flash"`).
  - Respect all human approval gates (`Gate-01a` through `Gate-05`) defined in [`core/rules/human-approval-gates.md`](./core/rules/human-approval-gates.md).
- **Gemini CLI:**
  - Stage workflow commands are available in `adapters/gemini-cli/commands/workflow.toml` (installed into `.gemini/commands/workflow.toml`).
- **Validation Command:** `python scripts/validate.py`
"""

    # 4. GitHub Copilot (.github/copilot-instructions.md & adapters/copilot/*)
    files[".github/copilot-instructions.md"] = f"""<!-- AUTO-GENERATED BY scripts/sync_adapters.py | Canonical Digest: {digest} -->
# GitHub Copilot Workspace Instructions

Follow [`AGENTS.md`](../AGENTS.md) and [`core/rules/engineering-principles.md`](../core/rules/engineering-principles.md) as the canonical engineering workflow for this repository.

## Mandatory Guardrails
1. **Spec & ADR First:** Do not generate feature implementation code until `docs/specs/03-specification.md` and required ADRs (`docs/adr/`) exist and are approved.
2. **TDD Cycle:** Write failing unit tests first (`Phase 9`), then minimal passing code, then refactor.
3. **Human Gates:** Pause for user approval before adding dependencies (`Gate-02`), running active security scans (`Gate-Sec`), or publishing releases (`Gate-04`).
4. **Zero Secrets:** Never emit hardcoded credentials, tokens, or private keys.
5. **Validation:** Run `python scripts/validate.py` and `python -m unittest discover -s tests -v` before completing changes.
"""

    files["adapters/copilot/framework.instructions.md"] = f"""---
applyTo: "**/*"
description: "AI Engineering Framework canonical rules for GitHub Copilot"
---
<!-- AUTO-GENERATED BY scripts/sync_adapters.py | Canonical Digest: {digest} -->
Follow all rules in [`AGENTS.md`](../../AGENTS.md), [`core/rules/engineering-principles.md`](../../core/rules/engineering-principles.md), and [`core/rules/security-guardrails.md`](../../core/rules/security-guardrails.md).
"""

    files["adapters/copilot/grill-me.prompt.md"] = """---
mode: "agent"
description: "Execute Phase 1 & Phase 2 (Grill Me) requirement clarification"
---
Read `workflows/01-discovery-and-grill-me.md` and `skills/core/grill-me/SKILL.md`.
Create `docs/specs/01-discovery-brief.md` and ask 3-5 batched clarifying questions with `(Recommended)` defaults before writing any code.
"""

    files["adapters/copilot/code-reviewer.agent.md"] = """---
description: "Independent Phase 10 Code & Architecture Reviewer"
tools: ["read_file", "run_command"]
---
Act as `code-reviewer` defined in `agents/code-reviewer.md`.
Inspect `git diff` against `docs/specs/03-specification.md`, `docs/adr/`, and `quality/code-review-rubric.md`.
Write findings to `.framework-state/10-review-report.md`. Do not modify production source files.
"""

    # 5. Google Antigravity Adapter (adapters/antigravity/* and root .agents/*)
    agy_rule_content = f"""---
trigger: always_on
---
<!-- AUTO-GENERATED BY scripts/sync_adapters.py | Canonical Digest: {digest} -->
# Antigravity Workspace Rule — AI Engineering Framework

Follow [`AGENTS.md`](../../../AGENTS.md) and [`core/rules/engineering-principles.md`](../../../core/rules/engineering-principles.md).
- Enforce `Gate-01a`, `Gate-01b`, `Gate-02`, `Gate-03`, `Gate-Sec`, `Gate-04`, and `Gate-05` from [`core/rules/human-approval-gates.md`](../../../core/rules/human-approval-gates.md).
- Write phase handoff packets to `.framework-state/handoffs/` per [`core/rules/context-handoff-protocol.md`](../../../core/rules/context-handoff-protocol.md).
- Validate changes with `python scripts/validate.py`.
"""
    files["adapters/antigravity/rules/framework-core.md"] = agy_rule_content
    files[".agents/rules/framework-core.md"] = agy_rule_content.replace("../../../", "../../")

    agy_skills_json = json.dumps(
        {
            "entries": [
                {"path": "skills/core"},
                {"path": "skills/optional/communication"},
                {"path": "skills/optional/context-engineering"},
                {"path": "skills/optional/agent-architecture"},
                {"path": "skills/optional/frontend-design"},
            ]
        },
        indent=2,
    ) + "\n"
    files["adapters/antigravity/skills.json"] = agy_skills_json
    files[".agents/skills.json"] = agy_skills_json

    files["adapters/antigravity/hooks.json"] = json.dumps(
        {
            "description": "Google Antigravity lifecycle hooks template for AI Engineering Framework",
            "hooks": {
                "preCommit": {
                    "command": "python scripts/validate.py",
                    "description": "Validate schemas, adapters, links, and secret patterns before commit",
                }
            },
        },
        indent=2,
    ) + "\n"

    # 6. Claude Code Adapter (adapters/claude-code/*)
    files["adapters/claude-code/settings.json"] = json.dumps(
        {
            "description": "Claude Code workspace settings template for AI Engineering Framework",
            "permissions": {
                "allow": [
                    "Bash(python scripts/validate.py*)",
                    "Bash(python scripts/sync_adapters.py*)",
                    "Bash(python -m unittest*)",
                    "Bash(graphify *)",
                ],
                "deny": [
                    "Bash(git push --force*)",
                    "Bash(rm -rf /*)",
                ],
            },
        },
        indent=2,
    ) + "\n"

    files["adapters/claude-code/commands/grill-me.md"] = """---
description: "Run Phase 1 & Phase 2 (Grill Me) requirement clarification"
---
Follow `workflows/01-discovery-and-grill-me.md` and `skills/core/grill-me/SKILL.md`.
Apply this to the user's feature request and pause at `Gate-01a` for answers.
"""

    files["adapters/claude-code/commands/validate-framework.md"] = """---
description: "Run AI Engineering Framework validation, adapter sync check, and unit tests"
---
Execute `python scripts/sync_adapters.py --check`, `python scripts/validate.py`, and `python -m unittest discover -s tests -v`. Report the exact exit codes and results.
"""

    files["adapters/claude-code/agents/code-reviewer.md"] = """---
name: framework-code-reviewer
description: "Independent Phase 10 Code Reviewer enforcing spec traceability, ADRs, and anti-slop rules"
subagent: true
mainAgent: false
tools: [read_file, write_file, run_command]
---
Follow the canonical role specification in `agents/code-reviewer.md` and rubric in `quality/code-review-rubric.md`.
Inspect the current diff and write `.framework-state/10-review-report.md`. Never edit production source files.
"""

    # 7. OpenAI Codex Adapter (adapters/codex/*)
    files["adapters/codex/config.toml"] = f"""# AUTO-GENERATED BY scripts/sync_adapters.py | Canonical Digest: {digest}
# OpenAI Codex workspace configuration template (.codex/config.toml)

approval_policy = "on-request"
sandbox_mode = "workspace-write"

# Optional MCP servers can be enabled below using environment variable placeholders:
# [mcp_servers.playwright]
# command = "npx"
# args = ["-y", "@playwright/mcp@latest"]
"""

    # 8. Gemini CLI Adapter (adapters/gemini-cli/*)
    files["adapters/gemini-cli/settings.json"] = json.dumps(
        {
            "description": "Gemini CLI workspace settings template for AI Engineering Framework",
            "contextFileName": ["GEMINI.md", "AGENTS.md"],
        },
        indent=2,
    ) + "\n"

    files["adapters/gemini-cli/commands/workflow.toml"] = f"""# AUTO-GENERATED BY scripts/sync_adapters.py | Canonical Digest: {digest}
description = "Execute the canonical AI Engineering Framework workflow stage"
prompt = \"\"\"
Read AGENTS.md and docs/WORKFLOW.md.
Check .framework-state/manifest.json (if present) to identify the current phase, execute the corresponding runbook in workflows/, and pause at any required Human Approval Gate (Gate-01a through Gate-05).
\"\"\"
"""

    return files


def sync_adapters(root: Path, check_only: bool = False) -> Tuple[bool, List[str]]:
    """Synchronize or check adapter files against canonical sources."""
    expected = generate_expected_files(root)
    drifted: List[str] = []
    updated: List[str] = []

    for rel_path, expected_content in sorted(expected.items()):
        target = root / Path(rel_path)
        normalized_expected = expected_content.replace("\r\n", "\n")
        if target.exists():
            current_content = target.read_text(encoding="utf-8").replace("\r\n", "\n")
            if current_content == normalized_expected:
                continue
        drifted.append(rel_path)
        if not check_only:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(normalized_expected, encoding="utf-8", newline="\n")
            updated.append(rel_path)

    if check_only:
        return (len(drifted) == 0), drifted
    return True, updated


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Synchronize platform adapters from canonical sources.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="Framework repository root path")
    parser.add_argument("--check", action="store_true", help="Check if adapters are in sync without modifying files")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    ok, paths = sync_adapters(root, check_only=args.check)
    if args.check:
        if ok:
            print("SYNC_CHECK: PASS (All platform adapters match canonical sources)")
            return 0
        print("SYNC_CHECK: FAIL (Drifted or missing adapter files):")
        for p in paths:
            print(f"  - {p}")
        return 1

    print(f"SYNC_WRITE: PASS ({len(paths)} adapter file(s) written/updated)")
    for p in paths:
        print(f"  + {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
