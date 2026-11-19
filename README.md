# AI Engineering Framework

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)
[![Version](https://img.shields.io/badge/version-0.4.0-success.svg)](./docs/VERSIONING.md)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](./docs/CONTRIBUTING.md)

**A modular, open-source, platform-independent engineering framework that standardizes the complete Software Development Lifecycle (SDLC) for AI coding agents.**

The **AI Engineering Framework** provides a single canonical source of truth for requirements discovery, specification-driven development, architectural decision records (ADRs), test-driven development (TDD), code review, security validation, and release automation across **GitHub Copilot**, **Google Antigravity**, **Claude Code**, **OpenAI Codex**, and **Gemini CLI**.

---

## Why This Framework Exists

Most AI-assisted development setups suffer from three structural failure modes:
1. **Prompt Sprawl & Vendor Lock-In:** Teams maintain conflicting instructions in `.github/copilot-instructions.md`, `CLAUDE.md`, `AGENTS.md`, and `GEMINI.md`.
2. **Vibe-Coding Drift:** Agents jump straight from a vague user prompt to writing implementation code without clarifying edge cases, documenting architecture, or writing failing tests first.
3. **Multi-Agent "Telephone Game" Degradation:** Passing project context purely through chat summaries causes ~50% information loss across agent handoffs.

**AI Engineering Framework solves this with three core primitives:**
- **Canonical 15-Phase Workflow ([docs/WORKFLOW.md](./docs/WORKFLOW.md)):** Every phase defines explicit inputs, outputs, responsible roles, entry/exit criteria, quality gates, and mandatory human approval checkpoints.
- **Filesystem Handoff Protocol ([core/rules/context-handoff-protocol.md](./core/rules/context-handoff-protocol.md)):** Agents exchange validated artifacts (`docs/specs/`, `docs/adr/`, `.framework-state/handoffs/`) on disk so every specialist agent starts with a clean, unpolluted context window.
- **Thin Platform Adapters ([adapters/](./adapters/)):** Maintain rules, roles, and skills (`SKILL.md`) once; synchronize native configurations for all 5 platforms with `python scripts/sync_adapters.py`.

---

## Architecture Overview

```mermaid
flowchart TB
    subgraph Tier1["Tier 1: Canonical Framework Core (Single Source of Truth)"]
        Rules["core/rules/ & core/schemas/"]
        Workflow["docs/WORKFLOW.md & workflows/"]
        Roles["agents/ (8 Canonical Roles)"]
        Skills["skills/core/ & skills/optional/ (SKILL.md)"]
    end

    subgraph Tier2["Tier 2: Thin Platform Adapters (scripts/sync_adapters.py)"]
        Copilot[".github/copilot-instructions.md & .github/agents/"]
        Antigravity["GEMINI.md & .agents/rules/ & hooks.json"]
        Claude["CLAUDE.md & .claude/agents/ & .claude/commands/"]
        Codex["AGENTS.md & .codex/config.toml"]
        GeminiCLI["GEMINI.md & .gemini/commands/"]
    end

    subgraph Tier3["Tier 3: Consumer Project Artifacts (Never Overwritten on Update)"]
        ProjectCfg["project.framework.json"]
        Specs["docs/specs/ & docs/adr/ & docs/plans/"]
    end

    subgraph Tier4["Tier 4: Runtime State (.framework-state/)"]
        Manifest[".framework-state/manifest.json"]
        Handoffs[".framework-state/handoffs/"]
        Graph["graphify-out/ (Knowledge Graph)"]
    end

    Tier1 --> Tier2
    Tier2 --> Tier3
    Tier3 --> Tier4
```

---

## Supported Platforms

All **5 platforms** ship complete inline entry files, adapters, native skill projections, custom prompts/MCP support, and schema contracts (`84/84` automated checks green):

| Platform | Entry Point | Adapter & Projection Layout | Status |
| :--- | :--- | :--- | :---: |
| **Google Antigravity** | [`GEMINI.md`](./GEMINI.md), [`AGENTS.md`](./AGENTS.md) | `.agents/rules/`, `.agents/skills/`, `hooks.json` | **`SUPPORTED`** |
| **Claude Code** | [`CLAUDE.md`](./CLAUDE.md), [`AGENTS.md`](./AGENTS.md) | `.claude/skills/`, `.claude/agents/`, `.claude/commands/`, `.claude/settings.json` | **`SUPPORTED`** |
| **GitHub Copilot** | [`.github/copilot-instructions.md`](./.github/copilot-instructions.md), [`AGENTS.md`](./AGENTS.md) | `.github/instructions/`, `.github/prompts/`, `.github/agents/`, `.agents/skills/` | **`SUPPORTED`** |
| **OpenAI Codex** | [`AGENTS.md`](./AGENTS.md) | `.agents/skills/*/SKILL.md`, `.codex/config.toml` | **`SUPPORTED`** |
| **Gemini CLI** | [`GEMINI.md`](./GEMINI.md), [`AGENTS.md`](./AGENTS.md) | `.gemini/commands/*.toml`, `.gemini/settings.json`, `.agents/skills/` | **`SUPPORTED`** |

See [`adapters/compatibility-matrix.md`](./adapters/compatibility-matrix.md) and [`docs/README.md`](./docs/README.md) for full documentation navigation.

---

## Quick Start

### 1. Validate the Framework Repository
Requires **Python 3.11+** and **Git 2.30+** (zero external `pip` packages required for core scripts):

```bash
python scripts/sync_adapters.py --check
python scripts/validate.py --mode framework
python scripts/run_tests.py --fail-on-skip
# Or via standard Python unittest discovery:
python -m unittest discover -s tests -v
```

### 2. Install into a New or Existing Project (Packaged `aief` CLI or Direct Python)
Install via standard Python packaging (`uvx` / `pipx`) or directly from source checkout without overwriting existing project files:

```bash
# Option A: One-command install via uvx / pipx (all 5 platforms, all 33 skills, auto-detected stacks)
uvx --from git+https://github.com/Raele24/ai-engineering-framework.git aief init /path/to/your-project
# Or install once via pipx install git+https://github.com/Raele24/ai-engineering-framework.git
aief init /path/to/your-project
aief compose /path/to/your-project

# Option B: Direct invocation from local framework clone
python scripts/bootstrap.py /path/to/your-project
python scripts/bootstrap.py /path/to/your-project --dry-run
python /path/to/your-project/scripts/compose.py --root /path/to/your-project
python /path/to/your-project/scripts/preflight.py --stacks dotnet,node/angular
```

### 3. Synchronize Platform Adapters After Editing Canonical Rules
```bash
python scripts/sync_adapters.py
python scripts/sync_adapters.py --check
```

---

## Repository Structure

| Path | Tier | Purpose |
| :--- | :--- | :--- |
| [`core/`](./core/) | Tier 1 | Canonical engineering rules (`core/rules/`), JSON schemas (`core/schemas/`), and `platform-capabilities.json` |
| [`agents/`](./agents/) | Tier 1 | 8 vendor-neutral agent role specifications (`product-analyst` through `devops-release-engineer`) |
| [`skills/`](./skills/) | Tier 1 | Modular `SKILL.md` packages (`skills/core/` + opt-in `skills/optional/` packs) and `skills/registry.json` |
| [`workflows/`](./workflows/) | Tier 1 | Step-by-step stage runbooks implementing the 15-phase canonical SDLC |
| [`templates/`](./templates/) | Tier 3 | Artifact templates (`PRD`, `SPEC`, `ADR`, `TEST_PLAN`, `HANDOFF_PACKET`, `project.framework.json`, stack `.gitignore` presets) |
| [`adapters/`](./adapters/) | Tier 2 | Platform-specific adapter configurations and [`compatibility-matrix.md`](./adapters/compatibility-matrix.md) |
| [`quality/`](./quality/) | Tier 1 | TDD protocol, code review rubric, Definition of Done, and tool classification matrix |
| [`security/`](./security/) | Tier 1 | Security authorization policy, secret prevention rules, and conditional Strix profile template |
| [`integrations/`](./integrations/) | Tier 1 | MCP server templates, Graphify knowledge graph runner, and optional orchestrator specs |
| [`scripts/`](./scripts/) | Tier 1 | Pure-stdlib Python CLIs (`bootstrap.py`, `compose.py`, `validate.py`, `sync_adapters.py`, `preflight.py`, `platform_capabilities.py`, `readiness.py`, `run_tests.py`) |
| [`docs/`](./docs/) | Tier 1 | Complete documentation suite (Architecture, Workflow, Getting Started, Consumer Usage Guide, Installation, Security, Roadmap) |
| [`tests/`](./tests/) | Tier 1 | Automated 6-tier offline regression suite (`84` stdlib tests via `scripts/run_tests.py`) |

---

## Documentation Index (`docs/README.md`)

Start from **[`docs/README.md`](./docs/README.md)** for the full structured documentation map. Key guides:

- **[Project Charter](./PROJECT_CHARTER.md)** — Vision, scope, non-goals, principles, and milestones.
- **[Canonical Workflow (`docs/WORKFLOW.md`)](./docs/WORKFLOW.md)** — Complete 15-phase operational SDLC specification.
- **[Architecture Guide (`docs/ARCHITECTURE.md`)](./docs/ARCHITECTURE.md)** — 4-tier architecture, state handoffs, and Graphify integration.
- **[Getting Started (`docs/GETTING_STARTED.md`)](./docs/GETTING_STARTED.md)** — End-to-end walkthrough of your first feature using the framework (`v0.4.0`).
- **[Consumer Usage Guide (`docs/CONSUMER_USAGE_GUIDE.md`)](./docs/CONSUMER_USAGE_GUIDE.md)** — Practical playbook for adopting and operating the framework day-to-day in real brownfield repositories.
- **[Customization & Auto-Loading Guide (`docs/CUSTOMIZATION_GUIDE.md`)](./docs/CUSTOMIZATION_GUIDE.md)** — Recipe guide for `.framework-custom/` (inline rules, custom skills, custom/appended agents), `disabled.*` toggles, and `scripts/compose.py`.
- **[Platform Compatibility Matrix (`adapters/compatibility-matrix.md`)](./adapters/compatibility-matrix.md)** — Configuration mapping, fallbacks, and platform verification status across all 5 platforms.
- **[Installation Guide (`docs/INSTALLATION.md`)](./docs/INSTALLATION.md)** — Prerequisites, bootstrap modes, and non-destructive updates.
- **[Configuration Reference (`docs/CONFIGURATION.md`)](./docs/CONFIGURATION.md)** — Configuring `project.framework.json`, platform adapters, and optional domain packs.
- **[Security Policy (`docs/SECURITY.md`)](./docs/SECURITY.md)** — Vulnerability reporting, secret prevention, and authorized security testing (Strix).
- **[Skill Compatibility Matrix (`docs/SKILL_COMPATIBILITY_MATRIX.md`)](./docs/SKILL_COMPATIBILITY_MATRIX.md)** — Per-platform discovery, activation, and script support for all 33 registered skills.
- **[Token Optimization Guide (`docs/TOKEN_OPTIMIZATION.md`)](./docs/TOKEN_OPTIMIZATION.md)** — Progressive disclosure principles, Ponytail, Caveman, RTK, and filesystem context offloading.
- **[Skill Installation Guide (`docs/SKILL_INSTALLATION_GUIDE.md`)](./docs/SKILL_INSTALLATION_GUIDE.md)** — Policy A/B/C classification and Windows CLI setup.
- **[Changelog (`CHANGELOG.md`)](./CHANGELOG.md)** — Release history from `v0.1.0` through `v0.4.0`.
- **[Versioning Policy (`docs/VERSIONING.md`)](./docs/VERSIONING.md)** — Semantic Versioning (`SemVer 2.0.0`) and schema migration guarantees.
- **[Contributing Guide (`docs/CONTRIBUTING.md`)](./docs/CONTRIBUTING.md)** — How to propose new skills, adapters, and workflow improvements.
- **[Roadmap (`docs/ROADMAP.md`)](./docs/ROADMAP.md)** — Milestone progression from `v0.1.0` through `v1.0.0`.

---

## License & Rationale

This project is licensed under the **[Apache License, Version 2.0](./LICENSE)**.

**Why Apache 2.0?**
1. **Explicit Patent Grant (Section 3):** Protects individual developers and enterprise engineering teams adopting the framework and its scripts against contributor patent litigation.
2. **Clear Derivative Work Rules (Section 4):** Consumer projects can embed, customize, and redistribute framework templates and adapters in proprietary or open-source software without viral copyleft obligations.
3. **Trademark Protection (Section 6):** Preserves the integrity of the official `ai-engineering-framework` name while allowing unrestricted forking and adaptation.
4. **Ecosystem Compatibility:** Fully compatible with the Agent Skills open standard and MIT-licensed dependencies.
