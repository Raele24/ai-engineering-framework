# Project Roadmap (`ROADMAP.md`)

**Version:** `0.7.1`  

---

## 1. Milestone Progression

```mermaid
flowchart LR
    V01["v0.1.0: Canonical Core & Adapters"] --> V03["v0.3.0: Consumer Bootstrap & Preflight"]
    V03 --> V031["v0.3.1: Lockfile v2 & Platform Parity"]
    V031 --> V04["v0.4.0: Inline Overlay, Custom Prompts/MCP & `aief` CLI"]
    V04 --> V05["v0.5.0: Isolated `.aief/` Layout & Zero-Collision Discovery"]
    V05 --> V06["v0.6.0: Interactive Setup Wizard, Monorepo Speed & Sandbox Hardening"]
    V06 --> V07["v0.7.0: .NET Backend & UI/Prompt Curated Skills"]
    V07 --> V08["v0.8.0+: Optional Registry Ecosystems (PyPI / npm / dotnet tool)"]
```

---

## 2. Release Progression

### `v0.1.0` — Canonical Foundation, Agents, Skills & Tooling *(Released)*
- Canonical 15-phase workflow (`docs/WORKFLOW.md`), 4 core rules (`core/rules/`), 4 JSON schemas (`core/schemas/`), 8 canonical roles (`agents/*.md`), portable skills (`skills/` + `skills/registry.json`), 6 stage runbooks (`workflows/`), 5 platform adapter suites (`adapters/`), CLI utilities (`bootstrap.py`, `validate.py`, `sync_adapters.py`), CI templates (`.github/`), unit tests, and Graphify integration (`graphify-out/`).

### `v0.3.0` — Consumer Bootstrap Hardening & Stack Preflight *(Released)*
- Consumer/framework validation modes (`--mode auto|framework|consumer`), optional skill pack filtering, stack `.gitignore` templates, and Windows user-space `DOTNET_ROOT` preflight.

### `v0.3.1` — Multi-Platform Adapter Parity & Lockfile `v2.0.0`
- Canonical declarative capability model (`core/platform-capabilities.json`, `scripts/platform_capabilities.py`) and dynamic `.agents/skills.json` sync.
- Native skill projections (`.agents/skills/`, `.claude/skills/`), Lockfile `v2.0.0` ownership/pruning/atomic writes, legacy `v0.3.0` migration + backup, and consumer-safe adapter overrides.
- Claude/Copilot read-only agent tool mappings, clean Claude/Gemini settings schemas, schema-valid opt-in Antigravity `hooks.json`, and stdlib `scripts/readiness.py` HTTP probe.

### `v0.4.0` — Custom Composition Engine, Prompts/MCP & `aief` CLI *(Released)*
- Autonomous consumer composition engine (`scripts/compose.py`) composing active rules + `.framework-custom/` overlays inline across all 5 platforms without per-prompt manual reminders.
- Granular `disabled.*` (`skills`, `agents`, `phases`, `gates`, `mechanisms`) and `customizations.*` (`overlayDir`, `promptInjectionMode`, `inlineMaxBytes`) controls.
- Custom project skills (`consumer_custom_skill`), custom/appended agents (`consumer_custom_agent` with read-only reviewer enforcement), custom slash prompts (`consumer_custom_prompt`), custom MCP servers (`consumer_custom_mcp` with secret guards), curated skills `session-handoff` / `i-have-adhd` / `humanizer` (`33/33` total), PEP 517 `aief` package + version-bump auto-release GitHub Action (`.github/workflows/release-on-version-bump.yml`), first-run brownfield instruction auto-import (`.framework-custom/imported/`), Angular/VS Code JSONC support, `pnpm`/`yarn` preflight, and `84/84` automated tests.

### `v0.5.0` — Isolated `.aief/` Layout & Brownfield Safety *(Released)*
- Isolated consumer runtime under `.aief/` (`config.json`, `lock.json`, `state/`, `custom/`, `core/`, `agents/`, `skills/`, `workflows/`, `scripts/`) keeping consumer roots limited to native platform touchpoints.
- Zero-collision brownfield validation scoped to `core/` and `optional/`, preserving pre-existing `skills/` and `.agents/rules/*.md`, `13` canonical specialist roles in `agents/`, plus Windows `MAX_PATH`-safe `bundle.zip` short-cache extraction (`86/86` automated checks).

### `v0.6.0` — Interactive Setup Wizard, Monorepo Speed & Sandbox Hardening *(Released)*
- Interactive pre-flight discovery and legacy migration wizard in `aief init` (`copy` / `move` / `skip` / `delete` per legacy entry file, duplicate content detection, external skill/rule unification, plus `--yes`, `--interactive`, `--no-import`).
- Pruned `os.walk` validation (`_iter_workspace_files`) for sub-second `pnpm` monorepo checks, nested `.vscode/*.json` JSONC support, `.aief/.gitignore` Python bytecode hygiene, and Windows sandbox-safe validation (`87/87` automated checks).

### `v0.7.0` — .NET Backend & UI/Prompt Curated Skills *(Released)*
- Added curated skills `prompt-master` (`communication`), `ui-styling` (`frontend-design`, `shadcn/ui` + Tailwind CSS with helper scripts), and the `backend-dotnet` *(alias `dotnet`)* optional pack (`dotnet-backend-patterns` + `dotnet-best-practices`), expanding the catalog to `37` skills across `6` optional packs.
- **`v0.7.1` *(Current Patch)*:** Scoped consumer JSON / disabled-skill workflow validation (`test_19`), clarified `.aief/custom/` overlay paths (`test_20`), decoupled `Independent Code Review (HARD GATE)` from the multi-file threshold and removed Antigravity-only leaks from non-Antigravity workspaces (`test_21`), plus updated `pipx --force` / `uvx --refresh` and IDE reload documentation (`90/90` automated tests).

### `v0.8.0`+ — Ecosystem Distribution *(Planned)*
- Optional PyPI Trusted Publishing activation (`PYPI_PUBLISH_ENABLED=true`) and thin `npx` / `dotnet tool` wrappers above the canonical Python engine.
- Helper commands (`aief bump`, `aief doctor`) and additional optional domain skill packs.
