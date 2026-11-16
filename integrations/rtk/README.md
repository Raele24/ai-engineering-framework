# RTK (Rust Token Killer) Integration Guide (`integrations/rtk/`)

**Upstream Repository:** `https://github.com/rtk-ai/rtk`  
**License:** Apache-2.0  
**Installation Policy:** **Category B (Requires User Approval)** for global binary installation; **Category A (Repository-Local)** for fallback skill [`skills/optional/communication/rtk-cli/SKILL.md`](../../skills/optional/communication/rtk-cli/SKILL.md).

---

## 1. Overview

**RTK (Rust Token Killer)** is a single-binary Rust CLI proxy (`<10ms` overhead) that filters and compresses terminal command output by **60% to 90%** before it enters an AI coding agent's context window.

---

## 2. Windows Installation (Requires User Approval — Category B)

RTK is verified in the official Windows Package Manager (`winget`) catalog as `rtk-ai.rtk` (`v1.2.0`).

### Option 1: Install via WinGet (Recommended on Windows)
```powershell
winget install -e --id rtk-ai.rtk
```

### Option 2: Build from Official GitHub Source via Cargo
> **CRITICAL WARNING:** Do **NOT** run `cargo install rtk` — `rtk` on `crates.io` is an unrelated crate (*Rust Type Kit*). Always specify the official GitHub repository URL:
```powershell
cargo install --git https://github.com/rtk-ai/rtk --branch master rtk
```

### Post-Install Verification
```powershell
rtk --version
rtk gain
```

---

## 3. Platform Hook Configuration (Project-Level vs. Global)

- **Project-Level Usage (Recommended Default):** Agents follow [`skills/optional/communication/rtk-cli/SKILL.md`](../../skills/optional/communication/rtk-cli/SKILL.md), invoking `rtk <cmd>` when `rtk` is detected in `PATH` and automatically falling back to compact native flags (`git status -sb`, `pytest -q --tb=short`) when `rtk` is absent. This guarantees **100% portability** across developer machines that have not installed `rtk`.
- **Optional Global Agent Hook (`rtk init` — Category B):**
  - Claude Code / Gemini CLI / Codex users who install `rtk` locally can optionally run `rtk init` (or `rtk init --global`) to register transparent `PreToolUse` command rewriting. Never commit machine-specific absolute binary paths into repository settings.
