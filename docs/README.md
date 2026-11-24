# Documentation Index (`docs/README.md`)

**Version:** `0.7.1`

Active user guides and canonical specifications included in this repository.

---

## 1. Adoption & Daily Usage

| Document | Purpose | Audience |
| :--- | :--- | :--- |
| [`GETTING_STARTED.md`](./GETTING_STARTED.md) | Quickstart, first feature walkthrough, session handoffs, and bounded readiness | Adopters & devs |
| [`CUSTOMIZATION_GUIDE.md`](./CUSTOMIZATION_GUIDE.md) | `.aief/custom/` recipes (rules, skills, agents, prompts, MCP), `disabled.*` toggles, and `compose.py` | Project owners |
| [`INSTALLATION.md`](./INSTALLATION.md) | System prerequisites, `aief` CLI / `bootstrap.py` flags, `.aief/` isolation, and `--update` | Maintainers & adopters |
| [`CONFIGURATION.md`](./CONFIGURATION.md) | `.aief/config.json` schema, lockfile `v2.0.0`, ownership classes, and validation severities | Maintainers & adopters |

---

## 2. Canonical Specifications & Reference

| Document | Purpose |
| :--- | :--- |
| [`WORKFLOW.md`](./WORKFLOW.md) | Canonical 15-phase SDLC specification, handoff state machine, and quality gates |
| [`ARCHITECTURE.md`](./ARCHITECTURE.md) | 4-tier architecture and Graphify integration |
| [`../adapters/compatibility-matrix.md`](../adapters/compatibility-matrix.md) | Platform mapping across Antigravity, Claude Code, Copilot, Codex, Gemini CLI |
| [`SKILL_COMPATIBILITY_MATRIX.md`](./SKILL_COMPATIBILITY_MATRIX.md) | Packs, Policy A/B/C, external CLIs (`rtk`, `graphify`), and compatibility matrix for all `37` skills |
| [`TOKEN_OPTIMIZATION.md`](./TOKEN_OPTIMIZATION.md) | Progressive disclosure principles and token optimization benchmarks |
| [`SECURITY.md`](./SECURITY.md) | Supported versions, secret guardrails, and Strix authorization policy |
| [`CONTRIBUTING.md`](./CONTRIBUTING.md) | Authoring rules, SemVer `2.0.0`, release checklist, and commit conventions |
| [`ROADMAP.md`](./ROADMAP.md) | Release progression (`v0.1.0` through `v0.7.1+`) |
| [`adr/`](./adr/ADR-0001-open-source-license.md) | Architecture Decision Records (`ADR-0001`..`ADR-0003`) |
