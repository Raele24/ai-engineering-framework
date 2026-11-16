# Installation & Update Guide (`INSTALLATION.md`)

**Version:** `0.1.0`  

---

## 1. System Requirements

| Requirement | Minimum Version | Verified Host Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Operating System** | Windows 10/11, macOS 12+, Linux | Windows 11 (`10.0.26300`) | Cross-platform path & line-ending support |
| **Git** | `2.30+` | `2.50.1.windows.1` | Version control & diff inspection |
| **Python** | `3.10+` | `3.13.14` | Executes `bootstrap.py`, `validate.py`, `sync_adapters.py` |
| **Node.js** *(Optional)* | `20.0+` | `v24.12.0` | Optional `npx skills`, Playwright E2E, and MCP bridges |
| **Graphify** *(Recommended)* | `0.9+` | `0.9.48` | Codebase knowledge graph (`graphify .`) |
| **GitHub CLI** *(Optional)* | `2.40+` | `2.104.0` | Remote repository & PR automation |

---

## 2. Installing the Framework Repository Locally

Clone the canonical framework repository:

```bash
git clone https://github.com/Raele24/ai-engineering-framework.git
cd ai-engineering-framework
python scripts/validate.py
```

---

## 3. Bootstrapping the Framework into a Target Project

The framework includes a non-destructive installer (`scripts/bootstrap.py`) designed to initialize or update the framework inside any new or existing software repository.

### 3.1 Command Syntax

```bash
python scripts/bootstrap.py \
  --target <PATH_TO_TARGET_PROJECT> \
  [--platforms antigravity,copilot,claude-code,codex,gemini-cli] \
  [--profile full|standard|hotfix] \
  [--optional-packs communication,frontend-design,growth-media] \
  [--update] \
  [--dry-run]
```

### 3.2 How Non-Destructive Installation Works

`scripts/bootstrap.py` enforces **Tier Separation** so your project-specific files are never lost or overwritten:

1. **Dry-Run Preview (`--dry-run`):** Lists every file that would be created, updated, or skipped without writing to disk.
2. **Consumer-Owned Files (Tier 3 — Create-If-Missing Only):**
   - `project.framework.json`
   - `docs/specs/`, `docs/adr/`, `docs/plans/`, `docs/retrospectives/`
   - Existing `README.md`, `.gitignore`, or `LICENSE` files in the target project are **never overwritten**.
3. **Framework-Managed Files (Tier 1 & Tier 2 — Lockfile Tracked):**
   - Core rules (`core/rules/`), schemas (`core/schemas/`), canonical agents (`agents/`), core skills (`skills/core/`), workflows (`workflows/`), and platform adapters (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`, `.agents/`, `.claude/`, `.codex/`, `.gemini/`).
   - `bootstrap.py` writes `.framework-lock.json` recording the framework version and the SHA-256 checksum of every installed Tier 1/2 file.

---

## 4. Updating an Existing Project (`--update`)

When a newer version of the **AI Engineering Framework** is released, update your consumer project safely:

```bash
python /path/to/ai-engineering-framework/scripts/bootstrap.py \
  --target /path/to/your-project \
  --update
```

**Update Safety Protocol:**
- For each managed file, `bootstrap.py` compares the current file's SHA-256 hash on disk against the hash recorded in `.framework-lock.json` at install time.
- **Unmodified by user:** Safely updated to the new framework version.
- **Modified locally by user:** **Skipped automatically** (or written beside as `<filename>.framework-new`) with a clear warning so local customizations are never destroyed.

---

## 5. Post-Installation Verification

Inside either the framework repository or any bootstrapped project, run:

```bash
python scripts/validate.py
```

`validate.py` verifies:
1. Required directories and core files exist.
2. All JSON files (`core/schemas/*.json`, `skills/registry.json`, `project.framework.json`) parse cleanly.
3. All `agents/*.md` and `skills/*/*/SKILL.md` files contain valid YAML frontmatter matching canonical requirements.
4. Platform adapters (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`) are in sync with canonical sources.
5. Relative markdown links in documentation resolve to existing files.
6. Working tree files contain zero leaked private keys or high-entropy credential patterns.
