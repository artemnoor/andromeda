import { afterEach, describe, expect, it, vi } from "vitest";

import { emptyDraft, hasInProgressDraft, loadDraft, setAnswer, setIntensity, STORAGE_KEY, toRequest, toggleAnswer } from "./state";

const storage = new Map<string, string>();

afterEach(() => {
  storage.clear();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function stubLocalStorage(): void {
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => storage.get(key) ?? null,
    setItem: (key: string, value: string) => storage.set(key, value),
    removeItem: (key: string) => storage.delete(key),
  });
}

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

  it("keeps an unfinished draft ahead of a completed server profile", () => {
    expect(hasInProgressDraft({ ...emptyDraft(), screen: "base" })).toBe(true);
    expect(hasInProgressDraft({ ...emptyDraft(), screen: "adaptive" })).toBe(true);
    expect(hasInProgressDraft({ ...emptyDraft(), screen: "results" })).toBe(false);
  });

  it("clears malformed persisted state instead of treating it as an in-progress draft", () => {
    stubLocalStorage();
    const warning = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ screen: "base", answers: "not-an-object" }));

    expect(loadDraft()).toEqual(emptyDraft());
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
    expect(warning).toHaveBeenCalledWith("[proftest] restored_state_invalid");
  });
});
