#!/usr/bin/env python3
"""Bootstrap or non-destructively update the AI Engineering Framework in a target project.

Key Guarantees:
1. Tier 3 Consumer-Owned Files (project.framework.json, .framework-state/manifest.json, .gitignore,
   docs/specs/, docs/adr/, docs/plans/, README.md) are NEVER overwritten if they already exist.
2. Tier 1 & Tier 2 Framework-Managed Files (core/, agents/, skills/, workflows/, platform adapters)
   and Native Platform Skill Projections (.agents/skills/, .claude/skills/) are tailored to the
   consumer's selected platforms and optional packs and tracked in `.framework-lock.json` (v2.0.0).
3. Ownership, hash integrity, atomic two-phase lockfile commits, and path-safety guards prevent
   overwriting locally customized files, deleting untracked files, or following symlinks/junctions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import posixpath
import re
import shutil
import stat
import sys
from typing import Dict, Iterable, List, Set, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import compose  # noqa: E402
import platform_capabilities  # noqa: E402
import preflight  # noqa: E402
import sync_adapters  # noqa: E402

FRAMEWORK_ROOT = SCRIPT_DIR.parent
FRAMEWORK_VERSION = "0.5.0"
LOCKFILE_NAME = ".aief/lock.json"
LOCKFILE_SCHEMA_VERSION = "2.0.0"
LOCKFILE_BACKUP_REL = ".aief/state/lock-backups/framework-lock-v0.3.0.json"

ALL_PLATFORMS: List[str] = list(
    platform_capabilities.load_platform_capabilities()["platform_ids"]
)

CORE_MANAGED_GLOBS = [
    "core/rules/*.md",
    "core/schemas/*.json",
    "core/platform-capabilities.json",
    "agents/*.md",
    "workflows/*.md",
    "quality/*.md",
    "security/*.md",
    "security/*.yaml",
    "templates/*.md",
    "templates/*.json",
    "templates/stacks/*.gitignore",
    "scripts/compose.py",
    "scripts/validate.py",
    "scripts/preflight.py",
    "scripts/platform_capabilities.py",
    "scripts/readiness.py",
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

SUPPORTED_PROJECTION_ROOTS: Set[str] = {".agents/skills", ".claude/skills"}
TEXT_SUFFIXES: Set[str] = {".md", ".json", ".py", ".csv", ".cjs", ".js", ".ts", ".txt", ".yaml", ".yml", ".toml", ".gitignore"}

CONSUMER_OWNED_EXACT: Set[str] = {
    ".aief/config.json",
    ".aief/.gitignore",
    ".aief/gitignore.recommended",
    ".aief/ENVIRONMENT_PREFLIGHT.md",
    "project.framework.json",
    ".gitignore",
    ".gitignore.framework-recommended",
    "README.md",
}
CONSUMER_OWNED_PREFIXES: Tuple[str, ...] = (
    "docs/",
    ".aief/state/",
    ".aief/custom/",
    ".framework-state/",
    ".framework-custom/",
)
ALLOWED_SKILL_PRUNE_ROOTS: Tuple[str, ...] = (
    ".agents/skills/",
    ".claude/skills/",
    ".aief/skills/core/",
    ".aief/skills/optional/",
    "skills/optional/",
)
ALLOWED_MANAGED_ADAPTER_PRUNE_EXACT: Set[str] = {
    "CLAUDE.md",
    "GEMINI.md",
    ".aief/adapters/antigravity/hooks.json",
    ".aief/adapters/antigravity/mcp_config.json",
    ".aief/adapters/antigravity/skills.json",
    "adapters/antigravity/hooks.json",
    "adapters/antigravity/mcp_config.json",
    ".agents/skills.json",
    ".mcp.json",
    ".vscode/mcp.json",
}
ALLOWED_MANAGED_ADAPTER_PRUNE_PREFIXES: Tuple[str, ...] = (
    ".agents/rules/",
    ".claude/agents/",
    ".claude/commands/",
    ".claude/settings.json",
    ".github/agents/",
    ".github/copilot-instructions.md",
    ".github/instructions/",
    ".github/prompts/",
    ".codex/",
    ".gemini/",
)
VALID_OWNERSHIP_CLASSES: Set[str] = {
    "framework_managed",
    "platform_projected_skill",
    "consumer_owned",
    "consumer_customized_generated",
    "consumer_custom_skill",
    "consumer_custom_agent",
    "consumer_custom_prompt",
    "consumer_custom_mcp",
    "obsolete_framework_managed",
    "unknown_untracked",
}

FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
REQUIRED_SKILLS_LINE_RE = re.compile(r"^(required_skills:\s*\[)([^\]]*)(\]\s*)$", re.MULTILINE)
SHA256_HEX_RE = re.compile(r"^[0-9a-fA-F]{64}$")
WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")


class BootstrapSecurityError(ValueError):
    """Raised when path safety, symlink/junction checks, or case collision guards fail."""


class LockfileError(ValueError):
    """Raised when .framework-lock.json is corrupted or ambiguous (fail-closed)."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def validate_safe_rel_path(rel_path: str, label: str = "path") -> str:
    """Reject traversal, absolute paths, drive prefixes, and NUL bytes; return POSIX rel path."""
    if not isinstance(rel_path, str) or not rel_path.strip():
        raise BootstrapSecurityError(f"Unsafe empty {label}")
    if "\x00" in rel_path:
        raise BootstrapSecurityError(f"NUL byte rejected in {label}: {rel_path!r}")
    normalized_raw = rel_path.replace("\\", "/")
    if normalized_raw.startswith("/") or WINDOWS_DRIVE_RE.match(normalized_raw):
        raise BootstrapSecurityError(f"Absolute or drive-qualified {label} rejected: {rel_path}")
    parts = [p for p in normalized_raw.split("/") if p != ""]
    if not parts or any(part in {".", ".."} for part in parts):
        raise BootstrapSecurityError(f"Path traversal or dot segment rejected in {label}: {rel_path}")
    return "/".join(parts)


def _is_reparse_or_symlink(path: Path) -> bool:
    """Return True if path is a symlink or Windows junction/reparse point without following it."""
    if path.is_symlink():
        return True
    try:
        st = os.lstat(path)
    except OSError:
        return False
    attrs = getattr(st, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x0400)
    return bool(attrs & reparse_flag)


def assert_safe_target_path(base_root: Path, rel_path: str, label: str = "destination") -> Path:
    """Validate rel_path is inside base_root and traverses no symlinks or Windows junctions."""
    safe_rel = validate_safe_rel_path(rel_path, label=label)
    base_resolved = base_root.resolve()
    current = base_root
    for segment in safe_rel.split("/"):
        current = current / segment
        if current.exists() or _is_reparse_or_symlink(current):
            if _is_reparse_or_symlink(current):
                raise BootstrapSecurityError(
                    f"Symlink or reparse point rejected at {current.relative_to(base_root).as_posix()}"
                )
    dst = (base_root / Path(safe_rel))
    resolved = dst.resolve(strict=False)
    if not resolved.is_relative_to(base_resolved):
        raise BootstrapSecurityError(f"Resolved {label} escapes target root: {rel_path}")
    return dst


def check_case_collisions(rel_paths: Iterable[str]) -> None:
    """Reject distinct relative paths that collide case-insensitively on Windows."""
    seen: Dict[str, str] = {}
    for rel in rel_paths:
        key = rel.casefold()
        if key in seen and seen[key] != rel:
            raise BootstrapSecurityError(
                f"Case-insensitive path collision detected: '{seen[key]}' vs '{rel}'"
            )
        seen[key] = rel


def _is_consumer_owned_path(rel_path: str) -> bool:
    return rel_path in CONSUMER_OWNED_EXACT or rel_path.startswith(CONSUMER_OWNED_PREFIXES)


def _is_prunable_path(rel_path: str, ownership: str) -> bool:
    if _is_consumer_owned_path(rel_path):
        return False
    if rel_path.startswith(ALLOWED_SKILL_PRUNE_ROOTS):
        return ownership in {"framework_managed", "platform_projected_skill", "consumer_custom_skill"}
    if ownership in {"framework_managed", "consumer_custom_agent", "consumer_custom_prompt", "consumer_custom_mcp"}:
        return (
            rel_path in ALLOWED_MANAGED_ADAPTER_PRUNE_EXACT
            or rel_path.startswith(ALLOWED_MANAGED_ADAPTER_PRUNE_PREFIXES)
        )
    return False


def _atomic_write_bytes(target_path: Path, data: bytes) -> None:
    """Atomically write data to target_path using a same-directory temp file and os.replace."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target_path.with_name(f".{target_path.name}.{os.getpid()}.tmp")
    try:
        with tmp_path.open("wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, target_path)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise


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


def _verify_projected_markdown_links(
    dst_rel: str,
    markdown_text: str,
    available_targets: Set[str],
) -> None:
    """Verify relative links in relocated projected Markdown resolve inside root to known targets."""
    dst_dir = posixpath.dirname(dst_rel.replace("\\", "/"))
    masked = FENCED_CODE_RE.sub("", markdown_text)
    masked = INLINE_CODE_RE.sub("", masked)
    for match in MD_LINK_RE.finditer(masked):
        target_raw = match.group(2).strip()
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
        if target_raw.startswith("/") or WINDOWS_DRIVE_RE.match(target_raw):
            raise BootstrapSecurityError(f"Projected skill link cannot be absolute: {dst_rel} -> {target_raw}")
        path_part = target_raw.split("#", 1)[0].strip()
        if not path_part:
            continue
        resolved = posixpath.normpath(posixpath.join(dst_dir, path_part) if dst_dir else path_part)
        if resolved == ".." or resolved.startswith("../") or "/../" in resolved:
            raise BootstrapSecurityError(f"Projected skill link escapes workspace root: {dst_rel} -> {target_raw}")
        if resolved not in available_targets:
            raise ValueError(f"Broken relocated link in projected skill {dst_rel}: '{target_raw}' -> '{resolved}'")


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


def _resolve_platform_projection_roots(
    framework_root: Path,
    platforms: List[str],
) -> Tuple[Dict[str, List[str]], Dict[str, str]]:
    """Derive {projection_root: [platform_ids]} and {platform_id: projection_root} from capabilities."""
    cap_path = framework_root / "core" / "platform-capabilities.json"
    model = platform_capabilities.load_platform_capabilities(cap_path)

    root_to_platforms: Dict[str, List[str]] = {}
    platform_to_root: Dict[str, str] = {}
    for pid in platforms:
        cap = platform_capabilities.get_platform(model, pid)
        native_paths = cap.get("native_skill_dirs", {}).get("paths", [])
        chosen_root = ""
        for pattern in native_paths:
            prefix = str(pattern).split("/<name>/", 1)[0].rstrip("/")
            if prefix in SUPPORTED_PROJECTION_ROOTS:
                chosen_root = prefix
                break
        if chosen_root:
            platform_to_root[pid] = chosen_root
            root_to_platforms.setdefault(chosen_root, [])
            if pid not in root_to_platforms[chosen_root]:
                root_to_platforms[chosen_root].append(pid)

    return root_to_platforms, {pid: root for pid, root in platform_to_root.items()}


def _read_normalized_skill_file(src: Path) -> bytes:
    if src.suffix.lower() in TEXT_SUFFIXES:
        try:
            return src.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
        except UnicodeDecodeError:
            return src.read_bytes()
    return src.read_bytes()


def _assert_overlay_safe(target_dir: Path, overlay_rel: str) -> None:
    """Validate overlay directory and every nested path are symlink/reparse safe."""
    assert_safe_target_path(target_dir, overlay_rel, label="overlayDir")
    overlay_root = target_dir / Path(overlay_rel)
    if _is_reparse_or_symlink(overlay_root):
        raise BootstrapSecurityError(f"Symlink or reparse point rejected at {overlay_rel}")
    if overlay_root.exists() and overlay_root.is_dir():
        for item in sorted(overlay_root.rglob("*")):
            if _is_reparse_or_symlink(item):
                raise BootstrapSecurityError(
                    f"Symlink or reparse point rejected at {item.relative_to(target_dir).as_posix()}"
                )


def collect_managed_plan_details(
    framework_root: Path,
    platforms: List[str],
    optional_packs: List[str],
    target_dir: Path | None = None,
    config_data: Dict[str, object] | None = None,
    profile: str = "standard",
    extra_imported: List[Tuple[str, str]] | None = None,
    layout: Dict[str, str] | None = None,
) -> Tuple[Dict[str, Dict[str, object]], Dict[str, Dict[str, object]]]:
    """Build deterministic detailed plan and projected_skills summary from canonical metadata."""
    entries: Dict[str, Dict[str, object]] = {}
    cfg = dict(config_data or {})
    active_layout = layout or (
        compose.resolve_consumer_layout(target_dir)
        if target_dir is not None
        else compose.resolve_consumer_layout(framework_root, force_layout="isolated")
    )
    fw_prefix = active_layout["fw_prefix"]
    hooks_rel = active_layout["hooks_rel"]
    controls = compose.normalize_project_controls(cfg, default_overlay_dir=active_layout["overlay_default"])
    overlay_rel = str(controls["customizations"]["overlayDir"])
    if target_dir is not None:
        _assert_overlay_safe(target_dir, overlay_rel)
        overlay = compose.load_project_overlay(target_dir, overlay_rel)
    else:
        overlay = {
            "overlay_rel": overlay_rel,
            "instruction_sections": [],
            "custom_skills": {},
            "agent_overrides": {},
            "agent_appends": {},
            "custom_prompts": {},
            "custom_mcp": {},
        }

    if extra_imported:
        existing_srcs = {src for src, _ in overlay["instruction_sections"]}  # type: ignore[attr-defined]
        for imp_rel, imp_text in extra_imported:
            if imp_rel not in existing_srcs and imp_text.strip():
                overlay["instruction_sections"].append((imp_rel, imp_text.strip()))  # type: ignore[attr-defined]

    digest = sync_adapters.compute_canonical_digest(framework_root)
    comp = compose.compose_consumer_artifacts(
        source_root=framework_root,
        target_dir=target_dir if target_dir is not None else framework_root,
        platforms=platforms,
        profile=profile,
        optional_packs=optional_packs,
        config_data=cfg,
        overlay=overlay,
        digest=digest,
        layout=active_layout,
    )
    consumer_reg = comp["consumer_registry"]

    def _add_managed(
        rel: str,
        data: bytes,
        source: str | None,
        owners: List[str],
        ownership: str = "framework_managed",
    ) -> None:
        safe_rel = validate_safe_rel_path(rel, label="managed destination")
        if safe_rel in entries:
            merged = sorted(set(entries[safe_rel]["platforms"]) | set(owners))
            entries[safe_rel]["platforms"] = merged
            entries[safe_rel]["bytes"] = data
            entries[safe_rel]["ownership"] = ownership
            if source is not None:
                entries[safe_rel]["source"] = source
            return
        entries[safe_rel] = {
            "bytes": data,
            "ownership": ownership,
            "source": source,
            "skill": None,
            "platforms": sorted(set(owners)),
        }

    # 1. Core framework managed globs (excluding dynamically composed agents/*.md)
    skill_dir_map = comp.get("skill_dir_map")  # type: ignore[assignment]
    for pattern in CORE_MANAGED_GLOBS:
        for src in sorted(framework_root.glob(pattern)):
            if src.is_file():
                rel = src.relative_to(framework_root).as_posix()
                if rel.startswith("agents/") and rel.endswith(".md"):
                    continue
                dst_rel = f"{fw_prefix}{rel}"
                if fw_prefix and src.suffix.lower() == ".md":
                    raw_md = src.read_text(encoding="utf-8")
                    data_bytes = compose.rewrite_markdown_relative_links(
                        raw_md,
                        rel,
                        dst_rel,
                        fw_prefix=fw_prefix,
                        skill_dir_map=skill_dir_map,  # type: ignore[arg-type]
                        strip_upstream_snapshot_links=True,
                    ).encode("utf-8")
                else:
                    data_bytes = _read_normalized_skill_file(src)
                _add_managed(dst_rel, data_bytes, rel, ["core"])

    for agent_rel, agent_bytes in comp["composed_agent_files"].items():  # type: ignore[attr-defined]
        _add_managed(agent_rel, agent_bytes, agent_rel, ["core"])

    # 2. Canonical skills subtree: only copied on disk for legacy root installs;
    # isolated (.aief/) consumers read directly from projected .agents/skills/ & .claude/skills/ + bundle cache.
    if not fw_prefix:
        core_skills_root = framework_root / "skills" / "core"
        if core_skills_root.exists():
            for src in sorted(core_skills_root.rglob("*")):
                if src.is_file() and "__pycache__" not in src.parts and src.suffix != ".pyc":
                    rel = src.relative_to(framework_root).as_posix()
                    _add_managed(rel, _read_normalized_skill_file(src), rel, ["core"])

    # 3. Filtered consumer skills/registry.json
    _add_managed(
        f"{fw_prefix}skills/registry.json",
        (json.dumps(consumer_reg, indent=2) + "\n").encode("utf-8"),
        "skills/registry.json",
        ["core"],
    )

    # 4. Selected optional skill pack subtrees (legacy layout only)
    if not fw_prefix:
        for pack in optional_packs:
            pack_rel_dir = OPTIONAL_PACK_DIRS.get(pack)
            if pack_rel_dir:
                pack_dir = framework_root / Path(pack_rel_dir)
                if pack_dir.exists():
                    for src in sorted(pack_dir.rglob("*")):
                        if src.is_file() and "__pycache__" not in src.parts and src.suffix != ".pyc":
                            rel = src.relative_to(framework_root).as_posix()
                            _add_managed(rel, _read_normalized_skill_file(src), rel, ["core"])

    # 5. Platform adapters (inline rules + overlay + active custom agents + static fallback)
    consumer_overrides = sync_adapters.generate_consumer_adapter_files(framework_root, digest=digest)
    composed_platform_files: Dict[str, str] = comp["platform_files"]  # type: ignore[assignment]

    for plat in platforms:
        for src_rel, dst_rel in PLATFORM_ADAPTER_MAPPINGS.get(plat, []):
            if dst_rel in {".claude/agents/framework-code-reviewer.md", ".github/agents/code-reviewer.agent.md"}:
                continue
            effective_dst = hooks_rel if dst_rel == "adapters/antigravity/hooks.json" else dst_rel
            if effective_dst in composed_platform_files:
                _add_managed(effective_dst, composed_platform_files[effective_dst].encode("utf-8"), src_rel, [plat])
                continue
            if effective_dst in consumer_overrides:
                _add_managed(effective_dst, consumer_overrides[effective_dst].encode("utf-8"), src_rel, [plat])
                continue

            src = framework_root / Path(src_rel)
            if not src.exists():
                continue

            raw_text = src.read_text(encoding="utf-8").replace("\r\n", "\n")
            if effective_dst.endswith(".md") and src_rel != effective_dst:
                rewritten_text = compose.rewrite_markdown_relative_links(raw_text, src_rel, effective_dst, fw_prefix=fw_prefix)
                _add_managed(effective_dst, rewritten_text.encode("utf-8"), src_rel, [plat])
            else:
                _add_managed(effective_dst, raw_text.encode("utf-8"), src_rel, [plat])

    if "claude-code" in platforms:
        for rel, (data, own) in comp["claude_agent_entries"].items():  # type: ignore[attr-defined]
            _add_managed(rel, data, rel, ["claude-code"], ownership=own)
        for rel, (data, own) in comp["claude_prompt_entries"].items():  # type: ignore[attr-defined]
            _add_managed(rel, data, rel, ["claude-code"], ownership=own)
    if "copilot" in platforms:
        for rel, (data, own) in comp["copilot_agent_entries"].items():  # type: ignore[attr-defined]
            _add_managed(rel, data, rel, ["copilot"], ownership=own)
        for rel, (data, own) in comp["copilot_prompt_entries"].items():  # type: ignore[attr-defined]
            _add_managed(rel, data, rel, ["copilot"], ownership=own)
    if "gemini-cli" in platforms:
        for rel, (data, own) in comp["gemini_prompt_entries"].items():  # type: ignore[attr-defined]
            _add_managed(rel, data, rel, ["gemini-cli"], ownership=own)
    for rel, (data, own, owners) in comp["mcp_entries"].items():  # type: ignore[attr-defined]
        active_owners = [p for p in owners if p in platforms]
        if active_owners:
            _add_managed(rel, data, rel, active_owners, ownership=own)

    # 6. Native platform skill projections (active framework skills + consumer custom skills)
    projected_skills_summary: Dict[str, Dict[str, object]] = comp["projected_skills_summary"]  # type: ignore[assignment]
    for dst_rel, meta in comp["projected_files"].items():  # type: ignore[attr-defined]
        entries[dst_rel] = meta

    # Verify Windows case-insensitive collisions across all planned paths
    check_case_collisions(entries.keys())

    # Verify every relocated link in projected Markdown resolves cleanly inside consumer workspace
    available_targets = set(entries.keys())
    for dst_rel, rewritten_text in comp["projected_md_checks"]:  # type: ignore[attr-defined]
        _verify_projected_markdown_links(dst_rel, rewritten_text, available_targets)

    return entries, projected_skills_summary


def collect_managed_plan_bytes(
    framework_root: Path,
    platforms: List[str],
    optional_packs: List[str],
) -> Dict[str, bytes]:
    """Return mapping of {target_rel_posix_path: content_bytes} for all managed and projected files."""
    details, _ = collect_managed_plan_details(framework_root, platforms, optional_packs)
    return {rel: bytes(meta["bytes"]) for rel, meta in details.items()}


def collect_managed_plan(
    framework_root: Path,
    platforms: List[str],
    optional_packs: List[str],
) -> Dict[str, Path]:
    """Legacy helper returning {target_rel_posix_path: source_abs_path} for callers."""
    canonical_packs = normalize_optional_packs(optional_packs)
    plan_bytes = collect_managed_plan_bytes(framework_root, platforms, canonical_packs)
    return {rel: (framework_root / Path(rel)) for rel in plan_bytes}


def _compose_stack_gitignore(framework_root: Path, stacks: List[str], *, isolated: bool = True) -> str:
    state_ignore = ".aief/state/" if isolated else ".framework-state/scratch/"
    sections: List[str] = [
        "# Generated by AI Engineering Framework",
        state_ignore,
        "graphify-out/",
        "",
    ]
    for st in stacks:
        tpl_path = framework_root / "templates" / "stacks" / f"{st}.gitignore"
        if tpl_path.exists():
            sections.append(tpl_path.read_text(encoding="utf-8").replace("\r\n", "\n").strip())
            sections.append("")
    return "\n".join(sections).rstrip() + "\n"


def _load_existing_lockfile(lock_path: Path) -> Dict[str, object]:
    """Load and validate an existing .framework-lock.json cleanly (fail-closed on corruption)."""
    empty_state: Dict[str, object] = {
        "exists": False,
        "version": None,
        "raw_bytes": b"",
        "raw": {},
        "managed_files": {},
        "projection_state": {"status": "none", "pending_entries": {}, "last_successful_projection": None},
    }
    if not lock_path.exists() and not _is_reparse_or_symlink(lock_path):
        return empty_state
    if _is_reparse_or_symlink(lock_path):
        raise LockfileError("Lockfile .framework-lock.json must not be a symlink or reparse point")

    raw_bytes = lock_path.read_bytes()
    try:
        raw_data = json.loads(raw_bytes.decode("utf-8"))
    except Exception as exc:
        raise LockfileError(
            f"Corrupted .framework-lock.json ({exc}). Resolve or restore backup before updating."
        ) from exc

    if not isinstance(raw_data, dict):
        raise LockfileError("Corrupted .framework-lock.json: root must be a JSON object")

    schema_version = raw_data.get("schema_version")
    if schema_version is None:
        # Legacy v0.3.0 lockfile format
        for req_key in ("framework_version", "platforms", "managed_files"):
            if req_key not in raw_data:
                raise LockfileError(f"Malformed legacy .framework-lock.json: missing key '{req_key}'")
        raw_managed = raw_data.get("managed_files")
        raw_platforms = raw_data.get("platforms")
        if not isinstance(raw_managed, dict) or not isinstance(raw_platforms, list):
            raise LockfileError("Malformed legacy .framework-lock.json: invalid managed_files/platforms types")
        normalized_managed: Dict[str, Dict[str, object]] = {}
        for raw_rel, raw_hash in raw_managed.items():
            try:
                safe_rel = validate_safe_rel_path(str(raw_rel), label="lockfile path")
            except BootstrapSecurityError as exc:
                raise LockfileError(f"Unsafe path in .framework-lock.json: {exc}") from exc
            if not isinstance(raw_hash, str) or not SHA256_HEX_RE.match(raw_hash):
                raise LockfileError(f"Malformed SHA-256 hash in .framework-lock.json for '{safe_rel}'")
            normalized_managed[safe_rel] = {
                "ownership": "framework_managed",
                "source": None,
                "sha256": raw_hash.lower(),
                "platforms": sorted(str(p) for p in raw_platforms),
            }
        return {
            "exists": True,
            "version": "0.3.0",
            "raw_bytes": raw_bytes,
            "raw": raw_data,
            "managed_files": normalized_managed,
            "projection_state": {"status": "completed", "pending_entries": {}, "last_successful_projection": None},
        }

    if schema_version != LOCKFILE_SCHEMA_VERSION:
        raise LockfileError(
            f"Unsupported .framework-lock.json schema_version '{schema_version}'. Expected '{LOCKFILE_SCHEMA_VERSION}'."
        )

    for req_key in ("framework_version", "enabled_platforms", "optional_packs", "projection_state", "projected_skills", "managed_files"):
        if req_key not in raw_data:
            raise LockfileError(f"Corrupted v2 .framework-lock.json: missing key '{req_key}'")

    proj_state = raw_data.get("projection_state")
    raw_managed = raw_data.get("managed_files")
    if not isinstance(proj_state, dict) or not isinstance(raw_managed, dict):
        raise LockfileError("Corrupted v2 .framework-lock.json: invalid projection_state/managed_files")
    if proj_state.get("status") not in {"in_progress", "completed"}:
        raise LockfileError(f"Corrupted v2 .framework-lock.json: invalid projection_state.status '{proj_state.get('status')}'")
    pending_raw = proj_state.get("pending_entries", {})
    if not isinstance(pending_raw, dict):
        raise LockfileError("Corrupted v2 .framework-lock.json: invalid pending_entries")

    def _normalize_v2_map(src_map: Dict[str, object]) -> Dict[str, Dict[str, object]]:
        out: Dict[str, Dict[str, object]] = {}
        for raw_rel, entry in src_map.items():
            try:
                safe_rel = validate_safe_rel_path(str(raw_rel), label="lockfile path")
            except BootstrapSecurityError as exc:
                raise LockfileError(f"Unsafe path in .framework-lock.json: {exc}") from exc
            if not isinstance(entry, dict):
                raise LockfileError(f"Malformed lockfile entry for '{safe_rel}'")
            ownership = entry.get("ownership")
            sha_val = entry.get("sha256")
            plats = entry.get("platforms")
            if ownership not in VALID_OWNERSHIP_CLASSES:
                raise LockfileError(f"Invalid ownership '{ownership}' in .framework-lock.json for '{safe_rel}'")
            if not isinstance(sha_val, str) or not SHA256_HEX_RE.match(sha_val):
                raise LockfileError(f"Invalid SHA-256 hash in .framework-lock.json for '{safe_rel}'")
            if not isinstance(plats, list):
                raise LockfileError(f"Invalid platforms list in .framework-lock.json for '{safe_rel}'")
            normalized_entry: Dict[str, object] = {
                "ownership": ownership,
                "source": entry.get("source"),
                "sha256": sha_val.lower(),
                "platforms": sorted(str(p) for p in plats),
            }
            if entry.get("skill") is not None:
                normalized_entry["skill"] = str(entry["skill"])
            out[safe_rel] = normalized_entry
        return out

    normalized_managed = _normalize_v2_map(raw_managed)
    normalized_pending = _normalize_v2_map(pending_raw)
    return {
        "exists": True,
        "version": LOCKFILE_SCHEMA_VERSION,
        "raw_bytes": raw_bytes,
        "raw": raw_data,
        "managed_files": normalized_managed,
        "projection_state": {
            "status": proj_state["status"],
            "pending_entries": normalized_pending,
            "last_successful_projection": proj_state.get("last_successful_projection"),
        },
    }


def _build_lockfile_entry(meta: Dict[str, object], data_hash: str | None = None) -> Dict[str, object]:
    entry: Dict[str, object] = {
        "ownership": meta["ownership"],
        "source": meta.get("source"),
        "sha256": data_hash if data_hash is not None else sha256_bytes(bytes(meta["bytes"])),
        "platforms": sorted(str(p) for p in meta.get("platforms", [])),
    }
    if meta.get("skill") is not None:
        entry["skill"] = str(meta["skill"])
    return entry


def _build_v2_lock_payload(
    platforms: List[str],
    canonical_packs: List[str],
    normalized_stacks: List[str],
    canonical_digest: str,
    status: str,
    projected_skills: Dict[str, Dict[str, object]],
    managed_files: Dict[str, Dict[str, object]],
    last_successful: Dict[str, object] | None,
    pending_entries: Dict[str, Dict[str, object]],
) -> Dict[str, object]:
    if status == "completed":
        skill_names: Set[str] = set()
        for pdata in projected_skills.values():
            skill_names.update(str(s) for s in pdata.get("skills", []))
        projected_file_count = sum(
            1
            for v in managed_files.values()
            if v.get("ownership") in {"platform_projected_skill", "consumer_custom_skill"}
        )
        effective_last = {
            "framework_version": FRAMEWORK_VERSION,
            "enabled_platforms": sorted(set(platforms)),
            "projected_skill_count": len(skill_names),
            "projected_file_count": projected_file_count,
        }
    else:
        effective_last = last_successful

    return {
        "schema_version": LOCKFILE_SCHEMA_VERSION,
        "framework_version": FRAMEWORK_VERSION,
        "enabled_platforms": sorted(set(platforms)),
        "optional_packs": list(canonical_packs),
        "stacks": list(normalized_stacks),
        "projection_state": {
            "status": status,
            "canonical_digest": canonical_digest,
            "last_successful_projection": effective_last,
            "pending_entries": {k: pending_entries[k] for k in sorted(pending_entries.keys())},
        },
        "projected_skills": {k: projected_skills[k] for k in sorted(projected_skills.keys())},
        "managed_files": {k: managed_files[k] for k in sorted(managed_files.keys())},
    }


def _cleanup_empty_dirs(target_dir: Path, pruned_paths: List[str] | None = None) -> None:
    """Prune empty subdirectories bottom-up strictly inside managed skill/adapter roots."""
    target_resolved = target_dir.resolve()
    for base_rel in (".agents/skills", ".claude/skills", ".aief/skills/core", ".aief/skills/optional", "skills/optional"):
        base = target_dir / Path(base_rel)
        if not base.exists() or _is_reparse_or_symlink(base):
            continue
        for sub in sorted(base.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            if sub.is_dir() and not _is_reparse_or_symlink(sub):
                try:
                    next(sub.iterdir())
                except StopIteration:
                    sub.rmdir()
        try:
            next(base.iterdir())
        except StopIteration:
            base.rmdir()

    # Clean empty parent adapter directories left behind by pruned files (never target_dir itself)
    if pruned_paths:
        candidates: Set[Path] = set()
        for rel in pruned_paths:
            parent = (target_dir / Path(rel)).parent
            while parent != target_dir and parent.resolve(strict=False).is_relative_to(target_resolved):
                candidates.add(parent)
                parent = parent.parent
        for d in sorted(candidates, key=lambda p: len(p.parts), reverse=True):
            if d.exists() and d.is_dir() and not _is_reparse_or_symlink(d):
                try:
                    next(d.iterdir())
                except StopIteration:
                    d.rmdir()


def bootstrap_project(
    target_dir: Path,
    platforms: List[str],
    profile: str = "standard",
    optional_packs: List[str] | None = None,
    stacks: List[str] | None = None,
    update_mode: bool = False,
    dry_run: bool = False,
    framework_root: Path = FRAMEWORK_ROOT,
) -> Dict[str, object]:
    """Bootstrap or update the framework in target_dir non-destructively using Lockfile v2."""
    raw_packs = optional_packs if optional_packs is not None else ["all"]
    canonical_packs = normalize_optional_packs(raw_packs)
    normalized_stacks = preflight.normalize_stacks(stacks or [])
    target_dir = target_dir.resolve()
    layout = compose.resolve_consumer_layout(target_dir)
    is_isolated = layout["mode"] == "isolated"
    fw_prefix = str(layout["fw_prefix"])
    lock_rel = str(layout["lock_rel"])
    config_rel = str(layout["config_rel"])
    state_rel = str(layout["state_rel"])
    lock_backup_rel = f"{state_rel}/lock-backups/framework-lock-v0.3.0.json"

    lock_path = target_dir / Path(lock_rel)
    existing_lock = _load_existing_lockfile(lock_path)
    prev_managed: Dict[str, Dict[str, object]] = dict(existing_lock["managed_files"])
    proj_state = dict(existing_lock["projection_state"])
    pending_recovery: Dict[str, Dict[str, object]] = (
        dict(proj_state.get("pending_entries", {})) if proj_state.get("status") == "in_progress" else {}
    )
    migrated_from = "0.3.0" if (existing_lock["version"] == "0.3.0" and update_mode) else None

    created: List[str] = []
    updated: List[str] = []
    unchanged: List[str] = []
    skipped_modified: List[str] = []
    pruned: List[str] = []
    conflicts_preserved: List[str] = []
    unknown_preserved: List[str] = []
    recovered: List[str] = []
    imported_files: List[str] = []
    preserved_external: List[str] = []
    tier3_writes: List[Tuple[str, bytes]] = []

    config_path = target_dir / Path(config_rel)
    existing_cfg_for_plan: Dict[str, object] = {}
    if config_path.exists() and not _is_reparse_or_symlink(config_path):
        try:
            loaded_cfg = json.loads(config_path.read_text(encoding="utf-8"))
            if isinstance(loaded_cfg, dict):
                existing_cfg_for_plan = loaded_cfg
        except Exception:
            existing_cfg_for_plan = {}

    controls_pre = compose.normalize_project_controls(
        existing_cfg_for_plan,
        default_overlay_dir=str(layout["overlay_default"]),
    )
    overlay_rel = str(controls_pre["customizations"]["overlayDir"])
    _assert_overlay_safe(target_dir, overlay_rel)

    # Brownfield auto-import on first bootstrap (no lockfile): preserve existing root instructions into overlay/imported/
    imported_entries: Dict[str, str] = {}
    in_memory_imported: List[Tuple[str, str]] = []
    if not existing_lock["exists"] and not update_mode:
        for entry_rel, imp_name in (
            ("AGENTS.md", "AGENTS.md"),
            ("CLAUDE.md", "CLAUDE.md"),
            ("GEMINI.md", "GEMINI.md"),
            (".github/copilot-instructions.md", "copilot-instructions.md"),
        ):
            entry_path = target_dir / Path(entry_rel)
            if entry_path.exists() and not _is_reparse_or_symlink(entry_path) and entry_path.is_file():
                raw_entry = entry_path.read_text(encoding="utf-8").replace("\r\n", "\n")
                if "AUTO-GENERATED" not in raw_entry and raw_entry.strip():
                    imp_rel = validate_safe_rel_path(f"{overlay_rel}/imported/{imp_name}", label="imported instruction")
                    assert_safe_target_path(target_dir, imp_rel, label="imported destination")
                    imported_entries[entry_rel] = imp_rel
                    if not (target_dir / Path(imp_rel)).exists():
                        tier3_writes.append((imp_rel, raw_entry.encode("utf-8")))
                        created.append(imp_rel)
                        imported_files.append(imp_rel)
                        in_memory_imported.append((imp_rel, raw_entry.strip()))

    effective_profile = (
        str(existing_cfg_for_plan.get("workflowProfile", profile))
        if (update_mode and existing_cfg_for_plan)
        else profile
    )
    desired_entries, projected_skills_summary = collect_managed_plan_details(
        framework_root,
        platforms,
        canonical_packs,
        target_dir=target_dir,
        config_data=existing_cfg_for_plan,
        profile=effective_profile,
        extra_imported=in_memory_imported,
        layout=layout,
    )
    if is_isolated:
        root_skills_dir = target_dir / "skills"
        if root_skills_dir.exists() and not _is_reparse_or_symlink(root_skills_dir):
            for ext_skill in sorted(root_skills_dir.glob("*/SKILL.md")):
                preserved_external.append(ext_skill.relative_to(target_dir).as_posix())
    agents_rules_dir = target_dir / ".agents" / "rules"
    if agents_rules_dir.exists() and not _is_reparse_or_symlink(agents_rules_dir):
        for ext_rule in sorted(agents_rules_dir.glob("*.md")):
            ext_rel = ext_rule.relative_to(target_dir).as_posix()
            if ext_rel not in desired_entries:
                preserved_external.append(ext_rel)
    canonical_digest = sync_adapters.compute_canonical_digest(framework_root)

    # Pre-validate safety on all desired paths and any existing lockfile paths
    for rel in desired_entries:
        assert_safe_target_path(target_dir, rel, label="planned destination")
    for rel in prev_managed:
        assert_safe_target_path(target_dir, rel, label="locked file")
    for rel in pending_recovery:
        assert_safe_target_path(target_dir, rel, label="pending recovery path")

    writes_to_apply: List[Tuple[str, bytes]] = []
    prunes_to_apply: List[str] = []
    pending_entries_payload: Dict[str, Dict[str, object]] = {}
    new_managed_files: Dict[str, Dict[str, object]] = {}

    # Classify obsolete lockfile entries not in desired plan
    for old_rel, old_entry in sorted(prev_managed.items()):
        if old_rel in desired_entries:
            continue
        old_path = target_dir / Path(old_rel)
        if not old_path.exists():
            continue
        if _is_prunable_path(old_rel, str(old_entry["ownership"])):
            disk_hash = sha256_file(old_path)
            if disk_hash == old_entry["sha256"]:
                pruned.append(old_rel)
                prunes_to_apply.append(old_rel)
            else:
                conflicts_preserved.append(old_rel)
                skipped_modified.append(old_rel)
                preserved_entry = dict(old_entry)
                preserved_entry["ownership"] = "consumer_customized_generated"
                preserved_entry["platforms"] = []
                new_managed_files[old_rel] = preserved_entry
        else:
            new_managed_files[old_rel] = dict(old_entry)

    # Classify desired entries
    for dst_rel, meta in sorted(desired_entries.items()):
        src_bytes = bytes(meta["bytes"])
        src_hash = sha256_bytes(src_bytes)
        dst_path = target_dir / Path(dst_rel)
        desired_lock_entry = _build_lockfile_entry(meta, data_hash=src_hash)

        if not dst_path.exists():
            created.append(dst_rel)
            writes_to_apply.append((dst_rel, src_bytes))
            pending_entries_payload[dst_rel] = desired_lock_entry
            new_managed_files[dst_rel] = desired_lock_entry
            continue

        current_hash = sha256_file(dst_path)
        prev_entry = prev_managed.get(dst_rel)
        rec_entry = pending_recovery.get(dst_rel)

        if current_hash == src_hash:
            unchanged.append(dst_rel)
            if rec_entry and current_hash == rec_entry["sha256"] and not prev_entry:
                recovered.append(dst_rel)
            new_managed_files[dst_rel] = desired_lock_entry
            continue

        # Interrupted bootstrap recovery: file matches pending_entry or previous locked hash
        recovered_unmodified = bool(
            rec_entry and (current_hash == rec_entry["sha256"] or (prev_entry and current_hash == prev_entry["sha256"]))
        )
        can_update_existing = bool(
            (update_mode and prev_entry and current_hash == prev_entry["sha256"]) or recovered_unmodified
        )

        if can_update_existing:
            updated.append(dst_rel)
            if recovered_unmodified:
                recovered.append(dst_rel)
            writes_to_apply.append((dst_rel, src_bytes))
            pending_entries_payload[dst_rel] = desired_lock_entry
            new_managed_files[dst_rel] = desired_lock_entry
        elif prev_entry or rec_entry:
            skipped_modified.append(dst_rel)
            conflicts_preserved.append(dst_rel)
            new_managed_files[dst_rel] = dict(prev_entry if prev_entry else rec_entry)
        elif dst_rel in imported_entries:
            updated.append(dst_rel)
            writes_to_apply.append((dst_rel, src_bytes))
            pending_entries_payload[dst_rel] = desired_lock_entry
            new_managed_files[dst_rel] = desired_lock_entry
        else:
            # Exists on disk with no prior lock provenance -> unknown_untracked, never overwrite
            skipped_modified.append(dst_rel)
            unknown_preserved.append(dst_rel)

    # Check Tier 3 consumer-owned files existence (created only if absent)
    optional_packs_payload = {
        "communication": ["caveman", "rtk-cli", "i-have-adhd", "humanizer"] if "communication" in canonical_packs else [],
        "contextEngineering": (
            [
                "context-optimization",
                "context-compression",
                "filesystem-context",
                "memory-systems",
                "session-handoff",
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
            "disabled": {
                "skills": [],
                "agents": [],
                "phases": [],
                "gates": [],
                "mechanisms": [],
            },
            "customizations": {
                "overlayDir": str(layout["overlay_default"]),
                "promptInjectionMode": "inline",
                "inlineMaxBytes": 16384,
            },
            "qualityGates": {
                "requireTddRedGreen": True,
                "requireIndependentCodeReview": True,
                "requireGraphifyCheck": True,
                "minimumTestCoveragePercent": 80,
            },
            "security": {
                "enforcePreCommitSecretScan": True,
                "allowActiveSecurityTesting": False,
                "strixProfilePath": f"{fw_prefix}security/strix-profile.yaml",
            },
            "paths": {
                "specsDir": "docs/specs",
                "adrDir": "docs/adr",
                "plansDir": "docs/plans",
                "retrospectivesDir": "docs/retrospectives",
                "stateDir": state_rel,
            },
        }
        tier3_writes.append((config_rel, (json.dumps(config_payload, indent=2) + "\n").encode("utf-8")))
    elif update_mode:
        try:
            existing_cfg = json.loads(config_path.read_text(encoding="utf-8"))
            changed = False
            if existing_cfg.get("frameworkVersion") != FRAMEWORK_VERSION:
                existing_cfg["frameworkVersion"] = FRAMEWORK_VERSION
                changed = True
            if existing_cfg.get("enabledPlatforms") != platforms:
                existing_cfg["enabledPlatforms"] = list(platforms)
                changed = True
            if existing_cfg.get("optionalSkillPacks") != optional_packs_payload:
                existing_cfg["optionalSkillPacks"] = optional_packs_payload
                changed = True
            if normalized_stacks and existing_cfg.get("stacks") != normalized_stacks:
                existing_cfg["stacks"] = normalized_stacks
                changed = True
            if changed:
                updated.append(config_rel)
                tier3_writes.append((config_rel, (json.dumps(existing_cfg, indent=2) + "\n").encode("utf-8")))
            else:
                unchanged.append(config_rel)
        except Exception:
            unchanged.append(config_rel)
    else:
        unchanged.append(config_rel)

    manifest_rel = f"{state_rel}/manifest.json"
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
        tier3_writes.append((manifest_rel, (json.dumps(manifest_payload, indent=2) + "\n").encode("utf-8")))
    else:
        unchanged.append(manifest_rel)

    if is_isolated:
        aief_gi_rel = ".aief/.gitignore"
        aief_gi_path = target_dir / Path(aief_gi_rel)
        if not aief_gi_path.exists():
            created.append(aief_gi_rel)
            tier3_writes.append((aief_gi_rel, b"# Ephemeral framework runtime state\nstate/\nlock.json.tmp\n"))
        else:
            unchanged.append(aief_gi_rel)

    if normalized_stacks:
        gitignore_content = _compose_stack_gitignore(framework_root, normalized_stacks, isolated=is_isolated)
        gitignore_path = target_dir / ".gitignore"
        rec_gitignore_rel = ".aief/gitignore.recommended" if is_isolated else ".gitignore.framework-recommended"
        rec_gitignore_path = target_dir / Path(rec_gitignore_rel)

        if not gitignore_path.exists():
            created.append(".gitignore")
            tier3_writes.append((".gitignore", gitignore_content.encode("utf-8")))
        else:
            unchanged.append(".gitignore")
            current_gi = gitignore_path.read_text(encoding="utf-8").replace("\r\n", "\n")
            if current_gi != gitignore_content:
                if not rec_gitignore_path.exists():
                    created.append(rec_gitignore_rel)
                    tier3_writes.append((rec_gitignore_rel, gitignore_content.encode("utf-8")))
                else:
                    unchanged.append(rec_gitignore_rel)

        preflight_rel = ".aief/ENVIRONMENT_PREFLIGHT.md" if is_isolated else "docs/ENVIRONMENT_PREFLIGHT.md"
        preflight_path = target_dir / Path(preflight_rel)
        if not preflight_path.exists():
            created.append(preflight_rel)
            if not dry_run:
                pf_report = preflight.run_preflight_checks(normalized_stacks, project_root=target_dir)
                pf_md = preflight.render_preflight_markdown(pf_report)
                tier3_writes.append((preflight_rel, pf_md.encode("utf-8")))
        else:
            unchanged.append(preflight_rel)

    custom_inst_rel = validate_safe_rel_path(f"{overlay_rel}/instructions.md", label="custom instructions")
    custom_inst_path = assert_safe_target_path(target_dir, custom_inst_rel, label="custom instructions")
    if not custom_inst_path.exists():
        created.append(custom_inst_rel)
        tier3_writes.append((custom_inst_rel, compose.DEFAULT_CUSTOM_INSTRUCTIONS_TEMPLATE.encode("utf-8")))
    else:
        unchanged.append(custom_inst_rel)

    final_lock_payload = _build_v2_lock_payload(
        platforms=platforms,
        canonical_packs=canonical_packs,
        normalized_stacks=normalized_stacks,
        canonical_digest=canonical_digest,
        status="completed",
        projected_skills=projected_skills_summary,
        managed_files=new_managed_files,
        last_successful=proj_state.get("last_successful_projection"),
        pending_entries={},
    )
    final_lock_bytes = (json.dumps(final_lock_payload, indent=2) + "\n").encode("utf-8")

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)
        init_dirs = (
            [
                f"{state_rel}/handoffs",
                f"{state_rel}/session-handoffs",
                f"{state_rel}/scratch",
                f"{overlay_rel}/rules",
                f"{overlay_rel}/skills",
                f"{overlay_rel}/prompts",
            ]
            if is_isolated
            else [
                "docs/specs",
                "docs/adr",
                "docs/plans",
                "docs/retrospectives",
                f"{state_rel}/handoffs",
                f"{state_rel}/scratch",
            ]
        )
        for sub in init_dirs:
            (target_dir / Path(sub)).mkdir(parents=True, exist_ok=True)

        # Back up v0.3.0 lockfile cleanly before upgrading to v2.0.0
        if migrated_from == "0.3.0" and existing_lock["raw_bytes"]:
            backup_path = assert_safe_target_path(target_dir, lock_backup_rel, label="lockfile backup")
            if not backup_path.exists():
                _atomic_write_bytes(backup_path, bytes(existing_lock["raw_bytes"]))

        need_lock_write = not lock_path.exists() or existing_lock["raw_bytes"] != final_lock_bytes
        if writes_to_apply or prunes_to_apply or pending_recovery:
            # Phase 1: Flush intent lockfile (status = in_progress, pending_entries)
            intent_payload = _build_v2_lock_payload(
                platforms=platforms,
                canonical_packs=canonical_packs,
                normalized_stacks=normalized_stacks,
                canonical_digest=canonical_digest,
                status="in_progress",
                projected_skills=projected_skills_summary,
                managed_files=prev_managed,
                last_successful=proj_state.get("last_successful_projection"),
                pending_entries=pending_entries_payload,
            )
            _atomic_write_bytes(lock_path, (json.dumps(intent_payload, indent=2) + "\n").encode("utf-8"))

            # Phase 2: Atomic per-file writes and safe pruning
            for rel, data in writes_to_apply:
                dst = assert_safe_target_path(target_dir, rel, label="write destination")
                _atomic_write_bytes(dst, data)

            for old_rel in prunes_to_apply:
                old_path = assert_safe_target_path(target_dir, old_rel, label="prune destination")
                if old_path.exists() and not _is_reparse_or_symlink(old_path):
                    old_path.unlink()
            if prunes_to_apply:
                _cleanup_empty_dirs(target_dir, prunes_to_apply)

        for t3_rel, t3_bytes in tier3_writes:
            dst = assert_safe_target_path(target_dir, t3_rel, label="tier3 destination")
            _atomic_write_bytes(dst, t3_bytes)

        # Phase 3: Commit final completed lockfile only if needed (zero-write when idempotent)
        if need_lock_write or writes_to_apply or prunes_to_apply or pending_recovery:
            _atomic_write_bytes(lock_path, final_lock_bytes)

    return {
        "created": created,
        "updated": updated,
        "unchanged": unchanged,
        "skipped_modified": skipped_modified,
        "pruned": pruned,
        "conflicts_preserved": conflicts_preserved,
        "unknown_preserved": unknown_preserved,
        "recovered": recovered,
        "imported": imported_files,
        "preserved_external": preserved_external,
        "migrated_from": migrated_from,
        "layout": layout["mode"],
    }


def parse_csv_list(raw: str, allowed: Set[str], flag_name: str) -> List[str]:
    if not raw.strip():
        return []
    items = [p.strip() for p in raw.split(",") if p.strip()]
    invalid = [p for p in items if p not in allowed]
    if invalid:
        raise ValueError(f"Invalid value(s) for {flag_name}: {invalid}. Allowed: {sorted(allowed)}")
    return items


def detect_project_stacks(target_dir: Path) -> List[str]:
    """Auto-detect technology stacks (.NET, Node/Angular, Python) from repository files."""
    if not target_dir.exists():
        return []
    detected: List[str] = []
    skip_dirs = {".git", "node_modules", "bin", "obj", "dist", ".angular", "__pycache__"}

    # Check root and immediate child directories cleanly without deep scanning
    candidates: List[Path] = [target_dir]
    try:
        for child in sorted(target_dir.iterdir()):
            if child.is_dir() and child.name not in skip_dirs and not _is_reparse_or_symlink(child):
                candidates.append(child)
    except OSError:
        pass

    has_dotnet = False
    has_node = False
    has_python = False
    for d in candidates:
        try:
            for item in d.iterdir():
                if not item.is_file():
                    continue
                if item.suffix.lower() in {".sln", ".csproj", ".fsproj"}:
                    has_dotnet = True
                elif item.name in {"package.json", "angular.json"}:
                    has_node = True
                elif item.name in {"pyproject.toml", "requirements.txt", "setup.py"}:
                    has_python = True
        except OSError:
            continue

    if has_dotnet:
        detected.append("dotnet")
    if has_node:
        detected.append("node-angular")
    if has_python:
        detected.append("python")
    return detected


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap or update AI Engineering Framework in a target repository."
    )
    parser.add_argument(
        "target_pos",
        nargs="?",
        type=Path,
        help="Target project directory (alternative to --target)",
    )
    parser.add_argument("--target", type=Path, dest="target_flag", help="Target project directory")
    parser.add_argument(
        "--platforms",
        type=str,
        default=None,
        help=f"Comma-separated platforms (default: all 5: {','.join(ALL_PLATFORMS)})",
    )
    parser.add_argument(
        "--profile",
        type=str,
        choices=["full", "standard", "hotfix"],
        default=None,
        help="Workflow profile in project.framework.json (default: standard)",
    )
    parser.add_argument(
        "--optional-packs",
        type=str,
        default=None,
        help="Comma-separated optional packs (default: all; options: none,all,communication,context-engineering,agent-architecture,frontend-design/design-ui,growth-media)",
    )
    parser.add_argument(
        "--stacks",
        type=str,
        default=None,
        help="Technology stacks for .gitignore/preflight (default: auto; options: auto,none,dotnet,node/angular,python)",
    )
    parser.add_argument("--update", action="store_true", help="Update unmodified framework-managed files")
    parser.add_argument("--dry-run", action="store_true", help="Preview file operations without writing to disk")
    args = parser.parse_args(argv)

    target_arg = args.target_flag or args.target_pos
    if target_arg is None:
        parser.error("Target path required (e.g. `python scripts/bootstrap.py D:\\path\\to\\project`).")

    # Resolve existing consumer preferences automatically during --update when flags are omitted
    layout = compose.resolve_consumer_layout(target_arg)
    existing_cfg: Dict[str, object] = {}
    existing_lock_raw: Dict[str, object] = {}
    if args.update:
        cfg_file = target_arg / Path(str(layout["config_rel"]))
        lock_file = target_arg / Path(str(layout["lock_rel"]))
        if cfg_file.exists():
            try:
                loaded = json.loads(cfg_file.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    existing_cfg = loaded
            except Exception:
                pass
        if lock_file.exists():
            try:
                loaded_lk = json.loads(lock_file.read_text(encoding="utf-8"))
                if isinstance(loaded_lk, dict):
                    existing_lock_raw = loaded_lk
            except Exception:
                pass

    try:
        if args.platforms is not None:
            platforms = parse_csv_list(args.platforms, set(ALL_PLATFORMS), "--platforms")
        elif args.update and isinstance(existing_cfg.get("enabledPlatforms"), list):
            platforms = parse_csv_list(
                ",".join(str(p) for p in existing_cfg["enabledPlatforms"]),
                set(ALL_PLATFORMS),
                "project.framework.json enabledPlatforms",
            )
        else:
            platforms = list(ALL_PLATFORMS)

        profile = (
            args.profile
            or (str(existing_cfg["workflowProfile"]) if args.update and existing_cfg.get("workflowProfile") else "standard")
        )

        if args.optional_packs is not None:
            raw_packs = [p.strip() for p in args.optional_packs.split(",") if p.strip()]
            optional_packs = normalize_optional_packs(raw_packs)
        elif args.update and isinstance(existing_lock_raw.get("optional_packs"), list):
            optional_packs = normalize_optional_packs([str(p) for p in existing_lock_raw["optional_packs"]])
        else:
            optional_packs = normalize_optional_packs(["all"])

        if args.stacks is not None:
            raw_stacks_str = args.stacks.strip()
            if raw_stacks_str.lower() == "none":
                stacks = []
            elif raw_stacks_str.lower() == "auto":
                stacks = detect_project_stacks(target_arg)
            else:
                raw_stacks = [s.strip() for s in raw_stacks_str.split(",") if s.strip()]
                stacks = preflight.normalize_stacks(raw_stacks)
        elif args.update and isinstance(existing_cfg.get("stacks"), list) and existing_cfg["stacks"]:
            stacks = preflight.normalize_stacks([str(s) for s in existing_cfg["stacks"]])
        else:
            stacks = detect_project_stacks(target_arg)

        summary = bootstrap_project(
            target_dir=target_arg,
            platforms=platforms,
            profile=profile,
            optional_packs=optional_packs,
            stacks=stacks,
            update_mode=args.update,
            dry_run=args.dry_run,
        )
    except (ValueError, LockfileError) as exc:
        print(f"BOOTSTRAP_ERROR: {exc}", file=sys.stderr)
        return 2

    mode_label = "DRY-RUN" if args.dry_run else ("UPDATE" if args.update else "BOOTSTRAP")
    print(f"=== AI Engineering Framework {mode_label} ({target_arg.resolve()}) ===")
    print(f"  Layout:             {summary['layout']} ({'.aief/' if summary['layout'] == 'isolated' else 'legacy root'})")
    print(f"  Platforms:          {', '.join(platforms)}")
    print(f"  Optional Packs:     {', '.join(optional_packs) if optional_packs else 'none (core-only)'}")
    if stacks:
        print(f"  Stacks (detected):  {', '.join(stacks)}")
    print(f"  Created:            {len(summary['created'])}")
    print(f"  Updated:            {len(summary['updated'])}")
    if summary.get("updated") and len(summary["updated"]) <= 15:
        print(f"  Updated Paths:      {', '.join(summary['updated'])}")
    print(f"  Unchanged:          {len(summary['unchanged'])}")
    print(f"  Pruned:             {len(summary['pruned'])}")
    print(f"  Skipped/Modified:   {len(summary['skipped_modified'])} (preserved)")
    if summary.get("imported"):
        print(f"  Imported Custom:    {', '.join(summary['imported'])}")
    if summary.get("preserved_external"):
        print(f"  Preserved External: {', '.join(summary['preserved_external'])}")
    if summary.get("unknown_preserved"):
        print(f"  Unknown Preserved:  {len(summary['unknown_preserved'])}")
    if summary.get("recovered"):
        print(f"  Recovered Pending:  {len(summary['recovered'])}")
    if summary.get("migrated_from"):
        print(f"  Lockfile Migrated:  {summary['migrated_from']} -> {LOCKFILE_SCHEMA_VERSION}")
    if shutil.which("graphify") is None:
        print("  Graphify CLI:       NOT INSTALLED (optional AST graph; install with 'pipx install graphifyy' or 'pip install graphifyy')")
    else:
        print("  Graphify CLI:       AVAILABLE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
