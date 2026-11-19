"""Packaged CLI wrapper for AI Engineering Framework."""

from __future__ import annotations

from pathlib import Path

__version__ = "0.4.0"


def resolve_framework_root() -> Path:
    """Resolve canonical framework asset root from either repo checkout or wheel _bundle."""
    pkg_dir = Path(__file__).resolve().parent
    bundled = pkg_dir / "_bundle"
    if (bundled / "core" / "rules" / "engineering-principles.md").is_file():
        return bundled
    repo_root = pkg_dir.parent
    if (repo_root / "core" / "rules" / "engineering-principles.md").is_file():
        return repo_root
    raise FileNotFoundError(
        f"Unable to locate canonical framework assets under '{bundled}' or '{repo_root}'."
    )
