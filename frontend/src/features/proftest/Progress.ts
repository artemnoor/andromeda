import type { components } from "../../api/generated";

type Question = components["schemas"]["QuestionResponse"];

export function questionBlockLabel(block: Question["block"]): string {
  if (block === "anti_interests") return "Антиинтересы";
  if (block === "activities") return "Тип деятельности";
  return "Интересы";
}

export function renderProgress(question: Question, index: number, total: number): string {
  const percent = total > 0 ? ((index + 1) / total) * 100 : 0;
  return `<div class="test-topline"><span class="eyebrow">${questionBlockLabel(question.block)}</span><span class="step-count" data-testid="proftest-progress">${index + 1} / ${total}</span></div><div class="progress-track" aria-label="Прогресс профтеста"><i style="width:${percent}%"></i></div>`;
}
