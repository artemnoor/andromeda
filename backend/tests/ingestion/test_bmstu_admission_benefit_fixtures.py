from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from andromeda.ingestion.contracts.raw import (
    RawAdmissionBenefitDocument,
    RawSourceSnapshot,
)
from andromeda.ingestion.universities.bmstu.normalizers.admission_benefits import (
    normalize_individual_achievements,
    normalize_olympiad_benefits,
)
from andromeda.ingestion.universities.bmstu.parser.admission_benefit_tables import (
    parse_benefit_tables,
)
from andromeda.ingestion.universities.bmstu.parser.admission_olympiads import (
    parse_olympiad_profile_source,
)
from andromeda.ingestion.universities.bmstu.parser.admission_rules import (
    parse_admission_rule_policy,
)
from andromeda.ingestion.universities.bmstu.parser.individual_achievements import (
    parse_individual_achievement_tables,
)
from andromeda.modules.admission_benefits.contracts.status import (
    BenefitPolicyVersion,
    RuleDataStatus,
)

FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "bmstu_admission_benefits"
RUN_ID = "ingest:" + "d" * 32
HASH_RE = re.compile(r"^[a-f0-9]{64}$")
VERSIONS = BenefitPolicyVersion(
    schema_version="admission-benefits-schema.v1",
    parser_version="admission-benefits-parser.v1",
    policy_version="admission-benefits-policy.v1",
)


def _manifest() -> dict[str, object]:
    return json.loads((FIXTURE_DIR / "manifest-2026.json").read_text(encoding="utf-8"))


def _document(kind: str, source_url: str, content_sha256: str) -> RawAdmissionBenefitDocument:
    return RawAdmissionBenefitDocument(
        document_kind=kind,
        document_title=f"BMSTU {kind} 2026",
        admission_year=2026,
        source_url=source_url,
        source_snapshot_hash=content_sha256,
        source_run_id=RUN_ID,
        captured_at=datetime(2026, 9, 22, tzinfo=UTC),
        locator={"source_url": source_url},
        parser_version="admission-benefits-parser.v1",
    )


def _table(payload: dict[str, object], kind: str) -> dict[str, object]:
    rows = payload["rows"]
    if kind == "appendix_5_1":
        headers = ["№", "Олимпиада", "Профиль", "Победитель", "Призер", "Направления"]
    else:
        headers = [
            "№",
            "Олимпиада",
            "Профиль",
            "Общеобразовательные предметы или направления подготовки",
            "Уровень",
            "Профильные общеобразовательные предметы для предоставления особого права на 100 баллов при подтверждении олимпиады 75 баллами по ЕГЭ",
            "Победитель",
            "Призер",
        ]
    table: dict[str, object] = {
        "page": 1,
        "table": 1,
        "rows": [headers, *rows],
    }
    for key in ("row_numbers", "row_pages"):
        if key in payload:
            table[key] = payload[key]
    return table


def test_official_manifest_is_complete_and_has_no_local_canonical_sources() -> None:
    manifest = _manifest()
    documents = manifest["documents"]
    cases = manifest["verification_cases"]
    assert manifest["admission_year"] == 2026
    assert len(documents) >= 5
    assert len(cases) == 10
    assert all(case["id"] for case in cases)
    assert all(HASH_RE.fullmatch(document["content_sha256"]) for document in documents)
    assert all(document["source_url"].startswith("https://") for document in documents)
    assert all(not document["source_url"].startswith("file:") for document in documents)
    for document in documents:
        extract_path = FIXTURE_DIR / document["extract_file"]
        assert extract_path.is_file(), document["extract_file"]
        extract = json.loads(extract_path.read_text(encoding="utf-8"))
        assert extract["source_url"] == document["source_url"]
        assert extract["content_sha256"] == document["content_sha256"]
        assert extract["locator"]


def test_minimized_extracts_keep_official_hashes_and_expected_values() -> None:
    for file_name in ("appendix-5-1.rows.json", "appendix-5-3.rows.json", "appendix-6.rows.json"):
        payload = json.loads((FIXTURE_DIR / file_name).read_text(encoding="utf-8"))
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        assert hashlib.sha256(serialized).hexdigest() != payload["content_sha256"]
        assert payload["source_url"].startswith("https://api.www.bmstu.ru/file/")
        assert payload["content_sha256"] in {
            "f76eb91353b83c0fdf7773fffa768c5d9fde69ade6ff94bb3192f70b29f47941",
            "3a59ad1e5d900f4e8bb67e58ef3e8a0421d52666f02cfa9c09abb6747ded2c6f",
            "5ae90e108dc8940b37fe3b07f211664b7871791792abdc6ddc0dd365fb948bb9",
        }


def test_appendix_51_covers_only_all_except_and_not_granted_rows() -> None:
    payload = json.loads((FIXTURE_DIR / "appendix-5-1.rows.json").read_text(encoding="utf-8"))
    document = _document("appendix_5_1", payload["source_url"], payload["content_sha256"])
    records, diagnostics = parse_benefit_tables(document, (_table(payload, "appendix_5_1"),))
    result = normalize_olympiad_benefits(
        records,
        university_id="university:bmstu",
        known_direction_codes=frozenset({"01.03.02", "09.03.04", "10.05.01", "10.05.03"}),
        policy_version=VERSIONS,
    )

    assert diagnostics == ()
    assert len(records) == 6
    assert len(result.rules) == 5
    only_rules = [rule for rule in result.rules if rule.scope.mode.value == "only"]
    all_except_rules = [rule for rule in result.rules if rule.scope.mode.value == "all_except"]
    assert len(only_rules) == 3
    assert len(all_except_rules) == 2
    assert {target.value for target in all_except_rules[0].scope.targets} == {
        "01.03.02",
        "09.03.04",
        "10.05.01",
        "10.05.03",
    }
    assert all(rule.result_type.value == "winner" for rule in result.rules if "Городская" in rule.source_text)


def test_appendix_53_keeps_target_subject_and_confirmation_but_fails_closed_on_scope() -> None:
    payload = json.loads((FIXTURE_DIR / "appendix-5-3.rows.json").read_text(encoding="utf-8"))
    document = _document("appendix_5_3", payload["source_url"], payload["content_sha256"])
    records, _ = parse_benefit_tables(document, (_table(payload, "appendix_5_3"),))
    result = normalize_olympiad_benefits(
        records,
        university_id="university:bmstu",
        known_direction_codes=frozenset(),
        policy_version=VERSIONS,
    )

    formula_rules = [rule for rule in result.rules if "Формула" in rule.source_text]
    assert len(formula_rules) == 2
    assert all(rule.status is RuleDataStatus.REVIEW_REQUIRED for rule in formula_rules)
    assert all(rule.target_subject == "математика" for rule in formula_rules)
    assert all(rule.confirmation_subjects[0].subject == "математика" for rule in formula_rules)
    assert all(rule.confirmation_subjects[0].minimum_score == 75 for rule in formula_rules)
    assert any(diagnostic.code == "hundred_point_program_scope_unknown" for diagnostic in result.diagnostics)


def test_appendix_6_keeps_fixed_points_and_document_evidence() -> None:
    payload = json.loads((FIXTURE_DIR / "appendix-6.rows.json").read_text(encoding="utf-8"))
    document = _document("appendix_6", payload["source_url"], payload["content_sha256"])
    records, diagnostics = parse_individual_achievement_tables(
        document,
        ({"page": 1, "table": 1, "rows": [["№", "Полное наименование индивидуального достижения", "Подтверждающий документ", "Баллы"], *payload["rows"]], "row_numbers": payload["row_numbers"], "row_pages": payload["row_pages"]},),
    )
    result = normalize_individual_achievements(
        records,
        university_id="university:bmstu",
        policy_version=VERSIONS,
    )

    assert diagnostics == ()
    assert result.policy is not None
    assert {rule.points for rule in result.policy.rules} == {10, 5}
    assert all(rule.provenance.source_snapshot_hash == payload["content_sha256"] for rule in result.policy.rules)


def test_historical_bvi_fixture_is_explicitly_not_an_eligibility_rule() -> None:
    payload = json.loads((FIXTURE_DIR / "historical-bvi-observation.json").read_text(encoding="utf-8"))
    assert payload["canonical_source"] is False
    assert payload["observation"] == {"competition_type": "bvi", "status": "bvi", "score": None}
    assert payload["observation"] != {"benefit_type": "bvi"}


def test_rules_extract_preserves_validity_and_confirmation_policy() -> None:
    payload = json.loads((FIXTURE_DIR / "rules-2026.extract.json").read_text(encoding="utf-8"))
    document = _document("rules", payload["source_url"], payload["content_sha256"])
    snapshot = RawSourceSnapshot(
        source_kind="bmstu_admission_document:rules",
        requested_url=document.source_url,
        final_url=document.source_url,
        status_code=200,
        content_type="application/json",
        captured_at=document.captured_at,
        content_sha256=document.source_snapshot_hash,
        body=(FIXTURE_DIR / "rules-2026.extract.json").read_bytes(),
        access_mode="fixture",
    )

    policy = parse_admission_rule_policy(snapshot)

    assert policy is not None
    assert policy.olympiad_result_max_age_years == 4
    assert policy.olympiad_confirmation_min_score == 75
    assert "четырех лет" in (policy.olympiad_result_validity_text or "")


def test_official_olympiad_profile_extract_resolves_engineering_subjects() -> None:
    payload = json.loads((FIXTURE_DIR / "shag-engineering.html.extract.json").read_text(encoding="utf-8"))
    snapshot = RawSourceSnapshot(
        source_kind="bmstu_olympiad_profile:engineering",
        requested_url=payload["source_url"],
        final_url=payload["source_url"],
        status_code=200,
        content_type="application/json",
        captured_at=datetime(2026, 9, 22, tzinfo=UTC),
        content_sha256=payload["content_sha256"],
        body=(FIXTURE_DIR / "shag-engineering.html.extract.json").read_bytes(),
        access_mode="fixture",
    )

    result = parse_olympiad_profile_source(snapshot, source_run_id=RUN_ID, admission_year=2026)

    assert result.diagnostics == ()
    assert result.source is not None
    assert result.source.profile_name == "Инженерное дело"
    assert result.source.corresponding_subjects == ("физика", "информатика", "математика", "химия")
    assert result.source.rsosh_level == 2
