import { describe, expect, it } from "vitest";

import {
  answersFor,
  emptyDraft,
  setAnswerIntensity,
  setSingleAnswer,
  toggleMultiAnswer,
  toRequest
} from "./testState";

describe("test draft state", () => {
  it("keeps single and multi-select answers while producing an API request", () => {
    let draft = emptyDraft();
    draft = setSingleAnswer(draft, "interest_scenario_1", "scenario_1_program");
    draft = toggleMultiAnswer(draft, "anti_interest_areas", "physics_astronomy");
    draft = setAnswerIntensity(draft, "anti_interest_areas", "physics_astronomy", 0.95);
    draft = toggleMultiAnswer(draft, "anti_interest_areas", "chemistry_materials");
    draft = {
      ...draft,
      adaptiveAnswer: {
        questionId: "adaptive_1",
        optionId: "more_first",
        firstDimension: "computer_science_data",
        secondDimension: "mathematics_statistics"
      }
    };

    expect(answersFor(draft, "anti_interest_areas")).toEqual([
      { questionId: "anti_interest_areas", optionId: "physics_astronomy", intensity: 0.95 },
      { questionId: "anti_interest_areas", optionId: "chemistry_materials", intensity: 0.5 }
    ]);
    expect(toRequest(draft)).toEqual({
      answers: [
        { questionId: "interest_scenario_1", optionId: "scenario_1_program" },
        { questionId: "anti_interest_areas", optionId: "physics_astronomy", intensity: 0.95 },
        { questionId: "anti_interest_areas", optionId: "chemistry_materials", intensity: 0.5 }
      ],
      adaptiveAnswers: [
        {
          questionId: "adaptive_1",
          optionId: "more_first",
          firstDimension: "computer_science_data",
          secondDimension: "mathematics_statistics"
        }
      ]
    });
  });

  it("removes a multi-select answer without mutating the previous draft", () => {
    const initial = emptyDraft();
    const selected = toggleMultiAnswer(initial, "anti_interest_areas", "physics_astronomy");
    const removed = toggleMultiAnswer(selected, "anti_interest_areas", "physics_astronomy");

    expect(answersFor(initial, "anti_interest_areas")).toEqual([]);
    expect(answersFor(selected, "anti_interest_areas")).toHaveLength(1);
    expect(answersFor(removed, "anti_interest_areas")).toEqual([]);
  });
});
