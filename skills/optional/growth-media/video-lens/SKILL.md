---
name: video-lens
description: Multimodal analysis of recorded video files (bug reproductions, UI session replays, product demos) producing timestamped technical event logs.
version: "1.0.0"
tier: optional-growth
platforms: [antigravity, copilot, claude-code, codex, gemini-cli]
requires_tools: [read_file, run_command]
security_scope: read-only
---

# Video Lens — Technical Video & Session Replay Analysis Skill

## 1. Purpose
Extract actionable engineering diagnostics, UI state transitions, and bug reproduction steps from recorded video files (`.mp4`, `.webm`, `.mov`).

## 2. Platform Execution Mapping
- **Native Multimodal Platforms (Google Antigravity, Gemini CLI):** Inspect video directly via `read_file`.
- **Frame-Extraction Fallback (Copilot, Claude Code, Codex):** Use Python `opencv-python` (`cv2`) or `ffmpeg` to sample keyframe PNGs at scene changes (`1 fps` or diff threshold) into `.framework-state/video-frames/` and inspect extracted frames.

## 3. Validation Criteria
- Produces a chronological `[MM:SS.ms]` event table mapping observed UI actions to console/network symptoms and code locations.
