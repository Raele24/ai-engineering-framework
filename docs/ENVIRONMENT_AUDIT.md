# Environment and Capability Audit

**Project:** AI Engineering Framework (`ai-engineering-framework`)  
**Audit Date:** 2026-11-16  
**Auditor Role:** Technical Project Lead, Software Architect & DevOps Engineer  
**Status:** Verified against live host environment

---

## 1. Executive Summary

This document records the verified hardware, operating system, shell, runtime, version control, authentication, and AI agent capabilities of the host development environment prior to bootstrapping the **AI Engineering Framework**.

Every capability listed below was empirically tested via terminal inspection and Antigravity tool introspection. No capability is assumed from external documentation. No credentials, tokens, or secrets are recorded in this document.

---

## 2. Operating System and Shell Environment

| Component | Verified Value | Status | Notes |
| :--- | :--- | :--- | :--- |
| **Operating System** | Microsoft Windows NT `10.0.26300.0` (Win32NT, x64) | Verified | Windows 11 Pro/Enterprise build family |
| **Default Agent Shell** | Windows PowerShell Desktop `5.1.26100.9818` | Verified | Each `run_command` executes in an isolated session |
| **PowerShell Core (`pwsh`)** | Not installed (`CommandNotFoundException`) | Missing (Optional) | Scripts must remain compatible with PowerShell 5.1 or use Python |
| **POSIX Shell (Git Bash)** | Available via Git for Windows (`C:\Program Files\Git\bin\bash.exe`) | Verified | Usable for `.sh` validation and cross-platform hook testing |
| **OpenSSH Client** | `ssh.exe` `9.5.6.4` (`C:\WINDOWS\System32\OpenSSH\ssh.exe`) | Verified | Installed; no SSH keys present in `C:\Users\raele\.ssh` |
| **System Utilities** | `tar.exe` (`10.0.26100.9711`), `curl` (PowerShell alias / system binary) | Verified | Available in `PATH` |
| **Package Manager (OS)** | Windows Package Manager (`winget`) `v1.29.380` | Verified | Available for installing missing CLI tools with user approval |
| **Other OS Package Managers** | `choco`, `scoop` | Not Installed | Not required; `winget` is available |

---

## 3. Version Control and GitHub Access

### 3.1 Git Installation and Configuration

| Setting / Tool | Verified Value | Implication for Framework |
| :--- | :--- | :--- |
| **Git Binary** | `git version 2.50.1.windows.1` (`C:\Program Files\Git\cmd\git.exe`) | Modern Git with full worktree, sparse-checkout, and LFS support |
| **Git User Name** | `user.name=raele` (in `C:\Users\raele\.gitconfig`) | Commits can be authored immediately without additional setup |
| **Git User Email** | `user.email=giorcelli.rael@gmail.com` (in `C:\Users\raele\.gitconfig`) | Verified author identity configured |
| **Default Branch Config** | `init.defaultbranch=master` (system-level `gitconfig`) | Framework initialization must explicitly pass `git init -b main` |
| **Line Endings** | `core.autocrlf=true` | Repository requires a `.gitattributes` file to enforce `LF` for shell/config files |
| **Symlinks** | `core.symlinks=true` | Enabled in Git config; however, Windows symlinks may require Developer Mode/admin rights, so framework adapters should prefer file generation/sync over symlinks |
| **Credential Helper** | `credential.helper=manager` (Git Credential Manager) | Supports HTTPS authentication via Windows Credential Manager |

### 3.2 GitHub CLI (`gh`) and Authentication Status

| Check | Result | Classification |
| :--- | :--- | :--- |
| **GitHub CLI (`gh`)** | Installed: `gh version 2.104.0 (2026-11-12)` (`C:\Program Files\GitHub CLI\gh.exe`) | **Verified Installed** (`gh auth status` reports not logged in; requires interactive `gh auth login` in Category C before M5 remote repo creation) |
| **Windows Credential Store** | Cached entries exist for `git:https://github.com` and `git:https://Raele24@github.com` | **Verified** (GitHub account `Raele24` is cached for Git HTTPS operations) |
| **SSH Keys (`~/.ssh`)** | No SSH key pairs found in `C:\Users\raele\.ssh` | HTTPS via Git Credential Manager is the active transport |
| **Remote Repository Creation** | Cannot be executed via CLI until `gh` is installed and authenticated, or repo is created via GitHub web UI | **Category B / C** (Requires `gh` install + auth approval, or manual creation on GitHub) |

---

## 4. Workspace and Directory Layout

| Location | Path | Status | Notes |
| :--- | :--- | :--- | :--- |
| **Active IDE Workspace** | None attached at session start | Verified | Antigravity session started without an open workspace folder |
| **Default Scratch Root** | `C:\Users\raele\.gemini\antigravity\scratch` | Verified | Exists and was empty prior to bootstrap |
| **Proposed Bootstrap Path** | `D:\PROGETTI\ai-engineering-framework` | Active Target | Relocated from initial scratch workspace and verified via SHA-256 checksums |
| **Existing User Repo Root** | `D:\PROGETTI\` | Verified | Primary project root on host (`D:\PROGETTI\ai-engineering-framework` active) |

---

## 5. Runtimes, Languages, and Development Tools

| Tool / Runtime | Version | Path / Source | Status |
| :--- | :--- | :--- | :--- |
| **Python** | `3.13.14` | `C:\Users\raele\AppData\Local\Microsoft\WindowsApps\python.exe` | **Available & Verified** |
| **pip** | `26.1.2` | `C:\Users\raele\AppData\Local\Microsoft\WindowsApps\pip.exe` | **Available & Verified** (Global packages include `pydantic 2.13.5`, `PyYAML 6.0.3`, `fastapi`, `httpx`, `tree-sitter-*`, `graphifyy 0.9.48`) |
| **pipx** | `1.16.7` | Python package / CLI | **Available & Verified** (`graphify` and `graphifyy` `0.9.48` installed) |
| **uv** | Not installed | — | **Unsupported / Missing** (Standard `python -m venv` and `pip` available) |
| **Node.js** | `v24.12.0` | `C:\nvm4w\nodejs\node.exe` | **Available & Verified** |
| **npm / npx** | `11.6.2` | `C:\nvm4w\nodejs\npm.ps1` | **Available & Verified** |
| **pnpm** | `10.25.0` | `C:\nvm4w\nodejs\pnpm.ps1` | **Available & Verified** |
| **Graphify CLI** | `0.9.48` | `graphify` (`pipx` + `pip`) & `@graphy/core@5.0.0-alpha.0` | **Available & Verified** (Codebase knowledge graph & architecture analysis tool) |
| **VS Code CLI** | `1.146.0` (x64) | `C:\Users\raele\AppData\Local\Programs\Microsoft VS Code\bin\code.cmd` | **Available & Verified** |
| **Antigravity CLI** | `1.5.9` | `C:\Users\raele\AppData\Local\agy\bin\agy.exe` | **Available & Verified** |
| **.NET SDK (`dotnet`)** | Not installed | — | **Unsupported / Missing** |
| **Docker (`docker`)** | Not installed | — | **Unsupported / Missing** (Impacts local containerized runners such as Strix dynamic sandbox) |

---

## 6. AI Coding Agent Platforms on Host

The framework targets five primary platforms plus compatible environments. Below is the verified state of each platform on this machine:

| Target Platform | Local CLI / App Status | Local Config Directories Present | Verification Capability on This Host |
| :--- | :--- | :--- | :--- |
| **1. Google Antigravity** | **Installed & Active** (`agy 1.5.9`) | `C:\Users\raele\.gemini\config\` (skills, plugins, `mcp_config.json`) | **Full native execution & verification** (rules, skills, subagents, workflows, swarm, MCP, hooks) |
| **2. GitHub Copilot** | **VS Code `1.146.0` Installed** | Workspace `.github/` | **Full file/schema validation** of `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, `.github/prompts/*.prompt.md`, `.github/agents/*.agent.md` |
| **3. Claude Code** | CLI (`claude`) not in `PATH` | `C:\Users\raele\.claude\` (`backups/`, `sessions/`, `skills/`) | **Config & schema validation** of `CLAUDE.md`, `.claude/agents/*.md`, `.claude/commands/*.md`, `.claude/settings.json`, `.mcp.json`; live CLI execution requires installing `@anthropic-ai/claude-code` |
| **4. OpenAI Codex** | CLI (`codex`) not in `PATH` | None (`~/.codex` absent) | **Config & schema validation** of `AGENTS.md`, `.codex/config.toml`, `.agents/skills/*/SKILL.md`; live CLI execution requires installing `@openai/codex` |
| **5. Gemini CLI** | Standalone `gemini` CLI not in `PATH` | Shares `~/.gemini/` hierarchy | **Config & schema validation** of `GEMINI.md`, `.gemini/settings.json`, `.gemini/commands/*.toml`; live CLI execution requires installing `@google/gemini-cli` |
| **Portable Agent Skills** | Active | `C:\Users\raele\.agents\skills\` (`.skill-lock.json`) | **Verified** cross-agent skill store already present on host with 25+ skills |

---

## 7. Antigravity Host Capabilities Matrix

### 7.1 Available and Verified Capabilities (Category A Ready)

- **Filesystem Operations:** `read_file`, `write_file`, `edit_file` (full support for creating documentation, templates, schemas, scripts, and platform adapters in the project workspace).
- **Terminal & Process Execution:** `run_command` and `manage_task` (PowerShell 5.1, Python 3.13, Node.js 24, Git 2.50, Graphify 0.9.48).
- **Subagent Delegation:** `invoke_subagent`, `define_subagent`, `manage_subagents`, `send_message` with built-in `self`, `research`, `browser`, and `image-generator` subagents.
- **Multi-Agent Orchestration:**
  - `run_workflow`: Python-based programmatic agent orchestration (`agent`, `parallel`, `pipeline`, `phase`).
  - `swarm`: Shared message-board multi-agent collaboration with isolated (`branch` / `share`) or inherited workspaces.
- **Browser Automation:** Built-in `browser` subagent capable of navigating live web applications, inspecting DOM/UI state, and taking verified screenshots.
- **Web & Marketplace Discovery:** `search_web` and `search_marketplace`.
- **Architecture Knowledge Graph:** `graphify` (`0.9.48`) verified working for AST/concept extraction, community detection, and architectural drift checks.
- **Installed Host Skills (34+):** Includes `caveman`, `graphify`, `find-skills`, `stop-slop`, `humanizer`, `multi-agent-patterns`, `project-development`, `tool-design`, `evaluation`, `self-improvement-loops`, `context-fundamentals`, `context-optimization`, `context-compression`, `context-degradation`, `filesystem-context`, `memory-systems`, `hosted-agents`, `design`, `design-system`, `ui-styling`, `ui-ux-pro-max`, `slides`, `banner-design`, `brand`, `prompt-master`.

### 7.2 Available but Not Yet Configured Capabilities

- **GitHub CLI (`gh`):** Installable via `winget`, but not yet installed.
- **Project Git Repository:** Not yet initialized in `ai-engineering-framework` (pending Phase 1 review approval).
- **Playwright E2E Runner:** Node.js `v24.12.0` and `npx` are available, but `@playwright/test` and browser binaries are not installed in the workspace.
- **Pre-commit / Static Analysis Hooks:** Python and Git are available, but repository hooks are not yet configured.

### 7.3 Unsupported Capabilities in Current Environment

- **Docker-Dependent Tooling (e.g., Strix Dynamic Sandbox):** Docker Desktop / Docker Engine is not installed on the host (`docker : CommandNotFoundException`). Strix requires Docker for isolated dynamic penetration-testing containers; therefore, Strix can be documented and integrated as an **optional/conditional security runner** (and run in GitHub Actions where Ubuntu runners provide Docker), but cannot execute dynamic container scans locally until Docker is installed.
- **PowerShell 7 (`pwsh`) Specific Syntax:** Operators exclusive to PowerShell 7+ (such as pipeline chain operators `&&` and `||` or ternary `?:` in PowerShell scripts) will fail in Windows PowerShell 5.1. All local automation scripts should be authored in **Python 3** (with thin `.ps1` / `.sh` wrappers) for guaranteed portability.

### 7.4 Capabilities Requiring Authentication or Human Interaction

- **GitHub Remote Repository Provisioning:** Creating the public `Raele24/ai-engineering-framework` repository on GitHub and pushing commits requires explicit user approval (**Category B**) and, if using `gh`, interactive OAuth login (**Category C**) or web UI repo creation.
- **External Security / LLM API Keys:** Tools like Strix (`STRIX_LLM`, `LLM_API_KEY`) require user-supplied API keys (**Category C**) and explicit target authorization before execution.
- **System-Level Software Installation:** Running `winget install` (e.g., for `GitHub.cli` or `Docker.DockerDesktop`) modifies host software outside the workspace and requires user approval (**Category B**) plus potential Windows UAC confirmation (**Category C**).
