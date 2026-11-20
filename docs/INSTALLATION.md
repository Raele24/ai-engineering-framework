# Installation & Update Guide (`INSTALLATION.md`)

**Version:** `0.4.0`  

---

## 1. System Requirements

| Requirement | Minimum Version | Purpose |
| :--- | :--- | :--- |
| **Operating System** | Windows 10/11, macOS 12+, Linux | Cross-platform path & line-ending support |
| **Git** | `2.30+` | Version control & diff inspection |
| **Python** | `3.11+` | Executes `aief` CLI, `bootstrap.py`, `compose.py`, `validate.py`, `sync_adapters.py`, `preflight.py` |
| **Node.js** *(Optional)* | `20.0+` | Optional Angular/Node projects, Playwright E2E, and MCP bridges |
| **.NET SDK** *(Optional)* | `8.0+ / 10.0 LTS` | Optional .NET consumer projects (supports Windows user-space `DOTNET_ROOT`) |
| **Graphify** *(Recommended)* | `0.9+` | Codebase knowledge graph (`graphify .`) |
| **GitHub CLI** *(Optional)* | `2.40+` | Remote repository & PR automation |

---

## 2. Validating the Upstream Framework Repository

```bash
python scripts/sync_adapters.py --check
python scripts/validate.py --mode framework
python scripts/run_tests.py --fail-on-skip
# Or via standard Python unittest discovery:
python -m unittest discover -s tests -v
```

---

## 3. Installing into Any Project (`aief` CLI or Direct `bootstrap.py`)

### 3.1 One-Command Packaged CLI (`uvx` / `pipx` / `pip`)
The framework ships standard PEP 517 metadata ([`pyproject.toml`](../pyproject.toml), [`setup.py`](../setup.py)) exposing the zero-dependency **`aief`** CLI ([`aief_cli/cli.py`](../aief_cli/cli.py)):

```bash
# Zero-install run directly from GitHub release tag (with uvx)
uvx --from git+https://github.com/Raele24/ai-engineering-framework.git aief init .

# Or install globally in isolation once via pipx
pipx install git+https://github.com/Raele24/ai-engineering-framework.git
aief init .                  # Bootstrap current project (all 5 platforms, 33 skills, auto stacks)
aief compose .               # Re-compose after editing .framework-custom/ or project.framework.json
aief update .                # Non-destructively upgrade framework files
aief validate . --mode consumer

# Or from PyPI once published (when vars.PYPI_PUBLISH_ENABLED == 'true')
uvx ai-engineering-framework init .
```

**Automated Release Workflow:** [`.github/workflows/release-on-version-bump.yml`](../.github/workflows/release-on-version-bump.yml) runs on every push to `main`: whenever `pyproject.toml`'s `project.version` produces a new `v<version>` tag not yet on GitHub, CI validates `84` tests + version parity, builds & smoke-tests the wheel, creates the annotated GitHub Release + SHA-256 checksums, and publishes to PyPI if OIDC Trusted Publishing (`PYPI_PUBLISH_ENABLED=true`) is enabled.

---

## 4. Direct Script Bootstrapper (`scripts/bootstrap.py`)

The framework includes a deterministic, non-destructive installer (`scripts/bootstrap.py`) that initializes or updates the framework inside any new or existing consumer repository without requiring manual post-bootstrap edits.

### 4.1 Command Syntax

```bash
# Zero-flag install (all 5 platforms, all 33 skills, auto-detected stacks)
python scripts/bootstrap.py <PATH_TO_TARGET_PROJECT>

# Full explicit syntax
python scripts/bootstrap.py \
  --target <PATH_TO_TARGET_PROJECT> \
  [--platforms antigravity,copilot,claude-code,codex,gemini-cli] \
  [--profile full|standard|hotfix] \
  [--optional-packs all|none|communication,context-engineering,agent-architecture,design-ui,growth-media] \
  [--stacks auto|none|dotnet,node/angular,python] \
  [--update] \
  [--dry-run]
```

### 4.2 Optional Skill Pack Filtering

`bootstrap.py` always installs the 8 mandatory core skills (`grill-me`, `tdd-cycle`, `ponytail`, `adr-writer`, `graphify`, `agent-browser`, `find-skills`, `anti-slop`) and filters all generated consumer files to match the `--optional-packs` selection:
1. **Consumer `skills/registry.json`:** Contains only the 8 core skills plus the skills belonging to the selected optional packs (preserving 100% of upstream attribution, license, source URL, and SHA-256 metadata).
2. **Consumer `AGENTS.md`:** Generates Section 4 (`Registered Skills`) with only the installed skills — zero dangling references to uninstalled packs.
3. **Consumer `agents/*.md`:** Filters `required_skills` in YAML frontmatter so agents only reference installed skills.
4. **Consumer `.agents/skills.json`:** Registers only `skills/core` and the installed `skills/optional/<pack>` directories.
5. **Native Platform Skill Projections:** Derived dynamically from `core/platform-capabilities.json`, `bootstrap.py` projects physical copies of installed skills into `.agents/skills/<skill-name>/` (when any `.agents/skills`-consuming platform is enabled) and `.claude/skills/<skill-name>/` (when `claude-code` is enabled), excluding `UPSTREAM_SKILL.md` and `__pycache__/` while keeping attribution in `skills/`.

*Supported pack names:* `all` *(default — all `33` skills)*, `communication`, `context-engineering`, `agent-architecture`, `frontend-design` (alias `design-ui`), `growth-media`, or `none` (core-only `8` skills).  
*CLI Defaults (when flags are omitted):* positional target or `--target`, all `5` platforms (`antigravity,copilot,claude-code,codex,gemini-cli`), `--profile standard`, `--optional-packs all` (`33` skills; disable unwanted items via `disabled.*` in `project.framework.json`), `--stacks auto` (auto-detects `dotnet`, `node-angular`, `python`).  
*Stack Naming Note:* `bootstrap.py --stacks` accepts `node/angular` (normalizing it automatically to `node-angular`), whereas `scripts/preflight.py --stacks` and `project.framework.json` use `node-angular`.

### 4.3 Adapter & Projected Skill Link Rewriting

When `bootstrap.py` relocates adapter Markdown files (e.g. `adapters/antigravity/rules/framework-core.md` $\rightarrow$ `.agents/rules/framework-core.md`) or projects skill files (e.g. `skills/core/find-skills/SKILL.md` $\rightarrow$ `.agents/skills/find-skills/SKILL.md`), `bootstrap.rewrite_markdown_relative_links()` rewrites relative Markdown links (`../../registry.json` $\rightarrow$ `../../../skills/registry.json`, `../../../AGENTS.md` $\rightarrow$ `../../AGENTS.md`) while preserving external URLs, anchors, fenced code blocks, and inline code spans. Relocated targets are verified to resolve inside the consumer workspace root. Consumer adapter overrides also suppress upstream-only references (`docs/WORKFLOW.md`, `scripts/sync_adapters.py`, `scripts/bootstrap.py`, `python -m unittest`).

### 4.4 Stack-Specific Templates & Windows SDK Preflight

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

## 5. Non-Destructive Updates (`--update`)

```bash
python /path/to/ai-engineering-framework/scripts/bootstrap.py \
  --target /path/to/your-project \
  --optional-packs communication,context-engineering,design-ui \
  --update
```

- **Tier 3 Consumer-Owned Files (`project.framework.json`, `.framework-custom/`, `.framework-state/manifest.json`, `.gitignore`, `README.md`, `docs/specs/`, `docs/adr/`, `docs/plans/`):** Created if missing; **never overwritten** on subsequent runs or `--update`.
- **Brownfield Auto-Import on First Bootstrap:** If a brownfield project already contains non-framework root instruction files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`) before the first bootstrap (no `.framework-lock.json`), `bootstrap.py` backs up their contents into `.framework-custom/imported/` and composes them inline into the new entry points so nothing is lost and automatic framework loading still activates across all enabled platforms.
- **Tier 1 & 2 Framework-Managed Files & Native Projections (Lockfile `v2.0.0`):** Tracked by explicit ownership class (`framework_managed`, `platform_projected_skill`, `consumer_custom_skill`, `consumer_custom_agent`), source path, active platform owners, and SHA-256 hash inside `.framework-lock.json`. Unmodified files are updated safely via two-phase atomic writes while preserving and re-composing `.framework-custom/` + `disabled.*` settings automatically; locally modified files are preserved (`skipped_modified`); obsolete or disabled projections are pruned only when ownership and unmodified hash are proven.
- **Migration from Legacy `v0.3.0` Lockfiles:** Running `--update` against a `v0.3.0` consumer validates the legacy lockfile, backs it up to `.framework-state/lock-backups/framework-lock-v0.3.0.json`, reconstructs ownership safely, and migrates to `schema_version: "2.0.0"` without touching consumer-customized files (failing closed on corrupted/ambiguous lockfiles).
- **Capabilities, Composition & Operational Helpers Installed:** Consumer projects receive `core/platform-capabilities.json`, `scripts/compose.py` (standalone consumer composition CLI), `scripts/platform_capabilities.py`, and `scripts/readiness.py` (stdlib bounded HTTP readiness check for Stage 5 E2E verification under Windows PowerShell `5.1+`).

---

## 6. Framework vs. Consumer Validation Modes (`scripts/validate.py`)

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
