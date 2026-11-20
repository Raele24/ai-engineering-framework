from __future__ import annotations

from pathlib import Path
import shutil
from setuptools import setup
from setuptools.command.build_py import build_py as _build_py
import zipfile

BUNDLE_DIRS = (
    "core",
    "agents",
    "skills",
    "workflows",
    "templates",
    "adapters",
    "quality",
    "security",
    "integrations",
    "scripts",
)
IGNORE_NAMES = {"__pycache__", ".DS_Store"}


def _should_skip(rel_parts: tuple[str, ...], name: str) -> bool:
    if name in IGNORE_NAMES or any(part in IGNORE_NAMES for part in rel_parts):
        return True
    return name.endswith((".pyc", ".pyo", ".pyd"))


def build_bundle_zip(src_root: Path, dst_zip: Path) -> None:
    """Package canonical framework directories into one compact zip to avoid Windows MAX_PATH limits."""
    dst_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dst_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel_dir in BUNDLE_DIRS:
            src_dir = src_root / rel_dir
            if not src_dir.is_dir():
                continue
            for item in sorted(src_dir.rglob("*")):
                if not item.is_file():
                    continue
                rel = item.relative_to(src_root)
                if _should_skip(rel.parts, item.name):
                    continue
                zf.write(item, arcname=rel.as_posix())
        for fname in ("LICENSE", "README.md"):
            fpath = src_root / fname
            if fpath.is_file():
                zf.write(fpath, arcname=fname)


class BuildPyWithBundle(_build_py):
    """Embed canonical framework assets as a single bundle.zip inside built wheels."""

    def run(self) -> None:
        super().run()
        if getattr(self, "editable_mode", False):
            return
        src_root = Path(__file__).resolve().parent
        old_dir = Path(self.build_lib) / "aief_cli" / "_bundle"
        if old_dir.exists():
            shutil.rmtree(old_dir)
        build_bundle_zip(src_root, Path(self.build_lib) / "aief_cli" / "bundle.zip")


setup(cmdclass={"build_py": BuildPyWithBundle})
