#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Парсер таблицы "План приема на 1-й курс МГТУ им. Н. Э. Баумана".

Что делает:
- извлекает таблицы из PDF через pdfplumber;
- восстанавливает значения из объединённых ячеек;
- определяет площадку/филиал (Москва, Мытищинский филиал, Калужский филиал);
- связывает: площадка -> направление -> образовательная программа -> кафедры;
- не дублирует КЦП на каждую кафедру, если в PDF одна ячейка КЦП объединяет несколько кафедр;
- сохраняет provenance: страница / таблица / строка PDF;
- пишет nested JSON + нормализованные CSV-таблицы для дальнейшей загрузки в БД.

Установка:
    pip install pdfplumber

Запуск:
    python bmstu_admission_parser.py "БС(3).pdf" --out-dir out

Результат:
    out/admission_nested.json
    out/campuses.csv
    out/directions.csv
    out/departments.csv
    out/programs.csv
    out/program_departments.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pdfplumber


CODE_RE = re.compile(r"\b\d{2}\.\d{2}\.\d{2}\b")
BASE_DEPARTMENT_RE = re.compile(r"^([А-ЯЁA-Z]+\d*|[A-Z]+\d*)")

EXPECTED_COLUMNS = 11


def clean_text(value: Optional[str]) -> Optional[str]:
    """Нормализует переносы строк и служебные символы PDF."""
    if value is None:
        return None
    value = value.replace("\u00ad", "")       # soft hyphen
    value = value.replace("￾", "-")          # артефакт некоторых PDF
    value = re.sub(r"\s*\n\s*", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value or None


def to_int(value: Optional[str]) -> Optional[int]:
    value = clean_text(value)
    if value is None:
        return None
    if re.fullmatch(r"\d+", value):
        return int(value)
    return None


def stable_id(prefix: str, *parts: object) -> str:
    raw = "\x1f".join("" if p is None else str(p) for p in parts)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:14]
    return f"{prefix}_{digest}"


def is_valid_code(value: Optional[str]) -> bool:
    return bool(value and CODE_RE.fullmatch(value.strip()))


def repair_direction_name_and_code(
    direction_name: Optional[str],
    direction_code: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    """
    Чинит редкий артефакт таблицы, когда конец названия направления попал
    в соседнюю колонку вместе с кодом, например:
        ["Информационные системы и технолог", "ии 09.03.02"]
    ->  ["Информационные системы и технологии", "09.03.02"]
    """
    name = clean_text(direction_name)
    code = clean_text(direction_code)

    if is_valid_code(code):
        return name, code

    combined = clean_text(" ".join(x for x in (name, code) if x))
    if not combined:
        return name, code

    match = CODE_RE.search(combined)
    if not match:
        return name, code

    fixed_code = match.group(0)

    if code and fixed_code in code:
        prefix = code.split(fixed_code, 1)[0].strip()
        if prefix and name:
            # Если в соседнюю колонку уехал короткий хвост слова: "технолог" + "ии".
            if re.fullmatch(r"[а-яё]{1,4}", prefix):
                fixed_name = name.rstrip() + prefix
            else:
                fixed_name = f"{name} {prefix}".strip()
        else:
            fixed_name = name
    else:
        fixed_name = combined[: match.start()].strip()

    return clean_text(fixed_name), fixed_code


def extract_region_text(page: Any, top: float, bottom: float) -> str:
    if bottom <= top:
        return ""
    try:
        return page.crop((0, top, page.width, bottom)).extract_text() or ""
    except Exception:
        return ""


def detect_location(text: str, current: Optional[str]) -> Optional[str]:
    """Ищет заголовок площадки/филиала перед очередной таблицей."""
    for raw_line in text.splitlines():
        line = clean_text(raw_line)
        if not line:
            continue

        if re.search(r"\bгород\s+Москва\b", line, flags=re.IGNORECASE):
            current = "Москва"
            continue

        if "филиал" in line.lower():
            match = re.search(r"([А-ЯЁ][А-Яа-яЁё\-]+\s+филиал)", line)
            if match:
                current = match.group(1)

    return current


def get_canonical_column_bounds(first_table: Any) -> List[Tuple[float, float]]:
    """
    Берём X-границы колонок из шапки первой таблицы.
    Они одинаковы во всём документе и нужны как fallback, если pdfplumber
    не видит отдельную ячейку из-за пропавшей вертикальной линии.
    """
    cells = first_table.rows[0].cells
    if len(cells) != EXPECTED_COLUMNS or any(cell is None for cell in cells):
        raise RuntimeError("Не удалось определить 11 колонок по шапке первой таблицы")
    return [(cell[0], cell[2]) for cell in cells]  # type: ignore[index]


def recover_text_from_column(
    page: Any,
    row_bbox: Tuple[float, float, float, float],
    x_bounds: Tuple[float, float],
) -> Optional[str]:
    """Fallback: собирает слова внутри X-колонки и текущей визуальной строки."""
    x0, x1 = x_bounds
    top, bottom = row_bbox[1], row_bbox[3]
    words = []

    for word in page.extract_words():
        cx = (word["x0"] + word["x1"]) / 2
        cy = (word["top"] + word["bottom"]) / 2
        if x0 <= cx <= x1 and top <= cy <= bottom:
            words.append(word)

    words.sort(key=lambda w: (round(w["top"], 2), w["x0"]))
    return clean_text(" ".join(w["text"] for w in words))


def split_department_code(raw_code: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    raw_code = clean_text(raw_code)
    if not raw_code:
        return None, None

    match = BASE_DEPARTMENT_RE.match(raw_code)
    if not match:
        return raw_code, None

    base = match.group(1)
    variant = raw_code[len(base):].strip() or None
    return base, variant


def iter_raw_rows(pdf_path: Path) -> List[Dict[str, Any]]:
    """Извлекает все физические строки таблиц с координатной привязкой."""
    rows: List[Dict[str, Any]] = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        if not pdf.pages:
            return rows

        first_tables = pdf.pages[0].find_tables()
        if not first_tables:
            raise RuntimeError("На первой странице не найдена таблица")

        column_bounds = get_canonical_column_bounds(first_tables[0])
        current_location: Optional[str] = None
        last_recovered_location: Optional[str] = None
        last_direction_code: Optional[str] = None

        for page_no, page in enumerate(pdf.pages, start=1):
            tables = sorted(page.find_tables(), key=lambda t: t.bbox[1])
            previous_bottom = 0.0

            for table_no, table in enumerate(tables, start=1):
                heading_area = extract_region_text(page, previous_bottom, table.bbox[1])
                current_location = detect_location(heading_area, current_location)
                if current_location != last_recovered_location:
                    last_recovered_location = current_location
                    last_direction_code = None

                extracted = table.extract()
                if len(extracted) != len(table.rows):
                    raise RuntimeError(
                        f"Страница {page_no}, таблица {table_no}: "
                        "число извлечённых строк не совпало с геометрией таблицы"
                    )

                for row_no, (cells, row_geometry) in enumerate(
                    zip(extracted, table.rows), start=1
                ):
                    cells = [clean_text(x) for x in cells]

                    if len(cells) != EXPECTED_COLUMNS:
                        raise RuntimeError(
                            f"Страница {page_no}, таблица {table_no}, строка {row_no}: "
                            f"ожидалось {EXPECTED_COLUMNS} колонок, получено {len(cells)}"
                        )

                    # Пропускаем шапку.
                    if cells[0] and cells[0].startswith("Наименование направления"):
                        continue

                    # В некоторых строках PDF объединённые ячейки направления
                    # визуально есть, но table.extract() возвращает их как None.
                    # Например, у 24.05.01 код и уровень находятся в той же
                    # физической строке, однако выпадают из первых трёх ячеек.
                    # Восстанавливаем первые колонки по координатам слов только
                    # если там действительно найден полный код направления.
                    if not is_valid_code(cells[1]):
                        recovered = [
                            recover_text_from_column(page, row_geometry.bbox, column_bounds[index])
                            for index in range(3)
                        ]
                        # Одна объединённая ячейка может занимать несколько
                        # физических строк. Если код совпадает с последним уже
                        # распознанным направлением, это продолжение, а не новая
                        # строка направления (пример: 27.03.05 на стр. 5).
                        if is_valid_code(recovered[1]) and recovered[1] != last_direction_code:
                            cells[:3] = [value or cells[index] for index, value in enumerate(recovered)]

                    cells[0], cells[1] = repair_direction_name_and_code(cells[0], cells[1])
                    if is_valid_code(cells[1]):
                        last_direction_code = cells[1]

                    # В исходном PDF есть как минимум один случай, где ячейка уровня
                    # визуально заполнена, но pdfplumber возвращает None из-за сетки.
                    # Восстанавливаем только когда строка явно начинает новое направление.
                    if is_valid_code(cells[1]) and not cells[2]:
                        recovered_level = recover_text_from_column(
                            page, row_geometry.bbox, column_bounds[2]
                        )
                        if recovered_level:
                            cells[2] = recovered_level

                    rows.append(
                        {
                            "page": page_no,
                            "table": table_no,
                            "row": row_no,
                            "location": current_location or "Не определено",
                            "cells": cells,
                        }
                    )

                previous_bottom = table.bbox[3]

    return rows


def build_model(raw_rows: Sequence[Dict[str, Any]], source_name: str) -> Dict[str, Any]:
    """
    Строит нормализованную модель.

    Важная семантика объединённых ячеек:
    - колонки направления (0..2) forward-fill внутри площадки;
    - если название образовательной программы пусто, строка считается продолжением
      предыдущей объединённой ячейки программы;
    - КЦП/платные места/квоты хранятся на уровне program instance, а не копируются
      в каждую связь program<->department. Это защищает от двойного суммирования.
    """

    campuses: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    directions: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    departments: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    programs: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    links: List[Dict[str, Any]] = []

    current_location: Optional[str] = None
    current_direction: Optional[Dict[str, Any]] = None
    current_program_id: Optional[str] = None
    current_program_direction_id: Optional[str] = None

    # Чтобы два одинаковых по тексту program block, встретившиеся отдельно,
    # не схлопнулись случайно, добавляем порядковый номер блока внутри направления.
    program_counter_by_direction: Dict[str, int] = {}

    for item in raw_rows:
        cells = item["cells"]
        location = item["location"]

        if location != current_location:
            current_location = location
            current_direction = None
            current_program_id = None
            current_program_direction_id = None

        campus_id = stable_id("campus", location)
        campuses.setdefault(campus_id, {"id": campus_id, "name": location})

        (
            direction_name,
            direction_code,
            education_level,
            department_code_raw,
            department_name,
            program_name,
            duration,
            budget_places,
            paid_places,
            special_quota,
            separate_quota,
        ) = cells

        # Новое направление начинается, когда в строке есть название/код.
        if direction_name or direction_code:
            if not direction_name or not is_valid_code(direction_code):
                raise ValueError(
                    f"Не удалось однозначно распознать направление: "
                    f"page={item['page']} table={item['table']} row={item['row']} "
                    f"name={direction_name!r} code={direction_code!r}"
                )

            current_direction = {
                "name": direction_name,
                "code": direction_code,
                "education_level": education_level,
                "campus_id": campus_id,
            }

        if current_direction is None:
            raise ValueError(
                f"Строка-продолжение встретилась без текущего направления: {item}"
            )

        # Если level не был указан в continuation-row, используем только level
        # текущего направления — это значение именно объединённой ячейки направления.
        direction_id = stable_id(
            "dir",
            current_direction["campus_id"],
            current_direction["code"],
            current_direction["name"],
            current_direction.get("education_level"),
        )

        directions.setdefault(
            direction_id,
            {
                "id": direction_id,
                "campus_id": current_direction["campus_id"],
                "code": current_direction["code"],
                "name": current_direction["name"],
                "education_level": current_direction.get("education_level"),
            },
        )

        if not department_code_raw and not department_name and not program_name:
            # На всякий случай пропускаем полностью пустые служебные строки.
            continue

        if not department_code_raw or not department_name:
            raise ValueError(
                f"Не удалось распознать кафедру: "
                f"page={item['page']} table={item['table']} row={item['row']}"
            )

        department_base_code, department_variant = split_department_code(department_code_raw)
        department_id = stable_id(
            "dept", department_code_raw, department_name
        )

        departments.setdefault(
            department_id,
            {
                "id": department_id,
                "code_raw": department_code_raw,
                "base_code": department_base_code,
                "variant": department_variant,
                "name": department_name,
            },
        )

        # Непустая ячейка "Название образовательной программы" = новый program block.
        # Пустая ячейка = продолжение предыдущей объединённой program-cell.
        if program_name:
            program_counter_by_direction[direction_id] = (
                program_counter_by_direction.get(direction_id, 0) + 1
            )
            block_no = program_counter_by_direction[direction_id]

            current_program_id = stable_id(
                "program",
                direction_id,
                block_no,
                program_name,
                duration,
                budget_places,
                paid_places,
                special_quota,
                separate_quota,
            )
            current_program_direction_id = direction_id

            programs[current_program_id] = {
                "id": current_program_id,
                "direction_id": direction_id,
                "name": program_name,
                "duration": duration,
                "admission": {
                    "budget_places": to_int(budget_places),
                    "paid_places": to_int(paid_places),
                    "special_quota_places": to_int(special_quota),
                    "separate_quota_places": to_int(separate_quota),
                },
                "source": {
                    "file": source_name,
                    "page": item["page"],
                    "table": item["table"],
                    "row": item["row"],
                },
            }

        else:
            if current_program_id is None or current_program_direction_id != direction_id:
                raise ValueError(
                    "Пустая ячейка программы встретилась без предыдущего program block: "
                    f"page={item['page']} table={item['table']} row={item['row']}"
                )

            # Для continuation-row проверяем, что отдельные значения КЦП не появились
            # неожиданно. Если появились — лучше упасть, чем молча приписать их не туда.
            if any(x is not None for x in (budget_places, paid_places, special_quota, separate_quota)):
                raise ValueError(
                    "В continuation-row программы обнаружены отдельные значения мест/квот; "
                    "нужна ручная проверка: "
                    f"page={item['page']} table={item['table']} row={item['row']}"
                )

        links.append(
            {
                "program_id": current_program_id,
                "department_id": department_id,
                "duration_in_row": duration,
                "source_page": item["page"],
                "source_table": item["table"],
                "source_row": item["row"],
            }
        )

    return {
        "metadata": {
            "source_file": source_name,
            "schema_version": 1,
            "relation": "campus -> direction -> program <-> department",
            "note": (
                "Места и квоты хранятся на уровне program block из PDF. "
                "Если одна ячейка программы/КЦП объединяет несколько кафедр, "
                "в program_departments будет несколько связей, но КЦП останется одно."
            ),
        },
        "campuses": list(campuses.values()),
        "directions": list(directions.values()),
        "departments": list(departments.values()),
        "programs": list(programs.values()),
        "program_departments": links,
    }


def build_nested(model: Dict[str, Any]) -> Dict[str, Any]:
    """Делает удобный nested JSON поверх нормализованных сущностей."""
    campus_by_id = {x["id"]: dict(x, directions=[]) for x in model["campuses"]}
    direction_by_id = {x["id"]: dict(x, programs=[]) for x in model["directions"]}
    department_by_id = {x["id"]: x for x in model["departments"]}

    program_to_departments: Dict[str, List[Dict[str, Any]]] = {}
    for link in model["program_departments"]:
        department = dict(department_by_id[link["department_id"]])
        department["source"] = {
            "page": link["source_page"],
            "table": link["source_table"],
            "row": link["source_row"],
        }
        program_to_departments.setdefault(link["program_id"], []).append(department)

    for program in model["programs"]:
        p = dict(program)
        p["departments"] = program_to_departments.get(program["id"], [])
        direction_by_id[program["direction_id"]]["programs"].append(p)

    for direction in direction_by_id.values():
        campus_by_id[direction["campus_id"]]["directions"].append(direction)

    return {
        "metadata": model["metadata"],
        "campuses": list(campus_by_id.values()),
    }


def write_csv(path: Path, rows: Sequence[Dict[str, Any]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def export_model(model: Dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    nested = build_nested(model)
    with (out_dir / "admission_nested.json").open("w", encoding="utf-8") as f:
        json.dump(nested, f, ensure_ascii=False, indent=2)

    with (out_dir / "admission_relational.json").open("w", encoding="utf-8") as f:
        json.dump(model, f, ensure_ascii=False, indent=2)

    write_csv(
        out_dir / "campuses.csv",
        model["campuses"],
        ["id", "name"],
    )
    write_csv(
        out_dir / "directions.csv",
        model["directions"],
        ["id", "campus_id", "code", "name", "education_level"],
    )
    write_csv(
        out_dir / "departments.csv",
        model["departments"],
        ["id", "code_raw", "base_code", "variant", "name"],
    )

    program_rows = []
    for p in model["programs"]:
        program_rows.append(
            {
                "id": p["id"],
                "direction_id": p["direction_id"],
                "name": p["name"],
                "duration": p["duration"],
                "budget_places": p["admission"]["budget_places"],
                "paid_places": p["admission"]["paid_places"],
                "special_quota_places": p["admission"]["special_quota_places"],
                "separate_quota_places": p["admission"]["separate_quota_places"],
                "source_page": p["source"]["page"],
                "source_table": p["source"]["table"],
                "source_row": p["source"]["row"],
            }
        )

    write_csv(
        out_dir / "programs.csv",
        program_rows,
        [
            "id",
            "direction_id",
            "name",
            "duration",
            "budget_places",
            "paid_places",
            "special_quota_places",
            "separate_quota_places",
            "source_page",
            "source_table",
            "source_row",
        ],
    )
    write_csv(
        out_dir / "program_departments.csv",
        model["program_departments"],
        [
            "program_id",
            "department_id",
            "duration_in_row",
            "source_page",
            "source_table",
            "source_row",
        ],
    )


def validate_model(model: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    direction_ids = {x["id"] for x in model["directions"]}
    department_ids = {x["id"] for x in model["departments"]}
    program_ids = {x["id"] for x in model["programs"]}

    for p in model["programs"]:
        if p["direction_id"] not in direction_ids:
            errors.append(f"Program {p['id']} -> unknown direction {p['direction_id']}")

    for link in model["program_departments"]:
        if link["program_id"] not in program_ids:
            errors.append(f"Unknown program in link: {link['program_id']}")
        if link["department_id"] not in department_ids:
            errors.append(f"Unknown department in link: {link['department_id']}")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse BMSTU admission plan PDF")
    parser.add_argument("pdf", type=Path, help="Путь к PDF")
    parser.add_argument("--out-dir", type=Path, default=Path("out"), help="Каталог результата")
    args = parser.parse_args()

    raw_rows = iter_raw_rows(args.pdf)
    model = build_model(raw_rows, args.pdf.name)
    errors = validate_model(model)

    if errors:
        raise SystemExit("\n".join(errors))

    export_model(model, args.out_dir)

    print(f"Готово: {args.out_dir.resolve()}")
    print(f"Площадок: {len(model['campuses'])}")
    print(f"Направлений: {len(model['directions'])}")
    print(f"Кафедр/вариантов кафедр: {len(model['departments'])}")
    print(f"Program blocks: {len(model['programs'])}")
    print(f"Связей program<->department: {len(model['program_departments'])}")


if __name__ == "__main__":
    main()
