import { completeProftestSession, getCurrentProftestSession, nextProftestSession, saveProftestSession, startProftestSession, type ProftestSessionAnswerRequest, type ProftestSessionResponse } from "../../api/client";
import { ApiError } from "../../api/errors";
import type { components } from "../../api/generated";
import { clearDraft, emptyDraft, loadDraft, saveDraft, type ProftestDraft } from "./state";
import { loadPersistedResults } from "./profilePersistence";
import { renderRecommendationDetail } from "../recommendations/RecommendationDetail";
import { renderRecommendationList } from "../recommendations/RecommendationList";
import { renderSessionQuestionMarkup } from "./QuestionScreen";
import { renderError, renderEmpty, renderLoading } from "./ProftestStates";

type Question = components["schemas"]["QuestionResponse"];
type Recommendation = components["schemas"]["RecommendationResponse"];

const renderTokens = new WeakMap<HTMLElement, symbol>();

export function renderProftestPage(root: HTMLElement): void {
  const renderToken = Symbol("proftest-render");
  renderTokens.set(root, renderToken);
  const isCurrentRender = (): boolean => renderTokens.get(root) === renderToken && window.location.hash === "#proftest";
  let draft: ProftestDraft = loadDraft();
  let selectedRecommendation = 0;
  renderLoading(root);
  void bootstrap();

  async function bootstrap(): Promise<void> {
    try {
      const session = await getCurrentProftestSession();
      if (!isCurrentRender()) return;
      applySession(session);
      if (session.status === "completed" && session.results) renderResults(true);
      else renderSession();
    } catch (error: unknown) {
      if (!isCurrentRender()) return;
      if (error instanceof ApiError && error.status === 404) {
        try {
          const persisted = await loadPersistedResults();
          if (persisted) {
            draft = { ...emptyDraft(), screen: "results", results: persisted };
            saveDraft(draft);
            renderResults(true);
          } else renderIntro();
        } catch (restoreError: unknown) {
          renderError(root, restoreError, () => renderProftestPage(root));
        }
      } else renderError(root, error, () => renderProftestPage(root));
    }
  }

  function renderIntro(): void {
    draft = { ...emptyDraft(), screen: "intro" };
    saveDraft(draft);
    root.innerHTML = `<section class="hero proftest-hero"><p class="eyebrow">Andromeda · профиль содержания</p><h1>Какие учебные планы тебе действительно интересны?</h1><p class="lead">Адаптивный сценарный тест сопоставит твои интересы с реальными дисциплинами МГТУ. Это не диагноз и не ярлык — только честное сравнение содержания обучения.</p><div class="proftest-meta"><span>24 базовых шага</span><span>примерно 8–12 минут</span><span>до 10 уточнений по каталогу</span></div><button class="primary-button" data-testid="proftest-start" type="button">Начать профтест</button></section>`;
    root.querySelector<HTMLButtonElement>("[data-testid='proftest-start']")?.addEventListener("click", () => void startSession());
  }

  async function startSession(): Promise<void> {
    draft = { ...emptyDraft(), screen: "loading" };
    saveDraft(draft);
    renderLoading(root);
    try {
      const session = await startProftestSession();
      if (!isCurrentRender()) return;
      applySession(session);
      renderSession();
    } catch (error: unknown) {
      if (isCurrentRender()) renderError(root, error, () => void startSession());
    }
  }

  function applySession(session: ProftestSessionResponse): void {
    const question = session.currentQuestion;
    const sessionQuestions = question ? { ...draft.sessionQuestions, [question.id]: question } : draft.sessionQuestions;
    draft = { ...draft, session, sessionQuestionId: null, screen: session.status === "completed" ? "results" : "base", sessionQuestions };
    if (session.results) draft = { ...draft, results: session.results };
    saveDraft(draft);
  }

  function renderSession(): void {
    const session = draft.session;
    if (!session) return renderIntro();
    if (session.status === "completed") return draft.results ? renderResults() : renderEmpty(root, "Результаты профтеста пока недоступны");
    const question = currentQuestion(session);
    if (!question) return void completeSession();
    draft = { ...draft, screen: question.adaptive ? "adaptive" : "base", sessionQuestions: { ...draft.sessionQuestions, [question.id]: question } };
    saveDraft(draft);
    root.innerHTML = renderSessionQuestionMarkup(question, draft, session.progress, isFirstQuestion(question));
    root.querySelectorAll<HTMLButtonElement>("[data-option]").forEach((button) => button.addEventListener("click", () => {
      const optionId = button.dataset.option ?? "";
      const current = draft.sessionAnswers[question.id];
      const optionIds = question.multiSelect ? toggleSessionOption(current?.optionIds ?? [], optionId, question.maxSelected) : [optionId];
      setSessionAnswer(question, { optionIds, status: "answered" });
      renderSession();
    }));
    root.querySelector<HTMLInputElement>("[data-testid='session-intensity']")?.addEventListener("input", (event) => {
      const intensity = Number((event.target as HTMLInputElement).value);
      setSessionAnswer(question, { intensity });
      const output = root.querySelector<HTMLOutputElement>("output");
      if (output) output.value = `${Math.round(intensity * 100)}%`;
      saveDraft(draft);
    });
    root.querySelector<HTMLButtonElement>("[data-testid='session-uncertain']")?.addEventListener("click", () => {
      setSessionAnswer(question, { optionIds: [], status: "uncertain" });
      renderSession();
    });
    root.querySelector<HTMLButtonElement>("[data-testid='session-skip']")?.addEventListener("click", () => {
      setSessionAnswer(question, { optionIds: [], status: "skipped" });
      renderSession();
    });
    root.querySelector<HTMLButtonElement>("[data-testid='session-back']")?.addEventListener("click", () => goBack(question));
    root.querySelector<HTMLButtonElement>("[data-testid='session-next']")?.addEventListener("click", () => void advance(question));
  }

  async function advance(question: Question): Promise<void> {
    const session = draft.session;
    if (!session) return;
    const answer = draft.sessionAnswers[question.id] ?? { questionId: question.id, optionIds: [], status: "uncertain" as const };
    if (question.required && (answer.optionIds ?? []).length === 0 && answer.status === "answered") return;
    draft = { ...draft, screen: "loading" };
    saveDraft(draft);
    renderLoading(root);
    try {
      const isEditing = session.currentQuestion?.id !== question.id;
      const next = isEditing
        ? await saveProftestSession([answer], session.revision)
        : await nextProftestSession(answer, session.revision);
      if (!isCurrentRender()) return;
      applySession(next);
      if (next.currentQuestion) renderSession();
      else void completeSession();
    } catch (error: unknown) {
      if (isCurrentRender()) renderError(root, error, () => renderSession());
    }
  }

  async function completeSession(): Promise<void> {
    const session = draft.session;
    if (!session) return;
    draft = { ...draft, screen: "loading" };
    saveDraft(draft);
    renderLoading(root);
    try {
      const completed = await completeProftestSession();
      if (!isCurrentRender()) return;
      applySession(completed);
      if (completed.results) {
        draft = { ...draft, screen: "results", results: completed.results };
        saveDraft(draft);
        renderResults();
      } else renderEmpty(root, "Профиль сохранён, но рекомендации пока недоступны");
    } catch (error: unknown) {
      if (isCurrentRender()) renderError(root, error, () => void completeSession());
    }
  }

  function goBack(question: Question): void {
    const previous = Object.values(draft.sessionQuestions)
      .filter((candidate) => candidate.order < question.order)
      .sort((a, b) => b.order - a.order)[0];
    if (!previous) return;
    draft = { ...draft, sessionQuestionId: previous.id, screen: "base" };
    saveDraft(draft);
    renderSession();
  }

  function currentQuestion(session: ProftestSessionResponse): Question | null {
    if (draft.sessionQuestionId) return draft.sessionQuestions[draft.sessionQuestionId] ?? session.currentQuestion ?? null;
    return session.currentQuestion ?? null;
  }

  function isFirstQuestion(question: Question): boolean {
    return question.order === 0 || Object.values(draft.sessionQuestions).every((candidate) => candidate.order >= question.order);
  }

  function setSessionAnswer(question: Question, patch: Partial<ProftestSessionAnswerRequest>): void {
    const previous = draft.sessionAnswers[question.id] ?? { questionId: question.id, optionIds: [], status: "answered" as const };
    draft = { ...draft, sessionAnswers: { ...draft.sessionAnswers, [question.id]: { ...previous, ...patch, questionId: question.id } } };
    saveDraft(draft);
  }

  function renderResults(restored = false): void {
    const results = draft.results;
    if (!results || results.recommendations.length === 0) return renderEmpty(root, "Для этого профиля пока нет подходящих программ");
    selectedRecommendation = Math.min(selectedRecommendation, results.recommendations.length - 1);
    root.innerHTML = renderRecommendationList(results, { restored });
    root.querySelectorAll<HTMLButtonElement>("[data-result-detail]").forEach((button) => button.addEventListener("click", () => {
      selectedRecommendation = Number(button.dataset.resultDetail ?? 0);
      renderDetail(results.recommendations[selectedRecommendation]);
    }));
    root.querySelector<HTMLButtonElement>("[data-testid='proftest-restart']")?.addEventListener("click", () => {
      clearDraft();
      draft = emptyDraft();
      renderIntro();
    });
  }

  function renderDetail(recommendation: Recommendation | undefined): void {
    if (!recommendation) return;
    const detail = root.querySelector<HTMLElement>("#proftest-detail");
    if (!detail) return;
    detail.innerHTML = renderRecommendationDetail(recommendation);
    detail.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function toggleSessionOption(current: readonly string[], optionId: string, maxSelected: number): string[] {
  return current.includes(optionId)
    ? current.filter((value) => value !== optionId)
    : current.length < maxSelected ? [...current, optionId] : [...current];
}
