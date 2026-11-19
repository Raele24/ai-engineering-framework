# Consumer Customization & Auto-Loading Guide (`CUSTOMIZATION_GUIDE.md`)

**Version:** `0.4.0`  

---

## 1. Why `.framework-custom/` + `scripts/compose.py` Exist

AI coding platforms do **not** read [`project.framework.json`](../templates/project.framework.json) or `.framework-custom/` directly on their own:

| Platform | Files Loaded Automatically on Startup | Composed From |
| :--- | :--- | :--- |
| **Google Antigravity** | `GEMINI.md`, `AGENTS.md`, `.agents/rules/framework-core.md`, `.agents/skills.json`, `.agents/skills/` | Framework core + `.framework-custom/` + `disabled.*` |
| **Claude Code** | `CLAUDE.md`, `AGENTS.md`, `.claude/skills/`, `.claude/agents/`, `.claude/commands/`, `.claude/settings.json` | Framework core + `.framework-custom/` + `disabled.*` |
| **GitHub Copilot** | `.github/copilot-instructions.md`, `.github/instructions/framework.instructions.md`, `AGENTS.md`, `.github/agents/` | Framework core + `.framework-custom/` + `disabled.*` |
| **OpenAI Codex** | `AGENTS.md`, `.agents/skills/`, `.codex/config.toml` | Framework core + `.framework-custom/` + `disabled.*` |
| **Gemini CLI** | `GEMINI.md`, `AGENTS.md`, `.agents/skills/`, `.gemini/commands/workflow.toml`, `.gemini/settings.json` | Framework core + `.framework-custom/` + `disabled.*` |

Instead of editing generated entry files in five places (which would freeze updates or drift between platforms), write every project customization inside **`.framework-custom/`** and toggle settings inside **`project.framework.json`**.  
Then **`scripts/compose.py`** acts as a zero-dependency local compiler inside your repository:
1. Combines active framework rules + gates + your `.framework-custom/` overlay inline across all enabled platform entry files.
2. Applies `disabled.*` exclusions and projects custom skills/agents.
3. Validates the resulting consumer workspace automatically in the same command.

> [!TIP]
> **Minimal Daily Friction:** During normal coding you do **not** run `compose.py`. Generated entry files already instruct AI agents to run `python scripts/compose.py` automatically whenever they edit `.framework-custom/` or `project.framework.json`. You only need to run it manually if you edit those files yourself in an editor.

---

## 2. Quick Install, Brownfield Auto-Import & Updates

### Clean Zero-Flag Bootstrap
From [`ai-engineering-framework`](../README.md), install everything with one command (or `aief init .`):

```powershell
python /path/to/ai-engineering-framework/scripts/bootstrap.py /path/to/my-project
# Or with packaged CLI: aief init /path/to/my-project
```

Defaults applied automatically when flags are omitted:
- **Platforms:** all `5` (`antigravity`, `copilot`, `claude-code`, `codex`, `gemini-cli`).
- **Skills:** `all` (`33/33` skills installed and projected; disable unwanted ones in `project.framework.json`).
- **Profile:** `standard`.
- **Stacks (`auto`):** detects `dotnet` (`*.sln`/`*.csproj`/`*.fsproj`), `node-angular` (`angular.json`/`package.json`), and `python` (`pyproject.toml`/`requirements.txt`/`setup.py`) automatically.
- **Brownfield Auto-Import:** if the repository has no `.framework-lock.json` yet and already contains pre-existing `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or `.github/copilot-instructions.md` (without `AUTO-GENERATED`), `bootstrap.py` backs them up under `.framework-custom/imported/` and composes their rules inline into every platform entry point so nothing is lost.

### Updating Later Without Losing Customizations
```powershell
python /path/to/ai-engineering-framework/scripts/bootstrap.py /path/to/my-project --update
# Or with packaged CLI: aief update /path/to/my-project
```
- Preserves `.framework-custom/` and `project.framework.json` (`disabled.*`, `customizations.*`).
- Preserves your saved `enabledPlatforms`, `workflowProfile`, `optionalSkillPacks`, and `stacks` automatically when flags are omitted.
- Updates unmodified framework files (`core/`, `workflows/`, `skills/`, `scripts/`) and **re-composes** all inline entry files with your latest `.framework-custom/` content.

---

## 3. Overlay Structure (`.framework-custom/`)

```text
.framework-custom/                 # Consumer-owned (Tier 3) — NEVER overwritten by --update
├── instructions.md                # Main project rules loaded inline into all 5 platforms
├── rules/                         # Topic-specific Markdown rules (loaded inline alphabetically)
│   ├── database.md
│   └── api-conventions.md
├── imported/                      # Auto-archived pre-existing root instructions (brownfield)
│   └── CLAUDE.md
├── skills/                        # Project-specific Agent Skills (projected to .agents/skills & .claude/skills)
│   └── billing-invariants/
│       ├── SKILL.md
│       └── checklist.md
├── agents/                        # Canonical role extensions or custom project subagents
│   ├── implementation-engineer.append.md
│   ├── code-reviewer.append.md
│   └── db-migrator.md
├── prompts/                       # Custom reusable slash prompts (projected to Copilot/Claude/Gemini CLI)
│   └── api-audit.md
└── mcp.json                       # Custom MCP servers (${ENV_VAR} placeholders only; secret scan enforced)
```

---

## 4. Practical Customization Recipes

### Recipe 1 — Add Project Rules Loaded Automatically on Turn 1
Edit `.framework-custom/instructions.md` or add focused files under `.framework-custom/rules/*.md`:

```markdown
# Project Engineering Rules
- Always use `PostgreSQL` UTC timestamps (`timestamptz`) and explicit Alembic migrations.
- Backend APIs live in `src/Api/`; frontend Angular workspace lives in `src/Web/`.
- Run `pytest -q` and `npm test -- --watch=false` before finishing any implementation task.
```

*(Note: an untouched placeholder `.framework-custom/instructions.md` containing only comments is ignored automatically.)*

Apply and verify in one command:
```powershell
python scripts/compose.py
```

Result:
- Your rules appear inline inside `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.agents/rules/framework-core.md`, `.github/copilot-instructions.md`, and `.github/instructions/framework.instructions.md`.

---

### Recipe 2 — Add a Project-Specific Custom Skill
Create `.framework-custom/skills/<skill-name>/SKILL.md` (folder names must be single-segment, without `/`, `..`, or symlinks):

```markdown
---
name: billing-invariants
description: Enforces decimal ledger rounding, idempotency keys, and audit log invariants
---

# Billing Invariants

- Never use IEEE-754 floats for monetary amounts; always store integer minor units or `DECIMAL(18,4)`.
- Every charge/refund mutation requires an idempotency key header verified before state write.
- See [checklist](./checklist.md).
```

Run `python scripts/compose.py`:
- Copies `.framework-custom/skills/billing-invariants/` into `.agents/skills/billing-invariants/` and `.claude/skills/billing-invariants/`.
- Tracks files in `.framework-lock.json` under `"ownership": "consumer_custom_skill"` (zero warnings from `validate.py`).
- Registers `billing-invariants` inside `AGENTS.md` Section 4 (`Active Skills`).
- Removing the folder or adding `"billing-invariants"` to `disabled.skills` prunes projections automatically.

---

### Recipe 3 — Extend Canonical Agents or Define Custom Agents

#### Option A: Append rules to an existing framework role (`*.append.md`)
Create `.framework-custom/agents/implementation-engineer.append.md` or `.framework-custom/agents/code-reviewer.append.md`:

```markdown
- Always validate EF Core migration down-scripts for reversibility.
- Reject endpoints missing authorization attributes or rate-limit policies.
```

- `implementation-engineer.append.md` appends to `agents/implementation-engineer.md`.
- `code-reviewer.append.md` appends to `agents/code-reviewer.md`, `.claude/agents/framework-code-reviewer.md`, and `.github/agents/code-reviewer.agent.md`.

#### Option B: Override an existing role or create a new custom subagent (`<name>.md`)
Create `.framework-custom/agents/db-migrator.md`:

```markdown
---
name: db-migrator
title: Database Migration Specialist
description: Authors and verifies reversible SQL schema migrations safely
phases: [9]
allowed_tools: [read_file, write_file, edit_file, run_command]
required_skills: [tdd-cycle]
---

Follow safe expand-and-contract zero-downtime migrations.
```

Tool mapping behavior in `scripts/compose.py`:
- Canonical `read_file`, `write_file`, `edit_file`, `run_command` are automatically translated to Claude Code tools (`Read, Glob, Grep`, `Write`, `Edit`, `Bash`) in `.claude/agents/db-migrator.md` and Copilot tools (`read`, `search`, `edit`, `terminal`) in `.github/agents/db-migrator.agent.md`.
- Any custom agent whose name contains **`reviewer`** (e.g. `sql-reviewer`) is **forced read-only** in generated Claude/Copilot configs (`tools: Read, Glob, Grep` + `disallowedTools: Write, Edit, Bash` / `["read", "search"]`).

---

### Recipe 4 — Disable Any Unwanted Skills, Agents, Phases, Gates, or Mechanisms
Edit `project.framework.json`:

```json
{
  "disabled": {
    "skills": ["caveman", "seo-audit", "ai-seo"],
    "agents": ["code-reviewer"],
    "phases": [2, 3, 10],
    "gates": ["Gate-02"],
    "mechanisms": ["tdd", "handoffs"]
  }
}
```

Valid keys and behavior ([`core/schemas/framework-config.schema.json`](../core/schemas/framework-config.schema.json)):
- **`disabled.skills`:** Removes listed framework/custom skills from `.agents/skills/`, `.claude/skills/`, and `AGENTS.md`, marking `"enabled": false` in `skills/registry.json`. **Original files remain on disk under `skills/`** so you can re-enable them offline anytime by removing their name and running `python scripts/compose.py`.
- **`disabled.agents`:** Omits listed roles from `AGENTS.md` and prunes generated subagents (`.claude/agents/framework-code-reviewer.md`, `.github/agents/code-reviewer.agent.md`, etc.) while keeping `agents/<role>.md` intact on disk for offline re-enabling and intact `workflows/` links.
- **`disabled.phases` (`1..15`):** Excludes those phases from inline stage runbook bullets and rules (disabling `2`/`3` omits Spec-First bullets; disabling `9` disables TDD rule injection; disabling `10` disables code-reviewer subagent generation).
- **`disabled.gates` (`Gate-01a`, `Gate-01b`, `Gate-02`, `Gate-03`, `Gate-Sec`, `Gate-04`, `Gate-05`):** Omits specified human approval gates from inline gate lists.
- **`disabled.mechanisms` (`"tdd"`, `"handoffs"`, `"graphify"`, `"code-review"`):** Disables core workflow behaviors cleanly (`qualityGates` booleans `requireTddRedGreen: false`, `requireIndependentCodeReview: false`, `requireGraphifyCheck: false` also toggle the matching mechanism if set to `false`).

---

### Recipe 5 — Control Inline Token Budget or Reference Mode
Configure `customizations` inside `project.framework.json`:

```json
"customizations": {
  "overlayDir": ".framework-custom",
  "promptInjectionMode": "inline",
  "inlineMaxBytes": 16384
}
```

- **`overlayDir`:** Relative path inside the consumer repo (default `.framework-custom`). Traversal (`..`), absolute paths, or symlinks fail closed.
- **`promptInjectionMode`:**
  - `"inline"` *(default)*: embeds all non-empty overlay markdown blocks directly into platform entry files.
  - `"reference"`: keeps entry files minimal and lists paths (`Read .framework-custom/...`) instead of inlining content.
- **`inlineMaxBytes` (`1024..65536`):** UTF-8 cap for inline overlay content; if exceeded, appends an explicit truncation note pointing agents to remaining files under `overlayDir`.

---

### Recipe 6 — Add Custom Slash Prompts Across Platforms (`.framework-custom/prompts/*.md`)
Create `.framework-custom/prompts/api-audit.md` (single-segment slug, cannot override built-in `grill-me`, `validate-framework`, or `workflow`):

```markdown
---
description: "Audit API endpoints against OpenAPI and auth rules"
---
Inspect all changed controllers and schemas for missing auth checks or breaking contract changes.
```

Run `python scripts/compose.py`:
- Projects `.github/prompts/api-audit.prompt.md` (**Copilot**), `.claude/commands/api-audit.md` (**Claude Code**), `.gemini/commands/api-audit.toml` (**Gemini CLI**), and indexes `/api-audit` inside `AGENTS.md`.
- Tracked under `"ownership": "consumer_custom_prompt"`; deleting the source file prunes unmodified generated prompts automatically.

---

### Recipe 7 — Configure Custom MCP Servers Across Platforms (`.framework-custom/mcp.json`)
Create `.framework-custom/mcp.json` using standard `"mcpServers"` format (`"disabled": true` skips an entry cleanly; **never** embed literal API keys — always use `${ENV_VAR}` placeholders):

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
      }
    }
  }
}
```

Run `python scripts/compose.py`:
- Generates `.mcp.json` (**Claude Code**), `.vscode/mcp.json` (**GitHub Copilot** `"servers"` schema), `[mcp_servers.*]` blocks inside `.codex/config.toml` (**Codex**), `"mcpServers"` inside `.gemini/settings.json` (**Gemini CLI**), and reference snippet `adapters/antigravity/mcp_config.json` (**Antigravity** manual host import).
- Rejects hardcoded tokens/keys fail-closed (`BootstrapSecurityError`), and deleting `.framework-custom/mcp.json` prunes/reverts generated MCP configs automatically.

---

## 5. Letting Your AI Agent Manage Customizations For You

Because entry files include the self-maintenance rule (`run python scripts/compose.py automatically after editing .framework-custom/ or project.framework.json`), you can customize via natural language in chat:
- *"Add a project rule under `.framework-custom/rules/testing.md` requiring Playwright traces on failure, and apply it."*
- *"Create a custom skill `.framework-custom/skills/api-errors/SKILL.md` documenting our RFC 9457 error envelope and re-compose."*
- *"Disable `caveman` and `tdd` in `project.framework.json` and run `python scripts/compose.py`."*

---

## 6. Security Guards & Known Boundaries

1. **Path & Symlink Fail-Closed Guards:** `bootstrap.py`, `compose.py`, and `validate.py` reject `..` traversal, drive/absolute paths, Windows case-insensitive collisions (e.g., `my-skill` vs `My-Skill`), and symlinks or NTFS reparse points inside `overlayDir` or custom skills/agents.
2. **Untracked Protection:** Never rename/overwrite files outside `.framework-custom/` without understanding `consumer_customized_generated`; direct edits to generated root files are preserved (`skipped_modified`) on `--update` and skip future automatic framework rule updates on those files until reconciled.
3. **Platform Coverage (`v0.4.0`):** Inline composition, schemas, custom prompts/MCP, and native skill projections pass for all **5 platforms** (`84/84` automated checks). See [`adapters/compatibility-matrix.md`](../adapters/compatibility-matrix.md) for per-platform asset layouts and prerequisites.
