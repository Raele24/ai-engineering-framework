# Stage 5 Runbook: Code Review, QA & Security Validation (Phases 10–12)

**Canonical Reference:** [`AGENTS.md`](../AGENTS.md) & [`core/rules/engineering-principles.md`](../core/rules/engineering-principles.md) (Phases 10, 11, 12)  
**Responsible Roles:** [`code-reviewer`](../agents/code-reviewer.md), [`qa-engineer`](../agents/qa-engineer.md), [`security-engineer`](../agents/security-engineer.md)  
**Required Skills:** [`anti-slop`](../skills/core/anti-slop/SKILL.md), [`tdd-cycle`](../skills/core/tdd-cycle/SKILL.md), [`agent-browser`](../skills/core/agent-browser/SKILL.md)  
**Human Approval Gates:** `Gate-Sec` (Required before any active/dynamic security scan such as Strix)  

---

## Step 1: Phase 10 — Independent Code Review (`code-reviewer`)
1. Inspect `git diff` against `docs/specs/03-specification.md`, `docs/adr/ADR-*.md`, and [`quality/code-review-rubric.md`](../quality/code-review-rubric.md).
2. If `graphify` is installed, run `graphify update .` to verify no architectural drift or circular dependencies were introduced.
3. Write `.framework-state/10-review-report.md`. If any `BLOCKER` or `MAJOR` defect exists, return to Phase 9.

## Step 2: Phase 11 — Automated Testing (`qa-engineer`)
1. Execute full unit, integration, edge-case, and regression suites (`python -m unittest discover -s tests -v`, `pytest`, `npm test`, or `npx playwright test`).
2. For web UI flows, verify rendered DOM and interaction states using [`skills/core/agent-browser/SKILL.md`](../skills/core/agent-browser/SKILL.md).
3. Record results in `.framework-state/11-test-report.json`.

## Step 3: Phase 12 — Security Validation (`security-engineer`)
1. Run passive/static security checks (`python scripts/validate.py`, dependency audits, secret pattern checks in [`security/pre-commit-secrets.md`](../security/pre-commit-secrets.md)).
2. **Conditional Active Security Scan (Strix):** Only if requested by the user AND approved at **`Gate-Sec`** with a signed scope in [`security/strix-profile.yaml`](../security/strix-profile.yaml), execute authorized dynamic testing.
3. Write `.framework-state/12-security-report.md` and `.framework-state/handoffs/phase-12-handoff.json`.
