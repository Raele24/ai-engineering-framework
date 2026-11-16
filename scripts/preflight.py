#!/usr/bin/env python3
"""Environment preflight and stack SDK detector for AI Engineering Framework consumer projects.

Features:
- Detects .NET SDKs across system PATH, DOTNET_ROOT, and Windows user-space ($HOME/.dotnet).
- Detects Node.js / npm / Angular CLI availability.
- Detects Python 3.10+ runtime availability.
- Never installs SDKs or mutates system state automatically; emits clear remediation guidance.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from typing import Dict, List, Set

STACK_ALIASES: Dict[str, str] = {
    "dotnet": "dotnet",
    ".net": "dotnet",
    "node": "node-angular",
    "angular": "node-angular",
    "node-angular": "node-angular",
    "node/angular": "node-angular",
    "python": "python",
    "py": "python",
}

SUPPORTED_STACKS: Set[str] = {"dotnet", "node-angular", "python"}


def normalize_stacks(raw_stacks: List[str]) -> List[str]:
    """Normalize stack identifiers while preserving order and uniqueness."""
    normalized: List[str] = []
    invalid: List[str] = []
    for item in raw_stacks:
        token = item.strip().lower()
        if not token:
            continue
        mapped = STACK_ALIASES.get(token)
        if not mapped:
            invalid.append(item)
        elif mapped not in normalized:
            normalized.append(mapped)
    if invalid:
        raise ValueError(
            f"Unsupported stack(s): {invalid}. Supported stacks: dotnet, node/angular (node-angular), python"
        )
    return normalized


def _list_dotnet_sdks(dotnet_bin: Path, run_env: Dict[str, str]) -> List[str]:
    try:
        proc = subprocess.run(
            [str(dotnet_bin), "--list-sdks"],
            env=run_env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
        )
        if proc.returncode != 0:
            return []
        return [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def detect_dotnet_sdk(
    env: Dict[str, str] | None = None,
    home_dir: Path | None = None,
) -> Dict[str, object]:
    """Detect .NET SDK availability across PATH, DOTNET_ROOT, and user-space ($HOME/.dotnet)."""
    effective_env = dict(os.environ) if env is None else dict(env)
    effective_home = home_dir if home_dir is not None else Path.home()
    is_windows = platform.system().lower().startswith("win")
    exe_name = "dotnet.exe" if is_windows else "dotnet"

    # 1. Check dotnet on PATH
    path_str = effective_env.get("PATH", "")
    which_dotnet = shutil.which("dotnet", path=path_str) if path_str else None
    if which_dotnet:
        bin_path = Path(which_dotnet)
        sdks = _list_dotnet_sdks(bin_path, effective_env)
        if sdks:
            return {
                "stack": "dotnet",
                "status": "AVAILABLE",
                "executable": str(bin_path),
                "dotnet_root": str(bin_path.parent),
                "sdks": sdks,
                "guidance": f".NET SDK detected on PATH ({sdks[0]}).",
            }

    # 2. Check explicit DOTNET_ROOT or user-space $HOME/.dotnet
    candidate_roots: List[Path] = []
    env_root = effective_env.get("DOTNET_ROOT")
    if env_root:
        candidate_roots.append(Path(env_root))
    candidate_roots.append(effective_home / ".dotnet")

    for root_dir in candidate_roots:
        candidate_bin = root_dir / exe_name
        if candidate_bin.exists() and candidate_bin.is_file():
            probe_env = dict(effective_env)
            probe_env["DOTNET_ROOT"] = str(root_dir)
            probe_env["PATH"] = f"{root_dir}{os.pathsep}{probe_env.get('PATH', '')}"
            sdks = _list_dotnet_sdks(candidate_bin, probe_env)
            if sdks:
                root_str = str(root_dir)
                return {
                    "stack": "dotnet",
                    "status": "AVAILABLE_USER_SPACE",
                    "executable": str(candidate_bin),
                    "dotnet_root": root_str,
                    "sdks": sdks,
                    "guidance": (
                        f"User-space .NET SDK detected at '{root_str}' ({sdks[0]}), "
                        "but not active on default PATH. Configure your shell before running dotnet commands:\n"
                        f'  PowerShell: $env:DOTNET_ROOT = "{root_str}"; $env:PATH = "{root_str};$env:PATH"\n'
                        f'  Bash/Zsh:   export DOTNET_ROOT="{root_str}" && export PATH="{root_str}:$PATH"'
                    ),
                }

    # 3. Missing
    return {
        "stack": "dotnet",
        "status": "MISSING",
        "executable": None,
        "dotnet_root": None,
        "sdks": [],
        "guidance": (
            ".NET SDK not found on PATH or in user-space ($HOME/.dotnet). Install manually:\n"
            "  Option A (Windows non-elevated user-space): Invoke-WebRequest https://dot.net/v1/dotnet-install.ps1 -OutFile dotnet-install.ps1; ./dotnet-install.ps1 -Channel LTS -InstallDir \"$HOME\\.dotnet\"\n"
            "  Option B (Windows elevated WinGet): winget install Microsoft.DotNet.SDK.10"
        ),
    }


def detect_node_angular(env: Dict[str, str] | None = None) -> Dict[str, object]:
    """Detect Node.js and npm availability."""
    effective_env = dict(os.environ) if env is None else dict(env)
    path_str = effective_env.get("PATH", "")
    node_bin = shutil.which("node", path=path_str) if path_str else None
    npm_bin = shutil.which("npm", path=path_str) if path_str else None

    if node_bin and npm_bin:
        try:
            proc = subprocess.run(
                [node_bin, "--version"],
                env=effective_env,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            node_ver = proc.stdout.strip() if proc.returncode == 0 else "unknown"
        except Exception:
            node_ver = "unknown"
        return {
            "stack": "node-angular",
            "status": "AVAILABLE",
            "node_executable": node_bin,
            "npm_executable": npm_bin,
            "node_version": node_ver,
            "guidance": f"Node.js ({node_ver}) and npm detected on PATH.",
        }

    return {
        "stack": "node-angular",
        "status": "MISSING",
        "node_executable": node_bin,
        "npm_executable": npm_bin,
        "node_version": None,
        "guidance": (
            "Node.js or npm not found on PATH. Install manually:\n"
            "  Windows (WinGet): winget install OpenJS.NodeJS.LTS\n"
            "  Angular CLI:      npm install -g @angular/cli"
        ),
    }


def detect_python() -> Dict[str, object]:
    """Detect Python 3.10+ runtime."""
    ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    ok = (sys.version_info.major, sys.version_info.minor) >= (3, 10)
    return {
        "stack": "python",
        "status": "AVAILABLE" if ok else "MISSING",
        "executable": sys.executable,
        "version": ver,
        "guidance": (
            f"Python {ver} detected ({sys.executable}). Create virtual environments via `python -m venv .venv`."
            if ok
            else f"Python 3.10+ required (found {ver}). Install Python 3.10+ from python.org or WinGet."
        ),
    }


def run_preflight_checks(
    stacks: List[str],
    env: Dict[str, str] | None = None,
    home_dir: Path | None = None,
) -> Dict[str, object]:
    """Execute preflight checks for the requested stacks."""
    normalized = normalize_stacks(stacks)
    results: Dict[str, Dict[str, object]] = {}
    for st in normalized:
        if st == "dotnet":
            results[st] = detect_dotnet_sdk(env=env, home_dir=home_dir)
        elif st == "node-angular":
            results[st] = detect_node_angular(env=env)
        elif st == "python":
            results[st] = detect_python()
    all_ready = all(r["status"] in ("AVAILABLE", "AVAILABLE_USER_SPACE") for r in results.values())
    return {
        "overall_status": "READY" if all_ready else "ACTION_REQUIRED",
        "stacks": results,
    }


def render_preflight_markdown(report: Dict[str, object]) -> str:
    """Render deterministic Markdown guidance for docs/ENVIRONMENT_PREFLIGHT.md."""
    lines = [
        "# Stack Environment Preflight Guidance (`docs/ENVIRONMENT_PREFLIGHT.md`)",
        "",
        "This document provides stack-specific environment verification and SDK guidance generated by the AI Engineering Framework.",
        "",
        "## Configured Stack Preflight Summary",
        "",
        "| Stack | Status | Guidance |",
        "| :--- | :--- | :--- |",
    ]
    stacks_map: Dict[str, Dict[str, object]] = report.get("stacks", {})  # type: ignore[assignment]
    for stack_name, info in stacks_map.items():
        status = str(info.get("status", "UNKNOWN"))
        guidance_first_line = str(info.get("guidance", "")).splitlines()[0] if info.get("guidance") else ""
        lines.append(f"| `{stack_name}` | `{status}` | {guidance_first_line} |")

    lines.extend(
        [
            "",
            "## Windows `.NET` User-Space SDK Configuration (`DOTNET_ROOT`)",
            "",
            "When `.NET SDK` is installed in user-space (`$HOME\\.dotnet`) rather than `C:\\Program Files\\dotnet` (or when `C:\\Program Files\\dotnet` contains only a runtime), export `DOTNET_ROOT` in every shell session before running `dotnet` commands:",
            "",
            "```powershell",
            '$env:DOTNET_ROOT = "$HOME\\.dotnet"',
            '$env:PATH = "$HOME\\.dotnet;$env:PATH"',
            "dotnet --list-sdks",
            "```",
            "",
            "## Re-running Preflight Verification",
            "",
            "```bash",
            "python scripts/preflight.py --stacks " + ",".join(stacks_map.keys()),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check stack SDK prerequisites without modifying the system.")
    parser.add_argument(
        "--stacks",
        type=str,
        default="dotnet,node-angular,python",
        help="Comma-separated stacks to check (dotnet,node-angular,python)",
    )
    parser.add_argument("--json", action="store_true", help="Emit preflight report as JSON")
    args = parser.parse_args(argv)

    raw_list = [s.strip() for s in args.stacks.split(",") if s.strip()]
    try:
        report = run_preflight_checks(raw_list)
    except ValueError as exc:
        print(f"PREFLIGHT_ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print("=== AI Engineering Framework Stack Preflight ===")
    for stack_name, info in report["stacks"].items():  # type: ignore[union-attr]
        print(f"  [{info['status']}] {stack_name}")
        for line in str(info["guidance"]).splitlines():
            print(f"      {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
