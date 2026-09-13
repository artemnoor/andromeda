import { describe, expect, it } from "vitest";

import type { ProgramAdmissionsResponse } from "../../api/client";
import { renderAdmissionFit, renderAdmissionFitEmpty, renderAdmissionFitError, renderAdmissionFitLoading } from "./AdmissionFitBlock";

const admissions = {
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
      id: "admission-offering:program:09.03.01-02:2026:unknown:budget:direction",
      admissionYear: 2026,
      studyForm: null,
      fundingType: "budget",
      scope: "direction",
      places: 318,
      exams: [
        {
          subject: "Математика",
          sourceName: "ЕГЭ",
          minimumScore: "46.00",
          isChoice: false,
          isRequired: true,
          provenance: {
            sourceKind: "fixture",
            sourceUrl: "https://example.test",
            capturedAt: "2026-01-01T00:00:00Z",
            contentSha256: "a".repeat(64),
          },
        },
      ],
      quotas: [],
      passingScores: [],
      tuition: [],
      provenance: [],
    },
  ],
} as unknown as ProgramAdmissionsResponse;

function fakeRoot(): HTMLElement {
  return { innerHTML: "", querySelector: () => null } as unknown as HTMLElement;
}

function interactiveRoot(): { root: HTMLElement; form: HTMLFormElement } {
  const select = { value: admissions.offerings[0]?.id ?? "", addEventListener: () => undefined };
  const submit = { disabled: false };
  const form = {
    innerHTML: "",
    addEventListener: () => undefined,
    querySelector: (selector: string) => selector.includes("offering") ? select : submit,
    querySelectorAll: () => [],
    requestSubmit: () => undefined,
  } as unknown as HTMLFormElement;
  const result = { innerHTML: "" } as HTMLElement;
  const root = {
    innerHTML: "",
    querySelector: (selector: string) => selector.includes("admission-fit-form") ? form : result,
  } as unknown as HTMLElement;
  return { root, form };
}

describe("admission fit block", () => {
  it("renders explicit loading, empty, and error states", () => {
    const root = fakeRoot();
    renderAdmissionFitLoading(root);
    expect(root.innerHTML).toContain("Готовим расчёт Admission Fit");
    renderAdmissionFitEmpty(root);
    expect(root.innerHTML).toContain("Недостаточно данных для расчёта");
    renderAdmissionFitError(root, "API недоступен");
    expect(root.innerHTML).toContain("API недоступен");
  });

  it("builds the form from source-backed offerings and exams", () => {
    const { root, form } = interactiveRoot();
    renderAdmissionFit(root, admissions.programId, admissions);

    expect(root.innerHTML).toContain('data-testid="admission-fit"');
    expect(form.innerHTML).toContain("Математика");
    expect(form.innerHTML).toContain("Рассчитать Admission Fit");
  });
});
