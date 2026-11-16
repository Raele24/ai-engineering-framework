# ADR-0003: Filesystem State Handoffs Over Conversational Memory

- **Status:** Accepted
- **Date:** 2026-11-16
- **Deciders:** Software Architect

## Context
Multi-phase and multi-agent workflows degrade rapidly when state is passed through conversational summarization (the "Telephone Game Problem", where ~50% of edge cases and negative constraints are lost across agent handoffs). Furthermore, external orchestration servers (such as Paperclip or database-backed state engines) add setup friction and violate the requirement that the framework operate standalone in any coding agent environment.

## Decision
Use the **local filesystem as the canonical state machine**:
1. Permanent phase deliverables are written to structured markdown/JSON files in `docs/specs/`, `docs/adr/`, and `docs/plans/`.
2. Ephemeral stage-transition metadata is written to `.framework-state/manifest.json` and `.framework-state/handoffs/phase-<NN>-handoff.json`, validated by `core/schemas/handoff-packet.schema.json`.
3. Downstream agents read upstream files directly from disk with a fresh context window.

## Consequences
### Positive
- Works natively across single-agent and multi-agent platforms with zero external servers or databases.
- Provides a complete, human-inspectable audit trail of every phase transition and decision.
- External orchestrators (LangGraph, Paperclip, CrewAI) can optionally plug in later by reading/writing the exact same `.framework-state/` files.

### Negative
- Requires agents to write a small JSON handoff file at phase boundaries.
