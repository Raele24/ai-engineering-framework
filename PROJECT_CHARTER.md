# Project Charter — AI Engineering Framework

> [!NOTE]
> **Historical M1 Baseline Document (`v0.1.0`):** This charter captures the initial architectural vision and M0–M5 milestone blueprint. For current `v0.7.1` platform status, CLI scripts (`bootstrap.py`, `compose.py`, `validate.py`, `sync_adapters.py`, `preflight.py`, `platform_capabilities.py`, `readiness.py`, `run_tests.py`), and roadmap details, see [`README.md`](./README.md) and [`docs/ROADMAP.md`](./docs/ROADMAP.md).

**Project Name:** AI Engineering Framework  
**Repository:** `ai-engineering-framework`  
**Version:** `0.1.0`  
**License:** Apache License 2.0  
**Status:** Active Foundation  

---

## 1. Vision and Mission

### 1.1 Vision
Establish an open-source, vendor-neutral engineering standard that enables software developers and teams to execute the complete Software Development Lifecycle (SDLC) with AI coding agents reliably, safely, and reproducibly across any supported agent platform.

### 1.2 Mission
Replace fragmented prompt collections and vendor-locked configurations with a **Canonical Engineering Workflow** backed by structured filesystem state handoffs, reusable role definitions, portable Agent Skills (`SKILL.md`), deterministic validation scripts, and thin platform-specific adapters.

---

## 2. Project Scope

### 2.1 In Scope
- **Canonical 15-Phase SDLC Workflow:** End-to-end operational methodology from discovery and requirement clarification (`Grill Me`) through specification, ADR creation, task decomposition, TDD implementation, code review, QA, security validation, CI/CD release, and retrospectives.
- **Modular Agent Role System:** Vendor-neutral role contracts defining responsibilities, tool permissions, inputs, outputs, and delegation boundaries.
- **Portable Skill Architecture:** Reusable procedural runbooks adhering to the Agent Skills (`SKILL.md`) open standard, separated into Core Engineering skills and opt-in Domain Packs.
- **Multi-Platform Adapters:** Automated generation and synchronization of thin configuration adapters for GitHub Copilot, Google Antigravity, Claude Code, OpenAI Codex, and Gemini CLI.
- **Quality & Authorized Security Framework:** Built-in TDD enforcement, static and architectural validation (via Graphify knowledge graphs), secret scanning, E2E testing patterns (Playwright), and strictly gated authorized security testing (Strix).
- **Non-Destructive Lifecycle Tooling:** Zero-dependency Python CLI utilities (`bootstrap.py`, `validate.py`, `sync_adapters.py`) for installing, updating, and verifying the framework in consumer repositories without overwriting project-owned files.

### 2.2 Out of Scope (Non-Goals)
- **Conversational Chatbot Wrapper:** This framework is built for autonomous and semi-autonomous coding agents with filesystem and terminal access, not web chat interfaces lacking repository tools.
- **Mandatory External Orchestration Server:** The framework must operate natively inside the host coding agent environment without requiring external daemons, databases, or paid SaaS orchestrators (such as Paperclip).
- **Vendor Lock-In:** No core workflow phase may depend exclusively on a proprietary feature of a single LLM provider or IDE.
- **Uncontrolled Autonomous Execution:** High-impact operations (requirement sign-off, architecture approval, active security scanning, public releases, and destructive commands) always require explicit human approval gates.

---

## 3. Target Users

1. **Individual Software Engineers & Architects:** Developers using AI coding agents who require rigorous engineering discipline (specs, ADRs, TDD, clean code review) instead of ad-hoc "vibe coding."
2. **Multi-Platform Engineering Teams:** Organizations where developers use heterogeneous tools (e.g., VS Code + GitHub Copilot, Google Antigravity, Claude Code, OpenAI Codex, Gemini CLI) on the same repository and require identical engineering rules and quality gates.
3. **Platform & DevSecOps Engineers:** Teams responsible for enforcing security guardrails, secret prevention, and reproducible CI/CD validation across AI-assisted repositories.

---

## 4. Architectural Principles

1. **Single Canonical Source of Truth:** All engineering rules, workflows, roles, and skills live once in canonical framework directories (`core/`, `workflows/`, `agents/`, `skills/`). Platform-specific files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`) are thin adapters referencing or synced from canonical files.
2. **Filesystem State Over Conversational Memory:** Agents transfer work between phases via structured artifacts on disk (`docs/specs/`, `docs/adr/`, `.framework-state/handoffs/`), eliminating the multi-agent "telephone game" degradation problem.
3. **Balanced Autonomy with Explicit Approval Gates:** Routine workspace tasks (drafting docs, writing tests, running local validation) execute autonomously (**Category A**), while consequential architectural, security, or external actions pause at mandatory human gates (**Category B / C**).
4. **Progressive Context Disclosure:** Skills and domain modules load on-demand only when relevant to the active task, preserving context window capacity and attention fidelity.
5. **Four-Tier Asset Separation:** Framework-wide assets, platform adapters, consumer project artifacts, and ephemeral runtime state are strictly isolated so framework updates never clobber project code or specifications.
6. **Zero-Dependency Core Portability:** Core bootstrap, adapter synchronization, and validation scripts run on the Python 3.12+ standard library across Windows, macOS, and Linux.

---

## 5. Supported Platforms

| Tier | Platform | Primary Entry Points & Adapter Mechanism |
| :--- | :--- | :--- |
| **Tier 1** | **GitHub Copilot** | `.github/copilot-instructions.md`, `AGENTS.md`, `.github/instructions/*.instructions.md`, `.github/prompts/*.prompt.md`, `.github/agents/*.agent.md` |
| **Tier 1** | **Google Antigravity** | `GEMINI.md`, `AGENTS.md`, `.agents/rules/*.md`, `.agents/skills/*/SKILL.md`, `hooks.json`, `mcp_config.json` |
| **Tier 1** | **Claude Code** | `CLAUDE.md`, `.claude/agents/*.md`, `.claude/commands/*.md`, `.claude/skills/*/SKILL.md`, `.claude/settings.json` |
| **Tier 1** | **OpenAI Codex** | `AGENTS.md`, `.codex/config.toml`, `.agents/skills/*/SKILL.md` |
| **Tier 1** | **Gemini CLI** | `GEMINI.md`, `.gemini/settings.json`, `.gemini/commands/*.toml`, `.agents/skills/*/SKILL.md` |
| **Tier 2** | **Other Compatible Agents** | Any IDE or CLI agent supporting `AGENTS.md`, Model Context Protocol (MCP), or the Agent Skills (`SKILL.md`) specification |

---

## 6. Success Criteria

1. **Completeness & Consistency:** All 11 foundation documents, 15 canonical workflow phases, 8 agent roles, core/optional skills, and 5 platform adapters are implemented and pass automated validation (`python scripts/validate.py` exits `0`).
2. **Zero Rule Duplication:** Platform adapters are deterministically synced via `python scripts/sync_adapters.py --check` with zero drift.
3. **Non-Destructive Bootstrap:** `python scripts/bootstrap.py` can initialize and update a target project directory while preserving consumer-modified files and verifying SHA-256 lock manifests.
4. **Automated Test Verification:** Unit and integration tests in `tests/test_framework.py` pass 100%.
5. **Architectural Observability:** Graphify (`graphify .`) builds a valid codebase knowledge graph (`graphify-out/`) confirming modular cohesion.

---

## 7. Initial Milestones

| Milestone | Scope | Status |
| :--- | :--- | :--- |
| **M0: Audit & Blueprint** | Initial environment audit and architectural implementation plan | Completed |
| **M1: Canonical Foundation** | Charter, README, 15-phase `WORKFLOW.md`, `ARCHITECTURE.md`, operational guides, schemas, and templates | In Progress |
| **M2: Agents, Skills & Domain Packs** | 8 canonical agent role definitions, `skills/registry.json`, core SDLC skills, and opt-in domain packs | Planned |
| **M3: Platform Adapters & Orchestration** | `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, 5 platform adapter suites, `sync_adapters.py`, and stage runbooks | Planned |
| **M4: Quality, Security & Local Tooling** | Quality rubrics, security policies, `bootstrap.py`, `validate.py`, unit tests, local Git repo, and Graphify graph | Planned |
| **M5: GitHub Publication & CI/CD** | Remote repository creation (`Raele24/ai-engineering-framework`), branch push, and live GitHub Actions verification | Pending Review Gate |
