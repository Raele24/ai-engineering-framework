# Configuration Reference (`CONFIGURATION.md`)

**Version:** `0.6.0`  

---

## 1. Overview

The **AI Engineering Framework** isolates all consumer runtime metadata inside `.aief/` (while remaining backward-compatible with legacy root `project.framework.json` / `.framework-lock.json` / `.framework-state/` installations):
1. **Project Configuration (`.aief/config.json`):** Checked into the consumer repository under `.aief/` (Tier 3). Controls workflow profile, active platform adapters, stack templates, quality gates, `disabled.*` toggles, and `customizations.*`.
2. **Runtime Workflow State (`.aief/state/manifest.json`):** Tracks the active canonical workflow phase (`1..15`), active human approval gate (`Gate-01a`..`Gate-05`), and completed handoff packets (`.aief/state/handoffs/`). Git-ignored by default via `.aief/.gitignore` and never overwritten on updates.
3. **Lockfile Metadata (`.aief/lock.json`, `schema_version: "2.0.0"`):** Deterministic two-phase lockfile tracking `framework_version`, `enabled_platforms`, `optional_packs`, `stacks`, `projection_state` (`status`, `canonical_digest`, `last_successful_projection`, `pending_entries`), `projected_skills` per platform, and per-file `managed_files` ownership/source/SHA-256/platform-owner metadata.

---

## 2. `.aief/config.json` Schema & Options

```json
{
  "$schema": "./core/schemas/framework-config.schema.json",
  "frameworkVersion": "0.6.0",
  "projectName": "my-software-project",
  "workflowProfile": "standard",
  "enabledPlatforms": [
    "antigravity",
    "copilot",
    "claude-code"
  ],
  "stacks": [
    "dotnet",
    "node-angular"
  ],
  "optionalSkillPacks": {
    "communication": ["caveman", "rtk-cli", "i-have-adhd", "humanizer"],
    "contextEngineering": [
      "context-optimization",
      "context-compression",
      "filesystem-context",
      "memory-systems",
      "session-handoff"
    ],
    "agentArchitecture": [],
    "frontendDesign": [
      "ui-ux-pro-max",
      "angular-developer",
      "angular-new-app",
      "web-design-guidelines",
      "canvas-design"
    ],
    "growthMedia": []
  },
  "disabled": {
    "skills": [],
    "agents": [],
    "phases": [],
    "gates": [],
    "mechanisms": []
  },
  "customizations": {
    "overlayDir": ".aief/custom",
    "promptInjectionMode": "inline",
    "inlineMaxBytes": 16384
  },
  "qualityGates": {
    "requireTddRedGreen": true,
    "requireIndependentCodeReview": true,
    "requireGraphifyCheck": true,
    "minimumTestCoveragePercent": 80
  },
  "security": {
    "enforcePreCommitSecretScan": true,
    "allowActiveSecurityTesting": false,
    "strixProfilePath": ".aief/security/strix-profile.yaml"
  },
  "paths": {
    "specsDir": "docs/specs",
    "adrDir": "docs/adr",
    "plansDir": "docs/plans",
    "retrospectivesDir": "docs/retrospectives",
    "stateDir": ".aief/state"
  }
}
```

### 2.1 Configuration Fields Reference

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `frameworkVersion` | `string` | `"0.6.0"` | SemVer version of the installed AI Engineering Framework |
| `projectName` | `string` | Folder name | Identifier used in handoff manifests and reports |
| `workflowProfile` | `"full"` \| `"standard"` \| `"hotfix"` | `"standard"` | Controls ceremony depth in `docs/WORKFLOW.md` |
| `enabledPlatforms` | `string[]` | All 5 platforms | Platforms configured by `scripts/bootstrap.py` and verified by `.aief/scripts/validate.py --mode consumer` |
| `stacks` | `string[]` | `[]` | Stack templates enabled (`"dotnet"`, `"node-angular"`, `"python"`) |
| `optionalSkillPacks.*` | `object` | Pack-dependent | Lists installed optional skills per pack (`communication`, `contextEngineering`, `agentArchitecture`, `frontendDesign`, `growthMedia`) |
| `disabled.skills` | `string[]` | `[]` | Framework or custom skill names excluded from native projections and active indexes (re-enabled cleanly via `aief compose .` from bundle cache) |
| `disabled.agents` | `string[]` | `[]` | Canonical or custom agent roles omitted from `AGENTS.md` and native subagent files |
| `disabled.phases` | `integer[]` | `[]` | Workflow phases (`1..15`) omitted from rendered stage tables and rule bullets |
| `disabled.gates` | `string[]` | `[]` | Human gates (`Gate-01a`..`Gate-05`) excluded from active inline guardrails |
| `disabled.mechanisms` | `string[]` | `[]` | Core mechanisms to disable (`"tdd"`, `"handoffs"`, `"graphify"`, `"code-review"`) |
| `customizations.overlayDir` | `string` | `".aief/custom"` | Project-owned Tier 3 overlay directory containing `instructions.md`, `rules/*.md`, `skills/<name>/SKILL.md`, `agents/<role>[.append].md`, `prompts/*.md`, `mcp.json`, and `imported/*.md` |
| `customizations.promptInjectionMode` | `"inline"` \| `"reference"` | `"inline"` | `"inline"` embeds overlay instructions directly inside entry files across all 5 platforms; `"reference"` links paths only |
| `customizations.inlineMaxBytes` | `integer` | `16384` | UTF-8 byte budget (`1024..65536`) for inline overlay sections before truncating with a pointer to `overlayDir` |
| `qualityGates.requireTddRedGreen` | `boolean` | `true` | Requires failing test creation before implementation in Phase 9 (also acts as mechanism toggle if `false`) |
| `qualityGates.requireIndependentCodeReview` | `boolean` | `true` | Requires Phase 10 review before Phase 13 release (also toggles `code-review` mechanism if `false`) |
| `qualityGates.requireGraphifyCheck` | `boolean` | `true` | Uses `graphify` knowledge graph during architecture and review phases (also toggles `graphify` if `false`) |
| `security.allowActiveSecurityTesting` | `boolean` | `false` | Must remain `false` unless explicit human approval (`Gate-Sec`) and target scope are configured |

---

## 3. Consumer Isolation, Validation Severities & Windows Operations

### 3.1 Consumer Workspace Boundaries & Ownership
`scripts/validate.py --mode consumer` enforces strict boundaries between ownership scopes inside a consumer repository (`v2.0.0` lockfile):
1. **`framework_managed` / `platform_projected_skill`:** Core rules, workflows, registry metadata (`.aief/skills/registry.json`), consumer adapters, and native projections (`.agents/skills/`, `.claude/skills/`) tracked with SHA-256 hashes and active platform owners in `.aief/lock.json`.
2. **`consumer_owned`:** Tier 3 project assets (`.aief/config.json`, `.aief/custom/`, `.aief/state/`, `docs/`, host `skills/`, `.gitignore`, `README.md`, app source) — never overwritten or pruned.
3. **`consumer_custom_skill` / `consumer_custom_agent` / `consumer_custom_prompt` / `consumer_custom_mcp`:** Dynamic custom overlays from `.aief/custom/{skills,agents,prompts,mcp.json}` (requiring no manual registry edits), tracked safely in `.aief/lock.json` and pruned cleanly when removed from the overlay.
4. **`consumer_customized_generated`:** Managed or projected files modified locally by the user (`disk_sha256 != recorded_sha256`) — preserved automatically on `--update` and `compose.py`.
5. **`unknown_untracked`:** Untracked files inside `.agents/skills/` or `.claude/skills/` with no lockfile entry — preserved on `--update` and reported as warnings.
6. **Host-Global External Directories (`INFO` Scope Only):** `~/.agents/skills`, `~/.claude/skills`, `~/.gemini/config/skills`, and `~/.codex/skills` belong to host runtimes, **not** the consumer workspace.

After changing `.aief/config.json` (`disabled.*` / `customizations.*`) or `.aief/custom/`, run `python .aief/scripts/compose.py` (or `aief compose .`) locally inside the consumer repo to re-compose inline entry files, projections, and validation in one step. `.aief/.gitignore` ignores runtime state (`state/`), scratch outputs, and Python bytecode (`__pycache__/`, `*.py[cod]`). Full customization recipes: [`docs/CUSTOMIZATION_GUIDE.md`](./CUSTOMIZATION_GUIDE.md).

### 3.2 Actionable Validation Severity Tiers (`scripts/validate.py`)
`validate.py` prunes heavy build/dependency trees (`node_modules/`, `.git/`, `.angular/`, `dist/`, `.venv/`) during workspace scans and supports JSONC (comments and trailing commas) in root and nested `.vscode/*.json` / `.devcontainer/*.json` monorepo configs (e.g., `apps/web/.vscode/*.json`).
- **`ERROR` (Exits `1`):** Invalid ownership class, unknown/disabled platform ownership metadata, projected skills absent from consumer `skills/registry.json`, missing required skill projections (`SKILL.md`), stale lockfile/platform projection entries, duplicate or case-insensitive skill/path collisions, unsafe paths (`..`, symlinks/reparse points), corrupted or interrupted (`in_progress`) lockfiles, invalid JSON/JSONC, or broken links/secrets.
- **`WARNING` (Exits `0`):** Unexpected untracked files inside `.agents/skills/` or `.claude/skills/` preserved by `--update`, locally modified managed/projected files differing from locked hashes, or legacy `v0.3.0` lockfile migration advisories.
- **`INFO` (Exits `0`):** Observed host-global skill directory visibility outside consumer workspace isolation boundaries.

### 3.3 Windows PowerShell 5.1 Operational Conventions
- Target Windows PowerShell `5.1+` without requiring PowerShell 7: use `; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }` instead of `&&`.
- Double-quote paths containing spaces (`"$workspace\scripts\validate.py"`), specify explicit working directories (`Set-Location` / `-WorkingDirectory`), pass closed stdin (`-`) when piping to headless `codex exec`, and use `python scripts/readiness.py` + PID-scoped `Stop-Process -Id $proc.Id` inside `try/finally` instead of fixed startup sleeps or process-name wildcards.

---

## 4. Environment Variables & Secrets Policy

1. **Zero Secrets in Git:** Never place API keys, OAuth tokens, JWT signing keys, database passwords, or private URLs in `.aief/config.json` (or legacy `project.framework.json`), `appsettings.json`, or any tracked file.
2. **Variable Placeholders:** Always reference secrets via environment variables (`APP_JWT_SIGNING_KEY`, `${GITHUB_PERSONAL_ACCESS_TOKEN}`, `${STRIX_LLM_API_KEY}`).
