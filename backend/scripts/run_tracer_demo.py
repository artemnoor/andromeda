"""Run and verify the complete contract-first tracer bullet locally or in CI."""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from subprocess import Popen
from typing import Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
FRONTEND_ROOT = REPO_ROOT / "frontend"
sys.path.insert(0, str(BACKEND_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bmstu_parser.tracer import DEFAULT_FIXTURE_DIR  # noqa: E402
from run_tracer_bullet import (  # noqa: E402
    TracerRunResult,
    configure_logging,
    run_ingest,
    selected_program_codes,
)

logger = logging.getLogger("tracer.demo")


class DemoError(RuntimeError):
    """Raised when a process or contract check fails during the demo."""


def default_database_url() -> str:
    return "sqlite:///backend/data/tracer-demo.db"


def resolve_database_url(database_url: str) -> str:
    """Make relative SQLite paths stable for ingestion and the child API process."""
    if not database_url.startswith("sqlite:///") or ":memory:" in database_url:
        return database_url
    raw_path = database_url.removeprefix("sqlite:///")
    database_path = Path(raw_path)
    if not database_path.is_absolute():
        base = REPO_ROOT if database_path.parts and database_path.parts[0] == "backend" else BACKEND_ROOT
        database_path = (base / database_path).resolve()
    return f"sqlite:///{database_path.as_posix()}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the complete BMSTU tracer bullet")
    parser.add_argument("--mode", choices=("fixture", "live"), default="fixture")
    parser.add_argument("--fixture-dir", type=Path, default=DEFAULT_FIXTURE_DIR)
    parser.add_argument("--database-url", default=default_database_url())
    parser.add_argument("--program-code", action="append", dest="program_codes")
    parser.add_argument("--program-id", action="append", dest="program_ids")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--api-port", type=int, default=8000)
    parser.add_argument("--frontend-port", type=int, default=5173)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--check", action="store_true", help="verify readiness and exit instead of keeping servers alive")
    parser.add_argument("--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"), default="INFO")
    return parser


def _http_get(url: str) -> bytes:
    request = Request(url, headers={"Accept": "application/json, text/html"})
    with urlopen(request, timeout=5.0) as response:
        if response.status != 200:
            raise DemoError(f"{url} returned HTTP {response.status}")
        return response.read()


def wait_for_http(url: str, process: Popen[bytes], timeout: float, label: str) -> None:
    deadline = time.monotonic() + timeout
    last_error = "no response"
    while time.monotonic() < deadline:
        return_code = process.poll()
        if return_code is not None:
            raise DemoError(f"{label} exited before readiness with code {return_code}")
        try:
            _http_get(url)
            logger.info("stage_ready name=%s url=%s", label, url)
            return
        except (DemoError, HTTPError, URLError, OSError, TimeoutError) as exc:
            last_error = str(exc)
            time.sleep(0.25)
    raise DemoError(f"Timed out waiting for {label} at {url}: {last_error}")


def _json_object(body: bytes, label: str) -> dict[str, object]:
    try:
        value = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DemoError(f"{label} did not return valid JSON") from exc
    if not isinstance(value, dict):
        raise DemoError(f"{label} did not return a JSON object")
    return value


def verify_compare(api_base_url: str, program_codes: Sequence[str]) -> None:
    if len(program_codes) != 2:
        raise DemoError("the tracer demo requires exactly two program codes")
    program_ids = tuple(f"program:{code}" for code in program_codes)
    query = quote(",".join(program_ids), safe="")
    body = _http_get(f"{api_base_url}/compare?programIds={query}")
    payload = _json_object(body, "compare endpoint")
    for key, expected_id in zip(("programA", "programB"), program_ids):
        program = payload.get(key)
        if not isinstance(program, dict) or program.get("id") != expected_id:
            raise DemoError(f"compare response has an invalid {key}")
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise DemoError("compare response contains no curriculum rows")
    logger.info("stage_verified name=compare programs=%s rows=%d", ",".join(program_ids), len(rows))


def _start_process(command: list[str], cwd: Path, env: dict[str, str], label: str) -> Popen[bytes]:
    logger.info("stage_start name=%s command=%s", label, " ".join(command))
    process_options: dict[str, object] = {}
    if os.name == "nt":
        process_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        process_options["start_new_session"] = True
    return subprocess.Popen(command, cwd=cwd, env=env, **process_options)


def _stop_process(process: Popen[bytes], label: str) -> None:
    if process.poll() is not None:
        return
    logger.info("stage_stop name=%s", label)
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        logger.warning("stage_kill name=%s", label)
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        process.wait(timeout=10)


def run_demo(args: argparse.Namespace) -> TracerRunResult:
    program_codes = selected_program_codes(args.program_codes, args.program_ids)
    database_url = resolve_database_url(args.database_url)
    fixture_dir = args.fixture_dir if args.fixture_dir.is_absolute() else (REPO_ROOT / args.fixture_dir).resolve()
    result = run_ingest(
        mode=args.mode,
        fixture_dir=fixture_dir,
        database_url=database_url,
        program_codes=program_codes,
    )
    logger.info("stage_complete name=database run_id=%s items=%d", result.run_id, result.curriculum_item_count)

    child_env = os.environ.copy()
    child_env["BMSTU_DATABASE_URL"] = database_url
    child_env["PYTHONPATH"] = os.pathsep.join(
        value for value in (str(BACKEND_ROOT / "src"), child_env.get("PYTHONPATH")) if value
    )
    api_base_url = f"http://{args.host}:{args.api_port}"
    frontend_url = f"http://{args.host}:{args.frontend_port}/"
    api_process: Popen[bytes] | None = None
    frontend_process: Popen[bytes] | None = None
    try:
        api_process = _start_process(
            [sys.executable, "-m", "uvicorn", "bmstu_parser.api.main:app", "--host", args.host, "--port", str(args.api_port)],
            REPO_ROOT,
            child_env,
            "api",
        )
        frontend_executable = "npm.cmd" if os.name == "nt" else "npm"
        frontend_process = _start_process(
            [frontend_executable, "run", "dev", "--", "--host", args.host, "--port", str(args.frontend_port)],
            FRONTEND_ROOT,
            child_env,
            "frontend",
        )
        wait_for_http(f"{api_base_url}/openapi.json", api_process, args.timeout, "api")
        wait_for_http(frontend_url, frontend_process, args.timeout, "frontend")
        verify_compare(api_base_url, program_codes)
        if not args.check:
            logger.info("demo_ready api=%s frontend=%s; press Ctrl-C to stop", api_base_url, frontend_url)
            while True:
                if api_process.poll() is not None:
                    raise DemoError("api exited while demo was running")
                if frontend_process.poll() is not None:
                    raise DemoError("frontend exited while demo was running")
                time.sleep(1.0)
        return result
    finally:
        if frontend_process is not None:
            _stop_process(frontend_process, "frontend")
        if api_process is not None:
            _stop_process(api_process, "api")


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging(args.log_level)
    try:
        result = run_demo(args)
    except KeyboardInterrupt:
        logger.info("demo_stopped_by_user")
        return 0
    except (DemoError, ValueError, OSError) as exc:
        logger.error("demo_failed error=%s", exc)
        return 1
    print(
        json.dumps(
            {
                "runId": result.run_id,
                "programIds": list(result.program_ids),
                "curriculumItemCount": result.curriculum_item_count,
                "sourceCount": result.source_count,
                "sourceHashes": list(result.source_hashes),
                "mode": args.mode,
                "check": args.check,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
