# Skills Catalog, Installation & Compatibility Matrix (`SKILL_COMPATIBILITY_MATRIX.md`)

**Version:** `0.4.0`

---

## 1. Installation Policy & Optional Packs

Canonical skills live under `skills/` (`33` skills across `core/` and `5` `optional/` packs, indexed by [`skills/registry.json`](../skills/registry.json)). Consumer workspaces receive native projections under `.agents/skills/<name>/SKILL.md` and `.claude/skills/<name>/SKILL.md` (plus custom project skills under `.framework-custom/skills/<name>/`).

- **Policy A (Repository-Local):** Markdown skills, offline CSV/reference datasets, and Python stdlib scripts under `skills/`. Installed via `aief init` / `bootstrap.py`.
- **Policy B (External CLI — User Approval Required):** Optional host binaries such as `rtk` (`rtk-ai/rtk`) or `graphify` (`graphifyy`). Never installed silently by framework scripts.
- **Policy C (Excluded References):** Overlapping packages kept out of runtime to prevent prompt bloat.

### Available `--optional-packs` Values
`aief init` and `scripts/bootstrap.py` default to `all` (`33` skills). Pass `--optional-packs` to filter at install time, or disable individual skills anytime in `project.framework.json` (`disabled.skills`):

| Pack ID | Skills Included | Count |
| :--- | :--- | :---: |
| *(Core — Always Installed)* | `grill-me`, `tdd-cycle`, `ponytail`, `adr-writer`, `graphify`, `agent-browser`, `find-skills`, `anti-slop` | `8` |
| `communication` | `caveman`, `rtk-cli`, `i-have-adhd`, `humanizer` | `4` |
| `context-engineering` | `context-optimization`, `context-compression`, `filesystem-context`, `memory-systems`, `session-handoff` | `5` |
| `agent-architecture` | `multi-agent-patterns`, `tool-design`, `evaluation`, `self-improvement-loops` | `4` |
| `frontend-design` *(alias `design-ui`)* | `ui-ux-pro-max` (BM25 `search.py` + 28 CSVs), `angular-developer` (36 guides), `angular-new-app`, `web-design-guidelines`, `canvas-design` | `5` |
| `growth-media` | `seo-audit`, `ai-seo`, `content-strategy`, `pricing`, `brand-strategy`, `video-lens`, `video-use` | `7` |
| `none` / `all` | Core-only (`8`) or full catalog (`33`, default) | — |

### Optional External CLIs (Policy B)
- **RTK (`rtk-ai/rtk`):** Compresses terminal output (`git`, `pytest`, `npm`, `cargo`). Install with `winget install -e --id rtk-ai.rtk --accept-source-agreements --accept-package-agreements`. Without it, `rtk-cli` falls back to compact CLI flags.
- **Graphify (`graphifyy`):** Builds AST/concept graphs (`graphify-out/`) for repos with $\ge 15$ files (or $> 2,000$ LOC). Install with `pipx install graphifyy`. If missing, `bootstrap.py`, `validate.py`, and Phase 1 report it explicitly without blocking work.

---

## 2. Platform Skill Discovery Paths

| Platform | Support (`v0.4.0`) | Native Skill Discovery Path | Bundled Scripts & `references/` Support |
| :--- | :---: | :--- | :--- |
| **1. Google Antigravity** | **`SUPPORTED`** | `.agents/skills.json` + `.agents/skills/<name>/SKILL.md` (workspace); `~/.gemini/config/skills/` (host-global) | `read_file` for `references/*.md`; shell execution for `scripts/*.py` |
| **2. OpenAI Codex CLI** | **`SUPPORTED`** | `.agents/skills/<name>/SKILL.md` (workspace) & `~/.codex/skills/` + `AGENTS.md` | Supported under `workspace-write` sandbox |
| **3. Claude Code** | **`SUPPORTED`** | `.claude/skills/<name>/SKILL.md` (workspace) & `~/.claude/skills/` | Supported via `Read` / `Bash` |
| **4. GitHub Copilot** | **`SUPPORTED`** | `.agents/skills/<name>/SKILL.md` (VS Code Agent Mode) + `.github/prompts/*.prompt.md` | Supported in VS Code Agent Mode |
| **5. Gemini CLI** | **`SUPPORTED`** | `.agents/skills/<name>/SKILL.md` + `GEMINI.md` + `.gemini/commands/*.toml` | Supported in trusted workspaces |

---

## 3. Per-Skill Compatibility Matrix (All 33 Registered Skills)

| # | Skill Name | Category / Tier | Priority | Origin | License | Native Discovery (AGY / Claude / Codex) | Adapter / Activation | Bundled Scripts / Data | Policy Class |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | `grill-me` | `core` | P0 | First-Party | Apache-2.0 | Yes | `.github/prompts/grill-me.prompt.md`, `.claude/commands/grill-me.md`; Phase 2 / `/grill-me` | None | **Policy A** |
| **2** | `tdd-cycle` | `core` | P0 | First-Party | Apache-2.0 | Yes | `AGENTS.md`; Phase 9 & 11 | None | **Policy A** |
| **3** | `ponytail` | `core` | P0 | Vendored (`DietrichGebert/ponytail`) | MIT | Yes | `AGENTS.md`; Phase 5, 9, 10 | None | **Policy A** |
| **4** | `adr-writer` | `core` | P0 | First-Party | Apache-2.0 | Yes | `AGENTS.md`; Phase 5 | `templates/ADR.template.md` | **Policy A** |
| **5** | `graphify` | `core` | P0 | Vendored (`Graphify-Labs/graphify`) | Apache-2.0 | Yes | `AGENTS.md`, `GEMINI.md`; repos $\ge 15$ files | Uses `graphify` CLI when present | **Policy A (Skill) / Policy B (CLI)** |
| **6** | `agent-browser` | `core` | P0 | First-Party | Apache-2.0 | Yes | `AGENTS.md`; Phase 4 & 11 UI checks | Antigravity `browser` subagent or Playwright MCP | **Policy A** |
| **7** | `find-skills` | `core` | P0 | Vendored (`vercel-labs/skills`) | MIT | Yes | `AGENTS.md`; on-demand discovery | Optional `npx skills` / `search_marketplace` | **Policy A** |
| **8** | `anti-slop` | `core` | P0 | Adapted (`stop-slop`) | MIT | Yes | `AGENTS.md`; Phase 3, 5, 10, 14 | None | **Policy A** |
| **9** | `caveman` | `optional-communication` | P0 | Vendored (`JuliusBrussee/caveman`) | MIT | Yes | `AGENTS.md`; `/caveman` or User Rule | `UPSTREAM_SKILL.md` preserved | **Policy A** |
| **10** | `rtk-cli` | `optional-communication` | P0 | Bridge (`rtk-ai/rtk`) | Apache-2.0 | Yes | `integrations/rtk/`; auto when `rtk` in `PATH` | Optional `rtk` binary | **Policy A (Skill) / Policy B (Binary)** |
| **11** | `i-have-adhd` | `optional-communication` | P1 | Vendored (`ayghri/i-have-adhd`) | MIT | Yes | `AGENTS.md`; short structured updates | Pure Markdown | **Policy A** |
| **12** | `humanizer` | `optional-communication` | P1 | Vendored (`blader/humanizer`) | MIT | Yes | `AGENTS.md`; prose editing alongside `anti-slop` | Pure Markdown (24 patterns) | **Policy A** |
| **13** | `context-optimization` | `optional-context` | P0 | Vendored (`muratcankoylan`) | MIT | Yes | `AGENTS.md`; context $>60\%$ or large outputs | `scripts/compaction_tokens.py`, `references/` | **Policy A** |
| **14** | `context-compression` | `optional-context` | P0 | Vendored (`muratcankoylan`) | MIT | Yes | `AGENTS.md`; long trajectories / handoffs | `scripts/compression_evaluator.py`, `references/` | **Policy A** |
| **15** | `filesystem-context` | `optional-context` | P1 | Vendored (`muratcankoylan`) | MIT | Yes | `AGENTS.md`; outputs $>2000$ chars | `scripts/context_scratchpad.py`, `references/` | **Policy A** |
| **16** | `memory-systems` | `optional-context` | P1 | Vendored (`muratcankoylan`) | MIT | Yes | `AGENTS.md`; cross-session entity memory | `scripts/memory_store.py`, `references/` | **Policy A** |
| **17** | `session-handoff` | `optional-context` | P0 | Vendored (`softaworks/agent-toolkit`) | MIT | Yes | `AGENTS.md`; chat switches (`.framework-state/session-handoffs/`) | `scripts/*.py` (stdlib), `references/` | **Policy A** |
| **18** | `multi-agent-patterns` | `optional-agent-architecture` | P1 | Vendored (`muratcankoylan`) | MIT | Yes | `AGENTS.md`; Phase 8 (`planner-orchestrator`) | `scripts/coordination.py`, `references/` | **Policy A** |
| **19** | `tool-design` | `optional-agent-architecture` | P1 | Vendored (`muratcankoylan`) | MIT | Yes | `AGENTS.md`; CLI/MCP design | `scripts/description_generator.py`, `references/` | **Policy A** |
| **20** | `evaluation` | `optional-agent-architecture` | P1 | Vendored (`muratcankoylan`) | MIT | Yes | `AGENTS.md`; Phase 10 & 11 | `scripts/evaluator.py`, `references/` | **Policy A** |
| **21** | `self-improvement-loops` | `optional-agent-architecture` | P1 | Vendored (`muratcankoylan`) | MIT | Yes | `AGENTS.md`; Phase 15 | `references/loop-design-evidence.md` | **Policy A** |
| **22** | `ui-ux-pro-max` | `optional-frontend` | P0 | Vendored (`nextlevelbuilder`) | MIT | Yes | `AGENTS.md`; UI/UX & styling tasks | `scripts/search.py`, `core.py`, `design_system.py`, `data/*.csv` (28 CSVs) | **Policy A** |
| **23** | `angular-developer` | `optional-frontend` | P1 | Vendored (`angular/skills`) | MIT | Yes | `AGENTS.md`; Angular apps | 36 `references/*.md` files | **Policy A** |
| **24** | `angular-new-app` | `optional-frontend` | P1 | Vendored (`angular/skills`) | MIT | Yes | `AGENTS.md`; scaffolding Angular workspaces | Uses `@angular/cli` when running | **Policy A** |
| **25** | `web-design-guidelines` | `optional-frontend` | P1 | First-Party | Apache-2.0 | Yes | `AGENTS.md`; web UI implementation & QA | None | **Policy A** |
| **26** | `canvas-design` | `optional-frontend` | P1 | First-Party | Apache-2.0 | Yes | `AGENTS.md`; 3-layer CSS tokens | None | **Policy A** |
| **27** | `seo-audit` | `optional-growth` | P2 | Adapted (`coreyhaines31/marketingskills`) | MIT | Yes | Public websites (toggle via `disabled.skills`) | None | **Policy A** |
| **28** | `ai-seo` | `optional-growth` | P2 | Adapted (`coreyhaines31/marketingskills`) | MIT | Yes | `llms.txt` & GEO | None | **Policy A** |
| **29** | `content-strategy` | `optional-growth` | P2 | Adapted (`coreyhaines31/marketingskills`) | MIT | Yes | On-demand | None | **Policy A** |
| **30** | `pricing` | `optional-growth` | P2 | Adapted (`coreyhaines31/marketingskills`) | MIT | Yes | On-demand | None | **Policy A** |
| **31** | `brand-strategy` | `optional-growth` | P2 | Adapted (`claudekit/brand`) | MIT | Yes | On-demand | `references/` | **Policy A** |
| **32** | `video-lens` | `optional-growth` | P2 | Adapted (`kar2phi/video-lens`) | MIT | Yes | Video analysis | Multimodal `read_file` or `opencv-python` | **Policy A** |
| **33** | `video-use` | `optional-growth` | P2 | Adapted (`browser-use/video-use`) | MIT | Yes | Video editing/demos | Playwright video / `ffmpeg` when requested | **Policy A** |

---

## 4. Curation & Deduplication Notes

1. **`RTK` vs. `Headroom`:** Selected `RTK` (`rtk-ai/rtk`, $<10\text{ms}$ Rust binary) instead of `Headroom` (`OPENAI_BASE_URL` proxy unsupported by IDE OAuth sessions).
2. **`ui-ux-pro-max` vs. `design` packs:** Retained `ui-ux-pro-max` + `angular-developer` + `web-design-guidelines` + `canvas-design`, avoiding `591 KB` of overlapping markdown.
3. **`Agent-Skills-for-Context-Engineering`:** Included the 8 operational skills and skipped the 5 conceptual background essays (~`250 KB` saved).
4. **`anti-slop` & `humanizer`:** Lightweight `anti-slop` stays in `core` for automatic Phase 3/5/10/14 code/spec hygiene, while `humanizer` (`optional-communication`) handles detailed 24-pattern Wikipedia prose editing and can be disabled anytime via `disabled.skills`.
