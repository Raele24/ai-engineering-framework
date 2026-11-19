from __future__ import annotations

from pathlib import Path
import shutil
from setuptools import setup
from setuptools.command.build_py import build_py as _build_py

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


class BuildPyWithBundle(_build_py):
    """Copy canonical framework directories into aief_cli/_bundle during wheel builds."""

    def run(self) -> None:
        super().run()
        if getattr(self, "editable_mode", False):
            return
        src_root = Path(__file__).resolve().parent
        dst_bundle = Path(self.build_lib) / "aief_cli" / "_bundle"
        if dst_bundle.exists():
            shutil.rmtree(dst_bundle)
        dst_bundle.mkdir(parents=True, exist_ok=True)
        ignore = shutil.ignore_patterns("__pycache__", "*.py[cod]", ".DS_Store")
        for rel_dir in BUNDLE_DIRS:
            src_dir = src_root / rel_dir
            if src_dir.is_dir():
                shutil.copytree(src_dir, dst_bundle / rel_dir, ignore=ignore, dirs_exist_ok=True)
        for fname in ("LICENSE", "README.md"):
            fpath = src_root / fname
            if fpath.is_file():
                shutil.copy2(fpath, dst_bundle / fname)


setup(cmdclass={"build_py": BuildPyWithBundle})
