# M7 Validation & M6 Consistency Reconciliation Report (`docs/M7_VALIDATION_REPORT.md`)

- **Framework Repository:** `D:\PROGETTI\ai-engineering-framework` (`v0.3.0`)
- **Clean Consumer Validation Workspace (`M7-06`):** `D:\PROGETTI\ai-engineering-framework-m7-consumer`
- **Read-Only Reference Pilot (`M7-07`):** `D:\PROGETTI\ai-engineering-framework-pilot` (Unmodified)
- **Date:** `2026-11-16`

---

## 1. Automated Unit & Regression Test Suite Results (`M7-05`)

**Command:**
```powershell
python -m unittest discover -s tests -v
```

**Result:** `Ran 13 tests in 3.755s — OK (0 failures, 0 errors)`

| Test Case | Requirement Verified | Status |
| :--- | :--- | :---: |
| `test_01_frontmatter_parser` | YAML frontmatter parsing & digest computation | **PASS** |
| `test_02_canonical_agents_and_skills_inventory` | 8 canonical agents & 30 curated skills in upstream registry | **PASS** |
| `test_03_adapter_sync_check_passes` | Upstream `sync_adapters.py --check` zero drift | **PASS** |
| `test_04_full_repository_validation_passes` | Upstream `validate.py --mode framework` passes | **PASS** |
| `test_05_ui_ux_pro_max_offline_bm25_search_works` | Offline BM25 `search.py` execution for Angular stack | **PASS** |
| `test_06_bootstrap_creates_and_preserves_consumer_files` | Non-destructive Tier 3 & user-modified file preservation | **PASS** |
| `test_m7_01_validation_modes_framework_consumer_and_auto` | `framework`, `consumer`, and `auto` modes without upstream authoring files | **PASS** |
| `test_m7_01_consumer_validation_detects_invalid_and_incomplete_state` | Missing `manifest.json`, malformed handoff JSON, and secret leak detection | **PASS** |
| `test_m7_02_optional_pack_filtering_four_scenarios` | Scenarios 1 (`core-only`: 8 skills), 2 (`core+design-ui`: 13 skills), 3 (`core+context+agent`: 16 skills), 4 (`all`: 30 skills) | **PASS** |
| `test_m7_03_antigravity_adapter_path_rewriting_and_resolution` | Markdown link rewriting (`../../../` $\rightarrow$ `../../`), code/URL preservation, and root-escape rejection | **PASS** |
| `test_m7_04_stack_templates_gitignore_preservation_and_preflight` | Stack `.gitignore` creation vs `.gitignore.framework-recommended` preservation & preflight | **PASS** |
| `test_m7_05_bootstrap_repeatability_and_determinism` | Idempotent repeat runs, cross-directory SHA-256 determinism, and `--update` pack pruning | **PASS** |
| `test_m7_06_dotnet_sdk_detection_missing_and_userspace` | Windows user-space `DOTNET_ROOT` (`AVAILABLE_USER_SPACE`) and `MISSING` SDK detection | **PASS** |

---

## 2. Clean Consumer Bootstrap Validation (`M7-06`)

**Workspace:** `D:\PROGETTI\ai-engineering-framework-m7-consumer`

### 2.1 Scenario A — Core-Only Bootstrap + Stack Templates (`dotnet,node/angular`)
**Command:**
```powershell
python "D:\PROGETTI\ai-engineering-framework\scripts\bootstrap.py" `
  --target "D:\PROGETTI\ai-engineering-framework-m7-consumer" `
  --platforms "antigravity,copilot,claude-code" `
  --optional-packs "none" `
  --stacks "dotnet,node/angular"
```
**Output:**
- `Created: 68, Updated: 0, Unchanged: 0, Skipped/Modified: 0`
- `skills/registry.json`: `total_skills: 8` (`['grill-me', 'tdd-cycle', 'ponytail', 'adr-writer', 'graphify', 'agent-browser', 'find-skills', 'anti-slop']`)
- `.agents/skills.json`: `{"entries": [{"path": "skills/core"}]}`
- `.agents/rules/framework-core.md`: Rewritten links `../../AGENTS.md`, `../../core/rules/engineering-principles.md`, `../../core/rules/human-approval-gates.md`, `../../core/rules/context-handoff-protocol.md`
- `validate.py --mode consumer` & `--mode auto`: **`OVERALL STATUS: PASS (0 total error(s))`**

### 2.2 Scenario B — Non-Destructive Update with Selected Optional Packs (`communication,context-engineering,design-ui`)
**Command:**
```powershell
python "D:\PROGETTI\ai-engineering-framework\scripts\bootstrap.py" `
  --target "D:\PROGETTI\ai-engineering-framework-m7-consumer" `
  --platforms "antigravity,copilot,claude-code" `
  --optional-packs "communication,context-engineering,design-ui" `
  --stacks "dotnet,node/angular" `
  --update
```
**Output:**
- `Created: 104, Updated: 8, Unchanged: 60, Skipped/Modified: 0`
- `skills/registry.json`: `total_skills: 19`, `installed_optional_packs: ['communication', 'context-engineering', 'frontend-design']`
- `validate.py --mode consumer`: **`OVERALL STATUS: PASS (0 total error(s))`**
- `preflight.py --stacks dotnet,node/angular`:
  - `[AVAILABLE_USER_SPACE] dotnet`: Detected `C:\Users\raele\.dotnet` (`10.0.404`) and printed PowerShell `DOTNET_ROOT` export snippet.
  - `[AVAILABLE] node-angular`: Detected Node.js `v24.12.0` and npm on `PATH`.

---

## 3. M6-Pilot Read-Only Consistency & Functional Reconciliation (`M7-07`)

Read-only inspection of `D:\PROGETTI\ai-engineering-framework-pilot` (left 100% unmodified at commit `1bc6bd2`) resolved all three consistency questions:

### 3.1 Foreign Key Delete Behavior (`ON DELETE SET NULL` vs. `DeleteBehavior.Restrict`)
- **Actual Implementation (`backend/src/Pilot.Api/Data/PilotDbContext.cs:86-90`):**
  ```csharp
  entity.HasOne(w => w.AssignedUser)
        .WithMany()
        .HasForeignKey(w => w.AssignedUserId)
        .OnDelete(DeleteBehavior.SetNull)
        .HasConstraintName("FK_WorkOrders_Users_AssignedUserId");
  ```
- **Reconciliation:**
  - `PilotDbContext.cs:89` implements `OnDelete(DeleteBehavior.SetNull)`, matching `docs/FINAL_ARCHITECTURE_REVIEW.md` (`ON DELETE SET NULL` if a `Users` row were ever hard-deleted at the SQL level).
  - Application-level user deactivation (`PATCH /api/users/{id}/status-role`) performs a soft update (`Users.IsActive = false`) and there is no `DELETE /api/users/{id}` endpoint; therefore, historical `WorkOrders.AssignedUserId` values remain intact with `assignedUserIsActive: false` (`AC-13` / `IT11b`).
  - Only a prose bullet in `RETRO-0001-m6-pilot.md` misstated `DeleteBehavior.Restrict` instead of `DeleteBehavior.SetNull`.

### 3.2 Code-Review Change Summary vs. `10-review-report.md`
- **Reconciliation:**
  - During Phase 10 (`T-06`), the isolated `code-reviewer` subagent (`6e14f1b4-c314-44cd-b7b3-db52a6ab3b0a`) audited 48 files and issued an `APPROVED` verdict with `0 BLOCKER`, `0 MAJOR`, `0 MEDIUM`, `2 MINOR`, and `2 NIT` findings:
    1. `MINOR-1`: `work-orders.component.ts` Edit modal `<select>` did not render a dedicated `<option>` when a work order's existing historical assignee was inactive (`assignedUserIsActive === false`).
    2. `MINOR-2`: `WorkOrdersController.cs` `Create` checked `while (await _db.WorkOrders.AnyAsync(w => w.Code == code, ct))` before `SaveChangesAsync`, which could throw `DbUpdateException` under simultaneous requests hitting unique index `IX_WorkOrders_Code`.
    3. `NIT-1`: `app.spec.ts` `T04-03` had redundant `sessionStorage.setItem` lines prior to calling `auth.login()`.
    4. `NIT-2`: `styles.css` used `--color-border: rgba(255, 255, 255, 0.12)` vs `0.08` in `MASTER.md` for higher dark-mode contrast.
  - Immediately after the subagent report returned, `implementation-engineer` applied `MINOR-1` (`editingInactiveAssignee` signal + `<option>`), `MINOR-2` (3-attempt `DbUpdateException` retry loop in `WorkOrdersController.cs:164-176`), and `NIT-1` before executing Phase 11 QA (`task-444`), and recorded them as `[MINOR - RESOLVED]` / `[NIT - RESOLVED]` inside `.framework-state/10-review-report.md`.

### 3.3 Accurate Classification of M6 Automated Tests & Browser E2E Limitation
- **Exact Breakdown of the 41 M6 Automated Tests:**
  1. **Backend Unit Tests (`23` tests in `Pilot.Tests`):** Pure in-memory domain, password hashing, and JSON converter tests (`WorkOrderValidatorTests.cs`: `15`, `AuthAndPasswordTests.cs`: `4`, `UtcDateTimeContractTests.cs`: `4`).
  2. **Backend HTTP + SQL Server LocalDB Integration Tests (`11` test methods covering scenarios `IT01`..`IT17` in `ApiIntegrationTests.cs`):** Full ASP.NET Core HTTP pipeline tests via `WebApplicationFactory<Program>` backed by real per-test SQL Server LocalDB databases (`(localdb)\MSSQLLocalDB`).
  3. **Frontend Component, Interceptor & Service Unit/Integration Tests (`7` tests in `frontend/src/app/app.spec.ts`):** Executed via Angular `TestBed` + `HttpTestingController` (mocked HTTP transport) inside Vitest `v4.1.12`.
- **Explicit Browser-Level E2E Limitation:**
  - `M6-Pilot` did **not** execute a live browser-driven E2E test connecting a real Chromium instance against both `ng serve` (`http://localhost:4200`) and `Pilot.Api` (`http://localhost:5000`) simultaneously.
- **Smallest Practical Browser E2E Smoke Test Proposal:**
  - A single 30-line Playwright test (`e2e/pilot-smoke.spec.ts`) or Antigravity `browser` subagent runbook with 4 deterministic assertions:
    1. Navigate to `http://localhost:4200/login`, submit `admin@pilot.local` / `PilotAdmin!2026`, and assert redirect to `/dashboard`.
    2. Assert `.kpi-grid .card` count equals `5` and live SQL Server seeded count (`8`) renders.
    3. Navigate to `/work-orders`, click `+ New Work Order`, submit title `"E2E Smoke Test Order"`, and assert `"WO-1009"` appears in `table.data-table`.
    4. Click `Sign Out` and assert redirect to `/login`.
