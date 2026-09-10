import { describe, expect, it } from "vitest";

import { emptyDraft, setAnswer, setIntensity, toRequest, toggleAnswer } from "./state";

describe("proftest draft state", () => {
  it("keeps single and capped multi-select answers in the API shape", () => {
    let draft = emptyDraft();
    draft = setAnswer(draft, "interest_free_day", ["software_tool"]);
    draft = toggleAnswer(draft, "anti_subjects", "avoid_physics", 3);
    draft = toggleAnswer(draft, "anti_subjects", "avoid_chemistry", 3);
    draft = toggleAnswer(draft, "anti_subjects", "avoid_programming", 3);
    draft = toggleAnswer(draft, "anti_subjects", "avoid_math", 3);

    expect(draft.answers.anti_subjects?.optionIds).toEqual(["avoid_physics", "avoid_chemistry", "avoid_programming"]);
    expect(toRequest(draft)).toEqual({ answers: [{ questionId: "interest_free_day", optionIds: ["software_tool"] }, { questionId: "anti_subjects", optionIds: ["avoid_physics", "avoid_chemistry", "avoid_programming"] }], adaptiveAnswers: [] });
  });

  it("updates anti-interest intensity without mutating the previous draft", () => {
    const initial = setAnswer(emptyDraft(), "anti_subjects", ["avoid_physics"], 0.5);
    const updated = setIntensity(initial, "anti_subjects", 0.95);

    expect(initial.answers.anti_subjects?.intensity).toBe(0.5);
    expect(updated.answers.anti_subjects?.intensity).toBe(0.95);
  });
});
