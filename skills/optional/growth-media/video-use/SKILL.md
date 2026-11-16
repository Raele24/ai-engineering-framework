---
name: video-use
description: Programmatic capture and assembly of reproducible product demo videos, E2E Playwright video traces, and release walkthroughs.
version: "1.0.0"
tier: optional-growth
platforms: [antigravity, copilot, claude-code, codex, gemini-cli]
requires_tools: [run_command, write_file]
security_scope: workspace-write
---

# Video Use — Automated Demo & Walkthrough Recording Skill

## 1. Purpose
Automate the creation of reproducible product walkthroughs, release demos, and visual E2E evidence without manual screen recording.

## 2. Execution Protocol
1. **Storyboard Specification:** Define a deterministic sequence of viewport dimensions, routes, user actions, and pause durations in JSON/Markdown.
2. **Automated Capture:** Execute scripted browser flows using Playwright (`recordVideo` context option) or Remotion compositions.
3. **Artifact Output:** Save generated `.webm`/`.mp4` recordings under `docs/demos/` or `.framework-state/artifacts/`.

## 3. Validation Criteria
- Recording script executes reproducibly with exit code `0` and produces a non-empty video artifact matching the storyboard steps.
