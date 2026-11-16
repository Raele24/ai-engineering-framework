# Getting Started with AI Engineering Framework

**Version:** `0.1.0`  

---

## 1. Overview

This guide walks you through using the **AI Engineering Framework** to take a software feature from an initial idea to a tested, reviewed, and validated implementation using any supported AI coding agent (**GitHub Copilot**, **Google Antigravity**, **Claude Code**, **OpenAI Codex**, or **Gemini CLI**).

---

## 2. Prerequisites

- **Git:** `>= 2.30`
- **Python:** `>= 3.10` (used by the zero-dependency `bootstrap.py`, `validate.py`, and `sync_adapters.py` scripts)
- **Optional Recommended Tools:**
  - `graphify` (`pipx install graphifyy`) for codebase knowledge graph generation and architectural queries.
  - `node >= 20` / `npx` for optional Playwright E2E testing and external skill discovery.
  - `gh` (GitHub CLI) for automated GitHub repository, PR, and release operations.

---

## 3. Step-by-Step Walkthrough

### Step 1: Bootstrap Your Project Repository

If you are starting a new project or adding the framework to an existing repository, run `scripts/bootstrap.py`:

```bash
python /path/to/ai-engineering-framework/scripts/bootstrap.py \
  --target /path/to/my-app \
  --platforms antigravity,copilot,claude-code,codex,gemini-cli \
  --optional-packs communication,context-engineering,agent-architecture,frontend-design \
  --profile standard
```

See [`docs/SKILL_INSTALLATION_GUIDE.md`](./SKILL_INSTALLATION_GUIDE.md) and [`docs/TOKEN_OPTIMIZATION.md`](./TOKEN_OPTIMIZATION.md) for configuring optional skill packs (`frontend-design` for UI/UX Pro Max & Angular; `growth-media` for SEO & video) and token optimization tools (`ponytail`, `caveman`, `rtk-cli`).

This creates:
- Canonical rules and workflows in your project (or links to them).
- Platform entry points (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`).
- Project configuration file `project.framework.json`.
- Artifact directories (`docs/specs/`, `docs/adr/`, `docs/plans/`, `.framework-state/`).

### Step 2: Verify the Installation

Run the validation script inside your project (or inside the framework repository):

```bash
python scripts/validate.py
```

Expect `STATUS: PASS` with zero errors.

### Step 3: Start Phase 1 & Phase 2 (Discovery + Grill Me)

Open your repository in your preferred AI coding agent and start with a clear feature prompt invoking the canonical workflow:

```text
Follow docs/WORKFLOW.md starting at Phase 1 & Phase 2 (Grill Me).
Feature request: Add role-based API key authentication with rate limiting.
Produce docs/specs/01-discovery-brief.md and ask me the Phase 2 clarifying questions before writing any code.
```

What happens next:
1. The agent acts as **`product-analyst`** ([`agents/product-analyst.md`](../agents/product-analyst.md)).
2. If `graphify-out/graph.json` exists, it inspects your existing architecture first.
3. It writes `docs/specs/01-discovery-brief.md` and presents 3–5 high-leverage clarifying questions with recommended defaults (**Gate-01a**).

### Step 4: Approve the Specification & Architecture (Phases 3–5)

Once you answer the clarifying questions:
1. The agent generates `docs/specs/03-specification.md` with testable `Given / When / Then` acceptance criteria (`AC-01..N`).
2. Switching to **`software-architect`** ([`agents/software-architect.md`](../agents/software-architect.md)), it documents the technical design and creates an ADR in `docs/adr/ADR-0001-api-key-auth.md`.
3. It pauses at **Gate-02** for your approval.

### Step 5: Execute Task Decomposition & TDD Implementation (Phases 6–9)

After you approve the spec and ADR:
1. **`planner-orchestrator`** breaks the work into atomic tasks in `docs/plans/07-task-backlog.json`.
2. **`implementation-engineer`** executes **Phase 9 (TDD)** using [`skills/core/tdd-cycle/SKILL.md`](../skills/core/tdd-cycle/SKILL.md):
   - Writes failing tests for `AC-01..N` (**RED**).
   - Writes minimal production code to pass (**GREEN**).
   - Refactors and runs linters/typechecks (**REFACTOR**).

### Step 6: Run Code Review, QA, and Security Validation (Phases 10–12)

Instruct your agent (or spawn a fresh subagent context) to run verification:

```text
Execute Phases 10, 11, and 12 of docs/WORKFLOW.md against the current diff.
Write the review, test, and security reports to .framework-state/.
```

1. **`code-reviewer`** checks the diff against `03-specification.md`, `ADR-0001`, and `quality/code-review-rubric.md`.
2. **`qa-engineer`** executes full unit, integration, and regression suites.
3. **`security-engineer`** checks for hardcoded secrets, injection vectors, and dependency vulnerabilities.

### Step 7: Update Graph & Release (Phases 13–15)

1. Run `graphify update .` (if Graphify is installed) and `python scripts/validate.py`.
2. Approve **Gate-04** to commit, tag, and push your release.
