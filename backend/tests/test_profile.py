from bmstu_parser.hierarchy import build_hierarchy
from bmstu_parser.profile import _priority_program_match, build_profile


def test_profile_keeps_only_requested_blocks_and_fields() -> None:
    records = [
        {
            "record_type": "University",
            "record_id": "u1",
            "name_short": "Тестовый вуз",
            "city": "Москва",
            "address": "ул. Тестовая, 1",
            "official_site": "https://example.test",
        },
        {"record_type": "OrganizationUnit", "record_id": "v1", "name": "Военный учебный центр"},
        {
            "record_type": "Faculty",
            "record_id": "f1",
            "name": 'Ф-т "Приборостроительный" (ПС)',
            "code": "ПС",
            "unit_type": "faculty",
        },
        {
            "record_type": "Department",
            "record_id": "d1",
            "name": 'Кафедра ПС-1 "Тест"',
            "code": "ПС-1",
            "parent_name": 'Ф-т "Приборостроительный" (ПС)',
            "unit_type": "department",
        },
        {"record_type": "Direction", "record_id": "dir1", "code": "01.03.02", "name": "Прикладная математика", "level": "бакалавриат"},
        {
            "record_type": "Program",
            "record_id": "p1",
            "source_id": "S03",
            "code": "01.03.02/01",
            "direction_code": "01.03.02",
            "name": "Математические методы",
            "profile": "Математические методы",
            "department_code": "ПС-1",
            "level": "бакалавриат",
            "form": "очная",
            "duration": "4 года",
        },
        {"record_type": "Tuition", "record_id": "t1", "code": "01.03.02", "year": 2026, "academic_year": "2026/2027", "price": 500000, "currency": "RUB"},
        {"record_type": "UniversityRanking", "record_id": "r1", "ranking": "Динамика мест МГТУ", "year": 2026, "rank": 12},
    ]
    tables = [
        {
            "source_id": "S10",
            "index": 3,
            "rows": [{"НП(С)": "01.03.02", "Пороговый балл по каждому предмету ЕГЭ": "85"}],
        },
        {
            "source_id": "S10",
            "index": 4,
            "rows": [{
                "НАПРАВЛЕНИЕ ПОДГОТОВКИ / СПЕЦИАЛЬНОСТЬ": "01.03.02",
                "2025": "29",
                "2025_2": "250",
                "2025_3": "294",
            }],
        },
    ]
    hierarchy = build_hierarchy(records)
    profile = build_profile(records, tables, hierarchy)

    assert set(profile["selected_blocks"]) == {
        "university", "faculties", "departments", "directions",
        "programs", "admission", "tuition", "study_plans",
    }
    assert profile["university"]["vuc"] is True
    assert "ratings" not in profile["university"]
    assert profile["faculties"][0]["university_id"] == "university:bmstu"
    assert profile["departments"][0]["code"] == "ПС-1"
    assert profile["programs"][0]["faculty_id"] == profile["faculties"][0]["id"]
    assert profile["admission"][0]["minimum_scores"][0]["score"] == 85
    assert profile["tuition"][0]["amount"] == 500000
    assert {
        "id", "name", "profile", "code", "direction_id", "direction_code",
        "department_id", "faculty_id", "form", "duration", "language", "study_plan_url",
    } <= set(profile["programs"][0])
    assert "description" in profile["fields"]["program"]


def test_study_plan_prefers_profile_code_over_direction_code() -> None:
    records = [
        {"record_type": "Direction", "record_id": "dir1", "code": "09.03.01", "name": "Информатика", "level": "бакалавриат"},
        {"record_type": "Program", "record_id": "p1", "source_id": "S06", "code": "09.03.01", "direction_code": "09.03.01", "name": "Информатика", "level": "бакалавриат"},
        {"record_type": "ProgramProfile", "record_id": "pp1", "profile_code": "09.03.01-01", "direction_code": "09.03.01", "name": "Профиль один"},
        {"record_type": "ProgramProfile", "record_id": "pp2", "profile_code": "09.03.01-02", "direction_code": "09.03.01", "name": "Профиль два"},
        {"record_type": "StudyPlan", "record_id": "sp1", "program_code": "09.03.01", "direction_code": "09.03.01", "program_profile_code": "09.03.01-02", "discipline": "Алгоритмы", "semester": 1, "hours": 72, "credits": 2},
    ]

    profile = build_profile(records)

    row = profile["study_plans"][0]
    assert row["program_id"] == "program:09.03.01-02"
    assert row["program_code"] == "09.03.01-02"


def test_priority_pdf_places_override_site_and_profile_disciplines_are_removed() -> None:
    records = [
        {"record_type": "Direction", "record_id": "dir1", "code": "09.03.01", "name": "Информатика", "level": "бакалавриат"},
        {
            "record_type": "Program", "record_id": "p1", "source_id": "S06", "code": "09.03.01",
            "direction_code": "09.03.01", "name": "Информатика", "level": "бакалавриат", "department_code": "ИУ-5",
        },
        {
            "record_type": "ProgramProfile", "record_id": "pp1", "profile_code": "09.03.01-01",
            "direction_code": "09.03.01", "name": "Интеллектуальные системы", "department": "ИУ5",
            "disciplines": ["Старое поле, которое больше не сохраняем"],
        },
        {"record_type": "Admission", "source_id": "S06", "direction_code": "09.03.01", "year": 2026, "place_type": "budget", "count": 1},
        {"record_type": "Admission", "source_id": "S06", "direction_code": "09.03.01", "year": 2026, "place_type": "paid", "count": 2},
        {"record_type": "Admission", "source_id": "S06", "direction_code": "09.03.01", "year": 2026, "exam": "Математика", "minimum_score": 40},
        {
            "record_type": "Admission", "source_id": "P01_BS_PDF", "direction_code": "09.03.01", "program_code": "09.03.01",
            "program_name": "Интеллектуальные системы", "department_code": "ИУ-5", "year": 2026,
            "budget_places": 42, "paid_places": 15, "budget_special_quota_places": 4, "paid_special_quota_places": 4,
            "source_priority": "primary", "source_url": "file:///БС.pdf", "pdf_page": 1, "pdf_row": 1,
        },
    ]

    profile = build_profile(records)

    program = profile["programs"][0]
    admission = next(item for item in profile["admission"] if item.get("source_id") == "P01_BS_PDF")
    assert "disciplines" not in program
    assert admission["program_code"] == "09.03.01-01"
    assert admission["budget_places"] == 42
    assert admission["paid_places"] == 15
    assert admission["budget_special_quota_places"] == 4
    assert admission["passing_score"] is None


def test_priority_pdf_does_not_guess_between_profiles() -> None:
    programs = [
        {
            "id": "program:09.03.01-02",
            "code": "09.03.01-02",
            "direction_code": "09.03.01",
            "name": "Интеллектуальные системы обработки информации и управления",
            "department_code": "ИУ-5",
        },
    ]
    second_higher = {
        "direction_code": "09.03.01",
        "department_code": "ИУ-5",
        "program_name": "Системы обработки информации и управления (второе ВО)",
    }
    branch_profile = {
        "direction_code": "09.03.01",
        "department_code": "ИУК-2",
        "program_name": "Интеллектуальные информационно-вычислительные системы",
    }

    assert _priority_program_match(second_higher, programs) is None
    assert _priority_program_match(branch_profile, programs) is None
