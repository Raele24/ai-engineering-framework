# Platform Compatibility Matrix (`compatibility-matrix.md`)

**Version:** `0.1.0`  
**Source of Truth:** Canonical rules in `core/rules/`, roles in `agents/`, and skills in `skills/`  

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
   - *Limitation:* Claude Code `settings.json` hooks (`PreToolUse`/`PostToolUse` matching `Bash`/`Edit`), Antigravity `hooks.json`, and GitHub Copilot have incompatible hook schemas.
   - *Fallback:* Each platform adapter in `adapters/<platform>/` includes its native hook template, while **universal Git pre-commit validation (`python scripts/validate.py`)** provides a 100% platform-independent enforcement layer.
