# Core Rule: Engineering Principles (`engineering-principles.md`)

**Rule ID:** `CORE-RULE-01`  
**Scope:** Always-On Across All Platforms  
**Source of Truth:** `core/rules/engineering-principles.md`  

---

## 1. Specification Before Implementation
1. Never write production application code for a new feature or architectural change before clarifying ambiguities (`Phase 2: Grill Me`) and documenting testable acceptance criteria (`Phase 3: Specification Creation`).
2. Every functional requirement must map to a deterministic `Given / When / Then` acceptance criterion (`AC-xx`).

## 2. Architectural Reduction & Simplicity
1. Prefer standard library primitives and existing repository conventions over adding new third-party dependencies.
2. Document every consequential architectural choice in an Architecture Decision Record (`docs/adr/ADR-xxxx.md`) before implementation.
3. When `graphify-out/graph.json` is present, query the knowledge graph (`graphify query`, `graphify path`) before performing broad file-tree scans.

## 3. Strict Test-Driven Development (TDD)
1. Follow the **Red $\rightarrow$ Green $\rightarrow$ Refactor** cycle in `Phase 9`:
   - **RED:** Write an automated test that reproduces the bug or verifies the target `AC-xx`, and confirm it fails.
   - **GREEN:** Write the minimal production code required to pass the test.
   - **REFACTOR:** Clean up duplication, types, and naming while keeping all tests green.
2. Never delete, weaken, or skip an existing test solely to make a build pass.

## 4. Independent Verification
1. Code review (`Phase 10`), QA (`Phase 11`), and security validation (`Phase 12`) must evaluate the actual Git diff and test execution output against the approved specification.
2. If an implementation fails the same test 3 consecutive times, trigger the **Circuit Breaker**: stop mutating code, revert broken uncommitted edits, and report the root cause.

## 5. High-Signal, Anti-Slop Communication
1. Keep all technical documentation, commit messages, PR descriptions, and code comments factual, concrete, and free of promotional AI filler (`skills/core/anti-slop/SKILL.md`).
2. Never alter exact file paths, CLI flags, code identifiers, error messages, or negations (`not`, `never`, `only`).
