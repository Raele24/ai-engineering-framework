# ADR-0002: Single Canonical Core with Thin Platform Adapters

- **Status:** Accepted
- **Date:** 2026-11-16
- **Deciders:** Software Architect

## Context
AI coding platforms (GitHub Copilot, Google Antigravity, Claude Code, OpenAI Codex, Gemini CLI) use different configuration files, directory conventions, and frontmatter schemas (`.github/copilot-instructions.md`, `GEMINI.md`, `CLAUDE.md`, `AGENTS.md`, `.claude/agents/`, `.agents/skills/`, `.gemini/commands/*.toml`). Maintaining separate hand-edited rules across 5 platforms guarantees rule drift and contradictory agent behavior.

## Decision
1. Store all authoritative rules, workflow phases, agent role definitions, and skills once in canonical vendor-neutral directories (`core/`, `docs/WORKFLOW.md`, `workflows/`, `agents/`, `skills/`).
2. Generate and verify platform-specific entry points and adapter directories (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`, `adapters/*`) deterministically via `scripts/sync_adapters.py`.
3. Enforce zero adapter drift in `scripts/validate.py` and CI.

## Consequences
### Positive
- Zero rule duplication; one edit in `core/rules/` or `agents/` propagates to all 5 platforms via `python scripts/sync_adapters.py`.
- Adding a 6th platform requires only a new adapter mapping in `scripts/sync_adapters.py` without changing the core workflow.

### Negative
- Contributors must run `python scripts/sync_adapters.py` after modifying canonical rules or roles (enforced automatically by `validate.py` and CI).
