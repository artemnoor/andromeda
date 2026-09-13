import { getProftestQuestions, getProftestResults, previewProftest, type ProftestPreviewResponse } from "../../api/client";
import type { components } from "../../api/generated";
import { clearDraft, emptyDraft, hasInProgressDraft, loadDraft, saveDraft, setAnswer, setIntensity, toRequest, toggleAnswer, type ProftestDraft } from "./state";
import { loadPersistedResults } from "./profilePersistence";
import { renderAdaptiveMarkup } from "./AdaptiveScreen";
import { renderRecommendationDetail } from "../recommendations/RecommendationDetail";
import { renderQuestionMarkup } from "./QuestionScreen";
import { renderRecommendationList } from "../recommendations/RecommendationList";
import { renderAdaptiveSkipped, renderError, renderEmpty, renderLoading } from "./ProftestStates";

type Question = components["schemas"]["QuestionResponse"];
type Recommendation = components["schemas"]["RecommendationResponse"];

export function renderProftestPage(root: HTMLElement): void {
  let questions: Question[] = [];
  let draft: ProftestDraft = loadDraft();
  let preview: ProftestPreviewResponse | null = null;
  let selectedRecommendation = 0;
  renderLoading(root);

  void getProftestQuestions()
    .then(async (response) => {
      questions = response.questions;
      if (hasInProgressDraft(draft)) {
        if (draft.screen === "base" && draft.currentQuestion < questions.length) renderQuestion();
        else if (draft.screen === "adaptive" && draft.adaptiveAnswer === null) void requestPreview();
        else renderIntro();
        return;
      }
      const persisted = await loadPersistedResults();
      if (persisted) {
        draft = { ...draft, screen: "results", results: persisted };
        saveDraft(draft);
        renderResults(true);
      } else if (draft.results && draft.screen === "results") renderResults();
      else renderIntro();
    })
    .catch((error: unknown) => renderError(root, error));

  function renderIntro(): void {
    draft = { ...emptyDraft(), screen: "intro" };
    saveDraft(draft);
    root.innerHTML = `<section class="hero proftest-hero"><p class="eyebrow">Andromeda · профиль содержания</p><h1>Какие учебные планы тебе действительно интересны?</h1><p class="lead">Небольшой сценарный тест сопоставит твои интересы с реальными дисциплинами МГТУ. Это не диагноз и не выбор профессии — только честное сравнение содержания обучения.</p><div class="proftest-meta"><span>6 базовых вопросов</span><span>8–12 минут</span><span>Реальные учебные планы</span></div><button class="primary-button" data-testid="proftest-start" type="button">Начать профтест</button></section>`;
    root.querySelector<HTMLButtonElement>("[data-testid='proftest-start']")?.addEventListener("click", () => {
      draft = { ...emptyDraft(), screen: "base" };
      saveDraft(draft);
      renderQuestion();
    });
  }

  function renderQuestion(): void {
    const question = questions[draft.currentQuestion];
    if (!question) {
      renderEmpty(root, "Вопросы профтеста недоступны");
      return;
    }
    draft = { ...draft, screen: "base" };
    saveDraft(draft);
    const selected = draft.answers[question.id]?.optionIds ?? [];
    root.innerHTML = renderQuestionMarkup(question, draft, draft.currentQuestion, questions.length);
    root.querySelectorAll<HTMLButtonElement>("[data-option]").forEach((button) => {
      button.addEventListener("click", () => {
        draft = question.multiSelect ? toggleAnswer(draft, question.id, button.dataset.option ?? "", question.maxSelected) : setAnswer(draft, question.id, [button.dataset.option ?? ""]);
        renderQuestion();
      });
    });
    root.querySelector<HTMLInputElement>("[data-testid='anti-intensity']")?.addEventListener("input", (event) => {
      const value = Number((event.target as HTMLInputElement).value);
      draft = setIntensity(draft, question.id, value);
      const output = root.querySelector<HTMLOutputElement>("output");
      if (output) output.value = `${Math.round(value * 100)}%`;
      saveDraft(draft);
    });
    root.querySelector<HTMLButtonElement>("[data-testid='proftest-back']")?.addEventListener("click", () => {
      if (draft.currentQuestion === 0) return;
      draft = { ...draft, currentQuestion: draft.currentQuestion - 1, screen: "base" };
      renderQuestion();
    });
    root.querySelector<HTMLButtonElement>("[data-testid='proftest-next']")?.addEventListener("click", () => {
      if (selected.length === 0 && question.required) return;
      if (draft.currentQuestion < questions.length - 1) {
        draft = { ...draft, currentQuestion: draft.currentQuestion + 1, screen: "base" };
        renderQuestion();
      } else void requestPreview();
    });
  }

  async function requestPreview(): Promise<void> {
    draft = { ...draft, screen: "loading" };
    saveDraft(draft);
    renderLoading(root);
    try {
      preview = await previewProftest(toRequest(draft));
      if (preview.adaptive.status === "ready" && preview.question) renderAdaptive(preview);
      else {
        draft = { ...draft, screen: "adaptive" };
        saveDraft(draft);
        renderAdaptiveSkipped(root, preview.adaptive.reason ?? null);
        root.querySelector<HTMLButtonElement>("[data-testid='adaptive-skipped-continue']")?.addEventListener("click", () => void requestResults());
      }
    } catch (error: unknown) {
      renderError(root, error);
    }
  }

  function renderAdaptive(currentPreview: ProftestPreviewResponse): void {
    const question = currentPreview.question;
    if (!question) {
      void requestResults();
      return;
    }
    draft = { ...draft, screen: "adaptive" };
    saveDraft(draft);
    root.innerHTML = renderAdaptiveMarkup(question, currentPreview, draft);
    root.querySelectorAll<HTMLButtonElement>("[data-adaptive-option]").forEach((button) => button.addEventListener("click", () => {
      const optionId = button.dataset.adaptiveOption ?? "";
      const dimension = currentPreview.adaptive.dimensions[0]?.code ?? "activity:analytical";
      draft = { ...draft, adaptiveAnswer: { questionId: question.id, optionId, dimension } };
      renderAdaptive(currentPreview);
    }));
    root.querySelector<HTMLButtonElement>("[data-testid='adaptive-back']")?.addEventListener("click", () => {
      draft = { ...draft, screen: "base", currentQuestion: questions.length - 1, adaptiveAnswer: null };
      renderQuestion();
    });
    root.querySelector<HTMLButtonElement>("[data-testid='adaptive-submit']")?.addEventListener("click", () => void requestResults());
  }

  async function requestResults(): Promise<void> {
    draft = { ...draft, screen: "loading" };
    saveDraft(draft);
    renderLoading(root);
    try {
      const results = await getProftestResults(toRequest(draft));
      draft = { ...draft, screen: "results", results };
      saveDraft(draft);
      if (results.recommendations.length === 0) renderEmpty(root, "Для этого профиля пока нет подходящих программ");
      else renderResults();
    } catch (error: unknown) {
      renderError(root, error);
    }
  }

  function renderResults(restored = false): void {
    const results = draft.results;
    if (!results || results.recommendations.length === 0) {
      renderEmpty(root, "Для этого профиля пока нет подходящих программ");
      return;
    }
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
