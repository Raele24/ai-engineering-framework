# Skills, Token Optimization & Context Engineering Research Report

**Project:** AI Engineering Framework (`ai-engineering-framework`)  
**Repository:** `D:\PROGETTI\ai-engineering-framework`  
**Date:** 2026-11-16  
**Author Role:** Senior AI Agent Architect, Context Engineer & Developer Tools Researcher  

---

## 1. Executive Summary & Selection Philosophy

This report documents targeted upstream research across **6 capability categories** (32 candidate skills, libraries, and CLI tools) to expand the **AI Engineering Framework** without introducing context bloat, duplicate design systems, or vendor lock-in.

### Core Selection Criteria Applied
1. **Upstream Provenance & License Verification:** Every selected capability traces to a verified upstream repository with a permissive open-source license (`MIT` or `Apache-2.0`).
2. **Progressive Context Disclosure:** Only compact frontmatter metadata (~40–60 tokens per skill) is indexed at session start. Full `SKILL.md` instructions load on-demand only when the active workflow phase or user task requires them; heavy reference tables (`.csv`, `references/*.md`) remain on disk and are queried via offline standard-library scripts (`search.py`, `graphify query`).
3. **Zero Redundant Systems:** Where multiple candidates overlap (e.g., `RTK` vs. `Headroom`; `ui-ux-pro-max` vs. `design`/`ui-styling`; 13 skills in `Agent-Skills-for-Context-Engineering`), we select the highest-signal, lowest-overhead primitive and reject or consolidate overlapping candidates.
4. **Installation Policy Enforcement:**
   - **Policy A (Repository-Local):** Pure `SKILL.md`, offline reference files, and zero-dependency Python stdlib scripts integrated directly into `skills/` and `integrations/`.
   - **Policy B (Requires User Approval):** External system binaries (`rtk-ai.rtk`), global IDE hooks, or MCP daemons. Documented with exact Windows PowerShell commands and never auto-installed.
   - **Policy C (Documentation-Only):** Overlapping, high-overhead, or narrow-scope tools documented for architectural awareness but excluded from repository installation.

---

## 2. Category A — Token Optimization

### 2.1 Ponytail (`DietrichGebert/ponytail`)
- **Upstream Repository:** `https://github.com/DietrichGebert/ponytail`
- **Maintainer:** Dietrich Gebert (`DietrichGebert`), active 2026 maintenance.
- **License:** MIT License (full redistribution and adaptation permitted with copyright notice).
- **Type:** Agent Skill (`skills/ponytail/SKILL.md`) + Ruleset (`AGENTS.md`).
- **Mechanism:** Enforces a deterministic 7-rung **YAGNI Decision Ladder** before an agent writes any code:
  1. *Does this need to exist?* $\rightarrow$ No: skip it (YAGNI).
  2. *Already in this codebase?* $\rightarrow$ Reuse existing functions/modules.
  3. *Stdlib does it?* $\rightarrow$ Use standard library primitives.
  4. *Native platform feature?* $\rightarrow$ Use native language/runtime features.
  5. *Installed dependency?* $\rightarrow$ Use packages already in lockfile.
  6. *One line?* $\rightarrow$ Prefer direct one-line expressions over wrapper classes.
  7. *Only then:* Write the strict minimum code that satisfies the test.
- **Safety Invariants:** Explicitly forbids cutting security validation, authentication/authorization checks, error handling at trust boundaries, or accessibility attributes.
- **Token & Code Impact:** Prevents speculative boilerplate (abstract factory wrappers, unused config layers), reducing generated diff sizes by 25–45% and lowering downstream review/test token costs.
- **Framework Decision:** **SELECTED (P0 — Policy A: Repository-Local)**. Integrated at `skills/core/ponytail/SKILL.md` and wired into `implementation-engineer`, `software-architect`, and `code-reviewer`.

### 2.2 Caveman (`JuliusBrussee/caveman`)
- **Upstream Repository:** `https://github.com/JuliusBrussee/caveman`
- **Maintainer:** Julius Brussee (`JuliusBrussee`), active 2026 maintenance.
- **License:** MIT License.
- **Type:** Agent Skill (`SKILL.md`) + optional Claude/Gemini plugin wrapper.
- **Mechanism:** Compresses agent conversational output by 65–75% using an answer-first pattern (`[thing] [action] [reason]. [next step].`), dropping pleasantries, hedging, and filler while keeping code blocks, commands, file paths, version numbers, and negations (`not`, `never`, `only`, `except`) 100% verbatim. Automatically reverts to full prose for security warnings, irreversible action confirmations, user multi-choice questions, and persisted files (`docs/`, commits, code comments, PRs).
- **Host Status:** Verified installed on host (`C:\Users\raele\.gemini\config\skills\caveman\SKILL.md`, `4,678` bytes).
- **Framework Decision:** **SELECTED & UPGRADED (P0 — Policy A: Repository-Local)**. Vendored with full upstream `JuliusBrussee/caveman` attribution at `skills/optional/communication/caveman/SKILL.md` (preserving exact upstream copy in `UPSTREAM_SKILL.md`).

### 2.3 RTK — Rust Token Killer (`rtk-ai/rtk`)
- **Upstream Repository:** `https://github.com/rtk-ai/rtk`
- **Maintainer:** RTK AI (`rtk-ai`), active 2026 maintenance (`v1.2.0` verified in WinGet catalog).
- **License:** Apache License 2.0.
- **Type:** External single-binary Rust CLI proxy (`rtk.exe`) + Agent Hook integration (`rtk init`, `rtk gain`).
- **Mechanism:** Intercepts shell commands executed by coding agents (`git status`, `git diff`, `git log`, `pytest`, `npm`, `pnpm`, `cargo`, `docker`) and strips repetitive progress bars, passing-test noise, and boilerplate headers, reducing terminal observation tokens by **60% to 90%** with `<10ms` execution overhead while preserving stack traces, failing assertions, and exit codes.
- **Windows Installation & Crate Collision Warning:**
  - Verified available in Windows Package Manager: `winget install -e --id rtk-ai.rtk` (`v1.2.0`).
  - **Security/Collision Note:** Running plain `cargo install rtk` installs an unrelated crate (*Rust Type Kit*). Source builds must use `cargo install --git https://github.com/rtk-ai/rtk --branch master rtk`.
- **Safe Fallback Behavior:** If `rtk` is not installed on a machine, agents and scripts must fall back cleanly to native shell commands (`git status -sb`, `pytest -q --tb=short`) without failing.
- **Framework Decision:** **SELECTED (P0 — Policy A for repo wrapper `skills/optional/communication/rtk-cli/SKILL.md` & `integrations/rtk/README.md`; Policy B requiring user approval before running `winget install -e --id rtk-ai.rtk`)**.

### 2.4 Headroom (`headroomlabs-ai/headroom`)
- **Upstream Repository:** `https://github.com/headroomlabs-ai/headroom`
- **Maintainer:** Headroom Labs AI (`headroomlabs-ai`).
- **License:** Apache License 2.0.
- **Type:** Local HTTP reverse proxy (`headroom proxy --port 8787`), CLI wrapper (`headroom wrap`), Python library (`headroom-ai`), and MCP server.
- **Evaluation vs. RTK + Context Skills:**
  1. **Architecture Friction:** Headroom intercepts LLM API calls by overriding `ANTHROPIC_BASE_URL` / `OPENAI_BASE_URL` to `http://localhost:8787`. Native IDE agents with built-in OAuth (Google Antigravity, GitHub Copilot) do not route traffic through custom localhost OpenAI/Anthropic proxy URLs.
  2. **Dependency Footprint:** `pip install "headroom-ai[all]"` pulls a heavy Python dependency stack, violating our zero-dependency core principle.
  3. **Capability Overlap:** Terminal command compression is already solved faster (<10ms in Rust) by **RTK**, while JSON/log offloading and observation masking are solved natively by **`filesystem-context`** and **`context-optimization`**.
- **Framework Decision:** **REJECTED FOR INSTALLATION / DOCUMENTED ONLY (Policy C)**. Documented in `docs/TOKEN_OPTIMIZATION.md` for teams building custom standalone LangGraph/LiteLLM pipelines, but not installed in the framework.

---

## 3. Category B — Context Engineering (`muratcankoylan/Agent-Skills-for-Context-Engineering`)

- **Upstream Repository:** `https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering`
- **Maintainer:** Muratcan Koylan (`muratcankoylan`) & Contributors (`v2.1.0`, updated 2026).
- **License:** MIT License.
- **Host Verification:** 12 skills from this collection are present on the local host (`C:\Users\raele\.gemini\config\skills\`), allowing empirical byte/token measurement and code inspection of bundled Python scripts and references.

### 3.1 Granular Evaluation of All 13 Skills in the Collection

| Skill Name | Host Size (`SKILL.md` / Total) | Evaluation & Relationship to Framework | Decision | Priority & Target Location |
| :--- | :--- | :--- | :--- | :--- |
| **`context-optimization`** | `15.9 KB` / `45.8 KB` | Provides operational rules for KV-cache prefix ordering, observation masking (60–80% reduction after 3+ turns), 70% utilization compaction triggers, and context partitioning. | **SELECTED** | **P0** — `skills/optional/context-engineering/context-optimization/` |
| **`context-compression`** | `18.5 KB` / `60.5 KB` | Defines Anchored Iterative Summarization, artifact-trail integrity tracking, and probe-based recall evaluation (`compression_evaluator.py`). Complements `.framework-state/handoffs/`. | **SELECTED** | **P0** — `skills/optional/context-engineering/context-compression/` |
| **`filesystem-context`** | `16.2 KB` / `50.5 KB` | Defines tool-output offloading (`>2,000` chars written to scratch files with 200-token summary), plan persistence, and file-backed subagent workspaces. Harmonized with `core/rules/context-handoff-protocol.md`. | **SELECTED** | **P1** — `skills/optional/context-engineering/filesystem-context/` |
| **`memory-systems`** | `16.8 KB` / `57.4 KB` | Covers cross-session entity tracking, temporal validity windows, and file/graph memory consolidation (`memory_store.py`). | **SELECTED** | **P1** — `skills/optional/context-engineering/memory-systems/` |
| **`multi-agent-patterns`** | `18.9 KB` / `53.4 KB` | Evaluates Supervisor, Swarm, and Hierarchical topologies; establishes the 3–5 worker cap, `forward_message` bypass, and anti-sycophancy debate protocols. Enhances `planner-orchestrator`. | **SELECTED (Cat D)** | **P1** — `skills/optional/agent-architecture/multi-agent-patterns/` |
| **`tool-design`** | `20.4 KB` / `58.0 KB` | Covers tool description routing, architectural reduction (Vercel d0 pattern), actionable error recovery messages, and MCP schema design. Enhances `software-architect` & `implementation-engineer`. | **SELECTED (Cat D)** | **P1** — `skills/optional/agent-architecture/tool-design/` |
| **`evaluation`** | `17.1 KB` / `49.7 KB` | Covers deterministic checks, multi-dimensional rubrics, regression suites, and production quality gates. Enhances `qa-engineer` & `code-reviewer`. | **SELECTED (Cat D)** | **P1** — `skills/optional/agent-architecture/evaluation/` |
| **`self-improvement-loops`** | `22.5 KB` / `36.3 KB` | Governs recursive self-improvement (RSI), failure mining, bounded scaffold edits, and metric-gaming prevention. Directly powers **Phase 15 (Retrospectives)** under `Gate-05`. | **SELECTED (Cat D)** | **P1** — `skills/optional/agent-architecture/self-improvement-loops/` |
| **`context-fundamentals`** | `17.2 KB` / `44.4 KB` | Explains transformer attention curves and context anatomy conceptually. Its operational takeaways are already enforced in `context-optimization`. Loading 17.2 KB of theory into active coding sessions wastes tokens. | **REJECTED (Consolidated)** | Covered by `context-optimization` & `docs/ARCHITECTURE.md` |
| **`context-degradation`** | `19.4 KB` / `52.8 KB` | Diagnostic taxonomy for lost-in-middle and context poisoning. Its actionable mitigations (masking, compaction, partitioning) already live in `context-optimization`. | **REJECTED (Consolidated)** | Consolidated into `context-optimization` |
| **`project-development`** | `19.3 KB` / `76.9 KB` | Covers `acquire -> prepare -> process -> parse -> render` batch LLM pipelines and architectural reduction. Architectural reduction is already in `core/rules/engineering-principles.md` and `ponytail`. | **REJECTED (Duplicate)** | Covered by `docs/WORKFLOW.md` & `ponytail` |
| **`hosted-agents`** | `18.0 KB` / `58.7 KB` | Covers building cloud sandbox infrastructure (Modal warm pools, remote VM snapshots). Too narrow for general application repositories. | **REJECTED (Policy C)** | Documented in research report only |
| **`advanced-evaluation`** | Not on host (~18 KB upstream) | Focuses on LLM-as-a-Judge pairwise swap/position-bias mitigation. Overlaps with `evaluation`. | **REJECTED (Consolidated)** | Key rubric rules covered by `evaluation` |

### 3.2 Conflict Prevention with `core/rules/context-handoff-protocol.md`
Upstream `filesystem-context` uses `scratch/` and `workspace/agents/` as example directories. In our framework adaptation note in `skills/optional/context-engineering/filesystem-context/SKILL.md`, we explicitly bind state persistence to `.framework-state/handoffs/phase-<NN>-handoff.json` and `.framework-state/scratch/` so all skills obey **ADR-0003** without path conflicts.

---

## 4. Category C — UI/UX and Design Intelligence

| Candidate Skill | Upstream Source | License | Host Size | Evaluation & Duplication Analysis | Decision |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`ui-ux-pro-max`** | `https://github.com/nextlevelbuilder/ui-ux-pro-max-skill` | MIT | `22.1 KB` `SKILL.md` (`2.03 MB` total with 28 CSVs & 3 Python stdlib scripts) | **Gold-standard offline design intelligence engine.** Uses zero-dependency Python 3 BM25 search (`scripts/search.py`) across 67 UI styles, 161 color palettes, 57 font pairings, 99 UX guidelines, 25 chart types, and **22 stack guides (including `data/stacks/angular.csv`, `react.csv`, `nextjs.csv`, `shadcn.csv`, `html-tailwind.csv`)**. Generates `design-system/MASTER.md` + page overrides. | **SELECTED (P0 — Policy A)** at `skills/optional/frontend-design/ui-ux-pro-max/` |
| **`angular-developer`** | `https://github.com/angular/skills` (Google Angular Team) | MIT | `9.7 KB` `SKILL.md` (`139.1 KB` across 36 reference files) | Official Google Angular skill covering Angular v20/v21+ standalone components, `signal`, `computed`, `linkedSignal`, `resource`, Signal Forms, Reactive Forms, hierarchical DI, SSR/hydration, ARIA (`angular-aria.md`), Tailwind CSS, and component test harnesses. | **SELECTED (P1 — Policy A)** at `skills/optional/frontend-design/angular-developer/` |
| **`angular-new-app`** | `https://github.com/angular/skills` (Google Angular Team) | MIT | `4.4 KB` (`1` file) | Official Angular CLI workspace initialization protocol (`ng new` flags, zoneless/signals defaults, SSR setup). Lightweight and non-overlapping. | **SELECTED (P1 — Policy A)** at `skills/optional/frontend-design/angular-new-app/` |
| **`web-design-guidelines`** | First-party / Vercel Web Interface Guidelines pattern | Apache-2.0 | `1.9 KB` | Concise WCAG 2.1 AA accessibility, keyboard focus, responsive breakpoints (`320px`–`1440px`), and 5-state UI (`default`, `hover/focus`, `loading`, `empty`, `error`) checklist. | **RETAINED (P1 — Policy A)** at `skills/optional/frontend-design/web-design-guidelines/` |
| **`canvas-design`** | First-party 3-Layer Token Spec | Apache-2.0 | `1.3 KB` | Defines the 3-layer CSS token hierarchy (`primitive -> semantic -> component`). Complements `ui-ux-pro-max` output tokens. | **RETAINED (P1 — Policy A)** at `skills/optional/frontend-design/canvas-design/` |
| **`design`** (`claudekit`) | ClaudeKit community skill pack | MIT | `241.9 KB` (35 files) | Focuses on AI logo generation (55 styles), corporate identity deliverables (50 mockups), and social media graphics. **Duplicates** `ui-ux-pro-max` for UI tokens while adding non-software graphic design bloat. | **REJECTED (Duplicate / Off-Scope)** |
| **`design-system`** (`claudekit`) | ClaudeKit community skill pack | MIT | `179.0 KB` (27 files) | Duplicates `canvas-design` (3-layer tokens) and `ui-ux-pro-max` (`--design-system` generator). | **REJECTED (Duplicate)** |
| **`ui-styling`** (`claudekit`) | ClaudeKit community skill pack | MIT | `170.9 KB` (16 files) | Covers shadcn/ui + Tailwind CSS, which are already covered inside `ui-ux-pro-max/data/stacks/shadcn.csv` and `html-tailwind.csv`. | **REJECTED (Duplicate)** |
| **`banner-design`** & **`slides`** | Community creative packs | MIT | `13.3 KB` & `19.3 KB` | Social media ad banners and HTML slide decks. Not core software interface engineering. | **REJECTED (Off-Scope)** |

---

## 5. Category D — Agent Architecture Enhancement Mapping

Rather than adding new agent roles (which would violate our 8-role anti-sprawl cap), the selected Category B & D skills upgrade the existing **8 canonical agent roles**:

| Canonical Role (`agents/*.md`) | Newly Integrated Skills Mapped | Capability Gained |
| :--- | :--- | :--- |
| **`product-analyst`** | `grill-me`, `anti-slop`, `context-compression` | Structured ambiguity resolution + high-fidelity requirement summarization |
| **`software-architect`** | `adr-writer`, `graphify`, `ponytail`, `tool-design`, `context-optimization` | Knowledge-graph impact analysis, YAGNI architectural reduction, and MCP/tool contract design |
| **`planner-orchestrator`** | `multi-agent-patterns`, `filesystem-context`, `memory-systems`, `self-improvement-loops`, `find-skills` | 3–5 worker cap enforcement, file-backed state handoffs, cross-session memory, and bounded Phase 15 retrospectives |
| **`implementation-engineer`** | `tdd-cycle`, `ponytail`, `ui-ux-pro-max`, `angular-developer`, `angular-new-app`, `web-design-guidelines`, `canvas-design` | YAGNI minimal code generation, BM25 design-system synthesis, and modern Angular/UI implementation |
| **`code-reviewer`** | `ponytail`, `graphify`, `evaluation`, `anti-slop` | Over-engineering detection, AST dependency drift verification, and rubric-based review |
| **`qa-engineer`** | `tdd-cycle`, `agent-browser`, `evaluation` | Deterministic test rubrics, probe-based validation, and browser E2E verification |
| **`security-engineer`** | `anti-slop`, `tool-design` | Safe tool boundary validation, external skill quarantine auditing, and `Gate-Sec` enforcement |
| **`devops-release-engineer`** | `rtk-cli`, `context-optimization`, `anti-slop` | Compressed CI/CLI output inspection and adapter sync verification |

*(Note: `prompt-master` (`235.1 KB`) and `humanizer` (`61.1 KB`) were evaluated and **rejected**: `prompt-master` targets external Midjourney/video prompt crafting, and `humanizer` duplicates our lightweight `anti-slop` (`2.1 KB`) skill at 29x the token cost.)*

---

## 6. Category E — Graphify and Codebase Intelligence (`Graphify-Labs/graphify`)

- **Upstream Repository:** `https://github.com/Graphify-Labs/graphify` (PyPI package: `graphifyy`)
- **Verified Host Version:** `graphify 0.9.48` (`graphifyy 0.9.48`), licensed under **Apache-2.0**.
- **Dependencies (Already Installed in Host Python 3.13):** `networkx`, `numpy`, `rapidfuzz`, `tree-sitter` + 26 language grammars (`python`, `typescript`, `javascript`, `c-sharp`, `rust`, `go`, `java`, `sql`/PostgreSQL schema support, `bash`, `powershell`, etc.).
- **Verified Native Platform Installers in `graphify 0.9.48`:**
  - Google Antigravity: `graphify antigravity install`
  - GitHub Copilot / VS Code: `graphify copilot install` & `graphify vscode install`
  - Claude Code: `graphify claude install`
  - OpenAI Codex: `graphify codex install`
  - Gemini CLI: `graphify gemini install`
  - Git Hooks: `graphify hook install` (auto-updates AST graph on `post-commit` / `post-checkout` with zero LLM API calls).
- **Corpus Size Threshold Guard (Preventing Unnecessary Graphs on Tiny Projects):**
  - Graphify should **only** be initialized/updated when a repository contains **$\ge 15$ tracked code/doc files OR $> 2,000$ lines of code**. Below this threshold, reading files directly uses fewer tokens than loading graph metadata.
- **Framework Decision:** **SELECTED (P0 — Policy A)** at `skills/core/graphify/SKILL.md` (with `UPSTREAM_SKILL.md` preserved) and integrated into `integrations/graphify/README.md`.

---

## 7. Category F — SEO, Growth, Brand, and Video Skills (P2 Optional Pack)

All Category F skills are strictly isolated under `skills/optional/growth-media/` with `default_enabled: false` so they **never** activate during backend, CLI, database, or infrastructure engineering tasks:

| Skill Name | Upstream Source | License | Purpose & Activation Condition | Decision |
| :--- | :--- | :--- | :--- | :--- |
| **`seo-audit`** | `https://github.com/coreyhaines31/marketingskills` (`skills/seo-audit`) | MIT | Technical & on-page SEO audit (crawlability, canonicals, JSON-LD, Core Web Vitals). Activates only on public web/docs portals. | **SELECTED (P2 — Policy A)** |
| **`ai-seo`** | `https://github.com/coreyhaines31/marketingskills` (`skills/ai-seo`) | MIT | Generative Engine Optimization (`llms.txt`, answer-engine chunking, citation structure). Activates only on public docs/marketing pages. | **SELECTED (P2 — Policy A)** |
| **`content-strategy`** | `https://github.com/coreyhaines31/marketingskills` (`skills/content-strategy`) | MIT | Diátaxis documentation taxonomy and developer content positioning. | **SELECTED (P2 — Policy A)** |
| **`pricing`** | `https://github.com/coreyhaines31/marketingskills` (`skills/pricing`) | MIT | LLM token/compute COGS unit economics, gross margin calculation, and SaaS tier packaging. | **SELECTED (P2 — Policy A)** |
| **`brand-strategy`** | Adapted from `claudekit/brand` & `coreyhaines31/marketingskills` | MIT | Brand voice consistency, messaging hierarchy, and visual identity tokens (`references/`). | **SELECTED (P2 — Policy A)** |
| **`video-lens`** | `https://github.com/kar2phi/video-lens` | MIT | Multimodal video/bug-replay & YouTube transcript analysis into timestamped HTML/Markdown reports. | **SELECTED (P2 — Policy A)** |
| **`video-use`** | `https://github.com/browser-use/video-use` | MIT | Agentic video editing, silence/filler cutting, Playwright/Remotion demo capture, and overlay assembly. | **SELECTED (P2 — Policy A)** |

---

## 8. Prioritized Integration Summary (P0 / P1 / P2)

- **P0 (Core Efficiency & Design Intelligence — Integrated Now):**
  1. `ponytail` (`skills/core/ponytail/`) — YAGNI decision ladder.
  2. `graphify` (`skills/core/graphify/`) — Codebase knowledge graph skill with $\ge 15$-file threshold guard.
  3. `caveman` (`skills/optional/communication/caveman/`) — Full upstream `JuliusBrussee/caveman` alignment.
  4. `rtk-cli` (`skills/optional/communication/rtk-cli/` + `integrations/rtk/`) — RTK command compression wrapper with safe fallback (binary install awaits Policy B user approval).
  5. `context-optimization` (`skills/optional/context-engineering/context-optimization/`) — KV-cache, observation masking, and compaction triggers.
  6. `context-compression` (`skills/optional/context-engineering/context-compression/`) — Anchored iterative summarization + `compression_evaluator.py`.
  7. `ui-ux-pro-max` (`skills/optional/frontend-design/ui-ux-pro-max/`) — Full offline BM25 search engine (`scripts/search.py`, `core.py`, `design_system.py`) + 28 CSV databases (including `angular.csv`).
- **P1 (Context Persistence, Agent Architecture & Angular — Integrated Now):**
  8. `filesystem-context` (`skills/optional/context-engineering/filesystem-context/`)
  9. `memory-systems` (`skills/optional/context-engineering/memory-systems/`)
  10. `multi-agent-patterns` (`skills/optional/agent-architecture/multi-agent-patterns/`)
  11. `tool-design` (`skills/optional/agent-architecture/tool-design/`)
  12. `evaluation` (`skills/optional/agent-architecture/evaluation/`)
  13. `self-improvement-loops` (`skills/optional/agent-architecture/self-improvement-loops/`)
  14. `angular-developer` (`skills/optional/frontend-design/angular-developer/` with 36 official Angular reference guides)
  15. `angular-new-app` (`skills/optional/frontend-design/angular-new-app/`)
- **P2 (Optional Growth, Brand & Video Domain Pack — Integrated & Disabled by Default):**
  16. `seo-audit`, `ai-seo`, `content-strategy`, `pricing`, `brand-strategy`, `video-lens`, `video-use` (`skills/optional/growth-media/`).
