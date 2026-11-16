#!/usr/bin/env python3
"""Bootstrap or non-destructively update the AI Engineering Framework in a target project.

Key Guarantees:
1. Tier 3 Consumer-Owned Files (project.framework.json, docs/specs/, docs/adr/, docs/plans/, README.md)
   are NEVER overwritten if they already exist in the target project.
2. Tier 1 & Tier 2 Framework-Managed Files (core/, agents/, skills/core/, workflows/, platform adapters)
   are tracked in `.framework-lock.json` with SHA-256 hashes.
3. During `--update`, if a user has locally customized a framework-managed file (its current SHA-256 differs
   from the hash recorded in `.framework-lock.json`), the file is preserved and skipped rather than overwritten.

Usage:
    python scripts/bootstrap.py --target /path/to/project --dry-run
    python scripts/bootstrap.py --target /path/to/project --platforms antigravity,copilot,claude-code
    python scripts/bootstrap.py --target /path/to/project --update
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Dict, List, Set

FRAMEWORK_ROOT = Path(__file__).resolve().parent.parent
FRAMEWORK_VERSION = "0.1.0"
LOCKFILE_NAME = ".framework-lock.json"

ALL_PLATFORMS = ["antigravity", "copilot", "claude-code", "codex", "gemini-cli"]

# Tier 1 files always installed into the consumer project
CORE_MANAGED_GLOBS = [
    "core/rules/*.md",
    "core/schemas/*.json",
    "agents/*.md",
    "skills/registry.json",
    "skills/core/*/*.md",
    "workflows/*.md",
    "quality/*.md",
    "security/*.md",
    "security/*.yaml",
    "templates/*",
    "scripts/validate.py",
    "scripts/sync_adapters.py",
]

# Platform-specific file mappings: (source_rel_in_framework, target_rel_in_consumer)
PLATFORM_ADAPTER_MAPPINGS: Dict[str, List[Tuple[str, str]]] = {
    "antigravity": [
        ("GEMINI.md", "GEMINI.md"),
        ("AGENTS.md", "AGENTS.md"),
        ("adapters/antigravity/rules/framework-core.md", ".agents/rules/framework-core.md"),
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

OPTIONAL_PACK_GLOBS: Dict[str, str] = {
    "communication": "skills/optional/communication/*/*.md",
    "frontend-design": "skills/optional/frontend-design/*/*.md",
    "growth-media": "skills/optional/growth-media/*/*.md",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def collect_managed_plan(
    framework_root: Path,
    platforms: List[str],
    optional_packs: List[str],
) -> Dict[str, Path]:
    """Return mapping of {target_rel_posix_path: source_abs_path}."""
    plan: Dict[str, Path] = {}

    for pattern in CORE_MANAGED_GLOBS:
        for src in sorted(framework_root.glob(pattern)):
            if src.is_file():
                rel = src.relative_to(framework_root).as_posix()
                plan[rel] = src

    for pack in optional_packs:
        glob_pat = OPTIONAL_PACK_GLOBS.get(pack)
        if glob_pat:
            for src in sorted(framework_root.glob(glob_pat)):
                if src.is_file():
                    rel = src.relative_to(framework_root).as_posix()
                    plan[rel] = src

    for plat in platforms:
        for src_rel, dst_rel in PLATFORM_ADAPTER_MAPPINGS.get(plat, []):
            src = framework_root / Path(src_rel)
            if src.exists():
                plan[dst_rel] = src
                # Also keep the canonical adapter copy under adapters/ so validate.py passes
                plan[src_rel] = src

    return plan


def bootstrap_project(
    target_dir: Path,
    platforms: List[str],
    profile: str = "standard",
    optional_packs: List[str] | None = None,
    update_mode: bool = False,
    dry_run: bool = False,
    framework_root: Path = FRAMEWORK_ROOT,
) -> Dict[str, List[str]]:
    """Bootstrap or update the framework in target_dir non-destructively."""
    optional_packs = optional_packs if optional_packs is not None else ["communication"]
    target_dir = target_dir.resolve()

    lock_path = target_dir / LOCKFILE_NAME
    existing_lock: Dict[str, object] = {}
    locked_hashes: Dict[str, str] = {}
    if lock_path.exists():
        existing_lock = json.loads(lock_path.read_text(encoding="utf-8"))
        locked_hashes = dict(existing_lock.get("managed_files", {}))

    plan = collect_managed_plan(framework_root, platforms, optional_packs)

    created: List[str] = []
    updated: List[str] = []
    unchanged: List[str] = []
    skipped_modified: List[str] = []

    new_locked_hashes: Dict[str, str] = dict(locked_hashes)

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)
        for sub in ["docs/specs", "docs/adr", "docs/plans", "docs/retrospectives", ".framework-state/handoffs"]:
            (target_dir / Path(sub)).mkdir(parents=True, exist_ok=True)

    for dst_rel, src_path in sorted(plan.items()):
        dst_path = target_dir / Path(dst_rel)
        src_bytes = src_path.read_bytes()
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

        # Destination exists and differs from source
        previous_locked_hash = locked_hashes.get(dst_rel)
        if update_mode and previous_locked_hash and current_hash == previous_locked_hash:
            # File was not modified by user since last install; safe to update
            updated.append(dst_rel)
            if not dry_run:
                dst_path.write_bytes(src_bytes)
            new_locked_hashes[dst_rel] = src_hash
        else:
            # Either not in update_mode or user customized this file locally -> preserve user file!
            skipped_modified.append(dst_rel)

    # Consumer-owned project.framework.json (Tier 3 - create ONLY if missing)
    config_rel = "project.framework.json"
    config_path = target_dir / config_rel
    if not config_path.exists():
        created.append(config_rel)
        config_payload = {
            "$schema": "./core/schemas/framework-config.schema.json",
            "frameworkVersion": FRAMEWORK_VERSION,
            "projectName": target_dir.name,
            "workflowProfile": profile,
            "enabledPlatforms": platforms,
            "optionalSkillPacks": {
                "communication": ["caveman"] if "communication" in optional_packs else [],
                "frontendDesign": ["web-design-guidelines", "canvas-design"] if "frontend-design" in optional_packs else [],
                "growthMedia": (
                    ["seo-audit", "ai-seo", "video-lens", "video-use", "content-strategy", "pricing"]
                    if "growth-media" in optional_packs
                    else []
                ),
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
    else:
        unchanged.append(config_rel)

    if not dry_run:
        lock_payload = {
            "framework_version": FRAMEWORK_VERSION,
            "platforms": platforms,
            "optional_packs": optional_packs,
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
        default="communication",
        help="Comma-separated optional packs (communication,frontend-design,growth-media)",
    )
    parser.add_argument("--update", action="store_true", help="Update unmodified framework-managed files")
    parser.add_argument("--dry-run", action="store_true", help="Preview file operations without writing to disk")
    args = parser.parse_args(argv)

    try:
        platforms = parse_csv_list(args.platforms, set(ALL_PLATFORMS), "--platforms")
        optional_packs = parse_csv_list(args.optional_packs, set(OPTIONAL_PACK_GLOBS.keys()), "--optional-packs")
    except ValueError as exc:
        print(f"BOOTSTRAP_ERROR: {exc}", file=sys.stderr)
        return 2

    summary = bootstrap_project(
        target_dir=args.target,
        platforms=platforms,
        profile=args.profile,
        optional_packs=optional_packs,
        update_mode=args.update,
        dry_run=args.dry_run,
    )

    mode_label = "DRY-RUN" if args.dry_run else ("UPDATE" if args.update else "BOOTSTRAP")
    print(f"=== AI Engineering Framework {mode_label} ({args.target.resolve()}) ===")
    print(f"  Created:          {len(summary['created'])}")
    print(f"  Updated:          {len(summary['updated'])}")
    print(f"  Unchanged:        {len(summary['unchanged'])}")
    print(f"  Skipped/Modified: {len(summary['skipped_modified'])} (user customizations preserved)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
