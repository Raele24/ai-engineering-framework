# Stage 2 Runbook: Technical Research, Architecture & ADRs (Phases 4–5)

**Canonical Reference:** [`docs/WORKFLOW.md`](../docs/WORKFLOW.md) (Phases 4, 5)  
**Responsible Role:** [`agents/software-architect.md`](../agents/software-architect.md)  
**Required Skills:** [`adr-writer`](../skills/core/adr-writer/SKILL.md), [`find-skills`](../skills/core/find-skills/SKILL.md), [`anti-slop`](../skills/core/anti-slop/SKILL.md)  
**Human Approval Gates:** `Gate-02` (Architecture & ADR Approval)  

---

## Step 1: Verify Upstream Handoff
1. Read `.framework-state/handoffs/phase-03-handoff.json` and confirm `docs/specs/03-specification.md` is approved (`Gate-01b`).

## Step 2: Phase 4 — Technical Research Spike
1. Evaluate candidate technical approaches, including a **Minimal / Standard Library Baseline** (Architectural Reduction principle).
2. Check license compatibility (must be compatible with project license), maintenance status, and host OS support (`docs/ENVIRONMENT_AUDIT.md`).
3. Document findings in `docs/architecture/04-research-spike.md`.

## Step 3: Phase 5 — Architecture & ADR Creation
1. Load [`skills/core/adr-writer/SKILL.md`](../skills/core/adr-writer/SKILL.md).
2. Create `docs/adr/ADR-xxxx-<slug>.md` using [`templates/ADR.template.md`](../templates/ADR.template.md) for any new dependency, schema change, or boundary contract.
3. Update `docs/ARCHITECTURE.md` with component boundaries and Mermaid data-flow diagrams.
4. Write `.framework-state/handoffs/phase-05-handoff.json` and pause at **`Gate-02`** for user approval.
