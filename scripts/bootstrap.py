#!/usr/bin/env python3
"""Bootstrap or non-destructively update the AI Engineering Framework in a target project.

Key Guarantees:
1. Tier 3 Consumer-Owned Files (project.framework.json, .framework-state/manifest.json, .gitignore,
   docs/specs/, docs/adr/, docs/plans/, README.md) are NEVER overwritten if they already exist.
2. Tier 1 & Tier 2 Framework-Managed Files (core/, agents/, skills/, workflows/, platform adapters)
   are tailored to the consumer's selected optional skill packs and tracked in `.framework-lock.json`.
3. During `--update`, if a user has locally customized a framework-managed file (its current SHA-256 differs
   from the hash recorded in `.framework-lock.json`), the file is preserved and skipped rather than overwritten.

Usage:
    python scripts/bootstrap.py --target /path/to/project --dry-run
    python scripts/bootstrap.py --target /path/to/project --platforms antigravity,copilot,claude-code
    python scripts/bootstrap.py --target /path/to/project --optional-packs communication,context-engineering,design-ui
    python scripts/bootstrap.py --target /path/to/project --optional-packs none --stacks dotnet,node/angular
    python scripts/bootstrap.py --target /path/to/project --update
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import posixpath
import re
import sys
from typing import Dict, List, Set, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import preflight  # noqa: E402
import sync_adapters  # noqa: E402

FRAMEWORK_ROOT = SCRIPT_DIR.parent
FRAMEWORK_VERSION = "0.3.0"
LOCKFILE_NAME = ".framework-lock.json"

ALL_PLATFORMS = ["antigravity", "copilot", "claude-code", "codex", "gemini-cli"]

CORE_MANAGED_GLOBS = [
    "core/rules/*.md",
    "core/schemas/*.json",
    "agents/*.md",
    "skills/core/*/*.md",
    "workflows/*.md",
    "quality/*.md",
    "security/*.md",
    "security/*.yaml",
    "templates/*.md",
    "templates/*.json",
    "templates/stacks/*.gitignore",
    "scripts/validate.py",
    "scripts/preflight.py",
]

PLATFORM_ADAPTER_MAPPINGS: Dict[str, List[Tuple[str, str]]] = {
    "antigravity": [
        ("GEMINI.md", "GEMINI.md"),
        ("AGENTS.md", "AGENTS.md"),
        ("adapters/antigravity/rules/framework-core.md", ".agents/rules/framework-core.md"),
        ("adapters/antigravity/skills.json", ".agents/skills.json"),
        ("adapters/antigravity/hooks.json", "adapters/antigravity/hooks.json"),
    ],
    "copilot": [
        ("AGENTS.md", "AGENTS.md"),
        (".github/copilot-instructions.md", ".github/copilot-instructions.md"),
        ("adapters/copilot/framework.instructions.md", ".github/instructions/framework.instructions.md"),
        ("adapters/copilot/grill-me.prompt.md", ".github/prompts/grill-me.prompt.md"),
        ("adapters/copilot/code-reviewer.agent.md", ".github/agents/code-reviewer.agent.md"),
    ],
    "claude-code": [
        ("CLAUDE.md", "CLAUDE.md"),
        ("AGENTS.md", "AGENTS.md"),
        ("adapters/claude-code/settings.json", ".claude/settings.json"),
        ("adapters/claude-code/commands/grill-me.md", ".claude/commands/grill-me.md"),
        ("adapters/claude-code/commands/validate-framework.md", ".claude/commands/validate-framework.md"),
        ("adapters/claude-code/agents/code-reviewer.md", ".claude/agents/framework-code-reviewer.md"),
    ],
    "codex": [
        ("AGENTS.md", "AGENTS.md"),
        ("adapters/codex/config.toml", ".codex/config.toml"),
    ],
    "gemini-cli": [
        ("GEMINI.md", "GEMINI.md"),
        ("AGENTS.md", "AGENTS.md"),
        ("adapters/gemini-cli/settings.json", ".gemini/settings.json"),
        ("adapters/gemini-cli/commands/workflow.toml", ".gemini/commands/workflow.toml"),
    ],
}

OPTIONAL_PACK_DIRS: Dict[str, str] = {
    "communication": "skills/optional/communication",
    "context-engineering": "skills/optional/context-engineering",
    "agent-architecture": "skills/optional/agent-architecture",
    "frontend-design": "skills/optional/frontend-design",
    "growth-media": "skills/optional/growth-media",
}

OPTIONAL_PACK_ALIASES: Dict[str, str] = {
    "communication": "communication",
    "context-engineering": "context-engineering",
    "agent-architecture": "agent-architecture",
    "frontend-design": "frontend-design",
    "design-ui": "frontend-design",
    "growth-media": "growth-media",
}

FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
REQUIRED_SKILLS_LINE_RE = re.compile(r"^(required_skills:\s*\[)([^\]]*)(\]\s*)$", re.MULTILINE)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def normalize_optional_packs(raw_packs: List[str]) -> List[str]:
    """Normalize optional pack names (supporting 'design-ui' alias, 'none', and 'all')."""
    cleaned = [p.strip().lower() for p in raw_packs if p.strip()]
    if not cleaned or cleaned == ["none"]:
        return []
    if "all" in cleaned:
        return list(OPTIONAL_PACK_DIRS.keys())

    normalized: List[str] = []
    invalid: List[str] = []
    for item in cleaned:
        if item == "none":
            continue
        mapped = OPTIONAL_PACK_ALIASES.get(item)
        if not mapped:
            invalid.append(item)
        elif mapped not in normalized:
            normalized.append(mapped)
    if invalid:
        allowed = sorted(set(OPTIONAL_PACK_ALIASES.keys()) | {"none", "all"})
        raise ValueError(f"Invalid value(s) for --optional-packs: {invalid}. Allowed: {allowed}")
    return normalized


def rewrite_markdown_relative_links(
    markdown_text: str,
    src_rel_path: str,
    dst_rel_path: str,
) -> str:
    """Rewrite Markdown relative link targets when moving a file from src_rel_path to dst_rel_path.

    Guarantees:
    - Does not modify fenced code blocks, inline code spans, or plain prose outside [label](target).
    - Preserves external URLs (http/https/mailto), URI schemes, anchors (#), and absolute paths.
    - Computes exact relative path from dst directory to target resolved from src directory.
    """
    src_dir = posixpath.dirname(src_rel_path.replace("\\", "/"))
    dst_dir = posixpath.dirname(dst_rel_path.replace("\\", "/"))
    if src_dir == dst_dir:
        return markdown_text

    fenced_blocks: List[str] = []

    def _mask_fenced(match: re.Match[str]) -> str:
        idx = len(fenced_blocks)
        fenced_blocks.append(match.group(0))
        return f"\x00FENCED_{idx}\x00"

    masked = FENCED_CODE_RE.sub(_mask_fenced, markdown_text)

    inline_spans: List[str] = []

    def _mask_inline(match: re.Match[str]) -> str:
        idx = len(inline_spans)
        inline_spans.append(match.group(0))
        return f"\x00INLINE_{idx}\x00"

    masked = INLINE_CODE_RE.sub(_mask_inline, masked)

    def _rewrite_link(match: re.Match[str]) -> str:
        label = match.group(1)
        target_raw = match.group(2).strip()
        if (
            not target_raw
            or target_raw.startswith("http://")
            or target_raw.startswith("https://")
            or target_raw.startswith("mailto:")
            or target_raw.startswith("#")
            or target_raw.startswith("/")
            or target_raw.startswith("file://")
            or target_raw.startswith("customization://")
            or target_raw.startswith("conversation://")
            or re.match(r"^[A-Za-z]:[/\\]", target_raw)
        ):
            return match.group(0)

        path_part, sep, fragment = target_raw.partition("#")
        path_part = path_part.strip()
        if not path_part:
            return match.group(0)

        repo_rel_target = posixpath.normpath(
            posixpath.join(src_dir, path_part) if src_dir else path_part
        )
        new_rel = posixpath.relpath(repo_rel_target, dst_dir if dst_dir else ".")
        if dst_dir == "" and path_part.startswith("./") and not new_rel.startswith("."):
            new_rel = f"./{new_rel}"

        rebuilt_target = f"{new_rel}{sep}{fragment}" if sep else new_rel
        return f"[{label}]({rebuilt_target})"

    rewritten = MD_LINK_RE.sub(_rewrite_link, masked)

    for idx, span in enumerate(inline_spans):
        rewritten = rewritten.replace(f"\x00INLINE_{idx}\x00", span)
    for idx, block in enumerate(fenced_blocks):
        rewritten = rewritten.replace(f"\x00FENCED_{idx}\x00", block)

    return rewritten


def build_filtered_registry(
    framework_root: Path,
    optional_packs: List[str],
) -> Tuple[Dict[str, object], Set[str]]:
    """Build a consumer-specific skills/registry.json containing core + selected optional packs."""
    canonical_reg_path = framework_root / "skills" / "registry.json"
    canonical_reg = json.loads(canonical_reg_path.read_text(encoding="utf-8"))

    allowed_prefixes = ["skills/core/"]
    for pack in optional_packs:
        pack_dir = OPTIONAL_PACK_DIRS.get(pack)
        if pack_dir:
            allowed_prefixes.append(f"{pack_dir}/")

    filtered_skills: List[Dict[str, object]] = []
    installed_names: Set[str] = set()
    for skill in canonical_reg.get("skills", []):
        skill_path = str(skill.get("path", ""))
        if skill.get("tier") == "core" or any(skill_path.startswith(pfx) for pfx in allowed_prefixes):
            filtered_skills.append(dict(skill))
            installed_names.add(str(skill.get("name", "")))

    consumer_reg: Dict[str, object] = {
        "schema_version": canonical_reg.get("schema_version", "2.0.0"),
        "framework_version": FRAMEWORK_VERSION,
        "description": canonical_reg.get("description", ""),
        "installed_optional_packs": list(optional_packs),
        "total_skills": len(filtered_skills),
        "skills": filtered_skills,
    }
    return consumer_reg, installed_names


def filter_agent_required_skills(agent_markdown: str, installed_skills: Set[str]) -> str:
    """Filter required_skills in an agent definition's YAML frontmatter to installed skills only."""
    def _replace_skills(match: re.Match[str]) -> str:
        prefix, inner, suffix = match.group(1), match.group(2), match.group(3)
        raw_items = [item.strip() for item in inner.split(",") if item.strip()]
        kept = [item for item in raw_items if item.strip("\"'") in installed_skills]
        return f"{prefix}{', '.join(kept)}{suffix}"

    return REQUIRED_SKILLS_LINE_RE.sub(_replace_skills, agent_markdown, count=1)


def build_consumer_agents_md(
    framework_root: Path,
    consumer_registry: Dict[str, object],
) -> str:
    """Generate a consumer AGENTS.md whose skill routing table matches the installed skills."""
    agents, _ = sync_adapters.load_canonical_metadata(framework_root)
    agents_table = sync_adapters.build_agents_table(agents)
    skills_table = sync_adapters.build_core_skills_table(consumer_registry)
    digest = sync_adapters.compute_canonical_digest(framework_root)

    return f"""<!-- AUTO-GENERATED BY scripts/bootstrap.py | Canonical Digest: {digest} -->
# AI Engineering Framework — Universal Agent Instructions (`AGENTS.md`)

This repository is governed by the **AI Engineering Framework**. Do not improvise ad-hoc workflows.
All instructions below derive from the canonical source of truth in `core/rules/` and `workflows/`.

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
python scripts/validate.py --mode consumer
```
"""


def build_consumer_antigravity_skills_json(optional_packs: List[str]) -> str:
    """Build .agents/skills.json listing only installed skill directories."""
    entries = [{"path": "skills/core"}]
    for pack in optional_packs:
        pack_dir = OPTIONAL_PACK_DIRS.get(pack)
        if pack_dir:
            entries.append({"path": pack_dir})
    return json.dumps({"entries": entries}, indent=2) + "\n"


def collect_managed_plan_bytes(
    framework_root: Path,
    platforms: List[str],
    optional_packs: List[str],
) -> Dict[str, bytes]:
    """Return mapping of {target_rel_posix_path: content_bytes} for all managed files."""
    plan_bytes: Dict[str, bytes] = {}
    consumer_reg, installed_skill_names = build_filtered_registry(framework_root, optional_packs)

    for pattern in CORE_MANAGED_GLOBS:
        for src in sorted(framework_root.glob(pattern)):
            if src.is_file():
                rel = src.relative_to(framework_root).as_posix()
                if rel.startswith("agents/") and rel.endswith(".md"):
                    raw_text = src.read_text(encoding="utf-8").replace("\r\n", "\n")
                    filtered_text = filter_agent_required_skills(raw_text, installed_skill_names)
                    plan_bytes[rel] = filtered_text.encode("utf-8")
                elif src.suffix in {".md", ".json", ".yaml", ".yml", ".py", ".gitignore", ".toml"}:
                    norm_text = src.read_text(encoding="utf-8").replace("\r\n", "\n")
                    plan_bytes[rel] = norm_text.encode("utf-8")
                else:
                    plan_bytes[rel] = src.read_bytes()

    # Filtered consumer skills/registry.json
    plan_bytes["skills/registry.json"] = (json.dumps(consumer_reg, indent=2) + "\n").encode("utf-8")

    # Selected optional skill pack files
    for pack in optional_packs:
        pack_rel_dir = OPTIONAL_PACK_DIRS.get(pack)
        if pack_rel_dir:
            pack_dir = framework_root / Path(pack_rel_dir)
            if pack_dir.exists():
                for src in sorted(pack_dir.rglob("*")):
                    if src.is_file() and "__pycache__" not in src.parts:
                        rel = src.relative_to(framework_root).as_posix()
                        if src.suffix in {".md", ".json", ".py", ".csv", ".cjs", ".js", ".ts"}:
                            try:
                                norm_text = src.read_text(encoding="utf-8").replace("\r\n", "\n")
                                plan_bytes[rel] = norm_text.encode("utf-8")
                            except UnicodeDecodeError:
                                plan_bytes[rel] = src.read_bytes()
                        else:
                            plan_bytes[rel] = src.read_bytes()

    consumer_agents_md_bytes = build_consumer_agents_md(framework_root, consumer_reg).encode("utf-8")
    consumer_agy_skills_bytes = build_consumer_antigravity_skills_json(optional_packs).encode("utf-8")

    for plat in platforms:
        for src_rel, dst_rel in PLATFORM_ADAPTER_MAPPINGS.get(plat, []):
            if dst_rel == "AGENTS.md":
                plan_bytes[dst_rel] = consumer_agents_md_bytes
                continue
            if dst_rel in {".agents/skills.json", "adapters/antigravity/skills.json"}:
                plan_bytes[dst_rel] = consumer_agy_skills_bytes
                continue

            src = framework_root / Path(src_rel)
            if not src.exists():
                continue

            raw_text = src.read_text(encoding="utf-8").replace("\r\n", "\n")
            if dst_rel.endswith(".md") and src_rel != dst_rel:
                rewritten_text = rewrite_markdown_relative_links(raw_text, src_rel, dst_rel)
                plan_bytes[dst_rel] = rewritten_text.encode("utf-8")
            else:
                plan_bytes[dst_rel] = raw_text.encode("utf-8")

    return plan_bytes


def collect_managed_plan(
    framework_root: Path,
    platforms: List[str],
    optional_packs: List[str],
) -> Dict[str, Path]:
    """Legacy helper returning {target_rel_posix_path: source_abs_path} for callers."""
    canonical_packs = normalize_optional_packs(optional_packs)
    plan_bytes = collect_managed_plan_bytes(framework_root, platforms, canonical_packs)
    return {rel: (framework_root / Path(rel)) for rel in plan_bytes}


def _compose_stack_gitignore(framework_root: Path, stacks: List[str]) -> str:
    sections: List[str] = [
        "# Generated by AI Engineering Framework (scripts/bootstrap.py)",
        ".framework-state/scratch/",
        "graphify-out/",
        "",
    ]
    for st in stacks:
        tpl_path = framework_root / "templates" / "stacks" / f"{st}.gitignore"
        if tpl_path.exists():
            sections.append(tpl_path.read_text(encoding="utf-8").replace("\r\n", "\n").strip())
            sections.append("")
    return "\n".join(sections).rstrip() + "\n"


def bootstrap_project(
    target_dir: Path,
    platforms: List[str],
    profile: str = "standard",
    optional_packs: List[str] | None = None,
    stacks: List[str] | None = None,
    update_mode: bool = False,
    dry_run: bool = False,
    framework_root: Path = FRAMEWORK_ROOT,
) -> Dict[str, List[str]]:
    """Bootstrap or update the framework in target_dir non-destructively."""
    raw_packs = (
        optional_packs
        if optional_packs is not None
        else ["communication", "context-engineering", "agent-architecture"]
    )
    canonical_packs = normalize_optional_packs(raw_packs)
    normalized_stacks = preflight.normalize_stacks(stacks or [])
    target_dir = target_dir.resolve()

    lock_path = target_dir / LOCKFILE_NAME
    existing_lock: Dict[str, object] = {}
    locked_hashes: Dict[str, str] = {}
    if lock_path.exists():
        existing_lock = json.loads(lock_path.read_text(encoding="utf-8"))
        locked_hashes = dict(existing_lock.get("managed_files", {}))

    plan_bytes = collect_managed_plan_bytes(framework_root, platforms, canonical_packs)

    created: List[str] = []
    updated: List[str] = []
    unchanged: List[str] = []
    skipped_modified: List[str] = []

    new_locked_hashes: Dict[str, str] = dict(locked_hashes)

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)
        for sub in [
            "docs/specs",
            "docs/adr",
            "docs/plans",
            "docs/retrospectives",
            ".framework-state/handoffs",
            ".framework-state/scratch",
        ]:
            (target_dir / Path(sub)).mkdir(parents=True, exist_ok=True)

    # If update_mode or optional_packs changed, prune previously managed optional skills that are no longer in plan_bytes
    if not dry_run and locked_hashes:
        for old_rel in list(locked_hashes.keys()):
            if old_rel not in plan_bytes and old_rel.startswith("skills/optional/"):
                old_file = target_dir / Path(old_rel)
                if old_file.exists() and sha256_file(old_file) == locked_hashes[old_rel]:
                    old_file.unlink()
                new_locked_hashes.pop(old_rel, None)

    for dst_rel, src_bytes in sorted(plan_bytes.items()):
        dst_path = target_dir / Path(dst_rel)
        src_hash = sha256_bytes(src_bytes)

        if not dst_path.exists():
            created.append(dst_rel)
            if not dry_run:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                dst_path.write_bytes(src_bytes)
            new_locked_hashes[dst_rel] = src_hash
            continue

        current_hash = sha256_file(dst_path)
        if current_hash == src_hash:
            unchanged.append(dst_rel)
            new_locked_hashes[dst_rel] = src_hash
            continue

        previous_locked_hash = locked_hashes.get(dst_rel)
        if update_mode and previous_locked_hash and current_hash == previous_locked_hash:
            updated.append(dst_rel)
            if not dry_run:
                dst_path.write_bytes(src_bytes)
            new_locked_hashes[dst_rel] = src_hash
        else:
            skipped_modified.append(dst_rel)

    # Tier 3 Consumer-Owned File 1: project.framework.json
    config_rel = "project.framework.json"
    config_path = target_dir / config_rel
    optional_packs_payload = {
        "communication": ["caveman", "rtk-cli"] if "communication" in canonical_packs else [],
        "contextEngineering": (
            [
                "context-optimization",
                "context-compression",
                "filesystem-context",
                "memory-systems",
            ]
            if "context-engineering" in canonical_packs
            else []
        ),
        "agentArchitecture": (
            [
                "multi-agent-patterns",
                "tool-design",
                "evaluation",
                "self-improvement-loops",
            ]
            if "agent-architecture" in canonical_packs
            else []
        ),
        "frontendDesign": (
            [
                "ui-ux-pro-max",
                "angular-developer",
                "angular-new-app",
                "web-design-guidelines",
                "canvas-design",
            ]
            if "frontend-design" in canonical_packs
            else []
        ),
        "growthMedia": (
            [
                "seo-audit",
                "ai-seo",
                "content-strategy",
                "pricing",
                "brand-strategy",
                "video-lens",
                "video-use",
            ]
            if "growth-media" in canonical_packs
            else []
        ),
    }
    if not config_path.exists():
        created.append(config_rel)
        config_payload = {
            "$schema": "./core/schemas/framework-config.schema.json",
            "frameworkVersion": FRAMEWORK_VERSION,
            "projectName": target_dir.name,
            "workflowProfile": profile,
            "enabledPlatforms": platforms,
            "stacks": normalized_stacks,
            "optionalSkillPacks": optional_packs_payload,
            "qualityGates": {
                "requireTddRedGreen": True,
                "requireIndependentCodeReview": True,
                "requireGraphifyCheck": True,
                "minimumTestCoveragePercent": 80,
            },
            "security": {
                "enforcePreCommitSecretScan": True,
                "allowActiveSecurityTesting": False,
                "strixProfilePath": "security/strix-profile.yaml",
            },
            "paths": {
                "specsDir": "docs/specs",
                "adrDir": "docs/adr",
                "plansDir": "docs/plans",
                "retrospectivesDir": "docs/retrospectives",
                "stateDir": ".framework-state",
            },
        }
        if not dry_run:
            config_path.write_text(json.dumps(config_payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    elif update_mode:
        try:
            existing_cfg = json.loads(config_path.read_text(encoding="utf-8"))
            changed = False
            if existing_cfg.get("frameworkVersion") != FRAMEWORK_VERSION:
                existing_cfg["frameworkVersion"] = FRAMEWORK_VERSION
                changed = True
            if existing_cfg.get("optionalSkillPacks") != optional_packs_payload:
                existing_cfg["optionalSkillPacks"] = optional_packs_payload
                changed = True
            if normalized_stacks and existing_cfg.get("stacks") != normalized_stacks:
                existing_cfg["stacks"] = normalized_stacks
                changed = True
            if changed:
                updated.append(config_rel)
                if not dry_run:
                    config_path.write_text(json.dumps(existing_cfg, indent=2) + "\n", encoding="utf-8", newline="\n")
            else:
                unchanged.append(config_rel)
        except Exception:
            unchanged.append(config_rel)
    else:
        unchanged.append(config_rel)

    # Tier 3 Consumer-Owned File 2: .framework-state/manifest.json
    manifest_rel = ".framework-state/manifest.json"
    manifest_path = target_dir / Path(manifest_rel)
    if not manifest_path.exists():
        created.append(manifest_rel)
        manifest_payload = {
            "schema_version": "1.0.0",
            "project_name": target_dir.name,
            "project_type": "consumer",
            "framework_version": FRAMEWORK_VERSION,
            "workflow_profile": profile,
            "current_phase": 1,
            "current_phase_slug": "01-discovery",
            "status": "bootstrapped",
            "active_gate": "Gate-01a",
            "completed_phases": [],
        }
        if not dry_run:
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(json.dumps(manifest_payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    else:
        unchanged.append(manifest_rel)

    # Tier 3 Consumer-Owned Stack Templates (.gitignore & docs/ENVIRONMENT_PREFLIGHT.md)
    if normalized_stacks:
        gitignore_content = _compose_stack_gitignore(framework_root, normalized_stacks)
        gitignore_path = target_dir / ".gitignore"
        rec_gitignore_rel = ".gitignore.framework-recommended"
        rec_gitignore_path = target_dir / rec_gitignore_rel

        if not gitignore_path.exists():
            created.append(".gitignore")
            if not dry_run:
                gitignore_path.write_text(gitignore_content, encoding="utf-8", newline="\n")
        else:
            unchanged.append(".gitignore")
            current_gi = gitignore_path.read_text(encoding="utf-8").replace("\r\n", "\n")
            if current_gi != gitignore_content:
                if not rec_gitignore_path.exists():
                    created.append(rec_gitignore_rel)
                    if not dry_run:
                        rec_gitignore_path.write_text(gitignore_content, encoding="utf-8", newline="\n")
                else:
                    unchanged.append(rec_gitignore_rel)

        preflight_rel = "docs/ENVIRONMENT_PREFLIGHT.md"
        preflight_path = target_dir / Path(preflight_rel)
        if not preflight_path.exists():
            created.append(preflight_rel)
            if not dry_run:
                pf_report = preflight.run_preflight_checks(normalized_stacks)
                pf_md = preflight.render_preflight_markdown(pf_report)
                preflight_path.parent.mkdir(parents=True, exist_ok=True)
                preflight_path.write_text(pf_md, encoding="utf-8", newline="\n")
        else:
            unchanged.append(preflight_rel)

    if not dry_run:
        lock_payload = {
            "framework_version": FRAMEWORK_VERSION,
            "platforms": platforms,
            "optional_packs": canonical_packs,
            "stacks": normalized_stacks,
            "managed_files": new_locked_hashes,
        }
        lock_path.write_text(json.dumps(lock_payload, indent=2) + "\n", encoding="utf-8", newline="\n")

    return {
        "created": created,
        "updated": updated,
        "unchanged": unchanged,
        "skipped_modified": skipped_modified,
    }


def parse_csv_list(raw: str, allowed: Set[str], flag_name: str) -> List[str]:
    if not raw.strip():
        return []
    items = [p.strip() for p in raw.split(",") if p.strip()]
    invalid = [p for p in items if p not in allowed]
    if invalid:
        raise ValueError(f"Invalid value(s) for {flag_name}: {invalid}. Allowed: {sorted(allowed)}")
    return items


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap or update AI Engineering Framework in a target repository.")
    parser.add_argument("--target", type=Path, required=True, help="Target project directory")
    parser.add_argument(
        "--platforms",
        type=str,
        default=",".join(ALL_PLATFORMS),
        help="Comma-separated platforms (antigravity,copilot,claude-code,codex,gemini-cli)",
    )
    parser.add_argument(
        "--profile",
        type=str,
        choices=["full", "standard", "hotfix"],
        default="standard",
        help="Default workflow profile in project.framework.json",
    )
    parser.add_argument(
        "--optional-packs",
        type=str,
        default="communication,context-engineering,agent-architecture",
        help="Comma-separated optional packs (none,all,communication,context-engineering,agent-architecture,frontend-design/design-ui,growth-media)",
    )
    parser.add_argument(
        "--stacks",
        type=str,
        default="",
        help="Optional comma-separated technology stacks for .gitignore and SDK preflight (dotnet,node/angular,python)",
    )
    parser.add_argument("--update", action="store_true", help="Update unmodified framework-managed files")
    parser.add_argument("--dry-run", action="store_true", help="Preview file operations without writing to disk")
    args = parser.parse_args(argv)

    try:
        platforms = parse_csv_list(args.platforms, set(ALL_PLATFORMS), "--platforms")
        raw_packs = [p.strip() for p in args.optional_packs.split(",") if p.strip()]
        optional_packs = normalize_optional_packs(raw_packs)
        raw_stacks = [s.strip() for s in args.stacks.split(",") if s.strip()]
        stacks = preflight.normalize_stacks(raw_stacks)
    except ValueError as exc:
        print(f"BOOTSTRAP_ERROR: {exc}", file=sys.stderr)
        return 2

    summary = bootstrap_project(
        target_dir=args.target,
        platforms=platforms,
        profile=args.profile,
        optional_packs=optional_packs,
        stacks=stacks,
        update_mode=args.update,
        dry_run=args.dry_run,
    )

    mode_label = "DRY-RUN" if args.dry_run else ("UPDATE" if args.update else "BOOTSTRAP")
    print(f"=== AI Engineering Framework {mode_label} ({args.target.resolve()}) ===")
    print(f"  Platforms:        {', '.join(platforms)}")
    print(f"  Optional Packs:   {', '.join(optional_packs) if optional_packs else 'none (core-only)'}")
    if stacks:
        print(f"  Stacks:           {', '.join(stacks)}")
    print(f"  Created:          {len(summary['created'])}")
    print(f"  Updated:          {len(summary['updated'])}")
    print(f"  Unchanged:        {len(summary['unchanged'])}")
    print(f"  Skipped/Modified: {len(summary['skipped_modified'])} (user customizations preserved)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
