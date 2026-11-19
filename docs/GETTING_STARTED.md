# Getting Started with AI Engineering Framework (`GETTING_STARTED.md`)

**Version:** `0.4.0`  

---

## 1. Overview

This guide shows how to adopt the **AI Engineering Framework** in a **new or existing (brownfield) software project** and execute a feature from initial clarification through code review, testing, security checks, and release.

> [!NOTE]
> **Two Distinct Workflows:**
> - **Framework Authoring (`ai-engineering-framework` repo):** Run `scripts/sync_adapters.py`, `scripts/validate.py --mode framework`, and `scripts/run_tests.py --fail-on-skip`.
> - **Consumer Adoption (Your Project Repo):** Run `scripts/bootstrap.py <project-path>` from the framework repo into your project. Day-to-day operations live in [`docs/CONSUMER_USAGE_GUIDE.md`](./CONSUMER_USAGE_GUIDE.md); project customizations and disabling toggles live in [`docs/CUSTOMIZATION_GUIDE.md`](./CUSTOMIZATION_GUIDE.md).

---

## 2. Prerequisites & Verified Platform Reality

- **Git:** `>= 2.30`
- **Python:** `>= 3.11` (all framework scripts run exclusively on Python's standard library — zero external `pip` dependencies)
- **Windows Shell Convention:** Framework scripts target stock Windows PowerShell `5.1+`. Avoid Bash-only `&&` chaining; propagate exit codes explicitly with `; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }` and quote paths containing spaces.
- **Verified Platform Support Tiers (see [`adapters/compatibility-matrix.md`](../adapters/compatibility-matrix.md)):**
  - **Google Antigravity IDE & CLI (`agy`):** `RUNTIME_VERIFIED` (reference runtime).
  - **OpenAI Codex CLI:** `PARTIAL_RUNTIME_VERIFIED` (`AGENTS.md` + native `.agents/skills/` verified; Windows sandbox blocks `exec_command` disk I/O unless configured externally).
  - **Claude Code / GitHub Copilot / Gemini CLI:** `CONTRACT_VALIDATED` + `BLOCKED_EXTERNAL` (schemas, native skills, and consumer adapters aligned; live CLI runs remain blocked on host install/account eligibility).
- **Optional Tools:** `graphify` (`0.9+`), Node.js `20+`, .NET SDK `8.0+/10.0 LTS`, `gh` CLI.

---

## 3. Step-by-Step Walkthrough

### Step 1: Bootstrap Your Project Repository

Run `scripts/bootstrap.py` against a new folder or an **existing repository**:

```powershell
# Preview changes safely first (--dry-run writes nothing to disk)
python /path/to/ai-engineering-framework/scripts/bootstrap.py /path/to/my-app --dry-run

# Install (enables all 5 platforms, all 33 skills, auto-detects stacks, imports legacy root rules)
python /path/to/ai-engineering-framework/scripts/bootstrap.py /path/to/my-app
# Or with packaged CLI: aief init /path/to/my-app
```

**Important CLI Defaults & Non-Destructive Behavior (`scripts/bootstrap.py`):**
- Omitting flags enables all `5` platforms, `standard` profile, `all` (`33`) skills, and automatic stack detection (`dotnet`, `node-angular`, `python`). Use `--optional-packs` or `disabled.*` in `project.framework.json` to trim or turn off specific items.
- **Canonical Skills vs. Native Skill Projections:** Installed skills live under `skills/core/` + `skills/optional/<pack>/` (preserving `UPSTREAM_SKILL.md` attribution) and are automatically projected into `.agents/skills/<name>/` (Antigravity, Copilot, Codex, Gemini CLI) and `.claude/skills/<name>/` (`claude-code`), with relative Markdown links rewritten cleanly.
- **Brownfield Protection & Auto-Import:** Existing `README.md`, `docs/`, `.framework-custom/`, and `.framework-state/` files are **never overwritten**. If your repository already has non-framework root instructions (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`), `bootstrap.py` archives them under `.framework-custom/imported/` and injects them inline automatically across all enabled platforms. Existing `.gitignore` files stay intact with `.gitignore.framework-recommended` generated beside them.
- **Ownership Lockfile:** `.framework-lock.json` (`schema_version: "2.0.0"`) records SHA-256 hashes and platform owners so `--update` safely upgrades unmodified framework files while preserving your customizations.

### Step 2: Customize (Optional) & Verify Environment

Inside your bootstrapped project root:
- Add project rules/skills/agents inside `.framework-custom/` or disable features inside `project.framework.json` (`disabled.*`), then compose + validate in one step (see [`docs/CUSTOMIZATION_GUIDE.md`](./CUSTOMIZATION_GUIDE.md)):

```powershell
python scripts/compose.py
python scripts/preflight.py --stacks dotnet,node-angular
```

*(Note the stack spelling difference: `bootstrap.py --stacks` accepts `node/angular` and normalizes it, whereas `preflight.py --stacks` and `project.framework.json` use `node-angular`.)*

Expect `OVERALL STATUS: PASS (0 total error(s), ...)` (exit code `0`). Informational (`INFO`) lines may note host-global folders such as `~/.agents/skills/` or `~/.gemini/config/skills/` outside framework workspace control; those never fail validation and host files are never modified.

### Step 3: Start Phase 1 & Phase 2 (Discovery + Grill Me)

Open your project in your AI coding agent and start a bounded feature request:

```text
Follow AGENTS.md and workflows/01-discovery-and-grill-me.md.
Feature request: Add role-based API key authentication with rate limiting.
Produce docs/specs/01-discovery-brief.md and ask me Phase 2 clarifying questions before writing any code.
```

What happens next:
1. If `graphify-out/graph.json` exists ($\ge 15$ files), the agent acts as **`product-analyst`** ([`agents/product-analyst.md`](../agents/product-analyst.md)) and queries the existing architecture first.
2. It writes `docs/specs/01-discovery-brief.md` and asks 3–5 categorized clarifying questions with `(Recommended)` defaults (**`Gate-01a`**).

### Step 4: Approve Specification & Architecture (`Gate-01b` / `Gate-02`)

1. Once you confirm answers, **`product-analyst`** generates `docs/specs/03-specification.md` with deterministic `Given / When / Then` criteria (`AC-01..N`) and pauses at **`Gate-01b`**.
2. **`software-architect`** ([`agents/software-architect.md`](../agents/software-architect.md)) evaluates options and records architectural decisions in `docs/adr/ADR-xxxx-<slug>.md`, pausing at **`Gate-02`**.
*(With `workflowProfile: "standard"`, Phases 1–3 and Spec/Plan approvals combine cleanly; use `"hotfix"` for isolated bug fixes.)*

### Step 5: Task Decomposition & TDD Implementation (Phases 6–9)

1. **`planner-orchestrator`** creates `docs/plans/06-implementation-plan.md` (**`Gate-03`**) and `docs/plans/07-task-backlog.json`, writing validated JSON handoffs conforming to [`core/schemas/handoff-packet.schema.json`](../core/schemas/handoff-packet.schema.json) (`phase_number`, `phase_slug`, `schema_version`, `timestamp_utc`, artifacts, and locked decisions) into `.framework-state/handoffs/`.
2. **`implementation-engineer`** loads [`skills/core/tdd-cycle/SKILL.md`](../skills/core/tdd-cycle/SKILL.md) (and [`skills/core/ponytail/SKILL.md`](../skills/core/ponytail/SKILL.md)) and implements tests before production code (**RED $\rightarrow$ GREEN $\rightarrow$ REFACTOR**).

### Step 6: Code Review, QA, Readiness & Security (Phases 10–12)

Use [`workflows/05-review-qa-and-security.md`](../workflows/05-review-qa-and-security.md) in a fresh session/subagent:

1. **`code-reviewer`** audits the Git diff against `docs/specs/03-specification.md`, ADRs, and [`quality/code-review-rubric.md`](../quality/code-review-rubric.md).
2. **`qa-engineer`** runs your project's unit/integration suites. For live UI/E2E verification, start only a workflow-owned dev server, wait via `python scripts/readiness.py --angular-config path/to/angular.json` (or `--url ...`), run [`skills/core/agent-browser/SKILL.md`](../skills/core/agent-browser/SKILL.md), and stop only that child PID.
3. **`security-engineer`** checks secrets (`validate.py --mode consumer`) and dependencies. Active dynamic scanners (Strix) require **`Gate-Sec`** approval; unavailable tools are logged explicitly as `NOT_RUN` or `BLOCKED` (never `PASS`).

### Step 7: Update Non-Destructively & Release (Phases 13–15)

1. Refresh `graphify update .` (if installed) and run `python scripts/validate.py --mode consumer`.
2. Pause at **`Gate-04`** before tagging, pushing, or publishing a release.
3. Whenever the framework updates (`0.3.x` $\rightarrow$ `0.4.0`), upgrade your consumer repo safely:
   ```powershell
   python /path/to/ai-engineering-framework/scripts/bootstrap.py /path/to/my-app --update
   python /path/to/my-app/scripts/validate.py --mode consumer
   # Or with packaged CLI: aief update /path/to/my-app
   ```
   Unmodified framework files and native skill projections update atomically, `.framework-custom/` + `disabled.*` are preserved and re-composed automatically, and any manual edits to generated files (`WARNING`) remain untouched.
