from bmstu_parser.models import ExtractionResult, FieldDefinition
from bmstu_parser.projector import project_fields


def _field(field_id: int, entity: str, name: str) -> FieldDefinition:
    return FieldDefinition(
        id=field_id,
        block="test",
        name=name,
        entity=entity,
        acquisition_status="Вычислять",
        primary_source="S01",
        url=None,
        extraction_target=None,
        format=None,
        recommended_method=None,
        coverage=None,
        reserve=None,
        reserve_url=None,
        history=None,
        refresh=None,
        reliability="Средняя",
        priority="P2",
        limitation=None,
        source_ids=("S01",),
    )


def test_does_not_project_unrelated_page_labels_as_a_fact() -> None:
    fields = [_field(1, "University", "Форма собственности")]
    extraction = ExtractionResult(
        source_id="S01",
        source_url="https://example.test",
        parser="test",
        captured_at="now",
        records=[
            {
                "record_type": "University",
                "source_id": "S01",
                "labels": {"Контакты": "example@test"},
            }
        ],
    )
    facts, _ = project_fields(fields, [extraction], {"S01": {"status": "ok"}}, {"S01"})
    assert facts[0]["value"] is None
    assert facts[0]["status"] == "not_found"


def test_does_not_treat_admission_links_as_demand_metrics() -> None:
    fields = [_field(2, "AdmissionDemandMetric", "Заявлений на место")]
    extraction = ExtractionResult(
        source_id="S01",
        source_url="https://example.test",
        parser="test",
        captured_at="now",
        records=[
            {
                "record_type": "AdmissionRow",
                "source_id": "S01",
                "values": {"href": "https://example.test/list.pdf"},
            }
        ],
    )
    facts, _ = project_fields(fields, [extraction], {"S01": {"status": "ok"}}, {"S01"})
    assert facts[0]["value"] is None
    assert facts[0]["status"] == "not_found"
