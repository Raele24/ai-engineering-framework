# Configuration Reference (`CONFIGURATION.md`)

**Version:** `0.3.0`  

---

## 1. Overview

The **AI Engineering Framework** separates configuration into three scopes:
1. **Project Configuration (`project.framework.json`):** Checked into the root of a consumer repository (Tier 3). Controls workflow profile, active platform adapters, stack templates, quality gates, and installed optional skill packs.
2. **Runtime Workflow State (`.framework-state/manifest.json`):** Tracks the active canonical workflow phase (`1..15`), active human approval gate (`Gate-01a`..`Gate-05`), and completed handoff packets (`.framework-state/handoffs/`). Initialized automatically by `scripts/bootstrap.py` and never overwritten on updates.
3. **Lockfile Metadata (`.framework-lock.json`):** Records installed `framework_version`, `platforms`, `optional_packs`, `stacks`, and SHA-256 hashes of framework-managed files to guarantee safe `--update` operations.

---

## 2. `project.framework.json` Schema & Options

```json
{
  "$schema": "./core/schemas/framework-config.schema.json",
  "frameworkVersion": "0.3.0",
  "projectName": "my-software-project",
  "workflowProfile": "standard",
  "enabledPlatforms": [
    "antigravity",
    "copilot",
    "claude-code"
  ],
  "stacks": [
    "dotnet",
    "node-angular"
  ],
  "optionalSkillPacks": {
    "communication": ["caveman", "rtk-cli"],
    "contextEngineering": [
      "context-optimization",
      "context-compression",
      "filesystem-context",
      "memory-systems"
    ],
    "agentArchitecture": [],
    "frontendDesign": [
      "ui-ux-pro-max",
      "angular-developer",
      "angular-new-app",
      "web-design-guidelines",
      "canvas-design"
    ],
    "growthMedia": []
  },
  "qualityGates": {
    "requireTddRedGreen": true,
    "requireIndependentCodeReview": true,
    "requireGraphifyCheck": true,
    "minimumTestCoveragePercent": 80
  },
  "security": {
    "enforcePreCommitSecretScan": true,
    "allowActiveSecurityTesting": false,
    "strixProfilePath": "security/strix-profile.yaml"
  },
  "paths": {
    "specsDir": "docs/specs",
    "adrDir": "docs/adr",
    "plansDir": "docs/plans",
    "retrospectivesDir": "docs/retrospectives",
    "stateDir": ".framework-state"
  }
}
```

### 2.1 Configuration Fields Reference

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `frameworkVersion` | `string` | `"0.3.0"` | SemVer version of the installed AI Engineering Framework |
| `projectName` | `string` | Folder name | Identifier used in handoff manifests and reports |
| `workflowProfile` | `"full"` \| `"standard"` \| `"hotfix"` | `"standard"` | Controls ceremony depth in `docs/WORKFLOW.md` |
| `enabledPlatforms` | `string[]` | All 5 platforms | Platforms configured by `scripts/bootstrap.py` and verified by `scripts/validate.py --mode consumer` |
| `stacks` | `string[]` | `[]` | Stack templates enabled (`"dotnet"`, `"node-angular"`, `"python"`) |
| `optionalSkillPacks.*` | `object` | Pack-dependent | Lists installed optional skills per pack (`communication`, `contextEngineering`, `agentArchitecture`, `frontendDesign`, `growthMedia`) |
| `qualityGates.requireTddRedGreen` | `boolean` | `true` | Requires failing test creation before implementation in Phase 9 |
| `qualityGates.requireIndependentCodeReview` | `boolean` | `true` | Requires Phase 10 review before Phase 13 release |
| `qualityGates.requireGraphifyCheck` | `boolean` | `true` | Uses `graphify` knowledge graph during architecture and review phases |
| `security.allowActiveSecurityTesting` | `boolean` | `false` | Must remain `false` unless explicit human approval (`Gate-Sec`) and target scope are configured |

---

## 3. Environment Variables & Secrets Policy

1. **Zero Secrets in Git:** Never place API keys, OAuth tokens, JWT signing keys, database passwords, or private URLs in `project.framework.json`, `appsettings.json`, or any tracked file.
2. **Variable Placeholders:** Always reference secrets via environment variables (`PILOT_JWT_KEY`, `${GITHUB_PERSONAL_ACCESS_TOKEN}`, `${STRIX_LLM_API_KEY}`).
