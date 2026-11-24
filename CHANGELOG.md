# Changelog

All notable changes to the **AI Engineering Framework** are documented in this file.
The format follows [Semantic Versioning 2.0.0](https://semver.org/) ([`docs/CONTRIBUTING.md`](./docs/CONTRIBUTING.md#3-semantic-versioning-semver-200--stability)).

---

## [0.6.0] - 2026-11-22

### Added
- **Interactive Arrow-Key TUI Discovery & Migration Wizard (`scripts/bootstrap.py`, `aief_cli/cli.py`):** On interactive TTY fresh installs (`aief init`), performs read-only discovery before writing files, detects identical/duplicate legacy entry files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`), provides a `↑`/`↓`/`Space`/`a`/`Enter`/`Esc` multi-select/select TUI (with clean `Ctrl+C`/`Esc` abort and ASCII fallback on non-TTY pipes) for target platforms, optional skill packs, per-file legacy migration actions (`copy`, `move` to `.aief/custom/rules/` with optional custom rule filename & old-file cleanup, `skip`, or `delete`), and external skill/rule unification, then outputs an explicit action receipt. Added `--yes` (`-y`), `--interactive` (`-i`), and `--no-import` CLI flags (`test_18_interactive_wizard_discovery_duplicates_and_actions`, bringing suite coverage to `87/87` automated checks).

### Fixed
- **Sub-Second Monorepo `pnpm` Validation (`scripts/validate.py`):** Replaced full-tree `Path.rglob()` scans in `check_json_files` and `check_secrets` with `_iter_workspace_files()` using `os.walk` directory pruning (`node_modules/`, `.git/`, `.angular/`, `dist/`, `.venv/`), cutting validation on large `pnpm` / Angular workspaces from minutes to `<1s`.
- **`.aief/.gitignore` Python Bytecode Hygiene & Nested Monorepo JSONC:** Added `__pycache__/` and `*.py[cod]` to `.aief/.gitignore` (auto-upgrading unmodified defaults on `aief update`) and enabled nested `.vscode/*.json` / `.devcontainer/*.json` JSONC support (`apps/web/.vscode/*.json`).
- **Sandbox-Safe Consumer Validation & Mandatory Subagent Gate:** Handled host-sandbox `PermissionError` (`[WinError 5]`) cleanly in `inspect_host_global_skill_visibility()`, added Windows sandbox fallback to `graphify`, and enforced a non-skippable `HARD GATE` on `>=3` modified/created files or `>=2` layers across `AGENTS.md`, `CLAUDE.md`, `.agents/rules/framework-core.md`, `adapters/antigravity/rules/framework-core.md`, `docs/WORKFLOW.md`, `workflows/04-tdd-and-implementation.md`, and `workflows/05-review-qa-and-security.md` (requiring layer delegation via `invoke_subagent`/`define_subagent` and independent `code-reviewer` execution reporting each `conversationId` + verdict when review is enabled).

---

## [0.5.0] - 2026-11-20

### Added
- **Isolated Consumer Layout (`.aief/`):** New consumer installations isolate all framework-managed runtime assets inside `.aief/` (`config.json`, `lock.json`, `state/`, `custom/`, `core/`, `agents/`, `skills/registry.json`, `workflows/`, `templates/`, `quality/`, `security/`, `scripts/`, `adapters/antigravity/`, `.aief/.gitignore`, `.aief/ENVIRONMENT_PREFLIGHT.md`, `.aief/gitignore.recommended`). Skill directories live solely in native platform paths (`.agents/skills/` and `.claude/skills/`) without duplicating skill files under `.aief/skills/`.
- **Single-Copy Rule & Overlay Injection (Zero `3x` Duplication):** Full inline rules, active gates, and `.aief/custom/` overlays live once in `AGENTS.md` (plus `CLAUDE.md` for Claude Code), while `GEMINI.md`, `.agents/rules/framework-core.md`, `.github/copilot-instructions.md`, and `.github/instructions/framework.instructions.md` emit slim platform-specific pointers to `AGENTS.md`.
- **Zero-Collision Brownfield Discovery (`scripts/validate.py` & `scripts/bootstrap.py`):** Consumer validation scans strictly `<skills_root>/core/` and `<skills_root>/optional/`, ensuring pre-existing host-app skills (`skills/<project>/SKILL.md`), custom rules (`.agents/rules/*.md`), and project `docs/` remain untouched and never trigger registry errors. Added brownfield regression test `test_17_vintgen_brownfield_isolation_no_skills_collision` (`86/86` automated checks green).
- **Short-Path Bundle Extraction (`aief_cli`, `setup.py`):** Packages framework assets into `aief_cli/bundle.zip` extracted to `~/.cache/aief/<version>-<hash>/` with zip-slip protection, eliminating Windows `WinError 206` (`MAX_PATH`) failures during `pipx`/`uvx` installation.
- **13 Canonical Specialist Roles & Subagent-First Orchestration (`agents/`, `compose.py`, `sync_adapters.py`):** Added `ui-ux-designer`, `data-engineer` (DB & Big Data), `backend-engineer`, `frontend-engineer`, and `ai-engineer`, expanded `devops-release-engineer` to `[9, 13]` (CI/CD pipelines, containers, deploy & rollback), added `Subagent-First Delegation` rules across `AGENTS.md` and stage runbooks (`workflows/02..06`), and expanded native `.claude/agents/*.md` and `.github/agents/*.agent.md` projection to cover every active role (preserving read-only reviewer guards and selective `disabled.agents` pruning).

### Changed
- Preserved full automatic **legacy layout detection (`"legacy"`)** in `compose.py`, `bootstrap.py`, `validate.py`, `preflight.py`, `aief_cli`, and `session-handoff` scripts for existing `v0.3.x` / `v0.4.x` consumer workspaces using root `project.framework.json` / `.framework-lock.json` / `.framework-state/`.

---

## [0.4.0] - 2026-11-19

### Added
- **Standalone Consumer Composition Engine (`scripts/compose.py`):** Shipped into every bootstrapped consumer repository so teams can edit `.framework-custom/` or `project.framework.json` and run `python scripts/compose.py` locally without upstream dependencies or custom changes being clobbered on framework updates.
- **Inline Auto-Loading Across All 5 Platforms:** Generated consumer entry points (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.agents/rules/framework-core.md`, `.github/copilot-instructions.md`, `.github/instructions/framework.instructions.md`) now embed active framework rules, active gates, and `.framework-custom/` instructions/rules directly inline (configurable via `customizations.promptInjectionMode` and `inlineMaxBytes`).
- **Consumer Custom Overlay Architecture (`.framework-custom/`):** Consumer-owned Tier 3 workspace overlay supporting custom project instructions (`instructions.md`, `rules/*.md`), custom native-projected skills (`skills/<name>/SKILL.md`, tracked as `consumer_custom_skill`), agent rule appends (`agents/<role>.append.md`), agent overrides or custom agents (`agents/<name>.md`, tracked as `consumer_custom_agent` with read-only reviewer enforcement), custom reusable slash prompts (`prompts/*.md`, tracked as `consumer_custom_prompt` across Copilot/Claude/Gemini CLI), custom MCP servers (`mcp.json`, tracked as `consumer_custom_mcp` with secret rejection across Claude/Copilot/Codex/Gemini CLI/Antigravity), and first-run brownfield auto-import (`imported/`).
- **Curated Skill Additions (`30 -> 33` Skills):** Added MIT-licensed `session-handoff` (`softaworks/agent-toolkit`, harmonized to `.framework-state/session-handoffs/`) under `skills/optional/context-engineering/`, plus `i-have-adhd` (`ayghri/i-have-adhd`) and `humanizer` (`blader/humanizer`, complementing core `anti-slop`) under `skills/optional/communication/`.
- **Granular Feature Toggles (`disabled.*`):** Backward-compatible `project.framework.json` schema (`core/schemas/framework-config.schema.json`) supporting `disabled.skills`, `disabled.agents`, `disabled.phases`, `disabled.gates`, and `disabled.mechanisms` (`tdd`, `handoffs`, `graphify`, `code-review`). Disabled skills/agents remain intact on disk under `skills/` and `agents/` for offline re-enabling while being pruned from native projections/subagents.
- **Standard PEP 517 Packaging (`pyproject.toml`, `aief` CLI) & Auto-Deploy Workflow ([`.github/workflows/release-on-version-bump.yml`](./.github/workflows/release-on-version-bump.yml)):** Installs directly via `uvx` / `pipx` / `pip` exposing `aief` (`init`, `update`, `compose`, `validate`, `preflight`, `check-sync`). On every push to `main` where `pyproject.toml` introduces a new version, CI verifies version parity + full suite, builds & smoke-tests the wheel, creates the GitHub tag + Release + SHA-256 checksums, and optionally publishes to PyPI via OIDC (`PYPI_PUBLISH_ENABLED=true`).
- **Tier E Automated Test Suite (`tests/test_m10_custom_composition.py`):** Added `16` deterministic tests covering inline composition, custom skills/agents/prompts/MCP, secret rejection, feature toggles, zero-flag CLI bootstrap, brownfield auto-import, JSONC validation, `pnpm` preflight detection, `session-handoff`/`i-have-adhd`/`humanizer`, packaging version parity + `aief` CLI, Graphify CLI detection/reporting, and safety guards (raising total suite coverage to `84/84` across Baseline + Tiers A–E).
- **Documentation Consolidation (`docs/README.md`, `docs/GETTING_STARTED.md`, `docs/CUSTOMIZATION_GUIDE.md`, `docs/CONFIGURATION.md`, `docs/INSTALLATION.md`, `docs/CONTRIBUTING.md`, `docs/SKILL_COMPATIBILITY_MATRIX.md`, `adapters/compatibility-matrix.md`):** Consolidated overlapping guides cleanly to `12` active docs for `v0.4.0`.

### Changed
- Integrated `scripts/compose.py` into `scripts/bootstrap.py`, preserving backward compatibility with Lockfile `v2.0.0`, legacy `v0.3.0` lockfiles, and `v0.3.x` `project.framework.json` configs lacking `disabled`/`customizations` keys.
- Updated `scripts/validate.py` in consumer mode to verify `.framework-custom/` safety, `consumer_custom_skill` / `consumer_custom_agent` ownership classes, disabled skill/agent pruning parity, and read-only reviewer constraints.

---

## [0.3.1] - 2026-11-19 (Release Candidate — Pending `Gate-04`)

### Added
- Canonical declarative capability model (`core/platform-capabilities.json` + stdlib `scripts/platform_capabilities.py`) tracking evidence states across Antigravity, GitHub Copilot, Claude Code, OpenAI Codex CLI, and Gemini CLI without over-claiming runtime verification.
- Native skill directory projection during consumer bootstrap (`.agents/skills/<name>/` and `.claude/skills/<name>/`) backed by Lockfile `v2.0.0` (`schema_version: "2.0.0"`) with ownership classes, two-phase atomic writes, safe pruning, relative Markdown link rewriting, and case-insensitive / traversal / NTFS reparse-point safety guards.
- Bounded stdlib HTTP/dev-server startup readiness helper (`scripts/readiness.py`) with angular/package endpoint derivation, fast build/`EADDRINUSE` failure detection, and strict child-PID-only cleanup.
- Deterministic 4-tier offline test runner (`scripts/run_tests.py`) consolidating `68` stdlib tests across Baseline (`13`), Tier A (`18`), Tier B (`18`), Tier C (`10`), and Tier D (`9`).
- Read-only host-global skill directory visibility (`INFO`) alongside three-tier validation severity reporting (`ERROR` / `WARNING` / `INFO`) in `scripts/validate.py`.

### Changed
- Parameterized `scripts/sync_adapters.py` and `scripts/bootstrap.py` to generate consumer-safe adapter references (`python scripts/validate.py --mode consumer`, `workflows/`, `core/rules/`) without upstream-only paths while keeping upstream framework CI intact.
- Dynamically derived upstream `.agents/skills.json` and `adapters/antigravity/skills.json` from `skills/registry.json` (`30/30` skills across `6` directories incl. `skills/optional/growth-media`).
- Aligned `adapters/claude-code/agents/code-reviewer.md` and `adapters/copilot/code-reviewer.agent.md` with platform-native read-only tool IDs, removed unsupported `subagent`/`mainAgent` frontmatter keys and top-level settings `"description"` keys, and refactored `adapters/antigravity/hooks.json` to schema-valid `"enabled": false` opt-in format.
- Updated `workflows/05-review-qa-and-security.md`, `docs/CONFIGURATION.md`, `docs/INSTALLATION.md`, and `adapters/compatibility-matrix.md` with Windows PowerShell `5.1` conventions and platform contract schemas.
- Preserved full backward compatibility and safe backup migration (`.framework-state/lock-backups/framework-lock-v0.3.0.json`) for legacy `v0.3.0` consumers.

---

## [0.3.0] - 2026-11-16

### Added
- Consumer vs. framework validation modes (`--mode auto|framework|consumer`) in `scripts/validate.py`.
- Optional skill pack filtering (`--optional-packs`) in `scripts/bootstrap.py`.
- Stack `.gitignore` templates (`--stacks dotnet,node/angular,python`) and Windows SDK preflight (`scripts/preflight.py`).

---

## [0.1.0] - 2026-11-16

### Added
- Canonical 15-phase SDLC specification (`docs/WORKFLOW.md`), 4 core rules (`core/rules/`), 4 JSON schemas (`core/schemas/`), 8 canonical agent roles (`agents/`), modular skills (`skills/`), 6 stage runbooks (`workflows/`), 5 platform adapter packages (`adapters/`), quality/security rubrics, and core CLI scripts.
