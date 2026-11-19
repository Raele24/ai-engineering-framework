# Documentation Index (`docs/README.md`)

**Version:** `0.4.0`  

Clean index of active **user guides** and **canonical specifications** included with the framework repository.

---

## 1. Start Here (Adoption & Daily Usage)

| Document | Purpose | Audience |
| :--- | :--- | :--- |
| [`GETTING_STARTED.md`](./GETTING_STARTED.md) | Zero-flag bootstrap and first feature walkthrough from Phase 1 to Release | New adopters |
| [`CONSUMER_USAGE_GUIDE.md`](./CONSUMER_USAGE_GUIDE.md) | Practical day-to-day playbook for real brownfield repositories | Project developers |
| [`CUSTOMIZATION_GUIDE.md`](./CUSTOMIZATION_GUIDE.md) | Recipes for `.framework-custom/` rules, custom skills, custom/appended agents, `disabled.*` toggles, and `scripts/compose.py` | Project owners |
| [`INSTALLATION.md`](./INSTALLATION.md) | System prerequisites, `bootstrap.py` CLI flags/defaults, `.gitignore` rules, and `--update` guarantees | Maintainers & adopters |
| [`CONFIGURATION.md`](./CONFIGURATION.md) | Complete `project.framework.json` schema, lockfile `v2.0.0`, validation severities, and PowerShell conventions | Maintainers & adopters |

---

## 2. Canonical Specifications & Platform Compatibility

| Document | Purpose |
| :--- | :--- |
| [`WORKFLOW.md`](./WORKFLOW.md) | Canonical 15-phase SDLC specification, handoff state machine, and quality gates |
| [`ARCHITECTURE.md`](./ARCHITECTURE.md) | 4-tier architecture (Core, Adapters, Consumer Project, Runtime State) and Graphify integration |
| [`../adapters/compatibility-matrix.md`](../adapters/compatibility-matrix.md) | Platform mapping (`Antigravity`, `Claude Code`, `Copilot`, `Codex`, `Gemini CLI`) + adapter support vs host live-probe status |
| [`SKILL_COMPATIBILITY_MATRIX.md`](./SKILL_COMPATIBILITY_MATRIX.md) | Discovery paths, projection rules, and per-skill matrix for all `33` canonical skills |
| [`SKILL_INSTALLATION_GUIDE.md`](./SKILL_INSTALLATION_GUIDE.md) | Policy A/B/C rules and external dependency installation guidance |
| [`TOKEN_OPTIMIZATION.md`](./TOKEN_OPTIMIZATION.md) | Progressive disclosure principles and context-engineering safety floor |
| [`SECURITY.md`](./SECURITY.md) | Supported versions, secret guardrails, and Strix authorization policy |
| [`VERSIONING.md`](./VERSIONING.md) | SemVer `2.0.0` policy and release checklist |
| [`ROADMAP.md`](./ROADMAP.md) | Milestone history (`v0.1.0` through `v0.4.0`) and planned evolution |
| [`CONTRIBUTING.md`](./CONTRIBUTING.md) | Standards for modifying canonical sources and running `sync_adapters.py` / `run_tests.py` |
| [`adr/`](./adr/ADR-0001-open-source-license.md) | Architecture Decision Records (`ADR-0001`..`ADR-0003`) |

