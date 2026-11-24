# Contributing, Versioning & Release Guide (`CONTRIBUTING.md`)

**Version:** `0.7.1`

---

## 1. Engineering Standards

Contributions to **AI Engineering Framework** follow the same rules enforced by the framework itself:
1. **Single Source of Truth:** Edit canonical files in `core/`, `agents/`, `skills/`, or `workflows/`, then run `python scripts/sync_adapters.py` instead of editing generated adapters by hand.
2. **Platform Capability Model:** Keep platform schema updates aligned with [`core/platform-capabilities.json`](../core/platform-capabilities.json), [`scripts/platform_capabilities.py`](../scripts/platform_capabilities.py), and [`adapters/compatibility-matrix.md`](../adapters/compatibility-matrix.md).
3. **Zero AI Slop:** Follow [`skills/core/anti-slop/SKILL.md`](../skills/core/anti-slop/SKILL.md) — concrete, direct instructions with no promotional filler.

---

## 2. Contribution Workflow

1. **Open an Issue:** Use the [Bug Report](../.github/ISSUE_TEMPLATE/bug_report.yml) or [Feature Request](../.github/ISSUE_TEMPLATE/feature_request.yml) template.
2. **ADR (for Major Changes):** Document workflow or architectural changes in `docs/adr/ADR-xxxx-<slug>.md` using [`templates/ADR.template.md`](../templates/ADR.template.md).
3. **Author Canonical Changes:**
   - **Add a Skill:** Create `skills/<tier>/<skill-name>/SKILL.md` matching [`core/schemas/skill-frontmatter.schema.json`](../core/schemas/skill-frontmatter.schema.json) with LF (`\n`) line endings and register its SHA-256 hash in [`skills/registry.json`](../skills/registry.json).
   - **Update Rules or Agents:** Edit `core/rules/*.md` or `agents/*.md`, then run `python scripts/sync_adapters.py`.
4. **Validate & Test:**
   ```bash
   python scripts/sync_adapters.py --check
   python scripts/validate.py --mode framework
   python scripts/run_tests.py --fail-on-skip
   ```
5. **Refresh Graphify (if installed):** `graphify update .`
6. **Open a Pull Request:** Complete [`.github/PULL_REQUEST_TEMPLATE.md`](../.github/PULL_REQUEST_TEMPLATE.md).

---

## 3. Semantic Versioning (`SemVer 2.0.0`) & Stability

- **`MAJOR` (`X.0.0`):** Breaking schema changes (`core/schemas/*.json`), removed/renamed workflow phases, or breaking CLI flag changes.
- **`MINOR` (`0.Y.0`):** Backward-compatible new optional packs, adapters, templates, or optional schema fields.
- **`PATCH` (`0.0.Z`):** Bug fixes, doc cleanups, or non-breaking adapter adjustments.
- **Pre-1.0 (`0.x.y`) Guarantee:** `aief update` / `bootstrap.py --update` preserves consumer-owned files (`.aief/config.json`, `.aief/custom/`, `docs/specs/`, `docs/adr/`) and legacy `0.3.x`/`0.4.x` consumer layouts.
- **Per-Skill Versions:** Each skill tracks its own `version` in `SKILL.md` frontmatter and `skills/registry.json`.

---

## 4. Release Checklist (Phase 13 — `Gate-04`)

Before pushing a new version bump to `main` (handled automatically by [`.github/workflows/release-on-version-bump.yml`](../.github/workflows/release-on-version-bump.yml)):
1. Update the version across all 5 files checked by CI: `pyproject.toml`, `aief_cli/__init__.py`, `scripts/bootstrap.py`, `templates/project.framework.json`, and `skills/registry.json` (plus `CHANGELOG.md`).
2. Run `python scripts/sync_adapters.py` and confirm `python scripts/sync_adapters.py --check` passes.
3. Run `python scripts/validate.py --mode framework` and `python scripts/run_tests.py --fail-on-skip` (`90/90` tests passing, 0 errors, 0 skipped).
4. Obtain explicit human approval (**`Gate-04`**) before committing or pushing to `main`.

---

## 5. Commit Messages & License

Use **Conventional Commits** (`feat(skills): ...`, `fix(scripts): ...`, `docs(...): ...`, `chore(adapters): ...`).

Contributions are licensed under the **[Apache License, Version 2.0](../LICENSE)** (Section 5: Submission of Contributions).
