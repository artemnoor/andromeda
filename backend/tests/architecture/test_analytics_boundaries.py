from __future__ import annotations

import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[2]
MODULES_ROOT = PROJECT_ROOT / "src" / "andromeda" / "modules"
FUTURE_MODULES = ("semantic", "analytics", "entity_resolution", "conversation", "presentation")
FORBIDDEN_IMPORT_PREFIXES = (
    "andromeda.api",
    "andromeda.composition",
    "andromeda.infrastructure",
    "andromeda.ingestion",
    "telegram",
    "andromeda_telegram",
    "jev",
    "max",
    "sqlalchemy",
)


def _resolved_imports(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return tuple(imports)


def _future_module_files() -> tuple[Path, ...]:
    return tuple(
        path
        for module in FUTURE_MODULES
        for path in (MODULES_ROOT / module).rglob("*.py")
        if path.is_file()
    )


def test_future_subject_modules_do_not_cross_transport_or_infrastructure_boundary() -> None:
    violations: list[str] = []
    for path in _future_module_files():
        for imported in _resolved_imports(path):
            if any(imported == prefix or imported.startswith(f"{prefix}.") for prefix in FORBIDDEN_IMPORT_PREFIXES):
                violations.append(f"{path.relative_to(MODULES_ROOT)} -> {imported}")
    assert violations == []


def test_future_subject_module_allowlist_is_explicit() -> None:
    assert FUTURE_MODULES == ("semantic", "analytics", "entity_resolution", "conversation", "presentation")
