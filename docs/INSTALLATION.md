# Installation & Update Guide (`INSTALLATION.md`)

**Version:** `0.3.0`  

---

## 1. System Requirements

| Requirement | Minimum Version | Verified Host Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Operating System** | Windows 10/11, macOS 12+, Linux | Windows 11 (`10.0.26300`) | Cross-platform path & line-ending support |
| **Git** | `2.30+` | `2.50.1.windows.1` | Version control & diff inspection |
| **Python** | `3.10+` | `3.13.14` | Executes `bootstrap.py`, `validate.py`, `sync_adapters.py`, `preflight.py` |
| **Node.js** *(Optional)* | `20.0+` | `v24.12.0` | Optional Angular/Node projects, Playwright E2E, and MCP bridges |
| **.NET SDK** *(Optional)* | `8.0+ / 10.0 LTS` | `10.0.404` | Optional .NET consumer projects (supports Windows user-space `DOTNET_ROOT`) |
| **Graphify** *(Recommended)* | `0.9+` | `0.9.48` | Codebase knowledge graph (`graphify .`) |
| **GitHub CLI** *(Optional)* | `2.40+` | `2.104.0` | Remote repository & PR automation |

---

## 2. Validating the Upstream Framework Repository

```bash
python scripts/validate.py --mode framework
python -m unittest discover -s tests -v
```

---

## 3. Bootstrapping the Framework into a Consumer Project (`scripts/bootstrap.py`)

The framework includes a deterministic, non-destructive installer (`scripts/bootstrap.py`) that initializes or updates the framework inside any new or existing consumer repository without requiring manual post-bootstrap edits.

### 3.1 Command Syntax

```bash
python scripts/bootstrap.py \
  --target <PATH_TO_TARGET_PROJECT> \
  [--platforms antigravity,copilot,claude-code,codex,gemini-cli] \
  [--profile full|standard|hotfix] \
  [--optional-packs none|all|communication,context-engineering,agent-architecture,design-ui,growth-media] \
  [--stacks dotnet,node/angular,python] \
  [--update] \
  [--dry-run]
```

### 3.2 Optional Skill Pack Filtering (`REC-02`)

`bootstrap.py` always installs the 8 mandatory core skills (`grill-me`, `tdd-cycle`, `ponytail`, `adr-writer`, `graphify`, `agent-browser`, `find-skills`, `anti-slop`) and filters all generated consumer files to match the `--optional-packs` selection:
1. **Consumer `skills/registry.json`:** Contains only the 8 core skills plus the skills belonging to the selected optional packs (preserving 100% of upstream attribution, license, source URL, and SHA-256 metadata).
2. **Consumer `AGENTS.md`:** Generates Section 4 (`Registered Skills`) with only the installed skills — zero dangling references to uninstalled packs.
3. **Consumer `agents/*.md`:** Filters `required_skills` in YAML frontmatter so agents only reference installed skills.
4. **Consumer `.agents/skills.json`:** Registers only `skills/core` and the installed `skills/optional/<pack>` directories.

*Supported pack names:* `communication`, `context-engineering`, `agent-architecture`, `frontend-design` (alias `design-ui`), `growth-media`, `none` (core-only), or `all`.

### 3.3 Antigravity & Platform Adapter Path Rewriting (`REC-03`)

When `bootstrap.py` copies adapter Markdown files from their upstream depth (`adapters/antigravity/rules/framework-core.md`, depth 3) into their consumer destination (`.agents/rules/framework-core.md`, depth 2), `bootstrap.rewrite_markdown_relative_links()` automatically rewrites relative Markdown link targets (`../../../AGENTS.md` $\rightarrow$ `../../AGENTS.md`) while preserving external URLs, anchors, fenced code blocks, and inline code spans. Every generated link resolves strictly inside the consumer repository root.

### 3.4 Stack-Specific Templates & Windows SDK Preflight (`REC-04`)

Passing `--stacks dotnet,node/angular,python` performs two non-destructive actions:
1. **Stack `.gitignore` Generation:**
   - If the consumer project has no `.gitignore`, creates `.gitignore` from `templates/stacks/{dotnet,node-angular,python}.gitignore`.
   - If the consumer project **already has a `.gitignore`**, the existing `.gitignore` is **never overwritten**; instead, `bootstrap.py` writes `.gitignore.framework-recommended` for manual review/merge.
2. **Environment Preflight & Windows `DOTNET_ROOT` Detection (`scripts/preflight.py` & `docs/ENVIRONMENT_PREFLIGHT.md`):**
   - Inspects `PATH`, `DOTNET_ROOT`, and Windows user-space `$HOME\.dotnet` without installing software automatically.
   - If `C:\Program Files\dotnet` contains only a runtime (`0` SDKs) while `$HOME\.dotnet` contains the `.NET SDK`, `preflight.py` reports `AVAILABLE_USER_SPACE` and prints the exact PowerShell session configuration:
     ```powershell
     $env:DOTNET_ROOT = "$HOME\.dotnet"
     $env:PATH = "$HOME\.dotnet;$env:PATH"
     ```

---

## 4. Non-Destructive Updates (`--update`)

```bash
python /path/to/ai-engineering-framework/scripts/bootstrap.py \
  --target /path/to/your-project \
  --optional-packs communication,context-engineering,design-ui \
  --update
```

- **Tier 3 Consumer-Owned Files (`project.framework.json`, `.framework-state/manifest.json`, `.gitignore`, `README.md`, `docs/specs/`, `docs/adr/`, `docs/plans/`):** Created if missing; **never overwritten** on subsequent runs or `--update`.
- **Tier 1 & 2 Framework-Managed Files:** Tracked by SHA-256 in `.framework-lock.json`. Unmodified files are updated; any file customized by the user (`current_hash != locked_hash`) is preserved (`skipped_modified`).

---

## 5. Framework vs. Consumer Validation Modes (`REC-01` — `scripts/validate.py`)

`scripts/validate.py` supports three modes via `--mode {auto,framework,consumer}`:

```bash
# Auto-detects mode based on repository markers
python scripts/validate.py --root /path/to/project

# Explicit consumer mode (does NOT require PROJECT_CHARTER.md, scripts/bootstrap.py, or scripts/sync_adapters.py)
python scripts/validate.py --root /path/to/consumer-project --mode consumer

# Explicit upstream framework mode
python scripts/validate.py --root /path/to/ai-engineering-framework --mode framework
```

In **`consumer` mode**, `validate.py` verifies:
- `project.framework.json`, `.framework-lock.json`, `.framework-state/manifest.json`, and `.framework-state/handoffs/*.json` schema integrity.
- Installed skills under `skills/` match `skills/registry.json`, `AGENTS.md`, `.agents/skills.json`, and `agents/*.md` `required_skills`.
- Platform adapter files exist for all `enabledPlatforms` and all relative Markdown links resolve inside the consumer repository root.
- Zero leaked private keys or API token patterns across the working tree.
