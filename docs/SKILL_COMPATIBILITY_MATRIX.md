# Skill Compatibility Matrix (`SKILL_COMPATIBILITY_MATRIX.md`)

**Project:** AI Engineering Framework (`ai-engineering-framework`)  
**Version:** `0.4.0`  
**Date:** `2026-11-19`  

---

## 1. Platform Discovery, Projection & Evidence Status

The framework maintains canonical skills under `skills/` (`33` registered skills across `core/` and `5` `optional/` packs, indexed by [`skills/registry.json`](../skills/registry.json)) plus consumer-defined skills under `.framework-custom/skills/<name>/`. During `bootstrap.py` and `compose.py`, [`scripts/bootstrap.py`](../scripts/bootstrap.py) reads [`core/platform-capabilities.json`](../core/platform-capabilities.json) and materializes **native skill projections** into `.agents/skills/<name>/SKILL.md` and (when `claude-code` is enabled) `.claude/skills/<name>/SKILL.md`, excluding authoring-only `UPSTREAM_SKILL.md` and `__pycache__/`.

| Platform | Contract Support (`v0.4.0`) | Maintainer-Host Live Probe | Native Skill Discovery Path | Activation & Reality Notes | Bundled Scripts & `references/` Support |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **1. Google Antigravity** | **`SUPPORTED`** | **`RUNTIME_VERIFIED`** | `.agents/skills.json` + `.agents/skills/<name>/SKILL.md` (workspace); `~/.gemini/config/skills/` (host-global) | **Verified live** (`agy v1.5.9`/`v1.5.10` + brownfield custom skill smoke): reads progressive skill metadata, loads `SKILL.md` via `read_file`, writes `.framework-state/scratch/`. | `read_file` for `references/*.md`; host shell needed for `scripts/*.py` when not in `accept-edits` |
| **2. OpenAI Codex CLI** | **`SUPPORTED`** | **`PARTIAL_RUNTIME_VERIFIED`** | `.agents/skills/<name>/SKILL.md` (workspace) & `~/.codex/skills/` + `AGENTS.md` | **Verified partial** (`codex 0.169.0`, `M8-03B`): Codex scans `<workspace>/.agents/skills/` and `$HOME/.agents/skills/`, and injects `AGENTS.md` skill tables. Windows sandbox requires external OS setup for disk write execution. | Documented for `workspace-write` sandbox; external Windows OS sandbox required |
| **3. Claude Code** | **`SUPPORTED`** | `Not run live on host` *(Auth prereq)* | `.claude/skills/<name>/SKILL.md` (workspace) & `~/.claude/skills/` | **Adapters & native `.claude/skills/` validated statically** (`84/84` suite): `CLAUDE.md`, `.claude/skills/` (framework + custom), read-only `.claude/agents/*.md`, `.claude/commands/*.md`, `.claude/settings.json`. Live CLI execution only awaited Claude `Pro`/`Max`/`Ultra` login on maintainer host. | Documented (`Read`/`Bash`); ready on disk, awaiting user host auth |
| **4. GitHub Copilot** | **`SUPPORTED`** | `Not run live on host` *(Auth prereq)* | `.agents/skills/<name>/SKILL.md` (VS Code Agent Mode) + `.github/prompts/*.prompt.md` | **Adapters & native `.agents/skills/` validated statically** (`84/84` suite): `.github/copilot-instructions.md`, `.instructions.md`, `.prompt.md`, `.agent.md`, `.agents/skills/`. Live IDE check awaits VS Code extension/Copilot auth. | Documented for Agent Mode; ready on disk, awaiting user VS Code Copilot session |
| **5. Gemini CLI** | **`SUPPORTED`** | `Not run live on host` *(Tier prereq)* | `.agents/skills/<name>/SKILL.md` + `GEMINI.md` + `.gemini/commands/*.toml` | **Adapters & `.agents/skills/` validated statically** (`cli 0.68.0` pre-auth `skills list` confirmed `.agents/skills` scan): post-auth requires an eligible Gemini CLI account tier on host. | Documented for trusted workspaces; ready on disk, awaiting eligible host tier |

---

## 2. Per-Skill Compatibility & Requirements Matrix (All 33 Registered Skills)

| # | Skill Name | Category / Tier | Priority | Origin | License | Native Discovery (AGY / Claude / Codex) | Adapter Required (Copilot / Gemini CLI) | Activation Mode | Bundled Scripts / Data | Policy Class |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | `grill-me` | `core` | P0 | First-Party | Apache-2.0 | Yes | `.github/prompts/grill-me.prompt.md`, `.claude/commands/grill-me.md` | Auto (Phase 2) + Explicit (`/grill-me`) | None | **Policy A** |
| **2** | `tdd-cycle` | `core` | P0 | First-Party | Apache-2.0 | Yes | Indexed in `AGENTS.md` | Auto (Phase 9 & 11) | None | **Policy A** |
| **3** | `ponytail` | `core` | P0 | Vendored (`DietrichGebert/ponytail`) | MIT | Yes | Indexed in `AGENTS.md` | Auto (Phase 5, 9, 10) | None | **Policy A** |
| **4** | `adr-writer` | `core` | P0 | First-Party | Apache-2.0 | Yes | Indexed in `AGENTS.md` | Auto (Phase 5) | Uses `templates/ADR.template.md` | **Policy A** |
| **5** | `graphify` | `core` | P0 | Vendored (`Graphify-Labs/graphify`) | Apache-2.0 | Yes | Indexed in `AGENTS.md` & `GEMINI.md` | Auto when `graphify-out/` exists or $\ge 15$ files | Uses host `graphify` CLI (`0.9.48`) | **Policy A** (CLI already on host) |
| **6** | `agent-browser` | `core` | P0 | First-Party | Apache-2.0 | Yes | Indexed in `AGENTS.md` | Auto (Phase 4 & 11 UI checks) | Uses Antigravity `browser` subagent or Playwright MCP | **Policy A** |
| **7** | `find-skills` | `core` | P0 | Vendored (`vercel-labs/skills`) | MIT | Yes | Indexed in `AGENTS.md` | Explicit / On-Demand when capability missing | Optional `npx skills` or `search_marketplace` | **Policy A** |
| **8** | `anti-slop` | `core` | P0 | Adapted (`stop-slop`) | MIT | Yes | Indexed in `AGENTS.md` | Auto (Phase 3, 5, 10, 14) | None | **Policy A** |
| **9** | `caveman` | `optional-communication` | P0 | Vendored (`JuliusBrussee/caveman`) | MIT | Yes | Indexed in `AGENTS.md` | Explicit (`/caveman`) or User Rule | `UPSTREAM_SKILL.md` preserved | **Policy A** |
| **10** | `rtk-cli` | `optional-communication` | P0 | Bridge (`rtk-ai/rtk`) | Apache-2.0 | Yes | Hook config in `integrations/rtk/` | Auto when `rtk` binary in `PATH`; safe fallback otherwise | Requires external `rtk.exe` for compression | **Policy A (Skill) / Policy B (Binary)** |
| **11** | `i-have-adhd` | `optional-communication` | P1 | Vendored (`ayghri/i-have-adhd`) | MIT | Yes | Indexed in `AGENTS.md` | Auto / Opt-in for short low-friction structured updates | Pure Markdown | **Policy A** |
| **12** | `humanizer` | `optional-communication` | P1 | Vendored (`blader/humanizer`) | MIT | Yes | Indexed in `AGENTS.md` | Explicit / On-Demand prose polishing alongside `anti-slop` | Pure Markdown (24 AI-writing patterns) | **Policy A** |
| **13** | `context-optimization` | `optional-context` | P0 | Vendored (`muratcankoylan`) | MIT | Yes | Indexed in `AGENTS.md` | Auto when context $>60\%$ or heavy tool outputs | `scripts/compaction_tokens.py`, `references/` | **Policy A** |
| **14** | `context-compression` | `optional-context` | P0 | Vendored (`muratcankoylan`) | MIT | Yes | Indexed in `AGENTS.md` | Auto on long trajectories / phase handoffs | `scripts/compression_evaluator.py`, `references/` | **Policy A** |
| **15** | `filesystem-context` | `optional-context` | P1 | Vendored (`muratcankoylan`) | MIT | Yes | Indexed in `AGENTS.md` | Auto when offloading outputs $>2000$ chars | `scripts/context_scratchpad.py`, `references/` | **Policy A** |
| **16** | `memory-systems` | `optional-context` | P1 | Vendored (`muratcankoylan`) | MIT | Yes | Indexed in `AGENTS.md` | On-Demand for cross-session entity memory | `scripts/memory_store.py`, `references/` | **Policy A** |
| **17** | `session-handoff` | `optional-context` | P0 | Vendored (`softaworks/agent-toolkit`) | MIT | Yes | Indexed in `AGENTS.md` | Auto/Explicit on chat switches (`create_handoff.py` -> `.framework-state/session-handoffs/`) | `scripts/*.py` (pure stdlib), `references/` | **Policy A** |
| **18** | `multi-agent-patterns` | `optional-agent-architecture` | P1 | Vendored (`muratcankoylan`) | MIT | Yes | Indexed in `AGENTS.md` | Auto in Phase 8 (`planner-orchestrator`) | `scripts/coordination.py`, `references/` | **Policy A** |
| **19** | `tool-design` | `optional-agent-architecture` | P1 | Vendored (`muratcankoylan`) | MIT | Yes | Indexed in `AGENTS.md` | On-Demand when designing CLI/MCP tools | `scripts/description_generator.py`, `references/` | **Policy A** |
| **20** | `evaluation` | `optional-agent-architecture` | P1 | Vendored (`muratcankoylan`) | MIT | Yes | Indexed in `AGENTS.md` | Auto in Phase 10 & 11 (`code-reviewer`, `qa-engineer`) | `scripts/evaluator.py`, `references/` | **Policy A** |
| **21** | `self-improvement-loops` | `optional-agent-architecture` | P1 | Vendored (`muratcankoylan`) | MIT | Yes | Indexed in `AGENTS.md` | Auto in Phase 15 (`Retrospectives`) | `references/loop-design-evidence.md` | **Policy A** |
| **22** | `ui-ux-pro-max` | `optional-frontend` | P0 | Vendored (`nextlevelbuilder`) | MIT | Yes | Indexed in `AGENTS.md` | Auto on UI/UX, dashboard, landing, or styling tasks | `scripts/search.py`, `core.py`, `design_system.py`, `data/*.csv` (28 CSVs incl. Angular) | **Policy A** |
| **23** | `angular-developer` | `optional-frontend` | P1 | Vendored (`angular/skills`) | MIT | Yes | Indexed in `AGENTS.md` | Auto when `angular.json` or `@angular/core` present | 36 `references/*.md` files | **Policy A** |
| **24** | `angular-new-app` | `optional-frontend` | P1 | Vendored (`angular/skills`) | MIT | Yes | Indexed in `AGENTS.md` | On-Demand when scaffolding a new Angular workspace | None (Uses `@angular/cli` when running) | **Policy A** |
| **25** | `web-design-guidelines` | `optional-frontend` | P1 | First-Party | Apache-2.0 | Yes | Indexed in `AGENTS.md` | Auto on web UI implementation & QA | None | **Policy A** |
| **26** | `canvas-design` | `optional-frontend` | P1 | First-Party | Apache-2.0 | Yes | Indexed in `AGENTS.md` | On-Demand for 3-layer CSS token systems | None | **Policy A** |
| **27** | `seo-audit` | `optional-growth` | P2 | Adapted (`coreyhaines31/marketingskills`) | MIT | Yes | Opt-in via `project.framework.json` | Explicit / Opt-in only (Public web sites) | None | **Policy A** |
| **28** | `ai-seo` | `optional-growth` | P2 | Adapted (`coreyhaines31/marketingskills`) | MIT | Yes | Opt-in via `project.framework.json` | Explicit / Opt-in only (`llms.txt` & GEO) | None | **Policy A** |
| **29** | `content-strategy` | `optional-growth` | P2 | Adapted (`coreyhaines31/marketingskills`) | MIT | Yes | Opt-in via `project.framework.json` | Explicit / Opt-in only | None | **Policy A** |
| **30** | `pricing` | `optional-growth` | P2 | Adapted (`coreyhaines31/marketingskills`) | MIT | Yes | Opt-in via `project.framework.json` | Explicit / Opt-in only | None | **Policy A** |
| **31** | `brand-strategy` | `optional-growth` | P2 | Adapted (`claudekit/brand`) | MIT | Yes | Opt-in via `project.framework.json` | Explicit / Opt-in only | `references/` | **Policy A** |
| **32** | `video-lens` | `optional-growth` | P2 | Adapted (`kar2phi/video-lens`) | MIT | Yes | Opt-in via `project.framework.json` | Explicit / Opt-in only (Video analysis) | Uses multimodal `read_file` or `opencv-python` | **Policy A** |
| **33** | `video-use` | `optional-growth` | P2 | Adapted (`browser-use/video-use`) | MIT | Yes | Opt-in via `project.framework.json` | Explicit / Opt-in only (Video editing/demos) | Uses Playwright video / `ffmpeg` when requested | **Policy A** |

---

## 3. Deduplication & Conflict Resolution Summary

1. **`RTK` vs. `Headroom`:** Selected `RTK` (`rtk-ai/rtk`) for shell command compression because it is a `<10ms` zero-dependency Rust binary with native hook support (`rtk init`), whereas `Headroom` requires hijacking `OPENAI_BASE_URL` / `ANTHROPIC_BASE_URL` via a local Python proxy that is unsupported by native IDE OAuth sessions (Antigravity, Copilot).
2. **`ui-ux-pro-max` vs. `design` / `design-system` / `ui-styling`:** Selected `ui-ux-pro-max` (`nextlevelbuilder/ui-ux-pro-max-skill`) + `angular-developer` (`angular/skills`) + `web-design-guidelines` + `canvas-design`. Rejected `claudekit/design`, `claudekit/design-system`, and `claudekit/ui-styling` (`591 KB` of redundant markdown and corporate-identity logo prompts) because `ui-ux-pro-max` already includes searchable databases for `shadcn`, `html-tailwind`, `angular`, `react`, `styles`, `colors`, and `typography`.
3. **`Agent-Skills-for-Context-Engineering` (8 Selected vs. 5 Rejected/Consolidated):** Selected the 8 operational skills (`context-optimization`, `context-compression`, `filesystem-context`, `memory-systems`, `multi-agent-patterns`, `tool-design`, `evaluation`, `self-improvement-loops`) and excluded `context-fundamentals`, `context-degradation`, `project-development`, `hosted-agents`, and `advanced-evaluation` to save `250+ KB` of overlapping conceptual prose.
4. **`anti-slop` & `humanizer`:** Both are now included intentionally with clear separation of roles: lightweight `anti-slop` stays in `core` for automatic Phase 3/5/10/14 code/spec hygiene, while `humanizer` (`optional-communication`) adds comprehensive 24-pattern Wikipedia AI-prose editing for documentation/marketing prose and can be toggled off anytime via `disabled.skills`.
