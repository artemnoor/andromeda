from __future__ import annotations

import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[2]
ANDROMEDA_ROOT = PROJECT_ROOT / "src" / "andromeda"


def _module_name(path: Path) -> str:
    return ".".join(path.relative_to(ANDROMEDA_ROOT).with_suffix("").parts)


def test_andromeda_package_has_subject_module_boundaries() -> None:
    expected = {
        "modules/universities/domain",
        "modules/universities/contracts",
        "modules/universities/services",
        "modules/universities/repository",
        "modules/programs/domain",
        "modules/programs/contracts",
        "modules/programs/services",
        "modules/programs/repository",
        "modules/curricula/domain",
        "modules/curricula/contracts",
        "modules/curricula/services",
        "modules/curricula/repository",
        "modules/disciplines/domain",
        "modules/disciplines/contracts",
        "modules/disciplines/services",
        "modules/disciplines/repository",
        "modules/comparison/domain",
        "modules/comparison/contracts",
        "modules/comparison/services",
        "modules/comparison/repository",
        "modules/proftest/domain",
        "modules/proftest/contracts",
        "modules/proftest/services",
        "modules/proftest/repository",
        "modules/recommendations/domain",
        "modules/recommendations/contracts",
        "modules/recommendations/services",
        "modules/recommendations/repository",
        "modules/events/domain",
        "modules/events/contracts",
        "modules/events/services",
        "modules/events/repository",
    }
    actual = {path.relative_to(ANDROMEDA_ROOT).as_posix() for path in ANDROMEDA_ROOT.glob("modules/*/*") if path.is_dir()}
    assert expected <= actual


def test_core_modules_do_not_import_infrastructure_api_or_legacy_package() -> None:
    forbidden_fragments = ("andromeda.infrastructure", "andromeda.api", "sqlalchemy", "bmstu_parser", "proftest_spike")
    violations: list[str] = []
    for path in ANDROMEDA_ROOT.glob("modules/**/*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            imported = ""
            if isinstance(node, ast.Import):
                imported = ",".join(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported = node.module or ""
            if any(fragment in imported for fragment in forbidden_fragments):
                violations.append(f"{_module_name(path)} -> {imported}")
    assert violations == []
