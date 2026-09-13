from __future__ import annotations

from decimal import Decimal

from andromeda.api.schemas.proftest import ProftestSubmissionRequest


def test_http_contract_uses_camel_case_and_forbids_extra_fields() -> None:
    request = ProftestSubmissionRequest.model_validate({"answers": [{"questionId": "q", "optionIds": ["a"], "intensity": Decimal("0.5")}], "adaptiveAnswers": []})

    assert request.answers[0].question_id == "q"
    assert request.model_dump(by_alias=True)["adaptiveAnswers"] == []
