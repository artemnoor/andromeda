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

export function renderSessionProgress(question: Question, progress: { stage: string; stageIndex: number; stageCount: number; minRemaining: number; maxRemaining: number }): string {
  const percent = Math.min(100, Math.max(4, ((progress.stageIndex + 1) / progress.stageCount) * 100));
  const remaining = progress.minRemaining === progress.maxRemaining ? `${progress.minRemaining}` : `${progress.minRemaining}–${progress.maxRemaining}`;
  return `<div class="test-topline"><span class="eyebrow">${question.stage ?? question.block}</span><span class="step-count" data-testid="proftest-progress">Этап ${progress.stageIndex + 1} из ${progress.stageCount} · осталось примерно ${remaining}</span></div><div class="progress-track" aria-label="Прогресс профтеста"><i style="width:${percent}%"></i></div>`;
}
