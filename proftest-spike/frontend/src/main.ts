import "./styles.css";

import { ApiError, getBootstrap, getResults, previewTest } from "./api/client";
import type { AdaptiveQuestion, BootstrapResponse, PreviewResponse, Recommendation, ResultsResponse } from "./api/generated";
import { renderEmpty, renderError, renderLoading } from "./components/States";
import { renderAdaptiveScreen } from "./features/adaptive/AdaptiveScreen";
import { renderIntroScreen } from "./features/test/IntroScreen";
import { renderQuestionScreen } from "./features/test/QuestionScreen";
import { renderResultDetail } from "./features/results/ResultDetail";
import { renderResultsScreen } from "./features/results/ResultsScreen";
import {
  answersFor,
  emptyDraft,
  loadDraft,
  saveDraft,
  setAnswerIntensity,
  setSingleAnswer,
  toggleMultiAnswer,
  toRequest,
  type DraftState
} from "./state/testState";

const root = document.querySelector<HTMLDivElement>("#app");
if (!root) throw new Error("Application root is missing");
const appRoot = root;

let bootstrap: BootstrapResponse | null = null;
let preview: PreviewResponse | null = null;
let draft: DraftState = loadDraft();
let detailRecommendation: Recommendation | null = null;

function debug(message: string): void {
  const level = ((import.meta.env.VITE_LOG_LEVEL as string | undefined) ?? "WARN").toUpperCase();
  if (level === "DEBUG") console.debug(`[proftest-spike] ${message}`);
}

function frame(content: HTMLElement): void {
  const app = document.createElement("main");
  app.className = "app-frame";
  const brandbar = document.createElement("header");
  brandbar.className = "brandbar";
  const brand = document.createElement("div");
  brand.className = "brand";
  const mark = document.createElement("span");
  mark.className = "brand-mark";
  mark.textContent = "A";
  const brandText = document.createElement("span");
  brandText.textContent = "Andromeda";
  brand.append(mark, brandText);
  const note = document.createElement("span");
  note.className = "brand-note";
  note.textContent = "образовательный навигатор";
  brandbar.append(brand, note);
  app.append(brandbar, content);
  appRoot.replaceChildren(app);
}

async function init(): Promise<void> {
  frame(renderLoading("Подключаем Andromeda API"));
  try {
    const loadedBootstrap = await getBootstrap();
    bootstrap = loadedBootstrap;
    debug(`bootstrap_loaded question_count=${loadedBootstrap.questions.length}`);
    if (draft.screen === "results" && draft.results) {
      renderResults(draft.results);
    } else {
      draft = { ...draft, screen: "intro" };
      saveDraft(draft);
      renderIntro();
    }
  } catch (error) {
    renderApiError(error, init);
  }
}

function renderIntro(): void {
  if (!bootstrap) return;
  frame(renderIntroScreen({
    bootstrap,
    hasDraft: Object.keys(draft.answers).length > 0 || Boolean(draft.results),
    onStart: () => {
      draft = { ...emptyDraft(), screen: "base" };
      preview = null;
      detailRecommendation = null;
      saveDraft(draft);
      renderBase();
    },
    onResume: () => {
      if (draft.results) {
        renderResults(draft.results);
      } else {
        draft = { ...draft, screen: "base" };
        saveDraft(draft);
        renderBase();
      }
    }
  }));
}

function renderBase(): void {
  if (!bootstrap) return;
  const loadedBootstrap = bootstrap;
  const question = loadedBootstrap.questions[draft.currentQuestion];
  if (!question) return renderIntro();
  frame(renderQuestionScreen({
    question,
    index: draft.currentQuestion,
    total: loadedBootstrap.questions.length,
    selected: answersFor(draft, question.id),
    onSelect: (optionId) => {
      draft = question.kind === "multi_intensity" ? toggleMultiAnswer(draft, question.id, optionId) : setSingleAnswer(draft, question.id, optionId);
      saveDraft(draft);
      renderBase();
    },
    onIntensity: (optionId, intensity) => {
      draft = setAnswerIntensity(draft, question.id, optionId, intensity);
      saveDraft(draft);
      renderBase();
    },
    onBack: () => {
      if (draft.currentQuestion === 0) return renderIntro();
      draft = { ...draft, currentQuestion: draft.currentQuestion - 1 };
      saveDraft(draft);
      renderBase();
    },
    onNext: () => {
      if (draft.currentQuestion < loadedBootstrap.questions.length - 1) {
        draft = { ...draft, currentQuestion: draft.currentQuestion + 1 };
        saveDraft(draft);
        renderBase();
      } else {
        void loadPreview();
      }
    }
  }));
}

async function loadPreview(): Promise<void> {
  draft = { ...draft, screen: "loading" };
  saveDraft(draft);
  frame(renderLoading("Ищем вопрос, который различит программы"));
  try {
    preview = await previewTest(toRequest(draft));
    debug(`adaptive_preview status=${preview.adaptive?.status ?? "none"}`);
    if (preview.status === "empty") return renderEmptyState("Каталог Andromeda пока не содержит учебных планов.");
    draft = { ...draft, screen: "adaptive" };
    saveDraft(draft);
    renderAdaptive();
  } catch (error) {
    renderApiError(error, () => void loadPreview());
  }
}

function renderAdaptive(): void {
  if (!preview) return renderErrorState("Адаптивное уточнение не загрузилось.", () => void loadPreview());
  const adaptiveQuestion: AdaptiveQuestion | null = preview.adaptive?.question ?? null;
  frame(renderAdaptiveScreen({
    question: adaptiveQuestion,
    skippedReason: preview.adaptive?.reason ?? null,
    selectedId: draft.adaptiveAnswer?.optionId ?? null,
    onSelect: (optionId) => {
      if (!adaptiveQuestion) return;
      draft = {
        ...draft,
        adaptiveAnswer: {
          questionId: adaptiveQuestion.id,
          optionId,
          firstDimension: adaptiveQuestion.firstDimension.code,
          secondDimension: adaptiveQuestion.secondDimension.code
        }
      };
      saveDraft(draft);
      renderAdaptive();
    },
    onBack: () => {
      draft = { ...draft, screen: "base", currentQuestion: (bootstrap?.questions.length ?? 1) - 1 };
      saveDraft(draft);
      renderBase();
    },
    onNext: () => void loadResults()
  }));
}

async function loadResults(): Promise<void> {
  draft = { ...draft, screen: "loading" };
  saveDraft(draft);
  frame(renderLoading("Собираем объяснимый shortlist"));
  try {
    const results = await getResults(toRequest(draft));
    if (results.status === "empty") return renderEmptyState(results.note);
    draft = { ...draft, results, screen: "results" };
    saveDraft(draft);
    debug(`results_rendered count=${results.recommendations.length}`);
    renderResults(results);
  } catch (error) {
    renderApiError(error, () => void loadResults());
  }
}

function renderResults(results: ResultsResponse): void {
  draft = { ...draft, results, screen: "results" };
  saveDraft(draft);
  detailRecommendation = null;
  frame(renderResultsScreen({
    results,
    onDetail: (recommendation) => {
      detailRecommendation = recommendation;
      draft = { ...draft, screen: "detail" };
      saveDraft(draft);
      renderDetail();
    },
    onRestart: () => {
      draft = { ...emptyDraft(), screen: "base" };
      saveDraft(draft);
      renderBase();
    }
  }));
}

function renderDetail(): void {
  const savedResults = draft.results;
  if (!detailRecommendation || !savedResults) return savedResults ? renderResults(savedResults) : renderIntro();
  frame(renderResultDetail(detailRecommendation, () => renderResults(savedResults)));
}

function renderEmptyState(message: string): void {
  draft = { ...draft, screen: "empty" };
  saveDraft(draft);
  frame(renderEmpty(message, () => {
    draft = { ...emptyDraft(), screen: "base" };
    saveDraft(draft);
    renderBase();
  }));
}

function renderErrorState(message: string, retry: () => void): void {
  draft = { ...draft, screen: "error" };
  saveDraft(draft);
  frame(renderError(message, retry));
}

function renderApiError(error: unknown, retry: () => void): void {
  const message = error instanceof ApiError ? error.message : "Проверь, что Spike backend и Andromeda API запущены.";
  renderErrorState(message, retry);
}

void init();
