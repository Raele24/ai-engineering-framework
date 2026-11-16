#!/usr/bin/env python3
"""Validate AI Engineering Framework integrity in 'framework', 'consumer', or 'auto' mode.

Modes:
- framework: Validates the upstream AI Engineering Framework authoring repository.
- consumer:  Validates an installed consumer project bootstrapped by scripts/bootstrap.py.
- auto:      Detects repository type via reliable markers (PROJECT_CHARTER.md + scripts/bootstrap.py
             vs project.framework.json / .framework-lock.json / .framework-state/manifest.json).

Usage:
    python scripts/validate.py
    python scripts/validate.py --mode consumer --root /path/to/consumer
    python scripts/validate.py --mode framework --json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Dict, List, Set, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
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
    "scripts/preflight.py",
]

REQUIRED_CONSUMER_FILES = [
    "project.framework.json",
    ".framework-lock.json",
    ".framework-state/manifest.json",
    "core/rules/engineering-principles.md",
    "core/rules/context-handoff-protocol.md",
    "core/rules/human-approval-gates.md",
    "core/rules/security-guardrails.md",
    "core/schemas/agent-role.schema.json",
    "core/schemas/skill-frontmatter.schema.json",
    "core/schemas/handoff-packet.schema.json",
    "core/schemas/framework-config.schema.json",
    "skills/registry.json",
    "scripts/validate.py",
]

CONSUMER_PLATFORM_FILES: Dict[str, List[str]] = {
    "antigravity": [
        "GEMINI.md",
        "AGENTS.md",
        ".agents/rules/framework-core.md",
        ".agents/skills.json",
        "adapters/antigravity/hooks.json",
    ],
    "copilot": [
        "AGENTS.md",
        ".github/copilot-instructions.md",
        ".github/instructions/framework.instructions.md",
        ".github/prompts/grill-me.prompt.md",
        ".github/agents/code-reviewer.agent.md",
    ],
    "claude-code": [
        "CLAUDE.md",
        "AGENTS.md",
        ".claude/settings.json",
        ".claude/commands/grill-me.md",
        ".claude/commands/validate-framework.md",
        ".claude/agents/framework-code-reviewer.md",
    ],
    "codex": [
        "AGENTS.md",
        ".codex/config.toml",
    ],
    "gemini-cli": [
        "GEMINI.md",
        "AGENTS.md",
        ".gemini/settings.json",
        ".gemini/commands/workflow.toml",
    ],
}

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

REQUIRED_MANIFEST_KEYS = {
    "schema_version",
    "project_name",
    "framework_version",
    "workflow_profile",
    "current_phase",
    "status",
    "completed_phases",
}

REQUIRED_HANDOFF_KEYS = {
    "schema_version",
    "phase_number",
    "phase_slug",
    "status",
    "producer_role",
    "next_role",
    "input_artifacts",
    "output_artifacts",
}

REQUIRED_CONSUMER_CONFIG_KEYS = {
    "frameworkVersion",
    "projectName",
    "workflowProfile",
    "enabledPlatforms",
    "optionalSkillPacks",
    "qualityGates",
    "security",
    "paths",
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

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
AGENTS_MD_SKILL_ROW_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`[^`]+`\s*\|\s*`[^`]+`\s*\|\s*\[`([^`]+)`\]", re.MULTILINE)


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


def detect_validation_mode(root: Path) -> str:
    """Detect whether root is the upstream 'framework' repository or a 'consumer' project."""
    root = root.resolve()
    if (root / "PROJECT_CHARTER.md").exists() and (root / "scripts" / "bootstrap.py").exists():
        return "framework"
    if (
        (root / "project.framework.json").exists()
        or (root / ".framework-lock.json").exists()
        or (root / ".framework-state" / "manifest.json").exists()
    ):
        return "consumer"
    return "framework"


def check_required_files(root: Path, mode: str = "framework") -> List[str]:
    errors: List[str] = []
    req_list = REQUIRED_FOUNDATION_FILES if mode == "framework" else REQUIRED_CONSUMER_FILES
    for rel in req_list:
        if not (root / Path(rel)).exists():
            errors.append(f"Missing required file: {rel}")
    if mode == "consumer" and not (root / ".framework-state" / "handoffs").is_dir():
        errors.append("Missing required directory: .framework-state/handoffs")
    return errors


def check_consumer_state(root: Path) -> List[str]:
    """Validate consumer project configuration, .framework-state/manifest.json, and handoff packets."""
    errors: List[str] = []

    # 1. project.framework.json
    cfg_path = root / "project.framework.json"
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            missing_cfg = REQUIRED_CONSUMER_CONFIG_KEYS - set(cfg.keys())
            if missing_cfg:
                errors.append(f"project.framework.json: Missing required keys: {sorted(missing_cfg)}")
        except Exception as exc:
            errors.append(f"project.framework.json: Invalid JSON ({exc})")

    # 2. .framework-lock.json
    lock_path = root / ".framework-lock.json"
    if lock_path.exists():
        try:
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            for k in ("framework_version", "platforms", "optional_packs", "managed_files"):
                if k not in lock:
                    errors.append(f".framework-lock.json: Missing key '{k}'")
        except Exception as exc:
            errors.append(f".framework-lock.json: Invalid JSON ({exc})")

    # 3. .framework-state/manifest.json
    manifest_path = root / ".framework-state" / "manifest.json"
    if not manifest_path.exists():
        errors.append("Missing required consumer state file: .framework-state/manifest.json")
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            missing_man = REQUIRED_MANIFEST_KEYS - set(manifest.keys())
            if missing_man:
                errors.append(f".framework-state/manifest.json: Missing required keys: {sorted(missing_man)}")
            completed = manifest.get("completed_phases", [])
            if not isinstance(completed, list):
                errors.append(".framework-state/manifest.json: 'completed_phases' must be a list")
            else:
                for entry in completed:
                    if isinstance(entry, dict) and entry.get("handoff_file"):
                        hf_rel = str(entry["handoff_file"])
                        if not (root / Path(hf_rel)).exists():
                            errors.append(
                                f".framework-state/manifest.json references missing handoff file: {hf_rel}"
                            )
        except Exception as exc:
            errors.append(f".framework-state/manifest.json: Invalid JSON ({exc})")

    # 4. .framework-state/handoffs/*.json
    handoffs_dir = root / ".framework-state" / "handoffs"
    if handoffs_dir.is_dir():
        for hf_path in sorted(handoffs_dir.glob("*.json")):
            rel = hf_path.relative_to(root).as_posix()
            try:
                hf = json.loads(hf_path.read_text(encoding="utf-8"))
                missing_hf = REQUIRED_HANDOFF_KEYS - set(hf.keys())
                if missing_hf:
                    errors.append(f"{rel}: Missing required handoff keys: {sorted(missing_hf)}")
            except Exception as exc:
                errors.append(f"{rel}: Invalid JSON ({exc})")

    return errors


def check_json_files(root: Path) -> List[str]:
    errors: List[str] = []
    skip_dirs = {".git", "node_modules", "graphify-out", "dist", ".angular", "bin", "obj", "__pycache__"}
    for json_path in sorted(root.rglob("*.json")):
        if any(part in skip_dirs for part in json_path.parts):
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

    known_agent_names = {p.stem for p in agent_files}
    registered_skills: Set[str] = set()
    reg_path = root / "skills" / "registry.json"
    if reg_path.exists():
        try:
            reg_data = json.loads(reg_path.read_text(encoding="utf-8"))
            registered_skills = {str(s.get("name", "")) for s in reg_data.get("skills", [])}
        except Exception:
            pass

    for path in agent_files:
        rel = path.relative_to(root).as_posix()
        meta = parse_simple_frontmatter(path.read_text(encoding="utf-8"))
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

        req_skills = meta.get("required_skills", [])
        if isinstance(req_skills, list) and registered_skills:
            for sk in req_skills:
                if str(sk) not in registered_skills:
                    errors.append(f"{rel}: required_skills references uninstalled/unregistered skill '{sk}'")

        targets = meta.get("delegation_targets", [])
        if isinstance(targets, list):
            for tgt in targets:
                if str(tgt) not in known_agent_names:
                    errors.append(f"{rel}: delegation_targets references unknown agent '{tgt}'")

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

    skills_list = registry.get("skills", [])
    declared_total = registry.get("total_skills")
    if isinstance(declared_total, int) and declared_total != len(skills_list):
        errors.append(
            f"skills/registry.json total_skills ({declared_total}) does not match skills count ({len(skills_list)})"
        )

    registered_by_name: Dict[str, Dict[str, object]] = {}
    for entry in skills_list:
        name = str(entry.get("name", ""))
        skill_rel = str(entry.get("path", ""))
        registered_by_name[name] = entry
        skill_path = root / Path(skill_rel)
        if not skill_path.exists():
            errors.append(f"skills/registry.json references non-existent path: {skill_rel}")
        upstream_rel = entry.get("upstream_preserved_path")
        if upstream_rel and not (root / Path(str(upstream_rel))).exists():
            errors.append(f"skills/registry.json references missing upstream snapshot: {upstream_rel}")

    discovered_skills = sorted((root / "skills").rglob("SKILL.md")) if (root / "skills").exists() else []
    if not discovered_skills:
        errors.append("No SKILL.md files found under skills/")

    for skill_file in discovered_skills:
        rel = skill_file.relative_to(root).as_posix()
        folder_name = skill_file.parent.name
        meta = parse_simple_frontmatter(skill_file.read_text(encoding="utf-8"))
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

    # Verify AGENTS.md skill routing table consistency (if AGENTS.md exists and has standard table)
    agents_md_path = root / "AGENTS.md"
    if agents_md_path.exists():
        agents_md_text = agents_md_path.read_text(encoding="utf-8")
        if "## 4. Registered Skills" in agents_md_text:
            table_skills = {m.group(1) for m in AGENTS_MD_SKILL_ROW_RE.finditer(agents_md_text)}
            uninstalled_in_table = table_skills - set(registered_by_name.keys())
            if uninstalled_in_table:
                errors.append(
                    f"AGENTS.md references skills not in skills/registry.json: {sorted(uninstalled_in_table)}"
                )

    # Verify .agents/skills.json entries exist on disk
    agy_skills_path = root / ".agents" / "skills.json"
    if agy_skills_path.exists():
        try:
            agy_data = json.loads(agy_skills_path.read_text(encoding="utf-8"))
            for item in agy_data.get("entries", []):
                entry_rel = str(item.get("path", ""))
                if entry_rel and not (root / Path(entry_rel)).exists():
                    errors.append(f".agents/skills.json references missing directory: {entry_rel}")
        except Exception as exc:
            errors.append(f".agents/skills.json parse error: {exc}")

    return errors


def check_adapter_sync(root: Path, mode: str = "framework") -> List[str]:
    if mode == "framework":
        if str(SCRIPT_DIR) not in sys.path:
            sys.path.insert(0, str(SCRIPT_DIR))
        import sync_adapters  # noqa: E402

        ok, drifted = sync_adapters.sync_adapters(root, check_only=True)
        if not ok:
            return [f"Platform adapter out of sync with canonical source: {p}" for p in drifted]
        return []

    # Consumer mode: check enabled platforms in project.framework.json
    errors: List[str] = []
    cfg_path = root / "project.framework.json"
    enabled_platforms = ["antigravity"]
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            if isinstance(cfg.get("enabledPlatforms"), list):
                enabled_platforms = [str(p) for p in cfg["enabledPlatforms"]]
        except Exception:
            pass

    for plat in enabled_platforms:
        for req_rel in CONSUMER_PLATFORM_FILES.get(plat, []):
            if not (root / Path(req_rel)).exists():
                errors.append(f"Missing consumer adapter file for platform '{plat}': {req_rel}")
    return errors


def check_markdown_links(root: Path) -> List[str]:
    errors: List[str] = []
    root_resolved = root.resolve()

    md_files: List[Path] = [
        root / "README.md",
        root / "PROJECT_CHARTER.md",
        root / "AGENTS.md",
        root / "CLAUDE.md",
        root / "GEMINI.md",
    ]
    for sub in ("docs", "workflows", ".agents", ".github", ".claude", "adapters"):
        sub_dir = root / sub
        if sub_dir.exists():
            md_files.extend(sorted(sub_dir.rglob("*.md")))

    seen: Set[Path] = set()
    for md_path in md_files:
        if not md_path.exists() or md_path in seen:
            continue
        seen.add(md_path)
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
            if not resolved.is_relative_to(root_resolved):
                errors.append(
                    f"{rel_source}: Relative link escapes repository root -> '{target_raw}'"
                )
            elif not resolved.exists():
                errors.append(f"{rel_source}: Broken relative link -> '{target_raw}'")
    return errors


def check_secrets(root: Path) -> List[str]:
    errors: List[str] = []
    exempt_rel_paths = {
        "security/pre-commit-secrets.md",
        "scripts/validate.py",
        "tests/test_framework.py",
    }
    skip_dirs = {".git", "node_modules", "graphify-out", "dist", ".angular", "bin", "obj", "__pycache__"}
    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        if any(part in skip_dirs for part in file_path.parts):
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


def run_validation(root: Path, mode: str = "auto") -> Tuple[bool, Dict[str, List[str]]]:
    effective_mode = detect_validation_mode(root) if mode == "auto" else mode
    if effective_mode not in {"framework", "consumer"}:
        raise ValueError(f"Unsupported validation mode '{mode}'. Choose from: auto, framework, consumer")

    report: Dict[str, List[str]] = {
        "required_files": check_required_files(root, mode=effective_mode),
        "json_syntax": check_json_files(root),
        "agents_frontmatter": check_agents_frontmatter(root),
        "skills_and_registry": check_skills_and_registry(root),
        "adapter_sync": check_adapter_sync(root, mode=effective_mode),
        "markdown_links": check_markdown_links(root),
        "secret_scan": check_secrets(root),
    }
    if effective_mode == "consumer":
        report["consumer_state"] = check_consumer_state(root)

    all_passed = all(len(errs) == 0 for errs in report.values())
    return all_passed, report


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate AI Engineering Framework integrity.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="Repository root path")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["auto", "framework", "consumer"],
        default="auto",
        help="Validation mode: framework (upstream repo), consumer (bootstrapped project), or auto",
    )
    parser.add_argument("--json", action="store_true", help="Emit validation report as JSON")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    effective_mode = detect_validation_mode(root) if args.mode == "auto" else args.mode
    passed, report = run_validation(root, mode=effective_mode)
    total_errors = sum(len(v) for v in report.values())

    if args.json:
        print(
            json.dumps(
                {
                    "mode": effective_mode,
                    "status": "PASS" if passed else "FAIL",
                    "total_errors": total_errors,
                    "checks": report,
                },
                indent=2,
            )
        )
        return 0 if passed else 1

    print(f"=== AI Engineering Framework Validation [{effective_mode.upper()}] ({root}) ===")
    for check_name, errs in report.items():
        status_str = "PASS" if not errs else f"FAIL ({len(errs)} error(s))"
        print(f"  [{status_str}] {check_name}")
        for err in errs:
            print(f"      - {err}")

    print(f"\nOVERALL STATUS: {'PASS' if passed else 'FAIL'} ({total_errors} total error(s))")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
