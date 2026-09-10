from bmstu_parser.hierarchy import build_hierarchy


def _node(graph, node_type, label):
    return next(node for node in graph["nodes"] if node["type"] == node_type and node["label"] == label)


def test_department_prefix_join_targets_faculty_not_arbitrary_unit():
    graph = build_hierarchy([
        {"record_type": "Faculty", "source_id": "S02", "name": 'Ф-т "Фундаментальные науки"', "unit_type": "faculty", "record_id": "f1"},
        {"record_type": "OrganizationUnit", "source_id": "S02", "name": 'Учебный центр "Бауманец"', "unit_type": "center", "code": "Э", "record_id": "u1"},
        {"record_type": "Department", "source_id": "S02", "name": 'Кафедра ФН-1 "Высшая математика"', "code": "ФН-1", "unit_type": "department", "record_id": "d1"},
    ])
    faculty = _node(graph, "Faculty", 'Ф-т "Фундаментальные науки"')
    department = _node(graph, "Department", 'Кафедра ФН-1 "Высшая математика"')
    wrong_unit = _node(graph, "OrganizationUnit", 'Учебный центр "Бауманец"')
    links = [edge for edge in graph["edges"] if edge["to"] == department["id"] and edge["relation"] == "contains"]
    assert any(edge["from"] == faculty["id"] and edge["basis"] == "derived" for edge in links)
    assert all(edge["from"] != wrong_unit["id"] for edge in links)


def test_education_and_price_are_explicitly_code_joined():
    graph = build_hierarchy([
        {"record_type": "Direction", "source_id": "S03", "code": "01.03.02", "name": "Прикладная математика и информатика", "level": "бакалавриат", "record_id": "dir"},
        {"record_type": "Program", "source_id": "S03", "code": "01.03.02-01", "direction_code": "01.03.02", "name": "Информатика", "record_id": "prog"},
        {"record_type": "ProgramOffering", "source_id": "S03", "program_code": "01.03.02-01", "direction_code": "01.03.02", "department_code": "ФН-1", "record_id": "off"},
        {"record_type": "DirectionStandard", "source_id": "S04", "code": "01.03.02", "direction_code": "01.03.02", "name": "ФГОС", "record_id": "std"},
        {"record_type": "Tuition", "source_id": "S10", "code": "01.03.02", "name": "Прикладная математика и информатика", "price": 699000, "record_id": "price"},
    ])
    direction = _node(graph, "Direction", "Прикладная математика и информатика")
    incoming = [edge for edge in graph["edges"] if edge["from"] == direction["id"]]
    assert any(edge["relation"] == "has_standard" and edge["basis"] == "code_join" for edge in incoming)
    assert any(edge["relation"] == "has_price" and edge["basis"] == "code_join" for edge in incoming)
    assert _node(graph, "DirectionStandard", "ФГОС")["record_ids"] == ["std"]


def test_admission_rows_are_kept_in_competition_evidence_without_flat_tree_nodes():
    graph = build_hierarchy([
        {"record_type": "AdmissionRow", "source_id": "S07", "source_scope": "Головной вуз / текущий приём", "admission_year": 2026, "document_url": "https://example.test/list.pdf", "row_no": 1, "applicant_id": "123456", "program_code": "01.03.02", "record_id": "a1", "is_data_row": True},
        {"record_type": "AdmissionRow", "source_id": "S07", "source_scope": "Головной вуз / текущий приём", "admission_year": 2026, "document_url": "https://example.test/list.pdf", "row_no": 2, "applicant_id": "123457", "program_code": "01.03.02", "record_id": "a2", "is_data_row": True},
    ])
    competition = _node(graph, "AdmissionCompetition", "list.pdf")
    assert competition["record_count"] == 2
    assert set(competition["record_ids"]) == {"a1", "a2"}
    assert not any(node["type"] in {"AdmissionApplication", "EnrollmentOutcome"} for node in graph["nodes"])
