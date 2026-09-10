import type {
  AdaptiveAnswerPayload,
  AnswerPayload,
  ResultsResponse,
  TestAnswersRequest
} from "../api/generated";

export type Screen = "intro" | "base" | "adaptive" | "loading" | "results" | "detail" | "error" | "empty";

export interface DraftState {
  screen: Screen;
  answers: Record<string, AnswerPayload[]>;
  currentQuestion: number;
  adaptiveAnswer: AdaptiveAnswerPayload | null;
  results: ResultsResponse | null;
}

const STORAGE_KEY = "andromeda-proftest-spike:v1";

export function emptyDraft(): DraftState {
  return { screen: "intro", answers: {}, currentQuestion: 0, adaptiveAnswer: null, results: null };
}

export function loadDraft(): DraftState {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return emptyDraft();
  try {
    const candidate: unknown = JSON.parse(raw);
    if (!isDraft(candidate)) throw new Error("invalid draft");
    return candidate;
  } catch {
    console.warn("[proftest-spike] restored_state_invalid");
    localStorage.removeItem(STORAGE_KEY);
    return emptyDraft();
  }
}

export function saveDraft(draft: DraftState): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(draft));
}

export function setSingleAnswer(draft: DraftState, questionId: string, optionId: string): DraftState {
  return { ...draft, answers: { ...draft.answers, [questionId]: [{ questionId, optionId }] } };
}

export function toggleMultiAnswer(draft: DraftState, questionId: string, optionId: string): DraftState {
  const current = draft.answers[questionId] ?? [];
  const exists = current.some((answer) => answer.optionId === optionId);
  const next = exists ? current.filter((answer) => answer.optionId !== optionId) : [...current, { questionId, optionId, intensity: 0.5 }];
  return { ...draft, answers: { ...draft.answers, [questionId]: next } };
}

export function setAnswerIntensity(draft: DraftState, questionId: string, optionId: string, intensity: number): DraftState {
  const current = draft.answers[questionId] ?? [];
  const next = current.map((answer) => (answer.optionId === optionId ? { ...answer, intensity } : answer));
  return { ...draft, answers: { ...draft.answers, [questionId]: next } };
}

export function answersFor(draft: DraftState, questionId: string): AnswerPayload[] {
  return draft.answers[questionId] ?? [];
}

export function toRequest(draft: DraftState): TestAnswersRequest {
  return {
    answers: Object.values(draft.answers).flat(),
    adaptiveAnswers: draft.adaptiveAnswer ? [draft.adaptiveAnswer] : []
  };
}

function isDraft(value: unknown): value is DraftState {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<DraftState>;
  if (!candidate.screen || !["intro", "base", "adaptive", "loading", "results", "detail", "error", "empty"].includes(candidate.screen)) return false;
  const currentQuestion = candidate.currentQuestion;
  if (!candidate.answers || typeof candidate.answers !== "object" || typeof currentQuestion !== "number" || !Number.isInteger(currentQuestion) || currentQuestion < 0) return false;
  if (candidate.adaptiveAnswer !== null && candidate.adaptiveAnswer !== undefined && typeof candidate.adaptiveAnswer !== "object") return false;
  if (candidate.results !== null && candidate.results !== undefined && typeof candidate.results !== "object") return false;
  return true;
}

export { STORAGE_KEY };
