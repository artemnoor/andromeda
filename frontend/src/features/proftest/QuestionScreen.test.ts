import { describe, expect, it } from "vitest";

import { emptyDraft } from "./state";
import { renderSessionQuestionMarkup } from "./QuestionScreen";

const progress = { stage: "about", stageIndex: 0, stageCount: 6, minRemaining: 20, maxRemaining: 30 };

function question(componentType: "ChipSelect" | "SingleChoiceCard" | "MultiChoiceCard" | "AnchoredScale" | "PairChoice" | "ScenarioChoice" | "RankTop") {
  return {
    id: `question:${componentType}`,
    block: "context" as const,
    prompt: "Что ближе?",
    options: [{ id: "one", label: "Первый вариант" }, { id: "two", label: "Второй вариант" }],
    required: true,
    adaptive: false,
    multiSelect: componentType === "ChipSelect" || componentType === "MultiChoiceCard",
    maxSelected: 2,
    stage: "about",
    componentType,
    order: 0,
    helperText: "Выбери близкий вариант",
    declaredDimensions: [],
    allowUncertain: true,
    allowSkip: false,
  };
}

describe("session question mechanics", () => {
  it("renders every configured mechanic from server metadata", () => {
    const markup = (["ChipSelect", "SingleChoiceCard", "MultiChoiceCard", "AnchoredScale", "PairChoice", "ScenarioChoice", "RankTop"] as const)
      .map((component) => renderSessionQuestionMarkup(question(component), emptyDraft(), progress, true));

    expect(markup.join("\n")).toContain('data-component="PairChoice"');
    expect(markup.join("\n")).toContain('data-testid="session-uncertain"');
    expect(markup.join("\n")).toContain('data-testid="session-next"');
  });
});
