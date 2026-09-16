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
      passingScores: [{ scoreType: "budget", competitionType: "general", status: "numeric", score: "220.00", provenance: { sourceKind: "orders", sourceUrl: "https://example.test/orders.pdf", capturedAt: "2026-01-01T00:00:00Z", contentSha256: "b".repeat(64) } }],
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
    expect(root.innerHTML).toContain("Минимум зачисленных: 220 баллов");
    expect(root.innerHTML).toContain("Общий конкурс");
  });

  it("renders quota minimums and BVI without formatting null as a number", () => {
    const root = fakeRoot();
    const mixed = structuredClone(response) as ProgramAdmissionsResponse;
    const offering = mixed.offerings[0];
    if (!offering) throw new Error("test fixture has no offering");
    offering.passingScores = [
      { scoreType: "budget", competitionType: "targeted", status: "numeric", score: "195.00", provenance: { sourceKind: "orders", sourceUrl: "https://example.test/orders.pdf", capturedAt: "2026-01-01T00:00:00Z", contentSha256: "c".repeat(64) } },
      { scoreType: "budget", competitionType: "separate_quota", status: "bvi", score: null, provenance: { sourceKind: "orders", sourceUrl: "https://example.test/orders.pdf", capturedAt: "2026-01-01T00:00:00Z", contentSha256: "d".repeat(64) } },
    ];
    renderAdmissions(root, mixed);
    expect(root.innerHTML).toContain("Целевая квота");
    expect(root.innerHTML).toContain("Минимум зачисленных: 195 баллов");
    expect(root.innerHTML).toContain("БВИ (без вступительных испытаний)");
    expect(root.innerHTML).not.toContain("null балла");
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
