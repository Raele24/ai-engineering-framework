# Orchestration Strategy & External Orchestrator Evaluation (`integrations/orchestrators/`)

**Version:** `0.1.0`  
**Core Principle:** The AI Engineering Framework requires **zero external orchestration servers** to function.  

---

## 1. Native Host Orchestration (Default — Tier 0)

By default, the framework uses the **Native Host Agent + Filesystem State Machine (`.framework-state/`)**:

1. **Single-Agent Sequential Execution:** Any coding agent (Copilot, Antigravity, Claude Code, Codex, Gemini CLI) reads the active stage runbook (`workflows/01..06-*.md`), writes the phase artifact to `docs/` or `src/`, and records `.framework-state/handoffs/phase-<NN>-handoff.json`.
2. **Native Subagent Delegation:** On platforms with native subagents (Google Antigravity `invoke_subagent` / `run_workflow` / `swarm`, Claude Code `.claude/agents/`), `planner-orchestrator` spawns isolated subagents passing only the required file paths from `.framework-state/`.

**Why Native First?**
- Zero daemon/Docker/database setup friction.
- Uses existing IDE/CLI subscriptions and credentials.
- 100% transparent markdown and JSON state files on disk.

---

## 2. Evaluation of Optional External Orchestrators

When an enterprise team requires unattended multi-repo batch orchestration, persistent webhook triggers, or budget metering across teams, external orchestrators can wrap the framework by consuming `.framework-state/handoffs/phase-<NN>-handoff.json`:

| Orchestrator | Architecture Style | Strengths | Limitations / Overhead | Framework Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **Native Host + `.framework-state/`** | Filesystem state machine + native IDE/CLI subagents | Zero external dependencies; works offline/locally; zero extra infra cost | Tied to active developer session or CI runner | **Core Default (Required)** |
| **Paperclip** | Autonomous company/org multi-agent control plane | Persistent ticket queues, role hierarchy, budget/cost dashboards | Requires external service/server setup; org-metaphor overhead for single repos | **Optional Future Integration** (Use only for multi-agent autonomous ticket queues) |
| **LangGraph** | Explicit state-machine graph (`StateGraph`) in Python/TS | Deterministic node transitions, checkpoint persistence, cyclic review loops | Requires authoring Python/TS graph runner and API key wiring | **Optional Adapter** (Best for programmatic CI/batch pipelines) |
| **CrewAI** | Role-based sequential/hierarchical crews | Maps cleanly to `agents/*.md` roles and `tasks` | Higher token multiplier due to conversational chatter if not constrained | **Optional Adapter** |
| **AutoGen** | Event-driven / conversational multi-agent group chat | Flexible exploratory debate patterns | Risk of sycophantic consensus and high token burn without strict termination rules | **Optional Adapter** |

---

## 3. Integration Contract for External Orchestrators

Any external orchestrator integrating with this framework must obey three rules:
1. **Never Redefine `docs/WORKFLOW.md`:** Each orchestrator node must invoke one of the 6 canonical stage runbooks (`workflows/01..06-*.md`).
2. **Read & Write `.framework-state/`:** State transitions must validate against `core/schemas/handoff-packet.schema.json`.
3. **Pause at Human Approval Gates:** External orchestrators must suspend execution and request human webhook/UI approval at `Gate-01a`, `Gate-01b`, `Gate-02`, `Gate-03`, `Gate-Sec`, `Gate-04`, and `Gate-05`.
