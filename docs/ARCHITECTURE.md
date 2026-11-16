# Architecture Guide (`ARCHITECTURE.md`)

**Status:** Canonical Architecture Specification  
**Version:** `0.1.0`  

---

## 1. Architectural Vision

The **AI Engineering Framework** is designed as a **layered, vendor-neutral engineering operating system** for AI coding agents. Its primary architectural goal is to decouple **what software engineering discipline requires** (the Canonical Core) from **how individual AI coding platforms load instructions, tools, and subagents** (the Platform Adapter Layer).

---

## 2. Four-Tier Layered Architecture

```mermaid
flowchart TD
    subgraph T1["Tier 1: Canonical Framework Core (Immutable / Framework-Managed)"]
        CR["core/rules/ (Engineering & Security Laws)"]
        CS["core/schemas/ (JSON Validation Schemas)"]
        WF["docs/WORKFLOW.md & workflows/ (15-Phase SDLC)"]
        AG["agents/ (8 Vendor-Neutral Role Specs)"]
        SK["skills/core/ & skills/optional/ (SKILL.md Standard)"]
        QL["quality/ & security/ (Rubrics, TDD, Strix Profiles)"]
        SC["scripts/ (bootstrap.py, validate.py, sync_adapters.py)"]
    end

    subgraph T2["Tier 2: Platform Adapter Layer (Generated / Synced via sync_adapters.py)"]
        A_UNI["Universal Entry Points: AGENTS.md, CLAUDE.md, GEMINI.md"]
        A_COP["GitHub Copilot: .github/copilot-instructions.md, .github/agents/"]
        A_AGY["Google Antigravity: .agents/rules/, .agents/skills/, hooks.json"]
        A_CLC["Claude Code: .claude/agents/, .claude/commands/, .claude/settings.json"]
        A_CDX["OpenAI Codex: .codex/config.toml, .agents/skills/"]
        A_GEM["Gemini CLI: .gemini/commands/*.toml, .gemini/settings.json"]
    end

    subgraph T3["Tier 3: Consumer Project Layer (Project-Owned / Never Overwritten)"]
        PCFG["project.framework.json"]
        PSPEC["docs/specs/ (PRDs, Clarified Reqs, Specs)"]
        PADR["docs/adr/ (Architecture Decision Records)"]
        PPLAN["docs/plans/ (Implementation Plans & Task Backlogs)"]
    end

    subgraph T4["Tier 4: Ephemeral Runtime & Knowledge State"]
        FSTATE[".framework-state/ (manifest.json & phase-NN-handoff.json)"]
        GRAPH["graphify-out/ (graph.json, GRAPH_REPORT.md)"]
    end

    T1 -->|"Compiled / Bridged by sync_adapters.py"| T2
    T1 -->|"Instantiates Templates"| T3
    T2 -->|"Executes Against"| T3
    T3 -->|"Reads & Writes State"| T4
```

### 2.1 Why Four Tiers?
1. **Zero Config Drift (Tier 1 $\rightarrow$ Tier 2):** Editing a rule in `core/rules/` or adding an agent role in `agents/` requires running `python scripts/sync_adapters.py`. The script regenerates or verifies all platform adapter files so Copilot, Antigravity, Claude Code, Codex, and Gemini CLI never diverge.
2. **Safe Downstream Upgrades (Tier 1/2 vs. Tier 3):** When a consumer project upgrades from Framework `v0.1.0` to `v0.2.0` via `python scripts/bootstrap.py --update`, only unmodified Tier 1 and Tier 2 files tracked in `.framework-lock.json` are updated. Tier 3 project artifacts (`project.framework.json`, `docs/specs/`, `docs/adr/`, application source code) are never overwritten.
3. **Clean Version Control (Tier 3 vs. Tier 4):** Ephemeral orchestration checkpoints in `.framework-state/` are git-ignored by default while permanent engineering decisions (`docs/specs/`, `docs/adr/`) are committed to Git.

---

## 3. Component Responsibilities & Dependencies

| Component | Path | Responsibility | Upstream Dependencies | Downstream Consumers |
| :--- | :--- | :--- | :--- | :--- |
| **Core Rules** | `core/rules/` | Defines non-negotiable engineering, approval, context-handoff, and security invariants | None | All agents, workflows, and platform adapters |
| **Core Schemas** | `core/schemas/` | Defines JSON schemas for roles, skills, handoff packets, and project config | None | `scripts/validate.py`, `scripts/bootstrap.py` |
| **Canonical Roles** | `agents/` | Defines the 8 specialized engineering roles, tool permissions, and boundaries | `core/schemas/agent-role.schema.json` | `workflows/`, `adapters/` |
| **Skill Library** | `skills/` | Provides on-demand procedural runbooks (`SKILL.md`) split into `core/` and `optional/` | `core/schemas/skill-frontmatter.schema.json` | `agents/`, host skill loaders (`.agents/skills/`) |
| **Workflow Runbooks** | `workflows/` | Operational stage playbooks implementing the 15 phases of `docs/WORKFLOW.md` | `core/rules/`, `agents/`, `skills/` | Host agents, slash commands, orchestrators |
| **Platform Adapters** | `adapters/` | Maps canonical roles, rules, and workflows to native platform files | `core/`, `agents/`, `skills/`, `workflows/` | Copilot, Antigravity, Claude Code, Codex, Gemini CLI |
| **Quality & Security** | `quality/`, `security/` | Enforces TDD contracts, review rubrics, secret scanning, and Strix authorization | `core/rules/security-guardrails.md` | Phases 9–12 (`implementation-engineer`, `code-reviewer`, `qa-engineer`, `security-engineer`) |
| **Integrations** | `integrations/` | Bridges optional MCP servers, Graphify knowledge graphs, and external orchestrators | `core/` | Optional project workflows |
| **CLI Scripts** | `scripts/` | Cross-platform Python utilities for bootstrap, adapter sync, and validation | Python 3.10+ stdlib, `core/schemas/` | Developers, agents, and GitHub Actions CI |

---

## 4. Context Engineering & Multi-Agent Topology

The framework incorporates modern context engineering principles (`context-fundamentals`, `multi-agent-patterns`, `filesystem-context`):

### 4.1 Context Isolation Over Anthropomorphism
Multiple agents exist in this framework **to isolate context windows**, not to simulate corporate bureaucracy:
- **Single-Agent Sequential Mode:** On platforms or tasks where a single agent executes the workflow, the agent transitions across phases by writing the phase handoff file to `.framework-state/handoffs/` and compacting/clearing prior conversational noise before starting the next stage.
- **Supervisor / Subagent Mode:** On platforms supporting subagents (Google Antigravity `invoke_subagent` / `run_workflow` / `swarm`, Claude Code subagents), `planner-orchestrator` dispatches fresh subagent instances with only the specific input files (`input_artifacts`) required for that task.
- **Hard Worker Cap:** A supervisor turn never spawns more than **3 to 5 concurrent workers**, preventing supervisor context saturation.

### 4.2 Progressive Skill Disclosure & Domain Isolation
Loading every guideline into the global system prompt causes the **Lost-in-the-Middle Effect** and wastes token budget.
- **Always-On Context (`AGENTS.md` / `CLAUDE.md` / `GEMINI.md`):** Kept concise (< 6 KB). Contains only core workflow routing, safety/approval gates, and a compact metadata index (~1,245 tokens for all 30 registered skills — a **98.4% reduction** compared to loading all `SKILL.md` bodies).
- **On-Demand Context (`skills/`):** Organized into `skills/core/` (8 core SDLC, YAGNI `ponytail`, and `graphify` skills) and 5 isolated optional domain packs (`communication`, `context-engineering`, `agent-architecture`, `frontend-design`, `growth-media`). See [`docs/SKILL_COMPATIBILITY_MATRIX.md`](./SKILL_COMPATIBILITY_MATRIX.md) and [`docs/TOKEN_OPTIMIZATION.md`](./TOKEN_OPTIMIZATION.md).
- **Offline Script & Database Execution:** Heavy reference assets (such as the 28 CSV databases in `ui-ux-pro-max` or the 36 Angular guides in `angular-developer`) remain on disk and are queried via standard-library Python scripts (`search.py`) or targeted `read_file` calls.

---

## 5. Codebase Knowledge Graph Integration (`Graphify`)

To prevent architectural drift and blind file grepping on medium-to-large repositories, the framework integrates **Graphify (`graphify 0.9.48`)** as a first-class architectural component ([`skills/core/graphify/SKILL.md`](../skills/core/graphify/SKILL.md)):

1. **Minimum Corpus Threshold Guard:** Only build or update `graphify-out/` when a repository has **$\ge 15$ tracked code/doc files OR $> 2,000$ lines of code**. For tiny projects ($< 15$ files), agents read files directly to avoid unnecessary graph overhead.
2. **Knowledge Graph Generation (`graphify .` / `graphify update .`):** Parses repository source code, SQL schemas, and documentation into `graphify-out/graph.json` and `graphify-out/GRAPH_REPORT.md` using local deterministic `tree-sitter` AST parsing (zero external LLM API cost).
3. **Phase 1 & 4 (Discovery & Research):** When `graphify-out/graph.json` exists, agents query the graph (`graphify query "<question>"`, `graphify path "<A>" "<B>"`, `graphify explain "<node>"`, `graphify god-nodes`) before scanning raw directory trees.
4. **Phase 10 & 14 (Code Review & Docs):** Agents run `graphify update .` to incrementally refresh the AST/concept graph and verify that new changes do not introduce unintended god-nodes or cross-layer couplings.

---

## 6. Key Architecture Decision Records (ADRs)

All major architectural decisions for the framework itself are recorded under [`docs/adr/`](./adr/):
- **[ADR-0001: Open-Source Licensing under Apache 2.0](./adr/ADR-0001-open-source-license.md)**
- **[ADR-0002: Single Canonical Core with Thin Platform Adapters](./adr/ADR-0002-canonical-core-and-thin-adapters.md)**
- **[ADR-0003: Filesystem State Handoffs over Conversational Memory](./adr/ADR-0003-filesystem-state-handoffs.md)**
