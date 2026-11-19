# Skill & Tool Installation Guide (`SKILL_INSTALLATION_GUIDE.md`)

**Project:** AI Engineering Framework (`ai-engineering-framework`)  
**Version:** `0.4.0`  
**Date:** `2026-11-19`  

---

## 1. Installation Policy Classification

Every skill and tool in the framework is governed by one of three installation policies:

- **Policy A — Repository-Local (Autonomous / Zero System Changes):**
  Skills, reference guides, offline CSV databases, and zero-dependency Python 3 standard-library scripts stored inside `skills/` and `integrations/`. Installed and updated in consumer projects via `python scripts/bootstrap.py`.
- **Policy B — External CLI / Global Hook (Requires Explicit User Approval):**
  System-wide binaries (`rtk-ai.rtk`, `GitHub.cli`), global IDE configurations, or global agent hooks (`rtk init --global`). Never executed without explicit user confirmation.
- **Policy C — Documentation-Only (Not Installed):**
  Tools evaluated during research that overlap with lighter primitives or require intrusive proxy infrastructure (e.g., `headroom-ai`, `hosted-agents`, `claudekit/design`).

---

## 2. Installing Repository-Local Skills into a Consumer Project (Policy A)

Use `scripts/bootstrap.py` to install core skills and selected optional skill packs into any target project without overwriting consumer-owned files. Installed skills are copied into canonical `skills/core/` + `skills/optional/<pack>/` (preserving `UPSTREAM_SKILL.md` attribution) and **automatically projected** into `.agents/skills/<name>/` (for Antigravity, Copilot, Codex, Gemini CLI) and `.claude/skills/<name>/` (for Claude Code), tracked in `.framework-lock.json` (`schema_version: "2.0.0"`):

```bash
# 1. Default Engineering Bootstrap (Core + Communication + Context Engineering + Agent Architecture = 18 skills)
python /path/to/ai-engineering-framework/scripts/bootstrap.py \
  --target /path/to/your-target-project \
  --platforms antigravity,copilot,claude-code,codex,gemini-cli

# 2. Core-Only Minimal Install (8 mandatory core skills)
python /path/to/ai-engineering-framework/scripts/bootstrap.py \
  --target /path/to/your-minimal-project \
  --platforms antigravity \
  --optional-packs none

# 3. Full-Stack / Angular Frontend Project (Add frontend-design pack, alias design-ui)
python /path/to/ai-engineering-framework/scripts/bootstrap.py \
  --target /path/to/your-angular-app \
  --optional-packs communication,context-engineering,agent-architecture,frontend-design \
  --stacks dotnet,node/angular

# 4. Public Docs / Marketing Portal (Add growth-media pack: seo-audit, ai-seo, content-strategy, pricing, brand-strategy, video-*)
python /path/to/ai-engineering-framework/scripts/bootstrap.py \
  --target /path/to/your-public-portal \
  --optional-packs all
```

### Available `--optional-packs` Values

| Pack ID | Skills Included | Default in `bootstrap.py` |
| :--- | :--- | :--- |
| *(Core — Always Installed)* | `grill-me`, `tdd-cycle`, `ponytail`, `adr-writer`, `graphify`, `agent-browser`, `find-skills`, `anti-slop` (`8`) | **Always On** |
| `communication` | `caveman`, `rtk-cli` (`2`) | **Enabled by Default** |
| `context-engineering` | `context-optimization`, `context-compression`, `filesystem-context`, `memory-systems` (`4`) | **Enabled by Default** |
| `agent-architecture` | `multi-agent-patterns`, `tool-design`, `evaluation`, `self-improvement-loops` (`4`) | **Enabled by Default** |
| `frontend-design` *(alias `design-ui`)* | `ui-ux-pro-max` (BM25 `search.py` + 28 CSVs), `angular-developer` (36 reference docs), `angular-new-app`, `web-design-guidelines`, `canvas-design` (`5`) | Opt-In |
| `growth-media` | `seo-audit`, `ai-seo`, `content-strategy`, `pricing`, `brand-strategy`, `video-lens`, `video-use` (`7`) | Opt-In |
| `none` / `all` | Core-only (`8` skills) or all `5` optional packs (`30` total skills) | CLI aliases |

---

## 3. External CLI Installations Requiring User Approval (Policy B)

The commands below modify host software or global user directories outside the repository. **Review and run them manually in Windows PowerShell (or approve the agent to execute them):**

### 3.1 RTK — Rust Token Killer (`rtk-ai/rtk` `v1.2.0`)
Compresses terminal outputs (`git`, `pytest`, `npm`, `cargo`, `docker`) by 60–90%.

```powershell
# Install official rtk-ai.rtk binary via Windows Package Manager (WinGet)
winget install -e --id rtk-ai.rtk --accept-source-agreements --accept-package-agreements

# Verify installation and view token savings dashboard
rtk --version
rtk gain
```
*(Note: If you choose not to install `rtk`, the framework's `rtk-cli` skill automatically falls back to compact native CLI flags with zero errors.)*

### 3.2 Graphify Optional Git Hooks & Platform Helpers (`graphify 0.9.48`)
`graphify 0.9.48` is already installed and verified on this host. For repositories with **$\ge 15$ files or $> 2,000$ LOC**, you can optionally install local Git hooks so the AST graph updates automatically after commits:

```powershell
Set-Location "/path/to/ai-engineering-framework"
graphify hook install
graphify hook status
```

---

## 4. Verifying Installed Skills and Provenance

Run the framework validator at any time to verify that all 33 skills in `skills/registry.json`, their `UPSTREAM_SKILL.md` snapshots, YAML frontmatter schemas, and platform adapters are intact:

```bash
# In the upstream framework repository:
python scripts/sync_adapters.py --check
python scripts/validate.py --mode framework
python scripts/run_tests.py --fail-on-skip

# In a bootstrapped consumer project:
python scripts/validate.py --mode consumer
```
