import type { components } from "../../api/generated";
import type { ProftestDraft } from "./state";
import { escapeHtml } from "./rendering";
import { renderProgress } from "./Progress";

type Question = components["schemas"]["QuestionResponse"];

export function renderQuestionMarkup(question: Question, draft: ProftestDraft, index: number, total: number): string {
  const selected = draft.answers[question.id]?.optionIds ?? [];
  const answer = draft.answers[question.id];
  const isSelected = (optionId: string): boolean => selected.includes(optionId);
  const options = question.options.map((option) => `<button class="choice-card ${isSelected(option.id) ? "selected" : ""}" data-option="${escapeHtml(option.id)}" type="button" aria-pressed="${isSelected(option.id)}"><span class="choice-mark">${isSelected(option.id) ? "✓" : ""}</span><span>${escapeHtml(option.label)}</span></button>`).join("");
  const intensity = question.multiSelect && selected.length > 0 ? `<label class="intensity-control"><span>Насколько это нежелательно?</span><input data-testid="anti-intensity" type="range" min="0" max="1" step="0.05" value="${answer?.intensity ?? 0.5}" /><output>${Math.round(Number(answer?.intensity ?? 0.5) * 100)}%</output></label>` : "";
  const helper = question.multiSelect ? `<p class="helper-text">Можно выбрать до ${question.maxSelected} вариантов. Если выбранная область не нравится особенно сильно, укажи это ниже.</p>` : "";
  const nextLabel = index === total - 1 ? "Посчитать совпадение" : "Дальше";
  const nextDisabled = question.required && selected.length === 0 ? "disabled" : "";
  return `<section class="test-shell">${renderProgress(question, index, total)}<h2>${escapeHtml(question.prompt)}</h2>${helper}<div class="question-options" role="group" aria-label="Варианты ответа">${options}</div>${intensity}<div class="test-actions"><button class="secondary-button" data-testid="proftest-back" type="button" ${index === 0 ? "disabled" : ""}>Назад</button><button class="primary-button" data-testid="proftest-next" type="button" ${nextDisabled}>${nextLabel}</button></div></section>`;
}
