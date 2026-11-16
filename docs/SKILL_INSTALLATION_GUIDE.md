# Skill & Tool Installation Guide (`SKILL_INSTALLATION_GUIDE.md`)

**Project:** AI Engineering Framework (`ai-engineering-framework`)  
**Version:** `0.2.0`  
**Date:** 2026-11-16  

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

Use `scripts/bootstrap.py` to install core skills and selected optional skill packs into any target project without overwriting consumer-owned files:

```powershell
# 1. Default Engineering Bootstrap (Core + Communication + Context Engineering + Agent Architecture)
python D:\PROGETTI\ai-engineering-framework\scripts\bootstrap.py `
  --target D:\PROGETTI\your-target-project `
  --platforms antigravity,copilot,claude-code,codex,gemini-cli

# 2. Full-Stack / Angular Frontend Project (Add frontend-design pack: ui-ux-pro-max, angular-developer, etc.)
python D:\PROGETTI\ai-engineering-framework\scripts\bootstrap.py `
  --target D:\PROGETTI\your-angular-app `
  --optional-packs communication,context-engineering,agent-architecture,frontend-design

# 3. Public Docs / Marketing Portal (Add growth-media pack: seo-audit, ai-seo, content-strategy, pricing, video-*)
python D:\PROGETTI\ai-engineering-framework\scripts\bootstrap.py `
  --target D:\PROGETTI\your-public-portal `
  --optional-packs communication,context-engineering,frontend-design,growth-media
```

### Available `--optional-packs` Values

| Pack ID | Skills Included | Default in `bootstrap.py` |
| :--- | :--- | :--- |
| *(Core — Always Installed)* | `grill-me`, `tdd-cycle`, `ponytail`, `adr-writer`, `graphify`, `agent-browser`, `find-skills`, `anti-slop` | **Always On** |
| `communication` | `caveman`, `rtk-cli` | **Enabled by Default** |
| `context-engineering` | `context-optimization`, `context-compression`, `filesystem-context`, `memory-systems` | **Enabled by Default** |
| `agent-architecture` | `multi-agent-patterns`, `tool-design`, `evaluation`, `self-improvement-loops` | **Enabled by Default** |
| `frontend-design` | `ui-ux-pro-max` (with BM25 `search.py` + 28 CSVs), `angular-developer` (with 36 reference docs), `angular-new-app`, `web-design-guidelines`, `canvas-design` | Opt-In (`--optional-packs ...frontend-design`) |
| `growth-media` | `seo-audit`, `ai-seo`, `content-strategy`, `pricing`, `brand-strategy`, `video-lens`, `video-use` | Opt-In (`--optional-packs ...growth-media`) |

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
Set-Location "D:\PROGETTI\ai-engineering-framework"
graphify hook install
graphify hook status
```

---

## 4. Verifying Installed Skills and Provenance

Run the framework validator at any time to verify that all 30 skills in `skills/registry.json`, their `UPSTREAM_SKILL.md` snapshots, YAML frontmatter schemas, and platform adapters are intact:

```powershell
Set-Location "D:\PROGETTI\ai-engineering-framework"
python scripts/sync_adapters.py --check
python scripts/validate.py
python -m unittest discover -s tests -v
```
