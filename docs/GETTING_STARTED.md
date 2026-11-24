# Getting Started & Consumer Usage (`GETTING_STARTED.md`)

**Version:** `0.6.0`

End-to-end guide for installing **AI Engineering Framework** into a project and operating it day-to-day.

---

## 1. Framework Repo vs. Consumer Repo

| Action | Upstream Framework Repo | Consumer Project (`my-app`) |
| :--- | :--- | :--- |
| **Edit rules, agents, or skills** | Edit `core/`, `agents/`, `skills/` → `python scripts/sync_adapters.py` | Edit `.aief/custom/` → `python .aief/scripts/compose.py` |
| **Validate integrity** | `python scripts/validate.py --mode framework` | `python .aief/scripts/validate.py --mode consumer` |
| **Install or upgrade** | Target a project with `aief init` / `bootstrap.py` | `aief update .` |
| **Run tests** | `python scripts/run_tests.py --fail-on-skip` | Run your app suite (`dotnet test`, `npm test`, `pytest`) |

---

## 2. Prerequisites & Quick Install

- **Git:** `>= 2.30`
- **Python:** `>= 3.11` (stdlib only, zero runtime dependencies)
- **Windows PowerShell `5.1+`:** Scripts avoid Bash `&&` chaining; propagate exit codes with `; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }` and quote paths containing spaces.
- **Supported Platforms:** Google Antigravity, GitHub Copilot, Claude Code, OpenAI Codex, Gemini CLI ([`adapters/compatibility-matrix.md`](../adapters/compatibility-matrix.md)).

Run against a new or existing project (`--dry-run` previews without writing). On an interactive TTY fresh install, `aief init` (and `bootstrap.py`) launches the **discovery & legacy migration TUI wizard** (`↑`/`↓`/`Space`/`a`/`Enter`/`Esc`, with ASCII fallback on non-TTY) to select platforms and optional packs, resolve duplicate legacy entry files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md` via `copy`, `move` to `.aief/custom/rules/`, `skip`, or `delete`), and unify external skills/rules. Pass `--yes` (`-y`) to accept defaults non-interactively, `--no-import` to skip legacy auto-import, or `--interactive` (`-i`) to force wizard prompts. New installs isolate framework runtime assets under `.aief/` (all 5 platforms, all `33` skills, stack auto-detection for `dotnet`, `node-angular`, `python`).

```powershell
# With packaged CLI (`pipx` / `uvx`):
aief init /path/to/my-app
aief init /path/to/my-app --yes --no-import
aief preflight /path/to/my-app --stacks dotnet,node-angular

# Or from a local framework clone:
python /path/to/ai-engineering-framework/scripts/bootstrap.py /path/to/my-app
python /path/to/my-app/.aief/scripts/preflight.py --stacks dotnet,node-angular
```

*(Install flags, `--update` semantics, and Lockfile `v2.0.0` details are in [`docs/INSTALLATION.md`](./INSTALLATION.md). Customization recipes live in [`docs/CUSTOMIZATION_GUIDE.md`](./CUSTOMIZATION_GUIDE.md).)*

---

## 3. Running Features Through the Workflow (Stages 1–6)

1. **Discovery & Grill Me (Phases 1–2):**
   ```text
   Follow AGENTS.md and workflows/01-discovery-and-grill-me.md.
   Feature request: Add role-based API key authentication with rate limiting.
   Produce docs/specs/01-discovery-brief.md and ask me Phase 2 clarifying questions before writing code.
   ```
   If `graphify-out/graph.json` is missing on repos with $\ge 15$ files, Phase 1 builds it with `graphify .` (or notifies you if the CLI is missing; if `graphify` CLI is blocked in a host sandbox, agents read `graphify-out/GRAPH_REPORT.md` / `graphify-out/graph.json` directly). Confirm the batched `(Recommended)` answers at **`Gate-01a`**.
2. **Specification & ADR (Phases 3–5):** Lock `docs/specs/03-specification.md` (`Given / When / Then` criteria `AC-01..N`) at **`Gate-01b`**, and record architecture decisions (`docs/adr/ADR-xxxx-*.md`) at **`Gate-02`**.
3. **Plan & TDD Implementation (Phases 6–9):** Approve `docs/plans/06-implementation-plan.md` (**`Gate-03`**). Implementation runs **RED → GREEN → REFACTOR** ([`skills/core/tdd-cycle/SKILL.md`](../skills/core/tdd-cycle/SKILL.md)). Under the **Subagent-First `HARD GATE`**, tasks touching `>= 3` modified/created files or `>= 2` layers must delegate disjoint layers to specialist subagents rather than implementing all files in a single session.
4. **Review, QA & Security (Phases 10–12):** In a fresh session (or via independent subagent before finishing `>= 3`-file / multi-layer changes), follow [`workflows/05-review-qa-and-security.md`](../workflows/05-review-qa-and-security.md): read-only `code-reviewer` (reporting each subagent's `conversationId` and verdict), project tests + `.aief/scripts/readiness.py` for E2E checks, and `.aief/scripts/validate.py --mode consumer` (**`Gate-Sec`** if active security scans are requested).
5. **Release & Upgrade (Phases 13–15):** Refresh `graphify update .`, run `python .aief/scripts/validate.py --mode consumer`, and pause at **`Gate-04`** before tagging or pushing.

---

## 4. Resuming Work & Handoffs Across Sessions

- **State & Handoffs:** Check `.aief/state/manifest.json` (`current_phase`, `active_gate`, `completed_phases`) and `.aief/state/handoffs/phase-NN-handoff.json` ([`core/schemas/handoff-packet.schema.json`](../core/schemas/handoff-packet.schema.json)).
- **Chat Switches:** Use [`session-handoff`](../skills/optional/context-engineering/session-handoff/SKILL.md) (`.aief/state/session-handoffs/`) when changing conversations mid-task.
- **Ephemeral Logs:** Store temporary outputs under `.aief/state/scratch/` (git-ignored via `.aief/.gitignore`).
- **Stage Runbooks:**
  - Phases 1–5 → `workflows/01-discovery-and-grill-me.md`, `workflows/02-specification-and-adr.md`
  - Phases 6–9 → `workflows/03-planning-and-decomposition.md`, `workflows/04-tdd-and-implementation.md`
  - Phases 10–12 → `workflows/05-review-qa-and-security.md`
  - Phases 13–15 → `workflows/06-release-and-retrospective.md`

### Bounded Dev-Server Readiness (`scripts/readiness.py`)
When verifying frontend UI/E2E on Windows PowerShell `5.1+`, poll readiness instead of fixed sleeps and stop only the child PID:

```powershell
$proc = Start-Process -FilePath "npm.cmd" -ArgumentList "start" -WorkingDirectory "$frontendDir" -PassThru
try {
    python "scripts/readiness.py" --angular-config "$frontendDir\angular.json" --timeout 60 --json
    if ($LASTEXITCODE -ne 0) { throw "Application readiness check failed." }
    # Run browser/E2E checks against the live URL here
} finally {
    if ($proc -and -not $proc.HasExited) { Stop-Process -Id $proc.Id -Force }
}
```
