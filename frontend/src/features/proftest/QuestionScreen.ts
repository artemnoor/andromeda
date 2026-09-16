import type { components } from "../../api/generated";
import type { ProftestDraft } from "./state";
import { escapeHtml } from "./rendering";
import { renderProgress, renderSessionProgress } from "./Progress";

type Question = components["schemas"]["QuestionResponse"];

export function renderQuestionMarkup(question: Question, draft: ProftestDraft, index: number, total: number): string {
  const selected = draft.answers[question.id]?.optionIds ?? [];
  const answer = draft.answers[question.id];
  const isSelected = (optionId: string): boolean => selected.includes(optionId);
  const options = question.options.map((option) => `<button class="choice-card component-${question.componentType} ${isSelected(option.id) ? "selected" : ""}" data-option="${escapeHtml(option.id)}" type="button" aria-pressed="${isSelected(option.id)}"><span class="choice-mark">${isSelected(option.id) ? "✓" : ""}</span><span>${escapeHtml(option.label)}</span></button>`).join("");
  const intensity = question.multiSelect && selected.length > 0 ? `<label class="intensity-control"><span>Насколько это нежелательно?</span><input data-testid="anti-intensity" type="range" min="0" max="1" step="0.05" value="${answer?.intensity ?? 0.5}" /><output>${Math.round(Number(answer?.intensity ?? 0.5) * 100)}%</output></label>` : "";
  const helper = question.multiSelect ? `<p class="helper-text">Можно выбрать до ${question.maxSelected} вариантов. Если выбранная область не нравится особенно сильно, укажи это ниже.</p>` : "";
  const nextLabel = index === total - 1 ? "Посчитать совпадение" : "Дальше";
  const nextDisabled = question.required && selected.length === 0 ? "disabled" : "";
  return `<section class="test-shell" data-component="${escapeHtml(question.componentType)}">${renderProgress(question, index, total)}<h2>${escapeHtml(question.prompt)}</h2>${helper}<p class="helper-text">${escapeHtml(question.helperText ?? componentHint(question.componentType))}</p><div class="question-options" role="group" aria-label="Варианты ответа">${options}</div>${intensity}<div class="test-actions"><button class="secondary-button" data-testid="proftest-back" type="button" ${index === 0 ? "disabled" : ""}>Назад</button>${question.allowUncertain ? `<button class="secondary-button" data-testid="proftest-uncertain" type="button">Пока не уверен</button>` : ""}${question.allowSkip ? `<button class="secondary-button" data-testid="proftest-skip" type="button">Пропустить</button>` : ""}<button class="primary-button" data-testid="proftest-next" type="button" ${nextDisabled}>${nextLabel}</button></div></section>`;
}

export function renderSessionQuestionMarkup(question: Question, draft: ProftestDraft, progress: { stage: string; stageIndex: number; stageCount: number; minRemaining: number; maxRemaining: number }, isFirst: boolean): string {
  const answer = draft.sessionAnswers[question.id];
  const selected = answer?.optionIds ?? [];
  const selectedOption = (optionId: string): boolean => selected.includes(optionId);
  const options = question.options.map((option) => {
    const active = selectedOption(option.id);
    return `<button class="choice-card component-${escapeHtml(question.componentType)} ${active ? "selected" : ""}" data-option="${escapeHtml(option.id)}" type="button" aria-pressed="${active}"><span class="choice-mark">${active ? "✓" : ""}</span><span>${escapeHtml(option.label)}</span></button>`;
  }).join("");
  const canContinue = !question.required || selected.length > 0 || answer?.status === "uncertain" || answer?.status === "skipped";
  const helper = question.multiSelect ? `Можно выбрать до ${question.maxSelected} вариантов.` : componentHint(question.componentType);
  const intensity = question.multiSelect && selected.length > 0 ? `<label class="intensity-control"><span>Насколько это выражено?</span><input data-testid="session-intensity" type="range" min="0" max="1" step="0.05" value="${answer?.intensity ?? 0.5}" /><output>${Math.round(Number(answer?.intensity ?? 0.5) * 100)}%</output></label>` : "";
  return `<section class="test-shell" data-testid="session-question" data-component="${escapeHtml(question.componentType)}">${renderSessionProgress(question, progress)}<p class="eyebrow">${escapeHtml(question.componentType)}</p><h2>${escapeHtml(question.prompt)}</h2><p class="helper-text">${escapeHtml(question.helperText ?? helper)}</p><div class="question-options" role="group" aria-label="Варианты ответа">${options}</div>${intensity}<div class="test-actions"><button class="secondary-button" data-testid="session-back" type="button" ${isFirst ? "disabled" : ""}>Назад</button>${question.allowUncertain ? `<button class="secondary-button" data-testid="session-uncertain" type="button">Не уверен</button>` : ""}${question.allowSkip ? `<button class="secondary-button" data-testid="session-skip" type="button">Пропустить</button>` : ""}<button class="primary-button" data-testid="session-next" type="button" ${canContinue ? "" : "disabled"}>${question.adaptive ? "Уточнить результат" : "Дальше"}</button></div></section>`;
}

function componentHint(component: Question["componentType"]): string {
  if (component === "PairChoice") return "Выбери тот вариант, который ближе; правильного ответа нет.";
  if (component === "ScenarioChoice") return "Представь сценарий и выбери наиболее естественную реакцию.";
  if (component === "AnchoredScale") return "Выбери точку между полюсами шкалы.";
  if (component === "RankTop") return "Выбери и расставь приоритеты среди вариантов.";
  if (component === "ChipSelect") return "Можно выбрать несколько близких вариантов.";
  return "Ответ можно изменить до завершения теста.";
}
