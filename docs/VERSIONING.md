# Versioning & Release Policy (`VERSIONING.md`)

**Version:** `0.4.0`  

---

## 1. Semantic Versioning (`SemVer 2.0.0`)

The **AI Engineering Framework** strictly follows **[Semantic Versioning 2.0.0](https://semver.org/) (`MAJOR.MINOR.PATCH`)**:

- **`MAJOR` (`X.0.0`):** Incompatible changes to canonical JSON schemas (`core/schemas/*.json`), removal/renaming of canonical workflow phases in `docs/WORKFLOW.md`, or breaking CLI flag changes in `scripts/bootstrap.py` / `scripts/validate.py`.
- **`MINOR` (`0.Y.0`):** Backward-compatible additions such as new optional skill packs (`skills/optional/`), new platform adapters (`adapters/`), additional fields with sensible defaults in schemas, or new templates (`templates/`).
- **`PATCH` (`0.0.Z`):** Backward-compatible bug fixes in scripts, documentation clarifications, typo fixes, or adapter template adjustments that require no consumer config migration.

---

## 2. Pre-1.0 (`0.x.y`) Stability Guarantees

While in the `0.x.y` series (`0.1.0` through `0.9.x`):
1. **Non-Destructive Updates Guaranteed:** `python scripts/bootstrap.py --update` will never overwrite consumer-modified files (`project.framework.json`, `docs/specs/`, `docs/adr/`, or locally customized rules).
2. **Schema Versioning:** Every JSON schema in `core/schemas/` carries a `$id` and version metadata. Any breaking schema change in `0.x` increments the minor version (`0.1.0` $\rightarrow$ `0.2.0`) and includes migration instructions in `CHANGELOG.md` and `docs/ROADMAP.md`.

---

## 3. Independent Skill Versioning

Individual skills in `skills/registry.json` maintain their own semantic `version` field in both `SKILL.md` YAML frontmatter and `skills/registry.json`, allowing individual domain skills to evolve and record SHA-256 integrity hashes independently between major framework releases.

---

## 4. Release Checklist (Phase 13)

Before tagging any release (`vX.Y.Z`):
1. Update `frameworkVersion` / `framework_version` in `templates/project.framework.json`, `scripts/bootstrap.py`, `scripts/compose.py` fallback, `skills/registry.json`, `core/platform-capabilities.json`, and active documentation headers.
2. Run `python scripts/sync_adapters.py` and verify `python scripts/sync_adapters.py --check`.
3. Run `python scripts/validate.py --mode framework` (must exit `0`).
4. Run `python scripts/run_tests.py --fail-on-skip` and `python -m unittest discover -s tests -v` (must pass 100%).
5. Obtain explicit human approval (**`Gate-04: Release Approval`**) before committing, pushing tags, or publishing a GitHub Release.
