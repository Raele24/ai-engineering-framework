# Platform Compatibility Matrix (`compatibility-matrix.md`)

**Version:** `0.4.0`  
**Source of Truth:** Canonical rules in `core/rules/`, roles in `agents/`, skills in `skills/`, [`scripts/compose.py`](../scripts/compose.py), and [`core/platform-capabilities.json`](../core/platform-capabilities.json)  

---

## 1. Configuration & Capability Mapping Across Supported Platforms

| Capability | Canonical Source | 1. GitHub Copilot | 2. Google Antigravity | 3. Claude Code | 4. OpenAI Codex | 5. Gemini CLI |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Root Instruction Entry** | `core/rules/*.md` | `.github/copilot-instructions.md` & `AGENTS.md` | `GEMINI.md` & `AGENTS.md` | `CLAUDE.md` | `AGENTS.md` | `GEMINI.md` |
| **Scoped / Hierarchical Rules** | `core/rules/*.md` | `.github/instructions/*.instructions.md` (`applyTo` globs) | `.agents/rules/*.md` (`trigger: always_on \| glob \| model_decision`) | Nested `CLAUDE.md` files | Nested `AGENTS.md` files | Nested `GEMINI.md` files |
| **Custom Agent Roles** | `agents/*.md` | `.github/agents/*.agent.md` | `.agents/agents/*.md` + `invoke_subagent` | `.claude/agents/*.md` | Role prompt / skill loading (`AGENTS.md`) | Custom commands (`.gemini/commands/*.toml`) |
| **Portable Agent Skills** | `skills/*/*/SKILL.md` | `.agents/skills/` + `.github/prompts/*.prompt.md` | `.agents/skills/<name>/SKILL.md` (Native) | `.claude/skills/<name>/SKILL.md` (Native) | `.agents/skills/<name>/SKILL.md` (Native) | `.agents/skills/<name>/SKILL.md` |
| **Slash Commands / Stage Prompts** | `workflows/*.md` | `.github/prompts/*.prompt.md` | Built-in commands + `.agents/skills/` | `.claude/commands/*.md` | `~/.codex/prompts/*.md` or skills | `.gemini/commands/*.toml` |
| **MCP Server Config** | `integrations/mcp/mcp.template.json` | `.vscode/mcp.json` | `mcp_config.json` | `.mcp.json` | `.codex/config.toml` (`[mcp_servers.*]`) | `.gemini/settings.json` (`mcpServers`) |
| **Lifecycle Hooks** | `core/rules/human-approval-gates.md` | Git hooks (`.githooks/`) | `hooks.json` | `.claude/settings.json` (`hooks`) | Git hooks + sandbox policies | `.gemini/settings.json` + Git hooks |
| **Browser Automation** | `skills/core/agent-browser/` | Playwright MCP (`@playwright/mcp`) | Native `browser` subagent | Playwright MCP / CLI | Playwright MCP / CLI | Playwright MCP |
| **Multi-Agent Parallelism** | `agents/planner-orchestrator.md` | Subagent calls in VS Code Agent Mode | Native `invoke_subagent`, `run_workflow`, `swarm` | Native `.claude/agents/` subagent tool | Parallel CLI worktrees / sub-runs | Sequential or shell-dispatched workers |

---

## 2. Unsupported or Partially Supported Platform Features & Fallbacks

1. **OpenAI Codex Custom Agent Files:**
   - *Limitation:* Codex CLI uses `AGENTS.md` and `.agents/skills/*/SKILL.md` rather than a dedicated `.codex/agents/*.md` subagent directory.
   - *Fallback:* `scripts/sync_adapters.py` maps all 8 canonical roles into `AGENTS.md` role-routing instructions and exposes stage workflows via skills.
2. **Gemini CLI Subagent Spawning:**
   - *Limitation:* Gemini CLI executes primarily as a single-session agent with custom TOML slash commands (`.gemini/commands/*.toml`).
   - *Fallback:* `adapters/gemini-cli/commands/` provides stage-transition TOML commands (`/workflow:stage1` through `/workflow:stage6`) that read/write `.framework-state/` sequentially.
3. **Hook Syntax Differences:**
   - *Limitation:* Claude Code `settings.json` hooks (`PreToolUse`/`PostToolUse` matching `Bash`/`Edit`), Antigravity `hooks.json` (`<hook-name>.{SessionStart,PreToolUse,PostToolUse,PreInvocation,PostInvocation,Stop}`), and GitHub Copilot have incompatible hook schemas.
   - *Fallback:* `adapters/antigravity/hooks.json` ships a schema-valid `"enabled": false` opt-in reminder template, while **universal Git/CLI validation (`python scripts/validate.py`)** provides a 100% platform-independent enforcement layer.
4. **Consumer Skill Isolation & Host-Global Discovery (`GAP-07`):**
   - *Verified Evidence:* In `M8-02B`, Antigravity CLI (`agy.exe`) executed `25/25` workspace calls inside the consumer root with `0` upstream repo leaks (`RUNTIME_VERIFIED`). In `M8-03A`/`M8-03B`, Codex CLI and Gemini CLI were observed scanning host-global `$HOME/.agents/skills/` alongside workspace paths, and Antigravity IDE exposes `$HOME/.gemini/config/skills/`.
   - *Boundary:* `scripts/validate.py --mode consumer` enforces lockfile-backed workspace boundaries inside `.agents/skills/` and `.claude/skills/` (`ERROR`/`WARNING`) and reports host-global skill folders as `INFO` only without touching user-global files.
5. **Current Compatibility Tier Summary (`v0.4.0`):**
   - **All 5 Platforms (Adapter & Schema Level):** Full inline entry composition (`scripts/compose.py`), native skill projection (`.agents/skills/` and `.claude/skills/`), read-only reviewer enforcement, and schema contracts are **`IMPLEMENTED & CONTRACT_VALIDATED`** (`84/84` automated offline tests).
   - **Maintainer-Host Live CLI Smoke Checks:**
     - **Antigravity IDE (`1.12.0`) & CLI (`agy v1.5.10`):** **`RUNTIME_VERIFIED`** (`M6-Pilot`, `M8`, `M9` reference live E2E + brownfield custom skill verification).
     - **OpenAI Codex CLI (`0.169.0`):** **`PARTIAL_RUNTIME_VERIFIED`** (`AGENTS.md` + native `.agents/skills/` discovery verified in M8-03B; `tool_id_map: unknown`; Windows sandbox requires external OS setup).
     - **Claude Code (`2.1.311`), GitHub Copilot, Gemini CLI (`0.68.0`):** **`CONTRACT_VALIDATED`** on disk; live CLI runs were **`Not Run on Maintainer Host`** (`core/platform-capabilities.json` state `BLOCKED_EXTERNAL` strictly denotes missing host account/extension prerequisites, **not** a framework defect).

---

## 3. Support-Tier Classification & Evidence Boundaries

| Platform | Adapter Contracts | Host Live Probe (`platform-capabilities.json`) | Verified Live Capabilities | Static / Contract-Validated Capabilities | Host Prerequisites for Live Testing |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **Google Antigravity** | **`SUPPORTED`** | **`RUNTIME_VERIFIED`** | Root instructions (`GEMINI.md`, `AGENTS.md`), `.agents/rules/`, `.agents/skills.json`, `.agents/skills/` (incl. custom), full 15-phase SDLC + Browser E2E | Agent frontmatter, `hooks.json` schema (`enabled: false`, `documentation_derived`) | Nested `run_command` under `accept-edits` / `exebox`; host-global `~/.gemini/config/skills/` visible |
| **OpenAI Codex CLI** | **`SUPPORTED`** | **`PARTIAL_RUNTIME_VERIFIED`** | ChatGPT OAuth, `AGENTS.md` auto-injection, native `.agents/skills/` scanning, `19`-skill listing | `.codex/config.toml` TOML schema, role routing via `AGENTS.md` (`hooks_support: unsupported`) | External Windows sandbox setup required for write execution (`tool_id_map: unknown`) |
| **Anthropic Claude Code** | **`SUPPORTED`** | `BLOCKED_EXTERNAL` *(Host auth)* | Isolated CLI `2.1.311` `--version`/`--help` | `.claude/skills/`, `CLAUDE.md`, read-only `.claude/agents/*.md` (`Read, Glob, Grep` / `disallowedTools: Write, Edit, Bash`), clean `.claude/settings.json` | Requires user Claude `Pro`, `Max`, or `Ultra` login to run live CLI smoke checks |
| **GitHub Copilot** | **`SUPPORTED`** | `BLOCKED_EXTERNAL` *(Host auth)* | Not yet run in Copilot IDE on host | `.github/copilot-instructions.md`, `.instructions.md`, `.prompt.md`, read-only `.agent.md` (`["read", "search"]`), `.agents/skills/`, `AGENTS.md` | Requires VS Code Copilot extensions or authenticated Copilot CLI on host |
| **Google Gemini CLI** | **`SUPPORTED`** | `BLOCKED_EXTERNAL` *(Host tier)* | Isolated CLI `0.68.0` pre-auth `skills list` global scan + untrusted-folder gate | `GEMINI.md`, clean `.gemini/settings.json`, `.gemini/commands/workflow.toml`, `.agents/skills/` | Requires eligible workspace/account tier (`tool_id_map: unknown`; `hooks_support: unknown`) |
