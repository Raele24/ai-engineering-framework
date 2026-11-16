# ADR-0001: Open-Source Licensing under Apache License 2.0

- **Status:** Accepted
- **Date:** 2026-11-16
- **Deciders:** Project Lead & Software Architect

## Context
The AI Engineering Framework is designed for open-source distribution and adoption by individual developers and enterprise engineering teams across commercial and open-source software repositories. We evaluated permissive open-source licenses, primarily **Apache License 2.0** and **MIT License**.

## Decision
Adopt **Apache License, Version 2.0** (`LICENSE`) as the official project license.

## Consequences
### Positive
- **Explicit Patent Grant (Section 3):** Protects downstream adopters and contributors from patent litigation related to contributed scripts, workflows, or tooling.
- **Enterprise Readiness:** Preferred by corporate legal and compliance teams for foundational engineering frameworks.
- **Contribution Clarity (Section 5):** Automatically covers inbound contributions under Apache 2.0 without requiring a separate Contributor License Agreement (CLA) infrastructure at launch.
- **Permissive Downstream Use:** Consumer projects bootstrapped with the framework can remain proprietary or use any license for their own application code.

### Negative
- Slightly longer license text than MIT (`LICENSE` file is ~200 lines vs. ~20 lines).

## Compliance
`LICENSE` contains the full official Apache 2.0 text, and `README.md` documents the license choice and rationale.
