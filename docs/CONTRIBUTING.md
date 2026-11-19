# Contributing Guide (`CONTRIBUTING.md`)

**Version:** `0.4.0`  

---

## 1. Welcome & Engineering Standards

Contributions to the **AI Engineering Framework** must uphold the exact engineering discipline the framework teaches:
1. **Single Source of Truth:** Never edit generated platform adapter files directly without updating the canonical source in `core/`, `agents/`, `skills/`, or `workflows/` and running `python scripts/sync_adapters.py`.
2. **Platform Capability Model:** Any platform capability or adapter schema change must stay aligned with [`core/platform-capabilities.json`](../core/platform-capabilities.json), [`scripts/platform_capabilities.py`](../scripts/platform_capabilities.py), and evidence rules in [`adapters/compatibility-matrix.md`](../adapters/compatibility-matrix.md) (never promote static parity to `RUNTIME_VERIFIED` without live evidence).
3. **Zero AI Slop:** All documentation and skill instructions must follow [`skills/core/anti-slop/SKILL.md`](../skills/core/anti-slop/SKILL.md) — concrete, direct, verifiable instructions with zero promotional filler.

---

## 2. Contribution Workflow

1. **Open or Reference an Issue:** Use the [Bug Report](../.github/ISSUE_TEMPLATE/bug_report.yml) or [Feature Request](../.github/ISSUE_TEMPLATE/feature_request.yml) template.
2. **Create a Specification or ADR (for Major Changes):**
   - New workflow changes or architectural modifications require an ADR in `docs/adr/ADR-xxxx-<slug>.md` using [`templates/ADR.template.md`](../templates/ADR.template.md).
3. **Author Canonical Changes:**
   - **Adding a Skill:** Create `skills/<tier>/<skill-name>/SKILL.md` with valid YAML frontmatter matching [`core/schemas/skill-frontmatter.schema.json`](../core/schemas/skill-frontmatter.schema.json) and register it in [`skills/registry.json`](../skills/registry.json).
   - **Updating Rules or Agents:** Edit `core/rules/*.md` or `agents/*.md`, then run `python scripts/sync_adapters.py`.
4. **Write & Run Automated Tests:**
   ```bash
   python scripts/sync_adapters.py --check
   python scripts/validate.py --mode framework
   python scripts/run_tests.py --fail-on-skip
   python -m unittest discover -s tests -v
   ```
5. **Update the Knowledge Graph (if `graphify` is installed):**
   ```bash
   graphify update .
   ```
6. **Submit a Pull Request:** Complete the checklist in [`.github/PULL_REQUEST_TEMPLATE.md`](../.github/PULL_REQUEST_TEMPLATE.md).

---

## 3. Commit Message Convention

Follow **Conventional Commits**:
- `feat(skills): add <skill-name> skill to <tier>`
- `fix(scripts): handle Windows path separators in bootstrap.py`
- `docs(workflow): clarify Phase 12 Strix authorization gate`
- `chore(adapters): sync platform adapters with core rules`

---

## 4. License Agreement

By submitting a contribution to this repository, you agree that your contribution is licensed under the **[Apache License, Version 2.0](../LICENSE)** (Section 5: Submission of Contributions).
