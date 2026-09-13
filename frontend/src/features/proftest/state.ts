import type { components } from "../../api/generated";

export type ProftestScreen = "intro" | "base" | "adaptive" | "loading" | "results" | "detail" | "error" | "empty";
type Answer = components["schemas"]["ProftestAnswerRequest"];
type AdaptiveAnswer = components["schemas"]["ProftestAdaptiveAnswerRequest"];
type Results = components["schemas"]["ProftestResultsResponse"];

export interface ProftestDraft {
  screen: ProftestScreen;
  answers: Record<string, Answer>;
  currentQuestion: number;
  adaptiveAnswer: AdaptiveAnswer | null;
  results: Results | null;
}

const STORAGE_KEY = "andromeda:proftest:v1";

export function emptyDraft(): ProftestDraft {
  return { screen: "intro", answers: {}, currentQuestion: 0, adaptiveAnswer: null, results: null };
}

export function setAnswer(draft: ProftestDraft, questionId: string, optionIds: readonly string[], intensity?: number): ProftestDraft {
  const answer: Answer = intensity === undefined ? { questionId, optionIds: [...optionIds] } : { questionId, optionIds: [...optionIds], intensity };
  return { ...draft, answers: { ...draft.answers, [questionId]: answer } };
}

export function toggleAnswer(draft: ProftestDraft, questionId: string, optionId: string, maxSelected: number): ProftestDraft {
  const current = draft.answers[questionId]?.optionIds ?? [];
  const next = current.includes(optionId) ? current.filter((value) => value !== optionId) : current.length < maxSelected ? [...current, optionId] : current;
  const existing = draft.answers[questionId];
  const intensity = typeof existing?.intensity === "number" ? existing.intensity : undefined;
  return setAnswer(draft, questionId, next, intensity);
}

export function setIntensity(draft: ProftestDraft, questionId: string, intensity: number): ProftestDraft {
  const current = draft.answers[questionId];
  if (!current) return draft;
  return { ...draft, answers: { ...draft.answers, [questionId]: { ...current, intensity } } };
}

export function toRequest(draft: ProftestDraft): components["schemas"]["ProftestSubmissionRequest"] {
  return { answers: Object.values(draft.answers), adaptiveAnswers: draft.adaptiveAnswer ? [draft.adaptiveAnswer] : [] };
}

export function saveDraft(draft: ProftestDraft): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(draft));
}

export function loadDraft(): ProftestDraft {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return emptyDraft();
  try {
    const value: unknown = JSON.parse(raw);
    if (!isDraft(value)) throw new Error("invalid draft");
    return value;
  } catch {
    console.warn("[proftest] restored_state_invalid");
    localStorage.removeItem(STORAGE_KEY);
    return emptyDraft();
  }
}

export function clearDraft(): void {
  localStorage.removeItem(STORAGE_KEY);
}

export function hasInProgressDraft(draft: ProftestDraft): boolean {
  return draft.screen === "base" || draft.screen === "adaptive" || draft.screen === "loading";
}

function isDraft(value: unknown): value is ProftestDraft {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<ProftestDraft>;
  return typeof candidate.screen === "string" && ["intro", "base", "adaptive", "loading", "results", "detail", "error", "empty"].includes(candidate.screen) && typeof candidate.currentQuestion === "number" && Number.isInteger(candidate.currentQuestion) && candidate.currentQuestion >= 0 && !!candidate.answers && typeof candidate.answers === "object" && (candidate.adaptiveAnswer === null || candidate.adaptiveAnswer === undefined || typeof candidate.adaptiveAnswer === "object") && (candidate.results === null || candidate.results === undefined || typeof candidate.results === "object");
}

export { STORAGE_KEY };
