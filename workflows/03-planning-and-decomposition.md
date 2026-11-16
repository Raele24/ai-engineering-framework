# Stage 3 Runbook: Planning, Decomposition & Delegation (Phases 6–8)

**Canonical Reference:** [`docs/WORKFLOW.md`](../docs/WORKFLOW.md) (Phases 6, 7, 8)  
**Responsible Role:** [`agents/planner-orchestrator.md`](../agents/planner-orchestrator.md)  
**Required Skills:** [`find-skills`](../skills/core/find-skills/SKILL.md), [`anti-slop`](../skills/core/anti-slop/SKILL.md)  
**Human Approval Gates:** `Gate-03` (Implementation Plan Approval)  

---

## Step 1: Phase 6 — Project Planning
1. Read `docs/specs/03-specification.md` and `docs/adr/ADR-*.md`.
2. Author `docs/plans/06-implementation-plan.md` defining milestones, dependency order, rollback points, and the **Category A / B / C** task classification matrix.
3. Pause at **`Gate-03`** for human approval of the implementation plan.

## Step 2: Phase 7 — Atomic Task Decomposition
1. Break the approved plan into atomic TDD tasks in `docs/plans/07-task-backlog.json`.
2. Every task must specify: `task_id`, `title`, `spec_ac_refs`, `target_files`, `test_files`, `verification_command`, and `dependencies`.
3. Ensure parallel tasks have strictly disjoint `target_files`.

## Step 3: Phase 8 — Agent Assignment & Context Isolation
1. Write `.framework-state/08-assignments.json` assigning each task to `implementation-engineer` (or specialist roles) and listing the exact `SKILL.md` files to load.
2. Default to sequential execution; use parallel subagents/swarm workers (max 3–5 concurrent workers) only when tasks operate on disjoint file subtrees.
3. Write `.framework-state/handoffs/phase-08-handoff.json`.
