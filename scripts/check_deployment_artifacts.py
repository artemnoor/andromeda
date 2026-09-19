"""Validate the tracked deployment packaging and internal port contract.

This is intentionally a static, secret-free gate.  A full compose/VM smoke
still runs in a disposable deployment environment, but this check catches the
most dangerous packaging drift before an image is published.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.is_file():
        raise AssertionError(f"missing deployment artifact: {relative_path}")
    return path.read_text(encoding="utf-8")


def _require(document: str, relative_path: str, fragment: str) -> None:
    if fragment not in document:
        raise AssertionError(f"{relative_path} is missing required fragment: {fragment}")


def main() -> int:
    compose_path = "deploy/yc/compose.yaml"
    compose = _read(compose_path)
    backend_dockerfile = _read("backend/Dockerfile")
    backend_entrypoint = _read("backend/docker-entrypoint.sh")
    frontend_dockerfile = _read("frontend-next/Dockerfile")
    frontend_config = _read("frontend-next/next.config.ts")
    standalone_script = _read("frontend-next/scripts/prepare-standalone.mjs")
    systemd_unit = _read("deploy/yc/andromeda-frontend.service")
    cloud_init = _read("deploy/yc/cloud-init.yaml")
    caddy = _read("deploy/yc/Caddyfile")
    telegram_env = _read("telegram-bot/.env.example")

    _require(compose, compose_path, "ANDROMEDA_INTERNAL_API_URL: http://backend:8020")
    _require(compose, compose_path, "ANDROMEDA_BACKEND_URL: http://backend:8020")
    _require(compose, compose_path, "backend:8020")
    if "backend:8000" in compose:
        raise AssertionError(f"{compose_path} contains obsolete backend:8000 fallback")

    _require(backend_dockerfile, "backend/Dockerfile", "EXPOSE 8020")
    _require(backend_entrypoint, "backend/docker-entrypoint.sh", "--port \"${PORT:-8020}\"")
    _require(frontend_dockerfile, "frontend-next/Dockerfile", "COPY --from=builder /app/.next/standalone ./")
    _require(frontend_dockerfile, "frontend-next/Dockerfile", 'CMD ["node", "server.js"]')
    _require(frontend_config, "frontend-next/next.config.ts", 'output: "standalone"')
    _require(standalone_script, "frontend-next/scripts/prepare-standalone.mjs", "standalone output was not created")
    _require(systemd_unit, "deploy/yc/andromeda-frontend.service", "/.next/standalone/server.js")
    _require(cloud_init, "deploy/yc/cloud-init.yaml", "--port 8020")
    _require(cloud_init, "deploy/yc/cloud-init.yaml", "/.next/standalone/server.js")
    _require(caddy, "deploy/yc/Caddyfile", "reverse_proxy backend:8020")
    _require(telegram_env, "telegram-bot/.env.example", "ANDROMEDA_BACKEND_URL=http://backend:8020")
    if "ANDROMEDA_BACKEND_URL=http://backend:8000" in telegram_env:
        raise AssertionError("telegram-bot/.env.example contains obsolete backend:8000")

    print("Deployment artifact contract passed: Docker, VM/systemd, Caddy, and internal API ports agree.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
