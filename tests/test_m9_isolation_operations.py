#!/usr/bin/env python3
"""M9-04 & M9-05 Tier C Consumer Validation & Tier D Operational Reliability Tests."""

from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import bootstrap  # noqa: E402
import readiness  # noqa: E402
import validate  # noqa: E402


def _free_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class TestM9ConsumerValidation(unittest.TestCase):
    """Tier C — Consumer & Host Isolation Validation (GAP-07 & validate.py modes)."""

    def test_01_unknown_projected_skill_untracked_warn_vs_unregistered_lock_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "consumer-iso"
            fake_home = root / "empty-home"
            fake_home.mkdir()

            bootstrap.bootstrap_project(
                target_dir=target,
                platforms=["antigravity"],
                optional_packs=[],
            )

            # Untracked local file inside .agents/skills -> WARNING, preserved
            extra = target / ".agents" / "skills" / "local-helper" / "SKILL.md"
            extra.parent.mkdir(parents=True)
            extra.write_text("# Local User Helper\n", encoding="utf-8")

            passed, report, warnings, _ = validate.run_validation_full(
                target, mode="consumer", home_dir=fake_home
            )
            self.assertTrue(passed, f"Unexpected error on untracked warning case: {report}")
            self.assertTrue(any("local-helper/SKILL.md" in w for w in warnings), warnings)

            # Projected skill entry in lockfile missing from canonical registry -> ERROR
            lock_path = target / ".framework-lock.json"
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            lock["managed_files"][".agents/skills/local-helper/SKILL.md"] = {
                "ownership": "platform_projected_skill",
                "skill": "local-helper",
                "source": "skills/core/local-helper/SKILL.md",
                "sha256": bootstrap.sha256_file(extra),
                "platforms": ["antigravity"],
            }
            lock_path.write_text(json.dumps(lock, indent=2), encoding="utf-8")

            passed2, report2, _, _ = validate.run_validation_full(
                target, mode="consumer", home_dir=fake_home
            )
            self.assertFalse(passed2)
            self.assertTrue(
                any("unregistered/stale skill 'local-helper'" in e for e in report2["consumer_state"]),
                report2["consumer_state"],
            )

    def test_02_missing_required_projection_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "missing-proj"
            bootstrap.bootstrap_project(target_dir=target, platforms=["claude-code"], optional_packs=[])
            (target / ".claude" / "skills" / "grill-me" / "SKILL.md").unlink()

            passed, report, _, _ = validate.run_validation_full(target, mode="consumer", home_dir=Path(tmp))
            self.assertFalse(passed)
            self.assertTrue(any(".claude/skills/grill-me/SKILL.md" in e for e in report["consumer_state"]))

    def test_03_stale_ownership_entry_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "stale-own"
            bootstrap.bootstrap_project(target_dir=target, platforms=["codex"], optional_packs=[])
            lock_path = target / ".framework-lock.json"
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            lock["projected_skills"]["claude-code"] = {
                "projection_root": ".claude/skills",
                "skills": ["grill-me"],
            }
            lock_path.write_text(json.dumps(lock, indent=2), encoding="utf-8")

            passed, report, _, _ = validate.run_validation_full(target, mode="consumer", home_dir=Path(tmp))
            self.assertFalse(passed)
            self.assertTrue(
                any("stale projected_skills platforms" in e for e in report["consumer_state"]),
                report["consumer_state"],
            )

    def test_04_modified_projected_file_emits_warning_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "modified-proj"
            bootstrap.bootstrap_project(target_dir=target, platforms=["antigravity"], optional_packs=[])
            proj_file = target / ".agents" / "skills" / "grill-me" / "SKILL.md"
            proj_file.write_text(proj_file.read_text(encoding="utf-8") + "\n# Local edit\n", encoding="utf-8")

            passed, report, warnings, _ = validate.run_validation_full(
                target, mode="consumer", home_dir=Path(tmp)
            )
            self.assertTrue(passed, f"Locally customized file should warn cleanly, not error: {report}")
            self.assertTrue(any(".agents/skills/grill-me/SKILL.md" in w for w in warnings), warnings)

    def test_05_invalid_platform_ownership_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "invalid-plat-own"
            bootstrap.bootstrap_project(target_dir=target, platforms=["antigravity"], optional_packs=[])
            lock_path = target / ".framework-lock.json"
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            lock["managed_files"][".agents/skills/grill-me/SKILL.md"]["platforms"] = ["claude-code", "bogus-cli"]
            lock_path.write_text(json.dumps(lock, indent=2), encoding="utf-8")

            passed, report, _, _ = validate.run_validation_full(target, mode="consumer", home_dir=Path(tmp))
            self.assertFalse(passed)
            errs = report["consumer_state"]
            self.assertTrue(any("unknown platform(s)" in e for e in errs), errs)
            self.assertTrue(any("inconsistent with" in e for e in errs), errs)

    def test_06_case_insensitive_collision_in_lockfile_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "case-collide"
            bootstrap.bootstrap_project(target_dir=target, platforms=["antigravity"], optional_packs=[])
            lock_path = target / ".framework-lock.json"
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            sample = dict(lock["managed_files"][".agents/skills/grill-me/SKILL.md"])
            lock["managed_files"][".agents/skills/Grill-Me/SKILL.md"] = sample
            lock_path.write_text(json.dumps(lock, indent=2), encoding="utf-8")

            passed, report, _, _ = validate.run_validation_full(target, mode="consumer", home_dir=Path(tmp))
            self.assertFalse(passed)
            self.assertTrue(
                any("case-insensitive path collision" in e for e in report["consumer_state"]),
                report["consumer_state"],
            )

    def test_07_global_skill_visibility_reported_as_info_never_modified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "consumer"
            fake_home = root / "fake-home"
            g_agents = fake_home / ".agents" / "skills" / "global-skill-one"
            g_claude = fake_home / ".claude" / "skills" / "global-skill-two"
            g_gemini = fake_home / ".gemini" / "config" / "skills" / "global-skill-three"
            g_codex = fake_home / ".codex" / "skills" / "global-skill-four"
            for d in (g_agents, g_claude, g_gemini, g_codex):
                d.mkdir(parents=True)
            sentinels = [
                (g_agents / "SKILL.md", "GLOBAL_SECRET_DO_NOT_TOUCH"),
                (g_claude / "SKILL.md", "GLOBAL_CLAUDE_SKILL"),
                (g_gemini / "SKILL.md", "GLOBAL_GEMINI_SKILL"),
                (g_codex / "SKILL.md", "GLOBAL_CODEX_SKILL"),
            ]
            before_hashes = {}
            for path, content in sentinels:
                path.write_text(content, encoding="utf-8")
                before_hashes[path] = bootstrap.sha256_file(path)

            bootstrap.bootstrap_project(target_dir=target, platforms=["antigravity"], optional_packs=[])
            passed, report, warnings, info = validate.run_validation_full(
                target, mode="consumer", home_dir=fake_home
            )
            self.assertTrue(passed, f"Harmless global skill must never cause error: {report}")
            self.assertEqual(warnings, [])
            for expected_tilde in ("~/.agents/skills", "~/.claude/skills", "~/.gemini/config/skills", "~/.codex/skills"):
                self.assertTrue(
                    any(expected_tilde in msg and "outside framework workspace control" in msg for msg in info),
                    f"Missing INFO visibility entry for {expected_tilde}: {info}",
                )
            for path, before_hash in before_hashes.items():
                self.assertEqual(bootstrap.sha256_file(path), before_hash)

    def test_08_three_tier_severity_classification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "severity-tiers"
            fake_home = root / "home"
            (fake_home / ".agents" / "skills" / "ext-skill").mkdir(parents=True)

            bootstrap.bootstrap_project(target_dir=target, platforms=["antigravity"], optional_packs=[])
            # Add untracked user note (WARNING) + missing projection (ERROR) + global dir (INFO)
            note = target / ".agents" / "skills" / "local-note.md"
            note.write_text("note", encoding="utf-8")
            (target / ".agents" / "skills" / "adr-writer" / "SKILL.md").unlink()

            passed, report, warnings, info = validate.run_validation_full(
                target, mode="consumer", home_dir=fake_home
            )
            self.assertFalse(passed)
            self.assertTrue(any("adr-writer/SKILL.md" in e for e in report["consumer_state"]))
            self.assertTrue(any("local-note.md" in w for w in warnings))
            self.assertTrue(any("~/.agents/skills" in i for i in info))

    def test_09_missing_required_file_and_invalid_ownership_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "missing-req"
            bootstrap.bootstrap_project(target_dir=target, platforms=["antigravity"], optional_packs=[])

            # Invalid ownership class in lockfile -> ERROR
            lock_path = target / ".framework-lock.json"
            lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
            lock_data["managed_files"]["AGENTS.md"]["ownership"] = "invented_class"
            lock_path.write_text(json.dumps(lock_data, indent=2), encoding="utf-8")

            passed1, rep1, _, _ = validate.run_validation_full(target, mode="consumer", home_dir=Path(tmp))
            self.assertFalse(passed1)
            self.assertTrue(any("invalid ownership" in e for e in rep1["consumer_state"]), rep1["consumer_state"])

            # Missing required consumer file (project.framework.json) -> ERROR
            (target / "project.framework.json").unlink()
            passed2, rep2, _, _ = validate.run_validation_full(target, mode="consumer", home_dir=Path(tmp))
            self.assertFalse(passed2)
            self.assertTrue(any("project.framework.json" in e for e in rep2["required_files"]), rep2["required_files"])

    def test_10_validate_cli_exit_codes_across_modes(self) -> None:
        val_py = REPO_ROOT / "scripts" / "validate.py"

        # 1. Framework mode exit 0
        fw_proc = subprocess.run(
            [sys.executable, str(val_py), "--root", str(REPO_ROOT), "--mode", "framework", "--json"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(fw_proc.returncode, 0, fw_proc.stderr)
        self.assertEqual(json.loads(fw_proc.stdout)["status"], "PASS")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "cli-consumer"
            fake_home = root / "fake-home"
            (fake_home / ".agents" / "skills" / "global-pack").mkdir(parents=True)
            bootstrap.bootstrap_project(target_dir=target, platforms=["antigravity"], optional_packs=[])

            # 2. Consumer warning + info (no errors) -> exit 0
            (target / ".agents" / "skills" / "local-warn.md").write_text("warn", encoding="utf-8")
            env = dict(os.environ)
            env["HOME"] = str(fake_home)
            env["USERPROFILE"] = str(fake_home)
            warn_proc = subprocess.run(
                [sys.executable, str(val_py), "--root", str(target), "--mode", "consumer", "--json"],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(warn_proc.returncode, 0, warn_proc.stderr)
            warn_payload = json.loads(warn_proc.stdout)
            self.assertEqual(warn_payload["status"], "PASS")
            self.assertGreater(warn_payload["total_warnings"], 0)
            self.assertGreater(warn_payload["total_info"], 0)

            # 3. Consumer error -> exit 1
            (target / ".agents" / "skills" / "grill-me" / "SKILL.md").unlink()
            err_proc = subprocess.run(
                [sys.executable, str(val_py), "--root", str(target), "--mode", "consumer", "--json"],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(err_proc.returncode, 1)
            err_payload = json.loads(err_proc.stdout)
            self.assertEqual(err_payload["status"], "FAIL")
            self.assertGreater(err_payload["total_errors"], 0)


class TestM9OperationalReliability(unittest.TestCase):
    """Tier D — Operational & Readiness Reliability (GAP-08 & Windows PowerShell 5.1)."""

    def test_09_powershell_51_syntax_compatibility_and_exit_propagation(self) -> None:
        runbook_text = (REPO_ROOT / "workflows" / "05-review-qa-and-security.md").read_text(encoding="utf-8")
        # PowerShell 5.1 does not support `&&`; verify runbook uses safe $LASTEXITCODE checks
        self.assertIn("$LASTEXITCODE", runbook_text)
        self.assertIn("Stop-Process -Id $proc.Id", runbook_text)
        self.assertNotIn("npm start &&", runbook_text)

        if sys.platform == "win32":
            ps_script = "python -c \"import sys; sys.exit(0)\"; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; python -c \"import sys; sys.exit(3)\"; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }"
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 3)

    def test_10_windows_paths_with_spaces_quoted_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spaced_target = Path(tmp) / "Consumer Project With Spaces"
            bootstrap.bootstrap_project(
                target_dir=spaced_target,
                platforms=["antigravity"],
                optional_packs=[],
            )
            passed, report, _, _ = validate.run_validation_full(
                spaced_target, mode="consumer", home_dir=Path(tmp)
            )
            self.assertTrue(passed, report)

            if sys.platform == "win32":
                val_py = REPO_ROOT / "scripts" / "validate.py"
                boot_py = REPO_ROOT / "scripts" / "bootstrap.py"
                ready_py = REPO_ROOT / "scripts" / "readiness.py"
                spaced_cli = Path(tmp) / "Bootstrapped Spaced App"
                ang_cfg = spaced_cli / "angular.json"
                cmd = (
                    f'& python "{boot_py}" --target "{spaced_cli}" --platforms antigravity --optional-packs none | Out-Null; '
                    f'if ($LASTEXITCODE -ne 0) {{ exit $LASTEXITCODE }}; '
                    f'& python "{val_py}" --root "{spaced_target}" --mode consumer --json; '
                    f'if ($LASTEXITCODE -ne 0) {{ exit $LASTEXITCODE }}'
                )
                proc = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-Command", cmd],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                payload = json.loads(proc.stdout)
                self.assertEqual(payload["status"], "PASS")
                self.assertTrue((spaced_cli / ".agents" / "skills" / "grill-me" / "SKILL.md").exists())

                ang_cfg.write_text(json.dumps({"projects": {"web": {"architect": {"serve": {"options": {"port": 4299}}}}}}), encoding="utf-8")
                bad_pkg = spaced_cli / "package.json"
                bad_pkg.write_text(json.dumps({"scripts": {"start": "ng serve"}}), encoding="utf-8")
                cfg_err_cmd = f'& python "{ready_py}" --package-json "{bad_pkg}"; if ($LASTEXITCODE -ne 0) {{ exit $LASTEXITCODE }}'
                cfg_proc = subprocess.run(["powershell.exe", "-NoProfile", "-Command", cfg_err_cmd], capture_output=True, text=True)
                self.assertEqual(cfg_proc.returncode, 2)

    def test_11_angular_config_derivation_and_http_readiness_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp) / "angular app"
            app_dir.mkdir()
            port = _free_local_port()

            angular_json = app_dir / "angular.json"
            angular_json.write_text(
                json.dumps({
                    "defaultProject": "web",
                    "projects": {
                        "web": {
                            "architect": {
                                "serve": {
                                    "options": {"port": port, "host": "127.0.0.1"}
                                }
                            }
                        }
                    },
                }),
                encoding="utf-8",
            )
            pkg_json = app_dir / "package.json"
            pkg_json.write_text(
                json.dumps({"scripts": {"start": f"ng serve --port {port} --host 127.0.0.1"}}),
                encoding="utf-8",
            )

            derived_a = readiness.derive_endpoint_from_angular_config(angular_json)
            derived_b = readiness.derive_endpoint_from_package_json(pkg_json)
            self.assertEqual(derived_a, f"http://127.0.0.1:{port}/")
            self.assertEqual(derived_b, f"http://127.0.0.1:{port}/")

            # Undeclared port fails explicitly (never invents ports)
            bad_angular = app_dir / "no-port.angular.json"
            bad_angular.write_text(json.dumps({"projects": {"web": {"architect": {"serve": {"options": {}}}}}}), encoding="utf-8")
            with self.assertRaises(readiness.ReadinessConfigError):
                readiness.derive_endpoint_from_angular_config(bad_angular)

            # Spawn local Python HTTP server after a short 0.25s startup delay
            proc, buf = readiness.start_owned_process(
                [
                    sys.executable,
                    "-c",
                    f"import time, http.server; time.sleep(0.25); http.server.HTTPServer(('127.0.0.1', {port}), http.server.SimpleHTTPRequestHandler).serve_forever()",
                ],
                cwd=app_dir,
            )
            try:
                res = readiness.wait_for_http_ready(
                    url=derived_a, proc=proc, output_buffer=buf, timeout_seconds=5.0, poll_interval=0.1
                )
                self.assertTrue(res["ready"], res)
                self.assertEqual(res["status"], "READY")
            finally:
                readiness.stop_owned_process(proc)
            self.assertIsNotNone(proc.poll())

    def test_12_readiness_timeout_reported_cleanly(self) -> None:
        unused_port = _free_local_port()
        with tempfile.TemporaryDirectory() as tmp:
            proc, buf = readiness.start_owned_process(
                [sys.executable, "-c", "import time; time.sleep(5)"],
                cwd=Path(tmp),
            )
            try:
                res = readiness.wait_for_http_ready(
                    url=f"http://127.0.0.1:{unused_port}/",
                    proc=proc,
                    output_buffer=buf,
                    timeout_seconds=0.35,
                    poll_interval=0.1,
                )
                self.assertFalse(res["ready"])
                self.assertEqual(res["status"], "TIMEOUT")
            finally:
                readiness.stop_owned_process(proc)

    def test_13_compilation_failure_detected_before_timeout(self) -> None:
        unused_port = _free_local_port()
        with tempfile.TemporaryDirectory() as tmp:
            proc, buf = readiness.start_owned_process(
                [
                    sys.executable,
                    "-c",
                    "import sys; print('ERROR in src/app/app.ts:12:4 - error TS1005: ; expected'); sys.exit(1)",
                ],
                cwd=Path(tmp),
            )
            try:
                res = readiness.wait_for_http_ready(
                    url=f"http://127.0.0.1:{unused_port}/",
                    proc=proc,
                    output_buffer=buf,
                    timeout_seconds=10.0,
                    poll_interval=0.05,
                )
                self.assertFalse(res["ready"])
                self.assertEqual(res["status"], "COMPILATION_FAILED")
                self.assertLess(res["elapsed_seconds"], 2.0)
                self.assertIn("error TS1005", str(res["error"]))
            finally:
                readiness.stop_owned_process(proc)

    def test_14_process_ownership_stops_only_workflow_child(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            owned_proc, _ = readiness.start_owned_process(
                [sys.executable, "-c", "import time; time.sleep(10)"],
                cwd=Path(tmp),
            )
            unrelated_proc = subprocess.Popen(
                [sys.executable, "-c", "import time; time.sleep(10)"],
                cwd=tmp,
            )
            try:
                self.assertIsNone(owned_proc.poll())
                self.assertIsNone(unrelated_proc.poll())
                stopped = readiness.stop_owned_process(owned_proc)
                self.assertTrue(stopped)
                self.assertIsNotNone(owned_proc.poll())
                time.sleep(0.1)
                # Unrelated user process MUST still be alive
                self.assertIsNone(unrelated_proc.poll())
            finally:
                readiness.stop_owned_process(owned_proc)
                unrelated_proc.terminate()
                unrelated_proc.wait(timeout=5)

    def test_15_stage5_review_qa_security_boundaries_explicit(self) -> None:
        text = (REPO_ROOT / "workflows" / "05-review-qa-and-security.md").read_text(encoding="utf-8")
        self.assertIn("Required Inputs:", text)
        self.assertIn("Expected Outputs:", text)
        self.assertIn("BLOCKER", text)
        self.assertIn("Gate-Sec", text)
        self.assertIn("NOT_RUN", text)
        self.assertIn("BLOCKED", text)
        self.assertIn("Never", text)
        self.assertIn("AC-01..N", text)

    def test_16_port_conflict_process_exit_and_config_edge_cases(self) -> None:
        unused_port = _free_local_port()
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp) / "edge-app"
            app_dir.mkdir()

            # 1. EADDRINUSE port conflict detected immediately before timeout
            proc_conflict, buf_conflict = readiness.start_owned_process(
                [sys.executable, "-c", "import sys; print('Error: listen EADDRINUSE: address already in use :::4200'); sys.exit(1)"],
                cwd=app_dir,
            )
            try:
                res_conflict = readiness.wait_for_http_ready(
                    url=f"http://127.0.0.1:{unused_port}/",
                    proc=proc_conflict,
                    output_buffer=buf_conflict,
                    timeout_seconds=10.0,
                    poll_interval=0.05,
                )
                self.assertFalse(res_conflict["ready"])
                self.assertEqual(res_conflict["status"], "COMPILATION_FAILED")
                self.assertIn("EADDRINUSE", str(res_conflict["error"]))
                self.assertLess(res_conflict["elapsed_seconds"], 2.0)
            finally:
                readiness.stop_owned_process(proc_conflict)

            # 2. Premature exit without error pattern returns PROCESS_EXITED
            proc_crash, buf_crash = readiness.start_owned_process(
                [sys.executable, "-c", "import sys; print('starting...'); sys.exit(42)"],
                cwd=app_dir,
            )
            try:
                res_crash = readiness.wait_for_http_ready(
                    url=f"http://127.0.0.1:{unused_port}/",
                    proc=proc_crash,
                    output_buffer=buf_crash,
                    timeout_seconds=5.0,
                    poll_interval=0.05,
                )
                self.assertFalse(res_crash["ready"])
                self.assertEqual(res_crash["status"], "PROCESS_EXITED")
                self.assertEqual(res_crash["returncode"], 42)
            finally:
                readiness.stop_owned_process(proc_crash)

            # 3. Angular config override (0.0.0.0 -> localhost, ssl -> https) & invalid configs
            ang_cfg = app_dir / "angular.json"
            ang_cfg.write_text(
                json.dumps({
                    "projects": {
                        "web": {
                            "architect": {
                                "serve": {
                                    "options": {"port": 4200, "host": "0.0.0.0"},
                                    "configurations": {"secure": {"port": 4443, "ssl": True}},
                                }
                            }
                        }
                    }
                }),
                encoding="utf-8",
            )
            self.assertEqual(readiness.derive_endpoint_from_angular_config(ang_cfg), "http://localhost:4200/")
            self.assertEqual(
                readiness.derive_endpoint_from_angular_config(ang_cfg, configuration="secure"),
                "https://localhost:4443/",
            )
            with self.assertRaises(readiness.ReadinessConfigError):
                readiness.derive_endpoint_from_angular_config(app_dir / "missing.json")

            # 4. Readiness CLI exit codes: 2 on invalid config, 1 on bounded timeout
            ready_py = REPO_ROOT / "scripts" / "readiness.py"
            no_args = subprocess.run([sys.executable, str(ready_py)], capture_output=True, text=True)
            self.assertEqual(no_args.returncode, 2)
            timeout_cli = subprocess.run(
                [sys.executable, str(ready_py), "--url", f"http://127.0.0.1:{unused_port}/", "--timeout", "0.2", "--interval", "0.05", "--json"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(timeout_cli.returncode, 1)
            self.assertEqual(json.loads(timeout_cli.stdout)["status"], "TIMEOUT")

    def test_17_stop_owned_process_kill_fallback_on_terminate_timeout(self) -> None:
        fake_proc = mock.MagicMock()
        fake_proc.poll.return_value = None
        fake_proc.wait.side_effect = [subprocess.TimeoutExpired(cmd="fake", timeout=0.01), None]
        self.assertTrue(readiness.stop_owned_process(fake_proc, grace_seconds=0.01))
        fake_proc.terminate.assert_called_once()
        fake_proc.kill.assert_called_once()


if __name__ == "__main__":
    unittest.main()
