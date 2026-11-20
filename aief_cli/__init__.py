"""Packaged CLI wrapper for AI Engineering Framework."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import tempfile
import zipfile

__version__ = "0.5.0"


def _default_cache_root() -> Path:
    try:
        home_cache = Path.home() / ".cache" / "aief"
        home_cache.mkdir(parents=True, exist_ok=True)
        return home_cache
    except OSError:
        tmp_cache = Path(tempfile.gettempdir()) / "aief-cache"
        tmp_cache.mkdir(parents=True, exist_ok=True)
        return tmp_cache


def _extract_bundle_zip(bundle_zip: Path, cache_base: Path | None = None) -> Path:
    """Safely extract bundle.zip into a short cache path once per content hash."""
    digest = hashlib.sha256(bundle_zip.read_bytes()).hexdigest()[:12]
    root_cache = cache_base if cache_base is not None else _default_cache_root()
    target_dir = root_cache / f"{__version__}-{digest}"
    ready_marker = target_dir / ".bundle_ready"
    if ready_marker.is_file() and (target_dir / "core" / "rules" / "engineering-principles.md").is_file():
        return target_dir

    root_cache.mkdir(parents=True, exist_ok=True)
    tmp_dir = root_cache / f".tmp-{__version__}-{digest}-{os.getpid()}"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir, ignore_errors=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        tmp_resolved = tmp_dir.resolve()
        with zipfile.ZipFile(bundle_zip, "r") as zf:
            for member in zf.infolist():
                if member.is_dir():
                    continue
                member_path = Path(member.filename)
                if member_path.is_absolute() or ".." in member_path.parts:
                    raise ValueError(f"Unsafe zip entry rejected: {member.filename}")
                out_path = (tmp_dir / member_path).resolve()
                if not out_path.is_relative_to(tmp_resolved):
                    raise ValueError(f"Zip slip entry rejected: {member.filename}")
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member, "r") as src, out_path.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
        (tmp_dir / ".bundle_ready").write_text(digest + "\n", encoding="utf-8")
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        os.replace(tmp_dir, target_dir)
        return target_dir
    except Exception:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise


def resolve_framework_root() -> Path:
    """Resolve canonical framework asset root from repo checkout, _bundle dir, or bundle.zip."""
    pkg_dir = Path(__file__).resolve().parent
    bundled_zip = pkg_dir / "bundle.zip"
    if bundled_zip.is_file():
        return _extract_bundle_zip(bundled_zip)
    bundled = pkg_dir / "_bundle"
    if (bundled / "core" / "rules" / "engineering-principles.md").is_file():
        return bundled
    repo_root = pkg_dir.parent
    if (repo_root / "core" / "rules" / "engineering-principles.md").is_file():
        return repo_root
    raise FileNotFoundError(
        f"Unable to locate canonical framework assets under '{bundled_zip}', '{bundled}', or '{repo_root}'."
    )
