"""Tests for deploy helpers and CI deploy contract.

These cover the failure mode that broke Deploy: a single Docker Hub TLS
timeout aborted the whole SSH session with no retries.
"""

from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import sys
import textwrap
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
DEPLOY = REPO / "deploy"
LIB_SH = DEPLOY / "lib.sh"
CI_DEPLOY = DEPLOY / "ci-deploy.sh"
RESTART = DEPLOY / "restart.sh"
FULL_RESTART = DEPLOY / "full-restart.sh"
COMPOSE = DEPLOY / "docker-compose.yml"
WORKFLOW = REPO / ".github" / "workflows" / "ci-cd.yml"


def _find_bash() -> str | None:
    """Prefer a real bash that can read the Windows filesystem (Git Bash)."""
    candidates: list[str] = []
    if env := os.environ.get("BASH"):
        candidates.append(env)
    if sys.platform == "win32":
        candidates.extend(
            [
                r"C:\Program Files\Git\bin\bash.exe",
                r"C:\Program Files\Git\usr\bin\bash.exe",
            ]
        )
    which = shutil.which("bash")
    if which:
        # Skip the Windows Store / WSL launcher — it cannot see C:\ paths.
        if sys.platform == "win32" and which.lower().endswith(r"\system32\bash.exe"):
            pass
        else:
            candidates.append(which)

    seen: set[str] = set()
    for cand in candidates:
        if not cand or cand in seen:
            continue
        seen.add(cand)
        if not Path(cand).is_file() and not shutil.which(cand):
            continue
        try:
            r = subprocess.run(
                [cand, "-c", "echo ok"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if r.returncode == 0 and "ok" in r.stdout:
                return cand
        except (FileNotFoundError, OSError):
            continue
    return None


BASH = _find_bash()
requires_bash = pytest.mark.skipif(BASH is None, reason="usable bash (e.g. Git Bash) is required")


def _bash(script: str, *, cwd: Path | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    assert BASH is not None
    merged = os.environ.copy()
    if env:
        merged.update(env)
    lib = LIB_SH.as_posix()
    full = f'source "{lib}"\n{script}'
    return subprocess.run(
        [BASH, "-c", full],
        cwd=str(cwd or DEPLOY),
        env=merged,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


class TestDeployFilesExist:
    def test_required_scripts_present(self):
        for path in (LIB_SH, CI_DEPLOY, RESTART, FULL_RESTART, COMPOSE):
            assert path.is_file(), f"missing {path}"

    def test_scripts_have_shebang(self):
        for path in (CI_DEPLOY, RESTART, FULL_RESTART, LIB_SH):
            first = path.read_text(encoding="utf-8").splitlines()[0]
            assert first.startswith("#!"), f"{path.name} missing shebang"

    def test_ci_deploy_sources_lib(self):
        text = CI_DEPLOY.read_text(encoding="utf-8")
        assert "source" in text and "lib.sh" in text
        assert "compose_pull" in text
        assert "warmup_sandbox" in text
        assert "wait_for_health" in text
        assert "DOCKERHUB_USER" in text

    def test_restart_uses_retry_helpers(self):
        text = RESTART.read_text(encoding="utf-8")
        assert "compose_pull" in text
        assert "warmup_sandbox" in text
        assert "docker compose pull\n" not in text

    def test_full_restart_uses_retry_helpers(self):
        text = FULL_RESTART.read_text(encoding="utf-8")
        assert "compose_pull" in text
        assert "warmup_sandbox" in text


@requires_bash
class TestBashSyntax:
    @pytest.mark.parametrize(
        "script",
        [LIB_SH, CI_DEPLOY, RESTART, FULL_RESTART],
        ids=lambda p: p.name,
    )
    def test_bash_n(self, script: Path):
        r = subprocess.run(
            [BASH, "-n", script.as_posix()],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        assert r.returncode == 0, r.stderr


@requires_bash
class TestUpsertEnv:
    def test_insert_and_update(self, tmp_path: Path):
        env_file = tmp_path / ".env"
        env_file.write_text("KEEP=1\nDOCKERHUB_USER=old\n", encoding="utf-8")
        r = _bash(
            textwrap.dedent(
                f"""
                upsert_env "{env_file.as_posix()}" DOCKERHUB_USER newuser
                upsert_env "{env_file.as_posix()}" SUB_PATH ""
                upsert_env "{env_file.as_posix()}" FRONTEND_URL "https://example.test"
                """
            )
        )
        assert r.returncode == 0, r.stderr
        body = env_file.read_text(encoding="utf-8")
        assert "KEEP=1" in body
        assert "DOCKERHUB_USER=newuser" in body
        assert "DOCKERHUB_USER=old" not in body
        assert re.search(r"^SUB_PATH=$", body, re.M)
        assert "FRONTEND_URL=https://example.test" in body

    def test_create_file_when_missing(self, tmp_path: Path):
        env_file = tmp_path / "fresh.env"
        r = _bash(f'upsert_env "{env_file.as_posix()}" FOO bar')
        assert r.returncode == 0, r.stderr
        assert env_file.read_text(encoding="utf-8").strip() == "FOO=bar"


@requires_bash
class TestRetryCmd:
    def test_succeeds_after_transient_failures(self, tmp_path: Path):
        counter = tmp_path / "n"
        counter.write_text("0", encoding="utf-8")
        flaky = tmp_path / "flaky.sh"
        flaky.write_text(
            textwrap.dedent(
                f"""\
                #!/usr/bin/env bash
                set -euo pipefail
                n=$(cat "{counter.as_posix()}")
                n=$((n + 1))
                echo "$n" > "{counter.as_posix()}"
                if (( n < 3 )); then
                  echo "fail $n" >&2
                  exit 1
                fi
                echo "ok $n"
                """
            ),
            encoding="utf-8",
        )
        flaky.chmod(0o755)
        r = _bash(f'retry_cmd 5 0 bash "{flaky.as_posix()}"')
        assert r.returncode == 0, r.stderr + r.stdout
        assert counter.read_text(encoding="utf-8").strip() == "3"
        assert "Retry" in r.stderr

    def test_fails_when_attempts_exhausted(self, tmp_path: Path):
        always_fail = tmp_path / "fail.sh"
        always_fail.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
        always_fail.chmod(0o755)
        r = _bash(f'retry_cmd 3 0 bash "{always_fail.as_posix()}"')
        assert r.returncode != 0
        assert "FAILED after 3 attempts" in r.stderr


@requires_bash
class TestWaitForHealth:
    def test_ok_when_endpoint_ready(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                if self.path == "/health/":
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"ok")
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, *_args):
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            r = _bash(f'wait_for_health "http://127.0.0.1:{port}/health/" 3')
            assert r.returncode == 0, r.stderr + r.stdout
            assert "Health check OK" in r.stdout
        finally:
            server.shutdown()

    def test_fails_quickly_with_patched_sleep(self):
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        r = subprocess.run(
            [
                BASH,
                "-c",
                textwrap.dedent(
                    f"""
                    source "{LIB_SH.as_posix()}"
                    sleep() {{ :; }}
                    wait_for_health "http://127.0.0.1:{port}/health/" 2
                    """
                ),
            ],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        assert r.returncode != 0
        assert "Health check failed" in r.stderr


class TestComposeContract:
    def test_app_images_use_pull_always(self):
        text = COMPOSE.read_text(encoding="utf-8")
        for name in ("backend", "nginx", "code-check-runner", "code-check-sandbox"):
            assert re.search(rf"(?m)^\s*{re.escape(name)}:\s*$", text), name
        assert text.count("pull_policy: always") >= 4

    def test_sandbox_is_noop_entrypoint(self):
        text = COMPOSE.read_text(encoding="utf-8")
        assert 'entrypoint: ["/bin/true"]' in text
        assert re.search(
            r"code-check-sandbox:.*?entrypoint: \[\"/bin/true\"\].*?restart: \"no\"",
            text,
            re.S,
        )

    def test_runner_depends_on_sandbox_completed(self):
        text = COMPOSE.read_text(encoding="utf-8")
        assert "service_completed_successfully" in text
        assert re.search(
            r"code-check-runner:.*?code-check-sandbox:.*?condition: service_completed_successfully",
            text,
            re.S,
        )


class TestWorkflowContract:
    def test_deploy_copies_lib_and_ci_script(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        assert "deploy/ci-deploy.sh" in text
        assert "deploy/lib.sh" in text

    def test_deploy_uses_ci_deploy_and_long_timeout(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        assert "command_timeout: 30m" in text
        assert "envs: DOCKERHUB_USER,FRONTEND_URL" in text
        match = re.search(
            r"name:\s*Deploy over SSH\n(.*?)(?:\n  [A-Za-z]|\Z)",
            text,
            re.S,
        )
        assert match, "Deploy over SSH step not found"
        block = match.group(1)
        assert "./ci-deploy.sh" in block
        assert "docker compose pull" not in block

    def test_deploy_layout_checks_new_files(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        assert "test -f /opt/bervinov-academy/ci-deploy.sh" in text
        assert "test -f /opt/bervinov-academy/lib.sh" in text

    def test_health_is_owned_by_ci_deploy(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        assert "name: Health check" not in text
        assert "wait_for_health" in CI_DEPLOY.read_text(encoding="utf-8")


@requires_bash
class TestCiDeployGuardrails:
    def test_requires_dockerhub_user(self, tmp_path: Path):
        stub_bin = tmp_path / "bin"
        stub_bin.mkdir()
        docker = stub_bin / "docker"
        docker.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        docker.chmod(0o755)
        env = os.environ.copy()
        env["PATH"] = f"{stub_bin.as_posix()}{os.pathsep}{env.get('PATH', '')}"
        env.pop("DOCKERHUB_USER", None)
        r = subprocess.run(
            [BASH, CI_DEPLOY.as_posix()],
            cwd=str(tmp_path),
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        assert r.returncode != 0
        assert "DOCKERHUB_USER" in (r.stderr + r.stdout)

    def test_ci_deploy_happy_path_with_stubs(self, tmp_path: Path):
        # On Windows PATH often has real docker.exe; override via exported
        # bash functions so the child ci-deploy.sh never hits the network.
        log = tmp_path / "docker.log"
        app = tmp_path / "app"
        app.mkdir()
        for name in ("lib.sh", "ci-deploy.sh"):
            (app / name).write_text((DEPLOY / name).read_text(encoding="utf-8"), encoding="utf-8")
        (app / "ci-deploy.sh").chmod(0o755)

        env = os.environ.copy()
        env["DOCKERHUB_USER"] = "testhub"
        env["FRONTEND_URL"] = "https://academy.example"
        env["DEPLOY_DOCKER_LOG"] = log.as_posix()

        wrapper = app / "run.sh"
        wrapper.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env bash
                set -euo pipefail
                docker() { echo "$*" >> "${DEPLOY_DOCKER_LOG}"; return 0; }
                curl() { return 0; }
                sleep() { :; }
                export -f docker curl sleep
                ./ci-deploy.sh
                """
            ),
            encoding="utf-8",
        )
        wrapper.chmod(0o755)

        r = subprocess.run(
            [BASH, wrapper.as_posix()],
            cwd=str(app),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert r.returncode == 0, r.stderr + r.stdout
        env_body = (app / ".env").read_text(encoding="utf-8")
        assert "DOCKERHUB_USER=testhub" in env_body
        assert "FRONTEND_URL=https://academy.example" in env_body
        assert "SUB_PATH=" in env_body
        calls = log.read_text(encoding="utf-8")
        assert "compose pull" in calls
        assert "compose run --rm --no-deps code-check-sandbox" in calls
        assert "compose up -d --remove-orphans" in calls
        assert "image prune -f" in calls
