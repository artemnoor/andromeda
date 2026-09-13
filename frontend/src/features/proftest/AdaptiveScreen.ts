import type { components } from "../../api/generated";
import type { ProftestPreviewResponse } from "../../api/client";
import type { ProftestDraft } from "./state";
import { escapeHtml } from "./rendering";

type Question = components["schemas"]["QuestionResponse"];

export function renderAdaptiveMarkup(question: Question, preview: ProftestPreviewResponse, draft: ProftestDraft): string {
  const options = question.options.map((option) => {
    const selected = draft.adaptiveAnswer?.optionId === option.id;
    return `<button class="choice-card ${selected ? "selected" : ""}" data-adaptive-option="${escapeHtml(option.id)}" type="button" aria-pressed="${selected}"><span class="choice-mark">${selected ? "✓" : ""}</span><span>${escapeHtml(option.label)}</span></button>`;
  }).join("");
  const dimension = preview.adaptive.dimensions[0]?.label;
  const context = dimension ? `Поможем различить программы по оси «${escapeHtml(dimension.toLowerCase())}».` : "Вопрос выбран по тому, чем отличаются реальные программы в текущем каталоге.";
  return `<section class="test-shell adaptive-shell"><div class="test-topline"><span class="eyebrow">Уточняющий вопрос</span><span class="step-count">Адаптивный шаг</span></div><div class="progress-track"><i style="width:100%"></i></div><p class="helper-text">${context}</p><h2>${escapeHtml(question.prompt)}</h2><div class="question-options" role="group" aria-label="Адаптивный вопрос">${options}</div><div class="test-actions"><button class="secondary-button" data-testid="adaptive-back" type="button">Назад</button><button class="primary-button" data-testid="adaptive-submit" type="button" ${draft.adaptiveAnswer ? "" : "disabled"}>Показать программы</button></div></section>`;
}
