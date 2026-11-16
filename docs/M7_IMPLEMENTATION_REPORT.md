# M7 Implementation Report: Framework Hardening & Consumer Bootstrap (`v0.3.0`)

- **Repository:** `D:\PROGETTI\ai-engineering-framework`
- **Target Version:** `v0.3.0` (hardened from `v0.2.0`)
- **Date:** `2026-11-16`
- **Scope:** Engineering remediation of `FL-01..FL-03` (`REC-01..REC-04`) discovered during `M6-Pilot`.

---

## 1. Before / After Summary (`REC-01` through `REC-04`)

| Recommendation | Pre-M7 (`v0.2.0`) Behavior | Post-M7 (`v0.3.0`) Behavior |
| :--- | :--- | :--- |
| **`REC-01` (`M7-01`): Consumer-Aware Validation (`scripts/validate.py`)** | `validate.py` assumed every target directory was the upstream framework repository, requiring `PROJECT_CHARTER.md`, `scripts/bootstrap.py`, `scripts/sync_adapters.py`, and 15+ upstream `docs/*.md` files. It also imported `sync_adapters` unconditionally at module load. | Supports `--mode {auto,framework,consumer}`. `auto` reliably detects `framework` vs `consumer` via repository markers. `consumer` mode is 100% self-contained (does not require `PROJECT_CHARTER.md`, `scripts/bootstrap.py`, or `scripts/sync_adapters.py`) and validates `project.framework.json`, `.framework-lock.json`, `.framework-state/manifest.json`, `.framework-state/handoffs/*.json`, filtered `skills/registry.json`, `agents/*.md` references, platform adapters, relative link containment, and secret hygiene. |
| **`REC-02` (`M7-02`): Optional Skill Pack Filtering (`scripts/bootstrap.py`)** | `bootstrap.py` copied only the selected `skills/optional/<pack>/` directories, but copied the full 30-skill `skills/registry.json`, full 30-skill `AGENTS.md` table, unfiltered `agents/*.md` `required_skills`, and static `.agents/skills.json`, causing missing-skill validation failures whenever any optional pack was omitted. | `bootstrap.py` generates a consumer-specific `skills/registry.json` (preserving 100% of upstream attribution, license, source URL, and SHA-256 metadata for installed skills), generates a matching `AGENTS.md` skill routing table, filters `agents/*.md` `required_skills` to installed skills only, and populates `.agents/skills.json` with only installed pack directories. Supports `--optional-packs none`, `all`, and `design-ui` / `frontend-design` aliases. |
| **`REC-03` (`M7-03`): Antigravity Adapter Relative Path Rewriting (`scripts/bootstrap.py`)** | Copying `adapters/antigravity/rules/framework-core.md` (depth 3) to `.agents/rules/framework-core.md` (depth 2) preserved `../../../AGENTS.md`, which escaped the consumer workspace root (`D:\PROGETTI\AGENTS.md`). Also, `workflows/01..06.md` linked to `../docs/WORKFLOW.md` (absent in consumer projects). | `bootstrap.rewrite_markdown_relative_links()` masks fenced code blocks and inline code spans, preserves external/anchor/URI links, and computes exact destination-relative paths (`../../../AGENTS.md` $\rightarrow$ `../../AGENTS.md`). `validate.py` verifies `resolved.is_relative_to(root.resolve())` so no link can escape the consumer root. Stage runbooks (`workflows/01..06.md`) link to `../AGENTS.md` and `../core/rules/engineering-principles.md`. |
| **`REC-04` (`M7-04`): Stack Templates & Windows SDK Preflight (`scripts/preflight.py`, `templates/stacks/`)** | No stack `.gitignore` templates or Windows user-space `.NET SDK` (`DOTNET_ROOT`) preflight guidance existed during consumer bootstrap. | Added `templates/stacks/{dotnet,node-angular,python}.gitignore` and `scripts/preflight.py`. `bootstrap.py --stacks dotnet,node/angular,python` creates `.gitignore` if missing, or writes `.gitignore.framework-recommended` if `.gitignore` already exists (never overwriting consumer `.gitignore`), and generates `docs/ENVIRONMENT_PREFLIGHT.md` with automatic Windows user-space `$HOME\.dotnet` (`DOTNET_ROOT`) detection. |

---

## 2. Modified & Created Files Inventory

| File Path | Action | Rationale |
| :--- | :---: | :--- |
| `scripts/validate.py` | Modified | Added `detect_validation_mode()`, `--mode {auto,framework,consumer}`, `check_consumer_state()`, self-contained `parse_simple_frontmatter()`, `required_skills` / `delegation_targets` cross-checks, and root-containment verification (`is_relative_to`) for Markdown links. |
| `scripts/bootstrap.py` | Modified | Added `normalize_optional_packs()`, `rewrite_markdown_relative_links()`, `build_filtered_registry()`, `filter_agent_required_skills()`, `build_consumer_agents_md()`, `build_consumer_antigravity_skills_json()`, `.framework-state/manifest.json` initialization, and `--stacks` support. |
| `scripts/preflight.py` | Created | Standalone stack SDK preflight utility supporting `dotnet` (including Windows user-space `DOTNET_ROOT` detection), `node-angular` (`node/angular`), and `python`. |
| `scripts/sync_adapters.py` | Modified | Updated `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`, and `adapters/antigravity/rules/framework-core.md` links to reference installed `core/rules/engineering-principles.md`. |
| `workflows/01..06-*.md` | Modified | Updated canonical header links from `../docs/WORKFLOW.md` to `../AGENTS.md` and `../core/rules/engineering-principles.md` so all links resolve in both framework and consumer workspaces. |
| `templates/stacks/dotnet.gitignore` | Created | Minimal `.NET / C#` `.gitignore` template. |
| `templates/stacks/node-angular.gitignore` | Created | Minimal `Node.js / Angular` `.gitignore` template. |
| `templates/stacks/python.gitignore` | Created | Minimal `Python` `.gitignore` template. |
| `templates/project.framework.json` | Modified | Updated `frameworkVersion` to `"0.3.0"` and added `"stacks": []`. |
| `skills/registry.json` | Modified | Updated `framework_version` to `"0.3.0"`. |
| `tests/test_m7_hardening.py` | Created | Automated TDD regression test suite (`7` test methods / `10` subtest executions) covering `M7-01`..`M7-06`. |
| `README.md`, `docs/INSTALLATION.md`, `docs/CONFIGURATION.md`, `docs/VERSIONING.md`, `docs/ROADMAP.md` | Modified | Documented `--mode consumer|framework|auto`, optional pack filtering, adapter path rewriting, `--stacks`, and `v0.3.0` release preparation. |
