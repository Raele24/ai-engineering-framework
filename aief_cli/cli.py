"""Unified `aief` CLI entrypoint wrapping canonical framework stdlib scripts."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
from typing import List

from . import __version__, resolve_framework_root


def _run_script(script_path: Path, script_args: List[str]) -> int:
    proc = subprocess.run([sys.executable, str(script_path), *script_args], check=False)
    return int(proc.returncode)


def _resolve_consumer_or_bundled(target_dir: Path, script_name: str, framework_root: Path) -> Path:
    local_script = target_dir / "scripts" / script_name
    if local_script.is_file():
        return local_script
    return framework_root / "scripts" / script_name


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aief",
        description="AI Engineering Framework CLI (init, update, compose, validate, preflight).",
    )
    parser.add_argument("--version", action="version", version=f"ai-engineering-framework {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    for cmd_name, help_text in (
        ("init", "Bootstrap AI Engineering Framework into a project (default: current directory)"),
        ("update", "Non-destructively update framework-managed files in a project"),
    ):
        p = sub.add_parser(cmd_name, help=help_text)
        p.add_argument("target", nargs="?", default=".", help="Target repository directory (default: .)")
        p.add_argument("--platforms", type=str, default=None, help="Comma-separated platforms")
        p.add_argument("--profile", type=str, choices=["full", "standard", "hotfix"], default=None, help="Workflow profile")
        p.add_argument("--optional-packs", type=str, default=None, help="Comma-separated optional skill packs")
        p.add_argument("--stacks", type=str, default=None, help="Stacks: auto, none, dotnet, node/angular, python")
        p.add_argument("--dry-run", action="store_true", help="Preview changes without modifying files")

    p_compose = sub.add_parser("compose", help="Re-compose inline instructions, toggles, prompts, and MCPs")
    p_compose.add_argument("target", nargs="?", default=".", help="Consumer repository directory (default: .)")
    p_compose.add_argument("--dry-run", action="store_true", help="Preview composition without writing")
    p_compose.add_argument("--no-validate", action="store_true", help="Skip automatic post-compose validation")

    p_val = sub.add_parser("validate", help="Validate framework or consumer repository integrity")
    p_val.add_argument("target", nargs="?", default=".", help="Repository root directory (default: .)")
    p_val.add_argument("--mode", type=str, choices=["auto", "framework", "consumer"], default="auto", help="Validation mode")
    p_val.add_argument("--json", action="store_true", help="Emit validation report as JSON")

    p_pre = sub.add_parser("preflight", help="Check SDK/tooling prerequisites without modifying the host")
    p_pre.add_argument("target", nargs="?", default=".", help="Repository root directory (default: .)")
    p_pre.add_argument("--stacks", type=str, default="dotnet,node-angular,python", help="Comma-separated stacks")
    p_pre.add_argument("--json", action="store_true", help="Emit preflight report as JSON")

    sub.add_parser("check-sync", help="Verify upstream canonical adapter synchronization")
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    framework_root = resolve_framework_root()

    if args.command in {"init", "update"}:
        target = Path(args.target).resolve()
        cmd_args = [str(target)]
        if args.platforms is not None:
            cmd_args.extend(["--platforms", args.platforms])
        if args.profile is not None:
            cmd_args.extend(["--profile", args.profile])
        if args.optional_packs is not None:
            cmd_args.extend(["--optional-packs", args.optional_packs])
        if args.stacks is not None:
            cmd_args.extend(["--stacks", args.stacks])
        if args.command == "update":
            cmd_args.append("--update")
        if args.dry_run:
            cmd_args.append("--dry-run")
        return _run_script(framework_root / "scripts" / "bootstrap.py", cmd_args)

    if args.command == "compose":
        target = Path(args.target).resolve()
        cmd_args = ["--root", str(target)]
        if args.dry_run:
            cmd_args.append("--dry-run")
        if args.no_validate:
            cmd_args.append("--no-validate")
        script = _resolve_consumer_or_bundled(target, "compose.py", framework_root)
        return _run_script(script, cmd_args)

    if args.command == "validate":
        target = Path(args.target).resolve()
        cmd_args = ["--root", str(target), "--mode", args.mode]
        if args.json:
            cmd_args.append("--json")
        script = _resolve_consumer_or_bundled(target, "validate.py", framework_root)
        return _run_script(script, cmd_args)

    if args.command == "preflight":
        target = Path(args.target).resolve()
        cmd_args = ["--root", str(target), "--stacks", args.stacks]
        if args.json:
            cmd_args.append("--json")
        script = _resolve_consumer_or_bundled(target, "preflight.py", framework_root)
        return _run_script(script, cmd_args)

    if args.command == "check-sync":
        cwd = Path.cwd().resolve()
        if (cwd / "PROJECT_CHARTER.md").is_file() and (cwd / "scripts" / "sync_adapters.py").is_file():
            return _run_script(cwd / "scripts" / "sync_adapters.py", ["--check"])
        if (framework_root / "PROJECT_CHARTER.md").is_file() and (framework_root / "scripts" / "sync_adapters.py").is_file():
            return _run_script(framework_root / "scripts" / "sync_adapters.py", ["--check"])
        print(
            "CHECK_SYNC_ERROR: 'aief check-sync' requires an upstream framework checkout containing PROJECT_CHARTER.md and scripts/sync_adapters.py.",
            file=sys.stderr,
        )
        return 2

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
