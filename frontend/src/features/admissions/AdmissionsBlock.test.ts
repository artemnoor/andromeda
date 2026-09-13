import { describe, expect, it } from "vitest";

import type { ProgramAdmissionsResponse } from "../../api/client";
import { renderAdmissions, renderAdmissionsEmpty, renderAdmissionsError, renderAdmissionsLoading } from "./AdmissionsBlock";

const response = {
  program: {
    id: "program:09.03.01-02",
    directionId: "direction:09.03.01",
    code: "09.03.01-02",
    name: "Информатика и вычислительная техника",
    educationYear: 2025,
    studyPlanUrl: "https://example.test/plan.pdf",
    sourceUrl: "https://example.test/program",
  },
  programId: "program:09.03.01-02",
  offerings: [
    {
      id: "admission-offering:program:09.03.01-02:2026:full_time:budget:direction",
      admissionYear: 2026,
      studyForm: "full_time",
      fundingType: "budget",
      scope: "direction",
      places: 318,
      exams: [{ subject: "Математика", sourceName: "BMSTU", minimumScore: "46.00", isChoice: false, isRequired: true, provenance: { sourceKind: "detail", sourceUrl: "https://example.test", capturedAt: "2026-01-01T00:00:00Z", contentSha256: "a".repeat(64) } }],
      quotas: [],
      passingScores: [],
      tuition: [],
      provenance: [{ sourceKind: "detail", sourceUrl: "https://example.test", capturedAt: "2026-01-01T00:00:00Z", contentSha256: "a".repeat(64), sourceName: "BMSTU detail" }],
    },
  ],
} as ProgramAdmissionsResponse;

function fakeRoot(): HTMLElement {
  return { innerHTML: "" } as HTMLElement;
}

describe("admissions block", () => {
  it("renders source-backed offering details", () => {
    const root = fakeRoot();
    renderAdmissions(root, response);
    expect(root.innerHTML).toContain("Поступление");
    expect(root.innerHTML).toContain("318");
    expect(root.innerHTML).toContain("Математика");
    expect(root.innerHTML).toContain("BMSTU detail");
  });

  it("has explicit loading, empty, and error states", () => {
    const root = fakeRoot();
    renderAdmissionsLoading(root);
    expect(root.innerHTML).toContain("Загружаем данные поступления");
    renderAdmissionsEmpty(root);
    expect(root.innerHTML).toContain("Пока нет опубликованных данных");
    renderAdmissionsError(root, "API недоступен");
    expect(root.innerHTML).toContain("API недоступен");
  });
});
