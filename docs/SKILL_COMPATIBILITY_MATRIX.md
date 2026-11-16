# Skill Compatibility Matrix (`SKILL_COMPATIBILITY_MATRIX.md`)

**Project:** AI Engineering Framework (`ai-engineering-framework`)  
**Version:** `0.2.0`  
**Date:** 2026-11-16  

---

## 1. Platform Discovery & Activation Mechanics

Different AI coding platforms discover and activate skills through distinct mechanisms. The framework maps a single canonical `skills/` directory across all 5 platforms without duplicating full skill bodies:

| Platform | Native Skill Discovery Path | Automatic (Model-Driven) Activation? | Explicit Invocation Syntax | Bundled Scripts & `references/` Support | Scope Support |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Google Antigravity** | `.agents/skills/<name>/SKILL.md` (workspace) & `~/.gemini/config/skills/<name>/SKILL.md` (global) | **Yes (Native Progressive Disclosure):** Only `name` + `description` are injected at startup; full `SKILL.md` loads via `read_file` when relevant. | `/caveman`, `/grill-me`, or natural language match | **Full:** Relative `references/` via `read_file` and Python `scripts/*.py` via `run_command` | Project (`.agents/skills/`) & Global (`~/.gemini/config/skills/`) |
| **2. GitHub Copilot** | `.agents/skills/<name>/SKILL.md` (VS Code Agent Mode) + `.github/prompts/<name>.prompt.md` | **Partial:** VS Code Agent Mode discovers `.agents/skills/` descriptions; Chat mode uses `AGENTS.md` index or `.prompt.md` files. | `#prompt:<name>` or `/grill-me` in Copilot Chat | **Full:** Relative links in Markdown and terminal execution in Agent Mode | Project (`.github/`, `.agents/skills/`) & User profile |
| **3. Claude Code** | `.claude/skills/<name>/SKILL.md` (workspace) & `~/.claude/skills/<name>/SKILL.md` (global) | **Yes (Native Progressive Disclosure):** Claude reads YAML frontmatter `description` and loads `SKILL.md` on demand. | `/grill-me`, `/validate-framework` (`.claude/commands/*.md`) or skill trigger | **Full:** Executes bundled `scripts/*.py` via `Bash` tool and reads `references/*.md` via `Read` | Project (`.claude/skills/`) & Global (`~/.claude/skills/`) |
| **4. OpenAI Codex** | `.agents/skills/<name>/SKILL.md` (workspace) & `~/.codex/skills/<name>/SKILL.md` (global) + `AGENTS.md` | **Yes:** Codex discovers `.agents/skills/*/SKILL.md` and `AGENTS.md` routing table. | Natural language or `$skill-name` mention | **Full:** Runs bundled Python scripts inside `workspace-write` sandbox | Project (`.agents/skills/`) & Global (`~/.codex/skills/`) |
| **5. Gemini CLI** | `.agents/skills/<name>/SKILL.md` + `GEMINI.md` index + `.gemini/commands/*.toml` | **Yes (via `GEMINI.md` & extensions):** Reads skill index from `GEMINI.md` and loads `SKILL.md` via file-read tool. | `/workflow` (`.gemini/commands/workflow.toml`) or natural language | **Full:** Executes Python stdlib scripts via shell tool | Project (`.gemini/`, `.agents/skills/`) & Global (`~/.gemini/`) |

---

## 2. Per-Skill Compatibility & Requirements Matrix (All 25 Registered Skills)

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
| **11** | `context-optimization` | `optional-context` | P0 | Vendored (`muratcankoylan`) | MIT | Yes | Indexed in `AGENTS.md` | Auto when context $>60\%$ or heavy tool outputs | `scripts/compaction_tokens.py`, `references/` | **Policy A** |
| **12** | `context-compression` | `optional-context` | P0 | Vendored (`muratcankoylan`) | MIT | Yes | Indexed in `AGENTS.md` | Auto on long trajectories / phase handoffs | `scripts/compression_evaluator.py`, `references/` | **Policy A** |
| **13** | `filesystem-context` | `optional-context` | P1 | Vendored (`muratcankoylan`) | MIT | Yes | Indexed in `AGENTS.md` | Auto when offloading outputs $>2000$ chars | `scripts/context_scratchpad.py`, `references/` | **Policy A** |
| **14** | `memory-systems` | `optional-context` | P1 | Vendored (`muratcankoylan`) | MIT | Yes | Indexed in `AGENTS.md` | On-Demand for cross-session entity memory | `scripts/memory_store.py`, `references/` | **Policy A** |
| **15** | `multi-agent-patterns` | `optional-agent-architecture` | P1 | Vendored (`muratcankoylan`) | MIT | Yes | Indexed in `AGENTS.md` | Auto in Phase 8 (`planner-orchestrator`) | `scripts/coordination.py`, `references/` | **Policy A** |
| **16** | `tool-design` | `optional-agent-architecture` | P1 | Vendored (`muratcankoylan`) | MIT | Yes | Indexed in `AGENTS.md` | On-Demand when designing CLI/MCP tools | `scripts/description_generator.py`, `references/` | **Policy A** |
| **17** | `evaluation` | `optional-agent-architecture` | P1 | Vendored (`muratcankoylan`) | MIT | Yes | Indexed in `AGENTS.md` | Auto in Phase 10 & 11 (`code-reviewer`, `qa-engineer`) | `scripts/evaluator.py`, `references/` | **Policy A** |
| **18** | `self-improvement-loops` | `optional-agent-architecture` | P1 | Vendored (`muratcankoylan`) | MIT | Yes | Indexed in `AGENTS.md` | Auto in Phase 15 (`Retrospectives`) | `references/loop-design-evidence.md` | **Policy A** |
| **19** | `ui-ux-pro-max` | `optional-frontend` | P0 | Vendored (`nextlevelbuilder`) | MIT | Yes | Indexed in `AGENTS.md` | Auto on UI/UX, dashboard, landing, or styling tasks | `scripts/search.py`, `core.py`, `design_system.py`, `data/*.csv` (28 CSVs incl. Angular) | **Policy A** |
| **20** | `angular-developer` | `optional-frontend` | P1 | Vendored (`angular/skills`) | MIT | Yes | Indexed in `AGENTS.md` | Auto when `angular.json` or `@angular/core` present | 36 `references/*.md` files | **Policy A** |
| **21** | `angular-new-app` | `optional-frontend` | P1 | Vendored (`angular/skills`) | MIT | Yes | Indexed in `AGENTS.md` | On-Demand when scaffolding a new Angular workspace | None (Uses `@angular/cli` when running) | **Policy A** |
| **22** | `web-design-guidelines` | `optional-frontend` | P1 | First-Party | Apache-2.0 | Yes | Indexed in `AGENTS.md` | Auto on web UI implementation & QA | None | **Policy A** |
| **23** | `canvas-design` | `optional-frontend` | P1 | First-Party | Apache-2.0 | Yes | Indexed in `AGENTS.md` | On-Demand for 3-layer CSS token systems | None | **Policy A** |
| **24** | `seo-audit` | `optional-growth` | P2 | Adapted (`coreyhaines31/marketingskills`) | MIT | Yes | Opt-in via `project.framework.json` | Explicit / Opt-in only (Public web sites) | None | **Policy A** |
| **25** | `ai-seo` | `optional-growth` | P2 | Adapted (`coreyhaines31/marketingskills`) | MIT | Yes | Opt-in via `project.framework.json` | Explicit / Opt-in only (`llms.txt` & GEO) | None | **Policy A** |
| **26** | `content-strategy` | `optional-growth` | P2 | Adapted (`coreyhaines31/marketingskills`) | MIT | Yes | Opt-in via `project.framework.json` | Explicit / Opt-in only | None | **Policy A** |
| **27** | `pricing` | `optional-growth` | P2 | Adapted (`coreyhaines31/marketingskills`) | MIT | Yes | Opt-in via `project.framework.json` | Explicit / Opt-in only | None | **Policy A** |
| **28** | `brand-strategy` | `optional-growth` | P2 | Adapted (`claudekit/brand`) | MIT | Yes | Opt-in via `project.framework.json` | Explicit / Opt-in only | `references/` | **Policy A** |
| **29** | `video-lens` | `optional-growth` | P2 | Adapted (`kar2phi/video-lens`) | MIT | Yes | Opt-in via `project.framework.json` | Explicit / Opt-in only (Video analysis) | Uses multimodal `read_file` or `opencv-python` | **Policy A** |
| **30** | `video-use` | `optional-growth` | P2 | Adapted (`browser-use/video-use`) | MIT | Yes | Opt-in via `project.framework.json` | Explicit / Opt-in only (Video editing/demos) | Uses Playwright video / `ffmpeg` when requested | **Policy A** |

---

## 3. Deduplication & Conflict Resolution Summary

1. **`RTK` vs. `Headroom`:** Selected `RTK` (`rtk-ai/rtk`) for shell command compression because it is a `<10ms` zero-dependency Rust binary with native hook support (`rtk init`), whereas `Headroom` requires hijacking `OPENAI_BASE_URL` / `ANTHROPIC_BASE_URL` via a local Python proxy that is unsupported by native IDE OAuth sessions (Antigravity, Copilot).
2. **`ui-ux-pro-max` vs. `design` / `design-system` / `ui-styling`:** Selected `ui-ux-pro-max` (`nextlevelbuilder/ui-ux-pro-max-skill`) + `angular-developer` (`angular/skills`) + `web-design-guidelines` + `canvas-design`. Rejected `claudekit/design`, `claudekit/design-system`, and `claudekit/ui-styling` (`591 KB` of redundant markdown and corporate-identity logo prompts) because `ui-ux-pro-max` already includes searchable databases for `shadcn`, `html-tailwind`, `angular`, `react`, `styles`, `colors`, and `typography`.
3. **`Agent-Skills-for-Context-Engineering` (8 Selected vs. 5 Rejected/Consolidated):** Selected the 8 operational skills (`context-optimization`, `context-compression`, `filesystem-context`, `memory-systems`, `multi-agent-patterns`, `tool-design`, `evaluation`, `self-improvement-loops`) and excluded `context-fundamentals`, `context-degradation`, `project-development`, `hosted-agents`, and `advanced-evaluation` to save `250+ KB` of overlapping conceptual prose.
4. **`anti-slop` vs. `humanizer`:** Retained `anti-slop` (`2.1 KB`) and rejected `humanizer` (`61.1 KB`) which duplicates the exact same AI-tell removal rules at 29x the token footprint.
