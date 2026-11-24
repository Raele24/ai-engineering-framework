# Installation & Update Guide (`INSTALLATION.md`)

**Version:** `0.7.1`  

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
# Zero-install run directly from latest GitHub `main` (with uvx --refresh)
uvx --refresh --from git+https://github.com/Raele24/ai-engineering-framework.git aief init .

# Or install / upgrade globally in isolation to latest `main` via pipx (--force refreshes same-version builds)
pipx install --force git+https://github.com/Raele24/ai-engineering-framework.git
aief init .                  # Interactive wizard on TTY (or --yes / non-TTY for zero-flag defaults)
aief init . --yes --no-import # Non-interactive bootstrap without legacy instruction auto-import
aief compose .               # Re-compose after editing .aief/custom/ or .aief/config.json
aief update .                # Non-destructively upgrade consumer framework files
aief validate . --mode consumer

# Pin a specific release tag if needed:
# pipx install --force git+https://github.com/Raele24/ai-engineering-framework.git@v0.7.1

# Or from PyPI once published (when vars.PYPI_PUBLISH_ENABLED == 'true')
uvx ai-engineering-framework init .
```

> [!NOTE]
> **Reload IDE / New Chat After Bootstrap or Update:** IDE extensions cache generated instructions (`AGENTS.md`, `.github/copilot-instructions.md`, `.agents/skills/`, `.github/agents/`) per window or chat session. After `aief init`, `aief update`, or `aief compose`, open a **new chat** or reload/restart the IDE (`Developer: Reload Window` in VS Code) so active agents pick up the updated files.

**Automated Release Workflow:** [`.github/workflows/release-on-version-bump.yml`](../.github/workflows/release-on-version-bump.yml) runs on every push to `main`: whenever `pyproject.toml`'s `project.version` produces a new `v<version>` tag not yet on GitHub, CI validates `90` tests + version parity, builds & smoke-tests the wheel, creates the annotated GitHub Release + SHA-256 checksums, and publishes to PyPI if OIDC Trusted Publishing (`PYPI_PUBLISH_ENABLED=true`) is enabled.

---

## 4. Direct Script Bootstrapper (`scripts/bootstrap.py`)

The framework includes a deterministic, non-destructive installer (`scripts/bootstrap.py`) that initializes or updates the framework inside any new or existing consumer repository without requiring manual post-bootstrap edits.

### 4.1 Command Syntax

```bash
# Zero-flag install (all 5 platforms, all 37 skills, auto-detected stacks)
python scripts/bootstrap.py <PATH_TO_TARGET_PROJECT>

# Full explicit syntax
python scripts/bootstrap.py \
  --target <PATH_TO_TARGET_PROJECT> \
  [--platforms antigravity,copilot,claude-code,codex,gemini-cli] \
  [--profile full|standard|hotfix] \
  [--optional-packs all|none|communication,context-engineering,agent-architecture,frontend-design,growth-media,backend-dotnet] \
  [--stacks auto|none|dotnet,node/angular,python] \
  [--update] \
  [--dry-run] \
  [--yes] \
  [--interactive] \
  [--no-import]
```

*(Note: `--optional-packs` accepts `frontend-design` (alias `design-ui`) and `backend-dotnet` (alias `dotnet`); `-y`/`--yes` skips the interactive TTY wizard and accepts defaults, `-i`/`--interactive` forces wizard prompts, and `--no-import` skips auto-importing legacy root AI instructions.)*

### 4.2 Optional Skill Pack Filtering

`bootstrap.py` always installs the 8 mandatory core skills (`grill-me`, `tdd-cycle`, `ponytail`, `adr-writer`, `graphify`, `agent-browser`, `find-skills`, `anti-slop`) and filters all generated consumer files to match the `--optional-packs` selection across `6` optional packs:
1. **Consumer `skills/registry.json`:** Contains only the 8 core skills plus the skills belonging to the selected optional packs (preserving 100% of upstream attribution, license, source URL, and SHA-256 metadata).
2. **Consumer `AGENTS.md`:** Generates Section 4 (`Active Skills`) with only the installed skills — zero dangling references to uninstalled packs.
3. **Consumer `agents/*.md`:** Filters `required_skills` in YAML frontmatter so agents only reference installed skills.
4. **Consumer `.agents/skills.json`:** Registers only `skills/core` and the installed `skills/optional/<pack>` directories.
5. **Native Platform Skill Projections:** Derived dynamically from `core/platform-capabilities.json`, `bootstrap.py` projects physical copies of installed skills into `.agents/skills/<skill-name>/` (when any `.agents/skills`-consuming platform is enabled) and `.claude/skills/<skill-name>/` (when `claude-code` is enabled), excluding `UPSTREAM_SKILL.md` and `__pycache__/` while keeping attribution in `skills/`.

*Supported pack names:* `all` *(default — all `37` skills across `6` optional packs + `8` core)*, `communication`, `context-engineering`, `agent-architecture`, `frontend-design` (alias `design-ui`), `growth-media`, `backend-dotnet` (alias `dotnet`), or `none` (core-only `8` skills).  
*CLI Defaults (when flags are omitted):* positional target or `--target`, all `5` platforms (`antigravity,copilot,claude-code,codex,gemini-cli`), `--profile standard`, `--optional-packs all` (`37` skills; disable unwanted items via `disabled.*` in `.aief/config.json` or legacy `project.framework.json`), `--stacks auto` (auto-detects `dotnet`, `node-angular`, `python`).  
*Stack Naming Note:* `bootstrap.py --stacks` accepts `node/angular` (normalizing it automatically to `node-angular`), whereas `scripts/preflight.py --stacks` and `.aief/config.json` (or legacy `project.framework.json`) use `node-angular`.

### 4.3 Adapter & Projected Skill Link Rewriting

When `bootstrap.py` relocates adapter Markdown files (e.g. `adapters/antigravity/rules/framework-core.md` $\rightarrow$ `.agents/rules/framework-core.md`) or projects skill files (e.g. `skills/core/find-skills/SKILL.md` $\rightarrow$ `.agents/skills/find-skills/SKILL.md`), `bootstrap.rewrite_markdown_relative_links()` rewrites relative Markdown links (`../../registry.json` $\rightarrow$ `../../../skills/registry.json`, `../../../AGENTS.md` $\rightarrow$ `../../AGENTS.md`) while preserving external URLs, anchors, fenced code blocks, and inline code spans. Relocated targets are verified to resolve inside the consumer workspace root. Consumer adapter overrides also suppress upstream-only references (`docs/WORKFLOW.md`, `scripts/sync_adapters.py`, `scripts/bootstrap.py`, `python -m unittest`).

### 4.4 Stack-Specific Templates & Windows SDK Preflight

Passing `--stacks dotnet,node/angular,python` performs two non-destructive actions:
1. **Stack `.gitignore` Generation:**
   - If the consumer project has no `.gitignore`, creates `.gitignore` from `templates/stacks/{dotnet,node-angular,python}.gitignore`.
   - If the consumer project **already has a `.gitignore`**, the existing `.gitignore` is **never overwritten**; instead, `bootstrap.py` writes `.gitignore.framework-recommended` for manual review/merge.
2. **Environment Preflight & Windows `DOTNET_ROOT` Detection (`.aief/scripts/preflight.py` & `.aief/ENVIRONMENT_PREFLIGHT.md`; legacy: `docs/ENVIRONMENT_PREFLIGHT.md`):**
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

- **Isolated Consumer Layout (`.aief/`):** New consumer installations place framework rules/agents/workflows/config/state (`core/`, `agents/`, `skills/registry.json`, `workflows/`, `templates/`, `quality/`, `security/`, `scripts/`, `adapters/antigravity/`, `config.json`, `lock.json`, `state/`, `custom/`, `.gitignore`, `ENVIRONMENT_PREFLIGHT.md`, `gitignore.recommended`) inside `.aief/`. Skill files live only once in native platform folders (`.agents/skills/` and `.claude/skills/` when enabled) without duplicating them inside `.aief/skills/`. Legacy `0.3.x`/`0.4.x` consumer layouts (`project.framework.json`, `.framework-lock.json`, `.framework-state/`) continue to be auto-detected and supported automatically on `--update` and validation.
- **Tier 3 Consumer-Owned Files (`.aief/config.json`, `.aief/custom/`, `.aief/state/manifest.json`, `.gitignore`, `README.md`, `docs/`, host `skills/`):** Created if missing inside `.aief/` (never creating empty `docs/*` directories at root in isolated mode); **never overwritten** on subsequent runs or `--update`.
- **Brownfield Auto-Import on First Bootstrap:** If a brownfield project already contains non-framework root instruction files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`) before the first bootstrap (no `.aief/lock.json`), `bootstrap.py` backs up their contents into `.aief/custom/imported/` and composes them inline into the new entry points so nothing is lost. Pre-existing project skills (`skills/<project>/SKILL.md`) and `.agents/rules/*.md` are preserved untouched outside `.aief/`.
- **Tier 1 & 2 Framework-Managed Files & Native Projections (Lockfile `v2.0.0`):** Tracked by explicit ownership class (`framework_managed`, `platform_projected_skill`, `consumer_custom_skill`, `consumer_custom_agent`), source path, active platform owners, and SHA-256 hash inside `.aief/lock.json`. Unmodified files are updated safely via two-phase atomic writes while preserving and re-composing `.aief/custom/` + `disabled.*` settings automatically; locally modified files are preserved (`skipped_modified`).
- **Migration from Legacy `v0.3.0` Lockfiles:** Running `--update` against a `v0.3.0` consumer validates the legacy lockfile, backs it up to `<stateDir>/lock-backups/framework-lock-v0.3.0.json`, reconstructs ownership safely, and migrates to `schema_version: "2.0.0"` without touching consumer-customized files (failing closed on corrupted/ambiguous lockfiles).
- **Capabilities, Composition & Operational Helpers Installed:** Consumer projects receive `.aief/core/platform-capabilities.json`, `.aief/scripts/compose.py` (standalone consumer composition CLI), `.aief/scripts/platform_capabilities.py`, and `.aief/scripts/readiness.py`.

---

## 6. Framework vs. Consumer Validation Modes (`scripts/validate.py`)

`scripts/validate.py` supports three modes via `--mode {auto,framework,consumer}`:

```bash
# Auto-detects mode based on repository markers
python scripts/validate.py --root /path/to/project

# Explicit consumer mode (does NOT require PROJECT_CHARTER.md, scripts/bootstrap.py, or scripts/sync_adapters.py)
python /path/to/consumer-project/.aief/scripts/validate.py --mode consumer

# Explicit upstream framework mode
python scripts/validate.py --root /path/to/ai-engineering-framework --mode framework
```

In **`consumer` mode**, `validate.py` verifies:
- `.aief/config.json`, `.aief/lock.json`, `.aief/state/manifest.json`, and `.aief/state/handoffs/*.json` schema integrity (or legacy root equivalents when auto-detected).
- Installed skills in `.agents/skills/` (or `.claude/skills/`) match `.aief/skills/registry.json`, `AGENTS.md`, `.agents/skills.json`, and `.aief/agents/*.md` `required_skills`, ignoring external host-app skills under root `skills/`.
- Platform adapter files exist for all `enabledPlatforms` and all relative Markdown links resolve inside the consumer repository root.
- Zero leaked private keys or API token patterns across the working tree.
