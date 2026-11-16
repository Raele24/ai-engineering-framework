#!/usr/bin/env python3
"""Validate AI Engineering Framework integrity, schemas, frontmatter, links, adapters, and secret hygiene.

Checks performed (using only Python 3.10+ standard library):
1. Required repository directories and foundation files exist.
2. All JSON files parse cleanly and required schema keys exist.
3. All canonical agent role definitions (agents/*.md) have valid frontmatter matching core/schemas/agent-role.schema.json.
4. All skill definitions (skills/*/*/SKILL.md) have valid frontmatter matching core/schemas/skill-frontmatter.schema.json and match skills/registry.json.
5. Platform adapters are 100% synchronized with canonical sources (via sync_adapters.sync_adapters(check_only=True)).
6. Relative Markdown links in README.md, PROJECT_CHARTER.md, and docs/*.md resolve to existing files.
7. Working tree files contain zero leaked private keys or high-entropy API token signatures.

Usage:
    python scripts/validate.py
    python scripts/validate.py --root /path/to/repo --json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Dict, List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import sync_adapters  # noqa: E402

REPO_ROOT = SCRIPT_DIR.parent

REQUIRED_FOUNDATION_FILES = [
    "PROJECT_CHARTER.md",
    "README.md",
    "LICENSE",
    ".gitignore",
    ".gitattributes",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".github/copilot-instructions.md",
    "docs/ENVIRONMENT_AUDIT.md",
    "docs/IMPLEMENTATION_PLAN.md",
    "docs/ARCHITECTURE.md",
    "docs/WORKFLOW.md",
    "docs/GETTING_STARTED.md",
    "docs/INSTALLATION.md",
    "docs/CONFIGURATION.md",
    "docs/CONTRIBUTING.md",
    "docs/VERSIONING.md",
    "docs/SECURITY.md",
    "docs/ROADMAP.md",
    "docs/SKILLS_RESEARCH_REPORT.md",
    "docs/SKILL_COMPATIBILITY_MATRIX.md",
    "docs/TOKEN_OPTIMIZATION.md",
    "docs/SKILL_INSTALLATION_GUIDE.md",
    "docs/RUNTIME_SKILLS_VALIDATION.md",
    "core/rules/engineering-principles.md",
    "core/rules/context-handoff-protocol.md",
    "core/rules/human-approval-gates.md",
    "core/rules/security-guardrails.md",
    "core/schemas/agent-role.schema.json",
    "core/schemas/skill-frontmatter.schema.json",
    "core/schemas/handoff-packet.schema.json",
    "core/schemas/framework-config.schema.json",
    "skills/registry.json",
    "scripts/bootstrap.py",
    "scripts/validate.py",
    "scripts/sync_adapters.py",
]

REQUIRED_AGENT_KEYS = {
    "name",
    "title",
    "description",
    "version",
    "phases",
    "allowed_tools",
    "required_skills",
    "delegation_targets",
    "approval_gates",
}

REQUIRED_SKILL_KEYS = {
    "name",
    "description",
    "version",
    "source",
    "license",
    "category",
    "tier",
    "platforms",
    "requires_tools",
    "dependencies",
    "security_scope",
}

VALID_SKILL_TIERS = {
    "core",
    "optional-communication",
    "optional-context",
    "optional-agent-architecture",
    "optional-frontend",
    "optional-growth",
}

VALID_SKILL_CATEGORIES = {
    "core-sdlc",
    "token-optimization",
    "context-engineering",
    "ui-ux-design",
    "agent-architecture",
    "codebase-intelligence",
    "seo-growth",
}

VALID_LICENSES = {
    "Apache-2.0",
    "MIT",
    "BSD-3-Clause",
}

VALID_PLATFORMS = {
    "antigravity",
    "copilot",
    "claude-code",
    "codex",
    "gemini-cli",
}

VALID_SECURITY_SCOPES = {
    "read-only",
    "workspace-write",
    "network-external",
}

SECRET_PATTERNS = [
    ("RSA_PRIVATE_KEY", re.compile(r"-----BEGIN RSA PRIVATE KEY-----")),
    ("OPENSSH_PRIVATE_KEY", re.compile(r"-----BEGIN OPENSSH PRIVATE KEY-----")),
    ("GITHUB_PAT", re.compile(r"ghp_[A-Za-z0-9]{36}")),
    ("GITHUB_FINE_PAT", re.compile(r"github_pat_[A-Za-z0-9_]{82}")),
    ("OPENAI_KEY", re.compile(r"sk-proj-[A-Za-z0-9_-]{40,}")),
    ("ANTHROPIC_KEY", re.compile(r"sk-ant-api03-[A-Za-z0-9_-]{80,}")),
    ("AWS_ACCESS_KEY", re.compile(r"AKIA[0-9A-Z]{16}")),
]

MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)


def check_required_files(root: Path) -> List[str]:
    errors: List[str] = []
    for rel in REQUIRED_FOUNDATION_FILES:
        if not (root / Path(rel)).exists():
            errors.append(f"Missing required file: {rel}")
    return errors


def check_json_files(root: Path) -> List[str]:
    errors: List[str] = []
    for json_path in sorted(root.rglob("*.json")):
        if ".git" in json_path.parts or "node_modules" in json_path.parts or "graphify-out" in json_path.parts:
            continue
        rel = json_path.relative_to(root).as_posix()
        try:
            json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"Invalid JSON in {rel}: {exc}")
    return errors


def check_agents_frontmatter(root: Path) -> List[str]:
    errors: List[str] = []
    agents_dir = root / "agents"
    if not agents_dir.exists():
        return ["Missing agents/ directory"]
    agent_files = sorted(agents_dir.glob("*.md"))
    if not agent_files:
        return ["No agent role definitions found in agents/"]

    for path in agent_files:
        rel = path.relative_to(root).as_posix()
        meta = sync_adapters.parse_simple_frontmatter(path.read_text(encoding="utf-8"))
        if not meta:
            errors.append(f"{rel}: Missing YAML frontmatter")
            continue
        missing = REQUIRED_AGENT_KEYS - set(meta.keys())
        if missing:
            errors.append(f"{rel}: Missing frontmatter keys: {sorted(missing)}")
        expected_name = path.stem
        if meta.get("name") != expected_name:
            errors.append(f"{rel}: frontmatter name '{meta.get('name')}' does not match filename '{expected_name}'")
        phases = meta.get("phases")
        if not isinstance(phases, list) or not phases or not all(isinstance(p, int) and 1 <= p <= 15 for p in phases):
            errors.append(f"{rel}: 'phases' must be a non-empty list of integers between 1 and 15")
    return errors


def check_skills_and_registry(root: Path) -> List[str]:
    errors: List[str] = []
    registry_path = root / "skills" / "registry.json"
    if not registry_path.exists():
        return ["Missing skills/registry.json"]

    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"skills/registry.json parse error: {exc}"]

    registered_by_name: Dict[str, Dict[str, object]] = {}
    for entry in registry.get("skills", []):
        name = str(entry.get("name", ""))
        skill_rel = str(entry.get("path", ""))
        registered_by_name[name] = entry
        skill_path = root / Path(skill_rel)
        if not skill_path.exists():
            errors.append(f"skills/registry.json references non-existent path: {skill_rel}")
        upstream_rel = entry.get("upstream_preserved_path")
        if upstream_rel and not (root / Path(str(upstream_rel))).exists():
            errors.append(f"skills/registry.json references missing upstream snapshot: {upstream_rel}")

    discovered_skills = sorted((root / "skills").rglob("SKILL.md"))
    if not discovered_skills:
        errors.append("No SKILL.md files found under skills/")

    for skill_file in discovered_skills:
        rel = skill_file.relative_to(root).as_posix()
        folder_name = skill_file.parent.name
        meta = sync_adapters.parse_simple_frontmatter(skill_file.read_text(encoding="utf-8"))
        if not meta:
            errors.append(f"{rel}: Missing YAML frontmatter")
            continue
        missing = REQUIRED_SKILL_KEYS - set(meta.keys())
        if missing:
            errors.append(f"{rel}: Missing frontmatter keys: {sorted(missing)}")
        if meta.get("name") != folder_name:
            errors.append(f"{rel}: frontmatter name '{meta.get('name')}' does not match folder '{folder_name}'")
        if meta.get("tier") not in VALID_SKILL_TIERS:
            errors.append(f"{rel}: invalid tier '{meta.get('tier')}'")
        if meta.get("category") not in VALID_SKILL_CATEGORIES:
            errors.append(f"{rel}: invalid category '{meta.get('category')}'")
        if meta.get("license") not in VALID_LICENSES:
            errors.append(f"{rel}: invalid license '{meta.get('license')}'")
        platforms = meta.get("platforms")
        if not isinstance(platforms, list) or not platforms or not set(platforms).issubset(VALID_PLATFORMS):
            errors.append(f"{rel}: invalid platforms list '{platforms}'")
        if meta.get("security_scope") not in VALID_SECURITY_SCOPES:
            errors.append(f"{rel}: invalid security_scope '{meta.get('security_scope')}'")
        if folder_name not in registered_by_name:
            errors.append(f"{rel}: skill '{folder_name}' is not listed in skills/registry.json")

    return errors


def check_adapter_sync(root: Path) -> List[str]:
    ok, drifted = sync_adapters.sync_adapters(root, check_only=True)
    if not ok:
        return [f"Platform adapter out of sync with canonical source: {p}" for p in drifted]
    return []


def check_markdown_links(root: Path) -> List[str]:
    errors: List[str] = []
    md_files = [
        root / "README.md",
        root / "PROJECT_CHARTER.md",
        root / "AGENTS.md",
        root / "CLAUDE.md",
        root / "GEMINI.md",
    ]
    md_files.extend(sorted((root / "docs").rglob("*.md")))
    md_files.extend(sorted((root / "workflows").rglob("*.md")))

    for md_path in md_files:
        if not md_path.exists():
            continue
        rel_source = md_path.relative_to(root).as_posix()
        text_no_code = FENCED_CODE_RE.sub("", md_path.read_text(encoding="utf-8"))
        for match in MD_LINK_RE.finditer(text_no_code):
            target_raw = match.group(1).strip()
            if (
                not target_raw
                or target_raw.startswith("http://")
                or target_raw.startswith("https://")
                or target_raw.startswith("mailto:")
                or target_raw.startswith("#")
                or target_raw.startswith("file://")
                or target_raw.startswith("customization://")
                or target_raw.startswith("conversation://")
            ):
                continue
            target_clean = target_raw.split("#", 1)[0].strip()
            if not target_clean:
                continue
            resolved = (md_path.parent / target_clean).resolve()
            if not resolved.exists():
                errors.append(f"{rel_source}: Broken relative link -> '{target_raw}'")
    return errors


def check_secrets(root: Path) -> List[str]:
    errors: List[str] = []
    exempt_rel_paths = {
        "security/pre-commit-secrets.md",
        "scripts/validate.py",
        "tests/test_framework.py",
    }
    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        if ".git" in file_path.parts or "graphify-out" in file_path.parts or "__pycache__" in file_path.parts:
            continue
        rel = file_path.relative_to(root).as_posix()
        if rel in exempt_rel_paths:
            continue
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for rule_id, regex in SECRET_PATTERNS:
            if regex.search(content):
                errors.append(f"{rel}: Potential leaked secret detected matching rule '{rule_id}'")
    return errors


def run_validation(root: Path) -> Tuple[bool, Dict[str, List[str]]]:
    report: Dict[str, List[str]] = {
        "required_files": check_required_files(root),
        "json_syntax": check_json_files(root),
        "agents_frontmatter": check_agents_frontmatter(root),
        "skills_and_registry": check_skills_and_registry(root),
        "adapter_sync": check_adapter_sync(root),
        "markdown_links": check_markdown_links(root),
        "secret_scan": check_secrets(root),
    }
    all_passed = all(len(errs) == 0 for errs in report.values())
    return all_passed, report


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate AI Engineering Framework integrity.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="Repository root path")
    parser.add_argument("--json", action="store_true", help="Emit validation report as JSON")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    passed, report = run_validation(root)
    total_errors = sum(len(v) for v in report.values())

    if args.json:
        print(
            json.dumps(
                {
                    "status": "PASS" if passed else "FAIL",
                    "total_errors": total_errors,
                    "checks": report,
                },
                indent=2,
            )
        )
        return 0 if passed else 1

    print(f"=== AI Engineering Framework Validation ({root}) ===")
    for check_name, errs in report.items():
        status_str = "PASS" if not errs else f"FAIL ({len(errs)} error(s))"
        print(f"  [{status_str}] {check_name}")
        for err in errs:
            print(f"      - {err}")

    print(f"\nOVERALL STATUS: {'PASS' if passed else 'FAIL'} ({total_errors} total error(s))")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
