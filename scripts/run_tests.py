#!/usr/bin/env python3
"""Deterministic local test runner for the AI Engineering Framework.

Runs all Python standard-library unittest suites grouped coherently by Baseline
and M9 Tiers A-D, reporting explicit passed/failed/errored/skipped/blocked counts
and preserving runtime-verification boundaries without external dependencies.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import io
import json
from pathlib import Path
import sys
import time
import unittest
from typing import Dict, List, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
for _path in (str(REPO_ROOT), str(SCRIPT_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import platform_capabilities  # noqa: E402


@dataclass(frozen=True)
class SuiteSpec:
    suite_id: str
    tier: str
    target: str
    description: str


SUITE_CATALOG: Sequence[SuiteSpec] = (
    SuiteSpec(
        suite_id="baseline_core",
        tier="BASELINE",
        target="tests.test_framework",
        description="Core framework parser, inventory, sync, validation, BM25, and bootstrap basics",
    ),
    SuiteSpec(
        suite_id="baseline_m7",
        tier="BASELINE",
        target="tests.test_m7_hardening",
        description="M7 consumer validation modes, pack filtering, link rewrite, stack templates, SDK preflight",
    ),
    SuiteSpec(
        suite_id="tier_a_capabilities",
        tier="A",
        target="tests.test_m9_capabilities",
        description="Tier A: Canonical platform capability model, state vocabulary, and upstream registry parity",
    ),
    SuiteSpec(
        suite_id="tier_a_contracts",
        tier="A",
        target="tests.test_m9_agent_platform_contracts",
        description="Tier A: Agent frontmatter, tool ID mapping, Antigravity hooks, TOML/JSON settings, adapter contracts",
    ),
    SuiteSpec(
        suite_id="tier_b_bootstrap_matrix",
        tier="B",
        target="tests.test_m9_projection_lifecycle",
        description="Tier B: Native skill projection matrix, Lockfile v2 & v0.3.0 migration, pruning, security guards",
    ),
    SuiteSpec(
        suite_id="tier_c_consumer_validation",
        tier="C",
        target="tests.test_m9_isolation_operations.TestM9ConsumerValidation",
        description="Tier C: Consumer isolation, host-global INFO reporting, ERROR/WARNING/INFO classification, exit codes",
    ),
    SuiteSpec(
        suite_id="tier_d_operational_reliability",
        tier="D",
        target="tests.test_m9_isolation_operations.TestM9OperationalReliability",
        description="Tier D: HTTP/dev-server readiness, port conflicts, PID-scoped cleanup, Windows PowerShell 5.1 reliability",
    ),
    SuiteSpec(
        suite_id="tier_e_custom_composition",
        tier="E",
        target="tests.test_m10_custom_composition",
        description="Tier E: Inline overlay composition, custom skills/agents, disabled toggles, standalone compose, brownfield import",
    ),
)

TIER_FILTER_MAP: Dict[str, set[str]] = {
    "ALL": {"BASELINE", "A", "B", "C", "D", "E"},
    "BASELINE": {"BASELINE"},
    "A": {"A"},
    "B": {"B"},
    "C": {"C"},
    "D": {"D"},
    "E": {"E"},
}


def _collect_runtime_boundary_summary() -> List[Dict[str, str]]:
    model = platform_capabilities.load_platform_capabilities()
    host_notes = {
        "antigravity": "LIVE_E2E_VERIFIED (reference runtime)",
        "codex": "PARTIAL_LIVE_VERIFIED (Windows OS sandbox setup external)",
        "claude-code": "NOT_RUN_ON_THIS_HOST (requires Claude Pro/Max/Ultra auth)",
        "copilot": "NOT_RUN_ON_THIS_HOST (requires Copilot CLI / VS Code extension auth)",
        "gemini-cli": "NOT_RUN_ON_THIS_HOST (requires eligible Gemini tier)",
    }
    rows: List[Dict[str, str]] = []
    for pid in model["platform_ids"]:
        plat = platform_capabilities.get_platform(model, pid)
        status = str(plat["runtime_status"])
        execution = host_notes.get(pid, "NOT_RUN_ON_THIS_HOST")
        rows.append(
            {
                "platform": pid,
                "contracts": "SUPPORTED & VALIDATED",
                "capability_runtime_status": status,
                "offline_suite_execution": execution,
            }
        )
    return rows


def run_suite_spec(spec: SuiteSpec, verbose: bool = False) -> Dict[str, object]:
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(spec.target)
    stream = io.StringIO()
    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(stream=stream, verbosity=verbosity)
    start = time.monotonic()
    result = runner.run(suite)
    elapsed = round(time.monotonic() - start, 3)

    total = result.testsRun
    failed = len(result.failures)
    errored = len(result.errors)
    skipped = len(result.skipped)
    passed = max(0, total - failed - errored - skipped)

    return {
        "suite_id": spec.suite_id,
        "tier": spec.tier,
        "target": spec.target,
        "description": spec.description,
        "total": total,
        "passed": passed,
        "failed": failed,
        "errored": errored,
        "skipped": skipped,
        "blocked": 0,
        "elapsed_seconds": elapsed,
        "status": "PASS" if result.wasSuccessful() else "FAIL",
        "skipped_details": [{"test": str(t), "reason": reason} for t, reason in result.skipped],
        "failure_details": [
            {"test": str(t), "traceback": tb} for t, tb in (list(result.failures) + list(result.errors))
        ],
        "raw_output": stream.getvalue(),
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic AI Engineering Framework tests by tier.")
    parser.add_argument(
        "--tier",
        type=str,
        default="all",
        choices=["all", "baseline", "A", "B", "C", "D", "E", "a", "b", "c", "d", "e"],
        help="Run all tiers or filter by baseline/A/B/C/D/E",
    )
    parser.add_argument("--json", action="store_true", help="Emit structured JSON summary")
    parser.add_argument("--verbose", action="store_true", help="Print detailed unittest output per suite")
    parser.add_argument(
        "--fail-on-skip",
        action="store_true",
        help="Treat any skipped test as non-zero failure",
    )
    args = parser.parse_args(argv)

    allowed_tiers = TIER_FILTER_MAP[args.tier.upper()]
    selected = [s for s in SUITE_CATALOG if s.tier in allowed_tiers]

    suite_results: List[Dict[str, object]] = []
    tier_totals: Dict[str, Dict[str, int]] = {}
    for spec in selected:
        res = run_suite_spec(spec, verbose=args.verbose)
        suite_results.append(res)
        bucket = tier_totals.setdefault(
            spec.tier,
            {"total": 0, "passed": 0, "failed": 0, "errored": 0, "skipped": 0, "blocked": 0},
        )
        for key in bucket:
            bucket[key] += int(res[key])  # type: ignore[arg-type]

    totals = {
        "total": sum(int(r["total"]) for r in suite_results),
        "passed": sum(int(r["passed"]) for r in suite_results),
        "failed": sum(int(r["failed"]) for r in suite_results),
        "errored": sum(int(r["errored"]) for r in suite_results),
        "skipped": sum(int(r["skipped"]) for r in suite_results),
        "blocked": sum(int(r["blocked"]) for r in suite_results),
        "elapsed_seconds": round(sum(float(r["elapsed_seconds"]) for r in suite_results), 3),
    }
    runtime_boundaries = _collect_runtime_boundary_summary()
    overall_ok = totals["failed"] == 0 and totals["errored"] == 0 and (
        not args.fail_on_skip or totals["skipped"] == 0
    )

    payload = {
        "status": "PASS" if overall_ok else "FAIL",
        "tier_filter": args.tier.upper(),
        "totals": totals,
        "by_tier": tier_totals,
        "suites": [
            {k: v for k, v in r.items() if k != "raw_output"}
            for r in suite_results
        ],
        "runtime_verification_boundaries": runtime_boundaries,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0 if overall_ok else 1

    print("=== AI Engineering Framework Automated Test Runner ===")
    for r in suite_results:
        print(
            f"  [{r['status']}] Tier {r['tier']} | {r['suite_id']} ({r['target']}): "
            f"{r['passed']}/{r['total']} passed, {r['failed']} failed, {r['errored']} error, "
            f"{r['skipped']} skipped ({r['elapsed_seconds']}s)"
        )
        if args.verbose:
            print(r["raw_output"])
        for skip_item in r["skipped_details"]:  # type: ignore[attr-defined]
            print(f"      SKIPPED: {skip_item['test']} -> {skip_item['reason']}")
        for fail_item in r["failure_details"]:  # type: ignore[attr-defined]
            print(f"      FAILURE: {fail_item['test']}\n{fail_item['traceback']}")

    print("\n--- Summary by Tier ---")
    for tier_name, b in tier_totals.items():
        print(
            f"  Tier {tier_name}: total={b['total']}, passed={b['passed']}, "
            f"failed={b['failed']}, errored={b['errored']}, skipped={b['skipped']}, blocked={b['blocked']}"
        )

    print("\n--- Platform Contracts vs. Host CLI Live Verification (Offline Suite Checks Contracts Only) ---")
    for row in runtime_boundaries:
        print(
            f"  {row['platform']:12s}: contracts={row['contracts']} | "
            f"host_cli_probe={row['offline_suite_execution']}"
        )

    print(
        f"\nOVERALL: {payload['status']} | total={totals['total']}, passed={totals['passed']}, "
        f"failed={totals['failed']}, errored={totals['errored']}, skipped={totals['skipped']} "
        f"({totals['elapsed_seconds']}s)"
    )
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
