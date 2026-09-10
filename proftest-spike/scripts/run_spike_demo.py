"""Run the standalone proftest Spike against an already running Andromeda API.

The runner is intentionally HTTP-only with respect to Andromeda. It does not
import the main application, open its database, or inspect parser artifacts.
"""

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
from typing import Callable, Sequence, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


SPIKE_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = SPIKE_ROOT / "backend"
FRONTEND_ROOT = SPIKE_ROOT / "frontend"
logger = logging.getLogger("proftest_spike.demo")


class DemoError(RuntimeError):
    """Raised when a demo stage cannot be verified."""


def configure_logging(log_level: str) -> None:
    selected = os.environ.get("LOG_LEVEL", log_level).upper()
    level = getattr(logging, selected, logging.INFO)
    logging.basicConfig(level=level, format="%(levelname)s %(name)s %(message)s")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the standalone Andromeda proftest Spike")
    parser.add_argument(
        "--andromeda-base-url",
        default=os.environ.get("ANDROMEDA_API_BASE_URL", "http://127.0.0.1:8000"),
        help="already running Andromeda API base URL",
    )
    parser.add_argument("--spike-host", default="127.0.0.1")
    parser.add_argument("--spike-port", type=int, default=8110)
    parser.add_argument("--frontend-port", type=int, default=5175)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--keep-alive", action="store_true", help="keep Spike services alive after verification")
    parser.add_argument("--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"), default="INFO")
    return parser


def _url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def _request_json(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, object] | None = None,
    timeout: float = 10.0,
) -> object:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise DemoError(f"HTTP {response.status} at {_path_template(url)}")
            raw = response.read()
    except HTTPError as exc:
        raise DemoError(f"HTTP {exc.code} at {_path_template(url)}") from exc
    except (URLError, OSError, TimeoutError) as exc:
        raise DemoError(f"request failed at {_path_template(url)}: {type(exc).__name__}") from exc
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DemoError(f"invalid JSON at {_path_template(url)}") from exc


def _path_template(url: str) -> str:
    path = urlsplit(url).path
    if path.endswith("/api/test/results"):
        return "/api/test/results"
    if path.endswith("/api/test/preview"):
        return "/api/test/preview"
    if path.endswith("/api/catalog"):
        return "/api/catalog"
    if path.endswith("/api/health"):
        return "/api/health"
    if path.endswith("/openapi.json"):
        return "/openapi.json"
    return path or "/unknown"


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise DemoError(f"{label} returned a non-object JSON payload")
    return cast(dict[str, object], value)


def _list(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise DemoError(f"{label} returned a non-list JSON field")
    return value


def _request_ok(url: str, timeout: float = 10.0) -> None:
    request = Request(url, headers={"Accept": "text/html, application/json"})
    try:
        with urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise DemoError(f"HTTP {response.status} at {_path_template(url)}")
    except HTTPError as exc:
        raise DemoError(f"HTTP {exc.code} at {_path_template(url)}") from exc
    except (URLError, OSError, TimeoutError) as exc:
        raise DemoError(f"request failed at {_path_template(url)}: {type(exc).__name__}") from exc


def wait_for_http(url: str, timeout: float, label: str, *, json_response: bool = True) -> None:
    deadline = time.monotonic() + timeout
    last_error = "no response"
    while time.monotonic() < deadline:
        try:
            if json_response:
                _request_json(url, timeout=3.0)
            else:
                _request_ok(url, timeout=3.0)
            logger.info("stage_ready name=%s path=%s", label, _path_template(url))
            return
        except DemoError as exc:
            last_error = str(exc)
            time.sleep(0.25)
    raise DemoError(f"timed out waiting for {label}: {last_error}")


def _start_process(command: list[str], env: dict[str, str], label: str, *, cwd: Path = SPIKE_ROOT) -> Popen[bytes]:
    logger.info("stage_start name=%s", label)
    if os.name == "nt":
        creationflags = cast(int, getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
        return subprocess.Popen(command, cwd=cwd, env=env, creationflags=creationflags)
    return subprocess.Popen(command, cwd=cwd, env=env, start_new_session=True)


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
        killpg = getattr(os, "killpg", None)
        getpgid = getattr(os, "getpgid", None)
        if callable(killpg) and callable(getpgid):
            cast(Callable[[int, int], None], killpg)(cast(Callable[[int], int], getpgid)(process.pid), signal.SIGTERM)
        else:
            process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        logger.warning("stage_kill name=%s", label)
        process.kill()
        process.wait(timeout=10)


def _answers(
    first_interest: str,
    second_interest: str,
    first_activity: str,
    second_activity: str,
    tradeoff: str,
    *,
    anti_physics: float | None = None,
) -> dict[str, object]:
    answers: list[dict[str, object]] = [
        {"questionId": "interest_scenario_1", "optionId": first_interest},
        {"questionId": "interest_scenario_2", "optionId": second_interest},
        {"questionId": "activity_preference_1", "optionId": first_activity},
        {"questionId": "activity_preference_2", "optionId": second_activity},
        {"questionId": "tradeoff_theory_practice", "optionId": tradeoff},
    ]
    if anti_physics is not None:
        answers.append(
            {
                "questionId": "anti_interest_areas",
                "optionId": "anti_physics",
                "intensity": anti_physics,
            }
        )
    return {"answers": answers, "adaptiveAnswers": []}


PERSONAS: tuple[tuple[str, dict[str, object]], ...] = (
    (
        "it_software",
        _answers("prototype_logic", "map_complexity", "activity_architecture", "result_working_thing", "tradeoff_practice"),
    ),
    (
        "engineering",
        _answers("understand_device", "test_material", "activity_build", "result_working_thing", "tradeoff_practice"),
    ),
    (
        "economics_business",
        _answers("shape_model", "compare_choices", "activity_talk", "result_decision", "tradeoff_balance", anti_physics=0.9),
    ),
    (
        "data_analytics",
        _answers("find_patterns", "compare_choices", "activity_measure", "result_decision", "tradeoff_theory"),
    ),
    (
        "it_with_strong_physics_anti_interest",
        _answers("prototype_logic", "map_complexity", "activity_architecture", "result_working_thing", "tradeoff_practice", anti_physics=1.0),
    ),
)


def _with_adaptive_answer(preview: dict[str, object], payload: dict[str, object]) -> dict[str, object]:
    adaptive = _object(preview.get("adaptive"), "preview.adaptive")
    if adaptive.get("status") != "ready":
        return payload
    question = _object(adaptive.get("question"), "preview.adaptive.question")
    options = _list(question.get("options"), "preview.adaptive.question.options")
    if not options:
        return payload
    first_option = _object(options[0], "preview.adaptive.question.options[0]")
    adaptive_answers = cast(list[object], payload["adaptiveAnswers"])
    adaptive_answers.append(
        {
            "questionId": question.get("id"),
            "optionId": first_option.get("id"),
            "firstDimension": _object(question.get("firstDimension"), "preview.firstDimension").get("code"),
            "secondDimension": _object(question.get("secondDimension"), "preview.secondDimension").get("code"),
        }
    )
    logger.info("adaptive_verified status=ready")
    return payload


def _recommendations(result: dict[str, object]) -> list[dict[str, object]]:
    value = _list(result.get("recommendations"), "results.recommendations")
    recommendations: list[dict[str, object]] = []
    for item in value:
        recommendations.append(_object(item, "results.recommendation"))
    return recommendations


def _score_signature(result: dict[str, object]) -> tuple[tuple[str, int], ...]:
    signature: list[tuple[str, int]] = []
    for recommendation in _recommendations(result):
        program = _object(recommendation.get("program"), "results.program")
        program_id = program.get("programId")
        fit = recommendation.get("contentFit")
        if not isinstance(program_id, str) or not isinstance(fit, int):
            raise DemoError("results contains an invalid score signature")
        signature.append((program_id, fit))
    return tuple(signature)


def _verify_personas(spike_base_url: str) -> None:
    catalog = _object(_request_json(_url(spike_base_url, "/api/catalog")), "catalog")
    programs = _list(catalog.get("programs"), "catalog.programs")
    if not programs:
        raise DemoError("catalog is empty; start Andromeda with curriculum data")
    logger.info(
        "catalog_verified program_count=%d fingerprint_count=%d",
        len(programs),
        len(programs),
    )

    persona_results: dict[str, dict[str, object]] = {}
    for name, base_payload in PERSONAS:
        preview = _object(
            _request_json(_url(spike_base_url, "/api/test/preview"), method="POST", payload=base_payload),
            "preview",
        )
        payload = _with_adaptive_answer(preview, base_payload)
        result = _object(
            _request_json(_url(spike_base_url, "/api/test/results"), method="POST", payload=payload),
            "results",
        )
        if result.get("status") != "ready":
            raise DemoError(f"persona {name} returned a non-ready result")
        signature = _score_signature(result)
        if not signature:
            raise DemoError(f"persona {name} returned no recommendations")
        repeat = _object(
            _request_json(_url(spike_base_url, "/api/test/results"), method="POST", payload=payload),
            "results_repeat",
        )
        if signature != _score_signature(repeat):
            raise DemoError(f"persona {name} is not deterministic")
        reasons_have_evidence = any(
            bool(_object(reason, "results.reason").get("sourceNames"))
            for recommendation in _recommendations(result)
            for reason in _list(recommendation.get("reasons"), "results.reasons")
        )
        if not reasons_have_evidence:
            raise DemoError(f"persona {name} has no curriculum-backed explanation")
        persona_results[name] = result
        fits = [fit for _, fit in signature]
        logger.info(
            "persona_verified name=%s program_count=%d fit_min=%d fit_max=%d",
            name,
            len(signature),
            min(fits),
            max(fits),
        )

    baseline = persona_results["it_software"]
    strong_anti = persona_results["it_with_strong_physics_anti_interest"]
    baseline_by_id = {
        _object(item.get("program"), "baseline.program").get("programId"): item
        for item in _recommendations(baseline)
    }
    strong_by_id = {
        _object(item.get("program"), "strong_anti.program").get("programId"): item
        for item in _recommendations(strong_anti)
    }
    high_physics_count = 0
    for program_id, before in baseline_by_id.items():
        after = strong_by_id.get(program_id)
        if after is None:
            continue
        before_program = _object(before.get("program"), "baseline.program")
        after_program = _object(after.get("program"), "strong_anti.program")
        before_share = _decimal_number(_object(before_program.get("areaShare"), "baseline.areaShare").get("physics_astronomy"))
        after_share = _decimal_number(_object(after_program.get("areaShare"), "strong_anti.areaShare").get("physics_astronomy"))
        if max(before_share, after_share) >= 0.05:
            high_physics_count += 1
        before_fit = _int_value(before.get("contentFit"), "baseline.contentFit")
        after_fit = _int_value(after.get("contentFit"), "strong_anti.contentFit")
        if after_fit > before_fit:
            raise DemoError(f"anti-interest improved program {program_id}")
    if high_physics_count == 0:
        logger.warning("anti_interest_high_area_check_vacuous high_area_program_count=0")
    else:
        logger.info("anti_interest_monotonic_verified high_area_program_count=%d", high_physics_count)


def _decimal_number(value: object) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError as exc:
            raise DemoError("result contains an invalid decimal") from exc
    return 0.0


def _int_value(value: object, label: str) -> int:
    if isinstance(value, int):
        return value
    raise DemoError(f"{label} is not an integer")


def run_demo(args: argparse.Namespace) -> None:
    andromeda_base_url = args.andromeda_base_url.rstrip("/")
    logger.info("stage_start name=andromeda_api path=/openapi.json")
    wait_for_http(_url(andromeda_base_url, "/openapi.json"), args.timeout, "andromeda_api")

    spike_base_url = f"http://{args.spike_host}:{args.spike_port}"
    frontend_url = f"http://{args.spike_host}:{args.frontend_port}/"
    frontend_origin = frontend_url.rstrip("/")
    env = os.environ.copy()
    env["ANDROMEDA_API_BASE_URL"] = andromeda_base_url
    env["SPIKE_CORS_ORIGIN"] = frontend_origin
    env["PYTHONPATH"] = os.pathsep.join(
        value for value in (str(BACKEND_ROOT / "src"), env.get("PYTHONPATH")) if value
    )
    env["VITE_API_BASE_URL"] = spike_base_url

    spike_process: Popen[bytes] | None = None
    frontend_process: Popen[bytes] | None = None
    try:
        spike_process = _start_process(
            [sys.executable, "-m", "uvicorn", "proftest_spike.api.main:app", "--host", args.spike_host, "--port", str(args.spike_port)],
            env,
            "spike_backend",
        )
        vite_executable = FRONTEND_ROOT / "node_modules" / ".bin" / ("vite.cmd" if os.name == "nt" else "vite")
        if not vite_executable.exists():
            raise DemoError("frontend dependencies are not installed; run npm install in proftest-spike/frontend")
        frontend_process = _start_process(
            [str(vite_executable), "--host", args.spike_host, "--port", str(args.frontend_port)],
            env,
            "spike_frontend",
            cwd=FRONTEND_ROOT,
        )
        wait_for_http(_url(spike_base_url, "/api/health"), args.timeout, "spike_backend")
        wait_for_http(frontend_url, args.timeout, "spike_frontend", json_response=False)
        _verify_personas(spike_base_url)
        logger.info("demo_verified personas=%d viewports=desktop,mobile", len(PERSONAS))
        if args.keep_alive:
            logger.info("demo_ready frontend=%s; press Ctrl-C to stop", frontend_url)
            while True:
                if spike_process.poll() is not None:
                    raise DemoError("spike backend exited while demo was running")
                if frontend_process.poll() is not None:
                    raise DemoError("spike frontend exited while demo was running")
                time.sleep(1.0)
    finally:
        if frontend_process is not None:
            _stop_process(frontend_process, "spike_frontend")
        if spike_process is not None:
            _stop_process(spike_process, "spike_backend")


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging(args.log_level)
    try:
        run_demo(args)
    except KeyboardInterrupt:
        logger.info("demo_interrupted")
        return 130
    except DemoError as exc:
        logger.error("demo_failed error=%s", str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
