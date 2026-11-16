# Phase 15 Retrospective: M7 Framework Hardening & Consumer Bootstrap (`RETRO-0002`)

- **Repository:** `D:\PROGETTI\ai-engineering-framework`
- **Version:** `v0.3.0`
- **Date:** `2026-11-16`

---

## 1. Objective & Outcome

Milestone **M7** hardened the AI Engineering Framework from `v0.2.0` to `v0.3.0` by resolving all four recommendations (`REC-01`..`REC-04`) discovered during `M6-Pilot` and verifying clean, zero-repair consumer bootstrapping in `D:\PROGETTI\ai-engineering-framework-m7-consumer`.

---

## 2. Key Technical Insights

1. **Decoupling Consumer Validation from Upstream Authoring Scripts (`M7-01`):**
   - Previously, `scripts/validate.py` imported `sync_adapters` at module load time and checked `REQUIRED_FOUNDATION_FILES` (`PROJECT_CHARTER.md`, `scripts/bootstrap.py`, `scripts/sync_adapters.py`). Embedding `parse_simple_frontmatter()` directly in `validate.py` and introducing `--mode {auto,framework,consumer}` made `validate.py` 100% self-contained in consumer projects.
2. **Holistic Skill Pack Filtering (`M7-02`):**
   - Filtering `skills/optional/<pack>/` directories alone is insufficient: consumer projects have four surfaces that reference skills (`skills/registry.json`, `AGENTS.md`, `agents/*.md` `required_skills`, and `.agents/skills.json`). Generating all four deterministically in `collect_managed_plan_bytes()` before computing `.framework-lock.json` SHA-256 hashes keeps `--update` idempotent while eliminating dangling references.
3. **Stage Runbook Link Portability (`M7-03`):**
   - Running `validate.py --mode consumer` against our new `test_m7_hardening.py` suite immediately caught that `workflows/01..06.md` linked to `../docs/WORKFLOW.md` (which is a framework-authoring document not copied into consumer projects). Updating those links to `../AGENTS.md` and `../core/rules/engineering-principles.md` resolved link validation across both framework and consumer workspaces.

---

## 3. Readiness for `v0.3.0`

All 14 M7 acceptance criteria are verified `PASS`. The framework is ready at `v0.3.0` for local commit on `main`.
