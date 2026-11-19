# Consumer Usage Guide — Adopting & Operating in Real Projects (`CONSUMER_USAGE_GUIDE.md`)

**Version:** `0.4.0`  

---

## 1. Framework Repo vs. Consumer Repo (Avoid the #1 Mistake)

The framework intentionally separates **authoring** from **adoption**:

| Action | Upstream Framework Repo (`ai-engineering-framework`) | Your Consumer Project (`my-app`) |
| :--- | :--- | :--- |
| **Update adapters after editing `core/`** | `python scripts/sync_adapters.py` | **Never present / never run** (`use compose.py` for project customizations) |
| **Re-compose inline rules, `.framework-custom/`, and `disabled.*`** | `python scripts/sync_adapters.py` | `python scripts/compose.py` (standalone, offline, instant) |
| **Validate repository integrity** | `python scripts/validate.py --mode framework` | `python scripts/validate.py --mode consumer` |
| **Install or upgrade framework assets** | `python scripts/bootstrap.py --target ...` | N/A (run from the framework repo targeting `my-app`) |
| **Run framework automated regression suite** | `python scripts/run_tests.py --fail-on-skip` | Run **your application's** unit/integration tests (`dotnet test`, `npm test`, `pytest`) |

---

## 2. Installing into an Existing (Brownfield) Repository

### Step A — Choose Your Flags
1. **`--platforms`:** Select only the AI platforms your team actually uses (`antigravity`, `copilot`, `claude-code`, `codex`, `gemini-cli`; omits extra files for unused tools).
2. **`--profile`:**
   - `full`: 15 explicit phases and all individual gates (best for greenfield architecture, DB migrations, auth).
   - `standard` *(default)*: Combines discovery/clarification/spec and pairs spec+plan approval cleanly for everyday features.
   - `hotfix`: Minimal bug spec $\rightarrow$ regression test + fix $\rightarrow$ review/QA/security $\rightarrow$ release.
3. **`--optional-packs`:**
   - Selection example: `communication,context-engineering,agent-architecture` (`21` skills total = `8` core + `13` optional).
   - Minimal core-only (`8` skills): `--optional-packs none`.
   - Frontend / Angular apps: include `frontend-design` (or alias `design-ui`).
   - Full catalog (`33` skills, CLI default): `--optional-packs all`.
4. **`--stacks`:** Pass `dotnet`, `node/angular`, and/or `python` (comma-separated).
   - If your repo **has no `.gitignore`**, `bootstrap.py` creates `.gitignore`.
   - If your repo **already has a `.gitignore`**, `bootstrap.py` **never overwrites it** and writes `.gitignore.framework-recommended` for manual review, plus `docs/ENVIRONMENT_PREFLIGHT.md`.

### Step B — Dry-Run, Bootstrap, Validate
```bash
# 1. Zero-flag install (all 5 platforms, all 33 skills, auto-detected stacks + brownfield import)
python /path/to/ai-engineering-framework/scripts/bootstrap.py /path/to/my-brownfield-app
# (Or via packaged CLI: aief init /path/to/my-brownfield-app)

# 2. Customize inside /path/to/my-brownfield-app/.framework-custom/ or disable features in project.framework.json, then compose + validate in one step:
cd /path/to/my-brownfield-app
python scripts/compose.py
```

---

## 3. What Was Created in Your Project (Ownership & Projections)

1. **Canonical Subset (`framework_managed`):** `core/`, `agents/`, `workflows/`, `quality/`, `security/`, `templates/`, `skills/core/`, `skills/optional/<selected>/`, and `scripts/{compose,validate,preflight,platform_capabilities,readiness}.py`.
2. **Inline Auto-Loaded Entry Files Across All 5 Platforms:** `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.agents/rules/framework-core.md`, `.github/copilot-instructions.md`, and `.github/instructions/framework.instructions.md` automatically embed active framework rules, gates, stages, and `.framework-custom/` instructions inline so agents apply them from turn 1 without manual file reminders.
3. **Native Skill Projections (`platform_projected_skill` / `consumer_custom_skill`):**
   - `.agents/skills/<name>/SKILL.md` is projected whenever `antigravity`, `copilot`, `codex`, or `gemini-cli` is enabled.
   - `.claude/skills/<name>/SKILL.md` is projected whenever `claude-code` is enabled.
   - Authoring-only `UPSTREAM_SKILL.md` and `__pycache__/` are excluded from native projections, and relative links (e.g., `find-skills` $\rightarrow$ `../../../skills/registry.json`) are rewritten cleanly.
4. **Project Customization Overlay (`consumer_owned` — Never Overwritten):** `.framework-custom/` (`instructions.md`, `rules/*.md`, `skills/<name>/SKILL.md`, `agents/<role>.append.md`, `agents/<name>.md`, and auto-imported brownfield files under `imported/`), alongside `project.framework.json`, `.framework-state/manifest.json`, `README.md`, `.gitignore`, `docs/`, and all application source code.
5. **Lockfile `v2.0.0` (`.framework-lock.json`):** Tracks SHA-256 hashes, active `platforms` owning shared directories, custom skill/agent ownership, and `projection_state` (`status: "completed"`).

---

## 4. Day-to-Day Operation Across Sessions

### Starting a Feature or Resuming Work
Keep conversational prompts thin. Rely on disk state:
1. Check `.framework-state/manifest.json` (`current_phase`, `active_gate`, `completed_phases`) and the latest `.framework-state/handoffs/phase-NN-handoff.json`.
2. Direct the agent to the active stage runbook:
   - Discovery/Grill Me/Spec $\rightarrow$ `workflows/01-discovery-and-grill-me.md` + `workflows/02-specification-and-adr.md`
   - Planning/TDD Implementation $\rightarrow$ `workflows/03-planning-and-decomposition.md` + `workflows/04-tdd-and-implementation.md`
   - Review/QA/Security $\rightarrow$ `workflows/05-review-qa-and-security.md`
   - Release/Docs/Retrospective $\rightarrow$ `workflows/06-release-and-retrospective.md`
3. Store temporary tool logs, smoke prompts, or scratch handoffs strictly under `.framework-state/scratch/` so tracked specs and code remain clean.

### Concrete Handoff Example (Phase 3 $\rightarrow$ Software Architect)
Every phase handoff under `.framework-state/handoffs/phase-NN-handoff.json` must match [`core/schemas/handoff-packet.schema.json`](../core/schemas/handoff-packet.schema.json) (`phase_number`, `phase_slug`, `schema_version`, `timestamp_utc`):

```json
{
  "schema_version": "1.0.0",
  "phase_number": 3,
  "phase_slug": "03-specification",
  "status": "completed",
  "timestamp_utc": "2026-11-19T09:00:00Z",
  "producer_role": "product-analyst",
  "next_role": "software-architect",
  "input_artifacts": [
    { "path": "docs/specs/01-discovery-brief.md", "sha256": "<64-hex-sha256>" }
  ],
  "output_artifacts": [
    { "path": "docs/specs/03-specification.md", "sha256": "<64-hex-sha256>" }
  ],
  "decisions_locked": [
    "No new third-party dependencies when stdlib covers requirements"
  ],
  "open_risks": [
    "Frontend serve cold compile requires HTTP readiness polling before browser E2E"
  ],
  "human_approval": {
    "gate_id": "Gate-01b",
    "required": true,
    "approved": true,
    "notes": "Spec approved for architecture review"
  }
}
```

### Bounded Live UI / Dev-Server Readiness (`scripts/readiness.py`)
In Stage 5 E2E checks on Windows PowerShell `5.1+`, derive the URL from project config and poll cleanly without blind sleeps:

```powershell
$proc = Start-Process -FilePath "npm.cmd" -ArgumentList "start" -WorkingDirectory "$frontendDir" -PassThru
try {
    python "scripts/readiness.py" --angular-config "$frontendDir\angular.json" --timeout 60 --json
    if ($LASTEXITCODE -ne 0) { throw "Application readiness check failed." }
    # Execute agent-browser checks against the ready endpoint here
} finally {
    if ($proc -and -not $proc.HasExited) { Stop-Process -Id $proc.Id -Force }
}
```

---

## 5. Customizing, Disabling Features, Updating & Platform Limits

### Customizing Your Project Safely (`.framework-custom/` + `scripts/compose.py`)
See [`docs/CUSTOMIZATION_GUIDE.md`](./CUSTOMIZATION_GUIDE.md) for full copy-paste examples and recipes. In short: never edit `AGENTS.md` or `CLAUDE.md` directly. Instead:
1. Edit `.framework-custom/instructions.md` or add topic files under `.framework-custom/rules/*.md`.
2. Add custom project skills under `.framework-custom/skills/<skill-name>/SKILL.md`.
3. Extend an existing agent (`agents/<role>.append.md`) or add/override an agent (`agents/<name>.md`; roles with `reviewer` remain read-only).
4. Disable unwanted skills, agents, phases, gates, or mechanisms (`"tdd"`, `"handoffs"`, `"graphify"`, `"code-review"`) inside `project.framework.json` (`disabled.*`).
5. Run `python scripts/compose.py` (composes + validates in one command; agents are also instructed to run it automatically after modifying `.framework-custom/` or `project.framework.json`).

### Safe Updates & Migration
```bash
python /path/to/ai-engineering-framework/scripts/bootstrap.py /path/to/my-brownfield-app --update
```
- **Legacy `v0.3.0` consumer?** `bootstrap.py --update` automatically validates `.framework-lock.json`, backs it up to `.framework-state/lock-backups/framework-lock-v0.3.0.json`, preserves customized files, projects `.agents/skills/` / `.claude/skills/`, and upgrades the lockfile to `v2.0.0`.
- **Modified a managed or projected file locally?** `bootstrap.py --update` skips overwriting (`skipped_modified`), preserves your edit, and `validate.py --mode consumer` emits a non-blocking **`WARNING`** (`exit 0`).
- **Removed a pack or platform?** Unmodified deselected skills are pruned automatically, while shared `.agents/skills/` files stay intact until the final owning platform is removed.
- **Added your own untracked file inside `.agents/skills/`?** Preserved on `--update` with a **`WARNING`** (`exit 0`).
- **`INFO` notices on `~/.agents/skills`, `~/.claude/skills`, `~/.gemini/config/skills`, `~/.codex/skills`:** Host runtimes may discover global user-profile skills outside workspace isolation. `validate.py` reports their presence read-only and never edits host-global files.

### Practical Platform Verification Summary (`v0.4.0`)
- **All 5 Platforms (`CONTRACT_VALIDATED`):** Inline entry files, adapters, native skill projections (`.agents/skills/`, `.claude/skills/`), and schemas pass `84/84` automated offline checks.
- **Google Antigravity IDE & CLI (`agy`):** **`RUNTIME_VERIFIED`** reference environment (`--model gemini-4-hydrogen-low` recommended; verified end-to-end including brownfield custom skills and rules).
- **Codex CLI:** **`PARTIAL_RUNTIME_VERIFIED`** (`AGENTS.md` + `.agents/skills/` scan verified; requires piped `-` stdin in Windows PowerShell non-TTY calls and external Windows OS sandbox config for disk writes).
- **Claude Code / Copilot / Gemini CLI:** Complete workspace adapters & skills ready on disk (`CONTRACT_VALIDATED`); live host CLI runs were simply not executed on the maintainer machine because they require an authenticated user account/extension on that host (capability token `BLOCKED_EXTERNAL` refers strictly to host auth prerequisites, not framework readiness).
